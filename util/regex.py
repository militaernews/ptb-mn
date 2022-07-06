import re

WHITESPACE = re.compile(r"[\s\n]+$")
HASHTAG = re.compile(r"#\w+", re.IGNORECASE)
