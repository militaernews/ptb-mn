import logging
from typing import List, Dict, Any, Optional
from telegram import Update, Message, InputMediaPhoto, InputMediaVideo
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

logger = logging.getLogger(__name__)

# States for the conversation
COLLECTING_MEDIA = 1

async def start_ai_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the AI post creation assistant."""
    if update.effective_user.id not in ADMINS:
        return ConversationHandler.END

    await update.message.reply_text(
        "🤖 <b>KI-Post-Assistent gestartet</b>\n\n"
        "Bitte sende mir Bilder oder Videos (oder leite sie weiter). "
        "Ich werde die Bildunterschriften zusammenfassen und dir am Ende "
        "alle Medien als Album mit dem optimierten Text zurücksenden.\n\n"
        "Wenn du fertig bist, sende /done. Mit /cancel kannst du abbrechen.",
        parse_mode="HTML"
    )
    context.user_data["media_captions"] = []
    context.user_data["media_list"] = []
    return COLLECTING_MEDIA

async def collect_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Collect media and captions sent by the admin."""
    if "media_captions" not in context.user_data:
        context.user_data["media_captions"] = []
    if "media_list" not in context.user_data:
        context.user_data["media_list"] = []

    message = update.message
    caption = message.caption or ""
    
    if message.photo:
        # Store the largest photo's file_id
        context.user_data["media_list"].append({"type": "photo", "file_id": message.photo[-1].file_id})
    elif message.video:
        # Store the video's file_id
        context.user_data["media_list"].append({"type": "video", "file_id": message.video.file_id})
    elif message.text:
        # If it's just text, treat it as a caption/information
        caption = message.text

    if caption:
        context.user_data["media_captions"].append(caption)

    count = len(context.user_data["media_list"])
    text_count = len(context.user_data["media_captions"])
    await update.message.reply_text(f"✅ Empfangen: {count} Medien, {text_count} Textabschnitte. Sende weitere oder /done.")

    return COLLECTING_MEDIA

async def process_ai_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the collected text with LLM and return a mediagroup with the summary."""
    if not context.user_data.get("media_captions") and not context.user_data.get("media_list"):
        await update.message.reply_text("❌ Du hast keine Inhalte gesendet. Abbruch.")
        return ConversationHandler.END

    await update.message.reply_text("⏳ Erstelle Nachrichtenartikel... Bitte warten.")
    await update.message.chat.send_chat_action(ChatAction.TYPING)

    captions = context.user_data["media_captions"]
    media_list = context.user_data["media_list"]

    # Build prompt for LLM
    system_prompt = (
        "Du bist ein erfahrener Nachrichtenredakteur für einen Militär-Informationskanal. "
        "Deine Aufgabe ist es, aus den bereitgestellten Texten einen professionellen, sachlichen "
        "und informativen Nachrichtenartikel zu verfassen.\n\n"
        "REGELN:\n"
        "1. Der Artikel MUSS mit passenden Flaggen-Emojis beginnen (z. B. 🇷🇺 🇺🇦).\n"
        "2. Der Artikel muss auf Deutsch sein.\n"
        "3. Der gesamte Text darf MAXIMAL 900 Zeichen lang sein.\n"
        "4. Fasse die wichtigsten Fakten prägnant zusammen.\n"
        "5. Vermeide Spekulationen, bleib bei den Fakten."
    )

    prompt_content = f"{system_prompt}\n\nHier sind die zu verarbeitenden Informationen:\n\n" + "\n---\n".join(captions)
    
    message_content = [{"role": "user", "content": prompt_content}]

    try:
        # Updated models for OpenRouter (avoiding 404s and 429s)
        models = [
            "google/gemini-2.0-flash-lite-preview-02-05:free",
            "meta-llama/llama-3.3-70b-instruct",
            "google/gemini-2.0-flash-001",
            "mistralai/mistral-7b-instruct-v0.1"
        ]
        result = None
        error_details = []
        
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
                            "messages": message_content,
                            "temperature": 0.5,
                            "max_tokens": 1000,
                        }
                    )
                    if response.status_code == 200:
                        data = response.json()
                        result = data['choices'][0]['message']['content']
                        break
                    else:
                        error_msg = f"Model {model}: Status {response.status_code}"
                        try:
                            error_json = response.json()
                            if 'error' in error_json:
                                error_msg += f" - {error_json['error'].get('message', 'Unknown error')}"
                        except:
                            pass
                        error_details.append(error_msg)
            except Exception as e:
                err_str = f"Model {model}: {str(e)}"
                logger.warning(f"AI Post Assistant: {err_str}")
                error_details.append(err_str)
                continue

        if result:
            # Ensure character limit
            if len(result) > 950:
                result = result[:900] + "..."
            
            final_text = f"📝 <b>Vorschlag für Nachrichtenartikel:</b>\n\n{result}"
            
            if media_list:
                # Create mediagroup
                media_group = []
                for i, m in enumerate(media_list[:10]): # Max 10 per mediagroup
                    if m["type"] == "photo":
                        media_group.append(InputMediaPhoto(m["file_id"], caption=result if i == 0 else "", parse_mode="HTML"))
                    elif m["type"] == "video":
                        media_group.append(InputMediaVideo(m["file_id"], caption=result if i == 0 else "", parse_mode="HTML"))
                
                await update.message.reply_media_group(media_group)
            else:
                await update.message.reply_text(final_text, parse_mode="HTML")
        else:
            detailed_error = "\n".join([f"• {err}" for err in error_details])
            await update.message.reply_text(
                f"❌ <b>Fehler bei der KI-Verarbeitung</b>\n\n"
                f"Alle versuchten Modelle sind fehlgeschlagen:\n{detailed_error}\n\n"
                f"Bitte versuche es später erneut.",
                parse_mode="HTML"
            )

    except Exception as e:
        logger.error(f"AI Post Assistant failed: {e}")
        await update.message.reply_text(f"❌ <b>Ein kritischer Fehler ist aufgetreten:</b>\n<code>{str(e)}</code>", parse_mode="HTML")

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
                MessageHandler(filters.TEXT & ~filters.COMMAND, collect_media),
                MessageHandler(filters.PHOTO | filters.VIDEO, collect_media),
                CommandHandler("done", process_ai_post),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_ai_post)],
    )
    application.add_handler(conv_handler)
