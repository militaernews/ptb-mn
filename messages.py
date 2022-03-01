from telegram import Update
from telegram.ext import CallbackContext


def add_footer_meme(update: Update, context: CallbackContext):
    update.message.caption = update.message.caption + "🔰 Subscribe to @MilitaerMemes for more"
