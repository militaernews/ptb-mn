import logging
import re

from telegram import Update
from telegram.ext import CallbackContext

from config import DIVIDER
from data.db import insert_single2
from data.lang import GERMAN, languages
from twitter import tweet_local_file
from util.helper import log_error
from util.patterns import BREAKING, PATTERN_HTMLTAG
from util.translation import translate_message, flag_to_hashtag, translate, segment_text


async def breaking_news(update: Update, context: CallbackContext):
    await update.channel_post.delete()

    text = re.sub(BREAKING, "", update.channel_post.text_html_urled)
    formatted_text = f"#{GERMAN.breaking} 🚨\n\n{flag_to_hashtag(text)}"
    breaking_photo_path = f"res/{GERMAN.lang_key}/breaking.png"

    try:
        # todo: reply??
        msg_de = await context.bot.send_photo(
            chat_id=GERMAN.channel_id,
            photo=open(breaking_photo_path, "rb"),
            caption=f"{formatted_text}{GERMAN.footer}",
        )
        await insert_single2(msg_de)
    except Exception as e:
        await log_error("send Breaking", context, GERMAN, e, update, )

    for lang in languages:
        caption = f"#{lang.breaking} 🚨\n\n{await translate_message(lang.lang_key, text, lang.lang_key_deepl)}"

        path = f"res/{lang.lang_key}/breaking.png"

        try:
            msg = await context.bot.send_photo(chat_id=lang.channel_id, photo=open(path, "rb"),
                                               caption=f"{caption}{DIVIDER}{lang.footer}")
            await insert_single2(msg, lang.lang_key)

            tweet_caption = segment_text(caption)
            await tweet_local_file(path, tweet_caption, lang.lang_key)
        except Exception as e:
            await log_error("send breaking", context, lang, e, update, )

    try:
        tweet_caption = segment_text(
            f"#{GERMAN.breaking} 🚨\n\n{flag_to_hashtag(re.sub(PATTERN_HTMLTAG, '', update.channel_post.text))}")
        await tweet_local_file(breaking_photo_path, tweet_caption, GERMAN.lang_key)
        logging.info("sent breaking to twitter")
    except Exception as e:
        await log_error("post breaking", context, "Twitter", e, update, )


async def announcement(update: Update, context: CallbackContext):
    await update.channel_post.delete()

    text = " 📢\n\n" + re.sub(
        re.compile(r"#mitteilung", re.IGNORECASE), "", update.channel_post.text_html_urled
    )

    try:
        msg_de = await context.bot.send_photo(
            chat_id=GERMAN.channel_id,
            photo=open(f"res/{GERMAN.lang_key}/announce.png", "rb"),
            caption=f"#MITTEILUNG{text}",
        )
        await insert_single2(msg_de)
        await msg_de.pin()

    except Exception as e:
        await log_error("send announcement", context, GERMAN, e, update, )

    for lang in languages:
        try:
            msg = await context.bot.send_photo(
                chat_id=lang.channel_id,
                photo=open(f"res/{lang.lang_key}/announce.png", "rb"),
                caption=f"#{lang.announce}{await translate_message(lang.lang_key, text, lang.lang_key_deepl)}",

            )
            await insert_single2(msg, lang.lang_key)
            await msg.pin()
        except Exception as e:
            await log_error("send announcement", context, lang, e, update, )


async def advertisement(update: Update, context: CallbackContext):
    await update.channel_post.delete()

    text = re.sub(
        re.compile(r"#werbung", re.IGNORECASE), "", update.channel_post.text_html_urled
    )

    try:
        msg_de = await context.bot.send_message(
            chat_id=GERMAN.channel_id,
            text=f"#{GERMAN.advertise}\n\n{text}",
            disable_web_page_preview=False
        )
        await insert_single2(msg_de)
        await msg_de.pin()

    except Exception as e:
        await log_error("send advertisement", context, GERMAN, e, update, )

    for lang in languages:
        try:
            msg = await context.bot.send_message(
                chat_id=lang.channel_id,
                text=f"#{lang.advertise}\n\n{await translate(lang.lang_key, text, lang.lang_key_deepl)}",
                disable_web_page_preview=False
            )
            await insert_single2(msg, lang.lang_key)
            await msg.pin()
        except Exception as e:
            await log_error("send advertisement", context, lang, e, update, )


async def post_info(update: Update, context: CallbackContext):
    logging.info("---- post info ----")
    text = "🔰 MN-Hauptquartier\n\n" + re.sub(
        re.compile(r"#info", re.IGNORECASE), "", update.channel_post.caption_html_urled
    )

    try:
        msg = await update.channel_post.edit_caption(text)
        await msg.pin()
    except Exception as e:
        await log_error("send info", context, GERMAN, e, update, )
