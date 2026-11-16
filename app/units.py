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


def route(question: str) -> dict:
    """Soruyla en çok anahtar kelime eşleşen birimi döndürür; yoksa varsayılanı."""
    q = _norm(question)
    units = load_units()
    best, best_score = None, 0
    for u in units:
        score = sum(1 for kw in u.get("anahtar_kelimeler", []) if _norm(kw) in q)
        if score > best_score:
            best, best_score = u, score
    if best is None:
        best = next(u for u in units if u.get("varsayilan"))
    return best


def format_unit(unit: dict) -> str:
    lines = [f"*{unit['ad']}* ile iletişime geçebilirsin:"]
    for key, label in (("telefon", "☎️"), ("eposta", "✉️"), ("web", "🌐"), ("konum", "📍")):
        if unit.get(key):
            lines.append(f"{label} {unit[key]}")
    return "\n".join(lines)
