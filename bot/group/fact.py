import base64
import logging
import re
from typing import List, Dict, Optional
from datetime import datetime

from httpx import AsyncClient
from settings.config import OPENROUTER_API_KEY
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import CallbackContext


# Configure logging format
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def encode_image_to_base64(photo_file) -> str:
    """
    Convert telegram photo to base64 string
    """
    try:
        photo_bytes = await photo_file.download_as_bytearray()
        base64_image = base64.b64encode(photo_bytes).decode('utf-8')
        logger.info(f"Image encoded: {len(base64_image)} chars ({len(photo_bytes)} bytes)")
        return base64_image
    except Exception as e:
        logger.error(f"Failed to encode image: {e}")
        raise


async def search_searx(query: str, max_results: int = 5) -> List[Dict]:
    """
    Search using SearXNG public instance - completely free, no API key needed
    """
    instances = [
        "https://searx.be",
        "https://search.sapti.me",
        "https://searx.work",
    ]
    
    for instance_url in instances:
        try:
            url = f"{instance_url}/search"
            params = {
                "q": query,
                "format": "json",
                "language": "de",
                "engines": "google,bing,duckduckgo"
            }
            
            async with AsyncClient(timeout=15.0) as client:
                response = await client.get(url, params=params)
                
                if response.status_code != 200:
                    continue
                    
                data = response.json()
                
                results = []
                for item in data.get("results", [])[:max_results]:
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "description": item.get("content", "")
                    })
                
                if results:
                    logger.info(f"✓ SearX ({instance_url}): {len(results)} results")
                    return results
                    
        except Exception as e:
            logger.debug(f"SearX {instance_url} failed: {str(e)[:50]}")
            continue
    
    return []


async def search_duckduckgo(query: str, max_results: int = 5) -> List[Dict]:
    """
    Search using DuckDuckGo Instant Answer API - completely free, no API key
    """
    try:
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1
        }
        
        async with AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            
            # Get abstract if available
            if data.get("Abstract"):
                results.append({
                    "title": data.get("Heading", "DuckDuckGo Answer"),
                    "url": data.get("AbstractURL", ""),
                    "description": data.get("Abstract", "")
                })
            
            # Get related topics
            for topic in data.get("RelatedTopics", [])[:max_results]:
                if isinstance(topic, dict) and "Text" in topic:
                    results.append({
                        "title": topic.get("Text", "")[:100],
                        "url": topic.get("FirstURL", ""),
                        "description": topic.get("Text", "")
                    })
                elif isinstance(topic, dict) and "Topics" in topic:
                    for subtopic in topic.get("Topics", [])[:2]:
                        if "Text" in subtopic:
                            results.append({
                                "title": subtopic.get("Text", "")[:100],
                                "url": subtopic.get("FirstURL", ""),
                                "description": subtopic.get("Text", "")
                            })
            
            # Remove duplicates and limit
            seen_urls = set()
            unique_results = []
            for r in results:
                if r["url"] and r["url"] not in seen_urls:
                    seen_urls.add(r["url"])
                    unique_results.append(r)
                    if len(unique_results) >= max_results:
                        break
            
            if unique_results:
                logger.info(f"✓ DuckDuckGo: {len(unique_results)} results")
            return unique_results
            
    except Exception as e:
        logger.debug(f"DuckDuckGo failed: {str(e)[:50]}")
        return []


async def search_jina(query: str, max_results: int = 5) -> List[Dict]:
    """
    Search using Jina AI Search - free, no credit card required
    """
    try:
        url = "https://s.jina.ai/"
        search_url = f"{url}{query}"
        
        headers = {
            "Accept": "application/json",
            "X-Return-Format": "json"
        }
        
        async with AsyncClient(timeout=15.0) as client:
            response = await client.get(search_url, headers=headers)
            
            if response.status_code != 200:
                return []
                
            data = response.json()
            
            results = []
            for item in data.get("data", [])[:max_results]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "description": item.get("description", "")
                })
            
            if results:
                logger.info(f"✓ Jina AI: {len(results)} results")
            return results
            
    except Exception as e:
        logger.debug(f"Jina AI failed: {str(e)[:50]}")
        return []


