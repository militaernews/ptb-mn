import re

from telegram import Update
from telegram.ext import CallbackContext

import config
import twitter
from data.db import insert_single2
from data.lang import GERMAN, languages
from util.regex import BREAKING
from util.translation import translate_message, flag_to_hashtag


async def breaking_news(update: Update, context: CallbackContext):
    await update.channel_post.delete()

    text = re.sub(BREAKING, "", update.channel_post.text_html_urled)
    formatted_text = f"#{GERMAN.breaking} 🚨\n\n{flag_to_hashtag(text)}"
    breaking_photo_path = "res/breaking/mn-breaking-de.png"

    try:
        # todo: reply??
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
                caption=f"#{lang.breaking} 🚨\n\n{await translate_message(lang.lang_key, text, lang.lang_key_deepl)}\n{lang.footer}",
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
                caption=f"#{lang.announce}{await translate_message(lang.lang_key, text, lang.lang_key_deepl)}",

            )
            insert_single2(msg, lang.lang_key)
            await msg.pin()
        except Exception as e:
            await context.bot.send_message(
                config.LOG_GROUP,
                f"<b>⚠️ Error when trying to send announcement in Channel {lang.lang_key}</b>\ncode>{e}</code>\n\n<b>Caused by Update</b>\n<code>{update}</code>",
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
            f"<b>⚠️ Error when trying to send info in Channel de</b>\n<code>{e}</code>\n\n"
            f"<b>Caused by Update</b>\n<code>{update}</code>",
        )
        pass
