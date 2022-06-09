from telegram import Update, Poll  #upm package(python-telegram-bot)
from telegram.ext import CallbackContext  #upm package(python-telegram-bot)
import random
import requests
from log import log
from data import *


def check_cas(user_id: int):
    response = requests.get(f"https://api.cas.chat/check?user_id={user_id}")
    print(user_id, response.json())
    return "True" == response.json()["ok"]


def join_member(update: Update, context: CallbackContext):
    for member in update.message.new_chat_members:
        if check_cas(member.id):
            context.bot.ban_chat_member(update.effective_chat.id,
                                        update.message.from_user.id)
            log(
                update, context,
                f"User { member.name} [<code>{ member.id}</code>] was banned in chat <a href='https://t.me/username'>{update.message.chat.title}</a> due to CAS-ban (<a href='https://cas.chat/check?user_id={ member.id}'>reason</a>)."
            )
            ## todo: find out deeplink that works with chat_id

        if not key_exists(member.id):
            # show captcha

            x = random.randrange(1, 20)
            y = random.randrange(4, 20)
            result = x + y
            options = [result * 2, result, result + 7, result - 3]
            random.shuffle(options)

            poll = update.message.reply_poll(
                f"✌🏼 Herzlich willkommen im MNChat, {member.first_name}!\n\nUm zu verifizieren, dass Sie ein echter Nutzer sind beantworten Sie bitte folgende Frage:\n\nWas ergibt {x} + {y} ?",
                [str(x) for x in options],
                is_anonymous=False,
              type=Poll.QUIZ,
            correct_option_id=options.index(result),
              explanation="To prevent this group from spam, answering this captcha incorrectly will get you kicked. If you believe this was an error, please contact @pentexnyx",
              open_period=60
              )

          ## hier dann schedulen wo geschaut wird wer poll geantwortet hat??
