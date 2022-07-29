from telegram import Update
from telegram.ext import CallbackContext

import config
from data.lang import ENGLISH, GERMAN


async def post_media_meme(update: Update, context: CallbackContext):
    if update.channel_post.media_group_id is None:
        add_footer_meme(update, context)
        return

    if update.channel_post.media_group_id not in context.bot_data:
        add_footer_meme(update, context)

        context.job_queue.run_once(
            remove_media_group_id,
            20,
            update.channel_post.media_group_id,
            str(update.channel_post.media_group_id),
        )


# TODO: make method more generic
def add_footer_meme(update: Update, context: CallbackContext):
    if update.channel_post.caption is None:
        original_caption = ""
    else:
        original_caption = update.channel_post.caption_html_urled

    if "#de" in original_caption:
        footer = "Abonniere @MilitaerMemes für mehr!"
        original_caption = original_caption.replace("#de", "")
    else:
        footer = "Subscribe to @MilitaerMemes for more"

    try:
        update.channel_post.edit_caption(f"{original_caption}\n\n🔰 {footer}")

        update.channel_post.forward(chat_id=GERMAN.chat_id)
        # TODO: iterate through all chats
        update.channel_post.forward(chat_id=ENGLISH.chat_id)
    except Exception as e:
        context.bot.send_message(
            config.LOG_GROUP,
            "<b>⚠️ Error when trying to send media in Channel meme</b>\n"
            f"<code>{e}</code>\n\n<b>Caused by Update</b>\n<code>{update}</code>",
        )


async def remove_media_group_id(context: CallbackContext):
    del context.bot_data[context.job.context]


async def post_text_meme(update: Update, context: CallbackContext):
    original_text = update.channel_post.text_html_urled

    if "#de" in original_text:
        footer = "Abonniere @MilitaerMemes für mehr!"
        original_text = original_text.replace("#de", "")
    else:
        footer = "Subscribe to @MilitaerMemes for more"

    try:
        await update.channel_post.edit_text(
            f"{original_text}\n\n🔰 {footer}", disable_web_page_preview=False
        )

        await update.channel_post.forward(chat_id=GERMAN.chat_id)
        await update.channel_post.forward(chat_id=ENGLISH.chat_id)
    except Exception as e:
        await context.bot.send_message(
            config.LOG_GROUP,
            "<b>⚠️ Error when trying to send text in Channel meme</b>\n"
            f"<code>{e}</code>\n\n<b>Caused by Update</b>\n<code>{update}</code>",
        )
