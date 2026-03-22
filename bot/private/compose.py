import logging
from telegram import Update, InputMediaPhoto, InputMediaVideo
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)
from settings.config import ADMINS

logger = logging.getLogger(__name__)

# States for the conversation
COLLECTING_MEDIA = 1
COLLECTING_CAPTION = 2

async def start_compose(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the media group composition."""
    if update.effective_user.id not in ADMINS:
        return ConversationHandler.END

    await update.message.reply_text(
        "📝 <b>MediaGroup-Composer gestartet</b>\n\n"
        "Bitte sende mir bis zu 10 Bilder oder Videos.\n"
        "Wenn du fertig bist, sende /done oder sende das 10. Medium.\n\n"
        "Mit /cancel kannst du jederzeit abbrechen.",
        parse_mode="HTML"
    )
    context.user_data["compose_media"] = []
    return COLLECTING_MEDIA

async def collect_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Collect media sent by the admin."""
    if "compose_media" not in context.user_data:
        context.user_data["compose_media"] = []

    message = update.message
    
    if message.photo:
        context.user_data["compose_media"].append({"type": "photo", "file_id": message.photo[-1].file_id})
    elif message.video:
        context.user_data["compose_media"].append({"type": "video", "file_id": message.video.file_id})
    else:
        await update.message.reply_text("❌ Bitte sende nur Fotos oder Videos.")
        return COLLECTING_MEDIA

    count = len(context.user_data["compose_media"])
    
    if count >= 10:
        await update.message.reply_text(f"✅ 10 Medien erreicht. Bitte sende nun die <b>Bildunterschrift</b> (Caption) für die MediaGroup.", parse_mode="HTML")
        return COLLECTING_CAPTION

    await update.message.reply_text(f"✅ Medium {count}/10 empfangen. Sende weitere oder /done.")
    return COLLECTING_MEDIA

async def request_caption(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Request the caption after media collection is done."""
    if not context.user_data.get("compose_media"):
        await update.message.reply_text("❌ Du hast keine Medien gesendet. Abbruch.")
        return ConversationHandler.END

    await update.message.reply_text("📝 Bitte sende nun die <b>Bildunterschrift</b> (Caption) für die MediaGroup.", parse_mode="HTML")
    return COLLECTING_CAPTION

async def finalize_compose(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Apply the caption and send the mediagroup back."""
    caption = update.message.text
    media_list = context.user_data.get("compose_media", [])

    if not media_list:
        await update.message.reply_text("❌ Ein Fehler ist aufgetreten (keine Medien gefunden).")
        return ConversationHandler.END

    media_group = []
    for i, m in enumerate(media_list):
        # Apply caption only to the first element
        current_caption = caption if i == 0 else ""
        
        if m["type"] == "photo":
            media_group.append(InputMediaPhoto(m["file_id"], caption=current_caption, parse_mode="HTML"))
        elif m["type"] == "video":
            media_group.append(InputMediaVideo(m["file_id"], caption=current_caption, parse_mode="HTML"))

    try:
        await update.message.reply_media_group(media=media_group)
    except Exception as e:
        logger.error(f"Error sending media group in compose: {e}")
        await update.message.reply_text(f"❌ Fehler beim Senden der MediaGroup: {e}")

    # Cleanup
    context.user_data.pop("compose_media", None)
    return ConversationHandler.END

async def cancel_compose(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    await update.message.reply_text("🚫 Composition abgebrochen.")
    context.user_data.pop("compose_media", None)
    return ConversationHandler.END

def register_compose(application):
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("compose", start_compose, filters.ChatType.PRIVATE)],
        states={
            COLLECTING_MEDIA: [
                MessageHandler(filters.PHOTO | filters.VIDEO, collect_media),
                CommandHandler("done", request_caption),
            ],
            COLLECTING_CAPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, finalize_compose),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_compose)],
    )
    application.add_handler(conv_handler)
