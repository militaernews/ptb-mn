import logging
from asyncio import sleep
from typing import Final, Set

from data.lang import GERMAN
from data.db import get_whitelist
from telegram import Update
from telegram.ext import MessageHandler, filters, CommandHandler, CallbackContext, Application
from util.helper import delete_msg, reply_html
from util.patterns import PATTERN_COMMAND

ALLOWED_URLS: Final[Set[str]] = {
    "bbc.co.uk",
    "bbc.com",
    "bloomberg.com",
    "businessinsider.com",
    "cbr.ru",
    "cnbc.com",
    "cnn.com",
    "dw.com",
    "faz.net",
    "forbes.com",
    "icrc.org",
    "independent.co.uk",
    "kremlin.ru",
    "maps.bot.goo.gl",
    "maps.google.com",
    "n-tv.de",
    "ntv.de",
    "nypost.com",
    "nytimes.com",
    "nzz.ch",
    "reuters.com",
    "spiegel.de",
    "statista.com",
    "t.me/militaernews",
    "t.me/mnchat",
    "t.me/sicherheitskonferenz",
    "tagesschau.de",
    "theguardian.com",
    "un.org",
    "understandingwar.org",
    "washingtonpost.com",
    "whitehouse.gov",
    "wikipedia.org",
    "wsj.com",
    "youtu.be",
    "youtube.com",
    "zeit.de",
    "apnews.com"
}


async def get_admin_ids(context: CallbackContext):
    admins = [admin.user.id for admin in (await context.bot.get_chat_administrators(GERMAN.chat_id))]
    print(admins)
    logging.info(admins)
    return admins


async def remove_url(update: Update, context: CallbackContext):
    if not update.message:
        return

    # Skip for admins
    if update.message.from_user.id in await get_admin_ids(context):
        return

    # Extract all URLs from the message (text and caption)
    from telegram.constants import MessageEntityType
    
    entities = update.message.entities or update.message.caption_entities
    text = update.message.text or update.message.caption
    
    if not entities or not text:
        return

    urls = []
    for e in entities:
        if e.type == MessageEntityType.URL:
            urls.append(text[e.offset : e.offset + e.length])
        elif e.type == MessageEntityType.TEXT_LINK:
            urls.append(e.url)

    if not urls:
        return

    db_urls = await get_whitelist()
    all_allowed = ALLOWED_URLS.union(set(db_urls))

    for url in urls:
        # Clean URL to get domain
        url_clean = url.lower().replace("https://", "").replace("http://", "")
        domain = url_clean.split("/")[0].split("?")[0].split("#")[0]
        
        # Check if the domain or any parent domain is allowed
        is_allowed = False
        for allowed in all_allowed:
            allowed_clean = allowed.lower().strip()
            if domain == allowed_clean or domain.endswith("." + allowed_clean):
                is_allowed = True
                break
        
        if not is_allowed:
            logging.info(f"Deleting message due to unauthorized link: {url} (Domain: {domain})")
            await delete_msg(update)
            return


async def send_whitelist(update: Update, context: CallbackContext):
    db_urls = await get_whitelist()
    all_urls = sorted(list(ALLOWED_URLS.union(set(db_urls))))
    
    text = (
        "🔗 <b>In dieser Gruppe erlaubte Links</b>\n\n"
        "Um Mitglieder vor Scam-Versuchen etc. zu schützen, sind nur folgende Links und deren Subdomains erlaubt:\n\n"
        + "\n\n".join(all_urls) +
        "\n\nNachrichten, die andere Links enthalten, werden automatisch gelöscht."
    )
    
    await update.message.reply_text(text, parse_mode="HTML", disable_web_page_preview=True)


async def log_msg(update: Update, _: CallbackContext):
    if not update.message:
        return
    logging.info(f"log_msg - {update.message.from_user.id} [{update.message.id}]: {update.message.text}")


def register_whitelist(app: Application):
    from telegram.constants import MessageEntityType
    app.add_handler(
        MessageHandler(
            filters.Chat(GERMAN.chat_id) & 
            (filters.Entity(MessageEntityType.URL) | filters.Entity(MessageEntityType.TEXT_LINK)),
            remove_url
        )
    )
    app.add_handler(CommandHandler("whitelist", send_whitelist, filters.Chat(GERMAN.chat_id)))

    app.add_handler(
        MessageHandler(filters.TEXT & filters.Chat(GERMAN.chat_id),
                       log_msg))
