import os
import re
import secrets
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
import llm_helpers
import tracker
from db import get_connection
from db import insert_returning_id

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


PUBLIC_PATHS = {"/healthz"}  # bypass auth — Render's probe doesn't send credentials


def require_auth(
    request: Request,
    credentials: Optional[HTTPBasicCredentials] = Depends(security),
):
    if request.url.path in PUBLIC_PATHS:
        return  # health check probe — let it through unauthenticated
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


@app.get("/healthz")
def healthz():
    """Public liveness probe for Render. Auth-bypassed via PUBLIC_PATHS."""
    return {"ok": True}


@app.get("/debug/gemini-probe")
def gemini_probe():
    """Diagnose why Gemini classification returns None on every email."""
    import os
    out = {"GEMINI_API_KEY_set": bool(os.environ.get("GEMINI_API_KEY")),
           "GEMINI_API_KEY_prefix": (os.environ.get("GEMINI_API_KEY", "")[:8] + "..." if os.environ.get("GEMINI_API_KEY") else None)}
    try:
        import email_analyzer
        out["is_available"] = email_analyzer.is_available()
        out["genai_module_loaded"] = email_analyzer._GENAI_AVAILABLE
    except Exception as e:
        out["import_error"] = f"{type(e).__name__}: {e}"
        return out

    if not email_analyzer.is_available():
        out["error"] = "email_analyzer.is_available() returned False"
        return out

    # Try a simple Gemini call with minimal prompt
    try:
        from google import genai
        from google.genai import types as t
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        # First: list available models to see what we have access to
        try:
            models = [m.name for m in client.models.list()][:10]
            out["available_models_sample"] = models
        except Exception as e:
            out["list_models_error"] = f"{type(e).__name__}: {e}"
        # Try a simple generation
        try:
            r = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=["Say 'pong' in JSON: {\"reply\": \"pong\"}"],
                config=t.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.0,
                ),
            )
            out["simple_call_ok"] = True
            out["simple_call_response"] = r.text[:200] if hasattr(r, 'text') else str(r)[:200]
        except Exception as e:
            out["simple_call_error"] = f"{type(e).__name__}: {str(e)[:500]}"
        # Try the actual analyze_email call
        try:
            result = email_analyzer.analyze_email(
                "Thank you for applying to Global Payments",
                "no-reply@globalpayments.com",
                "Hello, Thank you for your interest in the Associate Product Owner position.",
                [{"id": 32, "company": "Global Payments Inc.", "title": "APO", "status": "saved"}],
            )
            out["analyze_email_ok"] = result is not None
            if result:
                out["analyze_email_result"] = {
                    "is_job_related": result.is_job_related,
                    "matched_job_id": result.matched_job_id,
                    "event_type": result.event_type,
                    "target_status": result.target_status,
                    "summary": result.summary,
                    "confidence": result.confidence,
                }
            else:
                out["analyze_email_result"] = None
        except Exception as e:
            out["analyze_email_error"] = f"{type(e).__name__}: {str(e)[:500]}"
    except Exception as e:
        out["outer_error"] = f"{type(e).__name__}: {e}"
    return out


