"""One-shot SQLite -> Postgres migration script.

Usage (after creating the Render Postgres and getting its connection URL):

    .venv/bin/python migrate_to_postgres.py \\
        --source tracker.db \\
        --target "postgresql://USER:PASS@HOST:PORT/DBNAME"

Or set DATABASE_URL env var instead of --target:

    DATABASE_URL="postgresql://..." .venv/bin/python migrate_to_postgres.py

What it does:
1. Reads schema from db.SCHEMA_POSTGRES and runs it on the target (idempotent).
2. For each table (in FK-dependency order), copies every row from source SQLite
   to target Postgres, preserving primary keys.
3. After insert, advances each table's BIGSERIAL sequence to MAX(id)+1 so future
   inserts on the target don't collide with copied ids.
4. Reports row counts: source vs target. Fails loud if they don't match.

Safe to re-run: tables get CREATE TABLE IF NOT EXISTS, and rows use INSERT ...
ON CONFLICT (id) DO NOTHING so a partial migration can be resumed.
"""
import argparse
import os
import sqlite3
import sys
from typing import List, Tuple

import psycopg
from psycopg.rows import dict_row

# Import the Postgres schema from db.py so we have one source of truth.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import db as _db  # noqa: E402


# FK dependency order — must insert parents before children.
TABLES_IN_ORDER: List[Tuple[str, List[str]]] = [
    ("jobs", [
        "id", "title", "company", "link", "status", "notes", "added_at",
        "next_action_at", "next_action_note", "worth_pursuing",
        "last_activity_at", "jd_raw_text", "jd_summary", "level",
        "yoe_required", "must_have_skills", "nice_to_have_skills",
        "location", "comp_range", "source", "resume_md",
    ]),
    ("contacts", [
        "id", "job_id", "name", "role", "email", "phone", "linkedin_url",
        "notes", "added_at",
    ]),
    ("events", [
        "id", "job_id", "contact_id", "event_type", "body", "occurred_at",
        "recorded_at",
    ]),
    ("oauth_tokens", [
        "id", "provider", "access_token", "refresh_token", "expires_at",
        "scopes", "user_email", "created_at", "updated_at",
    ]),
    ("sync_state", ["key", "value", "updated_at"]),
    ("processed_messages", ["gmail_message_id", "event_id", "processed_at"]),
]


def parse_args():
    p = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--source", default="tracker.db",
        help="Path to source SQLite file (default: tracker.db)")
    p.add_argument("--target", default=None,
        help="Postgres connection URL. Falls back to DATABASE_URL env var.")
    p.add_argument("--dry-run", action="store_true",
        help="Print row counts only, don't insert anything.")
    return p.parse_args()


def get_source_conn(path: str) -> sqlite3.Connection:
    if not os.path.exists(path):
        print(f"ERROR: source SQLite file not found at {path}", file=sys.stderr)
        sys.exit(2)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def get_target_conn(url: str):
    if not url:
        print("ERROR: target Postgres URL missing. Pass --target or set DATABASE_URL.",
              file=sys.stderr)
        sys.exit(2)
    return psycopg.connect(url, row_factory=dict_row, autocommit=False)


def ensure_target_schema(target_conn) -> None:
    """Run the Postgres DDL from db.SCHEMA_POSTGRES on the target."""
    with target_conn.cursor() as cur:
        cur.execute(_db.SCHEMA_POSTGRES)
    target_conn.commit()
    print("✓ Target schema ensured (CREATE TABLE IF NOT EXISTS for all 6 tables)")


def copy_table(source_conn, target_conn, table: str, columns: List[str],
               dry_run: bool = False) -> Tuple[int, int]:
    """Copy a single table. Returns (source_count, inserted_count)."""
    rows = source_conn.execute(f"SELECT {', '.join(columns)} FROM {table}").fetchall()
    src_count = len(rows)
    if src_count == 0:
        print(f"  {table:<22} src=0 (skipped — empty table)")
        return (0, 0)

    if dry_run:
        print(f"  {table:<22} src={src_count} (dry-run — not inserted)")
        return (src_count, 0)

    cols_sql = ", ".join(columns)
    placeholders = ", ".join(["%s"] * len(columns))
    # Use ON CONFLICT to make this re-runnable. processed_messages has TEXT PK,
    # all others have integer id PK — both work with this pattern.
    pk = "gmail_message_id" if table == "processed_messages" else (
         "key" if table == "sync_state" else "id")
    sql = (f"INSERT INTO {table} ({cols_sql}) VALUES ({placeholders}) "
           f"ON CONFLICT ({pk}) DO NOTHING")

    inserted = 0
    with target_conn.cursor() as cur:
        for row in rows:
            cur.execute(sql, tuple(row[c] for c in columns))
            inserted += cur.rowcount
    target_conn.commit()
    print(f"  {table:<22} src={src_count} -> inserted={inserted} (skipped={src_count - inserted})")
    return (src_count, inserted)


def reset_sequences(target_conn, tables_with_serial: List[str]) -> None:
    """Set each table's id sequence to MAX(id) so future inserts don't collide."""
    print("\nResetting sequences:")
    with target_conn.cursor() as cur:
        for table in tables_with_serial:
            cur.execute(f"SELECT COALESCE(MAX(id), 0) AS m FROM {table}")
            max_id = cur.fetchone()["m"]
            if max_id > 0:
                # Postgres SERIAL/BIGSERIAL auto-creates a sequence named
                # <table>_<column>_seq
                seq_name = f"{table}_id_seq"
                cur.execute(f"SELECT setval(%s, %s)", (seq_name, max_id))
                print(f"  {table:<22} sequence {seq_name} -> {max_id}")
    target_conn.commit()


def verify_counts(source_conn, target_conn) -> bool:
    print("\nVerifying row counts:")
    ok = True
    for table, _cols in TABLES_IN_ORDER:
        src = source_conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"]
        with target_conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) AS n FROM {table}")
            tgt = cur.fetchone()["n"]
        flag = "OK " if src == tgt else "BAD"
        print(f"  [{flag}] {table:<22} source={src} target={tgt}")
        if src != tgt:
            ok = False
    return ok


def main():
    args = parse_args()
    target_url = args.target or os.environ.get("DATABASE_URL")

    print(f"Source: {args.source}")
    print(f"Target: {target_url[:30] + '...' if target_url else '(missing)'}")
    print(f"Dry run: {args.dry_run}\n")

    source = get_source_conn(args.source)
    target = get_target_conn(target_url)

    try:
        ensure_target_schema(target)
        print("\nCopying tables:")
        for table, cols in TABLES_IN_ORDER:
            copy_table(source, target, table, cols, dry_run=args.dry_run)

        if not args.dry_run:
            reset_sequences(target, [t for t, _ in TABLES_IN_ORDER
                                     if t not in ("sync_state", "processed_messages")])
            ok = verify_counts(source, target)
            if not ok:
                print("\n✗ MIGRATION INCOMPLETE — some row counts don't match.",
                      file=sys.stderr)
                sys.exit(3)
            print("\n✓ Migration complete. All row counts match.")
    finally:
        source.close()
        target.close()


if __name__ == "__main__":
    main()
