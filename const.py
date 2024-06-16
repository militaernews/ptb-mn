from typing import Set

PLACEHOLDER = "║"
PATTERN_COMMAND = r"^\/([^@\s]+)@?(?:(\S+)|)\s?([\s\S]*)$"

whitelist: Set[str] = {
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
    "nzz.ch",
    "faz.net",
    "maps.app.goo.gl",
    "understandingwar.org"
}
PATTERN_URL = r"\b(?!" + '|'.join(whitelist).replace('.', r'\.').replace('/', r'\/') + r")([\w-]+\.\w{2,})$\b"
