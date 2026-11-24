"""User-facing texts of the private-chat features, from res/strings/<lang>.json."""
from pathlib import Path
from typing import Final

from ptbkit import Strings

STRINGS: Final[Strings] = Strings(Path(__file__).resolve().parent.parent / "res" / "strings")
