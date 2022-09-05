import re

from telegram import (InputMedia, InputMediaAnimation, InputMediaPhoto,
                      InputMediaVideo, Message, MessageEntity, MessageId,
                      Update)
from telegram.error import TelegramError
from telegram.ext import CallbackContext

import config
import twitter
from data.db import insert_single3, query_replies, insert_single2, query_replies3, \
    get_post_id, query_files, PHOTO, VIDEO, ANIMATION, get_post_id2, query_replies4, get_msg_id
from data.lang import GERMAN, languages
from util.helper import sanitize_text, get_file
from util.regex import HASHTAG, WHITESPACE, BREAKING
from util.translation import flag_to_hashtag, translate_message


# TODO: make method more generic
async def post_channel_single(update: Update, context: CallbackContext, de_post_id: int):
    post_id = get_post_id(update.channel_post)
    original_caption = sanitize_text(update.channel_post.caption_html_urled)

    for lang in languages:
        print(lang)

        reply_id = query_replies4(update.channel_post, lang.lang_key)  # query_replies3(post_id, lang.lang_key)
        print("--- SINGLE ---", post_id, reply_id, lang.lang_key)

        try:

            msg_id: MessageId = await update.channel_post.copy(
                chat_id=lang.channel_id,
                caption=f"{translate_message(lang.lang_key, original_caption, lang.lang_key_deepl)}\n{lang.footer}",
                reply_to_message_id=reply_id
            )
            print("---------- MSG ID :::::::::", msg_id)
            insert_single3(msg_id.message_id, reply_id, update.channel_post, lang_key=lang.lang_key, post_id=de_post_id)

        except Exception as e:
            await context.bot.send_message(
                config.LOG_GROUP,
                "<b>⚠️ Error when trying to send single post in Channel "
                f"{lang.lang_key}</b>\n<code>{e}</code>\n\n"
                f"<b>Caused by Update</b>\n<code>{update}</code>",
            )
            pass

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
            pass

    try:

        # todo: upload photo aswell
        await twitter.tweet_file(formatted_text, await get_file(update))
        print("-")
    except Exception as e:
        await context.bot.send_message(
            config.LOG_GROUP,
            f"<b>⚠️ Error when trying to post single on Twitter</b>\n"
            f"<code>{e}</code>\n\n<b>Caused by Update</b>\n<code>{update}</code>",
        )
        pass

    await handle_url(update, context)  # TODO: maybe extend to breaking and media_group


# TODO: make method more generic
async def post_channel_english(update: Update, context: CallbackContext):
    post_id = insert_single2(update.channel_post)

    if update.channel_post.media_group_id is None:
        await post_channel_single(update, context, post_id)
        return

    for job in context.job_queue.get_jobs_by_name(update.channel_post.media_group_id):
        print("--- job gone ::::::::")
        job.schedule_removal()

    if update.channel_post.caption is not None:
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
            pass

    if update.channel_post.reply_to_message is not None:
        reply_id = update.channel_post.reply_to_message.id
    else:
        reply_id = None

    context.job_queue.run_once(
        share_in_other_channels,
        10,
        reply_id,
        update.channel_post.media_group_id
    )


