from telegram import Update
from telegram.ext import ContextTypes

from config import CHANNEL_SUGGEST
from util.translation import translate


async def suggest_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    translated_text = await translate("de", update.channel_post.caption_html_urled, )

    await update.channel_post.copy(chat_id=CHANNEL_SUGGEST, caption=translated_text)