import logging

from telegram import ParseMode  #upm package(python-telegram-bot)
from telegram.ext import Updater, MessageHandler, Filters, Defaults  #upm package(python-telegram-bot)

import config
from messages import flag_to_hashtag, post_channel_english, breaking_news,announcement
from meme import post_channel_meme
import re

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    updater = Updater(config.TOKEN,
                      defaults=Defaults(parse_mode=ParseMode.HTML))
    dp = updater.dispatcher

    dp.add_handler(
        MessageHandler(
            Filters.update.channel_post &
            (Filters.photo | Filters.video | Filters.animation)
            & Filters.chat(chat_id=config.CHANNEL_MEME), post_channel_meme))

    dp.add_handler(
        MessageHandler(
            Filters.update.channel_post &
            (Filters.photo | Filters.video | Filters.animation)
            & Filters.chat(chat_id=config.CHANNEL_DE), post_channel_english))

    dp.add_handler(
        MessageHandler(
            Filters.update.channel_post & Filters.text
            & Filters.regex(re.compile(r"#eilmeldung", re.IGNORECASE)),
            breaking_news))

    dp.add_handler(
        MessageHandler(
            Filters.update.channel_post & Filters.text
            & Filters.regex(re.compile(r"#mitteilung", re.IGNORECASE)),
            announcement))

    dp.add_handler(MessageHandler(Filters.chat(config.ADMINS),
                                  flag_to_hashtag))

    # Commands have to be added above
    # dp.add_error_handler(error)  # comment this one out for full stacktrace

    updater.start_polling()
    updater.idle()
