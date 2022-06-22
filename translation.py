import deepl  #upm package(deepl)
from typing import Union
import re
import os
from flag import flags
from deep_translator import GoogleTranslator

translator = deepl.Translator(os.environ['DEEPL'])


def flag_to_hashtag(text: str, language: Union[str, None] = None) -> str:

    if not re.compile(r'#\w+').search(text):

        last = None

        text += "\n\n"

        for c in text:

            if not is_flag_emoji(c):
                continue

            if last is None:
                last = c
                continue

            key = last + c

            if key in flags:
                text += "#" + get_hashtag(key, language).replace(" ", "") + " "

            last = None
    print("--- Translated Text ---")
    print(text)
    return text


def translate_message(target_lang: str, text: str) -> str:
    translated_text =  translate(target_lang, text)

    return flag_to_hashtag(translated_text, target_lang)


def is_flag_emoji(c):
    return "🇦" <= c <= "🇿" or c in ["🏴"]


def get_hashtag(key: str, language: Union[str, None] = None) -> str:
    hashtag = flags.get(key)

    if language is None:
        return hashtag

    return translate(language, hashtag)


def translate(target_lang: str, text: str) -> str:
    if target_lang == "fa": # or "ru"?
        return GoogleTranslator(source='de',
                                target=target_lang).translate(text=text)
    return translator.translate_text(text, target_lang=target_lang).text
