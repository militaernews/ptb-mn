from telegram import Update
from telegram.ext import CallbackContext


def add_footer_meme(update: Update, context: CallbackContext):
    print(update)

    update.channel_post.edit_caption(update.channel_post.caption + "\n\n🔰 Subscribe to @MilitaerMemes for more")

    update.channel_post.forward("MNChat")

def test(update: Update, context: CallbackContext):
    print("-------------------------")
    print(update.message.chat_id)