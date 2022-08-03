import re
from collections import defaultdict
from dataclasses import dataclass

from telegram import (InputMedia, InputMediaAnimation, InputMediaPhoto,
                      InputMediaVideo, Message, MessageEntity, MessageId,
                      Update)
from telegram.error import TelegramError
from telegram.ext import CallbackContext

import config
import twitter
from data.lang import ENGLISH, GERMAN, languages
from util.helper import get_replies, sanitize_text
from util.regex import HASHTAG, WHITESPACE
from util.translation import flag_to_hashtag, translate_message


# TODO: make method more generic
async def post_channel_single(update: Update, context: CallbackContext):
    original_caption = sanitize_text(update.channel_post.caption)

    replies = get_replies(context.bot_data, str(update.channel_post.message_id))

    for lang in languages:
        print(lang)
        print(context.bot_data[str(update.channel_post.message_id)])

        try:
            msg_id: MessageId = await update.channel_post.copy(
                chat_id=lang.channel_id,
                caption=f"{translate_message(lang.lang_key, original_caption, lang.lang_key_deepl)}\n{lang.footer}",
                reply_to_message_id=replies[lang.lang_key]
                if replies is not None
                else None,
            )

            print(msg_id)

            context.bot_data[str(update.channel_post.message_id)]["langs"][
                lang.lang_key
            ] = msg_id.message_id
        except Exception as e:
            await context.bot.send_message(
                config.LOG_GROUP,
                "<b>⚠️ Error when trying to send single post in Channel "
                f"{lang.lang_key}</b>\n<code>{e}</code>\n\n"
                f"<b>Caused by Update</b>\n<code>{update}</code>",
            )

    formatted_text = flag_to_hashtag(original_caption)

    try:
        await update.channel_post.edit_caption(formatted_text + GERMAN.footer)
    except TelegramError as e:
        if not e.message.startswith("Message is not modified"):
            await context.bot.send_message(
                config.LOG_GROUP,
                f"<b>⚠️ Error when trying to edit post in Channel de</b>\n"
                f"<code>{e}</code>\n\n<b>Caused by Update</b>\n<code>{update}</code>",
            )

    try:

        # todo: upload photo aswell
        # twitter.post_twitter(formatted_text)
        print("-")
    except Exception as e:
        await context.bot.send_message(
            config.LOG_GROUP,
            f"<b>⚠️ Error when trying to post single on Twitter</b>\n"
            f"<code>{e}</code>\n\n<b>Caused by Update</b>\n<code>{update}</code>",
        )

    await handle_url(update, context)  # TODO: maybe extend to breaking and media_group


# TODO: make method more generic
async def post_channel_english(update: Update, context: CallbackContext):
    if str(update.channel_post.message_id) not in context.bot_data:
        context.bot_data[str(update.channel_post.message_id)] = {
            "langs": defaultdict(str)
        }

    # only index 0 should have reply_to_message -- check this!
    if update.channel_post.reply_to_message is not None:
        print(":::::::::: reply exists! ::::::::::::::::::::::::")
        print(update.channel_post)
        context.bot_data[str(update.channel_post.message_id)]["reply"] = str(
            update.channel_post.reply_to_message.message_id
        )

    if update.channel_post.media_group_id is None:
        await post_channel_single(update, context)
        return

    if update.channel_post.media_group_id in context.bot_data:
        for job in context.job_queue.get_jobs_by_name(
                update.channel_post.media_group_id
        ):
            job.schedule_removal()
        print("--- job gone ::::::::")
    else:
        print("--- NEW MG ------------------------")
        context.bot_data[update.channel_post.media_group_id] = []

    if update.channel_post.photo:
        context.bot_data[update.channel_post.media_group_id].append(
            InputMediaPhoto(media=update.channel_post.photo[-1].file_id)
        )
        print(
            "--- PHOTO ----------------------------------------------------------------"
        )
    elif update.channel_post.video:
        context.bot_data[update.channel_post.media_group_id].append(
            InputMediaVideo(media=update.channel_post.video.file_id)
        )

    elif update.channel_post.animation:
        context.bot_data[update.channel_post.media_group_id].append(
            InputMediaAnimation(media=update.channel_post.animation.file_id)
        )

    if update.channel_post.caption is not None:
        context.bot_data[update.channel_post.message_id] = {}
        print(
            "trans---SINGLE ::: ",
            translate_message(ENGLISH.lang_key, update.channel_post.caption_html_urled, ENGLISH.lang_key_deepl),
        )

        context.bot_data[update.channel_post.media_group_id][
            -1
        ].caption = f"{update.channel_post.caption_html_urled}"

        try:
            await update.channel_post.edit_caption(
                flag_to_hashtag(update.channel_post.caption_html_urled) + GERMAN.footer
            )
        except Exception as e:
            await context.bot.send_message(
                config.LOG_GROUP,
                f"<b>⚠️ Error when trying to edit caption in channel DE</b>\n"
                f"<code>{e}</code>\n\n<b>Caused by Update</b>\n<code>{update}</code>",
            )

    context.job_queue.run_once(
        share_in_other_channels,
        30,
        JobContext(update.channel_post.media_group_id, update.channel_post.message_id),
        str(update.channel_post.media_group_id),
    )