@app.get("/debug/gmail-probe")
def gmail_probe():
    """Diagnostic: bypass our fetch wrapper and call Gmail directly.

    Returns what Gmail's messages.list actually returns from inside Render.
    Compare against the local result to localize where the bug is.
    """
    from datetime import datetime, timedelta, timezone
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    out = {"steps": []}
    try:
        tracker.init_db()
        with get_connection() as conn:
            creds = gmail_integration.load_credentials(conn)
        if not creds:
            out["error"] = "no_credentials"
            return out
        out["steps"].append("loaded_credentials")
        out["creds_expired_initial"] = creds.expired
        out["creds_has_refresh"] = bool(creds.refresh_token)
        out["creds_expiry"] = str(creds.expiry) if creds.expiry else None
        # Force a fresh refresh
        creds.refresh(Request())
        out["steps"].append("refreshed_token")
        out["creds_expired_after_refresh"] = creds.expired
        out["new_expiry"] = str(creds.expiry)
        # Build service
        service = build("gmail", "v1", credentials=creds, cache_discovery=False)
        out["steps"].append("built_service")
        # Try same query as deployed sync
        ts_7d = int((datetime.now(timezone.utc) - timedelta(days=7)).timestamp())
        for q in [
            f"in:inbox after:{ts_7d}",
            f"after:{ts_7d}",
            "newer_than:7d",
            "in:inbox",
        ]:
            r = service.users().messages().list(
                userId="me", q=q, maxResults=5,
            ).execute()
            out.setdefault("queries", []).append({
                "q": q,
                "resultSizeEstimate": r.get("resultSizeEstimate"),
                "msg_count": len(r.get("messages", [])),
                "first_id": r.get("messages", [{}])[0].get("id") if r.get("messages") else None,
            })
        out["steps"].append("ran_queries")
        # Also pull profile to verify creds-> account binding
        prof = service.users().getProfile(userId="me").execute()
        out["profile"] = {
            "emailAddress": prof.get("emailAddress"),
            "messagesTotal": prof.get("messagesTotal"),
            "historyId": prof.get("historyId"),
        }
        out["ok"] = True
    except Exception as exc:
        out["error"] = f"{type(exc).__name__}: {exc}"
        out["ok"] = False
    return out


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
            "statuses": PIPELINE_STATUSES,
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
    """Step 1 of OAuth: redirect the user to Google's consent screen.

    Also persists the PKCE code_verifier so the /callback handler can complete
    the token exchange.
    """
    if not gmail_integration.is_configured():
        return _gmail_not_configured_response()
    tracker.init_db()
    with get_connection() as conn:
        auth_url = gmail_integration.build_authorize_url(conn)
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
        with get_connection() as conn:
            creds = gmail_integration.exchange_code_for_token(conn, code, state)
            gmail_integration.store_credentials(conn, creds)
        return HTMLResponse(
            "<h1>Gmail connected ✓</h1>"
            "<p>Tokens stored. <a href='/'>back to dashboard</a></p>",
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




# ─────────────────────────────────────────────────────────────────────────────
# Add Job · Resume Studio · DM Studio  (LLM-powered authoring features)
# ─────────────────────────────────────────────────────────────────────────────

from pydantic import BaseModel
from typing import Optional as _Opt
from fastapi import Form


class ExtractedJob(BaseModel):
    """Schema Gemini fills from a pasted JD."""
    company: str
    title: str
    location: _Opt[str] = None
    level: _Opt[str] = None
    yoe_required: _Opt[str] = None
    must_have_skills: _Opt[str] = None
    nice_to_have_skills: _Opt[str] = None
    comp_range: _Opt[str] = None
    source: _Opt[str] = None
    jd_summary: str


JD_EXTRACT_PROMPT = """You're extracting structured fields from a pasted job-description for a personal job-tracker.

Required fields:
- company: the hiring company name (clean — no LLC/Inc unless distinctive)
- title: the role title as worded in the JD
- location: city/region + (Remote/Hybrid/On-site) if mentioned, or null
- level: junior / associate / mid / senior / lead / principal — whichever fits
- yoe_required: years of experience required (e.g. "2+ yrs" / "0-2 yrs" / "5-7 yrs")
- must_have_skills: comma-separated CORE skills the JD calls out
- nice_to_have_skills: comma-separated nice-to-haves
- comp_range: if disclosed (e.g. "₹15-25 LPA" or "$120K-160K"), else null
- source: 'linkedin' (default) or company portal name
- jd_summary: 1-2 sentence plain-English summary of what the role is + what they're looking for

Be conservative — return null for fields the JD doesn't actually mention. Don't invent."""


@app.get("/add-job", response_class=HTMLResponse)
def add_job_page(request: Request):
    return TEMPLATES.TemplateResponse("add_job.html", {"request": request})


@app.post("/add-job", response_class=HTMLResponse)
def add_job_submit(
    request: Request,
    link: str = Form(""),
    company: str = Form(""),
    title: str = Form(""),
    jd_text: str = Form(...),
):
    form = {"link": link, "company": company, "title": title, "jd_text": jd_text}
    if not jd_text or len(jd_text) < 50:
        return TEMPLATES.TemplateResponse("add_job.html", {
            "request": request, "form": form,
            "error": "JD text is too short — paste the full job description.",
        })

    if not llm_helpers.is_available():
        # Fall back: just insert with whatever the user typed manually
        try:
            tracker.init_db()
            now_iso = datetime.now().isoformat(timespec="seconds")
            with get_connection() as conn:
                new_id = insert_returning_id(
                    conn,
                    "INSERT INTO jobs (title, company, link, status, worth_pursuing, source, "
                    "jd_raw_text, added_at, last_activity_at) "
                    "VALUES (?, ?, ?, 'saved', 'unsure', 'manual', ?, ?, ?)",
                    (title or "(untitled)", company or "(unknown)", link, jd_text, now_iso, now_iso),
                )
            return RedirectResponse(f"/jobs/{new_id}", status_code=303)
        except Exception as exc:
            return TEMPLATES.TemplateResponse("add_job.html", {
                "request": request, "form": form,
                "error": f"Insert failed: {exc}",
            })

    # Gemini path
    try:
        extracted = llm_helpers.gemini_json(
            JD_EXTRACT_PROMPT,
            f"JD to extract from:\n\n{jd_text}",
            schema=ExtractedJob,
        )
    except Exception as exc:
        return TEMPLATES.TemplateResponse("add_job.html", {
            "request": request, "form": form,
            "error": f"Gemini extraction failed: {type(exc).__name__}: {str(exc)[:300]}. Try again, or fill the form manually if Gemini quota is exhausted.",
        })

    # Override with user-provided values where present
    company_final = company.strip() or extracted.company
    title_final = title.strip() or extracted.title

    tracker.init_db()
    now_iso = datetime.now().isoformat(timespec="seconds")
    try:
        with get_connection() as conn:
            new_id = insert_returning_id(
                conn,
                "INSERT INTO jobs (title, company, link, status, worth_pursuing, location, level, "
                "yoe_required, source, must_have_skills, nice_to_have_skills, comp_range, "
                "jd_raw_text, jd_summary, added_at, last_activity_at) "
                "VALUES (?, ?, ?, 'saved', 'unsure', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (title_final, company_final, link, extracted.location, extracted.level,
                 extracted.yoe_required, extracted.source or "linkedin",
                 extracted.must_have_skills, extracted.nice_to_have_skills,
                 extracted.comp_range, jd_text, extracted.jd_summary, now_iso, now_iso),
            )
            conn.execute(
                "INSERT INTO events (job_id, event_type, body, occurred_at, recorded_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (new_id, "job_added", f"Added via /jobs/new — Gemini-extracted from JD", now_iso, now_iso),
            )
    except Exception as exc:
        return TEMPLATES.TemplateResponse("add_job.html", {
            "request": request, "form": form, "preview": extracted.model_dump(),
            "error": f"Insert failed: {exc}",
        })

    return RedirectResponse(f"/jobs/{new_id}", status_code=303)


