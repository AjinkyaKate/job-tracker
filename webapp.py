import os
import re
import secrets
from datetime import datetime, timezone
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

    # Apply→reply gap: how long since user applied. NULL applied_at means we
    # don't know when (older jobs, jobs that never went through Applied).
    # 'is_stale' = status is still 'applied' AND >3 days passed without
    # advancing to Replied/Interview/Offer — the trigger for follow-up.
    applied_at = job_dict.get("applied_at")
    applied_days_ago = None
    is_stale = False
    is_stale_critical = False  # 7d+: louder visual
    if applied_at:
        try:
            d1 = datetime.strptime(applied_at, "%Y-%m-%d").date()
            d2 = datetime.fromisoformat(today).date()
            applied_days_ago = (d2 - d1).days
            if job_dict["status"] == "applied":
                if applied_days_ago >= 3:
                    is_stale = True
                if applied_days_ago >= 7:
                    is_stale_critical = True
        except Exception:
            pass
    job_dict["applied_days_ago"] = applied_days_ago
    job_dict["is_stale"] = is_stale
    job_dict["is_stale_critical"] = is_stale_critical
    # Activity preview: prefer next_action_note. Use 'or ""' to coerce NULL → "".
    # (.get(k, "") only returns the default when the KEY is missing — not when
    # the value is None, which is the common case for Postgres NULL columns.)
    next_note = job_dict.get("next_action_note") or ""
    notes_str = job_dict.get("notes") or ""
    job_dict["activity_preview"] = (next_note or notes_str[:80] or "")[:120]
    return job_dict


def _format_relative_time(iso_ts: Optional[str]) -> str:
    """Convert an ISO timestamp to a friendly relative string.

    Examples: "just now", "5m ago", "2h ago", "Yesterday 9:43 PM", "May 20, 4:12 PM".
    Returns "" for None / unparseable input.
    """
    if not iso_ts:
        return ""
    try:
        ts = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return ""
    # Normalize to UTC-aware for the diff, then render in local clock time
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    delta = now - ts
    secs = int(delta.total_seconds())
    if secs < 30:
        return "just now"
    if secs < 60:
        return f"{secs}s ago"
    if secs < 3600:
        return f"{secs // 60}m ago"
    if secs < 86400:
        return f"{secs // 3600}h ago"
    if secs < 172800:
        return f"Yesterday {ts.astimezone().strftime('%-I:%M %p')}"
    if secs < 604800:
        return f"{ts.astimezone().strftime('%a %-I:%M %p')}"
    return ts.astimezone().strftime("%b %-d, %-I:%M %p")


def _build_chip(label, key, qs_param, active_keys, base_query, single_select=False):
    """Build a filter-chip dict the template can render.

    single_select=False (default): clicking toggles the key in/out of the
        multi-valued qs_param. Use for orthogonal flags (e.g. 'stale').
    single_select=True: clicking an inactive chip REPLACES the qs_param
        with just this key (radio-button behavior). Clicking the active
        chip clears the qs_param. Use for mutually-exclusive groups like
        status, where Applied + Replied at once is rarely what you want."""
    is_active = key in active_keys
    if single_select:
        next_keys = [] if is_active else [key]
    else:
        if is_active:
            next_keys = [k for k in active_keys if k != key]
        else:
            next_keys = active_keys + [key]
    qs = dict(base_query)
    if next_keys:
        qs[qs_param] = ",".join(next_keys)
    else:
        qs.pop(qs_param, None)
    qstr = "&".join(f"{k}={v}" for k, v in qs.items())
    return {
        "label": label,
        "key": key,
        "active": is_active,
        "url": "/" + (f"?{qstr}" if qstr else ""),
    }


