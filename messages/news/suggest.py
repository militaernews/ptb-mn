from asyncio import get_event_loop
from typing import Final, List

from regex import sub
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, MessageOrigin
from telegram.ext import Application, MessageHandler, filters, CallbackContext

from config import CHANNEL_SUGGEST, CHANNEL_BACKUP
from data.db import get_suggested_sources
from util.translation import translate


def debloat_text(text: str) -> str:
    cleaned = sub(r'(https?)://[^\s/$.?#].[^\s]*|@[^\s]+$', '', text)
    cleaned = sub(r'#\w+\s*$', '', cleaned)
    cleaned = sub(r'.{,30}$', '', cleaned)
    return cleaned


async def suggest_single(update: Update, context: CallbackContext):
    if update.channel_post.forward_origin is None:
        return

    source: MessageOrigin = update.channel_post.forward_origin

    debloated = debloat_text(update.channel_post.caption_html)

    if 200 > len(debloated) > 900:
        return

    translated_text = await translate("de", debloated, "de")

    original_button = "🔗 Original" if update.channel_post.media_group_id is None else "🖼 Album"

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(
                original_button,
                url=f"{source.chat.ink}/{source.message_id}",
            ),

                InlineKeyboardButton(
                    "💾 Backup", url=update.channel_post.link
                ),
            ]
        ]
    )
    await update.channel_post.copy(chat_id=CHANNEL_SUGGEST, caption=translated_text, reply_markup=keyboard)


def register_suggest(app: Application):
    SUGGESTED_SOURCES: Final[List[int]] = get_event_loop().run_until_complete(get_suggested_sources())
    app.add_handler(MessageHandler(
        filters.Chat(CHANNEL_BACKUP) & filters.FORWARDED & filters.CAPTION & filters.ForwardedFrom(SUGGESTED_SOURCES),
        suggest_single))
