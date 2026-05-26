"""Database adapter — SQLite locally, Postgres on Render.

Backend is selected by the DATABASE_URL env var:
- Set (postgresql://...): psycopg connection
- Unset: sqlite3 connection at $DB_FILE (default tracker.db)

Consumer code uses one API regardless of backend:

    from db import get_connection, insert_returning_id, column_exists

    with get_connection() as conn:
        # ? placeholders work in BOTH backends — the wrapper translates for Postgres
        rows = conn.execute("SELECT * FROM jobs WHERE id = ?", (5,)).fetchall()
        # rows behave like dicts in both backends → row["column"], not row[0]

    new_id = insert_returning_id(
        conn,
        "INSERT INTO jobs (title, company, added_at) VALUES (?, ?, ?)",
        (title, company, now),
    )

    if not column_exists(conn, "jobs", "new_column"):
        conn.execute("ALTER TABLE jobs ADD COLUMN new_column TEXT")
"""
import os
import sqlite3
from typing import Sequence, Optional

DATABASE_URL = os.environ.get("DATABASE_URL")
DB_FILE = os.environ.get("DB_FILE", "tracker.db")
IS_POSTGRES = bool(DATABASE_URL)

if IS_POSTGRES:
    import psycopg
    from psycopg.rows import dict_row


# ─── Connection wrapper ─────────────────────────────────────────────────────

class Connection:
    """Thin wrapper providing a unified execute() API over sqlite3 + psycopg.

    All queries should use ? placeholders; this wrapper rewrites them to %s for
    Postgres. execute() returns a cursor that supports .fetchone(), .fetchall(),
    and (in SQLite) .lastrowid — use insert_returning_id() instead of lastrowid
    so it works on both backends.
    """

    def __init__(self, raw):
        self._raw = raw

    def execute(self, sql: str, params: Optional[Sequence] = None):
        if IS_POSTGRES:
            # Escape literal '%' (e.g. LIKE 'SUGGESTED%') to '%%' BEFORE converting
            # '?' placeholders to '%s' — otherwise psycopg tries to interpret the
            # literal % as a placeholder and fails.
            sql = sql.replace("%", "%%").replace("?", "%s")
            cur = self._raw.cursor()
            cur.execute(sql, params or ())
            return cur
        if params is not None:
            return self._raw.execute(sql, params)
        return self._raw.execute(sql)

    def executescript(self, sql: str) -> None:
        if IS_POSTGRES:
            with self._raw.cursor() as cur:
                cur.execute(sql)
        else:
            self._raw.executescript(sql)

    def cursor(self):
        return self._raw.cursor()

    def commit(self) -> None:
        self._raw.commit()

    def rollback(self) -> None:
        self._raw.rollback()

    def close(self) -> None:
        self._raw.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self._raw.commit()
        else:
            self._raw.rollback()
        return False


def get_connection() -> Connection:
    """Open a DB connection with dict-like row access in both backends."""
    if IS_POSTGRES:
        raw = psycopg.connect(DATABASE_URL, row_factory=dict_row, autocommit=False)
        return Connection(raw)
    raw = sqlite3.connect(DB_FILE)
    raw.row_factory = sqlite3.Row
    raw.execute("PRAGMA foreign_keys = ON")
    return Connection(raw)


# ─── Helpers for backend-specific patterns ──────────────────────────────────

def insert_returning_id(conn: Connection, sql: str, params: Sequence) -> int:
    """Execute an INSERT and return the new row's id.

    sql: raw INSERT using ? placeholders. Do NOT append RETURNING; this helper
         handles it for Postgres and falls back to lastrowid for SQLite.
    """
    if IS_POSTGRES:
        # Same %-escape rule as Connection.execute — see comment there.
        rewritten = sql.replace("%", "%%").replace("?", "%s") + " RETURNING id"
        cur = conn._raw.cursor()
        cur.execute(rewritten, params)
        row = cur.fetchone()
        if row is None:
            raise RuntimeError("INSERT ... RETURNING produced no row")
        return row["id"]
    cur = conn._raw.cursor()
    cur.execute(sql, params)
    return cur.lastrowid


