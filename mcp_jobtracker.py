"""MCP server for the Job Tracker — exposes the local SQLite DB to Claude Code.

After registering this server in ~/.claude.json, Claude Code sessions get
tools like list_leads, get_lead, score_lead, mark_applied, etc. The user
chats naturally ("show me strong leads", "mark Aurora as applied") and
Claude calls these tools to query/update the same DB the web UI reads.

Hardcoded to user_id=1 for now. When real multi-tenant lands (or when a
second user signs in via Claude Code), wire a CURRENT_USER_ID env var or
similar.

Runs under the .venv-mcp/ Python 3.11 environment (separate from the
web-app's Python 3.9 venv) because the official mcp SDK requires 3.10+.
"""
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

# ─── Configuration ──────────────────────────────────────────────────────────

# Default DB path resolves relative to this file. Override via JOBTRACKER_DB
# env var if you want the server to talk to a different DB (e.g. a copy).
DEFAULT_DB = Path(__file__).resolve().parent / "tracker.db"
DB_PATH = os.environ.get("JOBTRACKER_DB", str(DEFAULT_DB))

# Single-user mode. user_id=1 = Ajinkya (the only user in the local DB).
# Future: parse from CLAUDE_USER_ID env or accept user_id as a param.
USER_ID = 1


# ─── DB helpers ─────────────────────────────────────────────────────────────

