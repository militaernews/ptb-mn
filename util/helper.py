import re

from util.regex import FOOTER


def get_replies(bot_data, msg_id: str):
    print("Trying to get bot_data ------------------")
    print(bot_data)
    print("-------------------------")

    if "reply" in bot_data[msg_id]:
        print(bot_data[bot_data[msg_id]["reply"]])
        return bot_data[bot_data[msg_id]["reply"]]["langs"]

    return None


def sanitize_text(text: str = None) -> str:
    if text is None:
        return ""

    return re.sub(FOOTER, "", text)


def sanitize_hashtag(text: str) -> str:
    return text.replace(' ', '_').replace('-', '').replace('.', '').replace("'", "")
