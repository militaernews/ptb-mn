from replit import db


def key_exists(key: int) -> bool:
    return key in db.keys()


def create_user(user_id: int):
    db[user_id] = {"warnings": 0}
