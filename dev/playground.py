import traceback

from telegram import Update
from telegram.ext import ContextTypes, CallbackContext

from util.translation import translate_message


async def flag_to_hashtag_test(update: Update, context:ContextTypes.DEFAULT_TYPE):
    print("-------\n\nTEST\n\n-------")
    await update.message.reply_text("-------\n\nTEST\n\n-------")
    try:
        print("--")

       # await update.message.reply_text(translate_message("de", update.message.text_html_urled, None))

        chat = await context.bot.get_chat(update.message.from_user.id)

        await update.message.reply_text(chat.username)

        print("--")

        user =  await context.bot.get_chat("@n6y9x")

        await update.message.reply_text(str(user.id))

    except Exception as e:
        await update.message.reply_text("-------\n\nTEST FAIL\n\n-------")
        await update.message.reply_text(
            f"-------\n\nEXCEPTION: {e}\n\nTRACE: {traceback.format_exc()}\n\n-------"
        )

    await update.message.reply_text("-------\n\nTEST DONE\n\n-------")
