import logging
from asyncio import sleep
from typing import Final, Set

from telegram import Update
from telegram.ext import MessageHandler, filters, CommandHandler, CallbackContext, Application

from src.data.lang import GERMAN
from src.util.helper import delete_msg, reply_html
from src.util.patterns import PATTERN_COMMAND

ALLOWED_URLS: Final[Set[str]] = {
    "t.me/militaernews",
    "bbc.com",
    "bbc.co.uk",
    "nytimes.com",
    "cnn.com",
    "theguardian.com",
    "nypost.com",
    "forbes.com",
    "washingtonpost.com",
    "cnbc.com",
    "independent.co.uk",
    "businessinsider.com",
    "kremlin.ru",
    "un.org",
    "icrc.org",
    "whitehouse.gov",
    "ntv.de",
    "n-tv.de",
    "nzz.ch",
    "faz.net",
    "maps.src.goo.gl",
    "understandingwar.org",
    "wikipedia.org",
    "youtube.com",
    "youtu.be",
    "spiegel.de",
    "maps.google.com",
    "wsj.com",
    "reuters.com",
    "bloomberg.com",
    "dw.com",
    "zeit.de"
    "apnews.com",
    "tagesschau.de",
    "statista.com",
    "cbr.ru",
    "t.me/sicherheitskonferenz",
    "t.me/mnchat"
}


async def get_admin_ids(context: CallbackContext):
    admins = [admin.user.id for admin in (await context.bot.get_chat_administrators(GERMAN.chat_id))]
    print(admins)
    logging.info(admins)
    return admins


async def remove_command(update: Update, _: CallbackContext):
    await sleep(2)
    await delete_msg(update)


async def remove_url(update: Update, context: CallbackContext):
    logging.info(f"MATCH? {update.message.text}")
    print(f"MATCH? {update.message.text}")

    if update.message.from_user.id in await get_admin_ids(context):
        return

    if any(ext in update.message.text for ext in ALLOWED_URLS):
        print("NO MATCH ---")
        return

    await delete_msg(update)


async def send_whitelist(update: Update, context: CallbackContext):
    await reply_html(update, context, "whitelist", "\n\n".join(ALLOWED_URLS))


def register_whitelist(app: Application):
    #   src.add_handler(
    #   MessageHandler(filters.Chat(GERMAN.chat_id) & ~filters.SenderChat.ALL & filters.Entity(MessageEntity.URL),
    #               remove_url))
    app.add_handler(CommandHandler("whitelist", send_whitelist, filters.Chat(GERMAN.chat_id)))
    app.add_handler(
        MessageHandler(filters.Regex(PATTERN_COMMAND) & filters.Chat(GERMAN.chat_id),
                       remove_command))
