"""Anonim kullanım kaydı (KPI ölçümü için).

KVKK: Kullanıcı kimliği, adı, kullanıcı adı veya konumu KAYDEDİLMEZ.
Yalnızca zaman, yanıt süresi, yanıtlanıp yanıtlanmadığı ve kaba kategori tutulur.
Aktif kullanıcı sayımı için Telegram ID'si günlük tuzla tek yönlü özetlenir (geri çözülemez).
"""
import hashlib
import json
import os
import time
from datetime import date

from app.config import get_settings

_SALT = os.environ.get("STATS_SALT", "degistir-beni")


def anon_user(user_id: int | str | None) -> str | None:
    if user_id is None:
        return None
    raw = f"{_SALT}:{date.today().isoformat()}:{user_id}".encode()
    return hashlib.sha256(raw).hexdigest()[:16]


def log_event(*, kind: str, latency_ms: int, answered: bool, user: str | None = None) -> None:
    path = get_settings().stats_file
    path.parent.mkdir(parents=True, exist_ok=True)
    rec = {"ts": int(time.time()), "kind": kind, "latency_ms": latency_ms, "answered": answered, "u": user}
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def summary() -> dict:
    path = get_settings().stats_file
    if not path.exists():
        return {"toplam_soru": 0}
    recs = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not recs:
        return {"toplam_soru": 0}
    lat = sorted(r["latency_ms"] for r in recs)
    return {
        "toplam_soru": len(recs),
        "yanitlanan_orani": round(sum(r["answered"] for r in recs) / len(recs), 3),
        "ort_yanit_ms": round(sum(lat) / len(lat)),
        "p95_yanit_ms": lat[int(len(lat) * 0.95) - 1] if len(lat) > 1 else lat[0],
        "gunluk_tekil_kullanici_toplami": len({(r["u"], r["ts"] // 86400) for r in recs if r.get("u")}),
    }
