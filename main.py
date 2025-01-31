import logging
import re
from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy
from datetime import datetime
from os import makedirs, path
from sys import platform, version_info
from typing import Final

from telegram import LinkPreviewOptions
from telegram.constants import ParseMode
from telegram.ext import MessageHandler, Defaults, ApplicationBuilder, filters, CommandHandler, PicklePersistence, \
    Application

from config import TOKEN, ADMINS
from data.lang import GERMAN
from dev.playground import flag_to_hashtag_test
from messages.chat.bingo import register_bingo
from messages.chat.commands import register_commands
from messages.chat.management import register_management
from messages.chat.whitelist import register_whitelist
from messages.meme import register_meme
from messages.news.common import edit_channel, post_channel_english
from messages.news.special import breaking_news, announcement, post_info, advertisement
from messages.news.suggest import register_suggest
from messages.news.text import edit_channel_text, post_channel_text
from messages.private.advertisement import register_advertisement
from messages.private.promo import register_promo
from messages.private.setup import set_cmd
from util.patterns import ADVERTISEMENT_PATTERN, ANNOUNCEMENT_PATTERN, BREAKING_PATTERN, INFO_PATTERN


def add_logging():
    log_filename: Final[str] = rf"./logs/{datetime.now().strftime('%Y-%m-%d/%H-%M-%S')}.log"
    makedirs(path.dirname(log_filename), exist_ok=True)
    logging.basicConfig(
        format="%(asctime)s %(levelname)-5s %(funcName)-20s [%(filename)s:%(lineno)d]: %(message)s",
        encoding="utf-8",
        filename=log_filename,
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)


def register_news(app: Application):
    media = (filters.PHOTO | filters.VIDEO | filters.ANIMATION)
    news_post = filters.UpdateType.CHANNEL_POST & filters.Chat(chat_id=GERMAN.channel_id) & ~filters.FORWARDED

    app.add_handler(
        MessageHandler(news_post & media & filters.CaptionRegex(INFO_PATTERN), post_info))

    app.add_handler(MessageHandler(news_post & media, post_channel_english))

    app.add_handler(MessageHandler(news_post & filters.TEXT & filters.Regex(BREAKING_PATTERN),
                                   breaking_news))
    app.add_handler(MessageHandler(news_post & filters.TEXT & filters.Regex(ANNOUNCEMENT_PATTERN),
                                   announcement))
    app.add_handler(
        MessageHandler(news_post & filters.TEXT & filters.Regex(ADVERTISEMENT_PATTERN), advertisement))
    app.add_handler(MessageHandler(news_post & filters.TEXT, post_channel_text))

    news_edited = filters.UpdateType.EDITED_CHANNEL_POST & filters.Chat(
        chat_id=GERMAN.channel_id) & ~filters.CaptionRegex(
        re.compile(r"🔰 MN-Hauptquartier|#\S+|MN-Team", re.IGNORECASE))

    app.add_handler(MessageHandler(news_edited & media, edit_channel))
    app.add_handler(MessageHandler(news_edited & filters.TEXT, edit_channel_text))


if __name__ == "__main__":
    add_logging()

    if version_info >= (3, 8) and platform.lower().startswith("win"):
        set_event_loop_policy(WindowsSelectorEventLoopPolicy())

    app = (ApplicationBuilder().token(TOKEN)
           .defaults(Defaults(parse_mode=ParseMode.HTML, link_preview_options=LinkPreviewOptions(is_disabled=True)))
           .persistence(PicklePersistence(filepath="persistence"))
           .read_timeout(50).get_updates_read_timeout(50)
           .build())

    app.add_handler(CommandHandler("set_cmd", set_cmd, filters.Chat(ADMINS)))
    app.add_handler(MessageHandler(filters.Chat(ADMINS), flag_to_hashtag_test))

    register_news(app)
    register_suggest(app)
    register_advertisement(app)
    register_promo(app)

    register_meme(app)
    register_bingo(app)

    register_commands(app)
    register_management(app)
    #   register_captcha(app)

    register_whitelist(app)

    # Commands have to be added above
    #  app.add_error_handler( report_error)  # comment this one out for full stacktrace

    print("### RUNNING LOCAL ###")

    app.run_polling(poll_interval=1, drop_pending_updates=False)
