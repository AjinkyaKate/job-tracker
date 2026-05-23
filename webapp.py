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

        status_counts = conn.execute(
            """
            SELECT status, COUNT(*) AS n FROM jobs
            WHERE worth_pursuing IS NULL OR worth_pursuing != 'no'
            GROUP BY status ORDER BY n DESC
            """
        ).fetchall()

        backlog_count = conn.execute(
            "SELECT COUNT(*) AS n FROM jobs WHERE worth_pursuing = 'no'"
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
            "status_counts": _rows_to_dicts(status_counts),
            "backlog_count": backlog_count,
            "total_active": len(jobs_with_contacts) - backlog_count,
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

    return TEMPLATES.TemplateResponse(
        "job_detail.html",
        {
            "request": request,
            "job": dict(job),
            "contacts": _rows_to_dicts(contacts),
            "events": _rows_to_dicts(events),
        },
    )
