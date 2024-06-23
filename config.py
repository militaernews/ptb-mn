import os
from json import loads
from typing import Final, List, Set

from dotenv import load_dotenv

load_dotenv()

TOKEN: Final[str] = os.getenv('TELEGRAM')
PORT: Final[int] = int(os.getenv("PORT", 8080))
TEST_MODE: Final[bool] = os.getenv("TESTING", False)

WARN_LIMIT: Final[int] = 3

DATABASE_URL: Final[str] = os.getenv("DATABASE_URL")  # .replace("postgres", "postgresql", 1)
CHANNEL_MEME: Final[int] = int(os.getenv('CHANNEL_MEME'))
CHANNEL_SOURCE: Final[int] = int(os.getenv('CHANNEL_SOURCE'))
LOG_GROUP: Final[str] = os.getenv('LOG_GROUP')
ADMINS: Final = loads(os.getenv('ADMINS'))

ALLOWED_URLS: Final[Set[str]] = {
    "t.me/militaernews",
    "bbc.com",
    "bbc.co.uk",
    "nytimes.com",
    "cnn.com",
    "theguardian.com",
    "nypost.com",
    "forbes.com",
    "washingtonpost.com",
    "cnbc.com",
    "independent.co.uk",
    "businessinsider.com",
    "kremlin.ru",
    "un.org",
    "icrc.org",
    "whitehouse.gov",
    "ntv.de",
    "n-tv.de",
    "nzz.ch",
    "faz.net",
    "maps.app.goo.gl",
    "understandingwar.org",
    "wikipedia.org",
    "youtube.com",
    "youtu.be",
    "spiegel.de",
    "maps.google.com",
    "wsj.com",
    "reuters.com",
    "bloomberg.com",
    "dw.com",
    "zeit.de"
    "apnews.com",
    "tagesschau.de"
}

RULES: Final[List[str]] =  [
    "1️⃣ Keine Beleidigung anderer Mitglieder.",
    "2️⃣ Kein Spam (mehr als drei einzelne Nachrichten oder Alben hintereinander weitergeleitet).",
    "3️⃣ Keine pornografischen Inhalte.",
    "4️⃣ Keine Aufnahmen von Leichen oder Schwerverletzen.",
    "5️⃣ Keine privaten Inhalte anderer Personen teilen."
]
