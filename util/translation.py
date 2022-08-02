import os
import re

import deepl
from deep_translator import GoogleTranslator
from deepl import QuotaExceededException
from orjson import orjson

from data.lang import GERMAN
from util.helper import sanitize_text
from util.regex import FLAG_EMOJI, HASHTAG

translator = deepl.Translator(os.environ['DEEPL'])


def flag_to_hashtag(text: str, language: str = None) -> str:
    if not HASHTAG.search(text):

        flag_emojis = re.findall(FLAG_EMOJI, text)

        print("flag:::::::::::::: ", flag_emojis)

        text += "\n\n"

        for fe in flag_emojis:
            # todo: filter if valid flag?
            text += f"#{get_hashtag(fe, language)} "

    print("--- Translated Text ---")
    print(text)
    return text


def translate_message(target_lang: str, text: str, target_lang_deepl: str = None) -> str:
    translated_text = translate(target_lang, text, target_lang_deepl)

    return flag_to_hashtag(translated_text, target_lang)


# could be replaced by using multiple txt-files for the different languages
def get_hashtag(key: str, language: str = GERMAN.lang_key) -> str:
    print("--- hashtag ---")

    filename = f"res/countries/{key}.json"
    print(filename)

    with open(filename, 'rb') as f:
        return orjson.loads(f.read())[language]


def translate(target_lang: str, text: str, target_lang_deepl: str = None) -> str:
    print("---------------------------- text ----------------------------")
    print(text)
    print("--- footer")
    print(GERMAN.footer)
    print("--- replace")
    print(text.replace(GERMAN.footer, ""))
    print("--- cleaned text")

    sub_text = sanitize_text(text)

    cleaned_text = text.replace(GERMAN.footer, "")

    print(cleaned_text)
    print("--- sub text")
    print(sub_text)
    print("----------------------------")

    if target_lang == "fa":  # or "ru"?
        # text.replace: if bot was down and footer got added manually

        return GoogleTranslator(source='de', target=target_lang).translate(text=sub_text)
    try:
        return translator.translate_text(sub_text,
                                         target_lang=target_lang_deepl if target_lang_deepl is not None else target_lang,
                                         tag_handling="html").text
    except QuotaExceededException:
        print("--- Quota exceeded ---")
        return GoogleTranslator(source='de', target=target_lang).translate(text=sub_text)
        pass
    except Exception as e:
        print("--- other error translating --- ", e)
