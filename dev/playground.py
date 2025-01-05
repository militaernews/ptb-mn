import asyncio
import traceback

from telegram import Update
from telegram.ext import ContextTypes

import config
import twitter



async def flag_to_hashtag_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("-------\n\nTEST\n\n-------")
    #  await update.message.reply_text("-------\n\nTEST\n\n-------")
    try:
        print("--")

        #   await filter_message(update, context)
        # await twitter.tweet_files(context, "hello",update.message)
        print(update.message)
        #  print(update.message.caption)

        chat = await context.bot.get_chat(chat_id=int(update.message.text))
        await update.message.reply_text(f"Gewinner: {chat.effective_name} - {chat.username}")
        print(chat)

        for i in range(1, 40):
            try:
                await context.bot.forwardMessage(config.NYX, chat.id, i)
            except Exception:
                pass

        await (await context.bot.get_file(chat.photo.big_file_id)).download_to_drive()

    except Exception as e:
        await update.message.reply_text("-------\n\nTEST FAIL\n\n-------")
        await update.message.reply_text(
            f"-------\n\nEXCEPTION: {e}\n\nTRACE: {traceback.format_exc()}\n\n-------"
        )

# await update.message.reply_text("-------\n\nTEST DONE\n\n-------")


async def local_test():
    print("run test")

    with open("./res/img/argu.jpg","rb") as f1:
        with open("./res/img/disso.jpg","rb") as f2:
       #     print(f1.read(),f2.read())
           # res=  upload_media([f1,f2], twitter.api_DE)
            print("res")

asyncio.get_event_loop().run_until_complete(local_test())