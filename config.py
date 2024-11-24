import os
from json import loads
from typing import Final, List

from dotenv import load_dotenv

load_dotenv()

TOKEN: Final[str] = os.getenv('TELEGRAM')
PORT: Final[int] = int(os.getenv("PORT", 8080))
TEST_MODE: Final[bool] = os.getenv("TESTING", False)

CHANNEL_MEME: Final[int] = int(os.getenv('CHANNEL_MEME'))
CHANNEL_SOURCE: Final[int] = int(os.getenv('CHANNEL_SOURCE'))

CHANNEL_BACKUP: Final[int] = int(os.getenv('CHANNEL_BACKUP'))
CHANNEL_SUGGEST: Final[int] = int(os.getenv('CHANNEL_SUGGEST'))

LOG_GROUP: Final[str] = os.getenv('LOG_GROUP')
ADMINS: Final[List[str]] = loads(os.getenv('ADMINS'))

WARN_LIMIT: Final[int] = 3
DIVIDER: Final[str] = "\n\n"


