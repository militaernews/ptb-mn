import logging
import re

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from telegram.constants import ParseMode
from telegram.ext import MessageHandler, Defaults, ApplicationBuilder, filters, CommandHandler

from config import TEST_MODE, TOKEN, PORT, DATABASE_URL, CHANNEL_MEME, ADMINS
from data.lang import GERMAN
from data.postgres import PostgresPersistence
from dev.playground import flag_to_hashtag_test
from messages.bingo import bingo_field
from messages.chat import unwarn_user, ban_user, filter_message, warn_user, report_user, commands, maps, donbas
from messages.meme import post_media_meme, post_text_meme
from messages.news import edit_channel_text, announcement, breaking_news, edit_channel, post_channel_text, \
    post_channel_english, post_info

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def start_session() -> scoped_session:
    """Start the database session."""
    engine = create_engine(DATABASE_URL, client_encoding="utf8")
    return scoped_session(sessionmaker(bind=engine, autoflush=False))


if __name__ == "__main__":
    session = start_session()

    app = ApplicationBuilder().token(TOKEN).defaults(Defaults(parse_mode=ParseMode.HTML, disable_web_page_preview=True)) \
        .persistence(PostgresPersistence(url=DATABASE_URL, session=session)).build()

    app.add_handler(CommandHandler("bingo", bingo_field, filters.User(ADMINS)))
    #  app.add_handler(MessageHandler(filters.ATTACHMENT & filters.Chat(ADMINS), private_setup))
    app.add_handler(MessageHandler(filters.Chat(ADMINS), flag_to_hashtag_test))


    app.add_handler(
        MessageHandler(
            filters.UpdateType.CHANNEL_POST &
            (filters.PHOTO | filters.VIDEO | filters.ANIMATION)
            & filters.Chat(chat_id=CHANNEL_MEME), post_media_meme))
    app.add_handler(
        MessageHandler(filters.UpdateType.CHANNEL_POST & filters.TEXT & filters.Chat(chat_id=CHANNEL_MEME),
                       post_text_meme))

    app.add_handler(
        MessageHandler(
            filters.UpdateType.CHANNEL_POST & (
                    filters.PHOTO | filters.VIDEO | filters.ANIMATION) & filters.CaptionRegex(
                re.compile(r"#info", re.IGNORECASE)) & filters.Chat(chat_id=GERMAN.channel_id),
            post_info))

    app.add_handler(MessageHandler(
        filters.UpdateType.CHANNEL_POST &
        (filters.PHOTO | filters.VIDEO | filters.ANIMATION)
        & filters.Chat(chat_id=GERMAN.channel_id), post_channel_english))
    app.add_handler(MessageHandler(
        filters.UpdateType.EDITED_CHANNEL_POST &
        (filters.PHOTO | filters.VIDEO | filters.ANIMATION)
        & filters.Chat(chat_id=GERMAN.channel_id), edit_channel))

    app.add_handler(
        MessageHandler(
            filters.UpdateType.CHANNEL_POST & filters.TEXT & filters.Chat(chat_id=GERMAN.channel_id) & filters.Regex(
                re.compile(r"#eilmeldung", re.IGNORECASE)),
            breaking_news))
    app.add_handler(
        MessageHandler(
            filters.UpdateType.CHANNEL_POST & filters.TEXT & filters.Chat(chat_id=GERMAN.channel_id) & filters.Regex(
                re.compile(r"#mitteilung", re.IGNORECASE)),
            announcement))
    app.add_handler(
        MessageHandler(
            filters.UpdateType.CHANNEL_POST & filters.TEXT & filters.Chat(chat_id=GERMAN.channel_id),
            post_channel_text))
    app.add_handler(
        MessageHandler(filters.UpdateType.EDITED_CHANNEL_POST & filters.TEXT & filters.Chat(
            chat_id=GERMAN.channel_id) & ~filters.CaptionRegex(
            re.compile(r"🔰 MN-Hauptquartier", re.IGNORECASE)),
                       edit_channel_text))

    app.add_handler(CommandHandler("maps",maps, filters.Chat(GERMAN.chat_id)))
    app.add_handler(CommandHandler("donbas", donbas, filters.Chat(GERMAN.chat_id)))
    app.add_handler(CommandHandler("help", commands, filters.Chat(GERMAN.chat_id)))

    app.add_handler(MessageHandler(
        filters.UpdateType.MESSAGE & filters.TEXT & filters.Chat(GERMAN.chat_id) & ~filters.User(ADMINS),
        filter_message))
    app.add_handler(CommandHandler("warn", warn_user, filters.Chat(GERMAN.chat_id)))
    app.add_handler(CommandHandler("unwarn", unwarn_user, filters.Chat(GERMAN.chat_id)))
    app.add_handler(CommandHandler("ban", ban_user, filters.Chat(GERMAN.chat_id)))
    app.add_handler(CommandHandler("report", report_user, filters.Chat(GERMAN.chat_id)))



    # Commands have to be added above
    #  app.add_error_handler( report_error)  # comment this one out for full stacktrace

    if TEST_MODE:
        print("---testing---")
        app.run_polling()
    else:
        app.run_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN,
                        webhook_url=f"https://web-production-5e05.up.railway.app/{TOKEN}")
        # webhook_url=f"https://ptb-mn.herokuapp.com/{TOKEN}")
