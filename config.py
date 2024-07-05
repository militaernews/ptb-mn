import os
from json import loads
from typing import Final, List, Set

from dotenv import load_dotenv

load_dotenv()

TOKEN: Final[str] = os.getenv('TELEGRAM')
PORT: Final[int] = int(os.getenv("PORT", 8080))
TEST_MODE: Final[bool] = os.getenv("TESTING", False)

WARN_LIMIT: Final[int] = 3

CHANNEL_MEME: Final[int] = int(os.getenv('CHANNEL_MEME'))
CHANNEL_SOURCE: Final[int] = int(os.getenv('CHANNEL_SOURCE'))

CHANNEL_BACKUP: Final[int] = int(os.getenv('CHANNEL_BACKUP'))
CHANNEL_SUGGEST: Final[int] = int(os.getenv('CHANNEL_SUGGEST'))

LOG_GROUP: Final[str] = os.getenv('LOG_GROUP')
ADMINS: Final = loads(os.getenv('ADMINS'))


