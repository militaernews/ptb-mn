"""Database file."""

from collections import defaultdict
from logging import getLogger
from typing import Dict, Any, Callable

import ujson as json
from sqlalchemy.orm import scoped_session
from sqlalchemy.sql import text
from telegram.ext import DictPersistence
from telegram.utils.helpers import (
    encode_conversations_to_json,
    decode_conversations_from_json,
)


class PostgresPersistence(DictPersistence):
    """Class for database persistence."""

    def __init__(
            self,
            session: scoped_session,
            store_user_data: bool = True,
            store_chat_data: bool = True,
            store_bot_data: bool = True,
    ) -> None:
        """Make a new persistence."""
        super().__init__(
            store_user_data=store_user_data,
            store_chat_data=store_chat_data,
            store_bot_data=store_bot_data,
        )

        self.logger = getLogger(__name__)
        if not isinstance(session, scoped_session):
            raise TypeError("session must be `sqlalchemy.orm.scoped_session` object")

        self._session = session
        self.__init_database()
        self.__load_database()

    def __init_database(self) -> None:
        create_table_qry = """
            CREATE TABLE IF NOT EXISTS persistence(
            data json NOT NULL);"""
        self._session.execute(text(create_table_qry))
        self._session.commit()

    def __load_database(self) -> None:
        try:
            data_ = self._session.execute(text("SELECT data FROM persistence")).first()
            data = data_[0] if data_ is not None else {}

            self.logger.info("Loading database \n%s", data)
            self._chat_data = defaultdict(
                dict, self._key_mapper(data.get("chat_data", {}), int)
            )
            self._user_data = defaultdict(
                dict, self._key_mapper(data.get("user_data", {}), int)
            )
            self._bot_data = data.get("bot_data", {})
            self._conversations = decode_conversations_from_json(
                data.get("conversations", "{}")
            )
            self.logger.info("Database loaded successfully!")
        finally:
            self._session.close()

    @staticmethod
    def _key_mapper(iterable: Dict, func: Callable) -> Dict:
        return {func(k): v for k, v in iterable.items()}

    def _dump_into_json(self) -> Any:
        to_dump = {
            "chat_data": self._chat_data,
            "user_data": self._user_data,
            "bot_data": self.bot_data,
            "conversations": encode_conversations_to_json(self._conversations),
        }
        self.logger.info("Dumping %s", to_dump)
        return json.dumps(to_dump)

    def flush(self) -> None:
        """Flush database."""
        self.logger.info("Saving user/chat/bot data before shutdown")
        try:
            self._session.execute("DELETE FROM persistence")
            insert_qry = "INSERT INTO persistence (data) VALUES (:jsondata)"
            params = {"jsondata": self._dump_into_json()}
            self._session.execute(text(insert_qry), params)
            self._session.commit()
        except Exception as excp:  # pylint: disable=W0703
            self._session.close()
            self.logger.error(
                "Failed to save user/chat/bot data before shutdown...\nLogging exception:",
                exc_info=excp,
            )
        else:
            self.logger.info("SUCCESS! saved user/chat/bot data into database.")

        self.logger.info("Closing database...")
