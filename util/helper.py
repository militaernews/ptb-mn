import re

from telegram import Update

from util.regex import FOOTER


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
    result = text

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
