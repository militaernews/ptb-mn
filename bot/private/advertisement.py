import html
import logging
import re
from typing import Sequence, Union, Final, Optional

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, PhotoSize, Animation, Video, Message, Bot
from telegram.constants import MessageLimit
from telegram.ext import CommandHandler, ConversationHandler, filters, MessageHandler, CallbackContext, ContextTypes, \
    Application, CallbackQueryHandler

from data.lang import GERMAN, LANGUAGES
from settings.config import ADMINS
from util.translation import translate

ADVERTISEMENT_MEDIA: Final[str] = "new_ADVERTISEMENT_MEDIA"
ADVERTISEMENT_TEXT: Final[str] = "new_ADVERTISEMENT_TEXT"
ADVERTISEMENT_BUTTON: Final[str] = "new_ADVERTISEMENT_BUTTON"
ADVERTISEMENT_URL: Final[str] = "new_ADVERTISEMENT_URL"

SAVE_GERMAN_ONLY: Final[str] = "ad_save_de"
SAVE_ALL_CHANNELS: Final[str] = "ad_save_all"

NEEDS_MEDIA, NEEDS_TEXT, NEEDS_BUTTON, NEEDS_URL, SAVE_ADVERTISEMENT = range(5)

AdMedia = Union[Animation, Sequence[PhotoSize], Video, None]

_HTML_TAG = re.compile(r"<[^>]+>")


def visible_length(html_text: str) -> int:
    """Length as Telegram counts it for caption/text limits: after parsing the HTML, in UTF-16 code units."""
    plain = html.unescape(_HTML_TAG.sub("", html_text))
    return len(plain.encode("utf-16-le")) // 2


def text_limit(media: AdMedia) -> int:
    return MessageLimit.MAX_TEXT_LENGTH if media is None else MessageLimit.CAPTION_LENGTH


def ad_button(text: Optional[str], url: Optional[str]) -> Optional[InlineKeyboardMarkup]:
    if text is None:
        return None
    return InlineKeyboardMarkup.from_button(InlineKeyboardButton(text, url=url))


async def send_ad(bot: Bot, chat_id: int, media: AdMedia, text: str,
                  button: Optional[InlineKeyboardMarkup]) -> Message:
    if isinstance(media, Animation):
        return await bot.send_animation(chat_id, media, caption=text, reply_markup=button)
    if isinstance(media, Video):
        return await bot.send_video(chat_id, media, caption=text, reply_markup=button)
    if isinstance(media, Sequence):
        return await bot.send_photo(chat_id, media[-1], caption=text, reply_markup=button)
    return await bot.send_message(chat_id, text, reply_markup=button)


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
    return NEEDS_MEDIA


async def add_advertisement_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.chat_data[ADVERTISEMENT_MEDIA] = update.message.effective_attachment

    await update.message.reply_text(
        "Sende mir nun den Text der in der Werbung vorkommen soll."
        f"\n\nMit Bild/Video darf er höchstens {MessageLimit.CAPTION_LENGTH} Zeichen lang sein.")

    return NEEDS_TEXT


async def skip_media(update: Update, _: CallbackContext) -> int:
    await update.message.reply_text(
        "Media hinzufügen übersprungen!\n\nSende mir nun den Text der in der Werbung vorkommen soll.")

    return NEEDS_TEXT


async def add_advertisement_text(update: Update, context: CallbackContext) -> int:
    text = update.message.text_html_urled
    limit = text_limit(context.chat_data[ADVERTISEMENT_MEDIA])
    length = visible_length(text)

    if length > limit:
        await update.message.reply_text(
            f"Der Text ist {length} Zeichen lang, erlaubt sind höchstens {limit}."
            "\n\nBitte kürze ihn und sende ihn erneut, oder brich mit /cancel ab.")
        return NEEDS_TEXT

    context.chat_data[ADVERTISEMENT_TEXT] = text

    await update.message.reply_text(
        "Sende mir nun den Text der auf dem Button unterhalb der Nachricht angezeigt werden soll.\n\nWenn die Werbung keinen Button haben soll, dann drücke /skip.")

    return NEEDS_BUTTON


