import traceback

from telegram import Update
from telegram.ext import ContextTypes


async def flag_to_hashtag_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("-------\n\nTEST\n\n-------")
    await update.message.reply_text("-------\n\nTEST\n\n-------")
    try:
        print("--")

    except Exception as e:
        await update.message.reply_text("-------\n\nTEST FAIL\n\n-------")
    await update.message.reply_text(
        f"-------\n\nEXCEPTION: {e}\n\nTRACE: {traceback.format_exc()}\n\n-------"
    )

    await update.message.reply_text("-------\n\nTEST DONE\n\n-------")
