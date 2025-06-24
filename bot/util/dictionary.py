import re

REPLACEMENTS = {
    "Kyjiw": r"Kie[wv]",
}

def replace_name(text:str) -> str:
    for replacement, pattern in REPLACEMENTS.items():
        text = re.sub(pattern, replacement, text,re.IGNORECASE)

    return text