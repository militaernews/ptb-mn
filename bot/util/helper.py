import logging
import re
import subprocess
from typing import Final, Optional

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import CallbackContext
from telegram.helpers import mention_html

from bot.data.db import PHOTO, VIDEO, ANIMATION
from bot.data.lang import GERMAN, Language
from bot.settings.config import LOG_GROUP, ADMINS, MSG_REMOVAL_PERIOD, RES_PATH

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


async def get_file_type(update: Update):
    if update.channel_post.photo:
        return PHOTO
    elif update.channel_post.video:
        return VIDEO
    elif update.channel_post.animation:
        return ANIMATION


def get_tg_file_id(update: Update):
    if update.channel_post.photo:
        return update.channel_post.photo[-1].file_id
    elif update.channel_post.video:
        return update.channel_post.video.file_id
    elif update.channel_post.animation:
        return update.channel_post.animation.file_id


async def delete(context: CallbackContext):
    if context.job.data is dict:
        data = context.job.data[CHAT_ID]

    else:
        data = context.job.data

    # try delete
    await context.bot.delete_message(data, data)


def remove_reply(func):
    async def wrapper(update: Update, context: CallbackContext, ):
        await delete_msg(update)
        if update.message.reply_to_message is None or update.message.reply_to_message.from_user.id in ADMINS:
            return

        await func(update, context)

    return wrapper


def remove(func):
    async def wrapper(update: Update, *args, **kwargs):
        await delete_msg(update)

        await func(update, *args, **kwargs)

    return wrapper


def admin_reply(func):
    async def wrapper(update: Update, *args, **kwargs):
        await delete_msg(update)

        if update.message.from_user.id not in ADMINS or update.message.reply_to_message.from_user.id in ADMINS:
            return
        await func(update, *args, **kwargs)

    return wrapper


def admin(func):
    async def wrapper(update: Update, *args, **kwargs):
        await delete_msg(update)

        if update.message.from_user.id not in ADMINS:
            return
        await func(update, *args, **kwargs)

    return wrapper


@remove
async def reply_html(update: Update, context: CallbackContext, file_name: str, replacement: Optional[str] = None):
    try:
        with open(f"{RES_PATH}/de/{file_name}.html", "r", encoding='utf-8') as f:
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
    await delete_msg(update)

    try:
        with open(f"{RES_PATH}/img/{file_name}", "rb") as f:
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

    input_filename = filename.replace(".png", ".svg")

    with open(input_filename, "w", encoding='utf-8') as f:
        f.write(svg)

    command = fr'./tools/resvg "{input_filename}" "{filename}" --skip-system-fonts --background "#000000" --dpi 300 --font-family "Arial" --use-fonts-dir "./res/fonts"'
    result = subprocess.run(command, stdout=subprocess.PIPE)

    logging.info(f"RESVG: {result.returncode} - result: {result}")


def mention(update: Update) -> str:
    return mention_html(update.message.reply_to_message.from_user.id,
                        update.message.reply_to_message.from_user.first_name)


async def log_error(action: str, context: CallbackContext, lang: Language | str, e: Exception,
                    update: Optional[Update] = None, ):
    logging.exception(e)
    if isinstance(lang, Language):
        lang = lang.lang_key

    text = f"<b>⚠️ Error when trying to {action} in Channel {lang}</b>\n\n<code>{e}</code>"

    if update is not None:
        text += f"\n\n<b>Caused by Post</b>\n<code>{repr(update.channel_post)}</code>"

    await context.bot.send_message(LOG_GROUP, text)


async def delete_msg(update: Update):
    try:
        await update.message.delete()
    except TelegramError as e:
        logging.warning(f"Needs admin rights: {e}")
    except Exception as e:
        logging.error(f"Error when trying to delete message: {e}")
