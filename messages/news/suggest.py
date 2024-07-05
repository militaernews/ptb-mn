from regex import sub
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, Application, MessageHandler, filters

from config import CHANNEL_SUGGEST, CHANNEL_BACKUP
from util.translation import translate


def debloat_text(text: str) -> str:
    cleaned = sub(r'(https?)://[^\s/$.?#].[^\s]*|@[^\s]+$', '', text)
    cleaned = sub(r'#\w+\s*$', '', cleaned)
    cleaned  = sub(r'.{,40}$', '', cleaned)
    return cleaned

async def suggest_single(update: Update, context: ContextTypes.DEFAULT_TYPE):

    debloated = debloat_text(update.channel_post.caption_html)

    if 200 > len(debloated) > 900:
        return

    translated_text = await translate("de", debloated, "de")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 Quelle", url=update.channel_post.link)]])
    await update.channel_post.copy(chat_id=CHANNEL_SUGGEST, caption=translated_text, reply_markup=keyboard)

def register_suggest(app:Application):
    app.add_handler(MessageHandler(filters.Chat(CHANNEL_BACKUP) & filters.CAPTION & filters.FORWARDED & filters.ForwardedFrom(), suggest_single))