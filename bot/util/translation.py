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
from difflib import SequenceMatcher
from json import loads, load
from typing import Callable, List, Optional, Tuple

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


_HTML_TAG_PATTERN = re.compile(
    r'<tg-emoji[^>]+>.*?</tg-emoji>|<[^>]+>',
    re.IGNORECASE,
)


def _extract_flag_tokens(text: str) -> Tuple[str, List[str]]:
    """Placeholder-protect only flag emojis (not HTML tags), for non-English targets.

    See _strip_formatting for why HTML tags are stripped outright on those targets - but a
    single flag emoji is a much simpler token than a run of HTML tags/links, so it doesn't
    trigger the same "echo the input back untranslated" confusion, and flags need to survive
    translation intact for flag_to_hashtag() to turn them into a hashtag afterwards.
    """
    tokens: List[str] = []

    def _replace(m: re.Match) -> str:
        idx = len(tokens)
        tokens.append(m.group(0))
        return _PLACEHOLDER_TMPL.format(n=idx)

    processed = FLAG_PATTERN.sub(_replace, text)
    return processed, tokens


def _strip_formatting(text: str) -> str:
    """Remove HTML tags outright instead of placeholder-protecting them.

    Placeholder-protecting formatting (see _extract_tokens) works well for English, but in
    practice some translation providers - especially the small/local LLM tiers - get thrown
    off by the "keep this placeholder untouched" instruction on other target languages and
    just echo the German input back untranslated instead. For every target language other
    than English, HTML formatting is stripped outright before translation, trading inline
    formatting/hyperlinks for a guaranteed real translation. Flag emojis are handled
    separately by _extract_flag_tokens and are not touched here.
    """
    return _HTML_TAG_PATTERN.sub('', text)


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


# None of the 10 target languages (en, tr, fa, ru, pt, es, fr, it, ar, id) use CJK script,
# so any CJK character in a translation is always contamination, never a legitimate result.
# Seen in production: the small local Ollama model (qwen2.5:3b) occasionally starts mixing
# Chinese characters into otherwise-correct translations, e.g. for Indonesian ("Bu是一個...").
_CJK_RE = re.compile(
    r'[぀-ヿ㐀-䶿一-鿿가-힯豈-﫿]'
)


def _has_unexpected_cjk(text: str) -> bool:
    return bool(_CJK_RE.search(text))


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
    if _has_unexpected_cjk(candidate):
        return False
    return _placeholders_preserved(candidate, tokens)


def _content_lines(text: str) -> List[str]:
    return [line for line in text.split("\n") if line.strip()]


_LETTER_RE = re.compile(r'[^\W\d_]')
_ECHO_MIN_WORDS = 4
_ECHO_SIMILARITY = 0.9
_MIN_LENGTH_RATIO = 0.5


def _is_echo_line(source_line: str, candidate_line: str) -> bool:
    """Whether a translated line is (nearly) the German source line - e.g. a
    title the provider skipped while translating the rest, or a line with just
    an article changed. Short lines are exempt, they may legitimately stay the
    same (names, places).
    """
    source_plain = _PLACEHOLDER_RE.sub("", source_line).strip().casefold()
    if len(source_plain.split()) < _ECHO_MIN_WORDS:
        return False
    candidate_plain = _PLACEHOLDER_RE.sub("", candidate_line).strip().casefold()
    return SequenceMatcher(None, source_plain, candidate_plain).ratio() >= _ECHO_SIMILARITY


def _structure_preserved(candidate: str, source: str) -> bool:
    """Whether a translation of a multi-line post kept its shape: same number of
    lines (a provider dropping the whole body after the title has been seen in
    production), not drastically shorter, and no line left in German.
    """
    source_lines = _content_lines(source)
    candidate_lines = _content_lines(candidate)
    if len(source_lines) != len(candidate_lines):
        return False
    if len(candidate.strip()) < _MIN_LENGTH_RATIO * len(source.strip()):
        return False
    return not any(_is_echo_line(s, c) for s, c in zip(source_lines, candidate_lines))


def _placeholders_kept(candidate: str, source: str) -> bool:
    return set(_PLACEHOLDER_RE.findall(source)) <= set(_PLACEHOLDER_RE.findall(candidate))


async def _translate_first_acceptable(text: str, target_lang: str, accept: Callable[[str], bool]) -> Optional[str]:
    """Try the providers in order (Google, then the offline Argos, the local
    Ollama model and free OpenRouter models as fallbacks) and return the first
    translation `accept` approves of, or None.
    """
    try:
        google_translator.target = target_lang
        candidate = google_translator.translate(text=text)
        # Check for specific Google Translate 500 error message
        if candidate and "Error 500 (Server Error)" in candidate:
            logging.error(f"Google Translate returned 500 error for text: {text[:100]}...")
        elif candidate and accept(candidate):
            return candidate
        else:
            logging.warning(f"Google Translate returned an unusable result for {target_lang}")
    except Exception as e:
        logging.warning(f"Google Translate failed for {target_lang}: {e}")

    fallbacks = (
        ("Argos Translate", lambda: asyncio.to_thread(translate_argos, text, target_lang)),
        ("Ollama translation", lambda: translate_ollama(text, target_lang)),
        ("OpenRouter translation", lambda: translate_openrouter(text, target_lang)),
    )
    for name, run in fallbacks:
        try:
            candidate = await run()
            if candidate and accept(candidate):
                return candidate
            logging.warning(f"{name} returned an unusable result for {target_lang}")
        except Exception as e:
            logging.warning(f"{name} failed for {target_lang}: {e}")

    return None


