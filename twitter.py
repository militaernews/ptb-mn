import logging
import os

import telegram
import tweepy as tweepy
from dotenv import load_dotenv
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

TWEET_LENGTH = 300


def tweet_text(text: str):
    logging.info(f"--- tweet {text}")

    if len(text) <= TWEET_LENGTH:
        client.create_tweet(text=text)  # This requires read & write app permissions also elevated access type.


async def tweet_file(text: str, file: telegram.File):
    if len(text) <= TWEET_LENGTH:
        path = file.file_path.split('/')[-1]
        logging.info(f"file to download:::: {str(path)}")
        await file.download_to_drive(path)
        logging.info("-- download done")
        # todo: can also quote tweet here.. is that an option?
        try:

            filenames = [path]
            media_ids = []
            for filename in filenames:
                res = api.media_upload(filename)
                media_ids.append(res.media_id)

            # Tweet with multiple images
            client.create_tweet(text=text, media_ids=media_ids)
        except Exception as e:
            logging.info(f"⚠️ Error when trying to post single file to twitter: {e}")
            pass

        os.remove(path)


async def tweet_file_3(text: str, path: str):
    if len(text) <= TWEET_LENGTH:
        # todo: can also quote tweet here.. is that an option?
        media_id = api.media_upload(path)
        client.create_tweet(text=text, media_ids=[media_id.media_id])


async def tweet_file_2(update: Update, context: CallbackContext):
    await tweet_file(get_caption(update), await get_file(update))


async def tweet_files(context: CallbackContext, text: str, posts: [Post]):
    if len(text) > TWEET_LENGTH:
        # todo: better cut to text length
        return
    upload_files = []
    for post in posts:
        file = await context.bot.get_file(post.file_id)
        logging.info(f"file: {file}")
        path = file.file_path.split('/')[-1]
        await file.download_to_drive(path)
        logging.info(f"path: {path}")
        upload_files.append(path)

    try:

        media_ids = []
        for filename in upload_files:
            res = api.media_upload(filename)
            logging.info(f"media_id-RESULT: {res}")
            media_ids.append(res.media_id)

        # Tweet with multiple images
        client.create_tweet(text=text, media_ids=media_ids)
    except Exception as e:
        logging.info(f"⚠️ Error when trying to post multiple files to twitter: {e}")
    for path in upload_files:  # better use OS unlink path
        os.remove(path)
