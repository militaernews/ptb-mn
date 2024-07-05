#import regex as re
import re
from typing import Final

WHITESPACE = re.compile(r'[\s\n]+$')
HASHTAG = re.compile(r'#\S+')
FLAG_EMOJI = re.compile(r'🏴|🏳️|([🇦-🇿]{2})')
BREAKING = re.compile(r'#eilmeldung[\r\n\s]*', re.IGNORECASE)
PATTERN_HTMLTAG = re.compile(r'<[^a>]+>')

PLACEHOLDER: Final[str] = "║"
PATTERN_COMMAND: Final[str] = r"^\/([^@\s]+)@?(?:(\S+)|)\s?([\s\S]*)$"
