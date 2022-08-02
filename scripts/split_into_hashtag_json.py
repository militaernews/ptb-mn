from data.flag_en import flag_en
from data.lang import languages

for flag_key, hashtag in flag_en.items():
    print(flag_key, hashtag)
    filename = f"../res/countries/{flag_key}.json"

    text = ""

    first = True

    for lang in languages:

        if first:
            text += f"{{\"{lang.lang_key}\":\"{hashtag.replace(' ', '').replace('-', '').replace('.', '')}\""
            first = False
            continue

        text += f",\"{lang.lang_key}\":\"{hashtag.replace(' ', '').replace('-', '').replace('.', '')}\""

    text += "}"

    with open(filename, 'w') as f:
        f.write(text)
