from telegram import Update  #upm package(python-telegram-bot)
from telegram.ext import CallbackContext  #upm package(python-telegram-bot)

import requests


def check_cas(user_id: int):
    response = requests.get(f"https://api.cas.chat/check?user_id={user_id}")
    print(user_id, response.json())
    return "True" == response.json()["ok"]


def join_member(update: Update, context: CallbackContext):
    if check_cas(update.message.from_user.id):
        context.bot.ban_chat_member(update.effective_chat.id,
                                    update.message.from_user.id)
