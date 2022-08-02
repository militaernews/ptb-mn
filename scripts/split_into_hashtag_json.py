import os
import shutil
from os import mkdir
from pathlib import Path

from dotenv import load_dotenv
from orjson import orjson

load_dotenv()

from data.lang import languages, GERMAN
from util.translation import translate


def split_to_json():
    output_directory = '../res/countries/'

    input_languages = [GERMAN] + languages
    for lang in input_languages:
        input_filename = f"flag_{lang.lang_key}.json"

        with open(input_filename, 'rb') as f:
            print(input_filename,lang.lang_key)
            content = orjson.loads(f.read())

            for flag_key, hashtag in content.items():
                print(flag_key, hashtag)
                output_filename = f"{ output_directory}{flag_key}.json"

                text = ""

                if lang.lang_key == GERMAN.lang_key:
                    text += f"{{\"{lang.lang_key}\":\"{hashtag.replace(' ', '_').replace('-', '').replace('.', '')}\""
                else:
                    text += f",\"{lang.lang_key}\":\"{hashtag.replace(' ', '').replace('-', '').replace('.', '')}\""

                if lang.lang_key == languages[-1].lang_key:
                    text += "}"

                with open(output_filename, 'a') as f:
                    f.write(text)


def translate_json():
    filename = f"flag_de.json"

    with open(filename, 'rb') as f:
        content = orjson.loads(f.read())
        print(content)

        for lang in languages:
            with open(f"flag_{lang.lang_key}.json", 'w') as f:

                text = ""

                first = True

                for flag_key, country_name in content.items():

                    hashtag = translate(lang.lang_key, country_name, lang.lang_key_deepl)
                    print("-- translated hashtag:: ", hashtag)

                    if first:
                        text += f"{{\"{flag_key}\":\"{hashtag}\""
                        first = False
                        continue

                    text += f",\"{flag_key}\":\"{hashtag}\""

                text += "}"
                f.write(text)


if __name__ == "__main__":
   # translate_json()
    split_to_json()
