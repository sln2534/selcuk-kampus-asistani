"""Kişisel veri ön filtresi (KVKK).

Mesajda T.C. kimlik numarası, telefon, e-posta, IBAN ya da öğrenci numarası gibi kişisel veri
varsa mesaj Gemini'ye (yurt dışındaki üçüncü tarafa) hiç gönderilmez ve öğrenci uyarılır.
Mesajın kendisi hiçbir yere kaydedilmez; istatistiğe yalnızca "kisisel_veri" türü yazılır.

Kasıtlı olarak geniş tutuldu: yanlışlıkla bir soruyu engellemek, kişisel verinin Google'a
gitmesinden daha az zararlı.
"""
import re

PATTERNS: dict[str, re.Pattern] = {
    "T.C. kimlik numarası": re.compile(r"(?<!\d)[1-9]\d{10}(?!\d)"),
    "telefon numarası": re.compile(r"(?<!\d)(?:\+?90[\s-]?)?0?5\d{2}[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}(?!\d)"),
    "e-posta adresi": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    "IBAN": re.compile(r"\bTR\s?\d{2}(?:\s?\d{4}){5}\s?\d{2}\b", re.IGNORECASE),
    "öğrenci numarası": re.compile(r"(?<!\d)\d{9}(?!\d)"),
}


def find_personal_data(text: str) -> list[str]:
    """Mesajda bulunan kişisel veri türlerini döndürür (boş liste = temiz)."""
    return [name for name, pattern in PATTERNS.items() if pattern.search(text)]


def warning(kinds: list[str]) -> str:
    return (
        f"🔒 Mesajında kişisel bilgi var gibi görünüyor ({', '.join(kinds)}). "
        "Güvenliğin için bu mesajı yapay zekâya göndermedim ve hiçbir yere kaydetmedim.\n\n"
        "Sorunu kişisel bilgi olmadan tekrar yazar mısın? Örneğin: "
        "_Kayıt dondurma şartları nelerdir?_"
    )
