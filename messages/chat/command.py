import logging
import re
from collections import defaultdict

import requests
from telegram import Update
from telegram.ext import CallbackContext
from telegram.helpers import mention_html

import config
from util.helper import reply_html, reply_photo


async def is_admin_replying(update: Update, _: CallbackContext):
    return update.message.from_user.id in config.ADMINS and update.message.reply_to_message is not None


def manage_warnings(update: Update, context: CallbackContext, increment: int):
    user_id = update.message.reply_to_message.from_user.id
    user_data = context.bot_data.setdefault("users", defaultdict(lambda: {"warn": 0}))
    user_data[user_id]["warn"] = max(0, user_data[user_id]["warn"] + increment)
    return user_data[user_id]["warn"]


async def ban_user(update: Update, context: CallbackContext):
    await update.message.delete()
    if await is_admin_replying(update, context):
        logging.info(f"banning {update.message.reply_to_message.from_user.id} !!")
        await context.bot.ban_chat_member(update.message.chat_id, update.message.reply_to_message.from_user.id,
                                          until_date=1)
        await update.message.reply_to_message.reply_text(
            f"Aufgrund eines gravierenden Verstoßes habe ich {mention_html(update.message.reply_to_message.from_user.id, update.message.reply_to_message.from_user.first_name)} gebannt.")


async def unwarn_user(update: Update, context: CallbackContext):
    await update.message.delete()
    if await is_admin_replying(update, context):
        logging.info(f"unwarning {update.message.reply_to_message.from_user.id} !!")
        warnings = manage_warnings(update, context, -1)
        await update.message.reply_to_message.reply_text(
            f"Dem Nutzer {mention_html(update.message.reply_to_message.from_user.id, update.message.reply_to_message.from_user.first_name)} wurde eine Warnung erlassen, womit er nur noch {warnings} von 3 hat.")


async def warn_user(update: Update, context: CallbackContext):
    await update.message.delete()
    if await is_admin_replying(update, context):
        logging.info(f"warning {update.message.reply_to_message.from_user.id} !!")
        warnings = manage_warnings(update, context, 1)
        if warnings >= 3:
            logging.info(f"banning {update.message.reply_to_message.from_user.id} !!")
            await context.bot.ban_chat_member(update.message.reply_to_message.chat_id,
                                              update.message.reply_to_message.from_user.id, until_date=1)
            await update.message.reply_to_message.reply_text(
                f"Aufgrund wiederholter Verstöße habe ich {mention_html(update.message.reply_to_message.from_user.id, update.message.reply_to_message.from_user.first_name)} gebannt.")
            return
        await update.message.reply_to_message.reply_text(
            f"Wegen Beleidigung hat der Nutzer {mention_html(update.message.reply_to_message.from_user.id, update.message.reply_to_message.from_user.first_name)} die Warnung {warnings} von 3 erhalten.")


async def report_user(update: Update, context: CallbackContext):
    await update.message.delete()
    if await is_admin_replying(update, context):
        logging.info(f"reporting {update.message.reply_to_message.from_user.id} !!")
        r = requests.post(url="http://localhost:8080/reports",
                          json={
                              "user_id": update.message.reply_to_message.from_user.id,
                              "message": update.message.reply_to_message.text_html_urled,
                              "account_id": 1
                          })
        logging.info(r)
        await update.message.reply_to_message.reply_text(
            f"Der Nutzer {mention_html(update.message.reply_to_message.from_user.id, update.message.reply_to_message.from_user.first_name)} wurde Tartaros-Antispam gemeldet.")


async def maps(update: Update, context: CallbackContext):
    await reply_html(update, context, "maps")

    # todo: collect list of losses


async def loss(update: Update, context: CallbackContext):
    await reply_html(update, context, "loss")


async def donbas(update: Update, context: CallbackContext):
    await reply_html(update, context, "donbas")


async def commands(update: Update, context: CallbackContext):
    await reply_html(update, context, "cmd")


async def genozid(update: Update, context: CallbackContext):
    await reply_html(update, context, "genozid")


async def peace(update: Update, context: CallbackContext):
    await reply_html(update, context, "peace")


async def short(update: Update, context: CallbackContext):
    await reply_html(update, context, "short")


async def stats(update: Update, context: CallbackContext):
    await reply_html(update, context, "stats")


async def bias(update: Update, context: CallbackContext):
    await reply_html(update, context, "bias")


async def sold(update: Update, context: CallbackContext):
    await reply_html(update, context, "sold")


async def ref(update: Update, context: CallbackContext):
    await update.message.delete()

    link = re.findall(r"([^\/]\w*\/\d+$)", update.message.text[4:])
    logging.info(f"link REF: {link}")

    if len(link) == 0:
        return
    else:
        link = link[0]

    logging.info(link)

    text = f"Ich habe dir mal was passendes aus unserem Kanal rausgesucht😊\n\n👉🏼 <a href='t.me/{link}'>{link}</a>"
    if update.message.reply_to_message is not None:
        await update.message.reply_to_message.reply_text(
            f"Hey {update.message.reply_to_message.from_user.name}!\n{text}",
            disable_web_page_preview=False)
    else:
        await context.bot.send_message(update.message.chat_id, text, disable_web_page_preview=False)


async def sofa(update: Update, context: CallbackContext):
    await reply_photo(update, context, "sofa.jpg")


async def bot(update: Update, context: CallbackContext):
    await reply_photo(update, context, "bot.jpg")


async def mimimi(update: Update, context: CallbackContext):
    await reply_photo(update, context, "mimimi.jpg")


async def cia(update: Update, context: CallbackContext):
    await reply_photo(update, context, "cia.jpg")


async def duden(update: Update, context: CallbackContext):
    await reply_photo(update, context, "duden.jpg")


async def argu(update: Update, context: CallbackContext):
    await reply_photo(update, context, "argu.jpg")


async def disso(update: Update, context: CallbackContext):
    await reply_photo(update, context, "disso.jpg")


async def front(update: Update, context: CallbackContext):
    await reply_photo(update, context, "front.png")

async def pali(update: Update, context: CallbackContext):
    await reply_photo(update, context, "pali.jpg")
