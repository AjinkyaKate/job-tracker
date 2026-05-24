import sys
from datetime import datetime

from db import get_connection, init_schema, insert_returning_id, column_exists


def _ensure_column(conn, table, column, type_spec):
    """Add a column if missing. Backend-aware via db.column_exists."""
    if not column_exists(conn, table, column):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {type_spec}")


def init_db():
    with get_connection() as conn:
        init_schema(conn)
        # Idempotent ALTERs for columns introduced after the initial schema.
        # New deploys against fresh Postgres land all these columns via the
        # base schema; ALTERs are only needed for older SQLite databases.
        _ensure_column(conn, "jobs", "next_action_at", "TEXT")
        _ensure_column(conn, "jobs", "next_action_note", "TEXT")
        _ensure_column(conn, "jobs", "worth_pursuing", "TEXT DEFAULT 'unsure'")
        _ensure_column(conn, "jobs", "last_activity_at", "TEXT")
        _ensure_column(conn, "jobs", "jd_raw_text", "TEXT")
        _ensure_column(conn, "jobs", "jd_summary", "TEXT")
        _ensure_column(conn, "jobs", "level", "TEXT")
        _ensure_column(conn, "jobs", "yoe_required", "TEXT")
        _ensure_column(conn, "jobs", "must_have_skills", "TEXT")
        _ensure_column(conn, "jobs", "nice_to_have_skills", "TEXT")
        _ensure_column(conn, "jobs", "location", "TEXT")
        _ensure_column(conn, "jobs", "comp_range", "TEXT")
        _ensure_column(conn, "jobs", "source", "TEXT")
        _ensure_column(conn, "jobs", "resume_md", "TEXT")
        # Date of the Saved → Applied transition. Drives the "applied Xd ago"
        # activity line + the "Stale 3d+ no reply" filter on Pipeline.
        # NULL for jobs that never went through Applied or pre-date this column.
        _ensure_column(conn, "jobs", "applied_at", "TEXT")


def _require_job(conn, job_id):
    job = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if not job:
        print(f"\nNo job with id {job_id}. Use 'list' to see job IDs.\n")
        sys.exit(1)
    return job


def add_job():
    init_db()

    print("\nAdd job. Press Enter to skip a field.\n")
    title = input("  Job title: ").strip()
    company = input("  Company: ").strip()
    link = input("  Link: ").strip()
    status = input("  Status [saved]: ").strip() or "saved"
    notes = input("  Notes: ").strip()
    now = datetime.now().isoformat(timespec="seconds")

    if not title:
        print("\nA title is required. Aborting.\n")
        sys.exit(1)

    with get_connection() as conn:
        new_id = insert_returning_id(
            conn,
            "INSERT INTO jobs (title, company, link, status, notes, added_at, last_activity_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (title, company, link, status, notes, now, now),
        )
        conn.execute(
            "INSERT INTO events (job_id, event_type, body, occurred_at, recorded_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (new_id, "job_added", f"Job created: {title} @ {company}", now, now),
        )

    print(f"\nSaved as job #{new_id}: {title} @ {company}\n")


def add_contact(job_id):
    init_db()

    with get_connection() as conn:
        job = _require_job(conn, job_id)

    print(f"\nAdd contact for job #{job_id}: {job['title']} @ {job['company']}")
    print("Press Enter to skip a field.\n")

    name = input("  Name: ").strip()
    role = input("  Role (HR / founder / recruiter / etc): ").strip()
    email = input("  Email: ").strip()
    phone = input("  Phone: ").strip()
    linkedin_url = input("  LinkedIn URL: ").strip()
    notes = input("  Notes: ").strip()
    now = datetime.now().isoformat(timespec="seconds")

    if not name:
        print("\nA name is required. Aborting.\n")
        sys.exit(1)

    with get_connection() as conn:
        contact_id = insert_returning_id(
            conn,
            "INSERT INTO contacts (job_id, name, role, email, phone, linkedin_url, notes, added_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (job_id, name, role, email, phone, linkedin_url, notes, now),
        )
        conn.execute(
            "INSERT INTO events (job_id, contact_id, event_type, body, occurred_at, recorded_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (job_id, contact_id, "contact_added", f"{name} ({role})", now, now),
        )
        conn.execute("UPDATE jobs SET last_activity_at = ? WHERE id = ?", (now, job_id))

    print(f"\nSaved contact #{contact_id}: {name} -> job #{job_id} ({job['company']})\n")


def cmd_status(job_id, new_status):
    init_db()
    now = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        job = _require_job(conn, job_id)
        old_status = job["status"]
        conn.execute(
            "UPDATE jobs SET status = ?, last_activity_at = ? WHERE id = ?",
            (new_status, now, job_id),
        )
        conn.execute(
            "INSERT INTO events (job_id, event_type, body, occurred_at, recorded_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (job_id, "status_change", f"{old_status} -> {new_status}", now, now),
        )
    print(f"\nJob #{job_id}: status {old_status} -> {new_status}\n")


