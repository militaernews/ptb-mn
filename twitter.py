import os

import pytweet
import telegram
from dotenv import load_dotenv
from pytweet import Stream, Tweet, StreamConnection
from telegram import Update
from telegram.ext import CallbackContext

from util.helper import get_caption, get_file

load_dotenv()

# PyTweet at least kinda worked :(
# from peony import PeonyClient

consumer_key = os.getenv("CONSUMER_KEY")
consumer_secret = os.getenv("CONSUMER_SECRET")
access_token = os.getenv("ACCESS_KEY")
access_secret = os.getenv("ACCESS_SECRET")
bearer = os.getenv("BEARER")

#todo: does this work?
stream = Stream(5)
stream.add_rule("from:DarthPutinKGB")


client = pytweet.Client(
    bearer_token=bearer,
    consumer_key=consumer_key,
    consumer_key_secret=consumer_secret,
    access_token=access_token,
    access_token_secret=access_secret,
    stream=stream
)

stream.connect()
TWEET_LENGTH = 280


@client.event
def on_stream(tweet: Tweet, con: StreamConnection):
    print(f">>>>>>>>>> Someone posted a tweet: {tweet}")



def tweet_text(text: str):
    print("--- tweet", text)

    if len(text) <= TWEET_LENGTH:
        client.tweet(text)  # This requires read & write app permissions also elevated access type.


async def tweet_file(text: str, file: telegram.File):
    if len(text) <= TWEET_LENGTH:
        path = file.file_path.split('/')[-1]
        print("file to download:::: ", path)
        await file.download(path)
        print("-- download done")
        # todo: can also quote tweet here.. is that an option?
        try:
            client.tweet(text=text, file=pytweet.File(path))
        except Exception as e:
            print(f"⚠️ Error when trying to post single file to twitter: {e}")
            pass

        os.remove(path)


async def tweet_file_3(text: str, path: str):
    if len(text) <= TWEET_LENGTH:
        # todo: can also quote tweet here.. is that an option?
        client.tweet(text=text, file=pytweet.File(path))


async def tweet_file_2(update: Update, context: CallbackContext):
    await tweet_file(get_caption(update), await get_file(update))


async def tweet_files_2(update: Update, context: CallbackContext):
    print("---")


async def tweet_files(text: str, files: [telegram.File]):
    if len(text) <= TWEET_LENGTH:
        upload_files = list()
        for file in files:
            path = file.file_path.split('/')[-1]
            await file.download(path)
            upload_files.append(pytweet.File(path))
        # todo: param "files" is only available in 1.5.0a10
        # client.tweet(text=text, files=upload_files)

        try:
            client.tweet(text=text, file=upload_files[0])
        except Exception as e:
            print(f"⚠️ Error when trying to post multiple files to twitter: {e}")
            pass

        for file in upload_files:
            os.remove(file.path)
