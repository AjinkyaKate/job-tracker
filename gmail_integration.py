"""
Gmail integration for LinkedIn event auto-detection.

Phase 3 of the Job Tracker. Reads LinkedIn notification emails via Gmail API
and auto-logs events to the tracker (connection accepted, message received,
InMail received, application updates, etc.).

Setup: see GMAIL_SETUP.md for the Google Cloud Console steps.

Status: SCAFFOLDING (Phase 3 ship 1/3).
- get_oauth_flow + URL building     -> stubbed but functional
- callback + token storage          -> stubbed (Phase 3 ship 2/3)
- email fetch + parse + sync        -> stubbed (Phase 3 ship 3/3)
"""

import os
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Optional

# Google libs are optional at import time so the webapp doesn't crash if they
# aren't installed yet (we add them to requirements.txt in this ship).
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build
    GOOGLE_LIBS_AVAILABLE = True
except ImportError:
    GOOGLE_LIBS_AVAILABLE = False


SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
TOKEN_PROVIDER_KEY = "gmail"


# ─────────────────────────────────────────────────────────────────────────────
# Config helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_oauth_config() -> Optional[dict]:
    """Return the Google OAuth config dict, or None if env vars are missing."""
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.environ.get(
        "GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/gmail/callback"
    )
    if not (client_id and client_secret):
        return None
    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
    }


def is_configured() -> bool:
    """True only if both Google libs are importable AND env vars are set."""
    return GOOGLE_LIBS_AVAILABLE and get_oauth_config() is not None


# ─────────────────────────────────────────────────────────────────────────────
# OAuth flow (Phase 3 ship 2/3 will complete these)
# ─────────────────────────────────────────────────────────────────────────────

def build_flow() -> "Flow":
    """Build a google-auth-oauthlib Flow object from .env config."""
    cfg = get_oauth_config()
    if cfg is None:
        raise RuntimeError(
            "Google OAuth not configured. Set GOOGLE_CLIENT_ID and "
            "GOOGLE_CLIENT_SECRET in .env. See GMAIL_SETUP.md."
        )
    client_config = {
        "web": {
            "client_id": cfg["client_id"],
            "client_secret": cfg["client_secret"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [cfg["redirect_uri"]],
        }
    }
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=cfg["redirect_uri"],
    )
    return flow


def build_authorize_url(state: Optional[str] = None) -> str:
    """Build the URL to send the user to Google's consent screen."""
    flow = build_flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline",  # request a refresh_token
        prompt="consent",       # force consent so we always get refresh_token
        include_granted_scopes="true",
        state=state or "",
    )
    return auth_url


def exchange_code_for_token(code: str) -> "Credentials":
    """Exchange the OAuth callback code for credentials.

    Phase 3 ship 2/3 will wire this into /auth/gmail/callback.
    """
    flow = build_flow()
    flow.fetch_token(code=code)
    return flow.credentials


# ─────────────────────────────────────────────────────────────────────────────
# Token storage (Phase 3 ship 2/3 will complete these)
# ─────────────────────────────────────────────────────────────────────────────

