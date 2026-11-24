"""Unhandled errors go to the container log and to the bot's topic in the log group."""
from typing import Final

from ptbkit import ErrorReporter

from settings.config import LOG_GROUP_ID, THREAD_ID

REPORTER: Final[ErrorReporter] = ErrorReporter("PTB-MN", chat_id=LOG_GROUP_ID, thread_id=THREAD_ID or None)
