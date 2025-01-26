from telegram import Update
from telegram.ext import CallbackContext, Application, filters, MessageHandler

from config import LOG_GROUP, CHANNEL_MEME
from data.lang import ENGLISH, GERMAN, languages


async def post_media_meme(update: Update, context: CallbackContext):
    if update.channel_post.media_group_id is None:
        await add_footer_meme(update, context)

    elif update.channel_post.media_group_id not in context.chat_data:
        await add_footer_meme(update, context)

        context.job_queue.run_once(
            remove_media_group_id,
            20,
            update.channel_post.media_group_id,
            str(update.channel_post.media_group_id),
        )


# TODO: make method more generic
# TODO: apply footer only to 1st entry of mediagroup
async def add_footer_meme(update: Update, context: CallbackContext):
    context.chat_data[update.channel_post.media_group_id] = update.channel_post.id

    if update.channel_post.caption is None:
        original_caption = ""
    else:
        original_caption = update.channel_post.caption_html_urled

    try:
        await update.channel_post.edit_caption(format_meme_footer(original_caption))

        # Unfortunately it is not possible for bots to forward a media-group as a whole.
        await update.channel_post.forward(chat_id=GERMAN.chat_id)
    except Exception as e:
        await context.bot.send_message(
            LOG_GROUP,
            "<b>⚠️ Error when trying to send media in Channel meme</b>\n"
            f"<code>{e}</code>\n\n<b>Caused by Update</b>\n<code>{update}</code>",
        )

    if "#de" not in original_caption:
        for lang in languages:
            if lang.chat_id is not None:
                await update.channel_post.forward(chat_id=lang.chat_id)


async def remove_media_group_id(context: CallbackContext):
    del context.chat_data[context.job.context]


async def post_text_meme(update: Update, context: CallbackContext):
    try:
        await update.channel_post.edit_text(
            format_meme_footer(update.channel_post.text_html_urled), disable_web_page_preview=False
        )

        await update.channel_post.forward(chat_id=GERMAN.chat_id)
        await update.channel_post.forward(chat_id=ENGLISH.chat_id)
    except Exception as e:
        await context.bot.send_message(
            LOG_GROUP,
            "<b>⚠️ Error when trying to send text in Channel meme</b>\n"
            f"<code>{e}</code>\n\n<b>Caused by Update</b>\n<code>{update}</code>",
        )


def format_meme_footer(original_text: str) -> str:
    if "#de" in original_text:
        footer = "Abonniere @MilitaerMemes für mehr!"
        original_text = original_text.replace("#de", "")
    else:
        footer = "Subscribe to @MilitaerMemes for more"

    return f"{original_text}\n\n🔰 {footer}"


def register_meme(app: Application):
    media = (filters.PHOTO | filters.VIDEO | filters.ANIMATION)

    meme_post = filters.UpdateType.CHANNEL_POST & filters.Chat(chat_id=CHANNEL_MEME)

    app.add_handler(MessageHandler(meme_post & media, post_media_meme))
    app.add_handler(MessageHandler(meme_post & filters.TEXT, post_text_meme))