def _conn() -> sqlite3.Connection:
    """Open a fresh connection each call. SQLite is fine with this and it
    avoids cross-connection-cache surprises during long sessions."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _row_to_dict(row: sqlite3.Row) -> dict:
    return {k: row[k] for k in row.keys()}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _today_date() -> str:
    return datetime.now().date().isoformat()


# ─── MCP server ─────────────────────────────────────────────────────────────

mcp = FastMCP("job-tracker")


# ─── Read tools ─────────────────────────────────────────────────────────────

@mcp.tool()
def list_leads(status: str = "lead", limit: int = 20,
               score: Optional[str] = None) -> list[dict]:
    """List jobs filtered by status (default: 'lead' = un-triaged inbox).

    Statuses: 'lead', 'lead-dismissed', 'saved', 'applied', 'replied',
    'interview', 'offer', 'rejected', 'backlog'.

    Pass score='STRONG' | 'MAYBE' | 'SKIP' to filter to a specific AI score.
    Most recent first. Returns id, title, company, location, link, added_at,
    ai_score, ai_score_reason.
    """
    sql = (
        "SELECT id, title, company, location, link, added_at, "
        "ai_score, ai_score_reason "
        "FROM jobs WHERE user_id = ? AND status = ?"
    )
    params: list[Any] = [USER_ID, status]
    if score:
        sql += " AND ai_score = ?"
        params.append(score.upper())
    sql += " ORDER BY added_at DESC LIMIT ?"
    params.append(limit)

    with _conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_row_to_dict(r) for r in rows]


@mcp.tool()
def get_lead(job_id: int) -> dict:
    """Fetch full detail of one job by id, including the JD text, skills,
    and any cached AI analysis. Returns the row as a dict, or {'error': ...}
    if not found."""
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM jobs WHERE id = ? AND user_id = ?",
            (job_id, USER_ID),
        ).fetchone()
        if not row:
            return {"error": f"Job {job_id} not found"}
        return _row_to_dict(row)


@mcp.tool()
def search_jobs(query: str, limit: int = 20) -> list[dict]:
    """Case-insensitive LIKE search across title, company, and JD text.

    Example: search_jobs('python', limit=10) returns jobs that mention
    'python' anywhere in title, company name, or job description.
    """
    like = f"%{query}%"
    with _conn() as conn:
        rows = conn.execute(
            "SELECT id, title, company, location, status, ai_score "
            "FROM jobs WHERE user_id = ? AND ("
            "  LOWER(title) LIKE LOWER(?) OR "
            "  LOWER(company) LIKE LOWER(?) OR "
            "  LOWER(jd_raw_text) LIKE LOWER(?)"
            ") ORDER BY added_at DESC LIMIT ?",
            (USER_ID, like, like, like, limit),
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


@mcp.tool()
def pipeline_stats() -> dict:
    """Return counts by status for the user's active pipeline + a few
    convenience metrics (overdue, due today, strong leads waiting)."""
    today = _today_date()
    with _conn() as conn:
        status_rows = conn.execute(
            "SELECT status, COUNT(*) AS n FROM jobs "
            "WHERE user_id = ? GROUP BY status",
            (USER_ID,),
        ).fetchall()
        overdue = conn.execute(
            "SELECT COUNT(*) AS n FROM jobs WHERE user_id = ? "
            "AND next_action_at IS NOT NULL AND next_action_at < ? "
            "AND (worth_pursuing IS NULL OR worth_pursuing != 'no')",
            (USER_ID, today),
        ).fetchone()["n"]
        due_today = conn.execute(
            "SELECT COUNT(*) AS n FROM jobs WHERE user_id = ? "
            "AND next_action_at = ? "
            "AND (worth_pursuing IS NULL OR worth_pursuing != 'no')",
            (USER_ID, today),
        ).fetchone()["n"]
        strong_leads = conn.execute(
            "SELECT COUNT(*) AS n FROM jobs WHERE user_id = ? "
            "AND status = 'lead' AND ai_score = 'STRONG'",
            (USER_ID,),
        ).fetchone()["n"]
    return {
        "by_status": {r["status"]: r["n"] for r in status_rows},
        "overdue": overdue,
        "due_today": due_today,
        "strong_leads_waiting": strong_leads,
    }


@mcp.tool()
def today_view() -> dict:
    """Return what needs attention today: overdue items and due-today items.
    Use this when the user asks 'what should I work on today'."""
    today = _today_date()
    with _conn() as conn:
        overdue = conn.execute(
            "SELECT id, title, company, status, next_action_at, next_action_note "
            "FROM jobs WHERE user_id = ? AND next_action_at IS NOT NULL "
            "AND next_action_at < ? "
            "AND (worth_pursuing IS NULL OR worth_pursuing != 'no') "
            "ORDER BY next_action_at",
            (USER_ID, today),
        ).fetchall()
        due_today = conn.execute(
            "SELECT id, title, company, status, next_action_at, next_action_note "
            "FROM jobs WHERE user_id = ? AND next_action_at = ? "
            "AND (worth_pursuing IS NULL OR worth_pursuing != 'no') "
            "ORDER BY id",
            (USER_ID, today),
        ).fetchall()
    return {
        "today": today,
        "overdue": [_row_to_dict(r) for r in overdue],
        "due_today": [_row_to_dict(r) for r in due_today],
    }


@mcp.tool()
def get_profile() -> dict:
    """Return the user's profile text (used by the JD analysis AI).
    Returns the saved profile or a marker that the default is in effect."""
    with _conn() as conn:
        row = conn.execute(
            "SELECT profile_text, updated_at FROM user_profile WHERE user_id = ?",
            (USER_ID,),
        ).fetchone()
        if row:
            return {
                "profile_text": row["profile_text"],
                "updated_at": row["updated_at"],
                "is_default": False,
            }
    return {
        "profile_text": None,
        "is_default": True,
        "note": "No saved profile. The web app uses a hardcoded default.",
    }


# ─── Write tools ────────────────────────────────────────────────────────────

@mcp.tool()
def mark_applied(job_id: int) -> dict:
    """Mark a job as applied today. Sets status='applied', applied_at=today,
    last_activity_at=now, and logs a status_change event."""
    now = _now_iso()
    today = _today_date()
    with _conn() as conn:
        row = conn.execute(
            "SELECT id, status FROM jobs WHERE id = ? AND user_id = ?",
            (job_id, USER_ID),
        ).fetchone()
        if not row:
            return {"error": f"Job {job_id} not found"}
        old_status = row["status"]
        conn.execute(
            "UPDATE jobs SET status = 'applied', "
            "applied_at = COALESCE(applied_at, ?), "
            "last_activity_at = ? WHERE id = ? AND user_id = ?",
            (today, now, job_id, USER_ID),
        )
        conn.execute(
            "INSERT INTO events (job_id, event_type, body, occurred_at, "
            "recorded_at, user_id) VALUES (?, ?, ?, ?, ?, ?)",
            (job_id, "status_change",
             f"{old_status} -> applied (via MCP)", now, now, USER_ID),
        )
        conn.commit()
    return {"ok": True, "job_id": job_id, "from": old_status, "to": "applied"}


@mcp.tool()
def dismiss_lead(job_id: int) -> dict:
    """Hide a lead from the active inbox by setting status='lead-dismissed'.
    Use for jobs the user isn't interested in. Reversible via restore_lead."""
    now = _now_iso()
    with _conn() as conn:
        row = conn.execute(
            "SELECT id, status FROM jobs WHERE id = ? AND user_id = ?",
            (job_id, USER_ID),
        ).fetchone()
        if not row:
            return {"error": f"Job {job_id} not found"}
        conn.execute(
            "UPDATE jobs SET status = 'lead-dismissed', last_activity_at = ? "
            "WHERE id = ? AND user_id = ?",
            (now, job_id, USER_ID),
        )
        conn.commit()
    return {"ok": True, "job_id": job_id, "to": "lead-dismissed"}


