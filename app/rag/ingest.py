"""PDF'leri okuyup temizler, parçalar ve ChromaDB'ye yazar.

Kullanım:
    python -m app.rag.ingest            # data/pdfs altındaki tüm PDF'ler
    python -m app.rag.ingest --reset    # koleksiyonu silip baştan kur
"""
import argparse
import re
import shutil
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


def split_documents(docs: list[Document]) -> list[Document]:
    s = get_settings()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=s.chunk_size,
        chunk_overlap=s.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_documents(docs)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="mevcut indeksi sil")
    args = parser.parse_args()

    s = get_settings()
    if args.reset and s.chroma_dir.exists():
        shutil.rmtree(s.chroma_dir)

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
    store.add_documents(all_chunks, ids=ids)
    cache.clear()  # belgeler değişti: eski cevaplar geçersiz
    print(f"Toplam {len(all_chunks)} parça indekslendi -> {s.chroma_dir}")


if __name__ == "__main__":
    main()
