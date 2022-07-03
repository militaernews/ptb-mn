import re

from telegram import Update, InputMediaVideo, InputMediaPhoto, InputMedia, InputMediaAnimation
from telegram.ext import CallbackContext

import config
from lang import languages
from log import report_error
from translation import translate_message, flag_to_hashtag


def post_channel_english(update: Update, context: CallbackContext):
    if update.channel_post.media_group_id is None:
        original_post = update.channel_post
        original_caption = update.channel_post.caption_html_urled if update.channel_post.caption is not None else ''

        for lang in languages:
            try:
                original_post.copy(
                    chat_id=lang.channel_id,
                    caption=translate_message(lang.lang_key, original_caption) +
                            "\n" + lang.footer)
            except Exception:
                report_error(update, context, Exception)
                pass

        update.channel_post.edit_caption(
            flag_to_hashtag(original_caption) +
            "\n🔰 Abonnieren Sie @MilitaerNews\n🔰 Tritt uns bei @MNChat")
        return

    if update.channel_post.media_group_id in context.bot_data:
        for job in context.job_queue.get_jobs_by_name(
                update.channel_post.media_group_id):
            job.schedule_removal()
        print("--- job gone ::::::::")
    else:
        print("--- NEW MG ------------------------")
        context.bot_data[update.channel_post.media_group_id] = []

    if update.channel_post.photo:
        context.bot_data[update.channel_post.media_group_id].append(
            InputMediaPhoto(media=update.channel_post.photo[-1].file_id))
        print(
            "--- PHOTO ----------------------------------------------------------------"
        )
    elif update.channel_post.video:
        context.bot_data[update.channel_post.media_group_id].append(
            InputMediaVideo(media=update.channel_post.video.file_id))

    elif update.channel_post.animation:
        context.bot_data[update.channel_post.media_group_id].append(
            InputMediaAnimation(media=update.channel_post.animation.file_id))

    if update.channel_post.caption is not None:
        print("trans---SINGLE ::: ",
              translate_message("en-us", update.channel_post.caption))

        context.bot_data[update.channel_post.media_group_id][
            -1].caption = f"{update.channel_post.caption_html_urled}"

        update.channel_post.edit_caption(
            flag_to_hashtag(update.channel_post.caption_html_urled, None) +
            "\n🔰 Abonnieren Sie @MilitaerNews\n🔰 Tritt uns bei @MNChat")

    context.job_queue.run_once(share_in_other_channels, 40,
                               update.channel_post.media_group_id,
                               str(update.channel_post.media_group_id))


def breaking_news(update: Update, context: CallbackContext):
    update.channel_post.delete()
    context.bot.send_photo(
        chat_id=config.CHANNEL_DE,
        photo=open("res/breaking/mn-breaking-de.png", "rb"),
        caption=flag_to_hashtag(update.channel_post.text_html_urled) +
                "\n🔰 Abonnieren Sie @MilitaerNews\n🔰 Tritt uns bei @MNChat")

    text = re.sub(re.compile(r"#eilmeldung[\r\n]*", re.IGNORECASE), "",
                  update.channel_post.text_html_urled)

    for lang in languages:
        try:
            context.bot.send_photo(
                chat_id=lang.channel_id,
                photo=open(f"res/breaking/mn-breaking-{lang.lang_key}.png", "rb"),
                caption="#" + lang.breaking + "\n\n" +
                        translate_message(lang.lang_key, text) + "\n" + lang.footer)
        except Exception:
            report_error(update, context, Exception)
            pass


def announcement(update: Update, context: CallbackContext):
    update.channel_post.delete()

    text = " 📢\n\n" + re.sub(re.compile(r"#eilmeldung", re.IGNORECASE), "",
                             update.channel_post.text_html)

    msg_de = context.bot.send_photo(chat_id=config.CHANNEL_DE,
                                    photo=open(
                                        "res/announce/mn-announce-de.png",
                                        "rb"),
                                    caption="#MITTEILUNG" + text)
    msg_de.pin()

    for lang in languages:
        msg = context.bot.send_photo(
            chat_id=lang.channel_id,
            photo=open(f"res/announce/mn-announce-{lang.lang_key}.png", "rb"),
            caption="#" + lang.announce +
                    translate_message(lang.lang_key, text) + "\n" + lang.footer)
        msg.pin()


def share_in_other_channels(context: CallbackContext):
    files: [InputMedia] = []

    print("JOB ::::::::::::: ", context.job.context)
    print("bot-data :::::::::::::::::::::::::::",
          context.bot_data[context.job.context])

    for file in context.bot_data[context.job.context]:
        print(file)
        files.append(file)

    original_caption = files[0].caption

    for lang in languages:
        files[0].caption = translate_message(
            lang.lang_key, original_caption) + "\n" + lang.footer
        context.bot.send_media_group(chat_id=lang.channel_id, media=files)

    print("-- done --")

    del context.bot_data[context.job.context]
