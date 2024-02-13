import os
from typing import Final

from dotenv import load_dotenv

load_dotenv()

vipsbin = os.getenv(r"VIPSLIB")
add_dll_dir = getattr(os, 'add_dll_directory', None)
if callable(add_dll_dir):
    add_dll_dir(vipsbin)
else:
    os.environ['PATH'] = os.pathsep.join((vipsbin, os.environ['PATH']))

TOKEN: Final[str] = os.getenv('TELEGRAM')
PORT = int(os.getenv("PORT", 8080))
TEST_MODE: Final[bool] = os.getenv("TESTING", False)

DATABASE_URL: Final[str] = os.getenv("DATABASE_URL")  # .replace("postgres", "postgresql", 1)
DATABASE_URL_NN: Final[str] = os.getenv("DATABASE_URL_NN")

CHANNEL_MEME = -1001486678205
CHANNEL_SOURCE = -1001372304339

LOG_GROUP = -1001739784948

NYX = 703453307
ADMINS = (
    NYX,
    525147382,  # Melik
    466451473,  # Maxe
    5945157782  # MN-Kontakt
)

BINGO_ADMINS = ADMINS + (
    1869587716,  # TheObserver
    298169115  # Michael Kohl
)

# Constants
PLACEHOLDER = "║"
