import asyncio
import logging
import re
from collections import defaultdict
from typing import DefaultDict

from telegram import Update, Message
from telegram.error import TelegramError
from telegram.ext import CallbackContext

from channel.common import handle_url
from data.db import query_replies, insert_single2, update_text, get_msg_id
from data.lang import LANGUAGES, GERMAN
from settings.config import DIVIDER
from social.twitter import tweet_text
from util.helper import sanitize_text, log_error
from util.patterns import WHITESPACE, HASHTAG, FLAG_EMOJI
from util.translation import translate_message, flag_to_hashtag, segment_text

from util.dictionary import replace_name

# See channel/common.py's _live_captions/_post_locks/EDIT_DEBOUNCE_SECONDS for why these
# exist: a text post also goes through a per-language translation loop that can take a
# while, and needs to (a) pick up edits that arrive mid-loop instead of publishing the
# stale text captured at the start, (b) not race an edit's writes against that loop's
# writes to the same language channel message, and (c) collapse a quick burst of edits
# into a single translation pass instead of one per edit.
_live_texts: dict[int, str] = {}
_post_locks: DefaultDict[int, asyncio.Lock] = defaultdict(asyncio.Lock)
EDIT_DEBOUNCE_SECONDS = 3


async def post_channel_text(update: Update, context: CallbackContext):
    text = sanitize_text(update.channel_post.text_html_urled)

    await insert_single2(update.channel_post)

    logging.info(f"original caption::: {text}", )

    try:
        text_ger = flag_to_hashtag(replace_name(text))
    except Exception as e:
        await log_error("format German text", context, GERMAN, e, update, )
        text_ger = text

    # Add the German footer immediately, before the (potentially slow) per-language
    # translation loop below, instead of waiting for every other language to be posted.
    try:
        if FLAG_EMOJI.search(text):
            text_ger += DIVIDER + GERMAN.footer
        await update.channel_post.edit_text(text_ger)
    except TelegramError as e:
        if not e.message.startswith("Message is not modified"):
            await log_error("send text", context, GERMAN, e, update, )

    try:
        await tweet_text(segment_text(text_ger))
    except Exception as e:
        await log_error("tweet text DE", context, "Twitter", e, update, )

    _live_texts[update.channel_post.id] = text
    try:
        for lang in LANGUAGES:
            reply_id = await query_replies(update.channel_post.message_id, lang.lang_key)

            current_text = _live_texts.get(update.channel_post.id, text)

            try:
                async with _post_locks[update.channel_post.id]:
                    msg: Message = await context.bot.send_message(
                        chat_id=lang.channel_id,
                        text=f"{await translate_message(lang.lang_key, current_text, lang.lang_key_deepl, lang_username=lang.username)}{DIVIDER}{lang.footer}",
                        reply_to_message_id=reply_id
                    )
                    await insert_single2(msg, lang.lang_key)
            except Exception as e:
                await log_error("send text", context, lang, e, update, )

            try:
                await tweet_text(segment_text(text_ger), lang.lang_key)
            except Exception as e:
                await log_error(f"tweet text {lang.lang_key}", context, "Twitter", e, update, )
    finally:
        _live_texts.pop(update.channel_post.id, None)

    await handle_url(update, context)  # TODO: maybe extend to breaking and media_group


async def edit_channel_text(update: Update, context: CallbackContext):
    """Debounce entry point: collapse a quick burst of edits into a single translation pass."""
    job_name = f"edit-text-{update.edited_channel_post.id}"

    for job in context.job_queue.get_jobs_by_name(job_name):
        job.schedule_removal()

    context.job_queue.run_once(_apply_channel_edit_text, EDIT_DEBOUNCE_SECONDS, data=update, name=job_name)


async def _apply_channel_edit_text(context: CallbackContext):
    update: Update = context.job.data
    text = replace_name(re.sub(
        WHITESPACE,
        "",
        re.sub(
            HASHTAG,
            "",
            update.edited_channel_post.text_html_urled.replace(GERMAN.footer, ""),
        ),
    ))

    text_ger = flag_to_hashtag(text)
    if FLAG_EMOJI.search(text):
        text_ger += DIVIDER + GERMAN.footer

    if update.edited_channel_post.id in _live_texts:
        _live_texts[update.edited_channel_post.id] = text
        logging.info(
            f"Post {update.edited_channel_post.id} is still being distributed; "
            "queued text update for remaining languages"
        )

    await update_text(update.edited_channel_post.id, text_ger)

    logging.info(f"original caption::: {text}", )

    for lang in LANGUAGES:
        async with _post_locks[update.edited_channel_post.id]:
            try:
                translated_text = f"{await translate_message(lang.lang_key, text, lang.lang_key_deepl, lang_username=lang.username)}{DIVIDER}{lang.footer}"
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
