import base64
import logging
import os
from pathlib import Path
from typing import Optional, List, IO, Tuple

from dotenv import load_dotenv
from lxml.html import fromstring
from pytwitter import Api
from telegram import Update
from telegram.ext import CallbackContext, ContextTypes

from data.db import Post
from data.lang import ENGLISH, GERMAN
from twitter_uploader import TelegramTwitterTransfer

load_dotenv()


def create_instance(consumer_key: str, consumer_secret: str, access_token: str, access_secret: str) -> tuple[
    Api, TelegramTwitterTransfer]:
    api = Api(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        access_token=access_token,
        access_secret=access_secret
    )
    uploader = TelegramTwitterTransfer(api)
    return api, uploader


api_DE, uploader_DE = create_instance(
    os.getenv("CONSUMER_KEY_DE"),
    os.getenv("CONSUMER_SECRET_DE"),
    os.getenv("ACCESS_KEY_DE"),
    os.getenv("ACCESS_SECRET_DE"),
)

api_EN, uploader_EN = create_instance(
    os.getenv("CONSUMER_KEY_EN"),
    os.getenv("CONSUMER_SECRET_EN"),
    os.getenv("ACCESS_KEY_EN"),
    os.getenv("ACCESS_SECRET_EN"),
)

ACTIVE = True
TWEET_LENGTH = 280


def supply_twitter_instance(lang_key: Optional[str] = GERMAN.lang_key) -> Optional[Tuple[Api, TelegramTwitterTransfer]]:
    if not ACTIVE:
        return None
    clients = {
        ENGLISH.lang_key: (api_EN, uploader_EN),
        GERMAN.lang_key: (api_DE, uploader_DE)
    }
    return clients.get(lang_key)


def create_tweet(text: str, api: Api, media_ids=None, ):
    text = fromstring(text).text_content().strip()
    try:
        api.create_tweet(text=text.replace("\n", " ").replace("  ", " ")[:TWEET_LENGTH], media_media_ids=media_ids)
    except Exception as e:
        logging.error(f"Error when trying to post to twitter: {e}\n\ntext: {text}\n\nmedia_ids: {media_ids}")


async def tweet_file(update:Update, context:CallbackContext, caption: str, lang_key: Optional[str] = None, file_path: Optional[str] = None):
    instance = supply_twitter_instance(lang_key)
    print(instance)
    if instance is None:
        return

    api, uploader = instance

    if file_path is not None:
        media_id = uploader.upload_image(file_path)
    else:
        media_id = await uploader.transfer_to_twitter(update, context)

    print(media_id)
    create_tweet(caption, api,[ media_id])


def upload_media(files: List[IO], api: Api):
    return [
        api.upload_media_simple(media_data=base64.b64encode(file.read()).decode("utf-8")).media_id
        for file in files
    ]


# todo: migrate to uploader
async def tweet_files(context: ContextTypes.DEFAULT_TYPE, caption: str, posts: List, lang_key: Optional[str] = None):
    """Helper function to tweet multiple files with caption."""
    instance = supply_twitter_instance(lang_key)
    if instance is None:
        return

    api, uploader = instance
    transfer = TelegramTwitterTransfer(api)
    media_ids = []
    temp_files = []

    try:
        for post in posts:
            file = await context.bot.get_file(post.file_id)
            filename = file.file_path.split('/')[-1]
            filepath = Path(filename)

            await file.download_to_drive(str(filepath))
            temp_files.append(filepath)

            with open(filepath, 'rb') as media_file:
                media_type = TelegramTwitterTransfer.MEDIA_TYPES.get(filepath.suffix.lower(), 'video/mp4')
                media_id = transfer._upload_media(media_file, media_type)
                media_ids.append(media_id)

        # Create tweet with all media
        create_tweet(caption, api, media_ids)

    finally:
        # Cleanup temporary files
        for filepath in temp_files:
            if filepath.exists():
                filepath.unlink()


async def tweet_text(text: str, lang_key: Optional[str] = None):
    instance = supply_twitter_instance(lang_key)
    print(instance)
    if instance is None:
        return

    api, uploader = instance

    create_tweet(text, api)
