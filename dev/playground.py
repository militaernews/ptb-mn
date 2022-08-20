import traceback

from telegram import Update
from telegram.ext import ContextTypes
from wand.image import Image
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
from messages import bingo
from messages.bingo import create_svg


async def flag_to_hashtag_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("-------\n\nTEST\n\n-------")
    await update.message.reply_text("-------\n\nTEST\n\n-------")
    try:
        print("--")

        # await update.message.reply_text(translate_message("de", update.message.text_html_urled, None))

        if "bingo" not in context.bot_data:
            context.bot_data["bingo"] = bingo.generate_bingo_field()

        bingo.set_checked(update.message.text, context.bot_data["bingo"])

        with open("dev/field.svg", "w") as f:
            f.write(create_svg(context.bot_data["bingo"]))

        with open("dev/field.svg", "rb") as f:
            with Image(blob=f.read(), format="svg") as image:
                image.compression_quality = 100

                png_image = image.make_blob("jpg")

                await update.message.reply_photo(photo=png_image)

        drawing = svg2rlg("dev/field.svg")
        renderPM.drawToFile(drawing, "dev/my.jpg", fmt="JPG", bg=0x00231e)

        with open("dev/my.jpg", "rb") as f:
                await update.message.reply_photo(photo=f)

        await update.message.reply_text(str(bingo.check_win(context.bot_data["bingo"])))


    except Exception as e:
        await update.message.reply_text("-------\n\nTEST FAIL\n\n-------")
        await update.message.reply_text(
            f"-------\n\nEXCEPTION: {e}\n\nTRACE: {traceback.format_exc()}\n\n-------"
        )

    await update.message.reply_text("-------\n\nTEST DONE\n\n-------")
