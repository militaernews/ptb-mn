from deep_translator import GoogleTranslator
from telegram import Update, InputMediaVideo, InputMediaPhoto, InputMedia, ParseMode, InputMediaAnimation  #upm package(python-telegram-bot)
from telegram.ext import CallbackContext  #upm package(python-telegram-bot)
import re
from config import GROUP_MAIN, CHANNEL_EN


def post_channel_meme(update: Update, context: CallbackContext):
    if update.channel_post.media_group_id is None:
        add_footer_meme(update)
        return

    if update.channel_post.media_group_id not in context.bot_data:
        add_footer_meme(update)

        context.job_queue.run_once(remove_media_group_id, 20,
                                   update.channel_post.media_group_id,
                                   str(update.channel_post.media_group_id))


def add_footer_meme(update: Update):
    original_caption = update.channel_post.caption_html_urled if update.channel_post.caption is not None else ''
    if re.search(r"\sde$",
                 original_caption) is not None or original_caption == "de":
        footer = footer = "Abonniere @MilitaerMemes für mehr!"
        original_caption = original_caption[:-2]
    else:
        footer = "Subscribe to @MilitaerMemes for more"

    update.channel_post.edit_caption(f"{original_caption}\n\n🔰 {footer}")

    update.channel_post.forward(chat_id=GROUP_MAIN)


def remove_media_group_id(context: CallbackContext):
    del context.bot_data[context.job.context]