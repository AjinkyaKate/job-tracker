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
    FOREIGN KEY (job_id) REFERENCES jobs(id)
);
"""


def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
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


def add_contact(job_id):
    init_db()

    with get_connection() as conn:
        job = conn.execute(
            "SELECT id, title, company FROM jobs WHERE id = ?",
            (job_id,),
        ).fetchone()

    if not job:
        print(f"\nNo job with id {job_id}. Use 'list' to see job IDs.\n")
        sys.exit(1)

    print(f"\nAdd contact for job #{job_id}: {job['title']} @ {job['company']}")
    print("Press Enter to skip a field.\n")

    name = input("  Name: ").strip()
    role = input("  Role (HR / founder / recruiter / etc): ").strip()
    email = input("  Email: ").strip()
    phone = input("  Phone: ").strip()
    linkedin_url = input("  LinkedIn URL: ").strip()
    notes = input("  Notes: ").strip()
    added_at = datetime.now().isoformat(timespec="seconds")

    if not name:
        print("\nA name is required. Aborting.\n")
        sys.exit(1)

    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO contacts (job_id, name, role, email, phone, linkedin_url, notes, added_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (job_id, name, role, email, phone, linkedin_url, notes, added_at),
        )
        new_id = cursor.lastrowid

    print(f"\nSaved contact #{new_id}: {name} -> job #{job_id} ({job['company']})\n")


def list_jobs():
    init_db()

    with get_connection() as conn:
        jobs = conn.execute("SELECT * FROM jobs ORDER BY id").fetchall()
        contacts = conn.execute(
            "SELECT * FROM contacts ORDER BY job_id, id"
        ).fetchall()

    if not jobs:
        print("\nNo jobs yet. Add one with: python3 tracker.py add\n")
        return

    contacts_by_job = {}
    for c in contacts:
        contacts_by_job.setdefault(c["job_id"], []).append(c)

    print(f"\n{len(jobs)} job(s):\n")
    for job in jobs:
        print(f"  [{job['id']:>3}] {job['status']:<24}  {job['title']}  @  {job['company']}")
        if job["link"]:
            print(f"        {job['link']}")
        for c in contacts_by_job.get(job["id"], []):
            details = [d for d in (c["role"], c["email"], c["phone"]) if d]
            line = f"          -> [c{c['id']}] {c['name']}"
            if details:
                line += "  (" + "  |  ".join(details) + ")"
            print(line)
    print()


def usage():
    print("Usage: python3 tracker.py <command> [args]")
    print("Commands:")
    print("  add                       Add a new job (interactive)")
    print("  list                      Show all jobs and their contacts")
    print("  contact <job_id>          Add a contact to an existing job")


def main():
    if len(sys.argv) < 2:
        usage()
        sys.exit(1)

    command = sys.argv[1]
    if command == "add":
        add_job()
    elif command == "list":
        list_jobs()
    elif command == "contact":
        if len(sys.argv) < 3:
            print("Usage: python3 tracker.py contact <job_id>")
            sys.exit(1)
        try:
            job_id = int(sys.argv[2])
        except ValueError:
            print("job_id must be an integer")
            sys.exit(1)
        add_contact(job_id)
    else:
        print(f"Unknown command: {command}\n")
        usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
