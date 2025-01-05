import logging
import os
from typing import Optional

import telegram
from dotenv import load_dotenv
from lxml.html import fromstring
from pytwitter import Api
from telegram.ext import CallbackContext

from data.db import Post
from data.lang import ENGLISH

load_dotenv()


def create_instance(consumer_key: str, consumer_secret: str, access_token: str, access_secret: str, bearer_token: str):
    api = Api(
        consumer_key,
        consumer_secret,
        access_token,
        access_secret,
    )
    return api


api_DE = create_instance(
    os.getenv("CONSUMER_KEY_DE"),
    os.getenv("CONSUMER_SECRET_DE"),
    os.getenv("ACCESS_KEY_DE"),
    os.getenv("ACCESS_SECRET_DE"),
    os.getenv("BEARER_DE"),
)

api_EN = create_instance(
    os.getenv("CONSUMER_KEY_EN"),
    os.getenv("CONSUMER_SECRET_EN"),
    os.getenv("ACCESS_KEY_EN"),
    os.getenv("ACCESS_SECRET_EN"),
    os.getenv("BEARER_EN"),
)

ACTIVE = False
TWEET_LENGTH = 280


def supply_twitter_instance(lang_key: Optional[str] = None) -> Optional[Api]:
    if not ACTIVE:
        return None
    clients = {
        ENGLISH.lang_key: api_EN,
        None:api_DE
    }
    return clients.get(lang_key)


def upload_media(files, api: Api):
    return [api.upload_media_simple(file).media_id for file in files]


def create_tweet(text: str, api: Api, media_ids=None, ):
    text = fromstring(text).text_content().strip()
    try:
        api.create_tweet(text=text.replace("\n", " ").replace("  ", " ")[:TWEET_LENGTH], media_media_ids=media_ids)
    except Exception as e:
        logging.error(f"Error when trying to post to twitter: {e}\n\ntext: {text}\n\nmedia_ids: {media_ids}")


async def tweet_file(caption: str, file: telegram.File, lang_key: Optional[str] = None):
    instance = supply_twitter_instance(lang_key)
    if instance is None:
        return
    client, api = instance

    path = file.file_path.split('/')[-1]
    await file.download_to_drive(path)
    media_ids = upload_media([path], api)
    create_tweet(caption, client, media_ids)
    os.remove(path)


async def tweet_file_3(caption: str, path: str, lang_key: Optional[str] = None):
    instance = supply_twitter_instance(lang_key)
    if instance is None:
        return
    client, api = instance

    with open(path, "rb") as media:
        media_id = api.upload_media_simple(media=media).media_id
    create_tweet(caption, client, [media_id])


async def tweet_files(context: CallbackContext, caption: str, posts: [Post], lang_key: Optional[str] = None):
    instance = supply_twitter_instance(lang_key)
    if instance is None:
        return
    client, api = instance

    upload_files = []
    for post in posts:
        file = await context.bot.get_file(post.file_id)
        path = file.file_path.split('/')[-1]
        await file.download_to_drive(path)
        upload_files.append(path)

    media_ids = upload_media(upload_files, api)
    create_tweet(caption, client, media_ids)
    for path in upload_files:
        os.remove(path)


async def tweet_text(text: str, lang_key: Optional[str] = None):
    instance = supply_twitter_instance(lang_key)
    if instance is None:
        return
    client, api = instance

    create_tweet(text, client)