# ─── Resume Studio ────────────────────────────────────────────────────────

RESUME_TAILOR_PROMPT = """You're tailoring a candidate's resume for a specific job application.

CRITICAL RULES:
- Output ONLY the resume markdown. No commentary, no "Why X" sections, no strategic notes for the candidate.
- A recruiter reads this resume directly — never write content that addresses the candidate.
- Keep total length around 3500-4500 chars (1 page printed).
- Preserve the candidate's actual experience, education, certifications — never invent companies, roles, or dates.
- Adjust the SUMMARY (1-2 sentences at top) to mirror what the JD prioritises.
- Adjust BULLET POINTS in Experience to emphasise the most JD-relevant work the candidate has done.
- Skills section should reorder to put JD-relevant skills first.
- Use markdown: ## headers, ** for bold, - for bullets.
- Sections in order: Summary, Experience, Projects (optional), Skills, Education, Certifications.

The candidate is Ajinkya Kate. Use the provided base resume as the source of truth for facts."""


@app.get("/jobs/{job_id}/resume-studio", response_class=HTMLResponse)
def resume_studio_page(job_id: int, request: Request):
    tracker.init_db()
    with get_connection() as conn:
        job_row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if not job_row:
        return HTMLResponse(f"<h1>Job #{job_id} not found</h1><a href='/'>back</a>", status_code=404)
    job = dict(job_row)
    return TEMPLATES.TemplateResponse("resume_studio.html", {
        "request": request, "job": job,
        "current_len": len(job.get("resume_md") or ""),
        "new_resume_md": "",
    })


