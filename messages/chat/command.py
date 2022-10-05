import requests
from telegram import Update
from telegram.ext import CallbackContext
from telegram.helpers import mention_html

import config
from util.helper import reply_html, reply_photo


async def ban_user(update: Update, context: CallbackContext):
    await update.message.delete()

    if update.message.from_user.id in config.ADMINS and update.message.reply_to_message is not None:
        print(f"banning {update.message.reply_to_message.from_user.id} !!")
        await context.bot.ban_chat_member(update.message.chat_id, update.message.reply_to_message.from_user.id,
                                          until_date=1)
        await update.message.reply_to_message.reply_text(
            f"Aufgrund eines gravierenden Verstoßes habe ich {mention_html(update.message.reply_to_message.from_user.id, update.message.reply_to_message.from_user.first_name)} gebannt.")


async def unwarn_user(update: Update, context: CallbackContext):
    await update.message.delete()

    if update.message.from_user.id in config.ADMINS and update.message.reply_to_message is not None:
        print(f"unwarning {update.message.reply_to_message.from_user.id} !!")
        if "users" not in context.bot_data or update.message.reply_to_message.from_user.id not in context.bot_data[
            "users"] or "warn" not in context.bot_data["users"][update.message.reply_to_message.from_user.id]:
            warnings = 0
            context.bot_data["users"] = {update.message.reply_to_message.from_user.id: {"warn": warnings}}

        else:
            warnings = context.bot_data["users"][update.message.reply_to_message.from_user.id]["warn"]

            if warnings != 0:
                warnings = warnings - 1

            context.bot_data["users"][update.message.reply_to_message.from_user.id]["warn"] = warnings

            await update.message.reply_to_message.reply_text(
                f"Dem Nutzer {mention_html(update.message.reply_to_message.from_user.id, update.message.reply_to_message.from_user.first_name)} wurde eine Warnung erlassen, womit er nur noch {warnings} von 3 hat.")


async def warn_user(update: Update, context: CallbackContext):
    await update.message.delete()

    if update.message.from_user.id in config.ADMINS and update.message.reply_to_message is not None:
        print(f"warning {update.message.reply_to_message.from_user.id} !!")
        if "users" not in context.bot_data or update.message.reply_to_message.from_user.id not in context.bot_data[
            "users"] or "warn" not in context.bot_data["users"][update.message.reply_to_message.from_user.id]:
            warnings = 1
            context.bot_data["users"] = {update.message.reply_to_message.from_user.id: {"warn": warnings}}

        else:
            warnings = context.bot_data["users"][update.message.reply_to_message.from_user.id]["warn"]
            if warnings == 3:
                print(f"banning {update.message.reply_to_message.from_user.id} !!")
                await context.bot.ban_chat_member(update.message.reply_to_message.chat_id,
                                                  update.message.reply_to_message.from_user.id, until_date=1)
                await update.message.reply_to_message.reply_text(
                    f"Aufgrund wiederholter Verstöße habe ich {mention_html(update.message.reply_to_message.from_user.id, update.message.reply_to_message.from_user.first_name)} gebannt.")
                return
            else:
                warnings = warnings + 1
                context.bot_data["users"][update.message.reply_to_message.from_user.id]["warn"] = warnings

        await update.message.reply_to_message.reply_text(
            f"Wegen Beleidigung hat der Nutzer {mention_html(update.message.reply_to_message.from_user.id, update.message.reply_to_message.from_user.first_name)} die Warnung {warnings} von 3 erhalten.")


async def report_user(update: Update, context: CallbackContext):
    await update.message.delete()

    if update.message.from_user.id in config.ADMINS and update.message.reply_to_message is not None:
        print(f"reporting {update.message.reply_to_message.from_user.id} !!")
        r = requests.post(url="https://tartaros-telegram.herokuapp.com/reports/",
                          json={
                              "user_id": update.message.reply_to_message.from_user.id,
                              "message": update.message.reply_to_message.text_html_urled,
                              "account_id": 1
                          }
                          )
        print(r)

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


async def sofa(update: Update, context: CallbackContext):
    await reply_photo(update, context, "sofa.jpg")
