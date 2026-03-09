import logging
import base64
from typing import List, Dict, Any, Optional
from telegram import Update, Message
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)
from telegram.constants import ChatAction
from httpx import AsyncClient
from settings.config import ADMINS, OPENROUTER_API_KEY
from datetime import datetime

logger = logging.getLogger(__name__)

# States for the conversation
COLLECTING_MEDIA = 1

async def start_ai_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the AI post creation assistant."""
    if update.effective_user.id not in ADMINS:
        return ConversationHandler.END

    await update.message.reply_text(
        "🤖 <b>KI-Post-Assistent gestartet</b>\n\n"
        "Bitte sende mir bis zu 10 Bilder oder Videos (oder leite sie weiter), "
        "aus denen ich einen zusammenfassenden Nachrichtenartikel erstellen soll.\n\n"
        "Wenn du fertig bist, sende /done. Mit /cancel kannst du abbrechen.",
        parse_mode="HTML"
    )
    context.user_data["media_files"] = []
    context.user_data["media_captions"] = []
    return COLLECTING_MEDIA

async def collect_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Collect media sent by the admin."""
    if "media_files" not in context.user_data:
        context.user_data["media_files"] = []
        context.user_data["media_captions"] = []

    if len(context.user_data["media_files"]) >= 10:
        await update.message.reply_text("⚠️ Du hast bereits 10 Medien hochgeladen. Sende /done zum Erstellen des Posts.")
        return COLLECTING_MEDIA

    message = update.message
    caption = message.caption or ""
    
    if message.photo:
        photo_file = await message.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        base64_image = base64.b64encode(photo_bytes).decode('utf-8')
        context.user_data["media_files"].append({"type": "image", "data": base64_image})
    elif message.video:
        # We can't easily process video content with LLM unless we take frames, 
        # for now we'll just use the caption if available or a placeholder.
        context.user_data["media_files"].append({"type": "video", "info": "Video file provided"})
    
    if caption:
        context.user_data["media_captions"].append(caption)

    count = len(context.user_data["media_files"])
    await update.message.reply_text(f"✅ Medium {count}/10 empfangen. Sende weitere oder /done.")
    return COLLECTING_MEDIA

async def process_ai_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the collected media with LLM and return a summary."""
    if not context.user_data.get("media_files"):
        await update.message.reply_text("❌ Du hast keine Medien gesendet. Abbruch.")
        return ConversationHandler.END

    await update.message.reply_text("⏳ Erstelle Nachrichtenartikel... Bitte warten.")
    await update.message.chat.send_chat_action(ChatAction.TYPING)

    media_files = context.user_data["media_files"]
    captions = context.user_data["media_captions"]

    # Build prompt for LLM
    system_prompt = (
        "Du bist ein erfahrener Nachrichtenredakteur für einen Militär-Informationskanal. "
        "Deine Aufgabe ist es, aus den bereitgestellten Bildern und Bildunterschriften "
        "einen professionellen, sachlichen und informativen Nachrichtenartikel zu verfassen. "
        "Der Artikel sollte auf Deutsch sein, eine klare Struktur haben und die wichtigsten Fakten zusammenfassen. "
        "Vermeide Spekulationen, bleib bei den Fakten."
    )

    message_content = [{"type": "text", "text": f"{system_prompt}\n\nHier sind die Informationen aus den Medien:\n" + "\n".join(captions)}]
    
    # Add images to content (up to limit)
    for m in media_files:
        if m["type"] == "image":
            message_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{m['data']}"}
            })

    try:
        # Fallback models like in fact.py
        models = ["meta-llama/llama-3.1-8b-instruct:free", "google/gemini-flash-1.5-8b", "mistralai/mistral-7b-instruct:free"]
        result = None
        
        for model in models:
            try:
                async with AsyncClient(timeout=120.0) as client:
                    response = await client.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                            "HTTP-Referer": "https://telegram.org",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": model,
                            "messages": [{"role": "user", "content": message_content}],
                            "temperature": 0.5,
                        }
                    )
                    if response.status_code == 200:
                        data = response.json()
                        result = data['choices'][0]['message']['content']
                        break
            except Exception as e:
                logger.warning(f"AI Post Assistant: Model {model} failed: {e}")
                continue

        if result:
            await update.message.reply_text(f"📝 <b>Vorschlag für Nachrichtenartikel:</b>\n\n{result}", parse_mode="HTML")
        else:
            await update.message.reply_text("❌ Fehler bei der KI-Verarbeitung. Bitte versuche es später erneut.")

    except Exception as e:
        logger.error(f"AI Post Assistant failed: {e}")
        await update.message.reply_text("❌ Ein kritischer Fehler ist aufgetreten.")

    # Cleanup
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_ai_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    await update.message.reply_text("🚫 KI-Post-Assistent abgebrochen.")
    context.user_data.clear()
    return ConversationHandler.END

def register_ai_assistant(application):
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("ai_post", start_ai_post)],
        states={
            COLLECTING_MEDIA: [
                MessageHandler(filters.PHOTO | filters.VIDEO, collect_media),
                CommandHandler("done", process_ai_post),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_ai_post)],
    )
    application.add_handler(conv_handler)
