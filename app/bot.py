"""Telegram botu (python-telegram-bot v21). FastAPI'deki /ask uç noktasını çağırır.

    python -m app.bot
"""
import logging

import httpx
from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

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


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(WELCOME, parse_mode=ParseMode.MARKDOWN)


async def takvim(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    evs = takvim.upcoming()
    if not evs:
        await update.message.reply_text("Takvimde yaklaşan bir tarih bulamadım.")
        return
    text = "*Yaklaşan tarihler*\n" + "\n".join(takvim.format_event(e) for e in evs)
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def handle_question(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    question = update.message.text
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)  # "yazıyor…"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"{get_settings().api_url}/ask",
                json={"question": question, "user_id": str(update.effective_user.id)},
            )
            r.raise_for_status()
            data = r.json()
    except Exception:
        log.exception("API hatası")
        await update.message.reply_text("Şu an yanıt veremiyorum, birazdan tekrar dener misin? 🙏")
        return

    text = data["answer"]
    if data.get("sources"):
        text += "\n\n📄 *Kaynak:* " + "; ".join(data["sources"])
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
    app.add_handler(CommandHandler("takvim", takvim))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question))
    log.info("Bot çalışıyor…")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
