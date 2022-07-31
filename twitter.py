import tweepy
from dotenv import load_dotenv
import os
import pytweet

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
        client.tweet(
            "Hello world, Hello twitter!p")  # This requires read & write app permissions also elevated access type.

    # get EN translation, maybe just pass it as param
    # 1st file in mediagroup, or just the file if no mediagroup

# auth2 = tweepy.OAuth2UserHandler(client_id="a1ZnZXduV1lobDRpQ0VFVUdvMHA6MTpjaQ", client_secret="zB5yi4D4yeNwll_HhvS1mKj7sJffm7RRlbcLEtKm66qKkoWodK", redirect_uri="", scope="")

# auth = tweepy.OAuthHandler(consumer_key="fHDJmDN2b6wWHwHySJnt8d6nz",
#                          consumer_secret="TyX8jskhgZRl3asY7HIzdjnRWOD3DIw2oT5h6Rf4jB0oVA0FZx", )
# auth.set_access_token(key="1329114461882507266-7HSqZyYqdgMRAPoVJwmk53ayV0KGSjy",
#                    secret="BXmKV2I4MX7fEOsYAU7PUwRY0CLtMF3YsWwaE5dBpcwza")

# api = tweepy.API(auth2, wait_on_rate_limit=True, )

# print(api.get_friends())


# Before using PyTweet, make sure to create an application in https://apps.twitter.com.

# client.tweet("Hello world, Hello twitter!p")  # This requires read & write app permissions also elevated access type.
