import os

import pytweet
import telegram
from dotenv import load_dotenv

load_dotenv()

consumer_key = os.environ.get("CONSUMER_KEY")
consumer_secret = os.environ.get("CONSUMER_SECRET")
access_token = os.getenv("ACCESS_KEY")
access_secret = os.getenv("ACCESS_SECRET")
bearer = os.getenv("BEARER")

client = pytweet.Client(
    bearer_token=bearer,
    consumer_key=consumer_key,
    consumer_key_secret=consumer_secret,
    access_token=access_token,
    access_token_secret=access_secret
)


def post_twitter(text: str):
    print("--- tweet", text)

    if len(text) <= 280:
        client.tweet(text)  # This requires read & write app permissions also elevated access type.


async def tweet_photo(text: str, file: telegram.File):
    path = f"temp/{file.file_path.split('/')[-1]}"
    await file.download(path)
    # todo: can also quote tweet here.. is that an option?
    client.tweet(text=text, file=pytweet.File(path))
    os.remove(path)


async def tweet_album(text: str, files: [telegram.File]):
    upload_files = list()
    for file in files:
        path = f"temp/{file.file_path.split('/')[-1]}"
        await file.download(path)
        upload_files.append(pytweet.File(path))
    # todo: param "files" is only available in 1.5.0a10
    # client.tweet(text=text, files=upload_files)
    client.tweet(text=text, file=upload_files[0])

    for file in upload_files:
        os.remove(file.path)
