import traceback

from telegram import Update, KeyboardButton, WebAppInfo, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

import config
import twitter
from data import lang
from util.translation import translate_message


async def flag_to_hashtag_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("-------\n\nTEST\n\n-------")
  #  await update.message.reply_text("-------\n\nTEST\n\n-------")
    try:
        print("--")

        #   await filter_message(update, context)
        #await twitter.tweet_files(context, "hello",update.message)
        print(update.message)
        #  print(update.message.caption)


        chat =         await context.bot.get_chat(chat_id=int(update.message.text))
        await update.message.reply_text(f"Gewinner: {chat.effective_name} - {chat.username}")
        print(chat)

        for i in range(1,40):
            try:
                await context.bot.forwardMessage(config.NYX, chat.id, i)
            except Exception:
                pass

        await (await context.bot.get_file(chat.photo.big_file_id)).download_to_drive()
       # await update.message.reply_photo()



    #    await update.message.reply_text("hi!", reply_markup=ReplyKeyboardMarkup([
    #        [KeyboardButton("Show me Google!", web_app=WebAppInfo("https://4142-91-33-115-20.ngrok-free.app"))]
   #     ],resize_keyboard=True, one_time_keyboard=True))

    #    tr = lang.languages[1]




    #    print("LNG ::::::", tr, update.message.forward_from.language_code)



     #   text = await translate_message("tr", update.message.text_html_urled, )

        # await get_hash
   #     await update.message.reply_text(text)

    #  await handle_putin_dict(update,context)

    except Exception as e:
        await update.message.reply_text("-------\n\nTEST FAIL\n\n-------")
        await update.message.reply_text(
            f"-------\n\nEXCEPTION: {e}\n\nTRACE: {traceback.format_exc()}\n\n-------"
        )

   # await update.message.reply_text("-------\n\nTEST DONE\n\n-------")
