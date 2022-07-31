import re

WHITESPACE = re.compile(r"[\s\n]+$")
HASHTAG = re.compile(r"#\w+", re.IGNORECASE)
FOOTER = re.compile(r"\n*🔰\s*Abonnieren Sie @MilitaerNews\n🔰\s*Tritt uns bei @MNChat", re.IGNORECASE)
