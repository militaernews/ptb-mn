import logging
import sys
from contextlib import asynccontextmanager
from functools import wraps
from os import getenv
from ssl import Purpose, CERT_NONE, create_default_context
from typing import List
from typing import Optional, Callable, Awaitable

from asyncpg import Pool
from asyncpg import create_pool, Connection
from telegram import Message

from lang import GERMAN
from model import Post, ANIMATION, VIDEO, PHOTO
from ..settings.config import DATABASE_URL_NN, DATABASE_URL


def get_ssl():
    ssl_ctx = create_default_context(Purpose.SERVER_AUTH)
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = CERT_NONE
    return ssl_ctx


class DBPool:
    _pool: Optional[Pool] = None

    @classmethod
    def is_test(cls) -> bool:
        return 'pytest' in sys.modules or getenv('TESTING') == 'true'

    @classmethod
    async def get_pool(cls) -> Optional[Pool]:
        if cls.is_test():
            return None
        if cls._pool is None:
            cls._pool = await create_pool(DATABASE_URL)
        return cls._pool

    @classmethod
    @asynccontextmanager
    async def connection(cls):
        if cls.is_test():
            yield None
            return

        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            yield conn


def db(func: Callable[..., Awaitable]):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        async with DBPool.connection() as conn:
            if DBPool.is_test():
                return await func(*args, **kwargs)
            kwargs["conn"] = conn
            return await func(*args, **kwargs)

    return wrapper


@db
async def get_mg(meg_id: str, conn: Connection = None):
    res = await conn.fetchrow("select * from posts p where p.media_group_id=$1 and p.lang='de'", meg_id)
    logging.info(f">>> get_mg: {res}")
    return res


@db
async def query_files(meg_id: str, conn: Connection) -> List[Post]:
    rows = await conn.fetch("select * from posts p where p.media_group_id=$1 and p.lang='de'", meg_id)
    logging.info(f">>> query_files: {rows}")
    return [Post(**row) for row in rows]


@db
async def query_replies(msg_id: int, lang_key: str, conn: Connection) -> int:
    res = await conn.fetchrow("select p.reply_id from posts p where p.msg_id=$1 and p.lang=$2",
                              msg_id, lang_key)
    logging.info(f">>> query_replies: {res}")
    return res


@db
async def query_replies2(post_id: int, lang_key: str, conn: Connection = None):
    res = await conn.fetchrow("select p.reply_id from posts p where p.post_id=$1 and p.lang=$2",
                              post_id, lang_key)

    logging.info(f">>> query_replies2: {res}")
    return res


@db
async def get_post_id(msg: Message, conn: Connection = None):
    if msg.reply_to_message is None:
        return

    res = await conn.fetchrow("select p.post_id from posts p where p.msg_id=$1 and p.lang='de'",
                              msg.reply_to_message.id)

    logging.info(f">>> get_post_id: {res}")
    return res[0] if res is not None else res


@db
async def get_post_id2(msg_id: int, conn: Connection = None):
    res = await conn.fetchrow("select p.post_id from posts p where p.msg_id=$1 and p.lang='de'", msg_id)

    return res[0] if res is not None else res


@db
async def query_replies3(post_id: int, lang_key: str, conn: Connection = None):
    res = await conn.fetchrow("select p.reply_id from posts p where p.post_id=$1 and p.lang=$2",
                              post_id, lang_key)

    logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> {res}")
    return res[0] if res is not None else res


@db
async def query_replies4(msg: Message, lang_key: str, conn: Connection = None):
    if msg.reply_to_message is None:
        return

    res = await conn.fetchrow(
        "select p.msg_id from posts p where p.lang=$1 and p.post_id = (select pp.post_id from posts pp where pp.msg_id = $2 and pp.lang='de')",
        lang_key, msg.reply_to_message.id)

    logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> {res}")
    return res[0] if res is not None else res


@db
async def get_msg_id(msg_id: int, lang_key: str, conn: Connection = None):
    res = await conn.fetchrow(
        "select p.msg_id from posts p where p.lang=$1 and p.post_id = (select pp.post_id from posts pp where pp.msg_id = $2 and pp.lang='de')",
        lang_key, msg_id)

    logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> {res}")
    return res[0] if res is not None else res


@db
async def get_file_id(msg_id: int, conn: Connection = None):
    res = await conn.fetchrow("select p.file_id from posts p where p.msg_id=$1", msg_id)

    logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> {res}")
    return res[0] if res is not None else res


@db
async def update_text(msg_id: int, text: str, lang_key: str = GERMAN.lang_key, conn: Connection = None):
    await conn.execute("update posts p set text=$1 where p.msg_id=$2 and p.lang=$3",
                       text, msg_id, lang_key)


@db
async def update_post(msg: Message, lang_key: str = GERMAN.lang_key, conn: Connection = None):
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

    await conn.execute(
        "update posts p set file_id=$1, text=$2, file_type=$3 where p.msg_id=$4 and p.lang=$5",
        file_id, text, file_type, msg.id, lang_key)


@db
async def insert_single3(msg_id: int, reply_id: int, msg: Message, meg_id: str = None,
                         lang_key: str = GERMAN.lang_key,
                         post_id: int = None, conn: Connection = None):  # text=??
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
    await insert_single(msg_id=msg_id, meg_id=meg_id, reply_id=reply_id, file_type=file_type, file_id=file_id,
                        lang_key=lang_key, post_id=post_id,
                        spoiler=msg.has_media_spoiler or False
                        )


@db
async def insert_single2(msg: Message, lang_key: str = GERMAN.lang_key, conn: Connection = None):
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
    return await insert_single(msg_id=msg.id, meg_id=msg.media_group_id, reply_id=reply_id, file_type=file_type,
                               file_id=file_id, lang_key=lang_key, text=text,
                               spoiler=msg.has_media_spoiler or False)


@db
async def insert_single(msg_id: int, meg_id: str = None, reply_id: int = None, file_type: int = None,
                        file_id: str = None, lang_key: str = GERMAN.lang_key, post_id: int = None, text: str = None,
                        spoiler: bool = False, conn: Connection = None):
    if post_id is None:
        post_id = int(await conn.fetchval("select max(p.post_id) from posts p") or 0) + 1

    res = await conn.fetchval(
        "insert into posts(post_id, msg_id, media_group_id, reply_id, file_type, file_id,lang,text,spoiler) values ($1,$2,$3,$4,$5,$6,$7,$8,$9) returning post_id",
        post_id, msg_id, meg_id, reply_id, file_type, file_id, lang_key, text, spoiler)

    logging.info(f">> Result: post_id = {res}", )
    return res


@db
async def insert_promo(user_id: int, lang: str, promo_id: int, conn: Connection):
    res = await conn.fetchrow("select * from promos p where p.user_id=$1;", user_id)

    logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> insert_promo: {res}")
    if res is not None:
        return None

    res = await conn.fetchrow("insert into promos(user_id, lang, promo_id) values ($1,$2,$3) returning user_id;",
                              user_id, lang, promo_id)

    logging.info(f">> Result: user_id = {res}")
    return res["user_id"]


async def get_suggested_sources() -> List[int]:
    pool_nn = await create_pool(DATABASE_URL_NN, ssl=get_ssl())
    async with pool_nn.acquire() as conn:
        res = await conn.fetch("select s.channel_id from sources s where s.is_spread=false;")

    channel_ids = [record["channel_id"] for record in res]
    print(f"SUGGESTED SOURCES: {channel_ids}")
    return channel_ids
