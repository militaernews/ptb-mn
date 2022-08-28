import random
from typing import Dict

import requests
from orjson import orjson
from telegram import Poll, Update
from telegram.helpers import mention_html

import config
from data.db import *
from data.lang import languages
from messages.bingo import handle_bingo
from util.log import log


# fixme: refine
def key_exists(context, key):
    return (
            key in context.bot_data["users"]
    )


def check_cas(user_id: int):
    response = requests.get(f"https://api.cas.chat/check?user_id={user_id}")
    print(user_id, response.json())
    return "True" == response.json()["ok"]


def join_member(update: Update, context: CallbackContext):
    for member in update.message.new_chat_members:
        if check_cas(member.id):
            context.bot.ban_chat_member(
                update.effective_chat.id, update.message.from_user.id
            )
            log(
                update,
                context,
                f"User {member.name} [<code>{member.id}</code>] was banned in chat "
                "<a href='https://t.me/username'>{update.message.chat.title}</a> due"
                f" to CAS-ban (<a href='https://cas.chat/check?user_id={member.id}'>reason</a>). ",
            )
            # todo: find out deeplink that works with chat_id

        if not key_exists(context, member.id):
            # show captcha

            x = random.randrange(1, 20)
            y = random.randrange(4, 20)
            result = x + y
            options = [result * 2, result, result + 7, result - 3]
            random.shuffle(options)

            poll = update.message.reply_poll(
                f"✌🏼 Herzlich willkommen im MNChat, {member.first_name}!\n\n"
                "Um zu verifizieren, dass Sie ein echter "
                f"Nutzer sind beantworten Sie bitte folgende Frage:\n\nWas ergibt {x} + {y} ?",
                [str(x) for x in options],
                is_anonymous=False,
                type=Poll.QUIZ,
                correct_option_id=options.index(result),
                explanation="To prevent this group from spam, answering this captcha incorrectly will get you kicked. "
                            "If you believe this was an error, please contact @pentexnyx",
                open_period=60,
            )

        # hier dann schedulen wo geschaut wird wer poll geantwortet hat??


async def private_setup(update: Update, context: CallbackContext):
    """
    Allow adding entries to saved posts.
    """
    if update.message.caption == "repair":
        await update.message.reply_text("Processing json-file...")

        await repair_saved_post(update, context)


async def repair_saved_post(update: Update, context: CallbackContext):
    filename = await (await update.message.document.get_file()).download()

    with open(filename, 'rb') as f:
        content: Dict[str, int] = orjson.loads(f.read())
        print(content)

        for key, value in content.items():
            if type(key) is not str or type(value) is not int:
                await update.message.reply_text(f"Keys have to be text, values have to be numbers.")
                return

        if "de" not in content.keys():
            await update.message.reply_text(f"Missing key \"de\" of the post you want to edit.")
            return

        for lang in languages:
            if lang.lang_key not in content.keys():
                await update.message.reply_text(f"Missing key >> {lang.lang_key}")
                return

        post_id = str(content["de"])

        current_dict = None

        if post_id in context.bot_data:
            current_dict = context.bot_data[post_id]
            await update.message.reply_text(f"Entry is present in bot_data. Contents: {current_dict}")

        lang_dict = dict()

        for key, value in content.items():
            if any(lang.lang_key == key for lang in languages):
                lang_dict[key] = value

        final_dict = dict()

        final_dict["langs"] = lang_dict

        if "reply" in content.keys():
            final_dict["reply"] = content["reply"]

        await update.message.reply_text(f"Final bot_data: {final_dict}")

        await context.bot.send_message(
            config.LOG_GROUP,
            f"<b>⚠️ Editing bot_data by user {update.message.from_user.first_name} [<code>{update.message.from_user.id}</code>]</b>\n\n<b>Current bot_data:</b>\n<code>{current_dict}</code>\n\n<b>Input</b>\n<code>{content}</code>\n\n<b>Updated bot_data</b>\n<code>{final_dict}</code>",
        )

        context.bot_data[post_id] = final_dict


async def ban_user(update: Update, context: CallbackContext):
    await update.message.delete()

    if update.message.from_user.id in config.ADMINS and update.message.reply_to_message is not None:
        print(f"banning {update.message.reply_to_message.from_user.id} !!")
        await context.bot.ban_chat_member(update.message.chat_id, update.message.reply_to_message.from_user.id,
                                          until_date=1)
        await update.message.reply_to_message.reply_text(
            f"Aufgrund eines gravierenden Verstößes habe ich {mention_html(update.message.reply_to_message.from_user.id, update.message.reply_to_message.from_user.first_name)} gebannt.")


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


async def filter_message(update: Update, context: CallbackContext):
    print(update)
    text = update.message.text.lower()

    print(filter(lambda element: 'abc' in element, text))

    if 1 == 2:
        print("Spam detected")
        return
    # todo: filter and report

    elif any(ext in text for ext in ("Idiot", "Hurensohn")):
        print("warning user...")

        if "users" not in context.bot_data or update.message.from_user.id not in context.bot_data[
            "users"] or "warn" not in context.bot_data["users"][update.message.from_user.id]:
            warnings = 1
            context.bot_data["users"] = {update.message.from_user.id: {"warn": warnings}}

        else:
            warnings = context.bot_data["users"][update.message.from_user.id]["warn"]
            if warnings == 3:
                print(f"banning {update.message.from_user.id} !!")
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
