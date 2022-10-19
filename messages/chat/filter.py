import random

import requests
from telegram import Update, Poll
from telegram.ext import CallbackContext
from telegram.helpers import mention_html

from messages.chat.bingo import handle_bingo
from messages.chat.dictionary import handle_putin_dict
from util.log import log


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


async def filter_message(update: Update, context: CallbackContext):
    print(update)
    text = update.message.text.lower()

    # print(filter(lambda element: 'abc' in element, text))

    if 1 == 2:
        print("Spam detected")
        return
    # todo: filter and report

    elif any(ext in text for ext in ("Idiot", "Hurensohn", "Arschloch", "Ukronazi")):
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


async def handle_other_chats(update: Update, context: CallbackContext):
    await handle_bingo(update, context)

    await handle_putin_dict(update, context)
