from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from config import CHANNEL_SUGGEST
from util.translation import translate


async def suggest_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    translated_text = await translate("de", update.channel_post.caption_html_urled, "de")

    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Posten", switch_inline_query="share")],
                                     [InlineKeyboardButton("🔗 Quelle", url=update.channel_post.link)]])
    await update.channel_post.copy(chat_id=CHANNEL_SUGGEST, caption=translated_text, reply_markup=keyboard)
