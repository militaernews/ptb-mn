import logging
import os
from typing import Optional

import telegram
import tweepy as tweepy
from dotenv import load_dotenv
from lxml import html
from lxml.html import fromstring
from telegram import Update
from telegram.ext import CallbackContext
from tweepy import Client, API, OAuth1UserHandler

from data.db import Post
from util.helper import get_caption, get_file

load_dotenv()

consumer_key_DE = os.getenv("CONSUMER_KEY_DE")
consumer_secret_DE = os.getenv("CONSUMER_SECRET_DE")
access_token_DE = os.getenv("ACCESS_KEY_DE")
access_secret_DE = os.getenv("ACCESS_SECRET_DE")
bearer_DE = os.getenv("BEARER_DE")

client_DE = Client(
    consumer_key=consumer_key_DE,
    consumer_secret=consumer_secret_DE,
    access_token=access_token_DE,
    access_token_secret=access_secret_DE,
)
api_DE = API(OAuth1UserHandler(
    consumer_key=consumer_key_DE,
    consumer_secret=consumer_secret_DE,
    access_token=access_token_DE,
    access_token_secret=access_secret_DE,
))


consumer_key_EN = os.getenv("CONSUMER_KEY_EN")
consumer_secret_EN = os.getenv("CONSUMER_SECRET_EN")
access_token_EN = os.getenv("ACCESS_KEY_EN")
access_secret_EN = os.getenv("ACCESS_SECRET_EN")
bearer_EN = os.getenv("BEARER_EN")

client_EN = Client(
    consumer_key=consumer_key_EN,
    consumer_secret=consumer_secret_EN,
    access_token=access_token_EN,
    access_token_secret=access_secret_EN,
)
api_EN = API(OAuth1UserHandler(
    consumer_key=consumer_key_EN,
    consumer_secret=consumer_secret_EN,
    access_token=access_token_EN,
    access_token_secret=access_secret_EN,
))

ACTIVE = True
TWEET_LENGTH = 280


def supply_twitter_instance(lang_key: Optional[str]=None):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            if not ACTIVE:
                return

            if lang_key == "en":
                client = client_EN
                api = api_EN
            elif lang_key is None:
                client = client_DE
                api = api_DE
            else:
                return

            return await func(client, api, *args, **kwargs)

        return wrapper

    return decorator


def upload_media(files, api:API):
    media_ids = []
    for file in files:
        res = api.media_upload(file)
        media_ids.append(res.media_id)
    return media_ids


def create_tweet(text:str, client:Client,media_ids=None,):
    text = fromstring(text).text_content().strip()
    try:
        client.create_tweet(text=text.replace("\n", " ").replace("  ", " ")[:TWEET_LENGTH], media_ids=media_ids)
    except Exception as e:
        logging.error(f"Error when trying to post to twitter: {e}\n\ntext: {text}\n\nmedia_ids: {media_ids}")


@supply_twitter_instance
async def tweet_file(text: str, file: telegram.File, client:Client,api:API):
    path = file.file_path.split('/')[-1]
    await file.download_to_drive(path)
    media_ids = upload_media([path],api)
    create_tweet(text,client, media_ids)
    os.remove(path)

@supply_twitter_instance
async def tweet_file_3(text: str, path: str,api:API,client:Client):
    media_id = api.media_upload(path)
    create_tweet(text, client,[media_id.media_id])


@supply_twitter_instance
async def tweet_files(context: CallbackContext, text: str, client:Client,api:API, posts: [Post],):
    upload_files = []
    for post in posts:
        file = await context.bot.get_file(post.file_id)
        path = file.file_path.split('/')[-1]
        await file.download_to_drive(path)
        upload_files.append(path)

    media_ids = upload_media(upload_files,api)
    create_tweet(text, client, media_ids)
    for path in upload_files:
        os.remove(path)