@mcp.tool()
def restore_lead(job_id: int) -> dict:
    """Reverse a dismiss: move a job from 'lead-dismissed' back to 'lead'."""
    now = _now_iso()
    with _conn() as conn:
        row = conn.execute(
            "SELECT id, status FROM jobs WHERE id = ? AND user_id = ?",
            (job_id, USER_ID),
        ).fetchone()
        if not row:
            return {"error": f"Job {job_id} not found"}
        conn.execute(
            "UPDATE jobs SET status = 'lead', last_activity_at = ? "
            "WHERE id = ? AND user_id = ?",
            (now, job_id, USER_ID),
        )
        conn.commit()
    return {"ok": True, "job_id": job_id, "to": "lead"}


@mcp.tool()
def set_status(job_id: int, status: str) -> dict:
    """Change a job's status to any valid pipeline value.

    Valid statuses: 'lead', 'lead-dismissed', 'saved', 'applied', 'replied',
    'interview', 'offer', 'rejected', 'backlog'. Logs a status_change event.
    """
    valid = {"lead", "lead-dismissed", "saved", "applied", "replied",
             "interview", "offer", "rejected", "backlog"}
    if status not in valid:
        return {"error": f"Invalid status '{status}'. "
                         f"Must be one of: {sorted(valid)}"}
    now = _now_iso()
    with _conn() as conn:
        row = conn.execute(
            "SELECT id, status FROM jobs WHERE id = ? AND user_id = ?",
            (job_id, USER_ID),
        ).fetchone()
        if not row:
            return {"error": f"Job {job_id} not found"}
        old = row["status"]
        if old == status:
            return {"ok": True, "job_id": job_id, "status": status,
                    "changed": False}
        conn.execute(
            "UPDATE jobs SET status = ?, last_activity_at = ? "
            "WHERE id = ? AND user_id = ?",
            (status, now, job_id, USER_ID),
        )
        conn.execute(
            "INSERT INTO events (job_id, event_type, body, occurred_at, "
            "recorded_at, user_id) VALUES (?, ?, ?, ?, ?, ?)",
            (job_id, "status_change",
             f"{old} -> {status} (via MCP)", now, now, USER_ID),
        )
        conn.commit()
    return {"ok": True, "job_id": job_id, "from": old, "to": status}


@mcp.tool()
def set_next_action(job_id: int, days_from_now: int,
                    note: str = "") -> dict:
    """Schedule a follow-up reminder. Sets next_action_at to today +
    days_from_now days, and saves the note. Set days_from_now=0 for today."""
    target_date = (datetime.now().date()
                   + timedelta(days=days_from_now)).isoformat()
    with _conn() as conn:
        row = conn.execute(
            "SELECT id FROM jobs WHERE id = ? AND user_id = ?",
            (job_id, USER_ID),
        ).fetchone()
        if not row:
            return {"error": f"Job {job_id} not found"}
        conn.execute(
            "UPDATE jobs SET next_action_at = ?, next_action_note = ? "
            "WHERE id = ? AND user_id = ?",
            (target_date, note or None, job_id, USER_ID),
        )
        conn.commit()
    return {"ok": True, "job_id": job_id, "next_action_at": target_date,
            "note": note}


@mcp.tool()
def add_event(job_id: int, event_type: str, body: str) -> dict:
    """Append an event to a job's timeline. Use for logging things like
    'sent DM to Tali', 'recruiter call scheduled', 'interview rescheduled'.

    Common event_type values: 'note', 'message_sent', 'message_received',
    'call_scheduled', 'interview', 'inmail_received', 'application_sent'.
    """
    now = _now_iso()
    with _conn() as conn:
        row = conn.execute(
            "SELECT id FROM jobs WHERE id = ? AND user_id = ?",
            (job_id, USER_ID),
        ).fetchone()
        if not row:
            return {"error": f"Job {job_id} not found"}
        cur = conn.execute(
            "INSERT INTO events (job_id, event_type, body, occurred_at, "
            "recorded_at, user_id) VALUES (?, ?, ?, ?, ?, ?)",
            (job_id, event_type, body, now, now, USER_ID),
        )
        event_id = cur.lastrowid
        conn.execute(
            "UPDATE jobs SET last_activity_at = ? WHERE id = ? AND user_id = ?",
            (now, job_id, USER_ID),
        )
        conn.commit()
    return {"ok": True, "event_id": event_id, "job_id": job_id}


