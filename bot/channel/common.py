import logging
from re import sub, findall
from typing import List

from data.db import (insert_single3, insert_single2, query_replies3,
                     get_post_id, query_files, get_post_id2, query_replies4, get_msg_id, get_file_id,
                     update_post, get_media_group_msg_ids)
from data.lang import GERMAN, LANGUAGES
from data.model import Post, PHOTO, VIDEO, ANIMATION
from settings.config import DIVIDER, CHANNEL_SOURCE
from social.twitter import tweet_files
from telegram import (InputMedia, InputMediaAnimation, InputMediaPhoto,
                      InputMediaVideo, MessageEntity, MessageId,
                      Update)
from telegram.error import TelegramError
from telegram.ext import CallbackContext, ContextTypes
from util.dictionary import replace_name
from util.helper import log_error, get_tg_file_id
from util.patterns import HASHTAG, WHITESPACE, PATTERN_HTMLTAG
from util.translation import flag_to_hashtag, translate_message, segment_text


# TODO: make method more generic
async def post_channel_single(update: Update, context: ContextTypes.DEFAULT_TYPE, de_post_id: int):
    post_id = await get_post_id(update.channel_post)
    original_caption = update.channel_post.caption_html_urled
    file_ids = [get_tg_file_id(update)]

    for lang in LANGUAGES:
        logging.info(lang)

        reply_id = await query_replies4(update.channel_post, lang.lang_key)  # query_replies3(post_id, lang.lang_key)
        logging.info(f"--- SINGLE --- {post_id, reply_id, lang.lang_key}")

        caption = f"{await translate_message(lang.lang_key, original_caption, lang.lang_key_deepl, lang_username=lang.username)}"

        try:
            msg_id: MessageId = await update.channel_post.copy(chat_id=lang.channel_id,
                                                               caption=f"{caption}{DIVIDER}{lang.footer}",
                                                               reply_to_message_id=reply_id)
            logging.info(f"---------- MSG ID ::::::::: {msg_id}")
            await insert_single3(msg_id.message_id, reply_id, update.channel_post, lang_key=lang.lang_key,
                                 post_id=de_post_id)

        except  Exception as e:
            await log_error("send single post", context, lang, e, update)
            pass

        try:
            tweet_caption = segment_text(PATTERN_HTMLTAG.sub("", caption))

            await tweet_files(file_ids, context.bot, tweet_caption, lang.lang_key)
        except Exception as e:
            await log_error(f"tweet {lang.lang_key}", context, "Twitter", e, update, )
            pass

    formatted_text = flag_to_hashtag(replace_name(original_caption))

    try:
        await update.channel_post.edit_caption(formatted_text + DIVIDER + GERMAN.footer)
    except TelegramError as e:
        if not e.message.startswith("Message is not modified"):
            await log_error("edit Post", context, GERMAN, e, update, )
            pass
    except Exception as e:
        await log_error(f"adding footer to post", context, GERMAN.lang_key, e, update, )
        pass

    try:
        tweet_caption = segment_text(flag_to_hashtag(PATTERN_HTMLTAG.sub("", original_caption)))
        await tweet_files(file_ids, context.bot, tweet_caption, GERMAN.lang_key)
        logging.info(f"-")
    except Exception as e:
        await log_error("tweet DE", context, "Twitter", e, update, )
        pass

    await handle_url(update, context)  # TODO: maybe extend to breaking and media_group


# TODO: make method more generic
async def post_channel_english(update: Update, context: CallbackContext):
    post_id = await insert_single2(update.channel_post)

    if update.channel_post.media_group_id is None:
        await post_channel_single(update, context, post_id)
        return

    for job in context.job_queue.get_jobs_by_name(update.channel_post.media_group_id):
        logging.info("--- job gone ::::::::")
        job.schedule_removal()

    if update.channel_post.caption is not None:
        try:
            await update.channel_post.edit_caption(
                flag_to_hashtag(update.channel_post.caption_html_urled) + DIVIDER + GERMAN.footer
            )
        except Exception as e:
            await log_error("edit Caption", context, GERMAN, e, update, )

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


