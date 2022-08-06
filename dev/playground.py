import os
import traceback

import pytweet
from telegram import Update
from telegram.ext import ContextTypes


async def flag_to_hashtag_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("-------\n\nTEST\n\n-------")
    await update.message.reply_text("-------\n\nTEST\n\n-------")
    try:
        print("--")

        with open('temp/test.txt', 'w') as f:
            f.write('test123')

        with open('temp/test.txt', 'r') as f:
            print(f.read())

        with open('temp/test2.txt', 'r') as f:
            print(f.read())

        if len(update.message.photo) > 0:
            file = await update.message.photo[-1].get_file()
        elif update.message.video is not None:
            file = await update.message.video.get_file()

        path = f"./temp/{file.file_path.split('/')[-1]}"
        print("file to download:::: ", path)
        await file.download(path)
        print("-- download done")
        f = pytweet.File(path)
        print(f.path)
        # os.remove(path)

    except Exception as e:
        await update.message.reply_text("-------\n\nTEST FAIL\n\n-------")
        await update.message.reply_text(
            f"-------\n\nEXCEPTION: {e}\n\nTRACE: {traceback.format_exc()}\n\n-------"
        )

    await update.message.reply_text("-------\n\nTEST DONE\n\n-------")