def cmd_action(job_id, date_str, note):
    init_db()
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        print(f"\nDate must be YYYY-MM-DD format. Got: {date_str}\n")
        sys.exit(1)
    with get_connection() as conn:
        _require_job(conn, job_id)
        conn.execute(
            "UPDATE jobs SET next_action_at = ?, next_action_note = ? WHERE id = ?",
            (date_str, note, job_id),
        )
    print(f"\nJob #{job_id}: next action {date_str} - {note}\n")


def cmd_event(job_id, event_type, body):
    init_db()
    now = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        _require_job(conn, job_id)
        conn.execute(
            "INSERT INTO events (job_id, event_type, body, occurred_at, recorded_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (job_id, event_type, body, now, now),
        )
        conn.execute("UPDATE jobs SET last_activity_at = ? WHERE id = ?", (now, job_id))
    print(f"\nLogged '{event_type}' on job #{job_id}: {body}\n")


def cmd_pursue(job_id, value):
    init_db()
    if value not in ("yes", "no", "unsure"):
        print(f"\nworth_pursuing must be yes/no/unsure. Got: {value}\n")
        sys.exit(1)
    with get_connection() as conn:
        _require_job(conn, job_id)
        conn.execute(
            "UPDATE jobs SET worth_pursuing = ? WHERE id = ?",
            (value, job_id),
        )
    print(f"\nJob #{job_id}: worth_pursuing = {value}\n")


def cmd_today():
    init_db()
    today = datetime.now().date().isoformat()

    with get_connection() as conn:
        due = conn.execute(
            """
            SELECT id, title, company, status, next_action_at, next_action_note
            FROM jobs
            WHERE next_action_at IS NOT NULL
              AND next_action_at <= ?
              AND (worth_pursuing IS NULL OR worth_pursuing != 'no')
            ORDER BY next_action_at
            """,
            (today,),
        ).fetchall()

        upcoming = conn.execute(
            """
            SELECT id, title, company, status, next_action_at, next_action_note
            FROM jobs
            WHERE next_action_at IS NOT NULL
              AND next_action_at > ?
              AND (worth_pursuing IS NULL OR worth_pursuing != 'no')
            ORDER BY next_action_at
            LIMIT 5
            """,
            (today,),
        ).fetchall()

        counts = conn.execute(
            """
            SELECT status, COUNT(*) AS n FROM jobs
            WHERE worth_pursuing IS NULL OR worth_pursuing != 'no'
            GROUP BY status ORDER BY n DESC
            """
        ).fetchall()

        backlog = conn.execute(
            "SELECT COUNT(*) AS n FROM jobs WHERE worth_pursuing = 'no'"
        ).fetchone()["n"]

    print(f"\n=== TODAY ({today}) ===\n")

    if due:
        print(f"DUE NOW ({len(due)} job(s)):")
        for job in due:
            urgency = "OVERDUE" if job["next_action_at"] < today else "due today"
            print(f"  [{job['id']:>3}] {urgency} ({job['next_action_at']})")
            print(f"        {job['title']}  @  {job['company']}  [{job['status']}]")
            if job["next_action_note"]:
                print(f"        -> {job['next_action_note']}")
        print()
    else:
        print("Nothing due today.\n")

    if upcoming:
        print(f"UPCOMING (next 5):")
        for job in upcoming:
            print(f"  [{job['id']:>3}] {job['next_action_at']}  {job['title']}  @  {job['company']}")
            if job["next_action_note"]:
                print(f"        -> {job['next_action_note']}")
        print()

    if counts:
        print("ACTIVE PIPELINE (by status):")
        total_active = 0
        for c in counts:
            print(f"  {c['status']:<24}  {c['n']}")
            total_active += c["n"]
        print(f"  {'TOTAL':<24}  {total_active}")
        if backlog > 0:
            print(f"  (backlog/not-pursuing: {backlog})")
        print()


def list_jobs():
    init_db()

    with get_connection() as conn:
        jobs = conn.execute(
            """
            SELECT * FROM jobs
            ORDER BY
                CASE worth_pursuing
                    WHEN 'yes' THEN 0
                    WHEN 'unsure' THEN 1
                    ELSE 2
                END,
                id
            """
        ).fetchall()
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
        flag = ""
        if job["worth_pursuing"] == "no":
            flag = "  [BACKLOG]"
        elif job["worth_pursuing"] == "unsure":
            flag = "  [?]"

        print(f"  [{job['id']:>3}] {job['status']:<24}  {job['title']}  @  {job['company']}{flag}")
        if job["link"]:
            print(f"        {job['link']}")
        if job["next_action_at"] and job["worth_pursuing"] != "no":
            print(f"        DUE {job['next_action_at']}: {job['next_action_note']}")

        for c in contacts_by_job.get(job["id"], []):
            details = [d for d in (c["role"], c["email"], c["phone"]) if d]
            line = f"          -> [c{c['id']}] {c['name']}"
            if details:
                line += "  (" + "  |  ".join(details) + ")"
            print(line)
    print()


