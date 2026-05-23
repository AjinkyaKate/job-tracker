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
from fastapi import Body, Depends, FastAPI, HTTPException, Request, status
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


PIPELINE_STATUSES = [
    {"key": "saved",     "label": "Saved",     "color": "#9aa0a6"},
    {"key": "applied",   "label": "Applied",   "color": "#4b8df8"},
    {"key": "replied",   "label": "Replied",   "color": "#f5a524"},
    {"key": "interview", "label": "Interview", "color": "#22c55e"},
    {"key": "offer",     "label": "Offer",     "color": "#10b981"},
    {"key": "rejected",  "label": "Rejected",  "color": "#ef4444"},
    {"key": "backlog",   "label": "Backlog",   "color": "#6b7280"},
]


def _enrich_job(job_dict, today, contacts_by_job, drafts_by_job):
    """Add kanban-ready computed fields to a job dict."""
    company = job_dict.get("company") or "?"
    # Initials: take first letter of first two words (cap at 2 chars)
    words = [w for w in company.split() if w[0].isalnum()]
    if len(words) >= 2:
        ini = (words[0][0] + words[1][0]).upper()
    else:
        ini = company[:2].upper()

    pursue = job_dict.get("worth_pursuing")
    fit = 78 if pursue == "yes" else (50 if pursue == "unsure" else 22)

    next_at = job_dict.get("next_action_at")
    is_backlog = pursue == "no"
    is_overdue = bool(next_at and next_at < today and not is_backlog)
    days_overdue = 0
    if is_overdue:
        try:
            d1 = datetime.strptime(next_at, "%Y-%m-%d").date()
            d2 = datetime.fromisoformat(today).date()
            days_overdue = (d2 - d1).days
        except Exception:
            pass

    contacts = contacts_by_job.get(job_dict["id"], [])
    drafts = drafts_by_job.get(job_dict["id"], 0)

    job_dict["ini"] = ini
    job_dict["fit"] = fit
    job_dict["contacts"] = contacts
    job_dict["contact_count"] = len(contacts)
    job_dict["warm_count"] = len(contacts)  # placeholder; real metric in Phase 3
    job_dict["is_overdue"] = is_overdue
    job_dict["days_overdue"] = days_overdue
    job_dict["draft_count"] = drafts
    # Activity preview: prefer next_action_note (so card carries something useful)
    job_dict["activity_preview"] = (
        job_dict.get("next_action_note")
        or job_dict.get("notes", "")[:80]
        or ""
    )[:120]
    return job_dict


