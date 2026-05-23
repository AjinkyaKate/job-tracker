import sqlite3
import sys
from datetime import datetime

DB_FILE = "tracker.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    company TEXT,
    link TEXT,
    status TEXT NOT NULL DEFAULT 'saved',
    notes TEXT,
    added_at TEXT NOT NULL
);
"""


def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.executescript(SCHEMA)


def add_job():
    init_db()

    print("\nAdd job. Press Enter to skip a field.\n")
    title = input("  Job title: ").strip()
    company = input("  Company: ").strip()
    link = input("  Link: ").strip()
    status = input("  Status [saved]: ").strip() or "saved"
    notes = input("  Notes: ").strip()
    added_at = datetime.now().isoformat(timespec="seconds")

    if not title:
        print("\nA title is required. Aborting.\n")
        sys.exit(1)

    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO jobs (title, company, link, status, notes, added_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (title, company, link, status, notes, added_at),
        )
        new_id = cursor.lastrowid

    print(f"\nSaved as job #{new_id}: {title} @ {company}\n")


def list_jobs():
    init_db()

    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM jobs ORDER BY id").fetchall()

    if not rows:
        print("\nNo jobs yet. Add one with: python3 tracker.py add\n")
        return

    print(f"\n{len(rows)} job(s):\n")
    for job in rows:
        print(f"  [{job['id']:>3}] {job['status']:<24}  {job['title']}  @  {job['company']}")
        if job["link"]:
            print(f"        {job['link']}")
    print()


def usage():
    print("Usage: python3 tracker.py <command>")
    print("Commands:")
    print("  add    Add a new job (interactive prompts)")
    print("  list   Show all saved jobs")


def main():
    if len(sys.argv) < 2:
        usage()
        sys.exit(1)

    command = sys.argv[1]
    if command == "add":
        add_job()
    elif command == "list":
        list_jobs()
    else:
        print(f"Unknown command: {command}\n")
        usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
