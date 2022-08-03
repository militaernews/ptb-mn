import traceback

from telegram import Update
from telegram.ext import ContextTypes

import twitter


async def flag_to_hashtag_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("-------\n\nTEST\n\n-------")
    await update.message.reply_text("-------\n\nTEST\n\n-------")
    try:

        #   await update.message.reply_text(        translate_message("tr", update.message.text_html_urled))

        p = update.message.photo

        for pp in p:
            print(pp)

        f = await context.bot.get_file(update.message.photo[-1].file_id)
        # can use param "out" in download() to instead save to object, idk if that makes sense for twitter.
        ff = await f.download(f"../temp/")
        print(ff)
        await twitter.tweet_photo("", f)

    # await context.bot.send_photo(chat_id=NYX, photo=f.file_path)

    # twitter.tweet_photo(f.file_path)

    #   for lang in languages:
    #      await update.message.reply_text(flag_to_hashtag(update.message.text_html_urled, lang.lang_key))
    except Exception as e:
        await update.message.reply_text("-------\n\nTEST FAIL\n\n-------")
        await update.message.reply_text(
            f"-------\n\nEXCEPTION: {e}\n\nTRACE: {traceback.format_exc()}\n\n-------"
        )

    await update.message.reply_text("-------\n\nTEST DONE\n\n-------")
