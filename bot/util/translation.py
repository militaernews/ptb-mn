"""
Translation utilities.

Issue #8 – Handle formatting with translation better
-----------------------------------------------------
The previous approach used a single unnamed placeholder (║) to protect
HTML tags and flag emojis from being mangled by the translation engine.
This caused two problems:

1. The pattern `<[^a>]+>` intentionally skipped `<a href=...>` anchor
   tags, so hyperlinks were passed to the translator and often broken.
2. Using a single repeated placeholder meant that if the translator
   reordered, duplicated, or dropped placeholders, the wrong tokens
   were restored at the wrong positions.

Fix: replace every HTML tag (including `<a …>` / `</a>`) and every flag
emoji with a *numbered* placeholder `║N║` before translation and restore
them by index afterwards.  This makes restoration order-independent and
ensures that hyperlinks survive translation intact.
"""

import asyncio
import logging
import os
import re
from json import loads, load
from typing import List, Optional, Tuple

import argostranslate.translate
import httpx
from data.lang import GERMAN, LANGUAGES
from deep_translator import GoogleTranslator
from deepl import Translator
from pysbd import Segmenter
from settings.config import OLLAMA_HOST, OLLAMA_MODEL, OPENROUTER_API_KEY, RES_PATH
from social.twitter import TWEET_LENGTH
from util.helper import sanitize_text
from util.patterns import HASHTAG, AMP_PATTERN, QUOT_PATTERN

deepl_translator = Translator(os.environ['DEEPL'])
google_translator = GoogleTranslator(source='auto')

# Display names used in the Ollama translation prompt (last-resort fallback)
OLLAMA_LANG_NAMES = {
    "en": "English", "tr": "Turkish", "fa": "Persian", "ru": "Russian",
    "pt": "Portuguese", "es": "Spanish", "fr": "French", "it": "Italian",
    "ar": "Arabic", "id": "Indonesian",
}

flags_data = {lang.lang_key: load(open(rf"{RES_PATH}/{lang.lang_key}/flags.json", "r", encoding="utf-8")) for lang in
              [GERMAN] + LANGUAGES}

HASHTAG_PATTERN = re.compile(r'(\s{2,})?(#\w+\s)+', re.IGNORECASE)
FLAG_PATTERN = re.compile(
    r'(?:'
    r'🏳️‍🌈|'  # LGBT flag (white flag + ZWJ + rainbow)
    r'🏳️‍⚧️|'  # Transgender flag (white flag + ZWJ + transgender symbol)
    r'🏴‍☠️|'  # Pirate flag (black flag + ZWJ + skull and crossbones)
    r'🏴󠁧󠁢(?:󠁥󠁮󠁧|󠁳󠁣󠁴|󠁷󠁬󠁳)󠁿|'  # England, Scotland, Wales flags
    r'[\U0001F1E6-\U0001F1FF]{2}|'  # Country flags (regional indicators)
    r'🏴|'  # Black flag
    r'🏳'   # White flag
    r')',
    re.UNICODE
)

# Combined pattern: ALL HTML tags (including <a href=...> and </a>) plus flag emojis.
# Using <[^>]+> instead of the old <[^a>]+> so that anchor tags are also protected.
_PROTECT_PATTERN = re.compile(
    r'<tg-emoji[^>]+>.*?</tg-emoji>|<[^>]+>|' + FLAG_PATTERN.pattern,
    re.IGNORECASE | re.UNICODE,
)

# Numbered placeholder template – must not appear in normal text
_PLACEHOLDER_TMPL = "║{n}║"
_PLACEHOLDER_RE = re.compile(r'║(\d+)║')


def _extract_tokens(text: str) -> Tuple[str, List[str]]:
    """Replace all HTML tags and flag emojis with numbered placeholders.

    Returns the processed text and the list of extracted tokens in order.
    """
    tokens: List[str] = []

    def _replace(m: re.Match) -> str:
        idx = len(tokens)
        tokens.append(m.group(0))
        return _PLACEHOLDER_TMPL.format(n=idx)

    processed = _PROTECT_PATTERN.sub(_replace, text)
    return processed, tokens


