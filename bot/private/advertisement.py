import logging
from typing import Sequence, Union, Final

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, PhotoSize, Animation, Video
from telegram.ext import CommandHandler, ConversationHandler, filters, MessageHandler, CallbackContext, ContextTypes, \
    Application

from ..data import lang
from ..settings.config import ADMINS
from ..util.translation import translate

ADVERTISEMENT_MEDIA: Final[str] = "new_ADVERTISEMENT_MEDIA"
ADVERTISEMENT_TEXT: Final[str] = "new_ADVERTISEMENT_TEXT"
ADVERTISEMENT_BUTTON: Final[str] = "new_ADVERTISEMENT_BUTTON"
ADVERTISEMENT_URL: Final[str] = "new_ADVERTISEMENT_URL"

NEEDS_MEDIA, NEEDS_TEXT, NEEDS_BUTTON, NEEDS_URL, SAVE_ADVERTISEMENT = range(5)


async def cancel(update: Update, _: CallbackContext) -> int:
    await update.message.reply_text("Werbung verworfen.")
    return ConversationHandler.END


async def add_advertisement(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.chat_data[ADVERTISEMENT_MEDIA] = None
    context.chat_data[ADVERTISEMENT_TEXT] = None
    context.chat_data[ADVERTISEMENT_BUTTON] = None
    context.chat_data[ADVERTISEMENT_URL] = None

    await update.message.reply_text(
        "Werbung erstellen.\n\nSende mir nun ein Bild oder Video.\n\nWenn du nur einen Text haben möchtest, dann drücke /skip.\n\nDen ganzen Vorgang kannst du mit /cancel abbrechen.")
    print(update, context.chat_data)
    return NEEDS_MEDIA


async def add_advertisement_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    print(update)
    logging.info(update.message.effective_attachment)

    context.chat_data[ADVERTISEMENT_MEDIA] = update.message.effective_attachment

    await update.message.reply_text(
        "Sende mir nun den Text der in der Werbung vorkommen soll.")

    return NEEDS_TEXT


async def skip_media(update: Update, _: CallbackContext) -> int:
    await update.message.reply_text(
        "Media hinzufügen übersprungen!\n\nSende mir nun den Text der in der Werbung vorkommen soll.")

    return NEEDS_TEXT


async def add_advertisement_text(update: Update, context: CallbackContext) -> int:
    context.chat_data[ADVERTISEMENT_TEXT] = update.message.text_html_urled

    await update.message.reply_text(
        "Sende mir nun den Text der auf dem Button unterhalb der Nachricht angezeigt werden soll.\n\nWenn die Werbung keinen Button haben soll, dann drücke /skip.")

    return NEEDS_BUTTON


async def send_preview(update: Update, context: CallbackContext, button: InlineKeyboardMarkup = None):
    media: Union[Animation, Sequence[PhotoSize], Video, None] = context.chat_data[ADVERTISEMENT_MEDIA]
    text = context.chat_data[ADVERTISEMENT_TEXT]

    try:
        if isinstance(media, Animation):
            await update.message.reply_animation(media, caption=text, reply_markup=button)
        elif isinstance(media, Sequence):
            await update.message.reply_photo(media[-1], caption=text, reply_markup=button)
        elif isinstance(media, Video):
            await update.message.reply_video(media, caption=text, reply_markup=button)
        else:
            await update.message.reply_text(text, reply_markup=button)

        await update.message.reply_text("Passt das soweit?"
                                        "\n\nSende den Werbungs-Post mit /save oder verwerfe ihn und beginne von vorn mit /cancel.")
    except Exception as e:
        await update.message.reply_text("Fehler beim Senden der Vorschau! Beginne von vorn mit /cancel."
                                        f"\n\n<code>{e}</code>")


async def skip_button(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Button hinzufügen übersprungen!")
    await send_preview(update, context)

    return SAVE_ADVERTISEMENT


async def add_advertisement_button(update: Update, context: CallbackContext) -> int:
    context.chat_data[ADVERTISEMENT_BUTTON] = update.message.text

    await update.message.reply_text("Sende mir nun die URL auf die der Button verlinken soll.")

    return NEEDS_URL


async def add_advertisement_url(update: Update, context: CallbackContext) -> int:
    context.chat_data[ADVERTISEMENT_URL] = update.message.text

    logging.info(context.chat_data)

    button = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton(context.chat_data[ADVERTISEMENT_BUTTON], url=context.chat_data[ADVERTISEMENT_URL]))

    await send_preview(update, context, button)

    return SAVE_ADVERTISEMENT


async def save_advertisement(update: Update, context: CallbackContext) -> int:
    media: Union[Animation, Sequence[PhotoSize], Video, None] = context.chat_data[ADVERTISEMENT_MEDIA]
    text = context.chat_data[ADVERTISEMENT_TEXT]

    if context.chat_data[ADVERTISEMENT_BUTTON] is None:
        button = None
    else:
        button = InlineKeyboardMarkup.from_button(
            InlineKeyboardButton(context.chat_data[ADVERTISEMENT_BUTTON], url=context.chat_data[ADVERTISEMENT_URL]))

    if isinstance(media, Animation):
        msg = await context.bot.send_animation(lang.GERMAN.channel_id, media, caption=text, reply_markup=button)
    elif isinstance(media, Sequence):
        msg = await context.bot.send_photo(lang.GERMAN.channel_id, media[-1], caption=text, reply_markup=button)
    elif isinstance(media, Video):
        msg = await context.bot.send_video(lang.GERMAN.channel_id, media, caption=text, reply_markup=button)
    else:
        msg = await context.bot.send_text(lang.GERMAN.channel_id, text, reply_markup=button)

    await msg.pin()

    await update.message.reply_text("Post sollte nun im deutschen Kanal gesendet worden sein.")

    return ConversationHandler.END

    # await advertise_in_other_channels(text, button, media, update, context)


async def advertise_in_other_channels(text: str, button: InlineKeyboardMarkup | None,
                                      media: Union[Animation, Sequence[PhotoSize], Video, None], update: Update,
                                      context: CallbackContext):
    for language in lang.LANGUAGES:
        translated_text = await translate(language.lang_key, text, language.lang_key_deepl)

        if button is None:
            translated_button = None
        else:
            translated_button = InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(await translate(language.lang_key, context.chat_data[ADVERTISEMENT_BUTTON],
                                                     language.lang_key_deepl),
                                     url=context.chat_data[ADVERTISEMENT_URL]))

        if isinstance(media, Animation):
            msg = await context.bot.send_animation(language.channel_id, media, caption=translated_text,
                                                   reply_markup=translated_button)
        elif isinstance(media, Sequence):
            msg = await context.bot.send_photo(language.channel_id, media[-1], caption=translated_text,
                                               reply_markup=translated_button)
        elif isinstance(media, Video):
            msg = await context.bot.send_video(language.channel_id, media, caption=translated_text,
                                               reply_markup=translated_button)
        else:
            msg = await context.bot.send_text(language.channel_id, translated_text, reply_markup=translated_button)

        await msg.pin()

        await update.message.reply_text(f"Post sollte nun im Kanal {language.lang_key} gesendet worden sein.")


def register_advertisement(app: Application):
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("add_advertisement", add_advertisement, filters=filters.Chat(ADMINS))],
        states={
            NEEDS_MEDIA: [
                CommandHandler("skip", skip_media),
                MessageHandler(filters.PHOTO | filters.VIDEO | filters.ANIMATION, add_advertisement_media),
            ],
            NEEDS_TEXT: [MessageHandler(filters.TEXT & ~filters.Regex(r"/cancel"), add_advertisement_text)],
            NEEDS_BUTTON: [CommandHandler("skip", skip_button),
                           MessageHandler(filters.TEXT & ~filters.Regex(r"/cancel"), add_advertisement_button),
                           ],
            NEEDS_URL: [MessageHandler(filters.TEXT & ~filters.Regex(r"/cancel"), add_advertisement_url)],
            SAVE_ADVERTISEMENT: [CommandHandler("save", save_advertisement)]

        },
        fallbacks=[CommandHandler("cancel", cancel)],
    ))
