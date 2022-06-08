from telegram import Update  #upm package(python-telegram-bot)
from telegram.ext import CallbackContext  #upm package(python-telegram-bot)

import requests
from log import log


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
