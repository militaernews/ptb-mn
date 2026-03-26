"""
migrate_neon.py
===============
Migriert Daten von der Neon.tech PostgreSQL-Datenbank in die lokale Datenbank.
Liest Zugangsdaten aus Umgebungsvariablen oder einer .env Datei.
"""

import os
import psycopg2
import psycopg2.extras
import sys
import time
from dotenv import load_dotenv

# .env Datei aus dem Root-Verzeichnis laden (falls vorhanden)
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

# ── Verbindungsparameter ──────────────────────────────────────────────────────
# Standardwerte aus deinen Quadlets/Neon-Angaben
NEON_DSN_DEFAULT = "postgresql://mn_owner:CBylvJA4OVg1@ep-dry-river-a2r3ntij-pooler.eu-central-1.aws.neon.tech/mn?sslmode=require"
LOCAL_DSN_DEFAULT = "host=localhost port=5432 dbname=ptb_mn user=ptb_user password=ptb_password"

NEON_DSN = os.getenv("DATABASE_URL_NEON", NEON_DSN_DEFAULT)
LOCAL_DSN = os.getenv("DATABASE_URL", LOCAL_DSN_DEFAULT)

BATCH_SIZE = 1000

def connect(dsn: str, label: str):
    try:
        print(f"[INFO] Verbinde mit {label} ...")
        conn = psycopg2.connect(dsn)
        conn.autocommit = False
        print(f"[OK]   {label} verbunden.")
        return conn
    except Exception as e:
        print(f"[ERROR] Verbindung zu {label} fehlgeschlagen: {e}")
        sys.exit(1)

def init_schema(local_conn):
    schema = """
    CREATE TABLE IF NOT EXISTS posts (
        post_id int, lang char(2) NOT NULL, msg_id int NOT NULL,
        media_group_id varchar(120), reply_id int, file_type int,
        file_id varchar(120), text text, spoiler boolean NOT NULL DEFAULT false,
        PRIMARY KEY (msg_id, lang)
    );
    CREATE TABLE IF NOT EXISTS promos (
        user_id bigint NOT NULL PRIMARY KEY, lang char(2), promo_id bigint
    );
    CREATE TABLE IF NOT EXISTS suggest_posts (
        source_channel_id bigint NOT NULL, source_message_id int NOT NULL,
        suggest_message_id int NOT NULL, text text,
        created_at timestamptz NOT NULL DEFAULT now(),
        PRIMARY KEY (source_channel_id, source_message_id)
    );
    CREATE TABLE IF NOT EXISTS whitelist (
        id serial PRIMARY KEY, link text NOT NULL UNIQUE,
        created_at timestamptz NOT NULL DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS warnings (
        user_id bigint NOT NULL, chat_id bigint NOT NULL,
        count int NOT NULL DEFAULT 0, last_warned_at timestamptz NOT NULL DEFAULT now(),
        PRIMARY KEY (user_id, chat_id)
    );
    CREATE TABLE IF NOT EXISTS user_stats (
        user_id bigint NOT NULL, chat_id bigint NOT NULL,
        karma int NOT NULL DEFAULT 0, message_count int NOT NULL DEFAULT 0,
        joined_at timestamptz NOT NULL DEFAULT now(),
        PRIMARY KEY (user_id, chat_id)
    );
    CREATE TABLE IF NOT EXISTS user_events (
        id serial PRIMARY KEY, user_id bigint NOT NULL, chat_id bigint NOT NULL,
        event_type varchar(20) NOT NULL, created_at timestamptz NOT NULL DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS message_authors (
        message_id bigint NOT NULL, chat_id bigint NOT NULL, user_id bigint NOT NULL,
        created_at timestamptz NOT NULL DEFAULT now(),
        PRIMARY KEY (message_id, chat_id)
    );
    CREATE TABLE IF NOT EXISTS persistence (data json NOT NULL);
    """
    cur = local_conn.cursor()
    cur.execute(schema)
    local_conn.commit()
    cur.close()

def migrate_table(neon_conn, local_conn, table, columns, insert_sql, conflict_clause="ON CONFLICT DO NOTHING"):
    neon_cur = neon_conn.cursor(name=f"cur_{table}", cursor_factory=psycopg2.extras.DictCursor)
    local_cur = local_conn.cursor()
    neon_cur.execute(f"SELECT {', '.join(columns)} FROM {table};")
    total = 0
    full_sql = f"{insert_sql} {conflict_clause}"
    while True:
        rows = neon_cur.fetchmany(BATCH_SIZE)
        if not rows: break
        batch = [tuple(row) for row in rows]
        psycopg2.extras.execute_batch(local_cur, full_sql, batch, page_size=BATCH_SIZE)
        local_conn.commit()
        total += len(batch)
        print(f"  [{table}] {total} Zeilen ...", end="\r")
    neon_cur.close()
    local_cur.close()
    print(f"\n[OK]   {table}: {total} Zeilen migriert.")

def main():
    start = time.time()
    neon_conn = connect(NEON_DSN, "Neon.tech (Quelle)")
    local_conn = connect(LOCAL_DSN, "Lokal (Ziel)")
    init_schema(local_conn)

    tables = [
        ("posts", ["post_id", "lang", "msg_id", "media_group_id", "reply_id", "file_type", "file_id", "text", "spoiler"], 
         "INSERT INTO posts(post_id, lang, msg_id, media_group_id, reply_id, file_type, file_id, text, spoiler) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
         "ON CONFLICT (msg_id, lang) DO NOTHING"),
        ("promos", ["user_id", "lang", "promo_id"], "INSERT INTO promos(user_id, lang, promo_id) VALUES (%s, %s, %s)", "ON CONFLICT (user_id) DO NOTHING"),
        ("suggest_posts", ["source_channel_id", "source_message_id", "suggest_message_id", "text", "created_at"], "INSERT INTO suggest_posts(source_channel_id, source_message_id, suggest_message_id, text, created_at) VALUES (%s, %s, %s, %s, %s)", "ON CONFLICT (source_channel_id, source_message_id) DO NOTHING"),
        ("whitelist", ["link", "created_at"], "INSERT INTO whitelist(link, created_at) VALUES (%s, %s)", "ON CONFLICT (link) DO NOTHING"),
        ("warnings", ["user_id", "chat_id", "count", "last_warned_at"], "INSERT INTO warnings(user_id, chat_id, count, last_warned_at) VALUES (%s, %s, %s, %s)", "ON CONFLICT (user_id, chat_id) DO NOTHING"),
        ("user_stats", ["user_id", "chat_id", "karma", "message_count", "joined_at"], "INSERT INTO user_stats(user_id, chat_id, karma, message_count, joined_at) VALUES (%s, %s, %s, %s, %s)", "ON CONFLICT (user_id, chat_id) DO NOTHING"),
        ("user_events", ["user_id", "chat_id", "event_type", "created_at"], "INSERT INTO user_events(user_id, chat_id, event_type, created_at) VALUES (%s, %s, %s, %s)", ""),
        ("persistence", ["data"], "INSERT INTO persistence(data) VALUES (%s)", "")
    ]

    for t_name, cols, sql, conflict in tables:
        migrate_table(neon_conn, local_conn, t_name, cols, sql, conflict)

    neon_conn.close()
    local_conn.close()
    print(f"\n[FERTIG] Migration abgeschlossen in {time.time() - start:.1f}s")

if __name__ == "__main__":
    main()
