from telegram import Update
from telegram.ext import CallbackContext

from config import GROUP_MAIN


def add_footer_meme(update: Update, context: CallbackContext):
    print(update)

    if update.channel_post.caption is not None:
        original_caption = update.channel_post.caption
    else:
        original_caption = ''

    update.channel_post.edit_caption(original_caption + "\n\n🔰 Subscribe to @MilitaerMemes for more!")

    update.channel_post.forward(chat_id=GROUP_MAIN)
