"""Akademik birim rehberi (data/akademik_birimler.json): fakülte, enstitü, yüksekokul ve MYO'lar.

"Hemşirelik fakültesi var mı?", "Hukuk fakültesinin telefonu ne?", "Fen fakültesi nerede?",
"Hangi fakülteler var?" gibi soruları Gemini'ye gitmeden, resmî listeden cevaplar.

Güvenlik kuralları:
* Soru yalnızca birimle ilgiliyse cevaplanır. "Hukuk fakültesinde staj zorunlu mu?" gibi
  başka bir içerik soran sorular None döner ve belgelere (RAG) gider.
* "eğitim", "iletişim", "fen" gibi sıradan kelimeler tek başına birim sayılmaz; arkasından
  "fakültesi / enstitüsü / yüksekokulu" gelmelidir ("İletişim bilgileri nedir?" yanlış eşleşmesin).
* Boş (doğrulanmamış) iletişim alanları gösterilmez; harita bağlantısı yalnızca "arama" olarak verilir.
"""
import json
import re
from functools import lru_cache

from app.config import get_settings

TYPE_STEMS = ("meslek yüksekokul", "yüksekokul", "fakülte", "enstitü", "konservatuvar", "myo")
# Sıradan kelime de olan adlar: tek başına değil, ancak birim türüyle birlikte eşleşir.
AMBIGUOUS = {"eğitim", "iletişim", "fen", "teknoloji", "turizm", "edebiyat", "spor", "sağlık", "güzel sanatlar"}

AMBIGUOUS_N = set()  # _norm uygulanmış hâli aşağıda doldurulur
FILLER = {
    "selçuk", "selcuk", "selçukta", "selçukda", "üniversite", "üniversitesi", "üniversitesinde", "üniversitenin",
    "üniversitede", "su", "sü", "da", "de", "ta", "te", "mi", "mı", "mu", "mü", "acaba", "bir", "bu", "için", "ne",
    "nedir", "neler", "nelerdir", "hangi", "hangileri", "kaç", "tane", "adet", "ve", "ile", "bana", "söyler",
    "söyleyebilir", "misin", "musun", "verir", "verebilir", "öğrenebilir", "öğrenmek", "istiyorum", "lütfen",
    "merhaba", "selam", "peki", "o", "onun", "nasıl", "neresi", "nerede", "nerde", "nereye", "nereden",
}
EXISTENCE = ("var", "mevcut", "bulunuyor", "bulunur", "bulunmakta")
CONTACT = ("telefon", "numara", "iletişim", "ulaş", "eposta", "posta", "mail", "web", "site", "sayfa", "internet", "bilgi")
LOCATION = ("adres", "konum", "nerede", "nerde", "nereye", "neresi", "yer", "harita", "git", "gid", "kampüs", "yerleşke")
LIST_LABELS = {
    "fakülte": ("fakulte", "fakülte"),
    "enstitü": ("enstitu", "enstitü"),
    "meslek yüksekokul": ("meslek_yuksekokulu", "meslek yüksekokulu"),
    "yüksekokul": ("yuksekokul", "yüksekokul"),
    "myo": ("meslek_yuksekokulu", "meslek yüksekokulu"),
}
# Birim türü -> soruda o türü gösteren kelime kökleri ("Sağlık Bilimleri Enstitüsü" ≠ "... Fakültesi")
TYPE_OF = {
    "fakulte": ("fakülte",),
    "enstitu": ("enstitü",),
    "yuksekokul": ("yüksekokul", "yo"),
    "meslek_yuksekokulu": ("meslek yüksekokul", "myo"),
    "konservatuvar": ("konservatuvar",),
}
_SUFFIXES = ("meslek yüksekokulu", "yüksekokulu", "fakültesi", "enstitüsü", "konservatuvarı")
LIST_URL = "https://selcuk.edu.tr/anasayfa/akademik"
SOURCE = f"_Kaynak: Selçuk Üniversitesi resmî akademik birimler listesi ({LIST_URL})_"