async def breaking_news(update: Update, context: CallbackContext):
    await update.channel_post.delete()

    text = re.sub(BREAKING, "", update.channel_post.text_html_urled)
    formatted_text = f"#{GERMAN.breaking}\n\n{flag_to_hashtag(text)}"
    breaking_photo_path = "res/breaking/mn-breaking-de.png"

    try:
        msg_de = await context.bot.send_photo(
            chat_id=GERMAN.channel_id,
            photo=open(breaking_photo_path, "rb"),
            caption=f"{formatted_text}{GERMAN.footer}",
        )
        insert_single2(msg_de)
    except Exception as e:
        await context.bot.send_message(
            config.LOG_GROUP,
            f"<b>⚠️ Error when trying to send breaking news in channel DE</b>\n"
            f"<code>{e}</code>\n\n<b>Caused by Update</b>\n<code>{update}</code>",
        )
        pass

    for lang in languages:
        try:
            msg = await context.bot.send_photo(
                chat_id=lang.channel_id,
                photo=open(f"res/breaking/mn-breaking-{lang.lang_key}.png", "rb"),
                caption=f"#{lang.breaking}\n\n{translate_message(lang.lang_key, text, lang.lang_key_deepl)}\n{lang.footer}",
            )
            insert_single2(msg, lang.lang_key)
        except Exception as e:
            await context.bot.send_message(
                config.LOG_GROUP,
                f"<b>⚠️ Error when trying to send breaking news in channel {lang.lang_key}</b>\n"
                f"<code>{e}</code>\n\n<b>Caused by Update</b>\n<code>{update}</code>",
            )

    try:
        await twitter.tweet_file_3(formatted_text, breaking_photo_path)
        print("-")
    except Exception as e:
        await context.bot.send_message(
            config.LOG_GROUP,
            f"<b>⚠️ Error when trying to post breaking on Twitter</b>\n"
            f"<code>{e}</code>\n\n<b>Caused by Update</b>\n<code>{update}</code>",
        )
        pass


async def announcement(update: Update, context: CallbackContext):
    await update.channel_post.delete()

    text = " 📢\n\n" + re.sub(
        re.compile(r"#mitteilung", re.IGNORECASE), "", update.channel_post.text_html
    )

    try:
        msg_de = await context.bot.send_photo(
            chat_id=GERMAN.channel_id,
            photo=open("res/announce/mn-announce-de.png", "rb"),
            caption="#MITTEILUNG" + text,
        )
        insert_single2(msg_de)
        await msg_de.pin()

    except Exception as e:
        await context.bot.send_message(
            config.LOG_GROUP,
            f"<b>⚠️ Error when trying to send announcement in channel DE</b>\n"
            f"<code>{e}</code>\n\n<b>Caused by Update</b>\n<code>{update}</code>",
        )
        pass

    for lang in languages:
        try:
            msg = await context.bot.send_photo(
                chat_id=lang.channel_id,
                photo=open(f"res/announce/mn-announce-{lang.lang_key}.png", "rb"),
                caption=f"#{lang.announce}{translate_message(lang.lang_key, text, lang.lang_key_deepl)}",

            )
            insert_single2(msg, lang.lang_key)
            await msg.pin()
        except Exception as e:
            await context.bot.send_message(
                config.LOG_GROUP,
                f"<b>⚠️ Error when trying to send announcement in Channel {lang.lang_key}</b>\ncode>{e}</code>\n\n<b>Caused by Update</b>\n<code>{update}</code>",
            )
            pass


# TODO: make method more generic
async def share_in_other_channels(context: CallbackContext):
    posts = query_files(context.job.name)
    files: [InputMedia] = []

    for post in posts:
        print(post)

        if post.file_type == PHOTO:
            files.append(InputMediaPhoto(post.file_id))
        elif post.file_type == VIDEO:
            files.append(InputMediaVideo(post.file_id))
        elif post.file_type == ANIMATION:
            files.append(InputMediaAnimation(post.file_type))

    original_caption = posts[0].text

    print("::::::::::: share in other ::::::::::")
    post_id = get_post_id2(context.job.data)
    print(" ------------------------------------------- post_id:", post_id)

    for lang in languages:
        files[0].caption = (
                translate_message(lang.lang_key, original_caption, lang.lang_key_deepl) + "\n" + lang.footer
        )

        reply_id = query_replies3(post_id, lang.lang_key)
        print(" ------------------------------------------- reply_id:", reply_id)

        try:
            msgs: [Message] = await context.bot.send_media_group(
                chat_id=lang.channel_id,
                media=files,
                reply_to_message_id=reply_id
            )

            print(msgs)

            for index, msg in enumerate(msgs):
                insert_single3(msg.id, reply_id, msg, msg.media_group_id, lang_key=lang.lang_key,
                               post_id=posts[index].post_id)
        except Exception as e:
            await context.bot.send_message(
                config.LOG_GROUP,
                f"<b>⚠️ Error when trying to send media group in Channel {lang.lang_key}</b>\n\n"
                f"<code>{e}</code>",
            )
            pass

    print("----- done -----")

    # todo: tweet media_group


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
                msg_id = get_msg_id(update.edited_channel_post.id, lang.lang_key)
                await context.bot.edit_message_caption(
                    chat_id=lang.channel_id,
                    message_id=msg_id,
                    caption=f"{translate_message(lang.lang_key, original_caption, lang.lang_key_deepl)}\n{lang.footer}",
                )
            except TelegramError as e:
                if not e.message.startswith("Message is not modified"):
                    await context.bot.send_message(
                        config.LOG_GROUP,
                        f"<b>⚠️ Error when trying to edit post in Channel {lang.lang_key}</b>\n"
                        f"<code>{e}</code>\n\n<b>Caused by Update</b>\n<code>{update}</code>",
                    )
                    pass

        try:
            # not sure if this will cause eternal triggering, hopefully not
            await update.edited_channel_post.edit_caption(flag_to_hashtag(original_caption) + GERMAN.footer)
            # todo: update text in db
        except TelegramError as e:
            if not e.message.startswith("Message is not modified"):
                await context.bot.send_message(
                    config.LOG_GROUP,
                    f"<b>⚠️ Error when trying to edit post in Channel de</b>\n"
                    f"<code>{e}</code>\n\n<b>Caused by Update</b>\n<code>{update}</code>",
                )
                pass


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

    await context.bot.send_message(chat_id=config.CHANNEL_SOURCE, text=text, disable_web_page_preview=False)


