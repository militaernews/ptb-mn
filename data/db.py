import inspect
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from os import getenv
from traceback import format_exc
from typing import AsyncGenerator, Final

import aiopg
from aiopg import create_pool
from psycopg2 import OperationalError
from psycopg2.extras import NamedTupleCursor
from telegram import Message
from telegram.ext import CallbackContext

from data.lang import GERMAN

DATABASE_URL: Final[str] = getenv("DATABASE_URL")  # .replace("postgres", "postgresql", 1)
DATABASE_URL_NN: Final[str] = getenv("DATABASE_URL_NN")


def key_exists(context: CallbackContext, key: int) -> bool:
    return key in context.bot_data().keys()


def create_user(context: CallbackContext, user_id: int):
    context.bot_data[user_id] = {"warnings": 0}


@dataclass
class Post:
    post_id: int
    lang: str
    msg_id: int
    reply_id: int
    file_type: int
    file_id: str
    text: str
    spoiler: bool = False


@asynccontextmanager
async def db_cursor() -> AsyncGenerator:
    try:
        async with create_pool(DATABASE_URL) as pool:
            async with pool.acquire() as conn:
                async with conn.cursor(cursor_factory=NamedTupleCursor) as cursor:
                    yield cursor
    except OperationalError as err:
        logging.error(
            f"{inspect.currentframe().f_code.co_name} — DB-Operation failed!\npgerror: {err.pgerror} -- pgcode: {err.pgcode}\nextensions.Diagnostics: {err.diag}", )
    except Exception as e:
        logging.error(f"{inspect.currentframe().f_code.co_name} — DB-Operation failed {repr(e)} - {format_exc()}")


async def get_mg(mg_id: str):
    async with db_cursor() as c:
        await c.execute("select * from posts p where p.media_group_id = %s and p.lang='de'", [mg_id])
        res = await c.fetchone()

        logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> {res}")
        return res


PHOTO, VIDEO, ANIMATION = range(3)


async def query_files(meg_id: str) -> [Post]:
    async with db_cursor() as c:
        await c.execute("select * from posts p where p.media_group_id = %s and p.lang='de'", [meg_id])
        res = await c.fetchall()

        logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> {res}")
        return res


async def query_replies(msg_id: int, lang_key: str):
    async with db_cursor() as c:
        await c.execute("select p.reply_id from posts p where p.msg_id = %s and p.lang=%s",
                        (msg_id, lang_key))
        res = await c.fetchone()

        logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> {res}")
        return res


async def query_replies2(post_id: int, lang_key: str):
    async with db_cursor() as c:
        await c.execute("select p.reply_id from posts p where p.post_id = %s and p.lang=%s",
                        (post_id, lang_key))
        res = await c.fetchone()

        logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> {res}")
        return res[0] if res is not None else res


async def get_post_id(msg: Message):
    if msg.reply_to_message is None:
        return

    async with db_cursor() as c:
        await c.execute("select p.post_id from posts p where p.msg_id = %s and p.lang='de'",
                        [msg.reply_to_message.id, ])
        res = await c.fetchone()

        return res[0] if res is not None else res


async def get_post_id2(msg_id: int):
    async with db_cursor() as c:
        await c.execute("select p.post_id from posts p where p.msg_id = %s and p.lang='de'", [msg_id])
        res = await c.fetchone()

        return res[0] if res is not None else res


async def query_replies3(post_id: int, lang_key: str):
    async with db_cursor() as c:
        await c.execute("select p.reply_id from posts p where p.post_id = %s and p.lang=%s",
                        (post_id, lang_key))
        res = await c.fetchone()

        logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> {res}")
        return res[0] if res is not None else res


async def query_replies4(msg: Message, lang_key: str):
    if msg.reply_to_message is None:
        return
    async with db_cursor() as c:
        await c.execute(
            "select p.msg_id from posts p where p.lang=%s and p.post_id = (select pp.post_id from posts pp where pp.msg_id = %s and pp.lang='de')",
            (lang_key, msg.reply_to_message.id))
        res = await c.fetchone()

        logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> {res}")
        return res[0] if res is not None else res


async def get_msg_id(msg_id: int, lang_key: str):
    async with db_cursor() as c:
        await c.execute(
            "select p.msg_id from posts p where p.lang=%s and p.post_id = (select pp.post_id from posts pp where pp.msg_id = %s and pp.lang='de')",
            (lang_key, msg_id))
        res = await c.fetchone()

        logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> {res}")
        return res[0] if res is not None else res


async def get_file_id(msg_id: int):
    async with db_cursor() as c:
        await c.execute("select p.file_id from posts p where p.msg_id=%s", [msg_id])
        res = await c.fetchone()

        logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> {res}")
        return res[0] if res is not None else res


async def update_text(msg_id: int, text: str, lang_key: str = GERMAN.lang_key):
    async with db_cursor() as c:
        await c.execute("update posts p set text = %s where p.msg_id=%s and p.lang=%s",
                        (text, msg_id, lang_key))
        res = await c.fetchone()

        logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> {res}", )
        return res[0] if res is not None else res


async def update_post(msg: Message, lang_key: str = GERMAN.lang_key):
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

    async with db_cursor() as c:
        await c.execute(
            "update posts p set file_id = %s, text = %s, file_type = %s where p.msg_id=%s and p.lang=%s",
            (file_id, text, file_type, msg.id, lang_key))


async def insert_single3(msg_id: int, reply_id: int, msg: Message, meg_id: str = None, lang_key: str = GERMAN.lang_key,
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


async def insert_single2(msg: Message, lang_key: str = GERMAN.lang_key):
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
    return await insert_single(msg.id, msg.media_group_id, reply_id, file_type, file_id, lang_key, text=text,
                               spoiler=msg.has_media_spoiler or False)


async def insert_single(msg_id: int, meg_id: str = None, reply_id: int = None, file_type: int = None,
                        file_id: str = None, lang_key: str = GERMAN.lang_key, post_id: int = None, text: str = None,
                        spoiler: bool = False):
    if post_id is None:
        async with db_cursor() as c:
            await c.execute("select max(p.post_id) from posts p")
            post_id = int((await c.fetchone())[0] or 0) + 1

    insertable = (post_id, msg_id, meg_id, reply_id, file_type, file_id, lang_key, text, spoiler)
    logging.info(f">> Insert: {insertable}", )

    async with db_cursor() as c:
        await c.execute(
            "insert into posts(post_id, msg_id, media_group_id, reply_id, file_type, file_id,lang,text,spoiler) values (%s,%s,%s,%s,%s,%s,%s,%s,%s) returning post_id",
            insertable)
        res = (await c.fetchone()).post_id

        logging.info(f">> Result: post_id = {res}", )
        return res


async def insert_promo(user_id: int, lang: str, promo_id: int):
    insertable = (user_id, lang, promo_id)
    logging.info(f">> Insert: {insertable}", )

    async with db_cursor() as c:
        await c.execute("select * from promos p where p.user_id=%s;", [user_id])
        res = await c.fetchone()

        logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> {res}")
        if res is not None:
            return None

        await c.execute("insert into promos(user_id, lang, promo_id) values (%s,%s,%s) returning user_id;",
                        insertable)
        res = (await c.fetchone()).user_id

        logging.info(f">> Result: user_id = {res}", )
        return res


async def get_suggested_sources() -> [int]:
    async with aiopg.create_pool(DATABASE_URL_NN) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as c:
                await c.execute("select s.channel_id from sources s where s.is_spread=false;", )
                res = await c.fetchall()
                print(f"SUGGESTED SOURCES: {list(sum(res, ()))}")
                return list(sum(res, ()))
