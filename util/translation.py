import logging
import os
import re

import deepl
from deep_translator import GoogleTranslator
from deepl import QuotaExceededException
from orjson import orjson

from config import PLACEHOLDER
from data.lang import GERMAN
from util.helper import sanitize_text
from util.regex import FLAG_EMOJI, HASHTAG

translator = deepl.Translator(os.environ['DEEPL'])


def flag_to_hashtag(text: str, language: str = None):
    if not HASHTAG.search(text):

        flag_emojis = re.findall(FLAG_EMOJI, text)

        print("flag:::::::::::::: ", flag_emojis)

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
    if text == "" or text is None:
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

        with open(filename, 'rb') as f:
            # todo: find a way to open this file up just once when iterating through langs
            return orjson.loads(f.read())[language]
    except Exception as e:
        logging.error(f"Error when trying to get hashtag --- {e}")
        pass


async def translate(target_lang: str, text: str, target_lang_deepl: str = None) -> str:
    logging.info("---------------------------- text ----------------------------")
    logging.info(text)

    sub_text = sanitize_text(text)
    emojis = re.findall(FLAG_EMOJI, sub_text)
    text_to_translate = re.sub(FLAG_EMOJI, PLACEHOLDER, sub_text)

    if target_lang == "fa":  # or "ru"?
        # text.replace: if bot was down and footer got added manually

        # I'm uncertain, whether replacing emojis for Right-to-left languages like Persian butchers the order
        translated_text = GoogleTranslator(source='de', target=target_lang).translate(text=text_to_translate)
    try:
        translated_text = GoogleTranslator(source='de', target=target_lang).translate(
            text=text_to_translate)  # translator.translate_text(text_to_translate,
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

    logging.info(f"translated text ----------------- {text, emojis, sub_text, text_to_translate, translated_text}" )
    return translated_text
