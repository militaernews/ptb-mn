"""
Synthesize mode for PTB-MN: combine multiple text/media sources into one
Telegram-ready post and publish it directly into the German channel.

Ported from ptb-suggest's private/ai_assistant.py (same TITEL:/TEXT: parsing,
flag/word-count enforcement, pysbd sentence-splitting into a 2-paragraph/
5-sentence body). The key difference: ptb-suggest only ever hands the result
back to an admin for manual/placeholder publishing, while here "publish" is
real - posting to GERMAN.channel_id feeds straight into main.py's existing
news_post pipeline (register_news), which already translates/cross-posts/
tweets/indexes anything that lands in that channel, whether typed by a human
admin or sent by the bot itself.
"""
import logging
import re
from typing import Dict, List, Optional

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto,
    InputMediaVideo,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from telegram.constants import ChatAction
from httpx import AsyncClient
from pysbd import Segmenter

from data.lang import GERMAN
from settings.config import ADMINS, OPENROUTER_API_KEY
from util.translation import FLAG_PATTERN

logger = logging.getLogger(__name__)

# Conversation states
COLLECTING_SOURCES = 1
REVIEWING = 2
EDITING = 3

MAX_MEDIA = 10  # Telegram's own hard limit for a single media group (album)
MAX_TITLE_WORDS = 8
BODY_SENTENCES = 5


class PostSynthesizer:
    """Synthesizes multiple text snippets/captions into one Telegram-ready post."""

    def __init__(self):
        # Free-tier OpenRouter models - see ptb-suggest's ai_assistant.py for
        # why non-reasoning models go first and the nemotron fallback exists;
        # OpenRouter retires/renames free models often, re-check
        # https://openrouter.ai/api/v1/models if synthesis starts failing.
        self.models = [
            "minimax/minimax-m3:free",
            "z-ai/glm-5.2:free",
            "google/gemma-4-31b-it:free",
            "nvidia/nemotron-3-super-120b-a12b:free",
            "nvidia/nemotron-3-ultra-550b-a55b:free",
            "nvidia/nemotron-3.5-lightning:free",
        ]
        self.reasoning_models = {
            "nvidia/nemotron-3-super-120b-a12b:free",
            "nvidia/nemotron-3-ultra-550b-a55b:free",
            "nvidia/nemotron-3.5-lightning:free",
        }

    def _build_prompt(self, snippets: List[str]) -> str:
        snippets_text = "\n---\n".join(snippets)
        return f"""Du bist ein erfahrener Nachrichtenredakteur für einen Militär-Informationskanal.

Fasse die folgenden Nachrichtenausschnitte (Texte und/oder Bildunterschriften) aus
verschiedenen Quellen zu einem einzigen Kanal-Post zusammen.

REGELN:
1. Alles auf Deutsch, sachlich, keine Spekulation, keine Redundanzen zwischen den Quellen.
2. Der Titel beginnt mit den zum Inhalt passenden Länder-Flaggen-Emojis (z.B. 🇷🇺🇺🇦), gefolgt von maximal {MAX_TITLE_WORDS} prägnanten Wörtern. Kein Satzzeichen am Ende des Titels.
3. Der Fließtext besteht aus genau {BODY_SENTENCES} sachlichen, vollständigen Sätzen.

NACHRICHTENAUSSCHNITTE:
{snippets_text}

Antworte NUR in exakt diesem Format, ohne jeden zusätzlichen Text davor oder danach:
TITEL: <Flaggen-Emojis> <Titel in maximal {MAX_TITLE_WORDS} Wörtern>
TEXT: <Fließtext mit genau {BODY_SENTENCES} Sätzen>"""

    def _parse_post(self, content: str) -> Optional[Dict[str, str]]:
        """Parse the model's `TITEL: ... / TEXT: ...` reply into a Telegram-ready
        HTML post: a bold, flag-prefixed, word-capped title followed by two
        paragraphs totalling `BODY_SENTENCES` sentences.
        """
        title_match = re.search(r'TITEL:\s*(.+)', content, re.IGNORECASE)
        text_match = re.search(r'TEXT:\s*(.+)', content, re.IGNORECASE | re.DOTALL)
        if not title_match or not text_match:
            return None

        title_raw = title_match.group(1).splitlines()[0].strip()
        flags = "".join(FLAG_PATTERN.findall(title_raw))
        title_words = FLAG_PATTERN.sub("", title_raw).split()
        title_text = " ".join(title_words[:MAX_TITLE_WORDS]).strip(" .")
        if not title_text:
            return None
        title = f"{flags} {title_text}".strip() if flags else title_text

        body_raw = re.sub(r'\s+', ' ', text_match.group(1)).strip()
        sentences = [s.strip() for s in Segmenter(language="de", clean=False).segment(body_raw) if s.strip()]
        if not sentences:
            return None
        sentences = sentences[:BODY_SENTENCES]

        # Split into two paragraphs - 3+2 for the target of 5 sentences,
        # otherwise as evenly as possible (first paragraph gets the extra one).
        if len(sentences) <= 1:
            paragraphs = [" ".join(sentences)]
        else:
            split_at = min(3, len(sentences) - 1) if len(sentences) >= 5 else -(-len(sentences) // 2)
            paragraphs = [" ".join(sentences[:split_at]), " ".join(sentences[split_at:])]
        body = "\n\n".join(p for p in paragraphs if p)

        return {"title": title, "body": body, "html": f"<b>{title}</b>\n\n{body}"}

    async def synthesize(self, snippets: List[str]) -> Optional[Dict[str, str]]:
        if not snippets:
            logger.warning("[synthesizer] No snippets provided for synthesis")
            return None

        prompt = self._build_prompt(snippets)

        for model in self.models:
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
                            "messages": [{"role": "user", "content": prompt}],
                            "temperature": 0.5,
                            "max_tokens": 2500 if model in self.reasoning_models else 1000,
                        }
                    )

                    if response.status_code == 200:
                        data = response.json()
                        choice = data['choices'][0]
                        result = choice['message']['content']

                        if model in self.reasoning_models and choice.get('finish_reason') == 'length':
                            logger.warning(
                                f"[synthesizer] {model} was truncated mid-reasoning, discarding output"
                            )
                            continue

                        post = self._parse_post(result)
                        if post is None:
                            logger.warning(
                                f"[synthesizer] {model} did not follow the TITEL:/TEXT: format, discarding output"
                            )
                            continue

                        logger.info(f"[synthesizer] Successfully synthesized post via {model}")
                        return post
                    else:
                        error_msg = f"Model {model}: Status {response.status_code}"
                        try:
                            error_json = response.json()
                            if 'error' in error_json:
                                error_msg += f" - {error_json['error'].get('message', 'Unknown error')}"
                        except Exception:
                            pass
                        logger.warning(f"[synthesizer] {error_msg}")

                        if response.status_code == 401:
                            logger.error(
                                "[synthesizer] OPENROUTER_API_KEY was rejected (401), "
                                "not retrying remaining models."
                            )
                            return None

            except Exception as e:
                logger.warning(f"[synthesizer] Model {model} failed: {str(e)}")
                continue

        logger.error("[synthesizer] All models failed for synthesis")
        return None


