import psycopg2
from telegram import Message
from telegram.ext import CallbackContext

conn = psycopg2.connect(
    host="ec2-34-246-227-219.eu-west-1.compute.amazonaws.com",
    database="d23c16oa17p1os",
    user="oyefmwurylwzhi",
    port="5432",
    password="e17612f3bd355908dab3ce6dfc72571cf6d92bc1c57d0e2636935dd05b157e87")


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


def insert_single(msg: Message):
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

    insertable = (msg.id, msg.media_group_id, reply_id, file_type, file_id)
    print(">> Insert: ", insertable)

    with conn.cursor() as c:
        c.execute("insert into posts(post_id, media_group_id, reply_id, file_type, file_id) values (%s,%s,%s,%s,%s)",
                  insertable)

    conn.commit()