async def search_brave_free(query: str, max_results: int = 5) -> List[Dict]:
    """
    Brave Search using their free Web Search API
    """
    try:
        from settings.config import BRAVE_API_KEY
        
        if not BRAVE_API_KEY or BRAVE_API_KEY == "your-brave-api-key-here":
            return []
        
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": BRAVE_API_KEY
        }
        params = {
            "q": query,
            "count": max_results,
            "text_decorations": False,
            "search_lang": "de",
        }
        
        async with AsyncClient(timeout=15.0) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("web", {}).get("results", [])[:max_results]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "description": item.get("description", ""),
                })
            
            if results:
                logger.info(f"✓ Brave: {len(results)} results")
            return results
            
    except ImportError:
        return []
    except Exception as e:
        logger.debug(f"Brave failed: {str(e)[:50]}")
        return []


async def search_web(query: str, max_results: int = 5) -> List[Dict]:
    """
    Multi-engine search with automatic fallbacks
    """
    logger.info(f"Web search: '{query[:60]}{'...' if len(query) > 60 else ''}'")
    
    # Try Brave first if API key is available
    results = await search_brave_free(query, max_results)
    if results:
        return results
    
    # Try SearXNG
    results = await search_searx(query, max_results)
    if results:
        return results
    
    # Try DuckDuckGo
    results = await search_duckduckgo(query, max_results)
    if results:
        return results
    
    # Try Jina AI as last resort
    results = await search_jina(query, max_results)
    if results:
        return results
    
    logger.warning("⚠️ All search engines failed")
    return []


def format_search_results_for_context(results: List[Dict]) -> str:
    """
    Format search results into a readable context for the LLM
    """
    if not results:
        return "Keine Suchergebnisse gefunden."
    
    context = "AKTUELLE WEB-SUCHERGEBNISSE:\n\n"
    for i, result in enumerate(results, 1):
        context += f"[{i}] {result['title']}\n"
        context += f"URL: {result['url']}\n"
        if result.get('description'):
            context += f"{result['description']}\n"
        context += "\n"
    
    return context


def extract_urls_from_results(results: List[Dict]) -> List[str]:
    """
    Extract just the URLs from search results for source citation
    """
    return [r['url'] for r in results if r.get('url')]


def format_fact_check_result(result: str, sources: List[str] = None) -> str:
    """
    Format the LLM result with proper HTML formatting for Telegram
    """
    # Bold verdict keywords
    result = re.sub(r'\b(WAHR|TEILWEISE WAHR|FALSCH|MANIPULIERT|NICHT VERIFIZIERBAR)\b',
                    r'<b>\1</b>', result)

    # Format sources section if present
    if 'Quellen:' in result or 'Sources:' in result:
        result = result.replace('Quellen:', '\n<b>📚 Quellen:</b>')
        result = result.replace('Sources:', '\n<b>📚 Sources:</b>')
    elif sources:
        # Add sources if not already included
        result += "\n\n<b>📚 Quellen:</b>\n"
        for url in sources[:5]:
            result += f"{url}\n\n"

    return result


