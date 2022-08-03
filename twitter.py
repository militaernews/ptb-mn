import os

from dotenv import load_dotenv

load_dotenv()

# PyTweet at least kinda worked :(
from peony import PeonyClient
from telegram import File

consumer_key = os.environ.get("CONSUMER_KEY")
consumer_secret = os.environ.get("CONSUMER_SECRET")
access_token = os.getenv("ACCESS_KEY")
access_secret = os.getenv("ACCESS_SECRET")
bearer = os.getenv("BEARER")

client = PeonyClient(consumer_key=consumer_key,
                     consumer_key_secret=consumer_secret,
                     access_token=access_token,
                     access_token_secret=access_secret)


def tweet_text(text: str):
    print("--- tweet text", text)

    if len(text) <= 280:
        client.tweet(text)


async def tweet_file(text: str, file: File):
    print("--- tweet media", text)

    if len(text) <= 280:
        media = await client.upload_media(file.file_path)
        await client.api.statuses.update.post(status=text, media_ids=[media.media_id])


async def tweet_files(text: str, files: [File]):
    print("--- tweet album", text)

    if len(text) <= 280:
        media_ids = list()
        for file in files:
            media = await client.upload_media(file.file_path)
            media_ids.append(media.media_id)

        await client.api.statuses.update.post(status=text, media_ids=media_ids)
