"""Birim yönlendirme tablosu ("bilmiyorum" akışı).

data/birimler.json içinde her birim için anahtar kelimeler ve iletişim bilgisi bulunur.
İletişim bilgileri yalnızca üniversitenin resmî web sitesinden alınmalıdır.
"""
import json
from functools import lru_cache

from app.config import get_settings


def _norm(text: str) -> str:
    return text.replace("İ", "i").replace("I", "ı").lower()


@lru_cache
def load_units() -> list[dict]:
    path = get_settings().units_file
    with open(path, encoding="utf-8") as f:
        return json.load(f)["birimler"]


_SOFTEN = {"k": "ğ", "t": "d", "p": "b", "ç": "c"}


def _matches(question: str, keyword: str) -> bool:
    """Anahtar kelime soruda geçiyor mu? Türkçe ünsüz yumuşamasını da hesaba katar
    (topluluk -> topluluğuna, kitap -> kitabı)."""
    if keyword in question:
        return True
    last = keyword[-1:]
    return last in _SOFTEN and len(keyword) >= 4 and (keyword[:-1] + _SOFTEN[last]) in question


def match(question: str) -> dict | None:
    """Soruyla en iyi eşleşen birimi döndürür; hiçbir anahtar kelime eşleşmezse None.

    Puan = eşleşen anahtar kelimelerin toplam uzunluğu. Böylece özel bir ifade ("erasmus")
    genel bir kelimeden ("not") daha ağır basar.
    """
    q = _norm(question)
    best, best_score = None, 0
    for u in load_units():
        score = sum(len(kw) for kw in map(_norm, u.get("anahtar_kelimeler", [])) if _matches(q, kw))
        if score > best_score:
            best, best_score = u, score
    return best


def route(question: str) -> dict:
    """match() ile aynı; eşleşme yoksa varsayılan birimi (Öğrenci İşleri) döndürür."""
    return match(question) or next(u for u in load_units() if u.get("varsayilan"))


def format_unit(unit: dict) -> str:
    contacts = [
        f"{label} {unit[key]}"
        for key, label in (("telefon", "☎️"), ("eposta", "✉️"), ("web", "🌐"), ("konum", "📍"))
        if unit.get(key)
    ]
    if not contacts:  # iletişim bilgisi henüz doğrulanmamış birim: boş liste gösterme
        return f"*{unit['ad']}* ile iletişime geçebilirsin. Güncel iletişim bilgilerine kurumun resmî web sitesinden ulaşabilirsin."
    return "\n".join([f"*{unit['ad']}* ile iletişime geçebilirsin:", *contacts])