@app.post("/jobs/{job_id}/resume-studio", response_class=HTMLResponse)
def resume_studio_submit(
    job_id: int, request: Request,
    action: str = Form(...),
    new_resume_md: str = Form(""),
):
    tracker.init_db()
    with get_connection() as conn:
        job_row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if not job_row:
        return HTMLResponse(f"<h1>Job #{job_id} not found</h1>", status_code=404)
    job = dict(job_row)

    if action == "save":
        if not new_resume_md.strip():
            return TEMPLATES.TemplateResponse("resume_studio.html", {
                "request": request, "job": job,
                "current_len": len(job.get("resume_md") or ""),
                "new_resume_md": new_resume_md,
                "error": "Resume content is empty — nothing to save.",
            })
        now_iso = datetime.now().isoformat(timespec="seconds")
        with get_connection() as conn:
            conn.execute(
                "UPDATE jobs SET resume_md = ?, last_activity_at = ? WHERE id = ?",
                (new_resume_md, now_iso, job_id),
            )
            conn.execute(
                "INSERT INTO events (job_id, event_type, body, occurred_at, recorded_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (job_id, "note", f"Resume saved via Resume Studio ({len(new_resume_md)} chars)", now_iso, now_iso),
            )
        return RedirectResponse(f"/jobs/{job_id}/resume", status_code=303)

    # action == "regenerate"
    if not job.get("jd_raw_text"):
        return TEMPLATES.TemplateResponse("resume_studio.html", {
            "request": request, "job": job,
            "current_len": len(job.get("resume_md") or ""),
            "new_resume_md": "",
            "error": "No JD text on this job — Gemini needs the JD to tailor. Edit the job and paste the JD first.",
        })

    if not llm_helpers.is_available():
        return TEMPLATES.TemplateResponse("resume_studio.html", {
            "request": request, "job": job,
            "current_len": len(job.get("resume_md") or ""),
            "new_resume_md": "",
            "error": "GEMINI_API_KEY not configured.",
        })

    # Use peopleHum's resume (Job #19) as canonical base if this job has no current resume
    with get_connection() as conn:
        base_row = conn.execute("SELECT resume_md FROM jobs WHERE id = 19").fetchone()
    base_resume = (job.get("resume_md") or "").strip() or (base_row["resume_md"] if base_row else "")

    user_content = (
        f"# JOB DESCRIPTION\n\n{job.get('jd_raw_text', '')[:4000]}\n\n"
        f"# JOB METADATA\n\nCompany: {job.get('company')}\nTitle: {job.get('title')}\n"
        f"Location: {job.get('location')}\nLevel: {job.get('level')}\n"
        f"YoE required: {job.get('yoe_required')}\n\n"
        f"# CANDIDATE'S CURRENT RESUME (base — use as factual source of truth)\n\n{base_resume}"
    )

    try:
        new_text = llm_helpers.gemini_text(
            RESUME_TAILOR_PROMPT, user_content, temperature=0.3,
        ).strip()
    except Exception as exc:
        return TEMPLATES.TemplateResponse("resume_studio.html", {
            "request": request, "job": job,
            "current_len": len(job.get("resume_md") or ""),
            "new_resume_md": "",
            "error": f"Gemini call failed: {type(exc).__name__}: {str(exc)[:300]}",
        })

    return TEMPLATES.TemplateResponse("resume_studio.html", {
        "request": request, "job": job,
        "current_len": len(job.get("resume_md") or ""),
        "new_resume_md": new_text,
    })


