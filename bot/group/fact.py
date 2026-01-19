import logging

from httpx import AsyncClient
from settings.config import OPENROUTER_API_KEY
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import CallbackContext


async def fact_check_with_llm(claim: str) -> str:
    """
    Perform fact-checking using LLM with web search capabilities
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

VORGEHEN:
1. Analysiere die Behauptung
2. Suche nach aktuellen, verlässlichen Quellen
3. Bewerte die Faktenlage
4. Gib eine klare Einschätzung: WAHR, TEILWEISE WAHR, FALSCH, oder NICHT VERIFIZIERBAR
5. Verlinke deine Quellen mit vollständigen URLs

FORMAT:
- Sei SEHR prägnant und direkt (maximal 3-4 Sätze)
- Keine langen Erklärungen
- Verlinke Quellen direkt im Text oder als Liste am Ende
- Nutze klare Emojis: ✅ WAHR, ⚠️ TEILWEISE WAHR, ❌ FALSCH, ❓ NICHT VERIFIZIERBAR

Antworte auf Deutsch und sei präzise."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Überprüfe folgende Behauptung und nutze aktuelle Online-Quellen:\n\n{claim}"}
    ]

    try:
        async with AsyncClient(timeout=90.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "HTTP-Referer": "https://telegram.org",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "allenai/olmo-3.1-32b-think:free",
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 1200,
                }
            )
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content']
    except Exception as e:
        logging.error(f"Fact check failed: {e}", exc_info=True)
        return f"❌ Fehler beim Faktencheck: {str(e)}"


async def fact(update: Update, context: CallbackContext):
    """
    Fact-check a claim using LLM with web search
    Usage: /fact <claim> or reply to a message with /fact
    """
    await update.message.chat.send_chat_action(ChatAction.TYPING)

    await update.message.delete()

    # Check if replying to a message
    if update.message.reply_to_message and update.message.reply_to_message.text:
        claim = update.message.reply_to_message.text

    # Check if claim provided as command argument
    else:
        return

    if not claim or len(claim.strip()) < 10:
        await update.message.reply_text("❌ Die Behauptung ist zu kurz. Bitte gib mehr Details an.")
        return

    logging.info(f"Fact-checking claim: {claim[:100]}...")

    try:
        # Perform fact check
        result = await fact_check_with_llm(claim)

        # Format response
        response = f"🔍 <b>FAKTENCHECK</b>\n\n"
        response += f"<b>Behauptung:</b>\n<i>{claim[:200]}{'...' if len(claim) > 200 else ''}</i>\n\n"
        response += f"{result}"

        logging.info(f"Fact check completed: {len(result)} chars")

        await update.message.reply_text(response,  disable_web_page_preview=False)
    except Exception as e:
        logging.error(f"Error in fact command: {e}", exc_info=True)
        await update.message.reply_text("❌ Fehler beim Faktencheck. Bitte versuch's nochmal.")


