"""Akademik takvim modülü.

Tarih soruları LLM'e gönderilmez; doğrudan data/takvim.json'dan yanıtlanır
(yanlış/uydurma tarih riskini ortadan kaldırmak için).
"""
import json
import logging
import re
from datetime import date
from functools import lru_cache

from app.config import get_settings

log = logging.getLogger(__name__)

# Genel takvimden farklı takvimi olan programlar: dosya adı -> (görünen ad, sorudaki işaret kelimeleri)
SPECIAL_PROGRAMS = {
    "tip": ("Tıp Fakültesi", ["tıp"]),
    "dis_hekimligi": ("Diş Hekimliği Fakültesi", ["diş hekimliği", "diş"]),
    "hukuk": ("Hukuk Fakültesi", ["hukuk"]),
    "veteriner": ("Veteriner Fakültesi", ["veteriner", "veterinerlik"]),
    "hazirlik": ("Yabancı Diller Hazırlık", ["hazırlık"]),
}

DATE_WORDS = ("ne zaman", "hangi tarih", "tarihi", "kaçında", "kacinda", "son gün", "takvim", "başlıyor", "bitiyor")


def _norm(text: str) -> str:
    return text.replace("İ", "i").replace("I", "ı").lower()


@lru_cache
def load_calendar() -> dict:
    with open(get_settings().calendar_file, encoding="utf-8") as f:
        return json.load(f)


def is_date_question(question: str) -> bool:
    q = _norm(question)
    return any(w in q for w in DATE_WORDS)


def find_events(question: str) -> list[dict]:
    q = _norm(question)
    hits = []
    for ev in load_calendar()["etkinlikler"]:
        if any(_norm(kw) in q for kw in ev["anahtar_kelimeler"]):
            hits.append(ev)
    return hits


_FOLD = str.maketrans("çğıöşüâî", "cgiosuai")


def _tokens(text: str) -> list[str]:
    return re.findall(r"\w+", _norm(text).translate(_FOLD))


def detect_program(question: str) -> str | None:
    """Soruda Tıp, Hukuk gibi ayrı takvimi olan bir program geçiyorsa dosya adını döndürür.

    Burada harfler sadeleştirilmez: "diş" ile "dış" karışmasın. Kısa işaretler ("tıp", "diş")
    tam kelime olmalı ("tıpkı" eşleşmez); uzunlar kelime başı olabilir ("hukuk" -> "hukukçu").
    """
    words = re.findall(r"\w+", _norm(question))
    for key, (_, markers) in SPECIAL_PROGRAMS.items():
        for m in markers:
            mt = re.findall(r"\w+", _norm(m))
            for i in range(len(words) - len(mt) + 1):
                if all(words[i + j] == t or (len(t) > 3 and words[i + j].startswith(t)) for j, t in enumerate(mt)):
                    return key
    return None


@lru_cache
def load_special(key: str) -> dict | None:
    """Programın özel takvimini yükler; dosya yoksa ya da bozuksa None (genel takvime düşmez)."""
    path = get_settings().special_calendar_dir / f"{key}.json"
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data.get("etkinlikler"), list)
        return data
    except Exception as e:  # bozuk ya da eksik dosya
        log.warning("Özel takvim okunamadı (%s): %s", path.name, e)
        return None


def _keyword_matches(question_words: list[str], keyword: str, ignore: set[str]) -> bool:
    """Anahtar kelimedeki her kelime (program adı hariç) soruda bir kelimenin başı olarak geçmeli.
    "final" -> "finalleri" eşleşir; tek harfli kelimeler ("I" gibi) tam eşleşmeli."""
    kw = [t for t in _tokens(keyword) if t not in ignore]
    if not kw:
        return False
    for t in kw:
        if len(t) <= 2:
            if t not in question_words:
                return False
        elif not any(w.startswith(t) for w in question_words):
            return False
    return True


