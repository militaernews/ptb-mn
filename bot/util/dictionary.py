import re

REPLACEMENTS = {
    "Kyjiw": r"Kie[wv]",
    "Lemberg": r"L[wv][io][wv]",
    "Königsberg": r"Kaliningrad",
    "Selenskij": r"Zelensky",
}


def replace_name(text: str) -> str:
    for replacement, pattern in REPLACEMENTS.items():
        text = re.sub(pattern, replacement, text, re.IGNORECASE)

    return text
