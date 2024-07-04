import logging
import os
import re
from json import loads

import deepl
from deep_translator import GoogleTranslator
from deepl import QuotaExceededException
from pysbd import Segmenter

from data.lang import GERMAN
from twitter import TWEET_LENGTH
from util.helper import sanitize_text
from util.patterns import FLAG_EMOJI, HASHTAG, PLACEHOLDER

deepl_translator = deepl.Translator(os.environ['DEEPL'])
google_translator = GoogleTranslator(source='auto')


def flag_to_hashtag(text: str, language: str = None):
    if not HASHTAG.search(text):

        flag_emojis = re.findall(FLAG_EMOJI, text)

        logging.info(f"flag:::::::::::::: {flag_emojis}")

        if len(flag_emojis) == 0:
            return f"\n{text}"

        text += "\n\n"

        for fe in list(set(flag_emojis)):
            # todo: filter if valid flag?
            text += f"#{get_hashtag(fe, language)} "

    logging.info("--- Translated Text ---")
    logging.info(text)
    return text


async def translate_message(target_lang: str, text: str, target_lang_deepl: str = None) -> str | None:
    if not text or text is None:
        return None

    translated_text = await translate(target_lang, text, target_lang_deepl)

    return flag_to_hashtag(translated_text, target_lang)


# could be replaced by using multiple txt-files for the different languages
def get_hashtag(key: str, language: str = None) -> str:
    logging.info("--- hashtag ---")
    if language is None:
        language = GERMAN.lang_key

    try:
        filename = f"res/countries/{key}.json"
        logging.info(filename)

        with open(filename, 'rb', ) as f:
            # todo: find a way to open this file up just once when iterating through langs
            return loads(f.read())[language]
    except Exception as e:
        logging.error(f"Error when trying to get hashtag --- {e}")


async def translate(target_lang: str, text: str, target_lang_deepl: str = None) -> str:
    logging.info("---------------------------- text ----------------------------")
    logging.info(text)

    sub_text = sanitize_text(text)
    emojis = re.findall(FLAG_EMOJI, sub_text)
    text_to_translate = re.sub(FLAG_EMOJI, PLACEHOLDER, sub_text)

    if target_lang == "fa" or target_lang == "ar":  # or "ru"?
        # text.replace: if bot was down and footer got added manually

        # I'm uncertain, whether replacing emojis for Right-to-left languages like Persian butchers the order
        google_translator.target = target_lang
        translated_text = google_translator.translate(text=text_to_translate)
    try:
        google_translator.target = target_lang
        translated_text = google_translator.translate(text=text_to_translate)
    # translator.translate_text(text_to_translate,
    #   target_lang=target_lang_deepl if target_lang_deepl is not None else target_lang,
    #     tag_handling="html",
    #      preserve_formatting=True).text

    except QuotaExceededException:
        logging.warning("--- Quota exceeded ---")
        translated_text = GoogleTranslator(source='de', target=target_lang).translate(text=text_to_translate)
        pass
    except Exception as e:
        logging.error(f"--- other error translating --- {e}")

        translated_text = GoogleTranslator(source='de', target=target_lang).translate(text=text_to_translate)
        pass

    for emoji in emojis:
        translated_text = re.sub(PLACEHOLDER, emoji, translated_text, 1)

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
