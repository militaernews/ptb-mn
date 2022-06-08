import deepl  #upm package(deepl)
from typing import Union
import re
import os
from flag import flags

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

    return text


def translate_message(target_lang: str, text: str) -> str:
    translated_text = translator.translate_text(text, target_lang=target_lang)

    return flag_to_hashtag(translated_text, target_lang)


def is_flag_emoji(c):
    return "🇦" <= c <= "🇿" or c in ["🏴"]


def get_hashtag(key: str, language: Union[str, None] = None):
    hashtag = flags.get(key)

    if language is None:
        return hashtag

    return translator.translate_text(hashtag, target_lang=language)
