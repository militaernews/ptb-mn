import re

from deep_translator import DeepL
from telegram import Update, InputMediaVideo, InputMediaPhoto, InputMedia
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

    if update.channel_post.media_group_id not in context.bot_data:
        context.bot_data[update.channel_post.media_group_id] = {"text": None, "files": []}

    if update.channel_post.caption is not None and context.bot_data[update.channel_post.media_group_id][
        "text"] is None:
        context.bot_data[update.channel_post.media_group_id]["text"] = update.channel_post.caption

    if update.channel_post.video is not None:
        context.bot_data[update.channel_post.media_group_id]["files"].append(
            InputMediaVideo(media=update.channel_post.video.file_id).to_json())
    elif update.channel_post.photo is not None:
        context.bot_data[update.channel_post.media_group_id]["files"].append(
            InputMediaPhoto(media=update.channel_post.photo[-1].file_id).to_json())

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
    print("CTX ::::: ", context.job.context)
    print("ChatDAta :::::::::::::::::::::::::::::::::::: ", context.bot_data)
    print("CTX-ChatData :::::::::::::", context.bot_data[str(context.job.context)])

    files: [InputMedia] = []

    for file_id in context.bot_data[context.job.context]["files"]:
        files.append(context.bot.get_file(file_id))

    files[0].set_caption(context.bot_data[context.job.context]["text"])

    context.bot.send_media_group(chat_id=GROUP_MAIN, media=files)
