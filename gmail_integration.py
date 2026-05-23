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
from datetime import datetime, timezone
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


def fetch_linkedin_emails(creds: "Credentials", since_iso: Optional[str] = None) -> list:
    """Fetch LinkedIn emails from Gmail since the given ISO timestamp.

    Phase 3 ship 3/3 will implement this using:
        service = build("gmail", "v1", credentials=creds)
        results = service.users().messages().list(
            userId="me",
            q=f"from:linkedin.com after:{since_iso}",
            maxResults=50,
        ).execute()
    """
    raise NotImplementedError("Phase 3 ship 3/3 will implement this.")


def match_contact_in_tracker(conn: sqlite3.Connection, matched_name: str) -> Optional[dict]:
    """Find a contact in the tracker whose name fuzzy-matches the parsed name.

    Phase 3 ship 3/3 will implement this with:
    - Exact match first
    - Then last-name match
    - Then word-overlap fuzzy match (rapidfuzz lib OR simple in-Python)
    Returns the contact row + parent job, or None.
    """
    raise NotImplementedError("Phase 3 ship 3/3 will implement this.")


def sync_to_tracker(conn: sqlite3.Connection) -> dict:
    """Main entry: fetch new LinkedIn emails, parse, match contacts, log events.

    Returns a summary: {fetched, parsed, matched, logged, unmatched_names}.

    Phase 3 ship 3/3 will tie all the above functions together.
    """
    raise NotImplementedError("Phase 3 ship 3/3 will implement this.")
