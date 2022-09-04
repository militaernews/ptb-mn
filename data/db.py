import psycopg2
from telegram import Message
from telegram.ext import CallbackContext

from config import DATABASE_URL
from data.lang import GERMAN

conn = psycopg2.connect(DATABASE_URL)


def key_exists(context: CallbackContext, key: int) -> bool:
    return key in context.bot_data().keys()


def create_user(context: CallbackContext, user_id: int):
    context.bot_data[user_id] = {"warnings": 0}


def get_mg(mg_id: str):
    with conn.cursor() as c:
        c.execute("select * from posts")
        res = c.fetchone()

        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ", res)


PHOTO, VIDEO, ANIMATION = range(3)


def query_replies(msg_id: int,lang_key:str):
    with conn.cursor() as c:
        c.execute("select p.reply_id from posts p where p.msg_id = %s and p.lang=%s", (msg_id,lang_key))
        res = c.fetchone()

        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ", res)
        return res

def query_replies2(post_id: int,lang_key:str):
    with conn.cursor() as c:
        c.execute("select p.reply_id from posts p where p.post_id = %s and p.lang=%s", (post_id,lang_key))
        res = c.fetchone()[0]

        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ", res)
        return res


def insert_single3(post_id=int, msg_id: int, reply_id: int, msg: Message, meg_id: str = None, lang_key: str = GERMAN.lang_key):
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
    insert_single(post_id, msg_id, meg_id, reply_id, file_type, file_id, lang_key)


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

    # add text aswell?
    return insert_single(msg.id, msg.media_group_id, reply_id, file_type, file_id, lang_key)


def insert_single( msg_id: int, meg_id: str = None, reply_id: int = None, file_type: int = None, file_id: str = None,
                  lang_key: str = GERMAN.lang_key):
    insertable = (msg_id, meg_id, reply_id, file_type, file_id, lang_key)
    print(">> Insert: ", insertable)

    with conn.cursor() as c:
        c.execute(
            "insert into posts(msg_id, media_group_id, reply_id, file_type, file_id,lang) values (%s,%s,%s,%s,%s,%s) returning post_id",
            insertable)
        res = c.fetchone()[0]
        conn.commit()

        print(">> Result: post_id =",res)
        return res

