import os

import pytweet
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
