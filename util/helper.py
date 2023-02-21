import re

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import CallbackContext

import config
from util.regex import FOOTER

MSG_REMOVAL_PERIOD = 1200
CHAT_ID = "chat_id"
MSG_ID = "msg_id"


def get_replies(bot_data, msg_id: str):
    print("Trying to get bot_data ------------------")
    print(bot_data)
    print("-------------------------")

    if "reply" in bot_data[msg_id]:
        print(bot_data[str(bot_data[msg_id]["reply"])])
        return bot_data[str(bot_data[msg_id]["reply"])]["langs"]

    return None


def sanitize_text(text: str = None) -> str:
    if text is None:
        return ""

    return re.sub(FOOTER, "", text)


def sanitize_hashtag(lang_key: str, text: str) -> str:
    if lang_key == "fa":
        result = text.replace(' ', '_')
    else:
        result = text.replace(' ', '')

    return result.replace('-', '').replace('.', '').replace("'", "")


def get_caption(update: Update):
    if update.channel_post.caption is not None:
        return update.channel_post.caption

    return ""


async def get_file(update: Update):
    if len(update.channel_post.photo) > 0:
        return await update.channel_post.photo[-1].get_file()
    elif update.channel_post.video is not None:
        return await update.channel_post.video.get_file()
    elif update.channel_post.animation is not None:
        return await update.channel_post.animation.get_file()


async def delete(context: CallbackContext):
    await context.bot.delete_message(context.job.data[CHAT_ID], context.job.data[MSG_ID])


async def reply_html(update: Update, context: CallbackContext, file_name: str):
    try:
        await update.message.delete()
    except TelegramError as e:
        print("needs admin:", e)
        pass

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
        pass


async def reply_photo(update: Update, context: CallbackContext, file_name: str):
    await update.message.delete()

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
            f"<b>⚠️ Error when trying to read html-file {file_name}</b>\n<code>{e}</code>\n\n"
            f"<b>Caused by Update</b>\n<code>{update}</code>",
        )
        pass
