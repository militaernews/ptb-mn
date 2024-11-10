import logging
import os

import telegram
import tweepy as tweepy
from dotenv import load_dotenv
from lxml import html
from telegram import Update
from telegram.ext import CallbackContext

from data.db import Post
from util.helper import get_caption, get_file

load_dotenv()

consumer_key = os.getenv("CONSUMER_KEY")
consumer_secret = os.getenv("CONSUMER_SECRET")
access_token = os.getenv("ACCESS_KEY")
access_secret = os.getenv("ACCESS_SECRET")
bearer = os.getenv("BEARER")

ACTIVE = True

client = tweepy.Client(
    consumer_key=consumer_key,
    consumer_secret=consumer_secret,
    access_token=access_token,
    access_token_secret=access_secret,
)
auth = tweepy.OAuth1UserHandler(
    consumer_key=consumer_key,
    consumer_secret=consumer_secret,
    access_token=access_token,
    access_token_secret=access_secret,
)
api = tweepy.API(auth)

TWEET_LENGTH = 280


def upload_media(files):
    if not ACTIVE:
        return
    media_ids = []
    for file in files:
        res = api.media_upload(file)
        media_ids.append(res.media_id)
    return media_ids


def create_tweet(text, media_ids=None):
    if not ACTIVE:
        return

    text = html.fromstring(text).text_content().strip()
    try:
        client.create_tweet(text=text.replace("\n", " ").replace("  ", " ")[:TWEET_LENGTH], media_ids=media_ids)
    except Exception as e:
        logging.error(f"Error when trying to post to twitter: {e}")


async def tweet_file(text: str, file: telegram.File):
    if not ACTIVE:
        return
    path = file.file_path.split('/')[-1]
    await file.download_to_drive(path)
    media_ids = upload_media([path])
    create_tweet(text, media_ids)
    os.remove(path)


async def tweet_file_2(update: Update):
    await tweet_file(get_caption(update), await get_file(update))


async def tweet_file_3(text: str, path: str):
    if not ACTIVE:
        return
    media_id = api.media_upload(path)
    create_tweet(text=text, media_ids=[media_id.media_id])


async def tweet_files(context: CallbackContext, text: str, posts: [Post]):
    if not ACTIVE:
        return
    upload_files = []
    for post in posts:
        file = await context.bot.get_file(post.file_id)
        path = file.file_path.split('/')[-1]
        await file.download_to_drive(path)
        upload_files.append(path)

    media_ids = upload_media(upload_files)
    create_tweet(text, media_ids)
    for path in upload_files:
        os.remove(path)