async def breaking_news(update: Update, context: CallbackContext):
    await update.channel_post.delete()

    try:
        await context.bot.send_photo(
            chat_id=GERMAN.channel_id,
            photo=open("../res/breaking/mn-breaking-de.png", "rb"),
            caption=flag_to_hashtag(update.channel_post.text_html_urled)
                    + GERMAN.footer,
        )
    except Exception as e:
        await context.bot.send_message(
            config.LOG_GROUP,
            f"<b>⚠️ Error when trying to send breaking news in channel DE</b>\n"
            f"<code>{e}</code>\n\n<b>Caused by Update</b>\n<code>{update}</code>",
        )

    text = re.sub(
        re.compile(r"#eilmeldung[\r\n]*", re.IGNORECASE),
        "",
        update.channel_post.text_html_urled,
    )

    for lang in languages:
        try:
            await context.bot.send_photo(
                chat_id=lang.channel_id,
                photo=open(f"res/breaking/mn-breaking-{lang.lang_key}.png", "rb"),
                caption=f"#{lang.breaking}\n\n{translate_message(lang.lang_key, text, lang.lang_key_deepl)}\n{lang.footer}",
            )
        except Exception as e:
            await context.bot.send_message(
                config.LOG_GROUP,
                f"<b>⚠️ Error when trying to send breaking news in channel {lang.lang_key}</b>\n"
                f"<code>{e}</code>\n\n<b>Caused by Update</b>\n<code>{update}</code>",
            )


async def announcement(update: Update, context: CallbackContext):
    await update.channel_post.delete()

    text = " 📢\n\n" + re.sub(
        re.compile(r"#mitteilung", re.IGNORECASE), "", update.channel_post.text_html
    )

    try:
        msg_de = await context.bot.send_photo(
            chat_id=GERMAN.channel_id,
            photo=open("../res/announce/mn-announce-de.png", "rb"),
            caption="#MITTEILUNG" + text,
        )
        await msg_de.pin()
    except Exception as e:
        await context.bot.send_message(
            config.LOG_GROUP,
            f"<b>⚠️ Error when trying to send announcement in channel DE</b>\n"
            f"<code>{e}</code>\n\n<b>Caused by Update</b>\n<code>{update}</code>",
        )

    for lang in languages:
        try:
            msg = await context.bot.send_photo(
                chat_id=lang.channel_id,
                photo=open(f"res/announce/mn-announce-{lang.lang_key}.png", "rb"),
                caption=f"#{lang.announce}{translate_message(lang.lang_key, text, lang.lang_key_deepl)}\n{lang.footer}",

            )
            await msg.pin()
        except Exception as e:
            await context.bot.send_message(
                config.LOG_GROUP,
                f"<b>⚠️ Error when trying to send announcement in Channel {lang.lang_key}</b>\ncode>{e}</code>\n\n<b>Caused by Update</b>\n<code>{update}</code>",
            )


# TODO: make method more generic
async def share_in_other_channels(context: CallbackContext):
    job_context: JobContext = context.job.data
    files: [InputMedia] = []

    print("JOB ::::::::::::: ", context.job.data)
    print(
        "bot-data :::::::::::::::::::::::::::",
        context.bot_data[job_context.media_group_id],
    )

    for file in context.bot_data[job_context.media_group_id]:
        print(file)
        files.append(file)

    original_caption = files[0].caption

    replies = get_replies(context.bot_data, str(job_context.message_id))
    print("::::::::::: share in other ::::::::::")
    print(replies)

    for lang in languages:
        files[0].caption = (
                translate_message(lang.lang_key, original_caption, lang.lang_key_deepl) + "\n" + lang.footer
        )

        try:
            msgs: [Message] = await context.bot.send_media_group(
                chat_id=lang.channel_id,
                media=files,
                reply_to_message_id=replies[lang.lang_key]
                if replies is not None
                else None,
            )

            print(msgs)

            context.bot_data[str(job_context.message_id)]["langs"][lang.lang_key] = msgs[0].message_id
        except Exception as e:
            await context.bot.send_message(
                config.LOG_GROUP,
                f"<b>⚠️ Error when trying to send media group in Channel {lang.lang_key}</b>\n\n"
                f"<code>{e}</code>",
            )

    print("----- done -----")

    del context.bot_data[job_context.media_group_id]


