import logging
import os
import re
from json import loads, load

from data.lang import GERMAN, LANGUAGES
from deep_translator import GoogleTranslator
from deepl import QuotaExceededException, Translator
from pysbd import Segmenter
from settings.config import RES_PATH
from social.twitter import TWEET_LENGTH
from util.helper import sanitize_text
from util.patterns import HASHTAG, PLACEHOLDER, FLAG_EMOJI_HTMLTAG, AMP_PATTERN, QUOT_PATTERN

from util.llms import llm_translate_openai

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


async def translate_message(target_lang: str, text: str, target_lang_deepl: str = None) -> str | None:
    if not text or text is None:
        return None

    translated_text = await translate(target_lang, text, target_lang_deepl)

    return flag_to_hashtag(translated_text, target_lang)


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
    emojis = re.findall(FLAG_EMOJI_HTMLTAG, sub_text)
    text_to_translate = re.sub(FLAG_EMOJI_HTMLTAG, PLACEHOLDER, sub_text)

    translated_text = None
    try: 
        in_count = text_to_translate.count(PLACEHOLDER)
        translated_text = await llm_translate_openai(target_lang, text_to_translate)
        if not translated_text:
            raise ValueError("No output from LLM.")
        if translated_text.count(PLACEHOLDER) != in_count:
            raise ValueError("LLM placeholder count mismatch.")
    except Exception as e:
        logging.warning(f"LLM translation failed. Reason: {e}. Falling back to lobotomized methods.")

        if target_lang == "fa" or target_lang == "ar":  # or "ru"?
            # text.replace: if bot was down and footer got added manually

            # I'm uncertain, whether replacing emojis for Right-to-left languages like Persian butchers the order
            google_translator.target = target_lang
            translated_text = google_translator.translate(text=text_to_translate)
        else:
            try:
                google_translator.target = target_lang
                translated_text = google_translator.translate(text=text_to_translate)
            # translator.translate_text(text_to_translate,
            #   target_lang=target_lang_deepl if target_lang_deepl is not None else target_lang,
            #     tag_handling="html",
            #      preserve_formatting=True).text

            except QuotaExceededException:
                logging.warning("--- Quota exceeded ---")
                # TODO: switch to other deepl key
                translated_text = GoogleTranslator(source='de', target=target_lang).translate(text=text_to_translate)
                pass
            except Exception as e:
                logging.error(f"--- other error translating --- {e}")

                translated_text = GoogleTranslator(source='de', target=target_lang).translate(text=text_to_translate)
                pass

    for emoji in emojis:
        translated_text = re.sub(PLACEHOLDER, emoji, translated_text, 1)

    translated_text= AMP_PATTERN.sub(r"&",translated_text)
    translated_text= QUOT_PATTERN.sub(r'"',translated_text)

    logging.info(f"translated text ----------------- {text, emojis, sub_text, text_to_translate, translated_text}")
    return translated_text


def segment_text(text: str) -> str:
    segmenter = Segmenter(language='de', clean=False)

    tx = ""
    for s in segmenter.segment(text):
        if len(f"{tx} {s}") < TWEET_LENGTH - 20:
            tx += f" {s.lstrip()}"

    logging.info(f"----- tx {tx} -----")

    return tx
