import logging
import os
from typing import Optional, List, Tuple


from lxml.html import fromstring
from pytwitter import Api
from telegram import Bot

from bot.data.lang import ENGLISH, GERMAN
from bot.social.twitter_uploader import TelegramTwitterTransfer




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


def supply_twitter_instance(lang_key: str) -> Optional[Tuple[Api, TelegramTwitterTransfer]]:
    if not ACTIVE:
        return None
    clients = {
        ENGLISH.lang_key: (api_EN, uploader_EN),
        GERMAN.lang_key: (api_DE, uploader_DE)
    }
    return clients.get(lang_key)


def create_tweet(text: str, api: Api, media_ids=None, ):
    text = fromstring(text).text_content().strip()
    logging.info(f" Creating tweet with text: {text} ::: media_ids: {media_ids}")
    try:
        api.create_tweet(text=text.replace("\n", " ").replace("  ", " ")[:TWEET_LENGTH], media_media_ids=media_ids)
    except Exception as e:
        logging.error(f"Error when trying to post to twitter: {e}\n\ntext: {text}\n\nmedia_ids: {media_ids}")


async def tweet_local_file(file_path: str, caption: str, lang_key: str, ):
    instance = supply_twitter_instance(lang_key)
    print(instance)
    if instance is None:
        return

    api, uploader = instance

    media_id = uploader.upload_local_file(file_path)
    create_tweet(caption, api, [media_id])


async def tweet_files(file_ids: List[str], bot: Bot, caption: str, lang_key: str):
    """Helper function to tweet multiple files with caption."""
    instance = supply_twitter_instance(lang_key)
    if instance is None:
        return

    api, uploader = instance

    media_ids = await uploader.transfer_files(file_ids, bot)
    create_tweet(caption, api, media_ids)


async def tweet_text(text: str, lang_key: Optional[str] = None):
    instance = supply_twitter_instance(lang_key)
    print(instance)
    if instance is None:
        return

    api, uploader = instance
    create_tweet(text, api)
