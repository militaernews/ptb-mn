import logging
import base64
from io import BytesIO

from httpx import AsyncClient
from settings.config import OPENROUTER_API_KEY
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import CallbackContext


async def encode_image_to_base64(photo_file) -> str:
    """
    Convert telegram photo to base64 string
    """
    try:
        # Download the photo
        photo_bytes = await photo_file.download_as_bytearray()
        # Convert to base64
        base64_image = base64.b64encode(photo_bytes).decode('utf-8')
        return base64_image
    except Exception as e:
        logging.error(f"Error encoding image: {e}")
        raise


def format_fact_check_result(result: str) -> str:
    """
    Format the LLM result with proper HTML formatting for Telegram
    """
    import re

    # Bold verdict keywords
    result = re.sub(r'\b(WAHR|TEILWEISE WAHR|FALSCH|MANIPULIERT|NICHT VERIFIZIERBAR)\b',
                    r'<b>\1</b>', result)

    # Format sources section if present
    if 'Quellen:' in result or 'Sources:' in result:
        result = result.replace('Quellen:', '\n<b>📚 Quellen:</b>')
        result = result.replace('Sources:', '\n<b>📚 Sources:</b>')

    return result


async def fact_check_with_llm(claim: str = None, image_base64: str = None, caption: str = None) -> str:
    """
    Perform fact-checking using LLM with web search capabilities
    Supports text claims, images, or images with captions
    """
    system_prompt = """Du bist ein Faktenprüfer mit einer klaren pro-europäischen, demokratischen Perspektive.

DEINE HALTUNG:
- Pro-Europäisch und pro-demokratisch
- Kritisch gegenüber autoritären Regimen (Russland, China, Iran)
- Unterstützung der Ukraine im Verteidigungskrieg
- Kritisch gegenüber Putin, Xi Jinping und islamistischen Regimen
- Bevorzuge westliche und ukrainische Quellen

BEVORZUGTE QUELLEN (in dieser Reihenfolge):
1. Europäische Medien: BBC, Der Spiegel, Die Zeit, The Guardian, Le Monde
2. Ukrainische Quellen: Kyiv Independent, Ukrainska Pravda
3. Seriöse internationale Medien: Reuters, AP, AFP
4. Investigative Journalismus: Bellingcat, OSINT-Analysten
5. Think Tanks: ISW (Institute for the Study of War), Atlantic Council

VERMEIDE:
- Russische Staatsmedien (RT, Sputnik)
- Chinesische Staatsmedien (CGTN, Xinhua)
- Iranische Staatsmedien (Press TV)
- Verschwörungstheoretische Quellen

BEI BILDANALYSE:
- Analysiere den visuellen Inhalt sorgfältig
- Prüfe auf Anzeichen von Manipulation, Deepfakes oder Photoshop
- Suche nach der Originalquelle des Bildes (Reverse Image Search Kontext)
- Überprüfe Datum, Ort und Kontext
- Achte auf irreführende Bildunterschriften
- Erkenne aus dem Kontext gerissene Bilder

VORGEHEN:
1. Analysiere die Behauptung/das Bild/die Bildunterschrift
2. Suche nach aktuellen, verlässlichen Quellen
3. Bewerte die Faktenlage
4. Gib eine klare Einschätzung: WAHR, TEILWEISE WAHR, FALSCH, MANIPULIERT, oder NICHT VERIFIZIERBAR
5. Verlinke deine Quellen mit vollständigen URLs

FORMAT:
- Beginne direkt mit dem Urteil (✅ WAHR, ⚠️ TEILWEISE WAHR, ❌ FALSCH, 🖼️ MANIPULIERT, ❓ NICHT VERIFIZIERBAR)
- Keine Überschriften wie "FAKTENCHECK" - komm direkt zur Sache
- Sei SEHR prägnant und direkt (maximal 3-4 Sätze)
- Erkläre kurz WARUM die Behauptung wahr/falsch ist
- Untersuche mögliche Hintergründe: Was könnte der wahre Grund oder Kontext sein?
- Gib am Ende eine "Quellen:" Sektion an
- Liste Quellen als reine URLs auf, jede URL in einer neuen Zeile mit Leerzeile dazwischen
- **NUR funktionierende URLs angeben** - keine toten Links
- Beispiel für Quellen:

Quellen:
https://www.example.com/article1

https://www.example.com/article2

Antworte auf Deutsch und sei präzise."""

    # Build the user message based on what's provided
    message_content = []

    if image_base64:
        # Add image to message
        message_content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{image_base64}"
            }
        })

        # Add text prompt
        if caption:
            text_prompt = f"Analysiere dieses Bild und überprüfe die folgende Bildunterschrift:\n\n{caption}\n\nPrüfe: Ist das Bild authentisch? Passt die Bildunterschrift zum Inhalt? Gibt es Anzeichen von Manipulation?"
        else:
            text_prompt = "Analysiere dieses Bild. Prüfe: Ist es authentisch? Gibt es Anzeichen von Manipulation? Was zeigt es wirklich? Suche nach dem Originalkontext."

        message_content.append({
            "type": "text",
            "text": text_prompt
        })
    elif claim:
        # Text-only fact check
        message_content.append({
            "type": "text",
            "text": f"Überprüfe folgende Behauptung und nutze aktuelle Online-Quellen:\n\n{claim}"
        })
    else:
        return "❌ Keine Behauptung oder Bild zum Überprüfen angegeben."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message_content}
    ]

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
                    # Using :online suffix enables real-time web search via Exa.ai
                    # This costs $4 per 1000 results (default 5 results = $0.02 per request)
                    "model": "allenai/molmo-2-8b:free:online",
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 1500,
                }
            )
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content']
    except Exception as e:
        logging.error(f"Fact check failed: {e}", exc_info=True)
        raise


