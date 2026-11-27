"""PDF'leri okuyup temizler, parçalar ve ChromaDB'ye yazar.

Kullanım:
    python -m app.rag.ingest            # data/pdfs altındaki tüm PDF'ler
    python -m app.rag.ingest --reset    # koleksiyonu silip baştan kur
"""
import argparse
import os
import re
import shutil
import stat
import time
from collections import Counter
from pathlib import Path

import pymupdf as fitz
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app import cache
from app.config import get_settings
from app.rag.store import get_vectorstore


def clean_text(text: str) -> str:
    """PDF'ten gelen metindeki tipik gürültüyü temizler."""
    text = text.replace("­", "")              # yumuşak tire
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)   # satır sonu heceleme
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.M)  # yalnız sayfa numarası olan satırlar
    return text.strip()


def load_pdf(path: Path) -> list[Document]:
    docs = []
    with fitz.open(path) as pdf:
        for i, page in enumerate(pdf, start=1):
            text = clean_text(page.get_text())
            if len(text) < 30:
                continue
            docs.append(Document(page_content=text, metadata={"source": path.name, "page": i}))
    return docs


MIN_CHUNK_CHARS = 80
MADDE_RE = re.compile(r"(?im)^[ \t]*(?:MADDE|Madde)\s+(\d+)\b")


def _is_article_title(line: str) -> bool:
    """MADDE satırının hemen üstündeki kısa başlık satırını tanır (noktalama ile biten cümle değil)."""
    s = line.strip()
    return bool(s) and len(s) <= 90 and not s.endswith((".", ":", ";", ")")) and not MADDE_RE.match(s)


def _segment_page(
    text: str, current_madde: str, current_heading: str
) -> tuple[list[tuple[str, str, str]], str, str]:
    """Sayfa metnini madde sınırlarından segmentlere böler; sonraki sayfa için etkin maddeyi döndürür."""
    segments: list[tuple[str, str, str]] = []
    buf: list[str] = []
    seg_madde, seg_heading = current_madde, current_heading

    for line in text.splitlines():
        m = MADDE_RE.match(line)
        if m:
            title_line = buf.pop().strip() if buf and _is_article_title(buf[-1]) else ""
            if buf and (prev := "\n".join(buf).strip()):
                segments.append((seg_madde, seg_heading, prev))
            seg_madde = m.group(1)
            seg_heading = f"{title_line} — Madde {seg_madde}" if title_line else f"Madde {seg_madde}"
            buf = [title_line, line] if title_line else [line]
        else:
            buf.append(line)

    if buf and (tail := "\n".join(buf).strip()):
        segments.append((seg_madde, seg_heading, tail))
    return segments, seg_madde, seg_heading


def _pack_segments(segments: list[tuple[str, str, str]], chunk_size: int) -> list[tuple[str, str, str]]:
    """Aynı sayfadaki küçük komşu segmentleri chunk_size içine sığdığı sürece tek parçada birleştirir.

    Birleşik segmentlerde `madde` boş bırakılır; böylece farklı maddeler tek parçaya sıkışırken
    büyük maddeler asla başka bir maddeyle karışmaz.
    """
    packed: list[tuple[str, str, str]] = []
    for madde_num, heading, seg_text in segments:
        if (
            packed
            and len(seg_text) <= chunk_size
            and len(packed[-1][2]) <= chunk_size
            and len(packed[-1][2]) + 2 + len(seg_text) <= chunk_size
        ):
            _, _, prev_text = packed[-1]
            packed[-1] = ("", "", f"{prev_text}\n\n{seg_text}")
        else:
            packed.append((madde_num, heading, seg_text))
    return packed


def _tag_multi_part_articles(chunks: list[Document]) -> list[Document]:
    """Birden fazla parçaya bölünen maddelere kardeş parça metaverisi yazar, tekil etiketleri temizler."""
    counts = Counter(c.metadata["article_id"] for c in chunks if "article_id" in c.metadata)
    part_idx: dict[str, int] = {}
    for chunk in chunks:
        aid = chunk.metadata.get("article_id")
        if not aid:
            continue
        total = counts[aid]
        if total > 1:
            idx = part_idx.get(aid, 0)
            part_idx[aid] = idx + 1
            chunk.metadata["article_part"] = idx
            chunk.metadata["article_parts"] = total
        else:
            chunk.metadata.pop("article_id", None)
    return chunks