async def post_channel_text(update: Update, context: CallbackContext):
    original_caption = sanitize_text(update.channel_post.text_html_urled)

    insert_single2(update.channel_post)

    print("orignal caption::::::::::", original_caption)

    for lang in languages:
        print(lang)

        reply_id = query_replies(update.channel_post.message_id, lang.lang_key)

        try:
            msg: Message = await context.bot.send_message(
                chat_id=lang.channel_id,
                text=f"{translate_message(lang.lang_key, original_caption, lang.lang_key_deepl)}\n{lang.footer}",
                reply_to_message_id=reply_id
            )
            insert_single2(msg, lang.lang_key)
        except Exception as e:
            await context.bot.send_message(
                config.LOG_GROUP,
                f"<b>⚠️ Error when trying to send text post in Channel {lang.lang_key}</b>\n"
                f"<code>{e}</code>\n\n<b>Caused by Update</b>\n<code>{update}</code>",
            )
            pass

    try:
        await update.channel_post.edit_text(f"{flag_to_hashtag(original_caption)}{GERMAN.footer}")
    except TelegramError as e:
        if not e.message.startswith("Message is not modified"):
            await context.bot.send_message(
                config.LOG_GROUP,
                f"<b>⚠️ Error when trying to post text in Channel de</b>\n"
                f"<code>{e}</code>\n\n<b>Caused by Update</b>\n<code>{update}</code>",
            )
            pass

    try:
        await twitter.tweet_text(flag_to_hashtag(sanitize_text(update.channel_post.text)))
    except Exception as e:
        await context.bot.send_message(
            config.LOG_GROUP,
            f"<b>⚠️ Error when trying to post text on Twitter</b>\n"
            f"<code>{e}</code>\n\n<b>Caused by Update</b>\n<code>{update}</code>",
        )
        pass

    await handle_url(update, context)  # TODO: maybe extend to breaking and media_group


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

    print("orignal caption::::::::::", original_caption)

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
                pass


async def post_info(update: Update, context: CallbackContext):
    print("---- post info ----")
    text = "🔰 MN-Hauptquartier\n\n" + re.sub(
        re.compile(r"#info", re.IGNORECASE), "", update.channel_post.caption_html_urled
    )

    try:
        msg = await update.channel_post.edit_caption(text)
        await msg.pin()
    except Exception as e:
        await context.bot.send_message(
            config.LOG_GROUP,
            "<b>⚠️ Error when trying to send info in Channel de</b>\n<code>{e}</code>\n\n"
            f"<b>Caused by Update</b>\n<code>{update}</code>",
        )
        pass
