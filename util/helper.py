import logging
import re
from typing import Final

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import CallbackContext

import config
from data.lang import GERMAN

MSG_REMOVAL_PERIOD: Final[int] = 1200
CHAT_ID: Final[str] = "chat_id"
MSG_ID: Final[str] = "msg_id"


def sanitize_text(text: str = None) -> str:
    return "" if text is None else re.sub(GERMAN.footer, "", text)


def sanitize_hashtag(lang_key: str, text: str) -> str:
    return (
        text.replace(' ', '_' if lang_key in {"fa", "ar"} else '')
        .replace('-', '')
        .replace('.', '')
        .replace("'", "")
    )


def get_caption(update: Update):
    if update.channel_post.caption is not None:
        return update.channel_post.caption_html_urled

    return ""


async def get_file(update: Update):
    if update.channel_post.photo:
        return await update.channel_post.photo[-1].get_file()
    elif update.channel_post.video:
        return await update.channel_post.video.get_file()
    elif update.channel_post.animation:
        return await update.channel_post.animation.get_file()


async def delete(context: CallbackContext):
    await context.bot.delete_message(context.job.data[CHAT_ID], context.job.data[MSG_ID])


async def yreply_html(update: Update, context: CallbackContext, file_name: str):
    try:
        await update.message.delete()
    except TelegramError as e:
        logging.info(f"needs admin: {e}")

    try:
        with open(f"res/de/{file_name}.html", "r", encoding='utf-8') as f:
            text = f.read()

        if update.message.reply_to_message is not None:
            # if update.message.reply_to_message.from_user.first_name == "Telegram":

            msg = await update.message.reply_to_message.reply_text(text)
        #   else:
        #       msg = await update.message.reply_text(text)
        else:
            msg = await context.bot.send_message(update.message.chat_id, text)

        context.job_queue.run_once(delete, MSG_REMOVAL_PERIOD, {CHAT_ID: msg.chat_id, MSG_ID: msg.message_id})

    except Exception as e:
        await context.bot.send_message(
            config.LOG_GROUP,
            f"<b>⚠️ Error when trying to read html-file {file_name}</b>\n<code>{e}</code>\n\n"
            f"<b>Caused by Update</b>\n<code>{update}</code>",
        )


async def reply_photo(update: Update, context: CallbackContext, file_name: str):
    try:
        await update.message.delete()
    except TelegramError as e:
        logging.info(f"needs admin: {e}")

    try:
        with open(f"res/img/{file_name}", "rb") as f:
            if update.message.reply_to_message is not None:
                msg = await update.message.reply_to_message.reply_photo(f)
            else:
                msg = await context.bot.send_photo(update.message.chat_id, f)

            context.job_queue.run_once(delete, MSG_REMOVAL_PERIOD, msg.chat_id, str(msg.message_id))

    except Exception as e:
        await context.bot.send_message(
            config.LOG_GROUP,
            f"<b>⚠️ Error when trying to read photo {file_name}</b>\n<code>{e}</code>\n\n"
            f"<b>Caused by Update</b>\n<code>{update}</code>",
        )
