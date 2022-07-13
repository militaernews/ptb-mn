import re
from collections import defaultdict
from dataclasses import dataclass

from telegram import Update, InputMediaVideo, InputMediaPhoto, InputMedia, InputMediaAnimation, Message, MessageId, \
    MessageEntity, TelegramError
from telegram.ext import CallbackContext

import config
from lang import languages
from util.regex import HASHTAG, WHITESPACE
from util.translation import translate_message, flag_to_hashtag

FOOTER_DE = "\n🔰 Abonnieren Sie @MilitaerNews\n🔰 Tritt uns bei @MNChat"


def post_channel_single(update: Update, context: CallbackContext):
    original_caption = update.channel_post.caption_html_urled if update.channel_post.caption is not None else ''

    if "reply" in context.bot_data[update.channel_post.message_id]:
        replies = context.bot_data[context.bot_data[update.channel_post.message_id]["reply"]]["langs"]
    else:
        replies = None

    for lang in languages:
        print(lang)
        print(context.bot_data[update.channel_post.message_id])
        try:
            msg_id: MessageId = update.channel_post.copy(
                chat_id=lang.channel_id,
                caption=translate_message(lang.lang_key, original_caption) + "\n" + lang.footer,
                reply_to_message_id=replies[lang.lang_key] if replies is not None else None)

            print(msg_id)

            context.bot_data[update.channel_post.message_id]["langs"][lang.lang_key] = msg_id.message_id
        except Exception as e:
            context.bot.send_message(
                config.LOG_GROUP,
                f"<b>⚠️ Error when trying to send single post in Channel {lang.lang_key}</b>\n<code>{e}</code>\n\n<b>Caused by Update</b>\n<code>{update}</code>"
            )
            pass

    handle_url(update, context)  # TODO: maybe extend to breaking and media_group

    update.channel_post.edit_caption(flag_to_hashtag(original_caption) + FOOTER_DE)


def post_channel_english(update: Update, context: CallbackContext):
    if update.channel_post.message_id not in context.bot_data:
        context.bot_data[update.channel_post.message_id] = {
            "langs": defaultdict(str)
        }

    # only index 0 should have reply_to_message -- check this!
    if update.channel_post.reply_to_message is not None:
        context.bot_data[update.channel_post.message_id]["reply"] = update.channel_post.reply_to_message.message_id

    if update.channel_post.media_group_id is None:
        post_channel_single(update, context)
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
        context.bot_data[update.channel_post.message_id] = dict()
        print("trans---SINGLE ::: ", translate_message("en-us", update.channel_post.caption_html_urled))

        context.bot_data[update.channel_post.media_group_id][
            -1].caption = f"{update.channel_post.caption_html_urled}"

        update.channel_post.edit_caption(
            flag_to_hashtag(update.channel_post.caption_html_urled) + FOOTER_DE)

    context.job_queue.run_once(share_in_other_channels, 30,
                               JobContext(
                                   update.channel_post.media_group_id,
                                   update.channel_post.message_id
                               ),
                               str(update.channel_post.media_group_id))


def breaking_news(update: Update, context: CallbackContext):
    update.channel_post.delete()

    try:
        context.bot.send_photo(
            chat_id=config.CHANNEL_DE,
            photo=open("res/breaking/mn-breaking-de.png", "rb"),
            caption=flag_to_hashtag(update.channel_post.text_html_urled) + FOOTER_DE)
    except Exception as e:
        context.bot.send_message(
            config.LOG_GROUP,
            f"<b>⚠️ Error when trying to send breaking news in channel DE</b>\n<code>{e}</code>\n\n<b>Caused by Update</b>\n<code>{update}</code>"
        )
    pass

    text = re.sub(re.compile(r"#eilmeldung[\r\n]*", re.IGNORECASE), "",
                  update.channel_post.text_html_urled)

    for lang in languages:
        try:
            context.bot.send_photo(
                chat_id=lang.channel_id,
                photo=open(f"res/breaking/mn-breaking-{lang.lang_key}.png", "rb"),
                caption="#" + lang.breaking + "\n\n" +
                        translate_message(lang.lang_key, text) + "\n" + lang.footer)
        except Exception as e:
            context.bot.send_message(
                config.LOG_GROUP,
                f"<b>⚠️ Error when trying to send breaking news in channel {lang.lang_key}</b>\n<code>{e}</code>\n\n<b>Caused by Update</b>\n<code>{update}</code>"
            )
            pass


