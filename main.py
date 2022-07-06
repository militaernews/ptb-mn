import logging
import os
import re

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from telegram import ParseMode
from telegram.ext import Updater, MessageHandler, Filters, Defaults

import config
from admin import join_member
from log import report_error
from meme import post_channel_meme
from messages import post_channel_english, breaking_news, announcement, edit_channel
from postgres import PostgresPersistence
from testing import flag_to_hashtag_test

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def start_session() -> scoped_session:
    """Start the database session."""
    engine = create_engine(os.environ["DATABASE_URL"].replace("postgres", "postgresql", 1), client_encoding="utf8")
    return scoped_session(sessionmaker(bind=engine, autoflush=False))


if __name__ == "__main__":
    session = start_session()

    updater = Updater(os.environ["TELEGRAM"],
                      persistence=PostgresPersistence(session),
                      defaults=Defaults(parse_mode=ParseMode.HTML,
                                        disable_web_page_preview=True))
    dp = updater.dispatcher

    dp.add_handler(
        MessageHandler(
            Filters.status_update.new_chat_members
            & Filters.chat(
                chat_id=[config.LOG_GROUP]),  # config.CHAT_DE, config.CHAT_DE
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
            Filters.update.edited_channel_post &
            (Filters.photo | Filters.video | Filters.animation)
            & Filters.chat(chat_id=config.CHANNEL_DE), edit_channel))

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
  #  dp.add_error_handler( report_error)  # comment this one out for full stacktrace

    updater.start_webhook(
        "0.0.0.0",
        int(os.environ["PORT"]),
        os.environ["TELEGRAM"],
        webhook_url=f"https://ptb-mn.herokuapp.com/{os.environ['TELEGRAM']}",
    )
    updater.idle()