# A line formatted as a whole - e.g. "🇨🇷🔒 <b>Titel</b>", "<blockquote>Zitat</blockquote>" or "<a href=…>Quelle</a>":
# leading emojis/flag placeholders, one tag around the rest, trailing punctuation.
_WRAPPED_LINE_RE = re.compile(
    r'^(?P<pre>(?:║\d+║|[^\w<])*)'
    r'(?P<open><(?P<tag>b|strong|i|em|u|ins|s|strike|del|code|tg-spoiler|blockquote|a)(?:\s[^>]*)?>)'
    r'(?P<inner>.*)'
    r'(?P<close></(?P=tag)>)'
    r'(?P<post>[\s.,:;!?…]*)$',
    re.IGNORECASE,
)
_LEADING_SYMBOLS_RE = re.compile(r'^(?:║\d+║|[^\w<])*')
_TRAILING_PUNCTUATION_RE = re.compile(r'[\s.,:;!?…]*$')


def _wrapped_line(line: str) -> Optional[re.Match]:
    match = _WRAPPED_LINE_RE.match(line)
    if match is None or match.group("close") in match.group("inner"):
        return None  # e.g. "<b>A</b> text <b>B</b>" - not one tag around the whole line
    return match


def _plain_line(line: str) -> str:
    """The text of a line as sent to the translator - formatting stripped."""
    match = _wrapped_line(line)
    if match is None:
        return _strip_formatting(line)
    return f"{match.group('pre')}{_strip_formatting(match.group('inner'))}{match.group('post')}"


def _rewrap_line(source_line: str, translated_line: str) -> str:
    """Put a whole-line formatting (bold title, link, …) of `source_line` back
    around its translation, keeping leading emojis and trailing punctuation
    outside of it like in the source.
    """
    match = _wrapped_line(source_line)
    if match is None:
        return translated_line

    pre, core, post = "", translated_line, ""
    if match.group("pre").strip():
        pre_end = _LEADING_SYMBOLS_RE.match(core).end()
        pre, core = core[:pre_end], core[pre_end:]
    if match.group("post").strip():
        post_start = _TRAILING_PUNCTUATION_RE.search(core).start()
        core, post = core[:post_start], core[post_start:]
    return f"{pre}{match.group('open')}{core}{match.group('close')}{post}"


async def _translate_by_lines(flag_protected: str, target_lang: str) -> Optional[str]:
    """Translate with all formatting stripped except for lines formatted as a
    whole, which get their formatting re-applied around the translated line.
    Tries the post as a whole first, then line by line if no provider returns
    a translation that keeps the post's line structure.
    """
    source_lines = flag_protected.split("\n")
    plain_lines = [_plain_line(line) for line in source_lines]
    plain_text = "\n".join(plain_lines)

    whole = await _translate_first_acceptable(
        plain_text, target_lang,
        lambda c: _placeholders_kept(c, plain_text) and not _is_untranslated_echo(c, plain_text)
                  and not _has_unexpected_cjk(c) and _structure_preserved(c, plain_text),
    )
    if whole is not None:
        translated_lines = iter(_content_lines(whole))
        translated = [next(translated_lines) if plain.strip() else plain for plain in plain_lines]
    else:
        logging.warning(f"No whole-post translation kept the structure for {target_lang}, translating line by line")
        translated = []
        for plain in plain_lines:
            if not _LETTER_RE.search(_PLACEHOLDER_RE.sub("", plain)):
                translated.append(plain)  # blank, or just emojis/flags/punctuation
                continue
            line = await _translate_first_acceptable(
                plain, target_lang,
                lambda c, plain=plain: _placeholders_kept(c, plain) and not _has_unexpected_cjk(c)
                                       and len(_content_lines(c)) == 1 and not _is_echo_line(plain, c),
            )
            if line is None:
                return None
            translated.append(line.strip())

    return "\n".join(_rewrap_line(source, line) for source, line in zip(source_lines, translated))


async def translate(target_lang: str, text: str, target_lang_deepl: str = None) -> str:
    logging.info("---------------------------- text ----------------------------")
    logging.info(text)

    sub_text = sanitize_text(text)
    translated_text = None

    # Placeholder-protecting all formatting (numbered ║N║ tokens for HTML tags/flag
    # emojis) works reliably for English, so English keeps inline formatting and links.
    # For other target languages it makes some providers - especially the small/local
    # LLM tiers - echo the German input back untranslated, so there formatting is
    # stripped before translation, except that lines formatted as a whole (titles,
    # link lines) get it re-applied afterwards (see _translate_by_lines). Flag emojis
    # are placeholder-protected in both cases so they (and the hashtag flag_to_hashtag
    # derives from them) survive translation.
    if target_lang == "en":
        text_to_translate, tokens = _extract_tokens(sub_text)
        translated_text = await _translate_first_acceptable(
            text_to_translate, target_lang,
            lambda c: _translation_acceptable(c, tokens, text_to_translate)
                      and _structure_preserved(c, text_to_translate),
        )

    if translated_text is None:
        flag_protected, tokens = _extract_flag_tokens(sub_text)
        translated_text = await _translate_by_lines(flag_protected, target_lang)

    if not translated_text:
        # Let the failure propagate so the caller logs it to the bot log group
        # rather than publishing a corrupted or untranslated post.
        raise RuntimeError(f"All translation providers failed to produce a usable translation for {target_lang}")

    # Restore HTML tags and emojis by index
    translated_text = _restore_tokens(translated_text, tokens)

    translated_text = AMP_PATTERN.sub(r"&", translated_text)
    translated_text = QUOT_PATTERN.sub(r'"', translated_text)

    logging.info(f"translated text ----------------- {text, tokens, sub_text, translated_text}")
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
