import logging
import os

import telegram
from data.db import insert_promo, truncate_promo
from data.lang import LANG_DICT
from settings.config import ADMINS
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ChatMemberOwner, \
    ChatMemberAdministrator, ChatMemberMember
from telegram.ext import CallbackContext, Application, filters, MessageHandler, CallbackQueryHandler, CommandHandler

from bot.settings.config import RES_PATH


def get_text(update: Update, file: str):
    lang = update.effective_user.language_code
    path = f"{RES_PATH}/{lang}/promo/{file}.html"

    if os.path.exists(path):
        with open(path, "r", encoding='utf-8') as f:
            return f.read()

    with open(f"{RES_PATH}/en/promo/{file}.html", "r", encoding='utf-8') as f:
        return f.read()


def get_img(update: Update):
    lang = update.effective_user.language_code
    path = f"{RES_PATH}/img/mn-tg-promo-{lang}.png"

    if os.path.exists(path):
        return open(path, "rb")

    return open(f"{RES_PATH}/img/mn-tg-promo-en.png", "rb")


async def send_promos(_: Update, context: CallbackContext):
    for lang in LANG_DICT.values():
        with open(f"{RES_PATH}/{lang.lang_key}/promo/announce.html", "r", encoding='utf-8') as f:
            text = f.read()
        with open(f"{RES_PATH}/{lang.lang_key}/promo/verify.html", "r", encoding='utf-8') as f:
            btn = f.read()

        msg = await context.bot.send_photo(lang.channel_id,
                                           open(f"{RES_PATH}/img/mn-tg-promo-{lang.lang_key}.png", "rb"),
                                           text,
                                           reply_markup=InlineKeyboardMarkup.from_button(InlineKeyboardButton(
                                               btn,
                                               url=f"https://t.me/militaernews_posting_bot?start=promo_{lang.lang_key}"
                                           )))
        await msg.pin()


async def is_member(context: CallbackContext, user_id: int, lang: str):
    await context.bot.send_chat_action(chat_id=user_id, action=telegram.constants.ChatAction.TYPING)
    check = await context.bot.getChatMember(LANG_DICT[lang].channel_id, user_id)

    logging.info(f"check: {check} -- id {LANG_DICT[lang].channel_id}")

    return type(check) in (ChatMemberMember, ChatMemberOwner, ChatMemberAdministrator)


async def start_promo(update: Update, context: CallbackContext):
    data = update.message.text.split(" ")[1].split("_")[1:]

    cb_data = fr"promo_{data[0]}"
    promo_id = 0
    if len(data) == 2:
        promo_id = int(data[1])
        if int(data[1]) == update.message.from_user.id:
            return await update.message.reply_text(get_text(update, "own"))

        cb_data += f"_{data[1]}"

    if await is_member(context, update.message.from_user.id, data[0]):

        payload = get_text(update, "payload") + f"{data[0]}_"

        text = get_text(update, "done")

        res = await insert_promo(update.message.from_user.id, data[0], promo_id)
        if res is not None:
            return await update.message.reply_text("\n".join(get_text(update, "already").split("\n")[2:]),
                                                   reply_markup=InlineKeyboardMarkup.from_button(InlineKeyboardButton(
                                                       get_text(update, "share"),
                                                       url=f"{payload}{update.message.from_user.id}"
                                                   ))
                                                   )

        if len(data) == 2:
            try:
                await context.bot.send_message(data[1],
                                               get_text(update, "reward"),
                                               reply_markup=InlineKeyboardMarkup.from_button(InlineKeyboardButton(
                                                   get_text(update, "share"),
                                                   url=f"{payload}{data[1]}"
                                               )))
                text += get_text(update, "bonus")
            except Exception as e:
                logging.error(f"User blocked Bot. {e}")
        await update.message.reply_photo(get_img(update),
                                         text,
                                         reply_markup=InlineKeyboardMarkup.from_button(InlineKeyboardButton(
                                             get_text(update, "share"),
                                             url=f"{payload}{update.message.from_user.id}"
                                         )))

    else:
        await update.message.reply_photo(get_img(update),
                                         get_text(update, "instruct"),
                                         reply_markup=InlineKeyboardMarkup.from_button(
                                             InlineKeyboardButton(get_text(update, "verify"), callback_data=cb_data)
                                         ))


async def verify_promo(update: Update, context: CallbackContext):
    data = update.callback_query.data.split("_")[1:]
    logging.info(f"{update}----{data}")

    if await is_member(context, update.callback_query.from_user.id, data[0]):
        logging.info("is member")

        text = get_text(update, "done")
        if len(data) == 2:
            promo_id = int(data[1])
            text += get_text(update, "bonus")
        else:
            promo_id = None

        res = await insert_promo(update.callback_query.from_user.id, data[0], promo_id)

        payload = get_text(update, "payload") + f"{data[0]}_"

        if res is None:
            await update.callback_query.edit_message_caption(
                get_text(update, "already"),
                reply_markup=InlineKeyboardMarkup.from_button(InlineKeyboardButton(
                    get_text(update, "share"),
                    url=f"{payload}{update.callback_query.from_user.id}"
                ))
            )

        await update.callback_query.edit_message_caption(
            text,
            reply_markup=InlineKeyboardMarkup.from_button(InlineKeyboardButton(
                get_text(update, "share"),
                url=f"{payload}{update.callback_query.from_user.id}"
            ))
        )

        if promo_id is not None:
            payload = get_text(update, "payload") + f"{data[0]}_"

            try:
                await context.bot.send_message(promo_id,
                                               get_text(update, "reward"),
                                               reply_markup=InlineKeyboardMarkup.from_button(InlineKeyboardButton(
                                                   get_text(update, "share"),
                                                   url=f"{payload}{promo_id}"
                                               )))
            except Exception as e:
                logging.error(f"User blocked Bot. {e}")
        await update.callback_query.answer()

    else:
        logging.info("not member")
        await update.callback_query.answer(get_text(update, "require"))


async def clear_promo(update: Update, context: CallbackContext):
    await truncate_promo()
    await update.message.reply_text("cleared promos. you can now start a new promo with /promo.")


def register_promo(app: Application):
    app.add_handler(MessageHandler(filters.Regex(r"\/start promo_\w{2}(_\d+)?"), start_promo))
    app.add_handler(CallbackQueryHandler(verify_promo, r"promo_\w{2}(_\d+)?"))
    app.add_handler(CommandHandler("promo", send_promos, filters.Chat(ADMINS)))
    app.add_handler(CommandHandler("clear_promo", clear_promo, filters.Chat(ADMINS)))