async def send_preview(update: Update, context: CallbackContext):
    button = ad_button(context.chat_data[ADVERTISEMENT_BUTTON], context.chat_data[ADVERTISEMENT_URL])

    try:
        await send_ad(context.bot, update.effective_chat.id, context.chat_data[ADVERTISEMENT_MEDIA],
                      context.chat_data[ADVERTISEMENT_TEXT], button)
    except Exception as e:
        await update.message.reply_text("Fehler beim Senden der Vorschau! Beginne von vorn mit /cancel."
                                        f"\n\n<code>{html.escape(str(e))}</code>")
        return

    await update.message.reply_text(
        "Passt das soweit? Wo soll die Werbung gepostet werden?\n\nVerwerfen und von vorn beginnen mit /cancel.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"Nur @{GERMAN.username}", callback_data=SAVE_GERMAN_ONLY)],
            [InlineKeyboardButton("Alle Kanäle (übersetzt)", callback_data=SAVE_ALL_CHANNELS)],
        ]))


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
    await send_preview(update, context)

    return SAVE_ADVERTISEMENT


async def save_command(update: Update, context: CallbackContext) -> int:
    await publish_advertisement(update, context, all_channels=False)
    return ConversationHandler.END


async def save_button(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_reply_markup(None)

    await publish_advertisement(update, context, all_channels=query.data == SAVE_ALL_CHANNELS)
    return ConversationHandler.END


async def publish_advertisement(update: Update, context: CallbackContext, all_channels: bool):
    chat_id = update.effective_chat.id
    media: AdMedia = context.chat_data[ADVERTISEMENT_MEDIA]
    text = context.chat_data[ADVERTISEMENT_TEXT]
    button_text = context.chat_data[ADVERTISEMENT_BUTTON]
    url = context.chat_data[ADVERTISEMENT_URL]

    try:
        msg = await send_ad(context.bot, GERMAN.channel_id, media, text, ad_button(button_text, url))
        await msg.pin()
    except Exception as e:
        logging.exception("Posting advertisement to German channel failed")
        await context.bot.send_message(chat_id, f"❌ Fehler beim Posten in @{GERMAN.username}:"
                                                f"\n<code>{html.escape(str(e))}</code>")
        return

    await context.bot.send_message(chat_id, f"✅ Werbung in @{GERMAN.username} gepostet und angepinnt.")

    if all_channels:
        await advertise_in_other_channels(context, chat_id, media, text, button_text, url)


async def advertise_in_other_channels(context: CallbackContext, report_chat_id: int, media: AdMedia, text: str,
                                      button_text: Optional[str], url: Optional[str]):
    await context.bot.send_message(report_chat_id, "Übersetze und poste in die anderen Kanäle…")
    results = []

    for language in LANGUAGES:
        try:
            translated_text = await translate(language.lang_key, text, language.lang_key_deepl)

            length = visible_length(translated_text)
            limit = text_limit(media)
            if length > limit:
                results.append(f"⚠️ @{language.username}: Übersetzung zu lang ({length}/{limit} Zeichen), nicht gepostet")
                continue

            translated_button = None
            if button_text is not None:
                try:
                    translated_button_text = await translate(language.lang_key, button_text, language.lang_key_deepl)
                except Exception:
                    translated_button_text = button_text
                translated_button = ad_button(translated_button_text, url)

            msg = await send_ad(context.bot, language.channel_id, media, translated_text, translated_button)
            await msg.pin()
            results.append(f"✅ @{language.username}")
        except Exception as e:
            logging.exception(f"Posting advertisement to {language.lang_key} failed")
            results.append(f"❌ @{language.username}: <code>{html.escape(str(e))}</code>")

    await context.bot.send_message(report_chat_id, "\n".join(results))


def register_advertisement(app: Application):
    text_input = filters.TEXT & ~filters.COMMAND

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("add_advertisement", add_advertisement, filters=filters.Chat(ADMINS))],
        states={
            NEEDS_MEDIA: [
                CommandHandler("skip", skip_media),
                MessageHandler(filters.PHOTO | filters.VIDEO | filters.ANIMATION, add_advertisement_media),
            ],
            NEEDS_TEXT: [MessageHandler(text_input, add_advertisement_text)],
            NEEDS_BUTTON: [CommandHandler("skip", skip_button),
                           MessageHandler(text_input, add_advertisement_button),
                           ],
            NEEDS_URL: [MessageHandler(text_input, add_advertisement_url)],
            SAVE_ADVERTISEMENT: [
                CommandHandler("save", save_command),
                CallbackQueryHandler(save_button, pattern=f"^({SAVE_GERMAN_ONLY}|{SAVE_ALL_CHANNELS})$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    ))
