import sqlite3
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

import tracker

DB_FILE = "tracker.db"
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(
    title="Job Tracker",
    description="Personal job-application command center.",
)


def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _rows_to_dicts(rows):
    return [dict(r) for r in rows]


def _is_draft_event(event):
    if event.get("event_type") != "note":
        return False
    body = event.get("body") or ""
    first_line = body.split("\n", 1)[0]
    return "SUGGESTED" in first_line or "OPTIONAL" in first_line


def _parse_draft(body):
    """Split a 'SUGGESTED ... :' or 'OPTIONAL ... :' note into (label, message)."""
    if not body:
        return "Draft", ""
    parts = body.split("\n\n", 1)
    if len(parts) < 2:
        return body[:80], body

    label = parts[0].rstrip(":").rstrip().rstrip(" -")
    for prefix in ("SUGGESTED ", "OPTIONAL "):
        if label.startswith(prefix):
            label = label[len(prefix):]
            break

    msg_lines = parts[1].strip().split("\n")
    while msg_lines and msg_lines[-1].strip().startswith("(") and ")" in msg_lines[-1]:
        msg_lines.pop()
    message = "\n".join(msg_lines).strip()
    return label, message


@app.get("/", response_class=HTMLResponse)
def homepage(request: Request):
    tracker.init_db()
    today = datetime.now().date().isoformat()

    with get_connection() as conn:
        due = conn.execute(
            """
            SELECT * FROM jobs
            WHERE next_action_at IS NOT NULL
              AND next_action_at <= ?
              AND (worth_pursuing IS NULL OR worth_pursuing != 'no')
            ORDER BY next_action_at
            """,
            (today,),
        ).fetchall()

        upcoming = conn.execute(
            """
            SELECT * FROM jobs
            WHERE next_action_at IS NOT NULL
              AND next_action_at > ?
              AND (worth_pursuing IS NULL OR worth_pursuing != 'no')
            ORDER BY next_action_at
            LIMIT 5
            """,
            (today,),
        ).fetchall()

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

        backlog_count = conn.execute(
            "SELECT COUNT(*) AS n FROM jobs WHERE worth_pursuing = 'no'"
        ).fetchone()["n"]

        # count of pending draft messages across all active jobs (worth_pursuing != 'no')
        drafts_pending = conn.execute(
            """
            SELECT COUNT(*) AS n FROM events e
            JOIN jobs j ON j.id = e.job_id
            WHERE e.event_type = 'note'
              AND (e.body LIKE 'SUGGESTED%' OR e.body LIKE 'OPTIONAL%')
              AND (j.worth_pursuing IS NULL OR j.worth_pursuing != 'no')
            """
        ).fetchone()["n"]

    contacts_by_job = {}
    for c in contacts:
        contacts_by_job.setdefault(c["job_id"], []).append(dict(c))

    jobs_with_contacts = []
    for j in jobs:
        d = dict(j)
        d["contacts"] = contacts_by_job.get(j["id"], [])
        d["is_overdue"] = (
            d.get("next_action_at") is not None
            and d["next_action_at"] < today
            and d.get("worth_pursuing") != "no"
        )
        jobs_with_contacts.append(d)

    return TEMPLATES.TemplateResponse(
        "index.html",
        {
            "request": request,
            "today": today,
            "due": _rows_to_dicts(due),
            "upcoming": _rows_to_dicts(upcoming),
            "jobs": jobs_with_contacts,
            "backlog_count": backlog_count,
            "total_active": len(jobs_with_contacts) - backlog_count,
            "drafts_pending": drafts_pending,
        },
    )


@app.get("/jobs/{job_id}", response_class=HTMLResponse)
def job_detail(job_id: int, request: Request):
    tracker.init_db()
    with get_connection() as conn:
        job = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if not job:
            return HTMLResponse(
                f"<h1>Job #{job_id} not found</h1><a href='/'>back</a>",
                status_code=404,
            )
        contacts = conn.execute(
            "SELECT * FROM contacts WHERE job_id = ? ORDER BY id", (job_id,)
        ).fetchall()
        events = conn.execute(
            "SELECT * FROM events WHERE job_id = ? ORDER BY occurred_at",
            (job_id,),
        ).fetchall()

    contacts_dicts = _rows_to_dicts(contacts)
    contact_by_id = {c["id"]: c for c in contacts_dicts}

    drafts = []
    other_events = []
    for raw in events:
        e = dict(raw)
        if _is_draft_event(e):
            label, message = _parse_draft(e.get("body") or "")
            e["label"] = label
            e["message"] = message
            cid = e.get("contact_id")
            e["contact_name"] = contact_by_id[cid]["name"] if cid in contact_by_id else None
            e["contact_linkedin"] = contact_by_id[cid].get("linkedin_url") if cid in contact_by_id else None
            drafts.append(e)
        else:
            other_events.append(e)

    return TEMPLATES.TemplateResponse(
        "job_detail.html",
        {
            "request": request,
            "job": dict(job),
            "contacts": contacts_dicts,
            "events": other_events,
            "drafts": drafts,
        },
    )