@app.get("/", response_class=HTMLResponse)
def homepage(request: Request):
    tracker.init_db()
    today = datetime.now().date().isoformat()

    # Filter state from URL: ?status=applied,saved&flag=stale
    qp = request.query_params
    active_statuses = [s for s in (qp.get("status", "").split(",")) if s]
    active_flags = [f for f in (qp.get("flag", "").split(",")) if f]

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

    # Count for the "Stale 3d+" chip — must be from the UNFILTERED set,
    # otherwise the count drops to 0 the moment you toggle on the filter.
    stale_count = sum(1 for j in jobs if j["is_stale"])

    # Apply filter chips: status (multi) and flag=stale (multi-flags ready).
    # Empty status list → show all. Empty flags → no extra filter.
    filtered_jobs = jobs
    if active_statuses:
        filtered_jobs = [j for j in filtered_jobs if j["status"] in active_statuses]
    if "stale" in active_flags:
        filtered_jobs = [j for j in filtered_jobs if j["is_stale"]]

    # Group jobs by status (preserve PIPELINE_STATUSES order)
    by_status = {s["key"]: [] for s in PIPELINE_STATUSES}
    for j in filtered_jobs:
        if j["status"] in by_status:
            by_status[j["status"]].append(j)
        else:
            # Unknown status falls into Saved
            by_status["saved"].append(j)

    # Build chip rows for the template
    base_qs = {}  # keep this empty for now; status/flag get re-added in _build_chip
    status_chips = [
        _build_chip(s["label"], s["key"], "status", active_statuses, {}, single_select=True)
        for s in PIPELINE_STATUSES
    ]
    # Inject the current 'flag' selection into status-chip URLs so toggling
    # status doesn't accidentally clear the stale-only filter.
    if active_flags:
        flag_qs = "flag=" + ",".join(active_flags)
        for chip in status_chips:
            sep = "&" if "?" in chip["url"] else "?"
            chip["url"] = chip["url"] + sep + flag_qs
    flag_chips = [
        _build_chip(f"⚡ Stale 3d+ ({stale_count})", "stale", "flag", active_flags, {})
    ]
    if active_statuses:
        st_qs = "status=" + ",".join(active_statuses)
        for chip in flag_chips:
            sep = "&" if "?" in chip["url"] else "?"
            chip["url"] = chip["url"] + sep + st_qs

    any_filter_active = bool(active_statuses or active_flags)

    # Gmail integration status for top-bar Sync button
    gmail_state = {
        "configured": gmail_integration.is_configured(),
        "authorized": False,
        "last_sync": None,
        "last_sync_rel": "",
        "last_sync_summary": None,
    }
    if gmail_state["configured"]:
        with get_connection() as conn:
            creds = gmail_integration.load_credentials(conn)
            gmail_state["authorized"] = creds is not None
            last_sync = gmail_integration.get_last_sync(conn)
            gmail_state["last_sync"] = last_sync
            gmail_state["last_sync_rel"] = _format_relative_time(last_sync)
            gmail_state["last_sync_summary"] = gmail_integration.get_last_sync_summary(conn)

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
            "stale_count": stale_count,
            "status_chips": status_chips,
            "flag_chips": flag_chips,
            "any_filter_active": any_filter_active,
            "filtered_total": len(filtered_jobs),
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

        # Set applied_at the first time a job lands in 'applied' status (and
        # only if it hasn't been set before — preserves the original apply
        # date if a job bounces Applied → Replied → Applied).
        today = datetime.now().date().isoformat()
        if new_status == "applied":
            conn.execute(
                "UPDATE jobs SET status = ?, last_activity_at = ?, "
                "applied_at = COALESCE(applied_at, ?) WHERE id = ?",
                (new_status, now, today, job_id),
            )
        else:
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


# Filter chip definitions — chips map to keyword sets that LIKE-match against
# title or location. Multi-select within each row, combined AND across rows.
# Chip keys also map to a tailored role-family resume via role_resumes.py.
TITLE_CHIPS = [
    ("po",       "Product Owner",         ["product owner"]),
    ("pm",       "PM / APM",              ["product manager", "associate product manager",
                                           "junior product manager"]),
    ("spm",      "Senior PM",             ["senior product manager", "lead product manager",
                                           "principal product manager", "staff product manager"]),
    ("ai-pm",    "AI Product Manager",    ["ai product", "ml product", "machine learning",
                                           "llm product", "ai/ml"]),
    ("fd",       "Forward Deployed",      ["forward deployed", "forward-deployed"]),
    ("ai-eng",   "Applied AI Engineer",   ["applied ai", "ai engineer"]),
    ("founding", "Founding",              ["founding"]),
    ("sol-eng",  "Solutions / Customer Eng", ["solutions engineer", "customer engineer",
                                              "implementation engineer"]),
    ("prod-eng", "Product Engineer",      ["product engineer"]),
    ("ba",       "BA / Analyst",          ["business analyst", "product analyst"]),
]
LOC_CHIPS = [
    ("pune",   "Pune",         ["pune"]),
    ("mumbai", "Mumbai",       ["mumbai"]),
    ("blr",    "Bengaluru",    ["bengaluru", "bangalore"]),
    ("hyd",    "Hyderabad",    ["hyderabad", "hyderābād"]),
    ("remote", "Remote (India)", ["remote"]),
    ("delhi",  "Delhi/NCR",    ["delhi", "ncr", "gurugram", "noida", "gurgaon"]),
]


