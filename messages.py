import re

from deep_translator import DeepL
from telegram import Update, InputMediaVideo, InputMediaPhoto, InputMedia, ParseMode, InputMediaAnimation
from telegram.ext import CallbackContext

from config import GROUP_MAIN, CHANNEL_EN


def add_footer_meme(update: Update, context: CallbackContext):
    if update.channel_post.media_group_id is None:
        original_caption = update.channel_post.caption if update.channel_post.caption is not None else ''
        update.channel_post.edit_caption(f"{original_caption}\n\n🔰 Subscribe to @MilitaerMemes for more!")

        update.channel_post.forward(chat_id=GROUP_MAIN)
        return

    if update.channel_post.media_group_id in context.bot_data:
        for job in context.job_queue.get_jobs_by_name(update.channel_post.media_group_id):
            job.schedule_removal()
    else:
        context.bot_data[update.channel_post.media_group_id] = []

    if update.channel_post.photo is not None:
        context.bot_data[update.channel_post.media_group_id].append(
            InputMediaPhoto(media=update.channel_post.photo[-1].file_id, parse_mode=ParseMode.HTML))
    elif update.channel_post.video is not None:
        context.bot_data[update.channel_post.media_group_id].append(
            InputMediaVideo(media=update.channel_post.video.file_id, parse_mode=ParseMode.HTML))
    elif update.channel_post.animation is not None:
        context.bot_data[update.channel_post.media_group_id].append(
            InputMediaAnimation(media=update.channel_post.animation.file_id, parse_mode=ParseMode.HTML))

    if update.channel_post.caption is not None:
        context.bot_data[update.channel_post.media_group_id][
            -1].caption = f"{update.channel_post.caption}\n\n🔰 Subscribe to @MilitaerMemes for more!"

    context.job_queue.run_once(
        share_in_main_group, 30, update.channel_post.media_group_id, str(update.channel_post.media_group_id)
    )


def share_in_main_group(context: CallbackContext):
    files: [InputMedia] = []

    for file in context.bot_data[context.job.context]:
        files.append(file)

    context.bot.send_media_group(chat_id=GROUP_MAIN, media=files)

    del context.bot_data[context.job.context]


def flag_to_hashtag(update: Update, context: CallbackContext):
    print(re.findall(r"(#+[a-zA-Z\d(_)]+)", update.message.text))


# update.message.reply_text(translate_message(update.message.text))


def translate_message(text: str) -> str:
    return DeepL(source='de', target='en').translate(text)


def post_channel_english(update: Update, context: CallbackContext):
    if update.channel_post.media_group_id is None:
        original_caption = update.channel_post.caption if update.channel_post.caption is not None else ''
        update.channel_post.edit_caption(
            f"{translate_message(original_caption)}\n\n🔰 Subscribe to @MilitaryNewsEN for more!")

        update.channel_post.forward(chat_id=CHANNEL_EN)
        return

    if update.channel_post.media_group_id in context.bot_data:
        for job in context.job_queue.get_jobs_by_name(update.channel_post.media_group_id):
            job.schedule_removal()
    else:
        context.bot_data[update.channel_post.media_group_id] = []

    if update.channel_post.photo is not None:
        context.bot_data[update.channel_post.media_group_id].append(
            InputMediaPhoto(media=update.channel_post.photo[-1].file_id, parse_mode=ParseMode.HTML))
    elif update.channel_post.video is not None:
        context.bot_data[update.channel_post.media_group_id].append(
            InputMediaVideo(media=update.channel_post.video.file_id, parse_mode=ParseMode.HTML))
    elif update.channel_post.animation is not None:
        context.bot_data[update.channel_post.media_group_id].append(
            InputMediaAnimation(media=update.channel_post.animation.file_id, parse_mode=ParseMode.HTML))

    if update.channel_post.caption is not None:
        context.bot_data[update.channel_post.media_group_id][-1].caption = f"{translate_message(update.channel_post.caption)}\n\n🔰 Subscribe to @MilitaryNewsEN for more!"

    context.job_queue.run_once(
        share_in_english_channel, 30, update.channel_post.media_group_id, str(update.channel_post.media_group_id)
    )


def share_in_english_channel(context: CallbackContext):
    files: [InputMedia] = []

    for file in context.bot_data[context.job.context]:
        files.append(file)

    context.bot.send_media_group(chat_id=CHANNEL_EN, media=files)

    del context.bot_data[context.job.context]
