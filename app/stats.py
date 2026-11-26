"""Anonim kullanım kaydı (KPI ölçümü için).

KVKK: Kullanıcı kimliği, adı, kullanıcı adı veya konumu KAYDEDİLMEZ.
Yalnızca zaman, yanıt süresi, yanıtlanıp yanıtlanmadığı ve kaba kategori tutulur.
Aktif kullanıcı sayımı için Telegram ID'si günlük tuzla tek yönlü özetlenir.

Tuz her gün bellekte rastgele üretilir; dosyaya, .env'ye ya da loga YAZILMAZ ve gün değişince
atılır. Böylece ekip dahil hiç kimse bilinen bir ID'nin özetini yeniden hesaplayıp kayıtlarla
eşleştiremez (Silme, Yok Etme veya Anonim Hale Getirme Yönetmeliği m.10). Bedeli: Program aynı gün
yeniden başlatılırsa o günün kullanıcıları bir kez daha sayılabilir.
"""
import hashlib
import hmac
import json
import secrets
import threading
import time
from datetime import date

from app.config import get_settings

_salt_lock = threading.Lock()
_salt: dict = {"day": None, "value": b""}


def _daily_salt(today: date | None = None) -> bytes:
    today = today or date.today()
    with _salt_lock:
        if _salt["day"] != today:
            _salt["day"], _salt["value"] = today, secrets.token_bytes(32)  # eski tuz unutulur
        return _salt["value"]


def anon_user(user_id: int | str | None, today: date | None = None) -> str | None:
    if user_id is None:
        return None
    return hmac.new(_daily_salt(today), str(user_id).encode(), hashlib.sha256).hexdigest()[:16]


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
