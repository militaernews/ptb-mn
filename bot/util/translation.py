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

import logging
import os
import re
from json import loads, load
from typing import List, Optional, Tuple

from data.lang import GERMAN, LANGUAGES
from deep_translator import GoogleTranslator
from deepl import QuotaExceededException, Translator
from pysbd import Segmenter
from settings.config import RES_PATH
from social.twitter import TWEET_LENGTH
from util.helper import sanitize_text
from util.patterns import HASHTAG, AMP_PATTERN, QUOT_PATTERN

deepl_translator = Translator(os.environ['DEEPL'])
google_translator = GoogleTranslator(source='auto')

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
    r'<[^>]+>|' + FLAG_PATTERN.pattern,
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


async def translate(target_lang: str, text: str, target_lang_deepl: str = None) -> str:
    logging.info("---------------------------- text ----------------------------")
    logging.info(text)

    sub_text = sanitize_text(text)

    # Extract HTML tags and flag emojis as numbered placeholders so the
    # translator never sees them and cannot corrupt formatting or hyperlinks.
    text_to_translate, tokens = _extract_tokens(sub_text)

    if target_lang == "fa" or target_lang == "ar":  # or "ru"?
        # I'm uncertain whether replacing emojis for RTL languages like Persian
        # butchers the order – keeping the same branch as before.
        google_translator.target = target_lang
        translated_text = google_translator.translate(text=text_to_translate)
    else:
        try:
            google_translator.target = target_lang
            translated_text = google_translator.translate(text=text_to_translate)
            # DeepL alternative (kept for reference):
            # translated_text = deepl_translator.translate_text(
            #     text_to_translate,
            #     target_lang=target_lang_deepl if target_lang_deepl is not None else target_lang,
            #     tag_handling="html",
            #     preserve_formatting=True,
            # ).text

        except QuotaExceededException:
            logging.warning("--- Quota exceeded ---")
            # TODO: switch to other deepl key
            translated_text = GoogleTranslator(source='de', target=target_lang).translate(text=text_to_translate)
        except Exception as e:
            logging.error(f"--- other error translating --- {e}")
            translated_text = GoogleTranslator(source='de', target=target_lang).translate(text=text_to_translate)

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
