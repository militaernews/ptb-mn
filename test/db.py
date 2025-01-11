

import pytest
from asyncpg import connect
from testing.postgresql import Postgresql

from data.db import insert_promo, query_replies, query_files, get_mg
pytest_plugins = ["pytest_asyncio"]


# Helper functions
async def setup_schema(conn):
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            post_id SERIAL PRIMARY KEY,
            lang CHAR(2) NOT NULL,
            msg_id INT NOT NULL,
            media_group_id VARCHAR(120),
            reply_id INT,
            file_type INT,
            file_id VARCHAR(120),
            text TEXT,
            spoiler BOOLEAN DEFAULT FALSE NOT NULL
        );

        CREATE TABLE IF NOT EXISTS promos (
            user_id BIGINT PRIMARY KEY,
            lang CHAR(2),
            promo_id BIGINT
        );
    """)

async def cleanup_schema(conn):
    await conn.execute("DROP TABLE IF EXISTS posts;")
    await conn.execute("DROP TABLE IF EXISTS promos;")

# Fixtures
@pytest.fixture(scope="module")
async def db_connection():
    postgresql = Postgresql(port=7654)
    connection_url = postgresql.url()
    pool = await connect(connection_url)


    async with pool.acquire() as conn:
        await setup_schema(conn)
        yield conn
        await cleanup_schema(conn)


    await conn.close()
    postgresql.stop()


@pytest.mark.asyncio
async def test_get_mg(db_connection):
    print(db_connection)
    print("---- hi -- ")


    await db_connection.execute("""
            INSERT INTO posts (lang, msg_id, media_group_id, text)
            VALUES ('de', 1, 'group1', 'Test Message');
        """)

    result = await get_mg('group1', db_connection)
    assert result is not None
    assert result['media_group_id'] == 'group1'

@pytest.mark.asyncio
async def test_query_files(db_connection):
    conn = db_connection
    await conn.execute("""
        INSERT INTO posts (lang, msg_id, media_group_id, text)
        VALUES ('de', 2, 'group2', 'Another Test Message');
    """)

    results = await query_files('group2', conn)
    assert len(results) > 0
    assert results[0]['media_group_id'] == 'group2'

@pytest.mark.asyncio
async def test_query_replies(db_connection):
    conn = db_connection
    await conn.execute("""
        INSERT INTO posts (lang, msg_id, reply_id)
        VALUES ('de', 3, 123);
    """)

    result = await query_replies(3, 'de', conn)
    assert result is not None
    assert result['reply_id'] == 123

@pytest.mark.asyncio
async def test_insert_promo(db_connection):
    conn = db_connection


    user_id = 1001
    lang = 'en'
    promo_id = 5001

    result = await insert_promo(user_id, lang, promo_id, conn)
    assert result == user_id

    # Test duplicate insertion
    result_duplicate = await insert_promo(user_id, lang, promo_id, conn)
    assert result_duplicate is None
