"""Every language has every text, and every text the code asks for exists."""
import re
import sys
from pathlib import Path

BOT = Path(__file__).resolve().parent.parent / "bot"
sys.path.insert(0, str(BOT))

from util.strings import STRINGS  # noqa: E402

# Quoted literals like "ad.start" whose prefix is one of the key groups, in modules that use STRINGS
PREFIXES = "|".join(sorted({key.split(".")[0] for key in STRINGS.table["en"]}))
KEY_USE = re.compile(rf"""["']((?:{PREFIXES})\.\w+)["']""")


def test_languages():
    assert set(STRINGS.languages) == {"de", "en"}


def test_no_missing_or_unknown_keys():
    assert STRINGS.missing() == {"de": []}
    assert STRINGS.unknown() == {"de": []}


def test_every_used_key_exists():
    sources = [path.read_text(encoding="utf-8") for path in BOT.rglob("*.py")]
    used = {key for source in sources if "STRINGS" in source for key in KEY_USE.findall(source)}
    assert used, "the scan found no keys at all"
    assert sorted(key for key in used if not STRINGS.has(key)) == []


def test_admin_command_descriptions_exist():
    source = (BOT / "private" / "setup.py").read_text(encoding="utf-8")
    names = re.search(r"ADMIN_COMMANDS = \(([^)]*)\)", source).group(1)
    for name in re.findall(r'"(\w+)"', names):
        assert STRINGS.has(f"command.{name}")


def test_placeholders_match():
    fields = re.compile(r"{(\w+)}")
    for key, text in STRINGS.table["en"].items():
        assert set(fields.findall(STRINGS.table["de"][key])) == set(fields.findall(text)), key
