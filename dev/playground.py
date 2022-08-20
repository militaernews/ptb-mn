import traceback

import cairosvg
from telegram import Update
from telegram.ext import ContextTypes

from data.lang import GERMAN
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

        cairosvg.svg2png(bytestring=create_svg(context.bot_data["bingo"]), write_to='dev/my.png',
                         background_color="#00231e")

        with open("dev/my.png", "rb") as f:
            await update.message.reply_photo(photo=f,
                                             caption=f"<b>Militär-News Bullshit-Bingo</b>\n\nWenn eine im @MNChat gesendete Nachricht auf dem Spielfeld vorkommendende Begriffe enthält, werden diese rausgestrichen.\n\nIst eine gesamte Zeile oder Spalte durchgestrichen, dann heißt es <b>BINGO!</b> und eine neue Runde startet.\n{GERMAN.footer}")

        if bingo.check_win(context.bot_data["bingo"]):
            with open("dev/my.png", "rb") as f:
                await update.message.reply_photo(photo=f,
                                                 caption=f"<b>BINGO! 🥳</b>\n\n {update.message.from_user.name} hat den letzten Begriff beigetragen. So sah das Spielfeld am Ende aus.\n\nEine neue Runde beginnt...\n{GERMAN.footer}")
            context.bot_data["bingo"] = bingo.generate_bingo_field()



    except Exception as e:
        await update.message.reply_text("-------\n\nTEST FAIL\n\n-------")
        await update.message.reply_text(
            f"-------\n\nEXCEPTION: {e}\n\nTRACE: {traceback.format_exc()}\n\n-------"
        )

    await update.message.reply_text("-------\n\nTEST DONE\n\n-------")
