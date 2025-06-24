# import regex as re
import re
from typing import Final

WHITESPACE = re.compile(r'[\s\n]+$')
HASHTAG = re.compile(r'#\S+')
FLAG_EMOJI = re.compile(r'🏴|🏳️|([🇦-🇿]{2})')
BREAKING = re.compile(r'#eilmeldung[\r\n\s]*', re.IGNORECASE)
PATTERN_HTMLTAG = re.compile(r'<[^a>]+>')
FLAG_EMOJI_HTMLTAG = re.compile(
    f"{FLAG_EMOJI.pattern}|{PATTERN_HTMLTAG.pattern}", re.IGNORECASE
)

QUOT_PATTERN = re.compile(r'[^\S\n\r]?& quot;[^\S\n\r]{2,}',re.IGNORECASE)
AMP_PATTERN = re.compile(r'[^\S\n\r]?& amp;[^\S\n\r]{2,}',re.IGNORECASE)

PLACEHOLDER: Final[str] = "║"
PATTERN_COMMAND: Final[str] = r"^\/([^@\s]+)@?(?:(\S+)|)\s?([\s\S]*)$"

INFO_PATTERN = re.compile(r"#info", re.IGNORECASE)
BREAKING_PATTERN = re.compile(r"#eilmeldung", re.IGNORECASE)
ANNOUNCEMENT_PATTERN = re.compile(r"#mitteilung", re.IGNORECASE)
ADVERTISEMENT_PATTERN = re.compile(r"#werbung", re.IGNORECASE)
