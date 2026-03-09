"""
Suggest pipeline: forward posts from whitelisted source channels to the
suggest channel for editorial review.

Changes (Issue #6):
- Persist every forwarded post in the suggest_posts DB table so that
  duplicates are rejected across bot restarts.
- Handle edited channel posts: if the source message is edited, update
  the corresponding message in the suggest channel.
"""

import logging
from asyncio import get_event_loop
from typing import Final, List

from regex import sub
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    MessageOrigin,
    Message,
)
from telegram.error import TelegramError
from telegram.ext import Application, MessageHandler, filters, CallbackContext

from data.db import (
    get_suggested_sources,
    suggest_is_posted,
    suggest_insert,
    suggest_get_message_id,
    suggest_update_text,
)
from settings.config import CHANNEL_SUGGEST, CHANNEL_BACKUP
from util.translation import translate


def debloat_text(text: str) -> str:
    cleaned = sub(r'(https?)://[^\s/$.?#].[^\s]*|@[^\s]+$', '', text)
    cleaned = sub(r'#\w+\s*$', '', cleaned)
    cleaned = sub(r'.{,30}$', '', cleaned)
    return cleaned


def _build_keyboard(source: MessageOrigin, backup_link: str, is_album: bool) -> InlineKeyboardMarkup:
    original_button = "🖼 Album" if is_album else "🔗 Original"
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(original_button, url=f"{source.chat.link}/{source.message_id}"),
                InlineKeyboardButton("💾 Backup", url=backup_link),
            ]
        ]
    )


async def suggest_single(update: Update, _: CallbackContext):
    """Handle a new forwarded post in the backup channel."""
    post: Message = update.channel_post

    if post.forward_origin is None:
        return

    source: MessageOrigin = post.forward_origin
    source_channel_id: int = source.chat.id
    source_message_id: int = source.message_id

    # Duplicate check — skip if already forwarded to suggest channel
    if await suggest_is_posted(source_channel_id, source_message_id):
        logging.info(
            f"[suggest] Skipping duplicate: channel={source_channel_id} msg={source_message_id}"
        )
        return

    debloated = debloat_text(post.caption_html)
    if 200 > len(debloated) > 900:
        return

    translated_text = await translate("de", debloated, "de")
    keyboard = _build_keyboard(source, post.link, is_album=post.media_group_id is not None)

    sent: Message = await post.copy(
        chat_id=CHANNEL_SUGGEST,
        caption=translated_text,
        reply_markup=keyboard,
    )

    # Persist so we can deduplicate and propagate edits later
    await suggest_insert(
        source_channel_id=source_channel_id,
        source_message_id=source_message_id,
        suggest_message_id=sent.message_id,
        text=translated_text,
    )
    logging.info(
        f"[suggest] Forwarded: channel={source_channel_id} msg={source_message_id} "
        f"-> suggest msg={sent.message_id}"
    )


async def suggest_edit(update: Update, context: CallbackContext):
    """Handle an edited post in the backup channel and update the suggest channel."""
    post: Message = update.edited_channel_post

    if post.forward_origin is None or post.caption_html is None:
        return

    source: MessageOrigin = post.forward_origin
    source_channel_id: int = source.chat.id
    source_message_id: int = source.message_id

    suggest_msg_id = await suggest_get_message_id(source_channel_id, source_message_id)
    if suggest_msg_id is None:
        # Not yet in the suggest channel — nothing to update
        return

    debloated = debloat_text(post.caption_html)
    translated_text = await translate("de", debloated, "de")
    keyboard = _build_keyboard(source, post.link, is_album=post.media_group_id is not None)

    try:
        await context.bot.edit_message_caption(
            chat_id=CHANNEL_SUGGEST,
            message_id=suggest_msg_id,
            caption=translated_text,
            reply_markup=keyboard,
        )
        await suggest_update_text(source_channel_id, source_message_id, translated_text)
        logging.info(
            f"[suggest] Updated: channel={source_channel_id} msg={source_message_id} "
            f"-> suggest msg={suggest_msg_id}"
        )
    except TelegramError as e:
        if not e.message.startswith("Message is not modified"):
            logging.error(f"[suggest] Failed to edit suggest message {suggest_msg_id}: {e}")


def register_suggest(app: Application):
    SUGGESTED_SOURCES: Final[List[int]] = get_event_loop().run_until_complete(get_suggested_sources())

    app.add_handler(MessageHandler(
        filters.Chat(CHANNEL_BACKUP) & filters.FORWARDED & filters.CAPTION & filters.ForwardedFrom(SUGGESTED_SOURCES),
        suggest_single,
    ))

    app.add_handler(MessageHandler(
        filters.UpdateType.EDITED_CHANNEL_POST & filters.Chat(CHANNEL_BACKUP) & filters.CAPTION,
        suggest_edit,
    ))
