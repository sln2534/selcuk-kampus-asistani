"""Cevap önbelleği.

Belgeden başarıyla verilmiş cevaplar saklanır; aynı soru tekrar sorulursa Gemini'ye gidilmeden
hafızadan verilir. Böylece Google tarafındaki yoğunluk, daha önce cevaplanmış soruları etkilemez.

Güvenlik kuralları:
* Yalnızca belgeden verilmiş (answered=True) cevaplar saklanır; "bulamadım" ve hata cevapları saklanmaz.
* Belgeler yeniden indekslenince (`python -m app.rag.ingest`) önbellek silinir.
* Sistem talimatı (SYSTEM_PROMPT) değişirse eski kayıtlar kendiliğinden geçersiz sayılır.
* `.env` içinde CACHE_ENABLED=false ile tamamen kapatılabilir.
* Kullanıcıya dair hiçbir bilgi saklanmaz; yalnızca soru metni ve cevap.
"""
import hashlib
import json
import re
import threading

from app.config import get_settings

_lock = threading.Lock()
_data: dict | None = None


def _norm(question: str) -> str:
    q = question.replace("İ", "i").replace("I", "ı").lower()
    q = re.sub(r"[^\w\s]", " ", q)
    return re.sub(r"\s+", " ", q).strip()


def _prompt_version() -> str:
    from app.rag.answer import SYSTEM_PROMPT

    return hashlib.sha256(SYSTEM_PROMPT.encode("utf-8")).hexdigest()[:12]


def _load() -> dict:
    global _data
    if _data is None:
        path = get_settings().cache_file
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            loaded = {}
        if loaded.get("prompt_version") != _prompt_version():
            loaded = {"prompt_version": _prompt_version(), "entries": {}}
        _data = loaded
    return _data


def _save() -> None:
    path = get_settings().cache_file
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(_data, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(path)


def get(question: str) -> dict | None:
    if not get_settings().cache_enabled:
        return None
    with _lock:
        return _load()["entries"].get(_norm(question))


def put(question: str, answer: str, sources: list[str]) -> None:
    if not get_settings().cache_enabled:
        return
    with _lock:
        _load()["entries"][_norm(question)] = {"answer": answer, "sources": sources}
        _save()


def clear() -> None:
    global _data
    with _lock:
        _data = None
        get_settings().cache_file.unlink(missing_ok=True)
