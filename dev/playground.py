import traceback

from telegram import Update
from telegram.ext import ContextTypes

from messages.chat.dictionary import handle_putin_dict
from messages.chat.filter import filter_message
from util.translation import translate, translate_message


async def flag_to_hashtag_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("-------\n\nTEST\n\n-------")
    await update.message.reply_text("-------\n\nTEST\n\n-------")
    try:
        print("--")

     #   await filter_message(update, context)

        print(update.message.caption)

        text = await translate_message("tr", update.message.text_html_urled,)

       # await get_hash
        await update.message.reply_text(text)

      #  await handle_putin_dict(update,context)



    except Exception as e:
        await update.message.reply_text("-------\n\nTEST FAIL\n\n-------")
        await update.message.reply_text(
            f"-------\n\nEXCEPTION: {e}\n\nTRACE: {traceback.format_exc()}\n\n-------"
        )

    await update.message.reply_text("-------\n\nTEST DONE\n\n-------")
