import os
import re

import deepl
from deep_translator import GoogleTranslator
from deepl import QuotaExceededException

from data.flag import flags
from data.lang import GERMAN
from util.regex import HASHTAG, FOOTER

translator = deepl.Translator(os.environ['DEEPL'])


def flag_to_hashtag(text: str, language: str = None, target_lang_deepl: str = None) -> str:
    if not HASHTAG.search(text):

        last = None

        text += "\n\n"

        for c in text:

            if c not in ["🏴"]:
                if not is_flag_character(c):
                    continue

                if last is None:
                    last = c
                    continue

                key = last + c
            else:
                key = c

            if key in flags:
                text += "#" + get_hashtag(key, language, target_lang_deepl).replace(" ", "") + " "

            last = None
    print("--- Translated Text ---")
    print(text)
    return text


def translate_message(target_lang: str, text: str, target_lang_deepl: str = None) -> str:
    translated_text = translate(target_lang, text, target_lang_deepl)

    return flag_to_hashtag(translated_text, target_lang, target_lang_deepl)


def is_flag_character(c):
    return "🇦" <= c <= "🇿"


# could be replaced by using multiple txt-files for the different languages
def get_hashtag(key: str, language: str = None, target_lang_deepl: str = None) -> str:
    hashtag = flags.get(key)

    if language is None:
        return hashtag

    # maybe just pass along the hashtag an let it translate in full?
    # will not for for e.g. French where UK has hyphen
    return translate(language, hashtag, target_lang_deepl).replace("-", "")


def translate(target_lang: str, text: str, target_lang_deepl: str = None) -> str:
    print("---------------------------- text")
    print(text)
    print("--- footer")
    print(GERMAN.footer)
    print("--- replace")
    print(text.replace(GERMAN.footer, ""))
    print("--- cleaned text")

    sub_text = re.sub(FOOTER, "", text, )

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