async def fact_check_with_llm(claim: str = None, image_base64: str = None, caption: str = None) -> tuple[str, List[str]]:
    """
    Perform fact-checking using LLM with web search capabilities
    Returns: (fact_check_result, list_of_source_urls)
    """
    start_time = datetime.now()
    
    # Step 1: Perform web search if we have a text claim or caption
    search_results = []
    search_query = None
    
    if claim:
        search_query = claim[:200]
    elif caption:
        search_query = caption[:200]
    
    if search_query:
        search_results = await search_web(search_query, max_results=5)
        
        if not search_results:
            logger.warning("No search results - using LLM knowledge only")
    
    # Format search results for LLM context
    search_context = format_search_results_for_context(search_results)
    source_urls = extract_urls_from_results(search_results)
    
    system_instructions = """Du bist ein Faktenprüfer mit einer klaren pro-europäischen, demokratischen Perspektive.

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
- Suche nach der Originalquelle des Bildes
- Überprüfe Datum, Ort und Kontext
- Achte auf irreführende Bildunterschriften
- Erkenne aus dem Kontext gerissene Bilder

VORGEHEN:
1. Analysiere die Behauptung/das Bild/die Bildunterschrift
2. Nutze die bereitgestellten Web-Suchergebnisse
3. Bewerte die Faktenlage
4. Gib eine klare Einschätzung: WAHR, TEILWEISE WAHR, FALSCH, MANIPULIERT, oder NICHT VERIFIZIERBAR
5. Beziehe dich auf die nummerierten Quellen [1], [2], etc.

FORMAT:
- Beginne direkt mit dem Urteil (✅ WAHR, ⚠️ TEILWEISE WAHR, ❌ FALSCH, 🖼️ MANIPULIERT, ❓ NICHT VERIFIZIERBAR)
- Keine Überschriften wie "FAKTENCHECK" - komm direkt zur Sache
- Sei SEHR prägnant und direkt (maximal 3-4 Sätze)
- Erkläre kurz WARUM die Behauptung wahr/falsch ist
- Untersuche mögliche Hintergründe: Was könnte der wahre Grund oder Kontext sein?
- Referenziere Quellen mit [1], [2], etc. wenn du dich auf sie beziehst
- Füge KEINE "Quellen:" Sektion hinzu - die werden automatisch hinzugefügt

Antworte auf Deutsch und sei präzise."""

    # Build the user message
    message_content = []

    if image_base64:
        logger.info(f"Processing image fact-check{' with caption' if caption else ''}")
        
        message_content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{image_base64}"
            }
        })

        if caption:
            text_prompt = f"{system_instructions}\n\n{search_context}\n\nAnalysiere dieses Bild und überprüfe die folgende Bildunterschrift:\n\n{caption}\n\nPrüfe: Ist das Bild authentisch? Passt die Bildunterschrift zum Inhalt? Gibt es Anzeichen von Manipulation?"
        else:
            text_prompt = f"{system_instructions}\n\n{search_context}\n\nAnalysiere dieses Bild. Prüfe: Ist es authentisch? Gibt es Anzeichen von Manipulation? Was zeigt es wirklich? Suche nach dem Originalkontext."

        message_content.append({
            "type": "text",
            "text": text_prompt
        })
    elif claim:
        logger.info(f"Processing text fact-check: '{claim[:60]}...'")
        text_prompt = f"{system_instructions}\n\n{search_context}\n\nÜberprüfe folgende Behauptung basierend auf den obigen Suchergebnissen:\n\n{claim}"
        
        message_content.append({
            "type": "text",
            "text": text_prompt
        })
    else:
        return "❌ Keine Behauptung oder Bild zum Überprüfen angegeben.", []

    messages = [
        {"role": "user", "content": message_content}
    ]

    # Step 2: Call OpenRouter with fallback models (strictly free models)
    models = [
        "google/gemini-2.0-flash-lite-preview-02-05:free",
        "deepseek/deepseek-chat-v3:free",
        "qwen/qwen-2.5-72b-instruct:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "mistralai/mistral-7b-instruct:free"
    ]

    last_error = None
    for model in models:
        try:
            logger.info(f"Calling OpenRouter API with model: {model}...")
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
                        "messages": messages,
                        "temperature": 0.3,
                        "max_tokens": 1500,
                    }
                )

                if response.status_code != 200:
                    logger.warning(f"Model {model} failed with status {response.status_code}: {response.text[:100]}")
                    continue

                data = response.json()
                if 'choices' not in data or not data['choices']:
                    logger.warning(f"Model {model} returned no choices: {data}")
                    continue

                result = data['choices'][0]['message']['content']
                
                elapsed = (datetime.now() - start_time).total_seconds()
                logger.info(f"✓ Fact-check completed with {model} in {elapsed:.1f}s ({len(result)} chars, {len(source_urls)} sources)")
                
                return result, source_urls
                
        except Exception as e:
            logger.warning(f"Attempt with model {model} failed: {e}")
            last_error = e
            continue

    logger.error(f"All models failed. Last error: {last_error}")
    raise last_error if last_error else Exception("All models failed to return a result")


