import logging
import re
from typing import Final, Optional

from resvg_py import svg_to_bytes
from telegram import Update
from telegram.error import TelegramError
from telegram.ext import CallbackContext
from telegram.helpers import mention_html

from config import ADMINS, LOG_GROUP
from data.lang import GERMAN, Language

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
    if context.job.data is dict:
        data = context.job.data[CHAT_ID]

    else:
        data = context.job.data

    await context.bot.delete_message(data, data)


def remove_reply(func):
    async def wrapper(update: Update, context: CallbackContext, ):
        try:
            await update.message.delete()
        except TelegramError:
            logging.warning("Needs admin rights")
        if update.message.reply_to_message is None or update.message.reply_to_message.from_user.id in ADMINS:
            return

        await func(update, context)

    return wrapper


def remove(func):
    async def wrapper(update: Update, *args, **kwargs):
        try:
            await update.message.delete()
        except TelegramError:
            logging.warning("Needs admin rights")

        await func(update, *args, **kwargs)

    return wrapper


def admin_reply(func):
    async def wrapper(update: Update, *args, **kwargs):
        try:
            await update.message.delete()
        except TelegramError:
            logging.warning("Needs admin rights")

        if update.message.from_user.id not in ADMINS or update.message.reply_to_message is None or update.message.reply_to_message.from_user.id in ADMINS:
            return
        await func(update, *args, **kwargs)

    return wrapper


def admin(func):
    async def wrapper(update: Update, *args, **kwargs):
        try:
            await update.message.delete()
        except TelegramError:
            logging.warning("Needs admin rights")

        if update.message.from_user.id not in ADMINS:
            return
        await func(update, *args, **kwargs)

    return wrapper


@remove
async def reply_html(update: Update, context: CallbackContext, file_name: str, replacement: Optional[str] = None):
    try:
        with open(f"res/de/{file_name}.html", "r", encoding='utf-8') as f:
            text = f.read()

        if "{}" in text:
            text = re.sub(r"{}", replacement, text)

        if update.message.reply_to_message is not None:
            msg = await update.message.reply_to_message.reply_text(text)
        else:
            msg = await context.bot.send_message(update.message.chat_id, text)

        context.job_queue.run_once(delete, MSG_REMOVAL_PERIOD, {CHAT_ID: msg.chat_id, MSG_ID: msg.message_id})

    except Exception as e:
        logging.error(f"Couldn't read html-file {file_name}: {e}")
        await context.bot.send_message(
            LOG_GROUP,
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
            LOG_GROUP,
            f"<b>⚠️ Error when trying to read photo {file_name}</b>\n<code>{e}</code>\n\n"
            f"<b>Caused by Update</b>\n<code>{update}</code>",
        )


def export_svg(svg: str, filename: str):
    logging.info(svg)
    with open(filename, 'wb') as f:
        f.write(bytes(svg_to_bytes(svg_string=svg, dpi=300, font_dirs=["../res/fonts"])))


def mention(update: Update) -> str:
    return mention_html(update.message.reply_to_message.from_user.id,
                        update.message.reply_to_message.from_user.first_name)

async def log_error(action: str,context:CallbackContext,  lang:Language|str,e:Exception,update:Optional[Update]=None ,):
    if lang is Language:
        lang = lang.lang_key

    text =  f"<b>⚠️ Error when trying to {action} in Channel {lang}</b>\n<code>{e}</code>"

    if update is not None:
        text+=f"\n\n<b>Caused by Post</b>\n<code>{update.channel_post}</code>"

    await context.bot.send_message(LOG_GROUP,text)