import re

NUMBER_RULE = (
    "Große Zahlen kürzt du ab (Mio. statt Million/Millionen, Mrd. statt Milliarde/Milliarden), "
    "Währungen schreibst du als ISO-Code hinter der Zahl, z.B. „5 Mio. USD“ statt „5 Millionen US-Dollar“, "
    "„2,3 Mrd. EUR“ statt „2,3 Milliarden Euro“."
)

_NUMBER_SCALES = {
    "Mio.": r"Millionen|Million|Mio",
    "Mrd.": r"Milliarden|Milliarde|Mrd",
    "Bio.": r"Billionen|Billion|Bio",
}
_CURRENCIES = {
    "USD": r"US-Dollars?|Dollars?",
    "EUR": r"Euros?",
    "RUB": r"Rubel",
    "UAH": r"Hrywnjas?|Hrywnja|Hrywen",
}
# A trailing "." is consumed so "5 Millionen." becomes "5 Mio." rather than "5 Mio..".
_SCALE_RES = [(abbr, re.compile(rf"(\d\s*)(?:{words})\b\.?")) for abbr, words in _NUMBER_SCALES.items()]
_CURRENCY_RES = [
    (code, re.compile(rf"(\d\s*|(?:Mio|Mrd|Bio)\.\s*)(?:{words})\b(?!-)")) for code, words in _CURRENCIES.items()
]


def abbreviate_amounts(text: str) -> str:
    """'5 Millionen US-Dollar' -> '5 Mio. USD'; only touches words right after a number."""
    for abbr, pattern in _SCALE_RES:
        text = pattern.sub(rf"\g<1>{abbr}", text)
    for code, pattern in _CURRENCY_RES:
        text = pattern.sub(rf"\g<1>{code}", text)
    return text