# ─── DM Studio ─────────────────────────────────────────────────────────────

DM_PROMPT = """You're drafting a short personalized LinkedIn DM for Ajinkya Kate.

CRITICAL FRAMING (must follow):
- Ajinkya is Product Owner at D·engage (customer engagement SaaS), 2+ yrs PM, CSPO certified.
- His D·engage role wrapped in May 2026 and he's exploring his next product role.
- Use POSITIVE framing: "exploring my next product role" / "taking the next step." NEVER use "transitioning out," "just left," "in transition," "looking for a job," or anything that sounds like job-loss anxiety.
- Tone: warm peer-to-peer, never sycophantic, never demanding.

RULES:
- 3-4 short paragraphs MAX. Under 150 words total.
- Open with a specific reference to the recipient's profile (their role / background / something distinctive).
- Quick context on Ajinkya (1 line).
- ONE specific ask (the user provides it). Don't ask for too many things.
- Offer reciprocity at the end if natural — what Ajinkya might offer them.
- Close warm.
- Output ONLY the DM text. No "Hi NAME," prefix needed (LinkedIn shows the name). No sign-off "Cheers, Ajinkya" — already implied.
- Actually DO include "Hi <FirstName>," at the start.
- Actually DO include "Cheers, Ajinkya" at the end.
"""


@app.get("/contacts/{contact_id}/dm-studio", response_class=HTMLResponse)
def dm_studio_page(contact_id: int, request: Request):
    tracker.init_db()
    with get_connection() as conn:
        contact_row = conn.execute(
            "SELECT c.*, j.id AS j_id, j.company AS j_company, j.title AS j_title "
            "FROM contacts c JOIN jobs j ON c.job_id = j.id WHERE c.id = ?",
            (contact_id,),
        ).fetchone()
    if not contact_row:
        return HTMLResponse(f"<h1>Contact #{contact_id} not found</h1>", status_code=404)
    contact = dict(contact_row)
    job = {"id": contact["j_id"], "company": contact["j_company"], "title": contact["j_title"]}
    return TEMPLATES.TemplateResponse("dm_studio.html", {
        "request": request, "contact": contact, "job": job,
    })


