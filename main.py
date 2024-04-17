import asyncio
import logging
import os
import re
import sys

from telegram import LinkPreviewOptions  # LinkPreviewOptions,
from telegram.constants import ParseMode
from telegram.ext import MessageHandler, Defaults, ApplicationBuilder, filters, CommandHandler, PicklePersistence, \
    CallbackQueryHandler

import config
from data.lang import GERMAN
from dev.playground import flag_to_hashtag_test
from messages.chat.bingo import bingo_field, reset_bingo
from messages.chat.command import donbas, commands, sofa, maps, short, report_user, genozid, \
    loss, peace, bias, ref, bot, mimimi, cia, stats, duden, sold, argu, disso, front, pali
from messages.chat.filter import remove_command
from messages.meme import post_media_meme, post_text_meme
from messages.news.common import edit_channel, post_channel_english
from messages.news.special import breaking_news, announcement, post_info, advertisement
from messages.news.text import edit_channel_text, post_channel_text
from messages.private.advertise import add_advertisement_handler
from messages.private.promo import start_promo, verify_promo, send_promos
from messages.private.setup import set_cmd  # , private_setup


def add_logging():
    os.makedirs(os.path.dirname(config.LOG_FILENAME), exist_ok=True)
    logging.basicConfig(
        format="%(asctime)s %(levelname)-5s %(funcName)-20s [%(filename)s:%(lineno)d]: %(message)s",
        encoding="utf-8",
        filename=config.LOG_FILENAME,
        level=logging.DEBUG,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    # logging.getLogger(__name__).setLevel(logging.DEBUG)
    logging.getLogger("httpx").setLevel(logging.WARNING)


if __name__ == "__main__":
    add_logging()

    if sys.version_info >= (3, 8) and sys.platform.lower().startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    app = (ApplicationBuilder().token(config.TOKEN)
           .defaults(Defaults(parse_mode=ParseMode.HTML, link_preview_options=LinkPreviewOptions(is_disabled=True)))
           .persistence(PicklePersistence(filepath="persistence"))
           # .read_timeout(20).get_updates_read_timeout(20)
           .build())

    app.add_handler(add_advertisement_handler)

    app.add_handler(CommandHandler("bingo", bingo_field, filters.User(config.BINGO_ADMINS)))
    # app.add_handler(MessageHandler(filters.ATTACHMENT & filters.Chat(config.ADMINS), private_setup))
    app.add_handler(CommandHandler("reset_bingo", reset_bingo, filters.Chat(config.ADMINS)))
    app.add_handler(CommandHandler("set_cmd", set_cmd, filters.Chat(config.ADMINS)))

    app.add_handler(MessageHandler(filters.Regex(r"\/start promo_\w{2}(_\d+)?"), start_promo))
    app.add_handler(CallbackQueryHandler(verify_promo, r"promo_\w{2}(_\d+)?"))
    app.add_handler(CommandHandler("promo", send_promos, filters.Chat(config.ADMINS)))

    media = (filters.PHOTO | filters.VIDEO | filters.ANIMATION)

    meme_post = filters.UpdateType.CHANNEL_POST & filters.Chat(chat_id=config.CHANNEL_MEME)

    app.add_handler(MessageHandler(meme_post & media, post_media_meme))
    app.add_handler(MessageHandler(meme_post & filters.TEXT, post_text_meme))

    news_post = filters.UpdateType.CHANNEL_POST & filters.Chat(chat_id=GERMAN.channel_id)

    app.add_handler(
        MessageHandler(news_post & media & filters.CaptionRegex(re.compile(r"#info", re.IGNORECASE)), post_info))

    app.add_handler(MessageHandler(news_post & media, post_channel_english))

    app.add_handler(MessageHandler(news_post & filters.TEXT & filters.Regex(re.compile(r"#eilmeldung", re.IGNORECASE)),
                                   breaking_news))
    app.add_handler(MessageHandler(news_post & filters.TEXT & filters.Regex(re.compile(r"#mitteilung", re.IGNORECASE)),
                                   announcement))
    app.add_handler(
        MessageHandler(news_post & filters.TEXT & filters.Regex(re.compile(r"#werbung", re.IGNORECASE)), advertisement))
    app.add_handler(MessageHandler(news_post & filters.TEXT, post_channel_text))

    news_edited = filters.UpdateType.EDITED_CHANNEL_POST & filters.Chat(
        chat_id=GERMAN.channel_id) & ~filters.CaptionRegex(
        re.compile(r"🔰 MN-Hauptquartier|#\S+|MN-Team", re.IGNORECASE))

    app.add_handler(MessageHandler(news_edited & media, edit_channel))
    app.add_handler(MessageHandler(news_edited & filters.TEXT, edit_channel_text))

    app.add_handler(CommandHandler("maps", maps))
    app.add_handler(CommandHandler("donbas", donbas))
    app.add_handler(CommandHandler("cmd", commands))
    app.add_handler(CommandHandler("loss", loss))
    app.add_handler(CommandHandler("peace", peace))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("short", short))
    app.add_handler(CommandHandler("bias", bias))
    app.add_handler(CommandHandler("sold", sold))
    app.add_handler(CommandHandler("genozid", genozid))

    app.add_handler(CommandHandler("sofa", sofa))
    app.add_handler(CommandHandler("bot", bot))
    app.add_handler(CommandHandler("mimimi", mimimi))
    app.add_handler(CommandHandler("cia", cia))
    app.add_handler(CommandHandler("duden", duden))
    app.add_handler(CommandHandler("argu", argu))
    app.add_handler(CommandHandler("disso", disso))
    app.add_handler(CommandHandler("front", front))
    app.add_handler(CommandHandler("pali", pali))

    app.add_handler(MessageHandler(filters.Regex("/ref.*"), ref))

    # app.add_handler(CommandHandler("warn", warn_user, filters.Chat(GERMAN.chat_id)))
    # app.add_handler(CommandHandler("unwarn", unwarn_user, filters.Chat(GERMAN.chat_id)))
    # app.add_handler(CommandHandler("ban", ban_user, filters.Chat(GERMAN.chat_id)))
    app.add_handler(CommandHandler("report", report_user, filters.Chat(GERMAN.chat_id)))

    ##  app.add_handler(MessageHandler(
    ##   filters.UpdateType.MESSAGE & filters.TEXT & filters.Chat(GERMAN.chat_id) & ~filters.User(ADMINS),
    ##   filter_message))

    #  app.add_handler(CallbackQueryHandler(click_captcha, r"captcha_.+_.+", ))
    #  app.add_handler(ChatMemberHandler(send_captcha, ChatMemberHandler.CHAT_MEMBER))
    #  app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS & filters.Chat(GERMAN.chat_id), send_captcha))
    #   app.add_handler(CommandHandler("captcha", send_captcha, filters.Chat(config.ADMINS)))

    ##  app.add_handler(MessageHandler(
    ##      filters.UpdateType.MESSAGE & filters.TEXT & filters.Chat([
    ##      -1001618190222,  # Ukraine Russland Krieg Chat
    ##        -1001755040391  # Vitaliks Fanclub
    ##   ]), handle_other_chats))

    # Commands have to be added above
    #  app.add_error_handler( report_error)  # comment this one out for full stacktrace

    app.add_handler(MessageHandler(filters.Chat(config.ADMINS), flag_to_hashtag_test))

    app.add_handler(MessageHandler(filters.Regex(r"^\/([^@\s]+)@?(?:(\S+)|)\s?([\s\S]*)$"), remove_command))

    print("### RUN LOCAL ###")
    app.run_polling(poll_interval=1, drop_pending_updates=False)