def _restore_tokens(text: str, tokens: List[str]) -> str:
    """Restore numbered placeholders back to their original tokens."""
    def _replace(m: re.Match) -> str:
        idx = int(m.group(1))
        return tokens[idx] if idx < len(tokens) else m.group(0)

    return _PLACEHOLDER_RE.sub(_replace, text)


def _strip_formatting(text: str) -> str:
    """Remove HTML tags and flag emojis outright instead of placeholder-protecting them.

    Placeholder-protecting formatting (see _extract_tokens) works well for English, but in
    practice some translation providers - especially the small/local LLM tiers - get thrown
    off by the "keep this placeholder untouched" instruction on other target languages and
    just echo the German input back untranslated instead. For every target language other
    than English, formatting is stripped outright before translation, trading inline
    formatting/hyperlinks for a guaranteed real translation.
    """
    return _PROTECT_PATTERN.sub('', text)


def flag_to_hashtag(text: str, lang_key: str = GERMAN.lang_key):
    if not HASHTAG.search(text):
        flags_in_caption = set(FLAG_PATTERN.findall(text))
        flag_names = sorted({
            flags_data[lang_key][flag]
            for flag in flags_in_caption
            if flag in flags_data[lang_key]
        })
        logging.info(f"flag:::::::::::::: {flags_in_caption} - {flag_names}")
        hashtags = f"\n#{' #'.join(flag_names)}" if flag_names else ""
        text = f"{text}\n{hashtags}"

    logging.info("--- Translated Text ---")
    logging.info(text)

    return text


async def translate_message(
    target_lang: str,
    text: str,
    target_lang_deepl: str = None,
    lang_username: str = None,
) -> str | None:
    """Translate *text* to *target_lang* and post-process the result.

    If *lang_username* is provided, any internal t.me/<GERMAN.username>/<id>
    links in the translated text are rewritten to point to the equivalent
    message in the destination language channel (Issue #9).
    """
    if not text or text is None:
        return None

    translated_text = await translate(target_lang, text, target_lang_deepl)
    translated_text = flag_to_hashtag(translated_text, target_lang)

    if lang_username is not None:
        translated_text = await rewrite_internal_links(translated_text, target_lang, lang_username)

    return translated_text


# could be replaced by using multiple txt-files for the different languages
def get_hashtag(country_key: str, lang_key: str = GERMAN.lang_key) -> str:
    logging.info("--- hashtag ---")

    try:
        filename = f"{RES_PATH}/{lang_key}/flags.json"
        logging.info(filename)

        with open(filename, 'rb', ) as f:
            # todo: find a way to open this file up just once when iterating through langs
            return loads(f.read())[country_key]
    except Exception as e:
        logging.warning(f"Error when trying to get hashtag --- {e}")


def translate_argos(text: str, target_lang: str) -> str:
    """Offline fallback translation via Argos Translate.

    Argos only ships a direct de->en model; every other target is reached by
    Argos pivoting through English automatically, as long as both the de->en
    and en->target packages are installed (see util/argos_setup.py).
    """
    return argostranslate.translate.translate(text, "de", target_lang)


_LLM_PLACEHOLDER_RE = re.compile(r'\[\[(\d+)\]\]')


def _to_llm_placeholder_format(text: str) -> str:
    """Small/local LLMs (and some free cloud ones) handle the rare ║N║
    box-drawing placeholder unreliably - e.g. qwen2.5:3b would either echo
    the German input back untouched or start mixing in Chinese characters
    when asked to preserve it. Bracket-style [[N]] placeholders are far more
    common in LLM training data (software localization/templating) and
    survive translation reliably, so LLM-based tiers use them instead and
    convert back to ║N║ afterward for the shared restore step.
    """
    return _PLACEHOLDER_RE.sub(lambda m: f"[[{m.group(1)}]]", text)


def _from_llm_placeholder_format(text: str) -> str:
    return _LLM_PLACEHOLDER_RE.sub(lambda m: f"║{m.group(1)}║", text)


def _translation_prompt(text: str, language_name: str) -> str:
    return (
        f"Translate the following German text into {language_name}.\n"
        f"Keep every placeholder token of the exact form [[number]] exactly as it is, "
        "in the same order and quantity - never translate, remove, or alter them.\n"
        "Reply with only the translated text, nothing else - no explanations, no quotes.\n\n"
        f"{_to_llm_placeholder_format(text)}"
    )