async def fact(update: Update, context: CallbackContext):
    """
    Fact-check a claim, image, or image with caption using LLM with web search
    Usage:
    - /fact <claim> - check text claim
    - Reply to a text message with /fact - check that message
    - Reply to an image with /fact - check the image
    - Reply to an image with caption with /fact - check both
    - Reply to a message with /fact <additional context> - check with extra context
    """
    await update.message.chat.send_chat_action(ChatAction.TYPING)

    claim = None
    image_base64 = None
    caption = None
    additional_context = None

    # Check if replying to a message
    if update.message.reply_to_message:
        replied_msg = update.message.reply_to_message

        # Get additional context if provided
        if context.args:
            additional_context = " ".join(context.args)

        # Check for image
        if replied_msg.photo:
            # Get the highest resolution photo
            photo = replied_msg.photo[-1]
            photo_file = await photo.get_file()

            try:
                image_base64 = await encode_image_to_base64(photo_file)
                logging.info(f"Image encoded successfully: {len(image_base64)} chars")
            except Exception as e:
                await update.message.reply_text("❌ Fehler beim Laden des Bildes.")
                return

            # Get caption if exists
            if replied_msg.caption:
                caption = replied_msg.caption

        # Check for text
        elif replied_msg.text:
            claim = replied_msg.text

        # Delete the /fact command message for cleaner chat
        await update.message.delete()

    # Check if claim provided as command argument (only for text claims)
    elif context.args:
        claim = " ".join(context.args)

    # No content to check
    else:
        await update.message.reply_text(
            "❓ <b>Faktencheck - Nutzung:</b>\n\n"
            "📝 <b>Text prüfen:</b>\n"
            "• Antworte auf eine Nachricht mit /fact\n"
            "• Oder: /fact <Behauptung>\n\n"
            "🖼️ <b>Bild prüfen:</b>\n"
            "• Antworte auf ein Bild mit /fact\n"
            "• Funktioniert auch mit Bildunterschriften\n\n"
            "💬 <b>Mit zusätzlichem Kontext:</b>\n"
            "• Antworte auf eine Nachricht mit /fact <zusätzlicher Kontext>\n\n"
            "<i>Beispiel: /fact Die Erde ist eine Scheibe</i>",
            parse_mode='HTML'
        )
        return

    # Validate input
    if not image_base64 and (not claim or len(claim.strip()) < 10):
        await update.message.reply_text("❌ Die Behauptung ist zu kurz. Bitte gib mehr Details an.")
        return

    # Combine claim with additional context if provided
    if additional_context and claim:
        claim = f"{claim}\n\nZusätzlicher Kontext: {additional_context}"
    elif additional_context and caption:
        caption = f"{caption}\n\nZusätzlicher Kontext: {additional_context}"

    # Log what we're checking
    if image_base64:
        log_msg = f"Image with caption: {caption[:50] if caption else 'no caption'}"
        if additional_context:
            log_msg += f" + context: {additional_context[:30]}"
    else:
        log_msg = f"Text claim: {claim[:100]}"
    logging.info(f"Fact-checking {log_msg}...")

    try:
        # Perform fact check
        result = await fact_check_with_llm(claim=claim, image_base64=image_base64, caption=caption)

        # Format response with proper HTML
        response = ""

        if image_base64:
            response += "🖼️ <b>Bildanalyse</b>\n"
            if caption:
                response += f"<b>Bildunterschrift:</b> <i>{caption[:150]}{'...' if len(caption) > 150 else ''}</i>\n\n"
            else:
                response += "\n"
        else:
            response += f"<b>Behauptung:</b> <i>{claim[:150]}{'...' if len(claim) > 150 else ''}</i>\n\n"

        # Format the LLM result with proper HTML
        formatted_result = format_fact_check_result(result)
        response += formatted_result

        logging.info(f"Fact check completed: {len(result)} chars")

        # Reply to the original message being fact-checked
        if update.message.reply_to_message:
            await update.message.reply_to_message.reply_text(response, parse_mode='HTML',
                                                             disable_web_page_preview=False)
        else:
            await update.message.reply_text(response, parse_mode='HTML', disable_web_page_preview=False)

    except Exception as e:
        logging.error(f"Error in fact command: {e}", exc_info=True)