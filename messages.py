import re

from telegram import Update
from telegram.ext import CallbackContext
from deep_translator import GoogleTranslator

from config import GROUP_MAIN


def add_footer_meme(update: Update, context: CallbackContext):
    print(update)

    original_caption = update.channel_post.caption if update.channel_post.caption is not None else ''

    update.channel_post.edit_caption(f"{original_caption}\n\n🔰 Subscribe to @MilitaerMemes for more!")

    update.channel_post.forward(chat_id=GROUP_MAIN)


def flag_to_hashtag(update: Update, context: CallbackContext):
    print(re.findall(r"(#+[a-zA-Z\d(_)]+)", update.message.text))

    update.message.reply_text(translate_message(update.message.text))


def translate_message(text:str):

    return GoogleTranslator(source='de', target='en').translate(text)

