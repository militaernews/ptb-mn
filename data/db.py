import logging
import sys
from contextlib import asynccontextmanager

from functools import wraps
from inspect import currentframe
from os import getenv
from ssl import Purpose, CERT_NONE, create_default_context
from traceback import format_exc
from typing import List
from typing import Optional, Callable, Awaitable

from asyncpg import Pool
from asyncpg import create_pool, Connection
from telegram import Message

from config import DATABASE_URL, DATABASE_URL_NN
from data.lang import GERMAN
from data.model import Post, ANIMATION, VIDEO, PHOTO



def get_ssl():
    sslctx = create_default_context( Purpose.SERVER_AUTH)
    sslctx.check_hostname = False
    sslctx.verify_mode = CERT_NONE
    return sslctx


class DBPool:
    _pool: Optional[Pool] = None
    _test_mode: bool = False

    @classmethod
    def is_running_tests(cls) -> bool:
        """Check if code is running in a test environment."""
        if cls._test_mode:  # Allow manual override
            return True
        return (
                'pytest' in sys.modules or
                'unittest' in sys.modules or
                getenv('TESTING') == 'true'
        )

    @classmethod
    async def get_pool(cls) -> Optional[Pool]:
        """Get or create connection pool."""
        if cls.is_running_tests():
            return None

        if cls._pool is None:
            cls._pool = await create_pool(
              DATABASE_URL
            )
        return cls._pool

    @staticmethod
    async def _setup_connection(conn: Connection) -> None:
        """Optional: Set up connection defaults, prepare statements."""
        # Example: Set statement timeout
        await conn.execute('SET statement_timeout = 30000')  # 30 seconds

        # Example: Prepare commonly used statements
      #  await conn.prepare(
        #    'get_user',
         #   'SELECT * FROM users WHERE id = $1'
      #  )

    @classmethod
    async def close_pool(cls) -> None:
        """Close the connection pool."""
        if cls._pool is not None:
            await cls._pool.close()
            cls._pool = None

    @classmethod
    @asynccontextmanager
    async def get_connection(cls):
        """Get a connection from the pool."""
        if cls.is_running_tests():
            yield None
            return

        pool = await cls.get_pool()
        async with pool.acquire() as connection:
            yield connection


