from bot.app.data.lang import LANG_DICT
from telegram import Update
from telegram.ext import CallbackContext


async def join_folder(_: Update, context: CallbackContext):
    for lang in LANG_DICT.values():
        with open(f"./res/{lang.lang_key}/join.html", "r") as f:
            caption = f.read()

        msg = await context.bot.send_photo(lang.channel_id, open(f"./res/{lang.lang_key}/join.png", "rb"),
                                           caption=caption, show_caption_above_media=True)
        await msg.pin()
