from dataclasses import dataclass

PHOTO, VIDEO, ANIMATION = range(3)


@dataclass
class Post:
    post_id: int
    lang: str
    msg_id: int
    reply_id: int
    file_type: int
    file_id: str
    text: str
    media_group_id: str = None
    spoiler: bool = False
