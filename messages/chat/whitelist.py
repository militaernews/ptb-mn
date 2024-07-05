import logging
from asyncio import sleep

from telegram import Update, MessageEntity
from telegram.ext import MessageHandler, filters, CommandHandler, CallbackContext, Application

from config import ALLOWED_URLS
from data.lang import GERMAN
from util.helper import delete_msg, reply_html
from util.patterns import PATTERN_COMMAND


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
        app.add_handler(
            MessageHandler(filters.Chat(GERMAN.chat_id) & ~filters.SenderChat.ALL & filters.Entity(MessageEntity.URL),
                           remove_url))
        app.add_handler(CommandHandler("whitelist", send_whitelist, filters.Chat(GERMAN.chat_id)))
        app.add_handler(
            MessageHandler(filters.Regex(PATTERN_COMMAND) & filters.Chat(GERMAN.chat_id),
                           remove_command))