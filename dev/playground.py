import traceback

from telegram import Update
from telegram.ext import ContextTypes
from wand.image import Image

from messages import bingo


async def flag_to_hashtag_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("-------\n\nTEST\n\n-------")
    await update.message.reply_text("-------\n\nTEST\n\n-------")
    try:
        print("--")

        # await update.message.reply_text(translate_message("de", update.message.text_html_urled, None))

        with open("dev/bitmap.svg", "rb") as f:
            with Image(blob=f.read(), format="svg") as image:
                png_image = image.make_blob("png")

                await update.message.reply_photo(photo=png_image)

        if "bingo" not in context.bot_data:
            context.bot_data["bingo"] = bingo.generate_bingo_field()
        bingo.set_checked(update.message.text, context.bot_data["bingo"])

        await update.message.reply_text(str(bingo.check_win(context.bot_data["bingo"])))


    except Exception as e:
        await update.message.reply_text("-------\n\nTEST FAIL\n\n-------")
        await update.message.reply_text(
            f"-------\n\nEXCEPTION: {e}\n\nTRACE: {traceback.format_exc()}\n\n-------"
        )

    await update.message.reply_text("-------\n\nTEST DONE\n\n-------")
