import json
import os

from dotenv import load_dotenv

from bot.util.helper import sanitize_hashtag

load_dotenv()

from bot.data.lang import languages, GERMAN
from bot.util.translation import translate


def split_to_json():
    output_directory = '../res/countries/'
    if not os.path.isdir(output_directory):
        os.mkdir(output_directory)

    input_languages = [GERMAN] + languages
    for lang in input_languages:
        input_filename = f"flag_{lang.lang_key}.json"

        with open(input_filename, 'rb') as input_file:
            content = json.load(input_file)

        for flag_key, hashtag in content.items():
            output_filename = os.path.join(output_directory, f"{flag_key}.json")
            data = {lang.lang_key: sanitize_hashtag(lang.lang_key, hashtag)}

            with open(output_filename, 'a', encoding="utf-8") as output_file:
                json.dump(data, output_file, ensure_ascii=False)


def translate_json():
    filename = "res/flag_de.json"

    with open(filename, 'rb') as f:
        content = json.load(f)

        for lang in languages:
            output_filename = f"flag_{lang.lang_key}.json"
            translation = {flag_key: translate(lang.lang_key, country_name, lang.lang_key_deepl)
                           for flag_key, country_name in content.items()}

            with open(output_filename, 'w', encoding="utf-8") as f:
                json.dump(translation, f, ensure_ascii=False)


if __name__ == "__main__":
    # translate_json()
    split_to_json()
