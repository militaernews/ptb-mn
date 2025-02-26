import logging
import re
from typing import Final
from datetime import datetime
from os import path, makedirs, environ

from pip._internal.utils import subprocess
from telegram import LinkPreviewOptions
from telegram.constants import ParseMode
from telegram.ext import MessageHandler, Defaults, ApplicationBuilder, filters, CommandHandler, PicklePersistence, \
    Application

from bot.channel.common import edit_channel, post_channel_english
from bot.channel.meme import register_meme
from bot.channel.special import breaking_news, announcement, post_info, advertisement
from bot.channel.suggest import register_suggest
from bot.channel.text import edit_channel_text, post_channel_text

from bot.data.lang import GERMAN
from bot.group.bingo import register_bingo
from bot.group.commands import register_commands
from bot.group.management import register_management
from bot.group.whitelist import register_whitelist
from bot.private.advertisement import register_advertisement
from bot.private.promo import register_promo
from bot.private.setup import set_cmd
from bot.settings.config import ADMINS, TOKEN, CONTAINER
from bot.util.patterns import ADVERTISEMENT_PATTERN, ANNOUNCEMENT_PATTERN, BREAKING_PATTERN, INFO_PATTERN


def add_logging():
    if CONTAINER:
        logging.basicConfig(
            format="%(asctime)s %(levelname)-5s %(funcName)-20s [%(filename)s:%(lineno)d]: %(message)s",
            encoding="utf-8",

            level=logging.INFO,
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.StreamHandler(),
           #     logging.FileHandler('logs/bot.log')
            ]
        )

    else:
        log_filename: Final[str] = rf"./logs/{datetime.now().strftime('%Y-%m-%d/%H-%M-%S')}.log"
        makedirs(path.dirname(log_filename), exist_ok=True)
        logging.basicConfig(
            format="%(asctime)s %(levelname)-5s %(funcName)-20s [%(filename)s:%(lineno)d]: %(message)s",
            encoding="utf-8",
            filename=log_filename,
            level=logging.INFO,
            datefmt='%Y-%m-%d %H:%M:%S',
        )

    logging.getLogger("httpx").setLevel(logging.WARNING)


def register_news(application: Application):
    media = (filters.PHOTO | filters.VIDEO | filters.ANIMATION)
    news_post = filters.UpdateType.CHANNEL_POST & filters.Chat(chat_id=GERMAN.channel_id) & ~filters.FORWARDED

    application.add_handler(
        MessageHandler(news_post & media & filters.CaptionRegex(INFO_PATTERN), post_info))

    application.add_handler(MessageHandler(news_post & media, post_channel_english))

    application.add_handler(MessageHandler(news_post & filters.TEXT & filters.Regex(BREAKING_PATTERN),
                                           breaking_news))
    application.add_handler(MessageHandler(news_post & filters.TEXT & filters.Regex(ANNOUNCEMENT_PATTERN),
                                           announcement))
    application.add_handler(
        MessageHandler(news_post & filters.TEXT & filters.Regex(ADVERTISEMENT_PATTERN), advertisement))
    application.add_handler(MessageHandler(news_post & filters.TEXT, post_channel_text))

    news_edited = filters.UpdateType.EDITED_CHANNEL_POST & filters.Chat(
        chat_id=GERMAN.channel_id) & ~filters.CaptionRegex(
        re.compile(r"🔰 MN-Hauptquartier|#\S+|MN-Team", re.IGNORECASE))

    application.add_handler(MessageHandler(news_edited & media, edit_channel))
    application.add_handler(MessageHandler(news_edited & filters.TEXT, edit_channel_text))

def main():
    #    if version_info >= (3, 8) and platform.lower().startswith("win"):
    #      set_event_loop_policy(WindowsSelectorEventLoopPolicy())

    application = (ApplicationBuilder().token(TOKEN)
                   .defaults(
        Defaults(parse_mode=ParseMode.HTML, link_preview_options=LinkPreviewOptions(is_disabled=True)))
                   .persistence(PicklePersistence(filepath="../../persistence"))
                   .read_timeout(50).get_updates_read_timeout(50)
                   .build())

    application.add_handler(CommandHandler("set_cmd", set_cmd, filters.Chat(ADMINS)))

    register_news(application)
    register_suggest(application)
    register_advertisement(application)
    register_promo(application)

    register_meme(application)
    register_bingo(application)

    register_commands(application)
    register_management(application)
    #   register_captcha(application)

    register_whitelist(application)

    # Commands have to be added above
    #  application.add_error_handler( report_error)  # comment this one out for full stacktrace

    print("### RUNNING LOCAL ###")
    logging.info("### RUNNING LOCAL ###")

    application.run_polling(poll_interval=1, drop_pending_updates=False)

if __name__ == "__main__":
    add_logging()

    main()