async def fact(update: Update, context: CallbackContext):
    """
    Fact-check a claim, image, or image with caption using LLM with web search
    """
    user = update.effective_user
    chat_id = update.effective_chat.id
    logger.info(f"Fact-check request from user {user.id} ({user.username}) in chat {chat_id}")
    
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
            logger.info(f"Additional context provided: '{additional_context[:50]}...'")

        # Check for image
        if replied_msg.photo:
            photo = replied_msg.photo[-1]
            photo_file = await photo.get_file()

            try:
                image_base64 = await encode_image_to_base64(photo_file)
            except Exception as e:
                logger.error(f"Image encoding failed: {e}")
                await update.message.reply_text("❌ Fehler beim Laden des Bildes.")
                return

            if replied_msg.caption:
                caption = replied_msg.caption
                logger.info(f"Image with caption: '{caption[:50]}...'")

        # Check for text
        elif replied_msg.text:
            claim = replied_msg.text
            logger.info(f"Reply to text: '{claim[:50]}...'")

        # Delete the /fact command message for cleaner chat
        try:
            await update.message.delete()
        except:
            pass

    # Check if claim provided as command argument
    elif context.args:
        claim = " ".join(context.args)
        logger.info(f"Direct claim: '{claim[:50]}...'")

    # No content to check
    else:
        await update.message.reply_text(
            "ℹ️ <b>Verwendung:</b>\n"
            "• <code>/fact Deine Behauptung</code>\n"
            "• Antworte auf eine Nachricht mit <code>/fact</code>\n"
            "• Antworte auf ein Bild mit <code>/fact</code>",
            parse_mode="HTML"
        )
        return

    # Validate input
    if not image_base64 and (not claim or len(claim.strip()) < 10):
        logger.warning("Claim too short")
        await update.message.reply_text("❌ Die Behauptung ist zu kurz. Bitte gib mehr Details an.")
        return

    # Combine claim with additional context if provided
    if additional_context and claim:
        claim = f"{claim}\n\nZusätzlicher Kontext: {additional_context}"
    elif additional_context and caption:
        caption = f"{caption}\n\nZusätzlicher Kontext: {additional_context}"

    try:
        # Show "searching..." message
        status_msg = await update.message.reply_text("🔍 Suche aktuelle Informationen...")
        
        # Perform fact check with web search
        result, source_urls = await fact_check_with_llm(claim=claim, image_base64=image_base64, caption=caption)

        # Delete status message
        try:
            await status_msg.delete()
        except:
            pass

        # Format response
        response = ""

        if image_base64:
            response += "🖼️ <b>Bildanalyse</b>\n"
            if caption:
                response += f"<b>Bildunterschrift:</b> <i>{caption[:150]}{'...' if len(caption) > 150 else ''}</i>\n\n"
            else:
                response += "\n"
        else:
            response += f"<b>Behauptung:</b> <i>{claim[:150]}{'...' if len(claim) > 150 else ''}</i>\n\n"

        formatted_result = format_fact_check_result(result, source_urls)
        response += formatted_result

        logger.info(f"Sending response ({len(response)} chars)")

        # Reply to the original message
        if update.message.reply_to_message:
            await update.message.reply_to_message.reply_text(
                response,
                parse_mode="HTML",
                disable_web_page_preview=False
            )
        else:
            await update.message.reply_text(
                response,
                parse_mode="HTML",
                disable_web_page_preview=False
            )
            
        logger.info("✓ Fact-check response sent successfully")

    except Exception as e:
        logger.error(f"Fact-check failed: {e}", exc_info=True)
        error_msg = "❌ Fehler beim Faktencheck. Bitte versuche es später erneut."
        await update.message.reply_text(error_msg)