async def start_synthesis(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the synthesize workflow."""
    if update.effective_user.id not in ADMINS:
        await update.message.reply_text("❌ Du hast keine Berechtigung für diesen Befehl.")
        return ConversationHandler.END

    await update.message.reply_text(
        "📰 <b>Synthese-Assistent</b>\n\n"
        "Sende mir Text-Ausschnitte und/oder bis zu "
        f"{MAX_MEDIA} Bilder/Videos (Bildunterschriften werden mit übernommen). "
        "Am Ende kannst du den fertigen Post direkt im Kanal veröffentlichen.\n\n"
        "Wenn du fertig bist, sende /done. Mit /cancel kannst du abbrechen.",
        parse_mode="HTML"
    )
    context.user_data["synth_snippets"] = []
    context.user_data["synth_media"] = []
    return COLLECTING_SOURCES


async def collect_snippet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Collect text snippets and/or media (with captions) for synthesis."""
    snippets = context.user_data.setdefault("synth_snippets", [])
    media = context.user_data.setdefault("synth_media", [])

    message = update.message
    note = None

    if message.photo or message.video:
        if len(media) >= MAX_MEDIA:
            await message.reply_text(f"⚠️ Maximal {MAX_MEDIA} Medien pro Album. Dieses wurde ignoriert.")
        else:
            if message.photo:
                media.append({"type": "photo", "file_id": message.photo[-1].file_id})
            else:
                media.append({"type": "video", "file_id": message.video.file_id})
            note = f"🖼️ Medium #{len(media)} empfangen"
        if message.caption:
            snippets.append(message.caption)
    elif message.text and not message.text.startswith("/"):
        snippets.append(message.text)
        note = f"✅ Ausschnitt #{len(snippets)} empfangen ({len(message.text)} Zeichen)"

    if note:
        await message.reply_text(
            f"{note}.\n"
            f"📎 {len(media)} Medien, {len(snippets)} Text(e)/Bildunterschrift(en) gesammelt.\n"
            f"Weitere senden oder /done zum Starten.",
            parse_mode="HTML"
        )

    return COLLECTING_SOURCES


def _review_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Im Kanal veröffentlichen", callback_data="synth_publish")],
        [
            InlineKeyboardButton("✏️ Bearbeiten", callback_data="synth_edit"),
            InlineKeyboardButton("🚫 Verwerfen", callback_data="synth_discard"),
        ],
    ])