def announcement(update: Update, context: CallbackContext):
    update.channel_post.delete()

    text = " 📢\n\n" + re.sub(re.compile(r"#mitteilung", re.IGNORECASE), "",
                             update.channel_post.text_html)

    try:
        msg_de = context.bot.send_photo(chat_id=config.CHANNEL_DE,
                                        photo=open(
                                            "res/announce/mn-announce-de.png",
                                            "rb"),
                                        caption="#MITTEILUNG" + text)
        msg_de.pin()
    except Exception as e:
        context.bot.send_message(
            config.LOG_GROUP,
            f"<b>⚠️ Error when trying to send announcement in channel DE</b>\n<code>{e}</code>\n\n<b>Caused by Update</b>\n<code>{update}</code>"
        )
        pass

    for lang in languages:
        try:
            msg = context.bot.send_photo(
                chat_id=lang.channel_id,
                photo=open(f"res/announce/mn-announce-{lang.lang_key}.png", "rb"),
                caption="#" + lang.announce +
                        translate_message(lang.lang_key, text) + "\n" + lang.footer)
            msg.pin()
        except Exception as e:
            context.bot.send_message(
                config.LOG_GROUP,
                f"<b>⚠️ Error when trying to send announcement in Channel {lang.lang_key}</b>\n<code>{e}</code>\n\n<b>Caused by Update</b>\n<code>{update}</code>"
            )
            pass


def share_in_other_channels(context: CallbackContext):
    job_context: JobContext = context.job.context
    files: [InputMedia] = []

    print("JOB ::::::::::::: ", context.job.context)
    print("bot-data :::::::::::::::::::::::::::",
          context.bot_data[job_context.media_group_id])

    for file in context.bot_data[job_context.media_group_id]:
        print(file)
        files.append(file)

    original_caption = files[0].caption

    if "reply" in context.bot_data[job_context.message_id]:
        replies = context.bot_data[context.bot_data[job_context.message_id]["reply"]]["langs"]
    else:
        replies = None

    for lang in languages:
        files[0].caption = translate_message(lang.lang_key, original_caption) + "\n" + lang.footer

        try:
            msg: Message = context.bot.send_media_group(chat_id=lang.channel_id, media=files,
                                                        reply_to_message_id=replies[
                                                            lang.lang_key] if replies is not None else None)[0]

            context.bot_data[job_context.message_id]["langs"][lang.lang_key] = msg.message_id
        except Exception as e:
            context.bot.send_message(
                config.LOG_GROUP,
                f"<b>⚠️ Error when trying to send media group in Channel {lang.lang_key}</b>\n\n<code>{e}</code>"
            )
            pass

    print("-- done --")

    del context.bot_data[job_context.media_group_id]


def edit_channel(update: Update, context: CallbackContext):
    if update.edited_channel_post.caption is not None:
        original_caption = re.sub(WHITESPACE, "", re.sub(HASHTAG, "",
                                                         update.edited_channel_post.caption_html_urled.replace(
                                                             FOOTER_DE, "")))

        for lang in languages:
            try:
                context.bot.edit_message_caption(
                    chat_id=lang.channel_id,
                    message_id=context.bot_data[update.edited_channel_post.message_id]["langs"][lang.lang_key],
                    caption=translate_message(lang.lang_key, original_caption) + "\n" + lang.footer)
            except TelegramError as e:
                if e.message != "Message is not modified: specified new message content and reply markup are exactly the same as a current content and reply markup of the message":
                    context.bot.send_message(
                        config.LOG_GROUP,
                        f"<b>⚠️ Error when trying to edit post in Channel {lang.lang_key}</b>\n<code>{e}</code>\n\n<b>Caused by Update</b>\n<code>{update}</code>"
                    )
                pass

    # update.channel_post.edit_caption(flag_to_hashtag(original_caption) + FOOTER_DE)


@dataclass
class JobContext:
    media_group_id: str
    message_id: int


def handle_url(update: Update, context: CallbackContext):
    if update.channel_post.caption is None:
        return

    entities = update.channel_post.parse_caption_entities([MessageEntity.URL, MessageEntity.TEXT_LINK])

    print(entities)

    # TODO: maybe also remove the url/textlink from the initial message?

    if len(entities) == 0:
        return

    link = "folgenden Link" if len(entities) == 1 else "folgende Links"

    # fixme: change to channel_post
    text = f"Öffnen Sie gerne {link}, wenn Sie mehr über die Geschehnisse in <a href='https://t.me/militaernews/{update.channel_post.message_id}'>diesem Post</a> erfahren wollen:"

    for entity, content in entities.items():
        print(entity)
        if entity.type == "text_link":
            quelle = f"<a href='{entity.url}'>{content}</a>"
        else:
            quelle = content

        text += f"\n\n· {quelle}"

    text += "\n" + FOOTER_DE

    print(text)

    context.bot.send_message(chat_id=config.CHANNEL_SOURCE, text=text, disable_web_page_preview=False)