async def translate_ollama(text: str, target_lang: str) -> str:
    """Fallback translation via a local Ollama model."""
    language_name = OLLAMA_LANG_NAMES.get(target_lang, target_lang)

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{OLLAMA_HOST}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": _translation_prompt(text, language_name), "stream": False},
        )
        response.raise_for_status()
        return _from_llm_placeholder_format(response.json()["response"].strip())


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
# Free OpenRouter models, tried in order, used only as a last-resort translation
# fallback once Google, Argos and Ollama have all failed. OpenRouter's free-tier
# catalog changes over time, so entries here occasionally go stale - that's
# harmless, a stale model just fails fast and the loop moves to the next one.
OPENROUTER_TRANSLATE_MODELS = [
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "nvidia/nemotron-3.5-lightning:free",
    "google/gemma-4-26b-a4b-it:free",
    "liquid/lfm-2.5-2.6b:free",
]


async def translate_openrouter(text: str, target_lang: str) -> str:
    """Last-resort fallback translation via free OpenRouter models."""
    if not OPENROUTER_API_KEY:
        raise Exception("OPENROUTER_API_KEY not configured")

    language_name = OLLAMA_LANG_NAMES.get(target_lang, target_lang)
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/militaernews/ptb-mn",
        "X-Title": "ptb-mn Translation Fallback",
    }

    last_error = None
    async with httpx.AsyncClient(timeout=30.0) as client:
        for model in OPENROUTER_TRANSLATE_MODELS:
            try:
                response = await client.post(
                    OPENROUTER_URL,
                    headers=headers,
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": _translation_prompt(text, language_name)}],
                        "temperature": 0.2,
                    },
                )
                response.raise_for_status()
                translated = response.json()["choices"][0]["message"]["content"].strip()
                if translated:
                    return _from_llm_placeholder_format(translated)
            except Exception as e:
                last_error = e
                logging.warning(f"OpenRouter translation via {model} failed for {target_lang}: {e}")

    raise Exception(f"All OpenRouter translation models failed for {target_lang}: {last_error}")


def _placeholders_preserved(text: str, tokens: List[str]) -> bool:
    """Whether every numbered placeholder that protects an HTML tag or flag
    emoji is still present in *text*. MT engines - especially when pivoting
    through an intermediate language, as Argos does for every non-English
    target - can mangle or drop these placeholders instead of leaving them
    untouched, silently corrupting formatting/hyperlinks/flags. A translation
    that fails this check is discarded rather than published.
    """
    return all(_PLACEHOLDER_TMPL.format(n=i) in text for i in range(len(tokens)))


def _is_untranslated_echo(candidate: str, source_text: str) -> bool:
    """Whether *candidate* is just the (German) source text handed back unchanged.

    Some providers, when confused (e.g. by formatting placeholders they were told not to
    touch), play it safe and return the input verbatim instead of translating it. That's
    worse than an outright failure since it looks superficially like a valid result, so it
    has to be detected and rejected explicitly rather than published as a "translation".
    """
    return candidate.strip().casefold() == source_text.strip().casefold()


def _translation_acceptable(candidate: Optional[str], tokens: List[str], source_text: str) -> bool:
    if not candidate:
        return False
    if _is_untranslated_echo(candidate, source_text):
        return False
    return _placeholders_preserved(candidate, tokens)