@mcp.tool()
def add_lead(
    title: str,
    company: str,
    link: str,
    location: str = "",
    jd_text: str = "",
    jd_summary: str = "",
    must_have_skills: str = "",
    level: str = "",
    yoe_required: str = "",
    comp_range: str = "",
    company_size: str = "",
    company_industry: str = "",
    company_url: str = "",
    work_arrangement: str = "",
    employment_type: str = "",
    posted_at: str = "",
    external_apply_url: str = "",
    source: str = "apify-linkedin",
    recruiter_name: str = "",
    recruiter_title: str = "",
    recruiter_linkedin_url: str = "",
    recruiter_email: str = "",
) -> dict:
    """Create a new lead in the tracker from a scraped/external job posting.

    Inserts a jobs row (status='lead') and, if recruiter_name is given, a
    linked contacts row for the recruiter. Deduplicates by link: if a job
    with the same link already exists for the user, returns that job's id
    without creating a duplicate.

    Use this to drop jobs found via the Apify LinkedIn scraper (or any
    source) into the user's /leads inbox. Pass whatever fields you have;
    everything except title/company/link is optional.

    Returns: {ok, job_id, deduped, contact_id}.
    """
    now = _now_iso()
    with _conn() as conn:
        # Dedup by link (per user)
        if link:
            existing = conn.execute(
                "SELECT id FROM jobs WHERE link = ? AND user_id = ? LIMIT 1",
                (link, USER_ID),
            ).fetchone()
            if existing:
                return {"ok": True, "job_id": existing["id"], "deduped": True,
                        "contact_id": None}

        # status='discovered' keeps scraped jobs in the separate /discover
        # list, OUT of the Gmail-alert /leads inbox. Pursue moves them to
        # 'saved' (into the pipeline); dismiss to 'lead-dismissed'.
        cur = conn.execute(
            "INSERT INTO jobs (title, company, link, location, jd_raw_text, "
            "jd_summary, must_have_skills, level, yoe_required, comp_range, "
            "company_size, company_industry, company_url, work_arrangement, "
            "employment_type, posted_at, external_apply_url, source, status, "
            "worth_pursuing, added_at, last_activity_at, user_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
            "'discovered', 'unsure', ?, ?, ?)",
            (title, company, link, location, jd_text, jd_summary,
             must_have_skills, level, yoe_required, comp_range,
             company_size, company_industry, company_url, work_arrangement,
             employment_type, posted_at, external_apply_url, source,
             now, now, USER_ID),
        )
        job_id = cur.lastrowid

        contact_id = None
        if recruiter_name.strip():
            c = conn.execute(
                "INSERT INTO contacts (job_id, name, role, email, "
                "linkedin_url, notes, added_at, user_id) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (job_id, recruiter_name.strip(), recruiter_title.strip() or None,
                 recruiter_email.strip() or None, recruiter_linkedin_url.strip() or None,
                 f"Recruiter who posted this role (via {source}).",
                 now, USER_ID),
            )
            contact_id = c.lastrowid

        conn.commit()
    return {"ok": True, "job_id": job_id, "deduped": False,
            "contact_id": contact_id}


@mcp.tool()
def update_profile(profile_text: str) -> dict:
    """Replace the user's profile text used by JD analysis. Pass the FULL
    new profile (not a diff). Empty / whitespace-only is rejected."""
    text = (profile_text or "").strip()
    if not text:
        return {"error": "Profile text cannot be empty."}
    now = _now_iso()
    with _conn() as conn:
        existing = conn.execute(
            "SELECT user_id FROM user_profile WHERE user_id = ?",
            (USER_ID,),
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE user_profile SET profile_text = ?, updated_at = ? "
                "WHERE user_id = ?",
                (text, now, USER_ID),
            )
        else:
            conn.execute(
                "INSERT INTO user_profile (user_id, profile_text, updated_at) "
                "VALUES (?, ?, ?)",
                (USER_ID, text, now),
            )
        conn.commit()
    return {"ok": True, "user_id": USER_ID, "length": len(text)}


# ─── Server entry point ─────────────────────────────────────────────────────

if __name__ == "__main__":
    # FastMCP.run() handles the JSON-RPC stdio loop. Claude Code launches
    # this script and pipes stdin/stdout.
    mcp.run()