# TODO: make method more generic
async def share_in_other_channels(context: CallbackContext):
    posts = sorted(await query_files(context.job.name), key=lambda x: x.msg_id)
    logging.info(posts)
    files: List[InputMedia] = []
    file_ids = []

    original_caption = None

    post: Post
    for post in posts:
        logging.info(post)

        if original_caption is None and post.text is not None:
            if len(findall(GERMAN.footer, post.text)) == 0:
                original_caption = post.text
            else:
                # todo: make it actually filter out footer
                original_caption = sub(fr"\s*({HASHTAG})*\s*{GERMAN.footer}", "", post.text)

        if post.file_type == PHOTO:
            files.append(InputMediaPhoto(post.file_id, has_spoiler=post.spoiler))
        elif post.file_type == VIDEO:
            files.append(InputMediaVideo(post.file_id, has_spoiler=post.spoiler))
        elif post.file_type == ANIMATION:
            files.append(InputMediaAnimation(post.file_id, has_spoiler=post.spoiler))
        file_ids.append(post.file_id)

    logging.info("::::::::::: share in other ::::::::::")
    post_id = await get_post_id2(context.job.data)  # not mediagroupid??
    logging.info(f"------------------------------------------- post_id: {post_id}")

    for lang in LANGUAGES:
        caption = f"{await translate_message(lang.lang_key, original_caption, lang.lang_key_deepl, lang_username=lang.username)}"
        logging.info(f"caption::::::::::: {caption}")
        with files[0]._unfrozen():
            files[0].caption = f"{caption}{DIVIDER}{lang.footer}"

        reply_id = await query_replies3(posts[0].post_id, lang.lang_key)
        logging.info(f"------------------------------------------- reply_id: {reply_id}")

        try:
            msgs = await context.bot.send_media_group(
                chat_id=lang.channel_id,
                media=files,
                reply_to_message_id=reply_id
            )

            logging.info(msgs)

            for index, msg in enumerate(msgs):
                await insert_single3(msg.id, reply_id, msg, msg.media_group_id, lang_key=lang.lang_key,
                                     post_id=posts[index].post_id)
        except Exception as e:
            await log_error("send media group", context, lang, e)

        try:
            await tweet_files(file_ids, context.bot,
                              segment_text(PATTERN_HTMLTAG.sub("", caption)),
                              lang.lang_key)
        except Exception as e:
            await log_error(f"tweet multiple {lang.lang_key}", context, "Twitter", e)

    logging.info("----- done -----")

    try:
        await tweet_files(file_ids, context.bot,
                          segment_text(flag_to_hashtag(PATTERN_HTMLTAG.sub("", original_caption))),
                          GERMAN.lang_key)
    except Exception as e:
        await log_error("tweet multiple DE", context, "Twitter", e)


async def edit_channel(update: Update, context: CallbackContext):
    edited = update.edited_channel_post

    if edited.caption is not None:
        original_caption = WHITESPACE.sub(
            "",
            HASHTAG.sub(
                "",
                edited.caption_html_urled.replace(GERMAN.footer, ""),
            ),
        )
    else:
        original_caption = None

    # Determine the new file from the edited post
    if len(edited.photo) > 0:
        new_file = await edited.photo[-1].get_file()
        input_media = InputMediaPhoto(new_file.file_id)
    elif edited.video is not None:
        # todo: file is too big
        new_file = await edited.video.get_file()
        input_media = InputMediaVideo(new_file.file_id)
    elif edited.animation is not None:
        new_file = await edited.animation.get_file()
        input_media = InputMediaAnimation(new_file.file_id)
    else:
        new_file = None
        input_media = None

    old_file_id = await get_file_id(edited.id)
    file_changed = new_file is not None and old_file_id != new_file.file_id

    # Determine whether this post belongs to a media group
    media_group_id = edited.media_group_id

    for lang in LANGUAGES:
        msg = None

        if media_group_id is not None:
            # For media groups, retrieve all message IDs in this album for the target language
            # and find the position of the edited DE message within the album so we can edit
            # the corresponding message in the other language channels.
            de_msg_ids = await get_media_group_msg_ids(media_group_id, GERMAN.lang_key)
            lang_msg_ids = await get_media_group_msg_ids(media_group_id, lang.lang_key)
            try:
                position = de_msg_ids.index(edited.id)
                msg_id = lang_msg_ids[position] if position < len(lang_msg_ids) else None
            except ValueError:
                msg_id = None
        else:
            msg_id = await get_msg_id(edited.id, lang.lang_key)

        if msg_id is None:
            continue

        try:
            if original_caption is not None:
                translated_text = f"{await translate_message(lang.lang_key, original_caption, lang.lang_key_deepl, lang_username=lang.username)}{DIVIDER}{lang.footer}"
            else:
                translated_text = None

            if input_media is not None:
                with input_media._unfrozen():
                    input_media.caption = translated_text

            msg = await context.bot.edit_message_caption(
                chat_id=lang.channel_id,
                message_id=msg_id,
                caption=translated_text
            )

        except TelegramError as e:
            if not e.message.startswith("Message is not modified"):
                await log_error("edit Caption", context, lang, e, update)

        if file_changed and input_media is not None and (
            original_caption is None or GERMAN.breaking not in original_caption
        ):
            try:
                logging.info(f"- edit file -------------------------------------------------- {input_media}")
                msg = await context.bot.edit_message_media(
                    input_media,
                    chat_id=lang.channel_id,
                    message_id=msg_id
                )
            except TelegramError as e:
                if not e.message.startswith("Message is not modified"):
                    await log_error("edit Media", context, lang, e, update)

        if msg is not None:
            await update_post(msg, lang.lang_key)

    try:
        # not sure if this will cause eternal triggering, hopefully not
        text = None if original_caption is None else flag_to_hashtag(original_caption)

        if edited.caption is not None and "#" not in edited.caption:
            await edited.edit_caption(text + DIVIDER + GERMAN.footer)

        await update_post(edited)
    except TelegramError as e:
        if not e.message.startswith("Message is not modified"):
            await log_error("edit Post", context, GERMAN, e, update)


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

    logging.info(entities)

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
        logging.info(entity)
        text += f"\n\n· "
        if entity.type == "text_link":
            text += f"<a href='{entity.url}'>{content}</a>"
        else:
            text += content

    text += f"\n{GERMAN.footer}"
    logging.info(text)
    await context.bot.send_message(chat_id=CHANNEL_SOURCE, text=text, disable_web_page_preview=False)