async def translate(target_lang: str, text: str, target_lang_deepl: str = None) -> str:
    logging.info("---------------------------- text ----------------------------")
    logging.info(text)

    sub_text = sanitize_text(text)

    # Placeholder-protecting formatting (numbered ║N║ tokens for HTML tags/flag emojis)
    # works reliably for English, but in practice it makes some translation providers -
    # especially the small/local LLM tiers - just echo the German input back untranslated
    # for other target languages instead of translating it. So English keeps full
    # formatting preservation, while every other target language has formatting stripped
    # outright before translation (see _strip_formatting).
    if target_lang == "en":
        text_to_translate, tokens = _extract_tokens(sub_text)
    else:
        text_to_translate, tokens = _strip_formatting(sub_text), []

    translated_text = None
    try:
        google_translator.target = target_lang
        candidate = google_translator.translate(text=text_to_translate)
        # Check for specific Google Translate 500 error message
        if candidate and "Error 500 (Server Error)" in candidate:
            logging.error(f"Google Translate returned 500 error for text: {text_to_translate[:100]}...")
        elif _translation_acceptable(candidate, tokens, text_to_translate):
            translated_text = candidate
        else:
            logging.warning(f"Google Translate returned an unusable result for {target_lang}")
    except Exception as e:
        logging.warning(f"Google Translate failed for {target_lang}: {e}")

    if not translated_text:
        try:
            candidate = await asyncio.to_thread(translate_argos, text_to_translate, target_lang)
            if _translation_acceptable(candidate, tokens, text_to_translate):
                translated_text = candidate
            else:
                logging.warning(f"Argos Translate returned an unusable result for {target_lang}")
        except Exception as e:
            logging.warning(f"Argos Translate failed for {target_lang}: {e}")

    if not translated_text:
        try:
            candidate = await translate_ollama(text_to_translate, target_lang)
            if _translation_acceptable(candidate, tokens, text_to_translate):
                translated_text = candidate
            else:
                logging.warning(f"Ollama translation returned an unusable result for {target_lang}")
        except Exception as e:
            logging.warning(f"Ollama translation failed for {target_lang}: {e}")

    if not translated_text:
        try:
            candidate = await translate_openrouter(text_to_translate, target_lang)
            if _translation_acceptable(candidate, tokens, text_to_translate):
                translated_text = candidate
            else:
                logging.warning(f"OpenRouter translation returned an unusable result for {target_lang}")
        except Exception as e:
            logging.warning(f"OpenRouter translation failed for {target_lang}: {e}")

    if not translated_text:
        # Let the failure propagate so the caller logs it to the bot log group
        # rather than publishing a corrupted or untranslated post.
        raise RuntimeError(f"All translation providers failed to produce a usable translation for {target_lang}")

    # Restore HTML tags and emojis by index
    translated_text = _restore_tokens(translated_text, tokens)

    translated_text = AMP_PATTERN.sub(r"&", translated_text)
    translated_text = QUOT_PATTERN.sub(r'"', translated_text)

    logging.info(f"translated text ----------------- {text, tokens, sub_text, text_to_translate, translated_text}")
    return translated_text


# Pattern that matches t.me/<username>/<message_id> links (plain URL or inside href="...")
_INTERNAL_LINK_RE = re.compile(
    r'(https://t\.me/)' + re.escape(GERMAN.username) + r'/(\d+)',
    re.IGNORECASE,
)


async def rewrite_internal_links(
    text: str,
    lang_key: str,
    lang_username: str,
) -> str:
    """Replace t.me/<GERMAN.username>/<de_msg_id> links with the equivalent link
    in the destination language channel.

    For every match the DB is queried for the corresponding message ID in
    *lang_key*.  If a mapping is found the link is rewritten to
    t.me/<lang_username>/<lang_msg_id>; otherwise the original link is kept.
    """
    # Import here to avoid circular imports at module load time
    from data.db import get_lang_msg_id_for_de_msg_id

    if not _INTERNAL_LINK_RE.search(text):
        return text

    async def _replace(m: re.Match) -> str:
        de_msg_id = int(m.group(2))
        lang_msg_id: Optional[int] = await get_lang_msg_id_for_de_msg_id(de_msg_id, lang_key)
        if lang_msg_id is not None:
            return f"{m.group(1)}{lang_username}/{lang_msg_id}"
        # No mapping found – keep the original DE link
        return m.group(0)

    # re.sub does not support async callbacks; iterate manually
    result = text
    for m in list(_INTERNAL_LINK_RE.finditer(text)):
        replacement = await _replace(m)
        result = result.replace(m.group(0), replacement, 1)

    return result


def segment_text(text: str) -> str:
    segmenter = Segmenter(language='de', clean=False)

    tx = ""
    for s in segmenter.segment(text):
        if len(f"{tx} {s}") < TWEET_LENGTH - 20:
            tx += f" {s.lstrip()}"

    logging.info(f"----- tx {tx} -----")

    return tx