def store_credentials(conn: sqlite3.Connection, creds: "Credentials", user_email: str = "") -> None:
    """Save creds to oauth_tokens table (upsert on provider key)."""
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    expires_at = creds.expiry.isoformat(timespec="seconds") if creds.expiry else None
    scopes_str = " ".join(creds.scopes or [])

    existing = conn.execute(
        "SELECT id FROM oauth_tokens WHERE provider = ?",
        (TOKEN_PROVIDER_KEY,),
    ).fetchone()

    if existing:
        conn.execute(
            """
            UPDATE oauth_tokens
            SET access_token = ?, refresh_token = COALESCE(?, refresh_token),
                expires_at = ?, scopes = ?, user_email = ?, updated_at = ?
            WHERE provider = ?
            """,
            (creds.token, creds.refresh_token, expires_at, scopes_str,
             user_email, now, TOKEN_PROVIDER_KEY),
        )
    else:
        conn.execute(
            """
            INSERT INTO oauth_tokens
              (provider, access_token, refresh_token, expires_at, scopes,
               user_email, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (TOKEN_PROVIDER_KEY, creds.token, creds.refresh_token,
             expires_at, scopes_str, user_email, now, now),
        )
    conn.commit()


def load_credentials(conn: sqlite3.Connection) -> Optional["Credentials"]:
    """Load stored Gmail creds. Returns None if not yet authorized."""
    row = conn.execute(
        "SELECT access_token, refresh_token, scopes FROM oauth_tokens WHERE provider = ?",
        (TOKEN_PROVIDER_KEY,),
    ).fetchone()
    if not row or not row["access_token"]:
        return None
    cfg = get_oauth_config()
    if cfg is None:
        return None
    creds = Credentials(
        token=row["access_token"],
        refresh_token=row["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=cfg["client_id"],
        client_secret=cfg["client_secret"],
        scopes=row["scopes"].split() if row["scopes"] else SCOPES,
    )
    return creds


# ─────────────────────────────────────────────────────────────────────────────
# LinkedIn email parsing (Phase 3 ship 3/3 will complete these)
# ─────────────────────────────────────────────────────────────────────────────

LINKEDIN_SENDER_PATTERNS = [
    r"@linkedin\.com",
    r"@e?\.?linkedin\.com",
    r"@em\.linkedin\.com",
]

SUBJECT_PATTERNS = [
    # (regex, event_type, description)
    (r"(?P<name>[\w\s'\-\.]+?) accepted your invitation", "connection_accepted",
     "Connection request accepted"),
    (r"New message from (?P<name>[\w\s'\-\.]+)", "message_received",
     "Inbound LinkedIn message"),
    (r"(?P<name>[\w\s'\-\.]+) sent you a message", "message_received",
     "Inbound LinkedIn message"),
    (r"InMail from (?P<name>[\w\s'\-\.]+)", "inmail_received",
     "Inbound LinkedIn InMail"),
    (r"Your application was sent to (?P<company>[\w\s'\-\.,&]+)", "application_sent",
     "LinkedIn application confirmed"),
    (r"(?P<company>[\w\s'\-\.,&]+) is interested in your application",
     "application_interest", "Recruiter expressed interest"),
    (r"Your application was viewed by (?P<viewer>[\w\s'\-\.]+)",
     "application_viewed", "Application viewed by recruiter"),
    (r"(?P<name>[\w\s'\-\.]+) viewed your profile", "profile_viewed",
     "LinkedIn profile view"),
]


def parse_linkedin_email(msg: dict) -> Optional[dict]:
    """Extract structured event from a Gmail message dict.

    Returns: {event_type, name_or_company, raw_subject, message_id} or None
             if the message isn't a recognized LinkedIn pattern.

    Phase 3 ship 3/3 will wire this against actual Gmail API responses.
    """
    headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
    sender = headers.get("From", "")

    if not any(re.search(p, sender, re.IGNORECASE) for p in LINKEDIN_SENDER_PATTERNS):
        return None

    subject = headers.get("Subject", "")
    for pattern, event_type, _desc in SUBJECT_PATTERNS:
        m = re.search(pattern, subject, re.IGNORECASE)
        if m:
            return {
                "event_type": event_type,
                "matched_name": m.groupdict().get("name") or m.groupdict().get("company") or "",
                "raw_subject": subject,
                "raw_sender": sender,
                "gmail_message_id": msg.get("id"),
            }
    return None


def fetch_linkedin_emails(creds: "Credentials", since_iso: Optional[str] = None,
                          max_results: int = 50) -> list:
    """Fetch LinkedIn notification emails since the given ISO timestamp.

    Returns a list of Gmail message dicts (headers only — From, Subject, Date).
    Each dict has at least: {id, payload: {headers: [...]}}.
    """
    service = build("gmail", "v1", credentials=creds)

    # Build query: from:linkedin.com after:<unix_timestamp>
    query = "from:linkedin.com"
    if since_iso:
        try:
            dt = datetime.fromisoformat(since_iso)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            ts = int(dt.timestamp())
            query += f" after:{ts}"
        except ValueError:
            pass  # ignore bad timestamp, fetch everything

    result = service.users().messages().list(
        userId="me",
        q=query,
        maxResults=max_results,
    ).execute()

    fetched = []
    for m in result.get("messages", []):
        full = service.users().messages().get(
            userId="me",
            id=m["id"],
            format="metadata",
            metadataHeaders=["From", "Subject", "Date"],
        ).execute()
        fetched.append(full)
    return fetched


def _normalize_name(name: str) -> str:
    """Lowercase + collapse whitespace + strip punctuation."""
    if not name:
        return ""
    name = re.sub(r"[^\w\s]", " ", name)
    return " ".join(name.lower().split())


def match_contact_in_tracker(conn: sqlite3.Connection, matched_name: str) -> Optional[dict]:
    """Tiered fuzzy match: exact -> case-insensitive -> last-name -> first-name.

    Returns dict with keys: id, job_id, name (or None if no match).
    """
    if not matched_name or not matched_name.strip():
        return None

    needle = _normalize_name(matched_name)
    if not needle:
        return None

    rows = conn.execute(
        "SELECT id, job_id, name FROM contacts ORDER BY id"
    ).fetchall()

    # Tier 1: exact case-insensitive
    for r in rows:
        if _normalize_name(r["name"]) == needle:
            return dict(r)

    # Tier 2: last-name match (last token of needle vs last token of any contact)
    needle_tokens = needle.split()
    if needle_tokens:
        last_needle = needle_tokens[-1]
        for r in rows:
            contact_tokens = _normalize_name(r["name"]).split()
            if contact_tokens and contact_tokens[-1] == last_needle:
                return dict(r)

    # Tier 3: first-name match (only if needle is single token, or as fallback)
    if needle_tokens:
        first_needle = needle_tokens[0]
        for r in rows:
            contact_tokens = _normalize_name(r["name"]).split()
            if contact_tokens and contact_tokens[0] == first_needle:
                return dict(r)

    # Tier 4: any-token overlap (avoid false positives by requiring >=4 chars)
    if needle_tokens:
        long_needles = {t for t in needle_tokens if len(t) >= 4}
        for r in rows:
            contact_tokens = set(_normalize_name(r["name"]).split())
            if long_needles & contact_tokens:
                return dict(r)

    return None


def _get_sync_state(conn: sqlite3.Connection, key: str) -> Optional[str]:
    row = conn.execute(
        "SELECT value FROM sync_state WHERE key = ?", (key,)
    ).fetchone()
    return row["value"] if row else None


def _set_sync_state(conn: sqlite3.Connection, key: str, value: str) -> None:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    existing = conn.execute(
        "SELECT key FROM sync_state WHERE key = ?", (key,)
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE sync_state SET value = ?, updated_at = ? WHERE key = ?",
            (value, now, key),
        )
    else:
        conn.execute(
            "INSERT INTO sync_state (key, value, updated_at) VALUES (?, ?, ?)",
            (key, value, now),
        )


def _already_processed(conn: sqlite3.Connection, gmail_message_id: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM processed_messages WHERE gmail_message_id = ?",
        (gmail_message_id,),
    ).fetchone()
    return row is not None


def _mark_processed(conn: sqlite3.Connection, gmail_message_id: str, event_id: Optional[int]) -> None:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    conn.execute(
        "INSERT OR REPLACE INTO processed_messages (gmail_message_id, event_id, processed_at) "
        "VALUES (?, ?, ?)",
        (gmail_message_id, event_id, now),
    )


def sync_to_tracker(conn: sqlite3.Connection) -> dict:
    """Main sync entrypoint: pull new LinkedIn emails -> parse -> match -> log events.

    Returns: {ok, fetched, parsed, logged, unmatched, last_sync, duration_s}.
    """
    started = datetime.now(timezone.utc)

    creds = load_credentials(conn)
    if not creds:
        return {
            "ok": False,
            "error": "not_authorized",
            "message": "Gmail not authorized yet. Visit /auth/gmail/start to connect.",
        }

    # Determine since timestamp
    last_sync = _get_sync_state(conn, "last_gmail_sync")
    if not last_sync:
        # First sync: look back 7 days
        last_sync = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat(timespec="seconds")

    try:
        messages = fetch_linkedin_emails(creds, since_iso=last_sync)
    except Exception as exc:
        return {
            "ok": False,
            "error": "fetch_failed",
            "message": f"Gmail API call failed: {exc}",
        }

    fetched = len(messages)
    parsed_count = 0
    logged = []
    unmatched = []

    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")

    for msg in messages:
        gmail_id = msg.get("id")
        if not gmail_id or _already_processed(conn, gmail_id):
            continue

        parsed = parse_linkedin_email(msg)
        if not parsed:
            # Not a recognized LinkedIn pattern — mark processed anyway so we don't re-check
            _mark_processed(conn, gmail_id, None)
            continue

        parsed_count += 1
        contact = match_contact_in_tracker(conn, parsed["matched_name"])

        if contact:
            # Log a real event tied to that contact + its job
            cursor = conn.execute(
                "INSERT INTO events (job_id, contact_id, event_type, body, occurred_at, recorded_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    contact["job_id"],
                    contact["id"],
                    parsed["event_type"],
                    f"[Gmail] {parsed['raw_subject']}",
                    now_iso,
                    now_iso,
                ),
            )
            new_event_id = cursor.lastrowid
            # Touch the job's last_activity_at
            conn.execute(
                "UPDATE jobs SET last_activity_at = ? WHERE id = ?",
                (now_iso, contact["job_id"]),
            )
            _mark_processed(conn, gmail_id, new_event_id)
            logged.append({
                "gmail_id": gmail_id,
                "contact": contact["name"],
                "job_id": contact["job_id"],
                "event_type": parsed["event_type"],
                "subject": parsed["raw_subject"],
            })
        else:
            unmatched.append({
                "name": parsed["matched_name"],
                "event_type": parsed["event_type"],
                "subject": parsed["raw_subject"],
            })
            # Don't mark as processed — user may add the contact later and we want to retry

    _set_sync_state(conn, "last_gmail_sync", now_iso)
    conn.commit()

    duration_s = (datetime.now(timezone.utc) - started).total_seconds()

    return {
        "ok": True,
        "fetched": fetched,
        "parsed": parsed_count,
        "logged": len(logged),
        "logged_details": logged,
        "unmatched": unmatched,
        "last_sync": now_iso,
        "duration_s": round(duration_s, 2),
    }


def get_last_sync(conn: sqlite3.Connection) -> Optional[str]:
    """Returns the ISO timestamp of the most recent successful Gmail sync, or None."""
    return _get_sync_state(conn, "last_gmail_sync")