def _special_answer(question: str, key: str) -> str:
    name = SPECIAL_PROGRAMS[key][0]
    cal = load_special(key)
    if cal:
        # Program adı ve "tarihleri", "ne zaman" gibi soru kalıpları anahtar kelimede zorunlu değil:
        # "hukuk vize tarihleri" anahtarı "Hukukta vize ne zaman?" sorusuyla da eşleşsin.
        ignore = {t for m in SPECIAL_PROGRAMS[key][1] for t in _tokens(m)} | {
            "fakultesi", "fakulte", "tarih", "tarihi", "tarihleri", "takvim", "takvimi", "ne", "zaman",
        }
        words = _tokens(question)
        hits = [
            ev for ev in cal["etkinlikler"]
            if ev.get("baslangic") and any(_keyword_matches(words, kw, ignore) for kw in ev.get("anahtar_kelimeler", []))
        ]
        # "Tıp 5. sınıf" / "dönem 5" gibi bir sınıf numarası varsa yalnızca o dönemin etkinlikleri
        roman = {"1": "I", "2": "II", "3": "III", "4": "IV", "5": "V", "6": "VI"}
        wanted = {roman[w] for w in words if w in roman}
        if wanted and any(set(e.get("donemler") or []) & wanted for e in hits):
            hits = [e for e in hits if set(e.get("donemler") or []) & wanted]
        if hits:
            source = cal.get("kaynak")
            if isinstance(source, dict):
                source = source.get("belge")
            body = "\n".join(format_event(e) for e in hits[:8])
            return f"{body}\n\n_Kaynak: {source or name + ' akademik takvimi'}_"
    return (
        f"📌 *{name}* genel akademik takvimden farklı bir takvim uyguluyor. "
        "Sorduğun tarihi elimdeki takvimde bulamadım, yanlış tarih vermek istemem. 🙏\n\n"
        "Fakültenin resmî akademik takvimine ya da öğrenci işlerine bakmanı öneririm."
    )


def _fmt(d: str) -> str:
    return date.fromisoformat(d).strftime("%d.%m.%Y")


def format_event(ev: dict) -> str:
    title = ev.get("ad") or ev.get("etkinlik") or "Etkinlik"
    when = _fmt(ev["baslangic"])
    if ev.get("bitis") and ev["bitis"] != ev["baslangic"]:
        when += f" – {_fmt(ev['bitis'])}"
    extra = []
    semester = ev.get("yariyil") or ev.get("donem")  # dosyalar farklı alan adı kullanıyor
    if semester and str(semester).lower() in ("guz", "güz", "bahar", "yaz"):
        extra.append(str(semester).lower().replace("guz", "güz"))
    if ev.get("donemler"):
        extra.append("Dönem " + ", ".join(ev["donemler"]))
    suffix = f" ({'; '.join(extra)})" if extra else ""
    return f"📅 *{title}*{suffix}: {when}"


def upcoming(today: date | None = None, limit: int = 5) -> list[dict]:
    today = today or date.today()
    evs = [e for e in load_calendar()["etkinlikler"] if date.fromisoformat(e.get("bitis") or e["baslangic"]) >= today]
    return sorted(evs, key=lambda e: e["baslangic"])[:limit]


def answer_date_question(question: str) -> str | None:
    """Takvimde eşleşme varsa yanıt metni, yoksa None döner."""
    if not is_date_question(question):
        return None
    if (key := detect_program(question)) is not None:
        # Ayrı takvimi olan programa genel takvimin tarihini vermiyoruz.
        return _special_answer(question, key)
    events = find_events(question)
    if not events:
        return None
    cal = load_calendar()
    body = "\n".join(format_event(e) for e in events)
    return (
        f"{body}\n\n_Kaynak: {cal['kaynak']}_\n"
        "_Tıp, Diş Hekimliği, Hukuk, Veteriner ve Hazırlık'ın takvimi farklıdır; bunlar için fakülteni de yaz._"
    )
