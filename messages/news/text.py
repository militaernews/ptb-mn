import re
from mailbox import Message

from telegram import Update, MessageEntity
from telegram.constants import MessageEntityType
from telegram.error import TelegramError
from telegram.ext import CallbackContext

import config
import twitter
from data.db import query_replies, insert_single2, update_text, get_msg_id
from data.lang import languages, GERMAN
from messages.news.common import handle_url
from util.helper import sanitize_text
from util.regex import WHITESPACE, HASHTAG
from util.translation import translate_message, flag_to_hashtag


async def post_channel_text(update: Update, context: CallbackContext):
    original_caption = sanitize_text(update.channel_post.text_html_urled)

    insert_single2(update.channel_post)

    print("orignal caption::::::::::", original_caption)

    for lang in languages:
        #   print(lang)

        reply_id = query_replies(update.channel_post.message_id, lang.lang_key)

        try:
            msg: Message = await context.bot.send_message(
                chat_id=lang.channel_id,
                text=f"{await translate_message(lang.lang_key, original_caption, lang.lang_key_deepl)}\n{lang.footer}",
                reply_to_message_id=reply_id
            )
            insert_single2(msg, lang.lang_key)
        ##  print(lang.lang_key)
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
        print("tweet")
      #  await twitter.tweet_text(flag_to_hashtag(sanitize_text(update.channel_post.text)))
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

    update_text(update.edited_channel_post.id, f"{original_caption}\n{GERMAN.footer}")

    print("orignal caption::::::::::", original_caption)

    for lang in languages:
        try:
            translated_text = f"{await translate_message(lang.lang_key, original_caption, lang.lang_key_deepl)}\n{lang.footer}"
            msg_id = get_msg_id(update.edited_channel_post.id, lang.lang_key)
            await context.bot.edit_message_text(
                text=translated_text,
                chat_id=lang.channel_id,
                message_id=msg_id
            )

            update_text(msg_id, translated_text, lang.lang_key)
        except TelegramError as e:
            if not e.message.startswith("Message is not modified"):
                await context.bot.send_message(
                    config.LOG_GROUP,
                    f"<b>⚠️ Error when trying to edit post in Channel {lang.lang_key}</b>\n"
                    f"<code>{e}</code>\n\n<b>Caused by Update</b>\n<code>{update}</code>",
                )
                pass