def _norm(text: str) -> str:
    text = text.replace("İ", "i").replace("I", "ı").lower().replace("\u0307", "")
    # Birim adlarında ı/i karışmasın ("Ilgın" / "ilgın"); "diş"/"dış" ayrımı korunur.
    text = text.replace("ı", "i")
    text = re.sub(r"['’`-]", "", text)  # "Fakültesi'nin" -> "fakültesinin", "e-posta" -> "eposta"
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", text)).strip()


@lru_cache
def load_units() -> list[dict]:
    path = get_settings().academic_units_file
    with open(path, encoding="utf-8") as f:
        return json.load(f)["birimler"]


def _acronym(words: list[str]) -> str:
    return "".join(w[0] for w in words if w not in ("ve", "ile"))


@lru_cache(maxsize=None)
def _phrases_cached(name: str, keywords: tuple[str, ...]) -> tuple[str, ...]:
    phrases = {_norm(p) for p in (name, *keywords) if p}
    # Türü atılmış kök ad ve kısaltmalar: "Ilgın", "İİBF", "Akşehir İİBF", "Adalet MYO"
    base = _norm(name)
    for suf in _SUFFIXES:
        if base.endswith(" " + _norm(suf)):
            base = base[: -len(suf) - 1]
            break
    phrases.add(base)
    if _norm(name).endswith(_norm("konservatuvarı")):  # tek konservatuvar var; tür adı tek başına yeter
        phrases.add(_norm("konservatuvar"))
    if base.startswith(_norm("hukuk fakültesi ")):
        phrases.add(base.removeprefix(_norm("hukuk fakültesi")).strip())
    words = _norm(name).split()
    acr = _acronym(words)
    if len(acr) >= 4 and len(words) >= 4:
        phrases.add(acr)
    if len(words) >= 5:
        phrases.add(f"{words[0]} {_acronym(words[1:])}")
    return tuple(sorted(phrases, key=len, reverse=True))


def _phrases(unit: dict) -> tuple[str, ...]:
    return _phrases_cached(unit["ad"], tuple(unit.get("anahtar_kelimeler", [])))


_TYPE_RE = "|".join(_norm(t) for t in TYPE_STEMS)


def _find(q: str, unit: dict) -> tuple[int, int] | None:
    """Birimin soruda geçtiği aralık (başlangıç, bitiş) ya da None."""
    own = "|".join(_norm(t) for t in TYPE_OF.get(unit.get("tur"), TYPE_STEMS))
    for p in _phrases(unit):
        if re.search(rf"(?<!\w)(?:{_TYPE_RE})", p):
            m = re.search(rf"(?<!\w){re.escape(p)}\w*", q)  # "fakültesi" -> "fakültesinin"
        else:
            # Kök ad + bu birimin kendi türü ("sağlık bilimleri enstitüsü" Fakülte'ye gitmesin)
            m = re.search(rf"(?<!\w){re.escape(p)}\w*\s+(?:{own})\w*", q)
            other = re.search(rf"(?<!\w){re.escape(p)}\w*\s+(?:{_TYPE_RE})", q)
            if not m and not other and p not in AMBIGUOUS_N:
                m = re.search(rf"(?<!\w){re.escape(p)}(?!\w)", q) if len(p) <= 5 else re.search(rf"(?<!\w){re.escape(p)}\w*", q)
        if m:
            return m.span()
    return None


def match(question: str) -> tuple[dict, tuple[int, int]] | None:
    """Soruda geçen en uzun (en özel) birim adı; yoksa None."""
    q = _norm(question)
    best = None
    for u in load_units():
        span = _find(q, u)
        if span and (best is None or span[1] - span[0] > best[1][1] - best[1][0]):
            best = (u, span)
    return best


AMBIGUOUS_N.update(_norm(w) for w in AMBIGUOUS)
FILLER = {_norm(w) for w in FILLER}
EXISTENCE, CONTACT, LOCATION = (tuple(_norm(w) for w in g) for g in (EXISTENCE, CONTACT, LOCATION))
_TYPE_STEMS_N = tuple(_norm(t) for t in TYPE_STEMS)


def _starts(token: str, stems) -> bool:
    return any(token.startswith(s) for s in stems)


