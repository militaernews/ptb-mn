import logging
import re

from telegram import Update, Message
from telegram.error import TelegramError
from telegram.ext import CallbackContext

from common import handle_url
from ..data.db import query_replies, insert_single2, update_text, get_msg_id
from ..data.lang import LANGUAGES, GERMAN
from ..settings.config import DIVIDER
from ..social.twitter import tweet_text
from ..util.helper import sanitize_text, log_error
from ..util.patterns import WHITESPACE, HASHTAG, FLAG_EMOJI
from ..util.translation import translate_message, flag_to_hashtag, segment_text


async def post_channel_text(update: Update, context: CallbackContext):
    original_caption = sanitize_text(update.channel_post.text_html_urled)

    await insert_single2(update.channel_post)

    logging.info(f"original caption::: {original_caption}", )

    text_ger = flag_to_hashtag(original_caption)

    for lang in LANGUAGES:
        reply_id = await query_replies(update.channel_post.message_id, lang.lang_key)

        try:
            msg: Message = await context.bot.send_message(
                chat_id=lang.channel_id,
                text=f"{await translate_message(lang.lang_key, original_caption, lang.lang_key_deepl)}{DIVIDER}{lang.footer}",
                reply_to_message_id=reply_id
            )
            await insert_single2(msg, lang.lang_key)
        except Exception as e:
            await log_error("send text", context, lang, e, update, )

        try:
            await tweet_text(segment_text(text_ger), lang.lang_key)
        except Exception as e:
            await log_error(f"tweet text {lang.lang_key}", context, "Twitter", e, update, )

    try:

        if len(re.findall(FLAG_EMOJI, text_ger)) == 0:
            text_ger += GERMAN.footer
        await update.channel_post.edit_text(text_ger)
    except TelegramError as e:
        if not e.message.startswith("Message is not modified"):
            await log_error("send text", context, GERMAN, e, update, )

    try:
        await tweet_text(segment_text(text_ger))
    except Exception as e:
        await log_error("tweet text DE", context, "Twitter", e, update, )
    await handle_url(update, context)  # TODO: maybe extend to breaking and media_group


async def edit_channel_text(update: Update, context: CallbackContext):
    original_caption = re.sub(
        WHITESPACE,
        "",
        re.sub(
            HASHTAG,
            "",
            update.edited_channel_post.text_html_urled.replace(GERMAN.footer, ""),
        ),
    )

    await update_text(update.edited_channel_post.id, f"{original_caption}{DIVIDER}{GERMAN.footer}")

    logging.info(f"original caption::: {original_caption}", )

    for lang in LANGUAGES:
        try:
            translated_text = f"{await translate_message(lang.lang_key, original_caption, lang.lang_key_deepl)}{DIVIDER}{lang.footer}"
            msg_id = await get_msg_id(update.edited_channel_post.id, lang.lang_key)
            await context.bot.edit_message_text(
                text=translated_text,
                chat_id=lang.channel_id,
                message_id=msg_id
            )

            await update_text(msg_id, translated_text, lang.lang_key)
        except TelegramError as e:
            if not e.message.startswith("Message is not modified"):
                await log_error("edit text", context, lang, e, update, )
