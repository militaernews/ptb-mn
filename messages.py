import re

from deep_translator import DeepL
from telegram import Update
from telegram.ext import CallbackContext

from config import GROUP_MAIN


def add_footer_meme(update: Update, context: CallbackContext):
    if update.channel_post.media_group_id is None:
        print("Update::::: ", update)

        original_caption = update.channel_post.caption if update.channel_post.caption is not None else ''
        update.channel_post.edit_caption(f"{original_caption}\n\n🔰 Subscribe to @MilitaerMemes for more!")

        update.channel_post.forward(chat_id=GROUP_MAIN)
        return

    print("Media-Group::::::::::::::::::::::::::: ", update)

    if update.channel_post.caption is not None and (
            update.channel_post.media_group_id not in context.chat_data or "text" not in context.chat_data[
        update.channel_post.media_group_id]):
        context.chat_data[update.channel_post.media_group_id] = {"text": update.channel_post.caption, "file-ids": []}

    if update.channel_post.video is not None:
        context.chat_data[update.channel_post.media_group_id]["file-ids"].append(update.channel_post.video.file_id)
    elif update.channel_post.photo is not None:
        context.chat_data[update.channel_post.media_group_id]["file-ids"].append(update.channel_post.photo[-1].file_id)

    context.job_queue.run_once(
        send_channel, 20, update.channel_post.media_group_id, str(update.channel_post.media_group_id)
    )


def flag_to_hashtag(update: Update, context: CallbackContext):
    print(re.findall(r"(#+[a-zA-Z\d(_)]+)", update.message.text))

    update.message.reply_text(translate_message(update.message.text))


# update.message.media_group_id

# context.job_queue.run_once(
#     delete, 600, reply_message.chat_id, str(reply_message.message_id)
#  )


def translate_message(text: str):
    return DeepL(source='de', target='en').translate(text)


def send_channel(context: CallbackContext):
    print("CTX ::::: ", context.job.context, "CTX-ChatData :::::::::::::", context.chat_data[int(context.job.context)])
    context.bot.send_media_group(
        chat_id=GROUP_MAIN,
        media=list(
            context.bot.get_file(context.chat_data[context.job.context]["file-id"][0])
        )
    )
    context.bot.delete_message(str(context.job.context), context.job.name)
