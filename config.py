
from json import loads
from os import getenv
from typing import Final, List

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: Final[str] = getenv("DATABASE_URL")  # .replace("postgres", "postgresql", 1)
DATABASE_URL_NN: Final[str] = getenv("DATABASE_URL_NN")
DATABASE_URL_TEST: Final[str] = getenv("DATABASE_URL_TEST") 

TOKEN: Final[str] = getenv('TELEGRAM')
PORT: Final[int] = int(getenv("PORT", 8080))
TEST_MODE: Final[bool] = getenv("TESTING", False)

CHANNEL_MEME: Final[int] = int(getenv('CHANNEL_MEME'))
CHANNEL_SOURCE: Final[int] = int(getenv('CHANNEL_SOURCE'))

CHANNEL_BACKUP: Final[int] = int(getenv('CHANNEL_BACKUP'))
CHANNEL_SUGGEST: Final[int] = int(getenv('CHANNEL_SUGGEST'))

LOG_GROUP: Final[str] = getenv('LOG_GROUP')
ADMINS: Final[List[int]] = loads(getenv('ADMINS'))

WARN_LIMIT: Final[int] = 3
DIVIDER: Final[str] = "\n"