def _build_chip_clause(chips_def, selected_keys, column):
    """Build a WHERE clause for any-of-selected chip values matching `column`.

    Returns (sql_fragment, params_list). sql_fragment is like:
        (LOWER(title) LIKE ? OR LOWER(title) LIKE ? OR ...)
    """
    if not selected_keys:
        return "", []
    keywords = []
    for key in selected_keys:
        for k, _label, kws in chips_def:
            if k == key:
                keywords.extend(kws)
                break
    if not keywords:
        return "", []
    fragments = [f"LOWER({column}) LIKE ?"] * len(keywords)
    params = [f"%{k}%" for k in keywords]
    return f"({' OR '.join(fragments)})", params


@app.get("/leads", response_class=HTMLResponse)
def leads_inbox(request: Request, show: str = "", title: str = "", loc: str = ""):
    """Triage list of leads, filtered by chip-style title + location selectors.

    Both `title` and `loc` are comma-separated keys (e.g. ?title=po,pm&loc=pune,remote).
    """
    tracker.init_db()
    show_dismissed = (show == "dismissed")
    status_filter = "lead-dismissed" if show_dismissed else "lead"

    selected_titles = [t for t in (title or "").split(",") if t.strip()]
    selected_locs = [l for l in (loc or "").split(",") if l.strip()]

    title_clause, title_params = _build_chip_clause(TITLE_CHIPS, selected_titles, "title")
    loc_clause, loc_params = _build_chip_clause(LOC_CHIPS, selected_locs, "location")

    where_parts = ["status = ?"]
    params = [status_filter]
    if title_clause:
        where_parts.append(title_clause)
        params.extend(title_params)
    if loc_clause:
        where_parts.append(loc_clause)
        params.extend(loc_params)
    where_sql = " AND ".join(where_parts)

    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT id, title, company, link, location, added_at FROM jobs "
            f"WHERE {where_sql} ORDER BY added_at DESC LIMIT 200",
            tuple(params),
        ).fetchall()
        total_unfiltered = conn.execute(
            "SELECT COUNT(*) AS n FROM jobs WHERE status = ?", (status_filter,),
        ).fetchone()["n"]
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
        # Per-lead resume routing — auto-detect family from the job title so
        # each card gets a one-click '📄 Resume' button without the user
        # picking a chip first. URL also carries company so the resume page
        # can put the target company in the PDF filename.
        import role_resumes as _rr
        fam = _rr.detect_family_from_title(d.get("title") or "")
        d["resume_family"] = fam
        d["resume_label"] = _rr.FAMILY_LABELS.get(fam, fam)
        # Stable per-family URL — no company suffix in filename so the user
        # downloads each family resume ONCE and reuses across all leads.
        d["resume_url"] = f"/resumes/role/{fam}"
        # The stable PDF filename the user will pick from their Downloads
        # folder. Generated to match the resume page's download default so
        # the on-screen hint matches the file on disk.
        label_slug = (d["resume_label"] or fam).replace(" / ", "_").replace(" ", "_")
        d["resume_filename"] = f"Ajinkya_Kate_{label_slug}.pdf"
        leads.append(d)
    # Build display chips with active/inactive state + URLs that toggle membership
    def build_chip_state(defs, current_keys, param_name):
        """Single-select chip behavior (radio-button style):
        - clicking an inactive chip REPLACES current selection with just that key
        - clicking the active chip clears the row
        User asked for this in both Title + Loc rows — selecting two roles at
        once is rarely what they want at the triage moment."""
        out = []
        for key, label, _kws in defs:
            is_active = key in current_keys
            new_keys = [] if is_active else [key]
            query_parts = []
            if param_name == "title":
                if new_keys:
                    query_parts.append(f"title={','.join(new_keys)}")
                if selected_locs:
                    query_parts.append(f"loc={','.join(selected_locs)}")
            else:
                if selected_titles:
                    query_parts.append(f"title={','.join(selected_titles)}")
                if new_keys:
                    query_parts.append(f"loc={','.join(new_keys)}")
            url = "/leads" + (("?" + "&".join(query_parts)) if query_parts else "")
            out.append({"key": key, "label": label, "active": is_active, "url": url})
        return out

    # If any title chip is active, surface the matching role-family resume
    import role_resumes
    role_resume_link = None
    role_resume_label = None
    if selected_titles:
        # Use the FIRST selected title chip to pick the resume family
        first_key = selected_titles[0]
        family = role_resumes.CHIP_TO_RESUME_FAMILY.get(first_key)
        if family:
            role_resume_link = f"/resumes/role/{family}"
            role_resume_label = role_resumes.FAMILY_LABELS.get(family, family)

    return TEMPLATES.TemplateResponse("leads.html", {
        "request": request, "leads": leads,
        "show_dismissed": show_dismissed,
        "dismissed_count": dismissed_row["n"] if dismissed_row else 0,
        "title_chips": build_chip_state(TITLE_CHIPS, selected_titles, "title"),
        "loc_chips": build_chip_state(LOC_CHIPS, selected_locs, "loc"),
        "active_filters_count": len(selected_titles) + len(selected_locs),
        "total_unfiltered": total_unfiltered,
        "role_resume_link": role_resume_link,
        "role_resume_label": role_resume_label,
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


@app.post("/leads/{lead_id}/applied")
def leads_already_applied(lead_id: int):
    """User opened LinkedIn from the lead, found they already applied earlier.
    Skips the Saved → Applied dance: status straight to 'applied' + applied_at=today.
    """
    tracker.init_db()
    now_iso = datetime.now().isoformat(timespec="seconds")
    today = datetime.now().date().isoformat()
    with get_connection() as conn:
        conn.execute(
            "UPDATE jobs SET status = 'applied', worth_pursuing = 'yes', "
            "applied_at = COALESCE(applied_at, ?), last_activity_at = ? WHERE id = ?",
            (today, now_iso, lead_id),
        )
        conn.execute(
            "INSERT INTO events (job_id, event_type, body, occurred_at, recorded_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (lead_id, "status_change",
             "lead -> applied (already-applied path from Leads triage)",
             now_iso, now_iso),
        )
    return RedirectResponse("/leads", status_code=303)


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


@app.get("/resumes", response_class=HTMLResponse)
def resumes_library(request: Request):
    """One-stop library page: list all 15 family resumes with their stable
    filenames + open-in-new-tab links. User does a one-time pass on this
    page to download each PDF, then on every Lead card they just see which
    filename to use from disk."""
    import role_resumes
    families = []
    for family_key, label in role_resumes.FAMILY_LABELS.items():
        label_slug = label.replace(" / ", "_").replace(" ", "_")
        families.append({
            "key": family_key,
            "label": label,
            "filename": f"Ajinkya_Kate_{label_slug}.pdf",
            "url": f"/resumes/role/{family_key}",
        })
    return TEMPLATES.TemplateResponse(
        "resumes_library.html",
        {"request": request, "families": families},
    )


@app.get("/resumes/role/{family}", response_class=HTMLResponse)
def role_resume_page(family: str, request: Request):
    """Render a pre-tailored resume for a given role family.

    Optional ?company=X query param customizes the suggested PDF filename
    so downloading from a Lead card produces
    'Ajinkya_Kate_Allianz_AI_Product_Manager.pdf' instead of the generic
    'Ajinkya_Kate_AI_Product_Manager.pdf' — easier for the user to track
    which file they sent to which recruiter.
    """
    import role_resumes
    md = role_resumes.render_role_resume(family)
    if not md:
        return HTMLResponse(
            f"<h1>Unknown role family: {family}</h1>"
            f"<p>Known: {', '.join(role_resumes.ROLE_RESUMES.keys())}</p>",
            status_code=404,
        )
    resume_html = md_lib.markdown(md, extensions=["extra", "sane_lists"])
    label = role_resumes.FAMILY_LABELS.get(family, family)

    company = (request.query_params.get("company") or "").strip()
    company_slug = _slugify_for_filename(company) if company else ""
    label_slug = label.replace(" / ", "_").replace(" ", "_")
    if company_slug:
        pdf_filename = f"Ajinkya_Kate_{company_slug}_{label_slug}.pdf"
    else:
        pdf_filename = f"Ajinkya_Kate_{label_slug}.pdf"

    # Reuse the existing resume.html template — pass a synthetic "job" dict.
    # title displays target role @ target company at the top of the page.
    display_title = label
    display_company = company if company else label
    return TEMPLATES.TemplateResponse(
        "resume.html",
        {
            "request": request,
            "job": {"id": 0, "company": display_company, "title": display_title,
                    "resume_md": md, "link": "", "company_slug": company_slug or label_slug},
            "resume_html": resume_html,
            "pdf_filename": pdf_filename,
        },
    )