async def edit_channel(update: Update, context: CallbackContext):
    if update.edited_channel_post.caption is not None:
        original_caption = re.sub(
            WHITESPACE,
            "",
            re.sub(
                HASHTAG,
                "",
                update.edited_channel_post.caption_html_urled.replace(
                    GERMAN.footer, ""
                ),
            ),
        )

        for lang in languages:
            try:
                await context.bot.edit_message_caption(
                    chat_id=lang.channel_id,
                    message_id=context.bot_data[
                        str(update.edited_channel_post.message_id)
                    ]["langs"][lang.lang_key],
                    caption=f"{translate_message(lang.lang_key, original_caption, lang.lang_key_deepl)}\n{lang.footer}",
                )
            except TelegramError as e:
                if not e.message.startswith("Message is not modified"):
                    await context.bot.send_message(
                        config.LOG_GROUP,
                        f"<b>⚠️ Error when trying to edit post in Channel {lang.lang_key}</b>\n"
                        f"<code>{e}</code>\n\n<b>Caused by Update</b>\n<code>{update}</code>",
                    )

    # update.channel_post.edit_caption(flag_to_hashtag(original_caption) + FOOTER_DE)


@dataclass
class JobContext:
    media_group_id: str
    message_id: int


async def handle_url(update: Update, context: CallbackContext):
    if update.channel_post.caption is not None:
        entities = update.channel_post.parse_caption_entities(
            [MessageEntity.URL, MessageEntity.TEXT_LINK]
        )
    elif update.channel_post.text is not None:
        entities = update.channel_post.parse_entities(
            [MessageEntity.URL, MessageEntity.TEXT_LINK]
        )
    else:
        return

    print(entities)

    # TODO: maybe also remove the url/textlink from the initial message?

    if len(entities) == 0:
        return

    link = "folgenden Link" if len(entities) == 1 else "folgende Links"

    # fixme: change to channel_post
    text = (
        f"Öffnen Sie gerne {link}, wenn Sie mehr über die Geschehnisse in "
        f"<a href='https://t.me/militaernews/{update.channel_post.message_id}'>"
        "diesem Post</a> erfahren wollen:"
    )

    for entity, content in entities.items():
        print(entity)
        if entity.type == "text_link":
            quelle = f"<a href='{entity.url}'>{content}</a>"
        else:
            quelle = content

        text += f"\n\n· {quelle}"

    text += f"\n{GERMAN.footer}"

    print(text)

    await context.bot.send_message(
        chat_id=config.CHANNEL_SOURCE, text=text, disable_web_page_preview=False
    )


async def post_channel_text(update: Update, context: CallbackContext):
    if update.channel_post.message_id not in context.bot_data:
        print("::::: post channel text ::: new msg")
        context.bot_data[str(update.channel_post.message_id)] = {"langs": defaultdict(str)}

    # only index 0 should have reply_to_message -- check this!
    if update.channel_post.reply_to_message is not None:
        print("::::: post channel text ::: new reply")
        context.bot_data[str(update.channel_post.message_id)][
            "reply"
        ] = update.channel_post.reply_to_message.message_id

    original_caption = update.channel_post.text_html_urled

    replies = get_replies(context.bot_data, str(update.channel_post.message_id))

    for lang in languages:
        print(lang)
        print(context.bot_data[str(update.channel_post.message_id)])
        try:
            msg: Message = await context.bot.send_message(
                chat_id=lang.channel_id,
                text=translate_message(lang.lang_key, original_caption, lang.lang_key_deepl)
                     + "\n"
                     + lang.footer,
                reply_to_message_id=replies[lang.lang_key]
                if replies is not None
                else None,
            )

            print(msg.message_id)

            context.bot_data[str(update.channel_post.message_id)]["langs"][
                lang.lang_key
            ] = msg.message_id
        except Exception as e:
            await context.bot.send_message(
                config.LOG_GROUP,
                f"<b>⚠️ Error when trying to send text post in Channel {lang.lang_key}</b>\n"
                f"<code>{e}</code>\n\n<b>Caused by Update</b>\n<code>{update}</code>",
            )

    await handle_url(update, context)  # TODO: maybe extend to breaking and media_group

    try:
        await update.channel_post.edit_text(flag_to_hashtag(original_caption) + GERMAN.footer)
    except TelegramError as e:
        if not e.message.startswith("Message is not modified"):
            await context.bot.send_message(
                config.LOG_GROUP,
                f"<b>⚠️ Error when trying to post text in Channel de</b>\n"
                f"<code>{e}</code>\n\n<b>Caused by Update</b>\n<code>{update}</code>",
            )


async def edit_channel_text(update: Update, context: CallbackContext):
    original_caption = re.sub(
        WHITESPACE,
        "",
        re.sub(
            HASHTAG,
            "",
            update.edited_channel_post.text_html_urled.replace(GERMAN.footer, ""),
        ),
    )

    for lang in languages:
        try:
            await context.bot.edit_message_text(
                text=f"{translate_message(lang.lang_key, original_caption, lang.lang_key_deepl)}\n{lang.footer}",
                chat_id=lang.channel_id,
                message_id=context.bot_data[str(update.edited_channel_post.message_id)][
                    "langs"
                ][lang.lang_key],
            )
        except TelegramError as e:
            if not e.message.startswith("Message is not modified"):
                await context.bot.send_message(
                    config.LOG_GROUP,
                    f"<b>⚠️ Error when trying to edit post in Channel {lang.lang_key}</b>\n"
                    f"<code>{e}</code>\n\n<b>Caused by Update</b>\n<code>{update}</code>",
                )
