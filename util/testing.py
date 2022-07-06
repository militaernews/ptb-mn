from telegram import Update
from telegram.ext import CallbackContext

from util.translation import flag_to_hashtag, translate_message


def flag_to_hashtag_test(update: Update, context: CallbackContext):
    update.message.reply_text("flag to hashtag -- TR")
    update.message.reply_text(
        flag_to_hashtag(update.message.text_html_urled, "tr"))

    update.message.reply_text("deepl -- de -- formality more")
    update.message.reply_text(
        translate_message("de", update.message.text_html_urled))

    update.message.reply_text("deepl -- en-us")
    update.message.reply_text(
        translate_message("en-us", update.message.text_html_urled))
