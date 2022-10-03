import logging
from dataclasses import dataclass

import psycopg2
from psycopg2.extras import NamedTupleCursor
from telegram import Message
from telegram.ext import CallbackContext

from config import DATABASE_URL
from data.lang import GERMAN

logger = logging.getLogger(__name__)
conn = psycopg2.connect(DATABASE_URL, cursor_factory=NamedTupleCursor)


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


def get_mg(mg_id: str):
    with conn.cursor() as c:
        c.execute("select * from posts")
        res = c.fetchone()

        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ", res)


PHOTO, VIDEO, ANIMATION = range(3)


def query_files(meg_id: str):
    try:
        with conn.cursor() as c:
            c.execute("select * from posts p where p.media_group_id = %s and p.lang='de'", [meg_id])
            res = c.fetchall()

            print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ", res)

            return res
    except Exception as e:
        logger.error("DB-Operation failed", e)
        pass


def query_replies(msg_id: int, lang_key: str):
    try:
        with conn.cursor() as c:
            c.execute("select p.reply_id from posts p where p.msg_id = %s and p.lang=%s", (msg_id, lang_key))
            res = c.fetchone()

            print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ", res)
            return res
    except Exception as e:
        logger.error("DB-Operation failed", e)
        pass


def query_replies2(post_id: int, lang_key: str):
    try:
        with conn.cursor() as c:
            c.execute("select p.reply_id from posts p where p.post_id = %s and p.lang=%s", (post_id, lang_key))
            res = c.fetchone()

            print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ", res)
            if res is not None:
                return res[0]
            else:
                return res
    except Exception as e:
        logger.error("DB-Operation failed", e)
        pass


def get_post_id(msg: Message):
    if msg.reply_to_message is None:
        return
    try:
        with conn.cursor() as c:
            c.execute("select p.post_id from posts p where p.msg_id = %s and p.lang='de'", [msg.reply_to_message.id])
            res = c.fetchone()

            if res is not None:
                return res[0]
            else:
                return res
    except Exception as e:
        logger.error("DB-Operation failed", e)
        pass


def get_post_id2(msg_id: int):
    try:
        with conn.cursor() as c:
            c.execute("select p.post_id from posts p where p.msg_id = %s and p.lang='de'", [msg_id])
            res = c.fetchone()

            if res is not None:
                return res[0]
            else:
                return res
    except Exception as e:
        logger.error("DB-Operation failed", e)
        pass


def query_replies3(post_id: int, lang_key: str):
    try:
        with conn.cursor() as c:

            c.execute("select p.msg_id from posts p where p.post_id = %s and p.lang=%s", (post_id, lang_key))
            res = c.fetchone()

            print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ", res)
            if res is not None:
                return res[0]
            else:
                return res
    except Exception as e:
        logger.error("DB-Operation failed", e)
        pass


def query_replies4(msg: Message, lang_key: str):
    if msg.reply_to_message is None:
        return
    try:
        with conn.cursor() as c:

            c.execute(
                "select p.msg_id from posts p where p.lang=%s and p.post_id = (select pp.post_id from posts pp where pp.msg_id = %s and pp.lang='de')",
                (lang_key, msg.reply_to_message.id))
            res = c.fetchone()

            print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ", res)
            if res is not None:
                return res[0]
            else:
                return res
    except Exception as e:
        logger.error("DB-Operation failed", e)
        pass


def get_msg_id(msg_id: int, lang_key: str):
    try:
        with conn.cursor() as c:

            c.execute(
                "select p.msg_id from posts p where p.lang=%s and p.post_id = (select pp.post_id from posts pp where pp.msg_id = %s and pp.lang='de')",
                (lang_key, msg_id))
            res = c.fetchone()

            print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ", res)
            if res is not None:
                return res[0]
            else:
                return res
    except Exception as e:
        logger.error("DB-Operation failed", e)
        pass


def get_file_id(msg_id: int):
    try:
        with conn.cursor() as c:

            c.execute(
                "select p.file_id from posts p where p.msg_id=%s",
                [msg_id])
            res = c.fetchone()

            print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ", res)
            if res is not None:
                return res[0]
            else:
                return res
    except Exception as e:
        logger.error("DB-Operation failed", e)
        pass


def update_post(msg:Message, lang_key: str = GERMAN.lang_key):
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

    try:
        with conn.cursor() as c:

            c.execute(
                "update posts p set file_id = %s, text = %s, file_type = %s where p.msg_id=%s and p.lang=%s",
                (file_id, text, file_type, msg.id, lang_key))
    except Exception as e:
        logger.error("DB-Operation failed", e)
        pass


def insert_single3(msg_id: int, reply_id: int, msg: Message, meg_id: str = None,
                   lang_key: str = GERMAN.lang_key, post_id: int = None):  # text=??
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
    insert_single(msg_id, meg_id, reply_id, file_type, file_id, lang_key, post_id)


def insert_single2(msg: Message, lang_key: str = GERMAN.lang_key):
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

    if msg.reply_to_message is not None:
        reply_id = msg.reply_to_message.id
    else:
        reply_id = None

    if msg.caption is not None:
        text = msg.caption_html_urled
    elif msg.text is not None:
        text = msg.text_html_urled
    else:
        text = None

    # add text aswell?
    return insert_single(msg.id, msg.media_group_id, reply_id, file_type, file_id, lang_key, text=text)


def insert_single(msg_id: int, meg_id: str = None, reply_id: int = None, file_type: int = None, file_id: str = None,
                  lang_key: str = GERMAN.lang_key, post_id: int = None, text: str = None):
    try:
        if post_id is None:
            with conn.cursor() as c:
                c.execute("select max(p.post_id) from posts p")
                post_id = int(c.fetchone()[0] or 0) + 1

        insertable = (post_id, msg_id, meg_id, reply_id, file_type, file_id, lang_key, text)
        print(">> Insert: ", insertable)

        with conn.cursor() as c:
            c.execute(
                "insert into posts(post_id, msg_id, media_group_id, reply_id, file_type, file_id,lang,text) values (%s,%s,%s,%s,%s,%s,%s,%s) returning post_id",
                insertable)
            res = c.fetchone().post_id
            conn.commit()

            print(">> Result: post_id =", res)
            return res
    except Exception as e:
        logger.error("DB-Operation failed", e)
        pass
