import traceback

from telegram import Update
from telegram.ext import ContextTypes

from util.translation import flag_to_hashtag


async def flag_to_hashtag_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("-------\n\nTEST\n\n-------")
    await update.message.reply_text("-------\n\nTEST\n\n-------")
    try:

        #   await update.message.reply_text(        translate_message("tr", update.message.text_html_urled))
        await update.message.reply_text(flag_to_hashtag(update.message.text_html_urled, "de"))
    except Exception as e:
        await update.message.reply_text("-------\n\nTEST FAIL\n\n-------")
        await update.message.reply_text(
            f"-------\n\nEXCEPTION: {e}\n\nTRACE: {traceback.format_exc()}\n\n-------"
        )

    await update.message.reply_text("-------\n\nTEST DONE\n\n-------")
