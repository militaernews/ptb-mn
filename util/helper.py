import re

from telegram import Update
from telegram.ext import CallbackContext

from util.regex import FOOTER


def get_replies(bot_data, msg_id: str):
    print("Trying to get bot_data ------------------")
    print(bot_data)
    print("-------------------------")

    if "reply" in bot_data[msg_id]:
        print(bot_data[bot_data[msg_id]["reply"]])
        return bot_data[bot_data[msg_id]["reply"]]["langs"]

    return None


def sanitize_text(text: str = None) -> str:
    if text is None:
        return ""

    return re.sub(FOOTER, "", text)


def sanitize_hashtag(text: str) -> str:
    return text.replace(' ', '_').replace('-', '').replace('.', '').replace("'", "")


def get_file_id(update: Update):
    if update.channel_post.photo is not None:
        return update.channel_post.photo[-1].file_id
    elif update.channel_post.video is not None:
        return update.channel_post.video.file_id
    elif update.channel_post.animation is not None:
        return update.channel_post.animation.file_id


def get_caption(update: Update):
    if update.channel_post.caption is not None:
        return update.channel_post.caption

    return ""


async def get_file(update: Update, context: CallbackContext):
    return await context.bot.get_file(get_file_id(update))