async def _show_preview(message, post: Dict[str, str], media: List[dict]):
    label = f"📝 <b>Vorschau</b> ({len(media)} Medien):" if media else "📝 <b>Vorschau:</b>"
    await message.reply_text(
        f"{label}\n\n{post['html']}",
        parse_mode="HTML",
        reply_markup=_review_keyboard(),
    )


async def process_synthesis(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Synthesize the collected snippets/media into one post and show a preview."""
    snippets = context.user_data.get("synth_snippets", [])
    media = context.user_data.get("synth_media", [])

    if not snippets:
        await update.message.reply_text(
            "❌ Kein Text und keine Bildunterschrift gefunden. Sende mindestens einen "
            "Ausschnitt oder ein Bild/Video mit Bildunterschrift. Abbruch."
        )
        return ConversationHandler.END

    await update.message.reply_text("⏳ Synthetisiere Post... Bitte warten.")
    await update.message.chat.send_chat_action(ChatAction.TYPING)

    post = await PostSynthesizer().synthesize(snippets)
    if not post:
        await update.message.reply_text(
            "❌ <b>Fehler bei der Synthese</b>\n\n"
            "Alle verfügbaren Modelle sind fehlgeschlagen. Bitte versuche es später erneut.",
            parse_mode="HTML"
        )
        return ConversationHandler.END

    context.user_data["synth_post"] = post
    await _show_preview(update.message, post, media)
    return REVIEWING


async def request_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "✏️ Sende den neuen Text (Titel + Fließtext, HTML erlaubt). Mit /cancel abbrechen.",
        parse_mode="HTML"
    )
    return EDITING


async def collect_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message.text or update.message.text.startswith("/"):
        return EDITING

    post = context.user_data.get("synth_post", {})
    post["html"] = update.message.text
    context.user_data["synth_post"] = post

    media = context.user_data.get("synth_media", [])
    await _show_preview(update.message, post, media)
    return REVIEWING


async def publish_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Actually publish the synthesized post to the German channel - this feeds
    straight into main.py's news_post pipeline, which cross-posts/translates/
    tweets it exactly as if an admin had typed it into the channel directly.
    """
    query = update.callback_query
    await query.answer()

    post = context.user_data.get("synth_post")
    media = context.user_data.get("synth_media", [])

    if not post:
        await query.edit_message_text("❌ Kein synthetisierter Post gefunden. Bitte mit /synthesize neu starten.")
        return ConversationHandler.END

    try:
        if media:
            media_group = []
            for i, m in enumerate(media[:MAX_MEDIA]):
                cls = InputMediaPhoto if m["type"] == "photo" else InputMediaVideo
                kwargs = {"media": m["file_id"]}
                if i == 0:
                    kwargs["caption"] = post["html"]
                    kwargs["parse_mode"] = "HTML"
                media_group.append(cls(**kwargs))
            await context.bot.send_media_group(chat_id=GERMAN.channel_id, media=media_group)
        else:
            await context.bot.send_message(chat_id=GERMAN.channel_id, text=post["html"], parse_mode="HTML")
    except Exception as e:
        logger.error(f"[synthesize] Failed to publish to channel: {e}")
        await query.edit_message_text(f"❌ Veröffentlichung fehlgeschlagen: {e}")
        return ConversationHandler.END

    await query.edit_message_text("✅ Im Kanal veröffentlicht!")
    logger.info(f"[synthesize] Published post to channel {GERMAN.channel_id}")
    context.user_data.pop("synth_snippets", None)
    context.user_data.pop("synth_media", None)
    context.user_data.pop("synth_post", None)
    return ConversationHandler.END


async def discard_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🚫 Post verworfen.")
    context.user_data.pop("synth_snippets", None)
    context.user_data.pop("synth_media", None)
    context.user_data.pop("synth_post", None)
    return ConversationHandler.END


async def cancel_synthesis(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the synthesize workflow."""
    await update.message.reply_text("🚫 Synthese-Assistent abgebrochen.")
    context.user_data.pop("synth_snippets", None)
    context.user_data.pop("synth_media", None)
    context.user_data.pop("synth_post", None)
    return ConversationHandler.END


def register_synthesize(application):
    """Register the /synthesize handlers."""
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("synthesize", start_synthesis)],
        states={
            COLLECTING_SOURCES: [
                MessageHandler(
                    (filters.TEXT | filters.PHOTO | filters.VIDEO) & ~filters.COMMAND,
                    collect_snippet,
                ),
                CommandHandler("done", process_synthesis),
            ],
            REVIEWING: [
                CallbackQueryHandler(publish_post, pattern="^synth_publish$"),
                CallbackQueryHandler(request_edit, pattern="^synth_edit$"),
                CallbackQueryHandler(discard_post, pattern="^synth_discard$"),
            ],
            EDITING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, collect_edit),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_synthesis)],
    )
    application.add_handler(conv_handler)
    logger.info("[synthesize] Synthesize-and-publish assistant registered")