def cmd_show(job_id):
    init_db()
    with get_connection() as conn:
        job = _require_job(conn, job_id)
        contacts = conn.execute(
            "SELECT * FROM contacts WHERE job_id = ? ORDER BY id", (job_id,)
        ).fetchall()
        events = conn.execute(
            "SELECT * FROM events WHERE job_id = ? ORDER BY occurred_at", (job_id,)
        ).fetchall()

    print(f"\n=== JOB #{job['id']}: {job['title']} @ {job['company']} ===")
    print(f"Status:           {job['status']}")
    print(f"Worth pursuing:   {job['worth_pursuing']}")
    if job["next_action_at"]:
        print(f"Next action:      {job['next_action_at']} - {job['next_action_note']}")
    if job["link"]:
        print(f"Link:             {job['link']}")
    print(f"Added:            {job['added_at']}")
    if job["last_activity_at"]:
        print(f"Last activity:    {job['last_activity_at']}")
    if job["notes"]:
        print(f"Notes:            {job['notes']}")

    if contacts:
        print(f"\nContacts ({len(contacts)}):")
        for c in contacts:
            print(f"  [c{c['id']}] {c['name']} ({c['role']})")
            if c["email"]:
                print(f"        email: {c['email']}")
            if c["phone"]:
                print(f"        phone: {c['phone']}")
            if c["linkedin_url"]:
                print(f"        linkedin: {c['linkedin_url']}")
            if c["notes"]:
                print(f"        notes: {c['notes']}")

    if events:
        print(f"\nActivity log ({len(events)} events):")
        for e in events:
            print(f"  {e['occurred_at']}  {e['event_type']:<22}  {e['body'] or ''}")
    print()


def usage():
    print("Usage: python3 tracker.py <command> [args]")
    print("Commands:")
    print("  add                                Add a new job (interactive)")
    print("  list                               Show all jobs + contacts + next actions")
    print("  show <job_id>                      Show one job in full (contacts + timeline)")
    print("  today                              Action items due today + upcoming + pipeline")
    print("  contact <job_id>                   Add a contact to a job (interactive)")
    print("  status <job_id> <new_status>       Change a job's status (logs event)")
    print("  action <job_id> <YYYY-MM-DD> <note>")
    print("                                     Set next action date + note for a job")
    print("  event  <job_id> <event_type> <body>")
    print("                                     Log a freeform activity event")
    print("  pursue <job_id> yes|no|unsure      Mark job as worth pursuing or not")


def main():
    if len(sys.argv) < 2:
        usage()
        sys.exit(1)

    command = sys.argv[1]

    if command == "add":
        add_job()
    elif command == "list":
        list_jobs()
    elif command == "today":
        cmd_today()
    elif command == "show":
        if len(sys.argv) < 3:
            print("Usage: python3 tracker.py show <job_id>")
            sys.exit(1)
        cmd_show(int(sys.argv[2]))
    elif command == "contact":
        if len(sys.argv) < 3:
            print("Usage: python3 tracker.py contact <job_id>")
            sys.exit(1)
        add_contact(int(sys.argv[2]))
    elif command == "status":
        if len(sys.argv) < 4:
            print("Usage: python3 tracker.py status <job_id> <new_status>")
            sys.exit(1)
        cmd_status(int(sys.argv[2]), sys.argv[3])
    elif command == "action":
        if len(sys.argv) < 5:
            print('Usage: python3 tracker.py action <job_id> <YYYY-MM-DD> "<note>"')
            sys.exit(1)
        cmd_action(int(sys.argv[2]), sys.argv[3], sys.argv[4])
    elif command == "event":
        if len(sys.argv) < 5:
            print('Usage: python3 tracker.py event <job_id> <event_type> "<body>"')
            sys.exit(1)
        cmd_event(int(sys.argv[2]), sys.argv[3], sys.argv[4])
    elif command == "pursue":
        if len(sys.argv) < 4:
            print("Usage: python3 tracker.py pursue <job_id> yes|no|unsure")
            sys.exit(1)
        cmd_pursue(int(sys.argv[2]), sys.argv[3])
    else:
        print(f"Unknown command: {command}\n")
        usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
