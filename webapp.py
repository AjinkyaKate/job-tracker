import os
import re
import secrets
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import markdown as md_lib
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates

import gmail_integration
import tracker

DB_FILE = os.environ.get("DB_FILE", "tracker.db")
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")
PORT_ENV = os.environ.get("PORT")

# Production guard: Railway and most PaaS hosts set $PORT. If we detect that and
# auth env vars are missing, fail loudly at import time so we never accidentally
# expose personal data to the open internet.
if PORT_ENV and (not ADMIN_USERNAME or not ADMIN_PASSWORD):
    raise RuntimeError(
        "Detected production deploy ($PORT is set) but ADMIN_USERNAME or "
        "ADMIN_PASSWORD env var is missing. Set both in your platform's "
        "environment variables before deploying — this is the only auth in "
        "front of personal job-hunt data."
    )

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# auto_error=False lets us see the absence of credentials in our handler
# instead of being auto-rejected with 401 before we can check local-dev mode
security = HTTPBasic(auto_error=False)


def require_auth(credentials: Optional[HTTPBasicCredentials] = Depends(security)):
    if not ADMIN_USERNAME or not ADMIN_PASSWORD:
        return  # local dev: no auth configured, allow all
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Basic"},
        )
    correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


# Global auth dependency — covers every route incl. /docs and /openapi.json
app = FastAPI(
    title="Job Tracker",
    description="Personal job-application command center.",
    dependencies=[Depends(require_auth)],
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


def _slugify_for_filename(value: str) -> str:
    """Collapse non-alphanumeric runs to underscores; trim leading/trailing underscores."""
    if not value:
        return ""
    return re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_")


@app.get("/jobs/{job_id}/resume", response_class=HTMLResponse)
def job_resume(job_id: int, request: Request):
    tracker.init_db()
    with get_connection() as conn:
        job = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if not job:
            return HTMLResponse(
                f"<h1>Job #{job_id} not found</h1><a href='/'>back</a>",
                status_code=404,
            )

    job_dict = dict(job)
    resume_md = job_dict.get("resume_md") or ""

    if resume_md.strip():
        resume_html = md_lib.markdown(
            resume_md,
            extensions=["extra", "sane_lists"],
        )
    else:
        resume_html = None

    company_slug = _slugify_for_filename(job_dict.get("company") or "company")
    title_slug = _slugify_for_filename(job_dict.get("title") or "role")
    pdf_filename = f"Ajinkya_Kate_{company_slug}_{title_slug}.pdf"

    return TEMPLATES.TemplateResponse(
        "resume.html",
        {
            "request": request,
            "job": job_dict,
            "resume_html": resume_html,
            "pdf_filename": pdf_filename,
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# Phase 3 — Gmail OAuth routes (stubs; see GMAIL_SETUP.md)
# ─────────────────────────────────────────────────────────────────────────────

def _gmail_not_configured_response():
    return JSONResponse(
        status_code=503,
        content={
            "error": "gmail_not_configured",
            "message": (
                "Gmail integration is not yet configured. Set GOOGLE_CLIENT_ID "
                "and GOOGLE_CLIENT_SECRET in .env and restart. See GMAIL_SETUP.md."
            ),
        },
    )


@app.get("/auth/gmail/start")
def gmail_oauth_start():
    """Step 1 of OAuth: redirect the user to Google's consent screen."""
    if not gmail_integration.is_configured():
        return _gmail_not_configured_response()
    auth_url = gmail_integration.build_authorize_url()
    return RedirectResponse(url=auth_url, status_code=302)


@app.get("/auth/gmail/callback")
def gmail_oauth_callback(code: str = "", state: str = "", error: str = ""):
    """Step 2 of OAuth: Google redirects back with a code. We exchange + store.

    Phase 3 ship 2/3 will complete the token-storage path. Right now we just
    confirm the round-trip works and surface the result.
    """
    if error:
        return JSONResponse(
            status_code=400,
            content={"error": "oauth_denied", "message": f"Google returned: {error}"},
        )
    if not code:
        return JSONResponse(
            status_code=400,
            content={"error": "no_code", "message": "Missing authorization code"},
        )
    if not gmail_integration.is_configured():
        return _gmail_not_configured_response()
    try:
        creds = gmail_integration.exchange_code_for_token(code)
        with get_connection() as conn:
            gmail_integration.store_credentials(conn, creds)
        return HTMLResponse(
            "<h1>Gmail connected ✓</h1>"
            "<p>Tokens stored locally. <a href='/'>back to dashboard</a></p>",
            status_code=200,
        )
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"error": "exchange_failed", "message": str(exc)},
        )


@app.post("/gmail/sync")
def gmail_sync_now():
    """Manually trigger a Gmail → tracker sync of LinkedIn emails.

    Phase 3 ship 3/3 will implement the parser + matcher. For now, returns
    501 with a helpful message.
    """
    if not gmail_integration.is_configured():
        return _gmail_not_configured_response()
    return JSONResponse(
        status_code=501,
        content={
            "error": "not_implemented_yet",
            "message": "Gmail sync engine ships in Phase 3 ship 3/3 (next next turn).",
        },
    )


