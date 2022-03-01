from telegram import Update
from telegram.ext import CallbackContext

from config import GROUP_MAIN


def add_footer_meme(update: Update, context: CallbackContext):
    print(update)

    update.channel_post.edit_caption(update.channel_post.caption + "\n\n🔰 Subscribe to @MilitaerMemes for more")

    update.channel_post.forward(chat_id=GROUP_MAIN)
