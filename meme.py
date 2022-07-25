from telegram import Update
from telegram.ext import CallbackContext

import config
from lang import GERMAN, ENGLISH


def post_media_meme(update: Update, context: CallbackContext):
    if update.channel_post.media_group_id is None:
        add_footer_meme(update, context)
        return

    if update.channel_post.media_group_id not in context.bot_data:
        add_footer_meme(update, context)

        context.job_queue.run_once(remove_media_group_id, 20,
                                   update.channel_post.media_group_id,
                                   str(update.channel_post.media_group_id))


# TODO: make method more generic
def add_footer_meme(update: Update, context: CallbackContext):
    original_caption = update.channel_post.caption_html_urled if update.channel_post.caption is not None else ''
    if "#de" in original_caption:
        footer = "Abonniere @MilitaerMemes für mehr!"
        original_caption = original_caption.replace(r"#de", "")
    else:
        footer = "Subscribe to @MilitaerMemes for more"

    try:
        update.channel_post.edit_caption(f"{original_caption}\n\n🔰 {footer}")

        update.channel_post.forward(chat_id=GERMAN.channel_id)
        # TODO: iterate through all chats
        update.channel_post.forward(chat_id=ENGLISH.channel_id)
    except Exception as e:
        context.bot.send_message(
            config.LOG_GROUP,
            f"<b>⚠️ Error when trying to send media in Channel meme</b>\n<code>{e}</code>\n\n<b>Caused by Update</b>\n<code>{update}</code>"
        )
        pass


def remove_media_group_id(context: CallbackContext):
    del context.bot_data[context.job.context]


def post_text_meme(update: Update, context: CallbackContext):
    original_text = update.channel_post.text_html_urled
    if "#de" in original_text:
        footer = "Abonniere @MilitaerMemes für mehr!"
        original_text = original_text.replace(r"#de", "")
    else:
        footer = "Subscribe to @MilitaerMemes for more"

    try:
        update.channel_post.edit_text(f"{original_text}\n\n🔰 {footer}")

        update.channel_post.forward(chat_id=GERMAN.channel_id)
        update.channel_post.forward(chat_id=ENGLISH.channel_id)
    except Exception as e:
        context.bot.send_message(
            config.LOG_GROUP,
            f"<b>⚠️ Error when trying to send media in Channel meme</b>\n<code>{e}</code>\n\n<b>Caused by Update</b>\n<code>{update}</code>"
        )
        pass
