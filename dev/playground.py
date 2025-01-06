import asyncio
import traceback
import datetime

from telegram import Update, Message, Chat, PhotoSize, LinkPreviewOptions
from telegram.constants import ChatType, ParseMode
from telegram.ext import ContextTypes, CallbackContext, ApplicationBuilder, PicklePersistence, Defaults

import config
from data.lang import GERMAN, ENGLISH
from twitter import tweet_file


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
    update = Update(channel_post=Message(caption='🇱🇮 Test', channel_chat_created=False,
                                chat=Chat(id=-1001240262412, title='🔰 Militär-News', type=  ChatType.CHANNEL ,
                                username='militaernews'),
           date=datetime.datetime(2025, 1, 6, 3, 51, 43, tzinfo=datetime.timezone.utc), delete_chat_photo=False,
           group_chat_created=False, message_id=30770, photo=(
        PhotoSize(file_id='AgACAgIAAx0CSeznDAACeC9ne1K2Zwi2lQdvZx3ipYGs4OW43QACnewxG-Cy2Uss4Qw5VMC-AgEAAwIAA3MAAzYE',
                  file_size=1049, file_unique_id='AQADnewxG-Cy2Ut4', height=51, width=90),
        PhotoSize(file_id='AgACAgIAAx0CSeznDAACeC9ne1K2Zwi2lQdvZx3ipYGs4OW43QACnewxG-Cy2Uss4Qw5VMC-AgEAAwIAA20AAzYE',
                  file_size=14082, file_unique_id='AQADnewxG-Cy2Uty', height=180, width=320),
        PhotoSize(file_id='AgACAgIAAx0CSeznDAACeC9ne1K2Zwi2lQdvZx3ipYGs4OW43QACnewxG-Cy2Uss4Qw5VMC-AgEAAwIAA3gAAzYE',
                  file_size=53587, file_unique_id='AQADnewxG-Cy2Ut9', height=449, width=800),
        PhotoSize(file_id='AgACAgIAAx0CSeznDAACeC9ne1K2Zwi2lQdvZx3ipYGs4OW43QACnewxG-Cy2Uss4Qw5VMC-AgEAAwIAA3kAAzYE',
                  file_size=94859, file_unique_id='AQADnewxG-Cy2Ut-', height=718, width=1280)),
           sender_chat=Chat(id=-1001240262412, title='🔰 Militär-News', type=  ChatType.CHANNEL ,
           username='militaernews'), supergroup_chat_created = False), update_id = 171625171)

    app = (ApplicationBuilder().token(config.TOKEN)
           .defaults(Defaults(parse_mode=ParseMode.HTML, link_preview_options=LinkPreviewOptions(is_disabled=True)))
           .persistence(PicklePersistence(filepath="persistence"))
           .read_timeout(50).get_updates_read_timeout(50)
           .build())

   # await tweet_file(None, None,"Test", ENGLISH.lang_key,"./res/en/breaking.png")
    await tweet_file(update, CallbackContext(app), "Test2", ENGLISH.lang_key)

import contextlib
if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(local_test())
