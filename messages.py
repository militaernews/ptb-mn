from telegram import Update
from telegram.ext import CallbackContext


def add_footer_meme(update: Update, context: CallbackContext):
    print(update)

    update.channel_post.edit_caption(update.channel_post.caption + "🔰 Subscribe to @MilitaerMemes for more")
