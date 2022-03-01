from telegram import Update
from telegram.ext import CallbackContext


def add_footer_meme(update: Update, context: CallbackContext):
    print(update)

    update.message.edit_caption(update.message.caption + "🔰 Subscribe to @MilitaerMemes for more")
