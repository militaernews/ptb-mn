from telegram import ParseMode  #upm package(python-telegram-bot)
from telegram.ext import Updater, MessageHandler, Filters, Defaults  #upm package(python-telegram-bot)
import os
from messages import post_channel_english, breaking_news, announcement
from meme import post_channel_meme
from admin import join_member
from testing import flag_to_hashtag_test
import re
import config
from log import report_error

if __name__ == "__main__":
    updater = Updater(os.environ["TELEGRAM"],
                      defaults=Defaults(parse_mode=ParseMode.HTML,
                                        disable_web_page_preview=True))
    dp = updater.dispatcher

    dp.add_handler(
        MessageHandler(
            Filters.status_update.new_chat_members
            & Filters.chat(
                chat_id=[config.LOG_GROUP]),  #config.CHAT_DE, config.CHAT_DE
            join_member))

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

    dp.add_handler(
        MessageHandler(Filters.chat(config.ADMINS), flag_to_hashtag_test))

    # Commands have to be added above
    #   dp.add_error_handler(
    #       report_error)  # comment this one out for full stacktrace

    updater.start_polling()
    updater.idle()
