import re

from deep_translator import GoogleTranslator
from telegram import Update, InputMediaVideo, InputMediaPhoto, InputMedia, ParseMode, InputMediaAnimation  #upm package(python-telegram-bot)
from telegram.ext import CallbackContext  #upm package(python-telegram-bot)
import pycountry  #upm package(pycountry)
import emoji  #upm package(emoji)
from lang import languages
import config

from flag import flags


def flag_to_hashtag_test(update: Update, context: CallbackContext):
  update.message.reply_text(flag_to_hashtag(update.message.text, "tr"))

def flag_to_hashtag(text: str, language: str) -> str:

    last = None

    text+="\n\n"

    for c in text:

        if is_flag_emoji(c):
            if last is not None:
                key = last + c
                if key in flags:        
                  text  += "#" + GoogleTranslator(source='en', target=language).translate(flags.get(key)).replace(" ", "") + " "

                last = None

            else:
                last = c

    return text


def translate_message(target_lang: str, text: str) -> str:
    translated_text = GoogleTranslator(source='de', target=target_lang).translate(text)

    return flag_to_hashtag(translated_text, target_lang)


def post_channel_english(update: Update, context: CallbackContext):
    if update.channel_post.media_group_id is None:
        original_post = update.channel_post
        original_caption = update.channel_post.caption_html_urled if update.channel_post.caption is not None else ''

        for lang in languages:
            original_post.copy(
                chat_id=lang.channel_id,
                caption=translate_message(lang.lang_key, original_caption) +
                "\n" + lang.footer)

        update.channel_post.edit_caption(
            f"{update.channel_post.caption_html_urled}\n🔰 Abonnieren Sie @MilitaerNews\n🔰 Tritt uns bei @MNChat"
        )
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
            InputMediaPhoto(media=update.channel_post.photo[-1].file_id,
                            parse_mode=ParseMode.HTML))
        print(
            "--- PHOTO ----------------------------------------------------------------"
        )
    elif update.channel_post.video:
        context.bot_data[update.channel_post.media_group_id].append(
            InputMediaVideo(media=update.channel_post.video.file_id,
                            parse_mode=ParseMode.HTML))
    elif update.channel_post.animation:
        context.bot_data[update.channel_post.media_group_id].append(
            InputMediaAnimation(media=update.channel_post.animation.file_id,
                                parse_mode=ParseMode.HTML))

    if update.channel_post.caption is not None:
        print("trans---SINGLE ::: ",
              translate_message("en", update.channel_post.caption))

        context.bot_data[update.channel_post.media_group_id][
            -1].caption = f"{update.channel_post.caption_html_urled}"

        update.channel_post.edit_caption(
            f"{update.channel_post.caption_html_urled}\n🔰 Abonnieren Sie @MilitaerNews\n🔰 Tritt uns bei @MNChat"
        )

    context.job_queue.run_once(share_in_other_channels, 20,
                               update.channel_post.media_group_id,
                               str(update.channel_post.media_group_id))


def breaking_news(update: Update, context: CallbackContext):
    update.channel_post.delete()
    context.bot.send_photo(
        chat_id=config.CHANNEL_DE,
        photo=open("res/breaking/mn-breaking-de.png", "rb"),
        caption=
        f"{update.channel_post.text}\n🔰 Abonnieren Sie @MilitaerNews\n🔰 Tritt uns bei @MNChat"
    )

    text = re.sub(re.compile(r"#eilmeldung", re.IGNORECASE), "",
                  update.channel_post.text_html)

    for lang in languages:
        context.bot.send_photo(
            chat_id=lang.channel_id,
            photo=open(f"res/breaking/mn-breaking-{lang.lang_key}.png", "rb"),
            caption="#" + lang.breaking + "\n\n" +
            translate_message(lang.lang_key, text) + "\n" + lang.footer)


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


def is_flag_emoji(c):
    return "🇦" <= c <= "🇿"
  
  #  return "\U0001F1E6\U0001F1E8" <= c <= "\U0001F1FF\U0001F1FC" or c in [
   #     "\U0001F3F4\U000e0067\U000e0062\U000e0065\U000e006e\U000e0067\U000e007f",
   #     "\U0001F3F4\U000e0067\U000e0062\U000e0073\U000e0063\U000e0074\U000e007f",
    #    "\U0001F3F4\U000e0067\U000e0062\U000e0077\U000e006c\U000e0073\U000e007f"
   # ]


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
