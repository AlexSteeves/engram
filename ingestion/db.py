import os
import psycopg2
import psycopg2.extras
from datetime import datetime, timezone


def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))


def upsert_document(conn, source, source_id, title, body, metadata, created_at):
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO documents (source, source_id, title, body, metadata, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (source, source_id) DO UPDATE SET
            title      = EXCLUDED.title,
            body       = EXCLUDED.body,
            metadata   = EXCLUDED.metadata,
            created_at = EXCLUDED.created_at
        """,
        (source, source_id, title, body, psycopg2.extras.Json(metadata), created_at),
    )
    cur.close()


def get_last_synced(conn, source):
    cur = conn.cursor()
    cur.execute("SELECT last_synced_at FROM sync_state WHERE source = %s", (source,))
    row = cur.fetchone()
    cur.close()
    return row[0] if row else None


def set_last_synced(conn, source):
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO sync_state (source, last_synced_at) VALUES (%s, %s)
        ON CONFLICT (source) DO UPDATE SET last_synced_at = EXCLUDED.last_synced_at
        """,
        (source, datetime.now(timezone.utc)),
    )
    conn.commit()
    cur.close()
