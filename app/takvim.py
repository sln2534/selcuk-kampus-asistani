"""Akademik takvim modülü.

Tarih soruları LLM'e gönderilmez; doğrudan data/takvim.json'dan yanıtlanır
(yanlış/uydurma tarih riskini ortadan kaldırmak için).
"""
import json
from datetime import date
from functools import lru_cache

from app.config import get_settings

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


def _fmt(d: str) -> str:
    return date.fromisoformat(d).strftime("%d.%m.%Y")


def format_event(ev: dict) -> str:
    when = _fmt(ev["baslangic"])
    if ev.get("bitis") and ev["bitis"] != ev["baslangic"]:
        when += f" – {_fmt(ev['bitis'])}"
    return f"📅 *{ev['ad']}*: {when}"


def upcoming(today: date | None = None, limit: int = 5) -> list[dict]:
    today = today or date.today()
    evs = [e for e in load_calendar()["etkinlikler"] if date.fromisoformat(e.get("bitis") or e["baslangic"]) >= today]
    return sorted(evs, key=lambda e: e["baslangic"])[:limit]


def answer_date_question(question: str) -> str | None:
    """Takvimde eşleşme varsa yanıt metni, yoksa None döner."""
    if not is_date_question(question):
        return None
    events = find_events(question)
    if not events:
        return None
    cal = load_calendar()
    body = "\n".join(format_event(e) for e in events)
    return f"{body}\n\n_Kaynak: {cal['kaynak']}_"