def _only_about_unit(tokens: list[str]) -> bool:
    """Kalan kelimelerin hepsi dolgu/niyet kelimesi mi? (Başka bir şey soruluyorsa RAG'a bırak.)"""
    return all(t in FILLER or _starts(t, EXISTENCE + CONTACT + LOCATION) or _starts(t, _TYPE_STEMS_N) for t in tokens)


def _esc(text: str) -> str:
    return text.replace("_", "\\_").replace("*", "\\*")


def format_unit(unit: dict, location: bool = False) -> str:
    lines = []
    if unit.get("telefon"):
        lines.append(f"☎️ {unit['telefon']}")
    if unit.get("eposta"):
        lines.append(f"✉️ {_esc(unit['eposta'])}")
    if unit.get("web"):
        lines.append(f"🌐 {_esc(unit['web'])}")
    if unit.get("konum"):
        lines.append(f"📍 {_esc(unit['konum'])}")
    elif location:
        lines.append("📍 Adresi resmî kaynakta doğrulanamadığı için yazmıyorum; birimin web sitesine bakabilirsin.")
    if location and unit.get("harita_url"):
        lines.append(f"🗺 Haritada ara: {_esc(unit['harita_url'])}")
    return "\n".join(lines)


def _list_answer(q_tokens: list[str]) -> str | None:
    for stem, (tur, label) in LIST_LABELS.items():
        stem = _norm(stem)
        plural = any(t.startswith(stem.split()[-1]) and t.endswith(("ler", "leri", "lar", "ları")) for t in q_tokens)
        counting = "kaç" in q_tokens and any(t.startswith(stem.split()[-1]) for t in q_tokens)
        if plural or counting:
            names = [u["ad"] for u in load_units() if u.get("tur") == tur]
            if not names:
                return None
            body = "\n".join(f"• {n}" for n in names)
            return f"Selçuk Üniversitesi'nde {len(names)} {label} bulunuyor:\n\n{body}\n\n{SOURCE}"
    return None


def answer_unit_question(question: str) -> str | None:
    """Birim sorusuysa cevap metni, değilse None."""
    q = _norm(question)
    found = match(question)
    if found is None:
        tokens = q.split()
        if any(_starts(t, _TYPE_STEMS_N) for t in tokens):
            rest = [t for t in tokens if not _starts(t, _TYPE_STEMS_N)]
            if _only_about_unit(rest) and (lst := _list_answer(tokens)):
                return lst
            # "Mühendislik fakültesi var mı?" gibi listede olmayan bir ad
            named = re.search(rf"((?:\w+ ){{1,3}})(?:{_TYPE_RE})\w*\s+(?:{'|'.join(EXISTENCE)})", q)
            if named:
                words = [w for w in named.group(1).split() if w not in FILLER]
                if words:
                    similar = [u["ad"] for u in load_units() if any(w in _norm(u["ad"]) for w in words)]
                    text = "Selçuk Üniversitesi'nin resmî akademik birimler listesinde bu adla bir birim bulamadım."
                    if similar:
                        text += "\n\nBenzer adlı birimler:\n" + "\n".join(f"• {n}" for n in similar[:5])
                    return f"{text}\n\n{SOURCE}"
        return None

    unit, (start, end) = found
    rest = (q[:start] + " " + q[end:]).split()
    if not rest or not _only_about_unit(rest):
        return None  # yalnızca birim adı yazılmışsa ya da başka bir şey soruluyorsa belgelere bırak
    location = any(_starts(t, LOCATION) for t in rest)
    contact = any(_starts(t, CONTACT) for t in rest)
    if any(_starts(t, EXISTENCE) for t in rest) and not (location or contact):
        head = f"Evet, Selçuk Üniversitesi'nde *{unit['ad']}* bulunuyor. İletişim bilgileri:"
    elif location:
        head = f"*{unit['ad']}* için elimdeki bilgiler:"
    else:
        head = f"*{unit['ad']}* iletişim bilgileri:"
    body = format_unit(unit, location=location) or "Doğrulanmış iletişim bilgisi yok; üniversitenin web sitesine bakabilirsin."
    return f"{head}\n{body}\n\n{SOURCE}"
