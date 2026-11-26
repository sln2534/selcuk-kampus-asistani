"""Telegram botu (python-telegram-bot v21). FastAPI'deki /ask uç noktasını çağırır.

    python -m app.bot

KVKK: Kullanıcı aydınlatma metnini "Okudum, onaylıyorum" düğmesiyle onaylamadan hiçbir sorusu
işlenmez (API'ye ve Gemini'ye gitmez). Onay yalnızca botun belleğinde (user_data) tutulur, diske
yazılmaz; bot yeniden başlatılınca kullanıcıdan onay tekrar istenir. /onayiptal ile geri alınır.
"""
import logging

import httpx
from functools import wraps

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, LinkPreviewOptions, Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from app import takvim
from app.api import DISCLAIMER
from app.config import get_settings

logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)  # token'ın loglara düşmemesi için
log = logging.getLogger("bot")

WELCOME = (
    "Merhaba! 👋 Ben *Selçuk Kampüs Asistanı*.\n\n"
    "Akademik takvim, sınav ve mazeret kuralları, burs, yurt, yemekhane gibi konularda "
    "sorularını doğal dille yazabilirsin. Yanıtlarımı resmî belgelere dayandırır ve kaynağını gösteririm.\n\n"
    "Örnek: _Mazeret sınavına nasıl başvururum?_\n\n"
    "Komutlar: /takvim · /yardim\n\n" + DISCLAIMER
)


CONSENT_KEY = "kvkk_onay"
CONSENT_CALLBACK = "kvkk_onay"
KVKK_URL = "https://github.com/sln2534/selcuk-kampus-asistani/blob/main/docs/KVKK.md"
CONSENT_TEXT = (
    "🔒 *Kişisel verilerin korunması*\n\n"
    "Asistanı kullanmadan önce aydınlatma metnini okuyup onaylaman gerekiyor. Kısaca:\n"
    "• Adın, kullanıcı adın, telefonun ve konumun kaydedilmez.\n"
    "• Soruların cevap üretmek için Google Gemini'ye (yurt dışındaki sunuculara) gönderilir. "
    "Kişisel bilgi (TC kimlik, telefon, e-posta vb.) içeren mesajlar gönderilmez.\n"
    "• Kullanım istatistikleri anonim tutulur.\n\n"
    f"Metnin tamamı: {KVKK_URL}\n\n"
    "Onayını istediğin zaman /onayiptal ile geri alabilirsin."
)
CONSENT_BUTTON = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Okudum, onaylıyorum", callback_data=CONSENT_CALLBACK)]])


def has_consent(ctx: ContextTypes.DEFAULT_TYPE) -> bool:
    return bool(ctx.user_data.get(CONSENT_KEY))


async def ask_consent(update: Update) -> None:
    await update.effective_message.reply_text(
        CONSENT_TEXT, parse_mode=ParseMode.MARKDOWN, reply_markup=CONSENT_BUTTON,
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )


def requires_consent(handler):
    """Onay verilmemişse soruyu işlemez, onay ister."""

    @wraps(handler)
    async def wrapper(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        if not has_consent(ctx):
            await ask_consent(update)
            return
        await handler(update, ctx)

    return wrapper


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not has_consent(ctx):
        await ask_consent(update)
        return
    await update.message.reply_text(WELCOME, parse_mode=ParseMode.MARKDOWN)


async def consent_given(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    ctx.user_data[CONSENT_KEY] = True
    await query.answer("Teşekkürler!")
    await query.edit_message_reply_markup(reply_markup=None)  # düğme tekrar basılmasın
    await query.message.reply_text(WELCOME, parse_mode=ParseMode.MARKDOWN)


async def revoke_consent(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    ctx.user_data.pop(CONSENT_KEY, None)
    await update.message.reply_text(
        "Onayın geri alındı; artık sorularını işlemeyeceğim. Tekrar kullanmak istersen /start yazabilirsin."
    )


@requires_consent
async def takvim_komutu(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    evs = takvim.upcoming()
    if not evs:
        await update.message.reply_text("Takvimde yaklaşan bir tarih bulamadım.")
        return
    text = "*Yaklaşan tarihler*\n" + "\n".join(takvim.format_event(e) for e in evs)
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


def client_error_message(status_code: int, detail: object) -> str:
    """API'nin 4xx cevabını öğrencinin anlayacağı bir mesaja çevirir."""
    if status_code == 400 and isinstance(detail, str) and "karakter" in detail:
        return f"✂️ Mesajın çok uzun. {detail} Sorunu kısaltıp tekrar yazar mısın?"
    return "Sorunu tam anlayamadım. Biraz daha açık yazar mısın? 🙂"


@requires_consent
async def handle_question(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    question = update.message.text
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)  # "yazıyor…"
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            r = await client.post(
                f"{get_settings().api_url}/ask",
                json={"question": question, "user_id": str(update.effective_user.id)},
            )
            if 400 <= r.status_code < 500:
                await update.message.reply_text(client_error_message(r.status_code, r.json().get("detail")))
                return
            r.raise_for_status()
            data = r.json()
    except Exception:
        log.exception("API hatası")
        await update.message.reply_text("Şu an yanıt veremiyorum, birazdan tekrar dener misin? 🙏")
        return

    text = data["answer"]
    if data.get("sources"):
        # Dosya adlarındaki _ işaretleri Telegram'da eğik yazıya dönüşmesin diye kaçırılır.
        text += "\n\n📄 *Kaynak:* " + "; ".join(src.replace("_", "\\_") for src in data["sources"])
    try:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    except Exception:  # model çıktısında bozuk Markdown olursa düz metin gönder
        await update.message.reply_text(text)


def main() -> None:
    token = get_settings().telegram_bot_token
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN tanımlı değil (.env dosyasına bakın).")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler(["yardim", "help"], start))
    app.add_handler(CommandHandler("takvim", takvim_komutu))
    app.add_handler(CommandHandler("onayiptal", revoke_consent))
    app.add_handler(CallbackQueryHandler(consent_given, pattern=f"^{CONSENT_CALLBACK}$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question))
    log.info("Bot çalışıyor…")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