def split_documents(docs: list[Document]) -> list[Document]:
    """Belgeleri madde sınırlarına saygılı şekilde böler ve çok parçalı maddeleri etiketler."""
    s = get_settings()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=s.chunk_size,
        chunk_overlap=s.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    raw_chunks: list[Document] = []
    filtered_chunks: list[Document] = []
    current_source: str | None = None
    current_madde = ""
    current_heading = ""

    for doc in docs:
        source = str(doc.metadata.get("source") or "")
        if source != current_source:
            current_source = source
            current_madde, current_heading = "", ""

        segments, current_madde, current_heading = _segment_page(
            doc.page_content, current_madde, current_heading
        )
        for madde_num, heading, seg_text in _pack_segments(segments, s.chunk_size):
            pieces = splitter.split_text(seg_text)
            for pi, piece in enumerate(pieces):
                text = piece.strip()
                if not text:
                    continue
                if pi > 0 and heading and not text.startswith(heading):
                    text = f"[{heading} (devam)]\n{text}"
                meta = dict(doc.metadata)
                if madde_num:
                    meta["article_id"] = f"{source}:m{madde_num}"
                chunk = Document(page_content=text, metadata=meta)
                raw_chunks.append(chunk)
                if len(text) >= MIN_CHUNK_CHARS:
                    filtered_chunks.append(chunk)

    selected = filtered_chunks if filtered_chunks else raw_chunks
    return _tag_multi_part_articles(selected)


# Ücretsiz katman: embedding modeli dakikada en fazla 100 parça kabul ediyor.
BATCH_SIZE = 80      # bir seferde gönderilen parça (sınırın biraz altında)
BATCH_WAIT = 65.0    # iki grup arasında beklenen saniye (bir dakikalık pencere dolsun)


def _is_rate_limit(e: Exception) -> bool:
    msg = str(e)
    return "429" in msg or "RESOURCE_EXHAUSTED" in msg


def add_in_batches(store, chunks, ids, batch_size=BATCH_SIZE, wait=BATCH_WAIT, sleep=time.sleep, attempts=3):
    """Parçaları gruplar hâlinde yazar; gruplar arasında bekleyerek hız sınırına takılmaz.
    Yine de 429 gelirse bekleyip aynı grubu tekrar dener."""
    total = len(chunks)
    for start in range(0, total, batch_size):
        if start:
            print(f"  Hız sınırı için {wait:.0f} sn bekleniyor...")
            sleep(wait)
        part, part_ids = chunks[start:start + batch_size], ids[start:start + batch_size]
        for attempt in range(attempts):
            try:
                store.add_documents(part, ids=part_ids)
                break
            except Exception as e:
                if not _is_rate_limit(e) or attempt == attempts - 1:
                    raise
                print(f"  Google hız sınırı (429); {wait:.0f} sn sonra tekrar denenecek...")
                sleep(wait)
        print(f"  {min(start + batch_size, total)}/{total} parça yazıldı")


def _remove_readonly(func, path, _exc_info) -> None:
    os.chmod(path, stat.S_IWRITE)
    func(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="mevcut indeksi sil")
    args = parser.parse_args()

    s = get_settings()
    if args.reset and s.chroma_dir.exists():
        shutil.rmtree(s.chroma_dir, onerror=_remove_readonly)

    pdfs = sorted(s.pdf_dir.glob("*.pdf"))
    if not pdfs:
        print(f"{s.pdf_dir} içinde PDF yok. Önce resmî belgeleri bu klasöre koyun.")
        return

    all_chunks = []
    for pdf in pdfs:
        chunks = split_documents(load_pdf(pdf))
        print(f"{pdf.name}: {len(chunks)} parça")
        all_chunks.extend(chunks)

    store = get_vectorstore()
    ids = [f"{c.metadata['source']}-{c.metadata['page']}-{i}" for i, c in enumerate(all_chunks)]
    add_in_batches(store, all_chunks, ids)
    cache.clear()  # belgeler değişti: eski cevaplar geçersiz
    print(f"Toplam {len(all_chunks)} parça indekslendi -> {s.chroma_dir}")


if __name__ == "__main__":
    main()