@app.post("/contacts/{contact_id}/dm-studio", response_class=HTMLResponse)
def dm_studio_submit(
    contact_id: int, request: Request,
    action: str = Form(...),
    profile_text: str = Form(""),
    ask: str = Form(""),
    tone: str = Form("warm peer"),
    draft: str = Form(""),
):
    tracker.init_db()
    with get_connection() as conn:
        contact_row = conn.execute(
            "SELECT c.*, j.id AS j_id, j.company AS j_company, j.title AS j_title, "
            "j.status AS j_status, j.notes AS j_notes "
            "FROM contacts c JOIN jobs j ON c.job_id = j.id WHERE c.id = ?",
            (contact_id,),
        ).fetchone()
    if not contact_row:
        return HTMLResponse(f"<h1>Contact #{contact_id} not found</h1>", status_code=404)
    contact = dict(contact_row)
    job = {"id": contact["j_id"], "company": contact["j_company"], "title": contact["j_title"]}
    form = {"profile_text": profile_text, "ask": ask, "tone": tone}

    if action == "save":
        if not draft.strip():
            return TEMPLATES.TemplateResponse("dm_studio.html", {
                "request": request, "contact": contact, "job": job, "form": form,
                "error": "No draft to save.",
            })
        now_iso = datetime.now().isoformat(timespec="seconds")
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO events (job_id, contact_id, event_type, body, occurred_at, recorded_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (job["id"], contact_id, "note", f"SUGGESTED DM (via DM Studio):\n\n{draft}", now_iso, now_iso),
            )
        return RedirectResponse(f"/jobs/{job['id']}", status_code=303)

    # action == "generate"
    if not llm_helpers.is_available():
        return TEMPLATES.TemplateResponse("dm_studio.html", {
            "request": request, "contact": contact, "job": job, "form": form,
            "error": "GEMINI_API_KEY not configured.",
        })

    user_content = (
        f"RECIPIENT: {contact.get('name', 'them')}\n"
        f"RECIPIENT'S ROLE/HEADLINE: {contact.get('role', '—')}\n"
        f"RECIPIENT'S PROFILE CONTENT (if provided):\n{profile_text or '(none — base DM on role/headline only)'}\n\n"
        f"JOB CONTEXT FOR AJINKYA: applying for {job['title']} at {job['company']} (status: {contact.get('j_status')})\n\n"
        f"AJINKYA'S SPECIFIC ASK FOR THIS RECIPIENT: {ask}\n\n"
        f"DESIRED TONE: {tone}\n\n"
        f"Draft the DM now. Plain text, no markdown, ready to paste into LinkedIn."
    )

    try:
        draft_text = llm_helpers.gemini_text(
            DM_PROMPT, user_content, temperature=0.5,
        ).strip()
    except Exception as exc:
        return TEMPLATES.TemplateResponse("dm_studio.html", {
            "request": request, "contact": contact, "job": job, "form": form,
            "error": f"Gemini call failed: {type(exc).__name__}: {str(exc)[:300]}",
        })

    return TEMPLATES.TemplateResponse("dm_studio.html", {
        "request": request, "contact": contact, "job": job, "form": form,
        "draft": draft_text,
    })


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1 — Leads inbox (LinkedIn alerts → tracker)
# ─────────────────────────────────────────────────────────────────────────────

def _relative_time(iso_str: str) -> str:
    """Format ISO datetime as '2h ago' / 'just now' / '3d ago'."""
    if not iso_str:
        return ""
    try:
        from datetime import datetime as _dt, timezone as _tz
        dt = _dt.fromisoformat(iso_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=_tz.utc)
        delta = _dt.now(_tz.utc) - dt
        s = int(delta.total_seconds())
        if s < 60: return "just now"
        if s < 3600: return f"{s // 60}m ago"
        if s < 86400: return f"{s // 3600}h ago"
        if s < 604800: return f"{s // 86400}d ago"
        return f"{s // 604800}w ago"
    except Exception:
        return iso_str[:10]


@app.get("/leads", response_class=HTMLResponse)
def leads_inbox(request: Request, show: str = "", q: str = ""):
    """Triage list of LinkedIn-alert-imported leads (status='lead' or 'lead-dismissed').

    Optional ?q= filters by title/company/location (case-insensitive LIKE).
    """
    tracker.init_db()
    show_dismissed = (show == "dismissed")
    status_filter = "lead-dismissed" if show_dismissed else "lead"
    q_clean = (q or "").strip()
    with get_connection() as conn:
        if q_clean:
            like_arg = f"%{q_clean.lower()}%"
            rows = conn.execute(
                "SELECT id, title, company, link, location, added_at FROM jobs "
                "WHERE status = ? AND ("
                "  LOWER(title) LIKE ? OR LOWER(company) LIKE ? OR LOWER(location) LIKE ?"
                ") ORDER BY added_at DESC LIMIT 200",
                (status_filter, like_arg, like_arg, like_arg),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, title, company, link, location, added_at FROM jobs "
                "WHERE status = ? ORDER BY added_at DESC LIMIT 200",
                (status_filter,),
            ).fetchall()
        dismissed_row = conn.execute(
            "SELECT COUNT(*) AS n FROM jobs WHERE status = 'lead-dismissed'"
        ).fetchone()
    leads = []
    for r in rows:
        d = dict(r)
        co = d.get("company") or ""
        words = [w for w in co.split() if w[0:1].isalnum()]
        d["ini"] = ((words[0][0] + words[1][0]).upper()
                    if len(words) >= 2 else co[:2].upper() or "?")
        d["added_rel"] = _relative_time(d.get("added_at", ""))
        leads.append(d)
    # Build a LinkedIn search URL for the user's query (opens in new tab on click)
    linkedin_search_url = ""
    if q_clean:
        from urllib.parse import quote_plus
        linkedin_search_url = (
            f"https://www.linkedin.com/jobs/search/?keywords={quote_plus(q_clean)}"
        )
    return TEMPLATES.TemplateResponse("leads.html", {
        "request": request, "leads": leads,
        "show_dismissed": show_dismissed,
        "dismissed_count": dismissed_row["n"] if dismissed_row else 0,
        "q": q_clean,
        "linkedin_search_url": linkedin_search_url,
    })


