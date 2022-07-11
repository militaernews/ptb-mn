import traceback

from telegram import Update
from telegram.ext import CallbackContext

from messages import handle_url


def flag_to_hashtag_test(update: Update, context: CallbackContext):
    print("-------\n\nTEST\n\n-------")
    update.message.reply_text("-------\n\nTEST\n\n-------")
    try:

        handle_url(update, context)
    except Exception as e:
        update.message.reply_text("-------\n\nTEST FAIL\n\n-------")
        update.message.reply_text(f"-------\n\nEXCEPTION: {e}\n\nTRACE: {traceback.format_exc()}\n\n-------")

        pass

    update.message.reply_text("-------\n\nTEST DONE\n\n-------")