@app.get("/", response_class=HTMLResponse)
def homepage(request: Request):
    tracker.init_db()
    today = datetime.now().date().isoformat()

    with get_connection() as conn:
        jobs_rows = conn.execute("SELECT * FROM jobs ORDER BY id").fetchall()
        contacts_rows = conn.execute("SELECT * FROM contacts ORDER BY job_id, id").fetchall()
        drafts_rows = conn.execute(
            """
            SELECT job_id, COUNT(*) AS n FROM events
            WHERE event_type = 'note'
              AND (body LIKE 'SUGGESTED%' OR body LIKE 'OPTIONAL%')
            GROUP BY job_id
            """
        ).fetchall()

    contacts_by_job = {}
    for c in contacts_rows:
        contacts_by_job.setdefault(c["job_id"], []).append(dict(c))
    drafts_by_job = {r["job_id"]: r["n"] for r in drafts_rows}

    jobs = [_enrich_job(dict(j), today, contacts_by_job, drafts_by_job) for j in jobs_rows]

    # Stats
    status_counts = {s["key"]: 0 for s in PIPELINE_STATUSES}
    overdue_count = 0
    drafts_pending = 0
    due_today_count = 0
    upcoming_count = 0
    offer_count = 0
    for j in jobs:
        status_counts[j["status"]] = status_counts.get(j["status"], 0) + 1
        if j["is_overdue"]:
            overdue_count += 1
        if j.get("draft_count") and j.get("worth_pursuing") != "no":
            drafts_pending += j["draft_count"]
        next_at = j.get("next_action_at")
        if next_at and j.get("worth_pursuing") != "no":
            if next_at <= today:
                due_today_count += 1
            else:
                # Upcoming = within 7 days
                try:
                    d1 = datetime.strptime(next_at, "%Y-%m-%d").date()
                    d2 = datetime.fromisoformat(today).date()
                    if (d1 - d2).days <= 7:
                        upcoming_count += 1
                except Exception:
                    pass
        if j["status"] == "offer":
            offer_count += 1

    backlog_count = status_counts.get("backlog", 0)
    total_active = sum(c for s, c in status_counts.items() if s != "backlog")

    # Group jobs by status (preserve PIPELINE_STATUSES order)
    by_status = {s["key"]: [] for s in PIPELINE_STATUSES}
    for j in jobs:
        if j["status"] in by_status:
            by_status[j["status"]].append(j)
        else:
            # Unknown status falls into Saved
            by_status["saved"].append(j)

    # Gmail integration status for top-bar Sync button
    gmail_state = {
        "configured": gmail_integration.is_configured(),
        "authorized": False,
        "last_sync": None,
    }
    if gmail_state["configured"]:
        with get_connection() as conn:
            creds = gmail_integration.load_credentials(conn)
            gmail_state["authorized"] = creds is not None
            gmail_state["last_sync"] = gmail_integration.get_last_sync(conn)

    return TEMPLATES.TemplateResponse(
        "index.html",
        {
            "request": request,
            "today": today,
            "jobs": jobs,
            "by_status": by_status,
            "statuses": PIPELINE_STATUSES,
            "status_counts": status_counts,
            "overdue_count": overdue_count,
            "due_today_count": due_today_count,
            "upcoming_count": upcoming_count,
            "offer_count": offer_count,
            "backlog_count": backlog_count,
            "total_active": total_active,
            "drafts_pending": drafts_pending,
            "gmail": gmail_state,
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
# Job mutations (used by kanban drag-and-drop + future Add Job modal)
# ─────────────────────────────────────────────────────────────────────────────


@app.post("/jobs/{job_id}/status")
def update_job_status(job_id: int, payload: dict = Body(...)):
    """Change a job's status — used by drag-and-drop in the kanban view.

    Body: {"status": "applied"}.
    Side effects: updates jobs.status + jobs.last_activity_at, appends a
    status_change event to the events table.
    """
    new_status = (payload or {}).get("status")
    if not new_status or not isinstance(new_status, str):
        return JSONResponse(
            status_code=400,
            content={"error": "missing_status", "message": "Body must be {\"status\": \"<new>\"}."},
        )
    new_status = new_status.strip()

    tracker.init_db()
    now = datetime.now().isoformat(timespec="seconds")

    with get_connection() as conn:
        job = conn.execute(
            "SELECT id, status FROM jobs WHERE id = ?", (job_id,)
        ).fetchone()
        if not job:
            return JSONResponse(
                status_code=404,
                content={"error": "not_found", "message": f"Job #{job_id} not found"},
            )
        old_status = job["status"]
        if old_status == new_status:
            return {"ok": True, "id": job_id, "status": new_status, "changed": False}

        conn.execute(
            "UPDATE jobs SET status = ?, last_activity_at = ? WHERE id = ?",
            (new_status, now, job_id),
        )
        conn.execute(
            "INSERT INTO events (job_id, event_type, body, occurred_at, recorded_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (job_id, "status_change", f"{old_status} -> {new_status}", now, now),
        )

    return {
        "ok": True,
        "id": job_id,
        "from": old_status,
        "to": new_status,
        "changed": True,
    }


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
    """Manually trigger a Gmail → tracker sync of LinkedIn notification emails.

    Steps (handled inside gmail_integration.sync_to_tracker):
    1. Load Gmail credentials from oauth_tokens table
    2. Read last_gmail_sync from sync_state (default: 7 days ago)
    3. Gmail API messages.list with q='from:linkedin.com after:{ts}'
    4. For each new message: parse subject, fuzzy-match person to contact,
       INSERT event into events table, mark message processed
    5. Update last_gmail_sync
    """
    if not gmail_integration.is_configured():
        return _gmail_not_configured_response()
    try:
        tracker.init_db()
        with get_connection() as conn:
            result = gmail_integration.sync_to_tracker(conn)
        if not result.get("ok"):
            return JSONResponse(status_code=400, content=result)
        return result
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"error": "sync_failed", "message": str(exc)},
        )


@app.get("/gmail/status")
def gmail_status():
    """Reports Gmail integration state — used by the dashboard's Sync widget."""
    configured = gmail_integration.is_configured()
    authorized = False
    last_sync = None
    if configured:
        tracker.init_db()
        with get_connection() as conn:
            creds = gmail_integration.load_credentials(conn)
            authorized = creds is not None
            last_sync = gmail_integration.get_last_sync(conn)
    return {
        "configured": configured,
        "authorized": authorized,
        "last_sync": last_sync,
    }