def column_exists(conn: Connection, table: str, column: str) -> bool:
    """Cross-backend column check for idempotent ALTER TABLE migrations."""
    if IS_POSTGRES:
        cur = conn.execute(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = ? AND column_name = ?",
            (table, column),
        )
        return cur.fetchone() is not None
    info = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row["name"] == column for row in info)


def upsert_processed_message(conn: Connection, gmail_message_id: str,
                              event_id: Optional[int], processed_at: str,
                              user_id: int = 1) -> None:
    """Cross-backend upsert on processed_messages, tagged by user_id.

    Known caveat: processed_messages.gmail_message_id is still the singleton
    PK from the original schema. Two users could (in theory) have different
    messages with colliding Gmail IDs — when the second user lands we'll
    rebuild the PK to (user_id, gmail_message_id). Today, one user means no
    collision possible.
    """
    if IS_POSTGRES:
        conn.execute(
            "INSERT INTO processed_messages (gmail_message_id, event_id, processed_at, user_id) "
            "VALUES (?, ?, ?, ?) "
            "ON CONFLICT (gmail_message_id) DO UPDATE SET "
            "event_id = EXCLUDED.event_id, processed_at = EXCLUDED.processed_at, "
            "user_id = EXCLUDED.user_id",
            (gmail_message_id, event_id, processed_at, user_id),
        )
    else:
        conn.execute(
            "INSERT OR REPLACE INTO processed_messages "
            "(gmail_message_id, event_id, processed_at, user_id) VALUES (?, ?, ?, ?)",
            (gmail_message_id, event_id, processed_at, user_id),
        )


# ─── Schema (mirrored per backend) ──────────────────────────────────────────

SCHEMA_SQLITE = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    company TEXT,
    link TEXT,
    status TEXT NOT NULL DEFAULT 'saved',
    notes TEXT,
    added_at TEXT NOT NULL,
    next_action_at TEXT,
    next_action_note TEXT,
    worth_pursuing TEXT DEFAULT 'unsure',
    last_activity_at TEXT,
    user_id INTEGER
);

CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    role TEXT,
    email TEXT,
    phone TEXT,
    linkedin_url TEXT,
    notes TEXT,
    added_at TEXT NOT NULL,
    user_id INTEGER,
    FOREIGN KEY (job_id) REFERENCES jobs(id)
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    contact_id INTEGER,
    event_type TEXT NOT NULL,
    body TEXT,
    occurred_at TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    user_id INTEGER,
    FOREIGN KEY (job_id) REFERENCES jobs(id),
    FOREIGN KEY (contact_id) REFERENCES contacts(id)
);

CREATE TABLE IF NOT EXISTS oauth_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL UNIQUE,
    access_token TEXT,
    refresh_token TEXT,
    expires_at TEXT,
    scopes TEXT,
    user_email TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    user_id INTEGER
);

CREATE TABLE IF NOT EXISTS sync_state (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT NOT NULL,
    user_id INTEGER
);

CREATE TABLE IF NOT EXISTS processed_messages (
    gmail_message_id TEXT PRIMARY KEY,
    event_id INTEGER,
    processed_at TEXT NOT NULL,
    user_id INTEGER,
    FOREIGN KEY (event_id) REFERENCES events(id)
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    google_user_id TEXT UNIQUE,
    name TEXT,
    picture_url TEXT,
    created_at TEXT NOT NULL,
    last_login_at TEXT
);
"""

# Postgres translations:
#   INTEGER PRIMARY KEY AUTOINCREMENT  →  BIGSERIAL PRIMARY KEY
#   PRAGMA foreign_keys = ON           →  not needed (always enforced in PG)
#   TEXT, INTEGER, DEFAULT, FOREIGN KEY syntax unchanged
SCHEMA_POSTGRES = """
CREATE TABLE IF NOT EXISTS jobs (
    id BIGSERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    company TEXT,
    link TEXT,
    status TEXT NOT NULL DEFAULT 'saved',
    notes TEXT,
    added_at TEXT NOT NULL,
    next_action_at TEXT,
    next_action_note TEXT,
    worth_pursuing TEXT DEFAULT 'unsure',
    last_activity_at TEXT,
    user_id INTEGER
);

