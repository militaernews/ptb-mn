import re

WHITESPACE = re.compile(r"[\s\n]+$")
HASHTAG = re.compile(r"#\w+")
FOOTER = re.compile(r"\n*🔰\s*Abonnieren Sie @MilitaerNews\n🔰\s*Tritt uns bei @MNChat", re.IGNORECASE)
FLAG_EMOJI = re.compile(r"🏴|🏳️|([🇦-🇿]{2})")
BREAKING = re.compile(r"#eilmeldung[\r\n]*", re.IGNORECASE)
