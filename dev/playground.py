import traceback

from telegram import Update
from telegram.ext import ContextTypes

import twitter
from data import lang
from util.translation import translate_message


async def flag_to_hashtag_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("-------\n\nTEST\n\n-------")
    await update.message.reply_text("-------\n\nTEST\n\n-------")
    try:
        print("--")

        #   await filter_message(update, context)
        await twitter.tweet_file_3("hello","field.png")
        print(update.message)
        #  print(update.message.caption)

        tr = lang.languages[1]
        print("LNG ::::::", tr, update.message.forward_from.language_code)

        await context.bot.send_message(tr.channel_id, "test")

        text = await translate_message("tr", update.message.text_html_urled, )

        # await get_hash
        await update.message.reply_text(text)

    #  await handle_putin_dict(update,context)

    except Exception as e:
        await update.message.reply_text("-------\n\nTEST FAIL\n\n-------")
        await update.message.reply_text(
            f"-------\n\nEXCEPTION: {e}\n\nTRACE: {traceback.format_exc()}\n\n-------"
        )

    await update.message.reply_text("-------\n\nTEST DONE\n\n-------")