CREATE TABLE IF NOT EXISTS contacts (
    id BIGSERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    role TEXT,
    email TEXT,
    phone TEXT,
    linkedin_url TEXT,
    notes TEXT,
    added_at TEXT NOT NULL,
    user_id INTEGER,
    FOREIGN KEY (job_id) REFERENCES jobs(id)
);

CREATE TABLE IF NOT EXISTS events (
    id BIGSERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL,
    contact_id INTEGER,
    event_type TEXT NOT NULL,
    body TEXT,
    occurred_at TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    user_id INTEGER,
    FOREIGN KEY (job_id) REFERENCES jobs(id),
    FOREIGN KEY (contact_id) REFERENCES contacts(id)
);

CREATE TABLE IF NOT EXISTS oauth_tokens (
    id BIGSERIAL PRIMARY KEY,
    provider TEXT NOT NULL UNIQUE,
    access_token TEXT,
    refresh_token TEXT,
    expires_at TEXT,
    scopes TEXT,
    user_email TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    user_id INTEGER
);

CREATE TABLE IF NOT EXISTS sync_state (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT NOT NULL,
    user_id INTEGER
);

CREATE TABLE IF NOT EXISTS processed_messages (
    gmail_message_id TEXT PRIMARY KEY,
    event_id INTEGER,
    processed_at TEXT NOT NULL,
    user_id INTEGER,
    FOREIGN KEY (event_id) REFERENCES events(id)
);

CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    google_user_id TEXT UNIQUE,
    name TEXT,
    picture_url TEXT,
    created_at TEXT NOT NULL,
    last_login_at TEXT
);
"""


def init_schema(conn: Connection) -> None:
    """Create base tables + run migrations. Idempotent — safe on every app start."""
    conn.executescript(SCHEMA_POSTGRES if IS_POSTGRES else SCHEMA_SQLITE)
    migrate_add_user_id(conn)


def migrate_add_user_id(conn: Connection) -> None:
    """Phase 2 multi-tenancy: tag every row with its owning user_id.

    Adds a user_id column to all per-user data tables (idempotent via
    column_exists), then backfills any NULLs to user_id=1. The single-user
    backfill is the safe path because the project was strictly single-tenant
    before this migration — there is only one user whose Gmail was ever
    synced, and they own all existing rows.

    Constraint changes (e.g. dropping the UNIQUE on oauth_tokens.provider so
    multiple users can each connect Gmail) are deferred until the query
    layer is rewired in the next step.
    """
    per_user_tables = [
        "jobs", "contacts", "events",
        "oauth_tokens", "sync_state", "processed_messages",
    ]
    for table in per_user_tables:
        if not column_exists(conn, table, "user_id"):
            conn.execute(f"ALTER TABLE {table} ADD COLUMN user_id INTEGER")
        conn.execute(f"UPDATE {table} SET user_id = 1 WHERE user_id IS NULL")

    # sync_state keys were global before multi-tenancy; the new code reads
    # and writes them under a per-user prefix ("u1:last_gmail_sync"). Rename
    # the legacy bare keys so user 1's sync history isn't lost — otherwise
    # the first post-deploy sync would re-fetch 7 days of email.
    for old_key, new_key in [
        ("last_gmail_sync",   "u1:last_gmail_sync"),
        ("last_sync_summary", "u1:last_sync_summary"),
    ]:
        old = conn.execute(
            "SELECT value, updated_at FROM sync_state WHERE key = ?",
            (old_key,),
        ).fetchone()
        if not old:
            continue
        already_new = conn.execute(
            "SELECT 1 FROM sync_state WHERE key = ?", (new_key,),
        ).fetchone()
        if already_new:
            conn.execute("DELETE FROM sync_state WHERE key = ?", (old_key,))
            continue
        conn.execute(
            "INSERT INTO sync_state (key, value, updated_at, user_id) "
            "VALUES (?, ?, ?, 1)",
            (new_key, old["value"], old["updated_at"]),
        )
        conn.execute("DELETE FROM sync_state WHERE key = ?", (old_key,))
