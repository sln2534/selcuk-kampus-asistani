"""FastAPI servisi.

    uvicorn app.api:app --reload
"""
import logging
import re
import time

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app import cache, privacy, stats, takvim
from app.config import get_settings
from app.rag.answer import answer_question, small_talk_reply

log = logging.getLogger("api")

app = FastAPI(title="Selçuk Kampüs Asistanı API", version="0.1.0")

DISCLAIMER = "ℹ️ Öğrenci projesidir, resmî değildir. Kesin bilgi için Öğrenci İşleri'ne danışın."

# Basit prompt-injection ön filtresi. Asıl koruma sistem prompt'undadır; bu yalnızca bariz denemeleri keser.
INJECTION_PATTERNS = [
    r"(önceki|yukarıdaki|tüm)\s+(talimat|kural)\w*\s+(unut|yok say|görmezden)",
    r"(ignore|forget)\s+(all\s+|the\s+|your\s+)?(previous\s+|above\s+)?(instructions|rules)",
    r"system prompt",
    r"sistem (prompt|talimat)\w*\s*(göster|yaz|ver)",
    r"you are now|artık sen bir|\bsen artık\b",
    r"\byeni\s+kural\s*:",
    r"(yukarıdaki|önceki)\s+(ilk\s+)?mesaj\w*\s+(tekrar|yaz|göster)",
    r"(api\s*(anahtar|key)|\.env|gizli\s+(talimat|kural|anahtar))\w*\s*(göster|yaz|ver|söyle)",
    r"admin\s+modu|güvenlik\s+filtre\w*\s*(kapat|devre\s+dışı)",
]


class AskRequest(BaseModel):
    question: str = Field(..., min_length=2)
    user_id: str | None = None  # yalnızca anonim sayım için; saklanmaz


class AskResponse(BaseModel):
    answer: str
    sources: list[str] = []
    answered: bool
    kind: str
    latency_ms: int
    cached: bool = False


def looks_like_injection(q: str) -> bool:
    ql = q.lower()
    return any(re.search(p, ql) for p in INJECTION_PATTERNS)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/stats")
def get_stats():
    return stats.summary()


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    s = get_settings()
    q = req.question.strip()
    if len(q) > s.max_question_len:
        raise HTTPException(400, f"Soru en fazla {s.max_question_len} karakter olabilir.")

    start = time.perf_counter()
    sources: list[str] = []
    cached = False
    if found := privacy.find_personal_data(q):
        kind, answered = "kisisel_veri", False
        text = privacy.warning(found)
    elif looks_like_injection(q):
        kind, answered = "guvenlik", False
        text = "Bu isteğe yardımcı olamam. Üniversiteyle ilgili bir soru sorabilirsin. 😊"
    elif (chat := small_talk_reply(q)) is not None:
        kind, answered, text = "sohbet", True, chat
    elif (cal := takvim.answer_date_question(q)) is not None:
        kind, answered, text = "takvim", True, cal
    elif (hit := cache.get(q)) is not None:
        kind, answered, text, sources, cached = "rag", True, hit["answer"], hit["sources"], True
    else:
        try:
            res = answer_question(q)
            kind, answered, text, sources = "rag", res.answered, res.text, res.sources
            if res.answered:
                cache.put(q, text, sources)
        except Exception:
            log.exception("RAG yanıtı üretilemedi")
            kind, answered = "hata", False
            text = "Şu an yapay zekâ servisine ulaşamıyorum. Birkaç dakika sonra tekrar dener misin? 🙏"

    latency = int((time.perf_counter() - start) * 1000)
    stats.log_event(kind=kind, latency_ms=latency, answered=answered, user=stats.anon_user(req.user_id))
    return AskResponse(answer=text, sources=sources, answered=answered, kind=kind, latency_ms=latency, cached=cached)
