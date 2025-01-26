import logging
from asyncio import get_event_loop_policy
from typing import AsyncGenerator
from unittest.mock import Mock

import pytest
import pytest_asyncio
from asyncpg import Connection, connect

from config import DATABASE_URL_TEST
from data.db import insert_promo, query_replies, insert_single, query_files, get_mg, update_post

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)




@pytest_asyncio.fixture(loop_scope='function')
async def db() -> AsyncGenerator[Connection, None]:
    conn: Connection = await connect(DATABASE_URL_TEST)

    await conn.execute('DROP TABLE IF EXISTS posts CASCADE')
    await conn.execute('DROP TABLE IF EXISTS promos CASCADE')

    await conn.execute('''
            CREATE TABLE posts (
                post_id integer,
                lang character(2) NOT NULL,
                msg_id integer NOT NULL,
                media_group_id character varying(120),
                reply_id integer,
                file_type integer,
                file_id character varying(120),
                text text,
                spoiler boolean DEFAULT false NOT NULL,
                CONSTRAINT posts_pkey PRIMARY KEY (msg_id, lang)
            )
        ''')

    await conn.execute('''
            CREATE TABLE promos (
                user_id bigint NOT NULL,
                lang character(2),
                promo_id bigint,
                CONSTRAINT promos_pkey PRIMARY KEY (user_id)
            )
        ''')

    print("--------- conn: ", conn, "---")

    yield conn


 #   await conn.execute('DROP TABLE IF EXISTS posts CASCADE')
  #  await conn.execute('DROP TABLE IF EXISTS promos CASCADE')
    await conn.close()


@pytest.mark.asyncio
async def test_get_mg(db: Connection):
    table_exists = await db.execute(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'posts')"
    )
    assert table_exists, "Posts table does not exist"

    # Insert test data
    await db.execute(
        "INSERT INTO posts(post_id, msg_id, media_group_id, lang) VALUES($1, $2, $3, $4);",
        1, 100, 'test_group', 'de'
    )

    result = await get_mg('test_group', db)
    print(result)
    assert result is not None
    assert result['media_group_id'] == 'test_group'
    assert result['lang'] == 'de'


@pytest.mark.asyncio
async def test_query_files(db):
    test_data = [
        (1, 101, 'group1', 'de'),
        (2, 102, 'group1', 'de'),
    ]
    await db.executemany(
        "INSERT INTO posts(post_id, msg_id, media_group_id, lang) VALUES($1, $2, $3, $4)",
        test_data
    )

    results = await query_files('group1', db)
    assert len(results) == 2
    assert all(r.media_group_id == 'group1' for r in results)


@pytest.mark.asyncio
async def test_insert_single(db):
    post_id = await insert_single(
        msg_id=200,
        conn=db,
        meg_id='test_group',
        reply_id=None,
        file_type=1,
        file_id='abc123',
        lang_key='de',
        text='Test caption',
        spoiler=False
    )

    assert post_id is not None
    result = await db.fetchrow(
        "SELECT * FROM posts WHERE msg_id = $1 AND lang = $2",
        200, 'de'
    )
    assert result['file_id'] == 'abc123'
    assert result['text'] == 'Test caption'


@pytest.mark.asyncio
async def test_update_post(db):
    mock_msg = Mock()
    mock_msg.id = 300
    mock_msg.photo = [Mock(file_id='photo123')]
    mock_msg.video = None
    mock_msg.animation = None
    mock_msg.caption_html_urled = 'Test caption'
    mock_msg.text_html_urled = None

    await insert_single(
        msg_id=300,
        conn=db,
        lang_key='de'
    )

    await update_post(mock_msg, conn=db)

    result = await db.fetchrow(
        "SELECT * FROM posts WHERE msg_id = $1 AND lang = $2",
        300, 'de'
    )
    assert result['file_id'] == 'photo123'
    assert result['text'] == 'Test caption'


@pytest.mark.asyncio
async def test_query_replies(db):
    await db.execute(
        "INSERT INTO posts(post_id, msg_id, reply_id, lang) VALUES($1, $2, $3, $4)",
        1, 400, 401, 'de'
    )

    result = await query_replies(400, 'de', db)
    assert result is not None
    assert result['reply_id'] == 401


@pytest.mark.asyncio
async def test_insert_promo(db):
    result = await insert_promo(123, 'en', 456, db)
    assert result is not None

    duplicate = await insert_promo(123, 'en', 457, db)
    assert duplicate is None

    promo = await db.fetchrow("SELECT * FROM promos WHERE user_id = $1", 123)
    assert promo['promo_id'] == 456
    assert promo['lang'] == 'en'