@app.post("/leads/{lead_id}/pursue")
def leads_pursue(lead_id: int):
    """Promote a lead to status='saved'. Tries to fetch full JD from LinkedIn
    guest page so Resume Studio can tailor immediately.
    """
    import linkedin_fetch
    tracker.init_db()
    now_iso = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, link, jd_raw_text, company, title, location "
            "FROM jobs WHERE id = ?",
            (lead_id,),
        ).fetchone()
        if not row:
            return RedirectResponse("/leads", status_code=303)

        # Best-effort: fetch full JD from LinkedIn guest page if we don't have it
        link = row["link"] or ""
        already_has_jd = (row["jd_raw_text"] or "").strip()
        fetched_jd = None
        if link and not already_has_jd and "linkedin.com" in link:
            details = linkedin_fetch.fetch_job_details(link)
            if details and (details.get("jd_text") or "").strip():
                fetched_jd = details

        # Update job: promote to saved, optionally enrich with fetched JD
        if fetched_jd:
            conn.execute(
                "UPDATE jobs SET status = 'saved', worth_pursuing = 'yes', "
                "jd_raw_text = ?, "
                "title = COALESCE(NULLIF(title, ''), ?), "
                "company = COALESCE(NULLIF(company, ''), ?), "
                "location = COALESCE(NULLIF(location, ''), ?), "
                "last_activity_at = ? WHERE id = ?",
                (fetched_jd["jd_text"], fetched_jd.get("title") or row["title"],
                 fetched_jd.get("company") or row["company"],
                 fetched_jd.get("location") or row["location"],
                 now_iso, lead_id),
            )
            conn.execute(
                "INSERT INTO events (job_id, event_type, body, occurred_at, recorded_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (lead_id, "note",
                 f"Auto-fetched JD from LinkedIn guest page ({len(fetched_jd['jd_text'])} chars). "
                 "Resume Studio can now tailor against the real JD.",
                 now_iso, now_iso),
            )
        else:
            conn.execute(
                "UPDATE jobs SET status = 'saved', worth_pursuing = 'yes', last_activity_at = ? WHERE id = ?",
                (now_iso, lead_id),
            )

        conn.execute(
            "INSERT INTO events (job_id, event_type, body, occurred_at, recorded_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (lead_id, "status_change", "lead -> saved (promoted from Leads inbox)", now_iso, now_iso),
        )
    return RedirectResponse(f"/jobs/{lead_id}", status_code=303)


@app.post("/leads/{lead_id}/dismiss")
def leads_dismiss(lead_id: int):
    """Hide a lead — stays in DB so future LinkedIn emails dedup against it."""
    tracker.init_db()
    now_iso = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        conn.execute(
            "UPDATE jobs SET status = 'lead-dismissed', last_activity_at = ? WHERE id = ?",
            (now_iso, lead_id),
        )
    return RedirectResponse("/leads", status_code=303)


@app.post("/leads/{lead_id}/restore")
def leads_restore(lead_id: int):
    """Undo a dismiss — bring back to active leads."""
    tracker.init_db()
    now_iso = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        conn.execute(
            "UPDATE jobs SET status = 'lead', last_activity_at = ? WHERE id = ?",
            (now_iso, lead_id),
        )
    return RedirectResponse("/leads?show=dismissed", status_code=303)