def db(func: Callable[..., Awaitable]):
    """
    Decorator that provides a database connection from pool to the wrapped function.
    Skips actual database connection in test environment.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        async with DBPool.get_connection() as conn:
            if DBPool.is_running_tests:
                return await func( *args, **kwargs)
            else:
                return await func(conn, *args, **kwargs)

    return wrapper



@db
async def get_mg(mg_id: str, conn: Connection):
    res = await conn.fetch("select * from posts p where p.media_group_id = $1 and p.lang='de'", mg_id)
    logging.info(f">>> get_mg: {res}")
    print(f"res: {res}")
    return res


@db
async def query_files(meg_id, conn: Connection) -> List[Post]:
    res = await conn.fetchval("select * from posts p where p.media_group_id = %s and p.lang='de'", [meg_id])
    logging.info(f">>> query_files: {res}")
    return res


@db
async def query_replies(msg_id: int, lang_key: str, conn: Connection) -> int:
    res = await conn.fetchrow("select p.reply_id from posts p where p.msg_id = %s and p.lang=%s",
                              (msg_id, lang_key))
    logging.info(f">>> query_replies: {res}")
    return res


@db
async def query_replies2(post_id: int, lang_key: str, conn: Connection):
    res = await conn.fetchrow("select p.reply_id from posts p where p.post_id = %s and p.lang=%s",
                    (post_id, lang_key))

    logging.info(f">>> query_replies2: {res}")
    return res


@db
async def get_post_id(msg: Message, conn: Connection):
    if msg.reply_to_message is None:
        return

    await c.execute("select p.post_id from posts p where p.msg_id = %s and p.lang='de'",
                    [msg.reply_to_message.id, ])
    res = await c.fetchone()

    logging.info(f">>> get_post_id: {res}")
    return res[0] if res is not None else res


async def get_post_id2(msg_id: int, conn: Connection):
    await c.execute("select p.post_id from posts p where p.msg_id = %s and p.lang='de'", [msg_id])
    res = await c.fetchone()

    return res[0] if res is not None else res


@db
async def query_replies3(post_id: int, lang_key: str, conn: Connection):
    res = await conn.fetchrow("select p.reply_id from posts p where p.post_id = %s and p.lang=%s",
                              (post_id, lang_key))

    logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> {res}")
    return res[0] if res is not None else res


@db
async def query_replies4(msg: Message, lang_key: str, conn: Connection):
    if msg.reply_to_message is None:
        return

    await c.execute(
        "select p.msg_id from posts p where p.lang=%s and p.post_id = (select pp.post_id from posts pp where pp.msg_id = %s and pp.lang='de')",
        (lang_key, msg.reply_to_message.id))
    res = await c.fetchone()

    logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> {res}")
    return res[0] if res is not None else res


@db
async def get_msg_id(msg_id: int, lang_key: str, conn: Connection):
    await c.execute(
        "select p.msg_id from posts p where p.lang=%s and p.post_id = (select pp.post_id from posts pp where pp.msg_id = %s and pp.lang='de')",
        (lang_key, msg_id))
    res = await c.fetchone()

    logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> {res}")
    return res[0] if res is not None else res


@db
async def get_file_id(msg_id: int, conn: Connection):
    await c.execute("select p.file_id from posts p where p.msg_id=%s", [msg_id])
    res = await c.fetchone()

    logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> {res}")
    return res[0] if res is not None else res


@db
async def update_text(msg_id: int, text: str, conn: Connection, lang_key: str = GERMAN.lang_key):
    await c.execute("update posts p set text = %s where p.msg_id=%s and p.lang=%s",
                    (text, msg_id, lang_key))
    res = await c.fetchone()

    logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> {res}", )
    return res[0] if res is not None else res


@db
async def update_post(msg: Message, conn: Connection, lang_key: str = GERMAN.lang_key):
    if len(msg.photo) != 0:
        file_type = PHOTO
        file_id = msg.photo[-1].file_id
    elif msg.video is not None:
        file_type = VIDEO
        file_id = msg.video.file_id
    elif msg.animation is not None:
        file_type = ANIMATION
        file_id = msg.animation.file_id
    else:
        file_type = None
        file_id = None

    if msg.caption is not None:
        text = msg.caption_html_urled
    elif msg.text is not None:
        text = msg.text_html_urled
    else:
        text = None

    await c.execute(
        "update posts p set file_id = %s, text = %s, file_type = %s where p.msg_id=%s and p.lang=%s",
        (file_id, text, file_type, msg.id, lang_key))


@db
async def insert_single3(msg_id: int, reply_id: int, msg: Message, conn: Connection, meg_id: str = None,
                         lang_key: str = GERMAN.lang_key,
                         post_id: int = None):  # text=??
    if len(msg.photo) != 0:
        file_type = PHOTO
        file_id = msg.photo[-1].file_id
    elif msg.video is not None:
        file_type = VIDEO
        file_id = msg.video.file_id
    elif msg.animation is not None:
        file_type = ANIMATION
        file_id = msg.animation.file_id
    else:
        file_type = None
        file_id = None
    await insert_single(msg_id, meg_id, reply_id, file_type, file_id, lang_key, post_id, msg.has_media_spoiler or False)


@db
async def insert_single2(msg: Message, conn: Connection, lang_key: str = GERMAN.lang_key):
    if len(msg.photo) != 0:
        file_type = PHOTO
        file_id = msg.photo[-1].file_id
    elif msg.video is not None:
        file_type = VIDEO
        file_id = msg.video.file_id
    elif msg.animation is not None:
        file_type = ANIMATION
        file_id = msg.animation.file_id
    else:
        file_type = None
        file_id = None

    reply_id = None if msg.reply_to_message is None else msg.reply_to_message.id

    if msg.caption is not None:
        text = msg.caption_html_urled
    elif msg.text is not None:
        text = msg.text_html_urled
    else:
        text = None

    # add text aswell?
    return await insert_single(msg.id, conn, msg.media_group_id, reply_id, file_type, file_id, lang_key, text=text,
                               spoiler=msg.has_media_spoiler or False)


@db
async def insert_single(msg_id: int, conn: Connection, meg_id: str = None, reply_id: int = None, file_type: int = None,
                        file_id: str = None, lang_key: str = GERMAN.lang_key, post_id: int = None, text: str = None,
                        spoiler: bool = False):
    if post_id is None:
        await c.execute("select max(p.post_id) from posts p")
        post_id = int((await c.fetchone())[0] or 0) + 1

    insertable = (post_id, msg_id, meg_id, reply_id, file_type, file_id, lang_key, text, spoiler)
    logging.info(f">> Insert: {insertable}", )

    await c.execute(
        "insert into posts(post_id, msg_id, media_group_id, reply_id, file_type, file_id,lang,text,spoiler) values (%s,%s,%s,%s,%s,%s,%s,%s,%s) returning post_id",
        insertable)
    res = (await c.fetchone()).post_id

    logging.info(f">> Result: post_id = {res}", )
    return res


@db
async def insert_promo(user_id: int, lang: str, promo_id: int, conn: Connection):
    insertable = (user_id, lang, promo_id)
    logging.info(f">> Insert: {insertable}", )

    res = await conn.fetchrow("select * from promos p where p.user_id=%s;", [user_id])

    logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> {res}")
    if res is not None:
        return None

    await conn.execute("insert into promos(user_id, lang, promo_id) values (%s,%s,%s) returning user_id;",
                       insertable)
    res = (await conn.fetchone()).user_id

    logging.info(f">> Result: user_id = {res}", )
    return res


async def get_suggested_sources() -> List[int]:
    pool_nn = await create_pool(DATABASE_URL_NN,ssl= get_ssl())
    async with pool_nn.acquire() as conn:
        res = await conn.fetch("select s.channel_id from sources s where s.is_spread=false;")

    channel_ids = [record["channel_id"] for record in res]
    print(f"SUGGESTED SOURCES: {channel_ids}")
    return channel_ids
