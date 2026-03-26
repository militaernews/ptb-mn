import logging
import re
from datetime import datetime
from os import path, makedirs
from typing import Final

from telegram import LinkPreviewOptions
from telegram.constants import ParseMode
from telegram.ext import MessageHandler, Defaults, ApplicationBuilder, filters, CommandHandler, PicklePersistence, \
    Application, ContextTypes

from channel.common import edit_channel, post_channel_english
from channel.meme import register_meme
from channel.special import breaking_news, announcement, post_info, advertisement
from channel.crawler import register_crawler
from channel.text import edit_channel_text, post_channel_text
from data.lang import GERMAN
from data.db import init_db
from private.advertisement import register_advertisement
from private.promo import register_promo
from private.setup import set_cmd
from util.media_handler import register_media_downloader
from settings.config import ADMINS, TOKEN, CONTAINER
from util.patterns import ADVERTISEMENT_PATTERN, ANNOUNCEMENT_PATTERN, BREAKING_PATTERN, INFO_PATTERN


def add_logging():
    if CONTAINER:
        logging.basicConfig(
            format="%(asctime)s %(levelname)-5s %(funcName)-20s [%(filename)s:%(lineno)d]: %(message)s",
            encoding="utf-8",
            level=logging.INFO,
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[logging.StreamHandler()]
        )
    else:
        log_filename: Final[str] = rf"../logs/{datetime.now().strftime('%Y-%m-%d/%H-%M-%S')}.log"
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
    """Register handlers for the core posting pipeline."""
    media = (filters.PHOTO | filters.VIDEO | filters.ANIMATION)
    news_post = filters.UpdateType.CHANNEL_POST & filters.Chat(chat_id=GERMAN.channel_id) & ~filters.FORWARDED

    # Handle posts with INFO pattern (special formatting)
    application.add_handler(
        MessageHandler(news_post & media & filters.CaptionRegex(INFO_PATTERN), post_info))

    # Handle media posts (photos/videos) - translate and post to other languages
    application.add_handler(MessageHandler(news_post & media, post_channel_english))

    # Handle breaking news posts
    application.add_handler(MessageHandler(news_post & filters.TEXT & filters.Regex(BREAKING_PATTERN),
                                           breaking_news))
    
    # Handle announcement posts
    application.add_handler(MessageHandler(news_post & filters.TEXT & filters.Regex(ANNOUNCEMENT_PATTERN),
                                           announcement))
    
    # Handle advertisement posts
    application.add_handler(
        MessageHandler(news_post & filters.TEXT & filters.Regex(ADVERTISEMENT_PATTERN), advertisement))
    
    # Handle regular text posts
    application.add_handler(MessageHandler(news_post & filters.TEXT, post_channel_text))

    # Handle edited posts - sync changes across language channels
    news_edited = filters.UpdateType.EDITED_CHANNEL_POST & filters.Chat(
        chat_id=GERMAN.channel_id) & ~filters.CaptionRegex(
        re.compile(r"🔰 MN-Hauptquartier|#\S+|MN-Team", re.IGNORECASE))

    application.add_handler(MessageHandler(news_edited & media, edit_channel))
    application.add_handler(MessageHandler(news_edited & filters.TEXT, edit_channel_text))


def main():
    application = (ApplicationBuilder().token(TOKEN)
                   .defaults(
        Defaults(parse_mode=ParseMode.HTML, link_preview_options=LinkPreviewOptions(is_disabled=True)))
              .persistence(PicklePersistence(filepath="persistence"))
                   .read_timeout(50).get_updates_read_timeout(50)
                   .build())

    # Admin command for setting up custom commands
    application.add_handler(CommandHandler("set_cmd", set_cmd, filters.Chat(ADMINS)))

    # Register core posting pipeline handlers
    register_news(application)
    
    # Register crawler for external sources
    register_crawler(application)
    
    # Register advertisement and promo handlers
    register_advertisement(application)
    register_promo(application)
    
    # Register meme posting handler
    register_meme(application)
    
    # Register media downloader for social media content
    register_media_downloader(application)

    # Error handler
    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        logging.error("Exception while handling an update:", exc_info=context.error)

    application.add_error_handler(error_handler)

    # Initialize database schema
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(init_db())
        else:
            loop.run_until_complete(init_db())
    except Exception as e:
        logging.error(f"Could not initialize database: {e}")

    logging.info("### PTB-MN (Posting Pipeline) RUNNING ###")

    application.run_polling(poll_interval=1, drop_pending_updates=False)


if __name__ == "__main__":
    add_logging()
    main()
