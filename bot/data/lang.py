import json
import os
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Language:
    lang_key: str
    channel_id: int
    footer: str
    breaking: str
    announce: str
    advertise: str
    username: str
    chat_id: Optional[int] = None
    lang_key_deepl: Optional[str] = None
    # captcha:str


def _load_languages() -> tuple["Language", List["Language"]]:
    """Load language configuration from languages.json, falling back to env vars for IDs."""
    config_path = os.path.join(os.path.dirname(__file__), "languages.json")
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    def _make(entry: dict) -> "Language":
        # Allow individual channel IDs to be overridden via environment variables.
        # E.g. CHANNEL_ID_DE, CHANNEL_ID_EN, CHAT_ID_DE, CHAT_ID_EN …
        key = entry["lang_key"].upper()
        channel_id = int(os.getenv(f"CHANNEL_ID_{key}", entry["channel_id"]))
        chat_id = entry.get("chat_id")
        if chat_id is not None:
            chat_id = int(os.getenv(f"CHAT_ID_{key}", chat_id))
        return Language(
            lang_key=entry["lang_key"],
            channel_id=channel_id,
            footer=entry["footer"],
            breaking=entry["breaking"],
            announce=entry["announce"],
            advertise=entry["advertise"],
            username=entry["username"],
            chat_id=chat_id,
            lang_key_deepl=entry.get("lang_key_deepl"),
        )

    german = _make(data["german"])
    languages = [_make(e) for e in data["languages"]]
    return german, languages


GERMAN, LANGUAGES = _load_languages()

# Keep ENGLISH as a convenience alias (first entry in LANGUAGES)
ENGLISH = LANGUAGES[0]

LANG_DICT = {language.lang_key: language for language in [GERMAN] + LANGUAGES}
