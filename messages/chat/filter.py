import logging
import re
from asyncio import sleep

import requests
from telegram import Update
from telegram.ext import CallbackContext
from telegram.helpers import mention_html

from config import ALLOWED_URLS, ADMINS, LOG_GROUP
from messages.chat.bingo import handle_bingo
from messages.chat.dictionary import handle_putin_dict
from util.memo import get_admin_ids


def check_cas(user_id: int):
    response = requests.get(f"https://api.cas.chat/check?user_id={user_id}")
    logging.info(f"{user_id} --- {response.json()}")
    return response.json()["ok"] == "True"


def join_member(update: Update, context: CallbackContext):
    for member in update.message.new_chat_members:
        if check_cas(member.id):
            context.bot.ban_chat_member(
                update.effective_chat.id, update.message.from_user.id
            )

            context.bot.send_message(LOG_GROUP,
                                     f"User {mention_html(member.id, member.name)} [<code>{member.id}</code>] was banned in chat "
                                     "<a href='https://t.me/username'>{update.message.chat.title}</a> due"
                                     f" to CAS-ban (<a href='https://cas.chat/check?user_id={member.id}'>reason</a>). ",
                                     )


async def filter_message(update: Update, context: CallbackContext):
    #  logging.info()(update)
    text = update.message.text.lower()

    # logging.info()(filter(lambda element: 'abc' in element, text))

    if re.search(r"@\S*trade\S*|testimony|contact him|Petr Johnson", text) is not None:
        reply_text = "👀 Scammst du? Bitte sei brav!"

        for admin in ADMINS:
            reply_text += mention_html(admin, "​")

        await update.message.reply_text(reply_text)
        logging.info(f"Spam detected: {update.message.from_user} :::: {text}")
        return
    # todo: filter and report

    elif any(ext in text for ext in ("Idiot", "Hurensohn", "Arschloch", "Ukronazi")):
        logging.info("warning user...")

        if "users" not in context.bot_data or update.message.from_user.id not in context.bot_data[
            "users"] or "warn" not in context.bot_data["users"][update.message.from_user.id]:
            warnings = 1
            context.bot_data["users"] = {update.message.from_user.id: {"warn": warnings}}

        else:
            warnings = context.bot_data["users"][update.message.from_user.id]["warn"]
            if warnings == 3:
                logging.info(f"banning {update.message.from_user.id} !!")
                await context.bot.ban_chat_member(update.message.chat_id, update.message.from_user.id, until_date=1)
                await update.message.reply_text(
                    f"Aufgrund wiederholter Verstöße habe ich {mention_html(update.message.from_user.id, update.message.from_user.first_name)} gebannt.")
                return
            else:
                warnings = warnings + 1
                context.bot_data["users"][update.message.from_user.id]["warn"] = warnings

        # Verstoßes gegen die Regeln dieser Gruppe - siehe /rules ???
        await update.message.reply_text(
            f"Wegen Beleidigung hat der Nutzer {mention_html(update.message.from_user.id, update.message.from_user.first_name)} die Warnung {warnings} von 3 erhalten.")

    else:
        await handle_bingo(update, context)


async def handle_other_chats(update: Update, context: CallbackContext):
    await handle_bingo(update, context)

    await handle_putin_dict(update, context)


async def remove_command(update: Update, _: CallbackContext):
    await sleep(2)
    await update.message.delete()


async def remove_url(update: Update, context: CallbackContext):
    logging.info(f"MATCH? {update.message.text}")
    print(f"MATCH? {update.message.text}")

    if update.message.from_user.id in await get_admin_ids(context):
        return

    if any(ext in update.message.text for ext in ALLOWED_URLS):
        print("NO MATCH ---")
        return

    await update.message.delete()
