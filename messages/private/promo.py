import logging

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ChatMemberOwner, \
    ChatMemberAdministrator, ChatMemberMember
from telegram.ext import CallbackContext

from data.db import insert_promo
from data.lang import all_langs


async def is_member( context: CallbackContext, user_id:int, channel_index:int):
    check =await context.bot.getChatMember(all_langs[channel_index].channel_id, user_id)

    print(f"check: {check} -- id {all_langs[channel_index].channel_id}")

    return type(check)  in  (ChatMemberMember,ChatMemberOwner,ChatMemberAdministrator)

async def start_promo(update: Update, context: CallbackContext):

    data =update.message.text.split(" ")[1].split("_")[1:]

    cb_data = fr"promo_{data[0]}"
    if len(data) == 2:
        if int(data[1]) == update.message.from_user.id:
            return await update.message.reply_text(
                "Du kannst deinen eigenen Link nicht verwenden. Schicke ihn gerne an jemand anderen 😉")

        cb_data += f"_{data[1]}"


    if await is_member(context, update.message.from_user.id, int(data[0])):



        await update.message.reply_text(
            "respond promo",
            reply_markup=InlineKeyboardMarkup.from_button(InlineKeyboardButton(
                "Teilen",
                url=f"https://t.me/share/url?url=https://t.me/militaernews_posting_bot?start=promo_{data[0]}_{update.message.from_user.id}&text=Bitte%20komm"
            ))
        )
    else:


        await update.message.reply_text(
            "RES -- Damit du an der Verlosung zum Jubiläum von MilitärNews teilnehmen kannst, musst du zuerst den Kanal abonnieren.\n\n"
            "Klicke einfach auf diesen Link:\n\n"
            "<b>https://t.me/militaernews</b>\n\n"
            "-------------------\n\n"
            "Wenn du abonniert hast, dann verifiziere deine Teilnahme an der Verlosung mit einem Klick auf den Button unten.",
            reply_markup=InlineKeyboardMarkup.from_button(InlineKeyboardButton(
                "Verify",
                callback_data=cb_data
            ))
        )








async def verify_promo(update: Update, context: CallbackContext):


    data = update.callback_query.data.split("_")[1:]
    print(update)
    print(data)

    if await is_member(context,update.callback_query.from_user.id, int(data[0])):
        print("is member")

        if len(data) ==2:
           promo_id = int(data[1])
        else:
            promo_id=None


        res = insert_promo(update.callback_query.from_user.id, int(data[0]), promo_id)

        if res is None:
            await update.callback_query.edit_message_text(
                f"Du bist bereits über einen Promo-Link beigetreten. Hier nochmal dein Promo-Link:",
                reply_markup=InlineKeyboardMarkup.from_button(InlineKeyboardButton(
                    "Teilen",
                    url=f"https://t.me/share/url?url=https://t.me/militaernews_posting_bot?start=promo_{data[0]}_{update.callback_query.from_user.id}&text=Bitte%20komm"
                ))
            )

        await update.callback_query.edit_message_text(
            f"verified promo, Rewarded {promo_id}",
            reply_markup=InlineKeyboardMarkup.from_button(InlineKeyboardButton(
                "Teilen",
                url=f"https://t.me/share/url?url=https://t.me/militaernews_posting_bot?start=promo_{data[0]}_{update.callback_query.from_user.id}&text=Bitte%20komm"
            ))
        )

        if promo_id is not None:
            try:
                await context.bot.send_message(promo_id, "Ein Nutzer hat uns über deinen Link abonniert! Zur Belohung erhältst du ein weiteres Los für unsere Jubiläums-Verlosung 🎉\n\n"
                                                         "Teile deinen Link mit weiteren Leuten für eine höhere Gewinnchance 😉"
                                               ,
                                               reply_markup=InlineKeyboardMarkup.from_button(InlineKeyboardButton(
                                                   "Teilen",
                                                   url=f"https://t.me/share/url?url=https://t.me/militaernews_posting_bot?start=promo_{data[0]}_{promo_id}&text=Bitte%20komm"
                                               ))
                                               )
            except Exception as e:
                logging.error(f"User blocked Bot. {e}")
                pass

        await update.callback_query.answer()

    else:
        print("not member")
        await update.callback_query.answer(f"You have to subscribe to our channel first!")



