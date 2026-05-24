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
from datetime import datetime, timedelta, timezone
from typing import Optional

from db import Connection, insert_returning_id, upsert_processed_message

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


def build_authorize_url(conn: Connection) -> str:
    """Build the URL to send the user to Google's consent screen.

    Google's OAuth now requires PKCE end-to-end: the authorize step sends a
    code_challenge derived from a random code_verifier, and the token-exchange
    step must echo back the same code_verifier. Since each HTTP request creates
    a fresh Flow object, we persist the code_verifier in sync_state keyed by
    the state token that Google will echo back on /auth/gmail/callback.
    """
    flow = build_flow()
    flow.autogenerate_code_verifier = True  # enable PKCE
    auth_url, returned_state = flow.authorization_url(
        access_type="offline",  # request a refresh_token
        prompt="consent",       # force consent so we always get a refresh_token
        include_granted_scopes="true",
    )
    if flow.code_verifier:
        _store_pkce_verifier(conn, returned_state, flow.code_verifier)
    return auth_url


def exchange_code_for_token(conn: Connection, code: str, state: str) -> "Credentials":
    """Exchange the OAuth callback code for credentials.

    Pulls the persisted code_verifier for this state (set by build_authorize_url)
    and feeds it to the token-exchange request so Google accepts the swap.
    """
    flow = build_flow()
    verifier = _pop_pkce_verifier(conn, state) if state else None
    if verifier:
        flow.code_verifier = verifier
    flow.fetch_token(code=code)
    return flow.credentials


def _pkce_key(state: str) -> str:
    return f"oauth_pkce_{state}"


def _store_pkce_verifier(conn: Connection, state: str, code_verifier: str) -> None:
    """Persist PKCE code_verifier keyed by Google-supplied state token."""
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    key = _pkce_key(state)
    existing = conn.execute(
        "SELECT key FROM sync_state WHERE key = ?", (key,)
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE sync_state SET value = ?, updated_at = ? WHERE key = ?",
            (code_verifier, now, key),
        )
    else:
        conn.execute(
            "INSERT INTO sync_state (key, value, updated_at) VALUES (?, ?, ?)",
            (key, code_verifier, now),
        )
    conn.commit()


def _pop_pkce_verifier(conn: Connection, state: str) -> Optional[str]:
    """Retrieve + delete the persisted code_verifier for this state."""
    key = _pkce_key(state)
    row = conn.execute(
        "SELECT value FROM sync_state WHERE key = ?", (key,)
    ).fetchone()
    if not row or not row["value"]:
        return None
    conn.execute("DELETE FROM sync_state WHERE key = ?", (key,))
    conn.commit()
    return row["value"]


# ─────────────────────────────────────────────────────────────────────────────
# Token storage (Phase 3 ship 2/3 will complete these)
# ─────────────────────────────────────────────────────────────────────────────

def store_credentials(conn: Connection, creds: "Credentials", user_email: str = "") -> None:
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


def load_credentials(conn: Connection) -> Optional["Credentials"]:
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
# Email parsing — LinkedIn relationship events + ATS application emails
# ─────────────────────────────────────────────────────────────────────────────

# Sender filter — covers LinkedIn + the common ATS systems and role-based
# recruiting addresses companies use (no-reply, careers, recruiting, etc.).
RELEVANT_SENDER_PATTERNS = [
    # LinkedIn
    r"@linkedin\.com",
    r"@e?\.?linkedin\.com",
    r"@em\.linkedin\.com",
    # Generic role-based addresses
    r"no-?reply@",
    r"noreply@",
    r"careers@",
    r"recruiting@",
    r"recruiter@",
    r"hiring@",
    r"jobs@",
    r"talent@",
    r"hr@",
    r"applications@",
    r"people-?ops@",
    # Major ATS platforms
    r"@greenhouse\.io",
    r"@lever\.co",
    r"@workable\.com",
    r"@.*myworkdayjobs\.com",
    r"@taleo\.net",
    r"@icims\.com",
    r"@bamboohr\.com",
    r"@smartrecruiters\.com",
    r"@jobvite\.com",
    r"@successfactors\.com",
    r"@ashbyhq\.com",
]

# Pipeline status ranking — used to prevent auto-downgrades when an old email
# arrives after status has advanced (e.g. don't reset interview -> applied).
STATUS_RANK = {
    "saved": 0,
    "applied": 1,
    "replied": 2,
    "interview": 3,
    "offer": 4,
    "rejected": 5,    # terminal
    "backlog": -1,    # never auto-promote into backlog
}

# Subject regex patterns. Each tuple: (regex, event_type, target_status).
# target_status: if set, sync auto-advances jobs.status to this value (but
# never moves backwards in the pipeline ordering above).
SUBJECT_PATTERNS = [
    # ─── LinkedIn relationship events ──────────────────────────────────────
    (r"(?P<name>[\w\s'\-\.]+?) accepted your invitation", "connection_accepted", None),
    (r"New message from (?P<name>[\w\s'\-\.]+)", "message_received", None),
    (r"(?P<name>[\w\s'\-\.]+) sent you a message", "message_received", None),
    (r"InMail from (?P<name>[\w\s'\-\.]+)", "inmail_received", None),
    (r"(?P<name>[\w\s'\-\.]+) viewed your profile", "profile_viewed", None),

    # ─── Application acknowledged (ATS) ────────────────────────────────────
    (r"Thank you for applying to (?P<company>[\w\s'\-\.,&]+)", "application_acknowledged", "applied"),
    (r"Thank you for your application(?:.*?(?:to|at|with)\s+(?P<company>[\w\s'\-\.,&]+))?", "application_acknowledged", "applied"),
    (r"We received your application", "application_acknowledged", "applied"),
    (r"Your application(?:.*?(?:to|at|with|for))?\s+(?P<company>[\w\s'\-\.,&]+?)\s+(?:has been received|received|is being reviewed)", "application_acknowledged", "applied"),
    (r"Application (?:received|confirmation)", "application_acknowledged", "applied"),
    (r"Your application was sent to (?P<company>[\w\s'\-\.,&]+)", "application_sent", "applied"),

    # ─── Recruiter interest / next steps ───────────────────────────────────
    (r"(?P<company>[\w\s'\-\.,&]+) is interested in your application", "application_interest", "replied"),
    (r"Next steps (?:on|for|in) (?:your|the)", "recruiter_interest", "replied"),
    (r"Your application was viewed", "application_viewed", None),

    # ─── Interview ─────────────────────────────────────────────────────────
    (r"Interview invitation", "interview_invited", "interview"),
    (r"Invitation to interview", "interview_invited", "interview"),
    (r"Schedule (?:an? )?(?:initial |first |phone |video |onsite )?interview", "interview_invited", "interview"),
    (r"(?:Phone|Video|Onsite|Tech|Technical)\s+interview", "interview_invited", "interview"),
    (r"Interview scheduled", "interview_scheduled", "interview"),

    # ─── Offer ─────────────────────────────────────────────────────────────
    (r"(?:Job|Offer|Employment)\s+(?:offer|letter)", "offer_received", "offer"),
    (r"Offer of employment", "offer_received", "offer"),

    # ─── Rejection ─────────────────────────────────────────────────────────
    (r"Unfortunately,?\s+we", "application_rejected", "rejected"),
    (r"(?:will|won't)\s+not\s+be\s+(?:moving forward|proceeding|continuing)", "application_rejected", "rejected"),
    (r"After (?:careful |thorough )?(?:consideration|review)", "application_rejected", "rejected"),
    (r"Regretfully", "application_rejected", "rejected"),
    (r"decided to (?:pursue|go with|move forward with) other", "application_rejected", "rejected"),
    (r"(?:not |un)?selected", "application_rejected", "rejected"),
]


def _normalize_company(s: str) -> str:
    """Normalize a company string for fuzzy comparison."""
    if not s:
        return ""
    s = re.sub(r"[^\w\s]", " ", s)
    return " ".join(s.lower().split())


def parse_email(msg: dict) -> Optional[dict]:
    """Extract a structured event from a Gmail message.

    Returns dict with: event_type, target_status, matched_name, matched_company,
    raw_subject, raw_sender, gmail_message_id, body_snippet — or None if the
    sender/subject didn't match any pattern.

    If subject didn't yield a company name, falls back to the sender's domain.
    """
    headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
    sender = headers.get("From", "")
    subject = headers.get("Subject", "")

    if not any(re.search(p, sender, re.IGNORECASE) for p in RELEVANT_SENDER_PATTERNS):
        return None

    matched_event_type = None
    matched_target_status = None
    matched_name = ""
    matched_company = ""

    for pattern, event_type, target_status in SUBJECT_PATTERNS:
        m = re.search(pattern, subject, re.IGNORECASE)
        if not m:
            continue
        matched_event_type = event_type
        matched_target_status = target_status
        groups = m.groupdict()
        matched_name = (groups.get("name") or "").strip()
        matched_company = (groups.get("company") or "").strip()
        break

    if matched_event_type is None:
        return None

    # If subject captured neither name nor company, fall back to sender's domain
    # (e.g. no-reply@disco.com → "disco") so rejection / generic emails still match.
    if not matched_company and not matched_name:
        domain_match = re.search(r"@([\w\.-]+)", sender)
        if domain_match:
            domain_parts = domain_match.group(1).split(".")
            if len(domain_parts) >= 2:
                # Use the second-to-last label (the "brand" before TLD).
                matched_company = domain_parts[-2]

    return {
        "event_type": matched_event_type,
        "target_status": matched_target_status,
        "matched_name": matched_name,
        "matched_company": matched_company,
        "raw_subject": subject,
        "raw_sender": sender,
        "gmail_message_id": msg.get("id"),
        "body_snippet": (msg.get("snippet") or "")[:500],
    }


# Backwards-compat alias for any external code still importing the old name.
parse_linkedin_email = parse_email


def match_job_by_company(conn: Connection, company_name: str) -> Optional[dict]:
    """Fuzzy-match a captured company string to a job in the tracker.

    Tier 1: exact normalized match (case-insensitive, punctuation stripped).
    Tier 2: prefix match either direction (e.g. captured "GHX - Product Owner"
            matches tracker company "GHX India" via shared "ghx" prefix token).
    Tier 3: token overlap with words ≥3 chars (avoids "of", "and").

    Returns {id, company, status} dict for the best match, or None.
    """
    if not company_name or not company_name.strip():
        return None
    needle = _normalize_company(company_name)
    if not needle:
        return None
    needle_tokens = {t for t in needle.split() if len(t) >= 3}

    rows = conn.execute(
        "SELECT id, company, status FROM jobs WHERE company IS NOT NULL"
    ).fetchall()

    candidates = []
    for r in rows:
        job_company = _normalize_company(r["company"])
        if not job_company:
            continue
        job_tokens = {t for t in job_company.split() if len(t) >= 3}

        if job_company == needle:
            return dict(r)
        if needle.startswith(job_company) or job_company.startswith(needle):
            candidates.append((100, dict(r)))
            continue
        overlap = job_tokens & needle_tokens
        if overlap:
            candidates.append((len(overlap) * 10, dict(r)))

    if not candidates:
        return None
    candidates.sort(reverse=True, key=lambda x: x[0])
    return candidates[0][1]


def fetch_relevant_emails(creds: "Credentials", since_iso: Optional[str] = None,
                          max_results: int = 100) -> list:
    """Fetch potentially-relevant emails (LinkedIn + ATS + recruiting addresses).

    Returns Gmail message dicts with metadata headers + snippet (the first
    ~200 chars of body). We don't fetch full body — snippet is enough for the
    activity feed; user clicks the Gmail link if they want the full email.
    """
    service = build("gmail", "v1", credentials=creds)

    sender_query = " OR ".join([
        "from:linkedin.com",
        "from:no-reply",
        "from:noreply",
        "from:careers",
        "from:recruiting",
        "from:recruiter",
        "from:talent",
        "from:hiring",
        "from:jobs",
        "from:hr",
        "from:applications",
        "from:greenhouse.io",
        "from:lever.co",
        "from:workable.com",
        "from:myworkdayjobs.com",
        "from:ashbyhq.com",
    ])
    query = f"({sender_query})"
    if since_iso:
        try:
            dt = datetime.fromisoformat(since_iso)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            ts = int(dt.timestamp())
            query += f" after:{ts}"
        except ValueError:
            pass

    result = service.users().messages().list(
        userId="me", q=query, maxResults=max_results,
    ).execute()

    fetched = []
    for m in result.get("messages", []):
        full = service.users().messages().get(
            userId="me", id=m["id"],
            format="metadata",
            metadataHeaders=["From", "Subject", "Date"],
        ).execute()
        fetched.append(full)
    return fetched


# Backwards-compat alias for any external code still importing the old name.
fetch_linkedin_emails = fetch_relevant_emails


def _normalize_name(name: str) -> str:
    """Lowercase + collapse whitespace + strip punctuation."""
    if not name:
        return ""
    name = re.sub(r"[^\w\s]", " ", name)
    return " ".join(name.lower().split())


def match_contact_in_tracker(conn: Connection, matched_name: str) -> Optional[dict]:
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


def _get_sync_state(conn: Connection, key: str) -> Optional[str]:
    row = conn.execute(
        "SELECT value FROM sync_state WHERE key = ?", (key,)
    ).fetchone()
    return row["value"] if row else None


def _set_sync_state(conn: Connection, key: str, value: str) -> None:
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


def _already_processed(conn: Connection, gmail_message_id: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM processed_messages WHERE gmail_message_id = ?",
        (gmail_message_id,),
    ).fetchone()
    return row is not None


def _mark_processed(conn: Connection, gmail_message_id: str, event_id: Optional[int]) -> None:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    upsert_processed_message(conn, gmail_message_id, event_id, now)


def sync_to_tracker(conn: Connection) -> dict:
    """Pull recent emails → parse → match to contact or job → log events.

    Tries two match paths per email:
      1. matched_name → contact lookup (LinkedIn relationship events)
      2. matched_company → job lookup (ATS application emails)
    Whichever lands first wins. If both miss, the message goes to the
    'unmatched' bucket and is NOT marked processed (so user can re-sync after
    adding the missing contact/job).

    Auto-advances jobs.status when an email's pattern carries a target_status
    that's further along the pipeline than the job's current status. Never
    moves backwards (won't reset interview → applied on stale acks).

    Returns: {ok, fetched, parsed, logged, unmatched, status_changes, last_sync,
              duration_s}.
    """
    started = datetime.now(timezone.utc)

    creds = load_credentials(conn)
    if not creds:
        return {
            "ok": False,
            "error": "not_authorized",
            "message": "Gmail not authorized yet. Visit /auth/gmail/start to connect.",
        }

    last_sync = _get_sync_state(conn, "last_gmail_sync")
    if not last_sync:
        last_sync = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat(timespec="seconds")

    try:
        messages = fetch_relevant_emails(creds, since_iso=last_sync)
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
    status_changes = []

    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")

    for msg in messages:
        gmail_id = msg.get("id")
        if not gmail_id or _already_processed(conn, gmail_id):
            continue

        parsed = parse_email(msg)
        if not parsed:
            _mark_processed(conn, gmail_id, None)
            continue
        parsed_count += 1

        # Match priority: contact (LinkedIn) → job (ATS).
        contact = None
        job = None
        if parsed["matched_name"]:
            contact = match_contact_in_tracker(conn, parsed["matched_name"])
            if contact:
                job_row = conn.execute(
                    "SELECT id, status, company FROM jobs WHERE id = ?",
                    (contact["job_id"],),
                ).fetchone()
                if job_row:
                    job = dict(job_row)
        if not job and parsed["matched_company"]:
            job = match_job_by_company(conn, parsed["matched_company"])

        if not job:
            unmatched.append({
                "subject": parsed["raw_subject"],
                "sender": parsed["raw_sender"],
                "event_type": parsed["event_type"],
                "tried_name": parsed["matched_name"] or None,
                "tried_company": parsed["matched_company"] or None,
            })
            # Intentionally NOT marked processed — user may add the missing
            # contact/job later and re-trigger sync.
            continue

        # Multi-line event body so the activity feed shows real content + a
        # link back to Gmail. The job_detail template renders body as plain
        # text inside a <pre>-ish container, so newlines display naturally.
        gmail_url = f"https://mail.google.com/mail/u/0/#inbox/{gmail_id}"
        event_body = (
            f"{parsed['raw_subject']}\n"
            f"From: {parsed['raw_sender']}\n\n"
            f"{parsed['body_snippet']}\n\n"
            f"Open in Gmail: {gmail_url}"
        )

        new_event_id = insert_returning_id(
            conn,
            "INSERT INTO events (job_id, contact_id, event_type, body, occurred_at, recorded_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                job["id"],
                contact["id"] if contact else None,
                parsed["event_type"],
                event_body,
                now_iso,
                now_iso,
            ),
        )
        conn.execute(
            "UPDATE jobs SET last_activity_at = ? WHERE id = ?",
            (now_iso, job["id"]),
        )

        # Auto-advance status if the pattern set a target and it's further
        # along the pipeline than the job's current status.
        if parsed["target_status"]:
            current_rank = STATUS_RANK.get(job["status"], 0)
            target_rank = STATUS_RANK.get(parsed["target_status"], 0)
            if target_rank > current_rank:
                conn.execute(
                    "UPDATE jobs SET status = ?, last_activity_at = ? WHERE id = ?",
                    (parsed["target_status"], now_iso, job["id"]),
                )
                conn.execute(
                    "INSERT INTO events (job_id, event_type, body, occurred_at, recorded_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (
                        job["id"],
                        "status_change",
                        f"{job['status']} -> {parsed['target_status']} (auto from Gmail: {parsed['event_type']})",
                        now_iso,
                        now_iso,
                    ),
                )
                status_changes.append({
                    "job_id": job["id"],
                    "company": job.get("company"),
                    "from": job["status"],
                    "to": parsed["target_status"],
                    "reason": parsed["event_type"],
                })

        _mark_processed(conn, gmail_id, new_event_id)
        logged.append({
            "gmail_id": gmail_id,
            "company": job.get("company"),
            "contact": contact["name"] if contact else None,
            "job_id": job["id"],
            "event_type": parsed["event_type"],
            "subject": parsed["raw_subject"],
        })

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
        "status_changes": status_changes,
        "last_sync": now_iso,
        "duration_s": round(duration_s, 2),
    }


def get_last_sync(conn: Connection) -> Optional[str]:
    """Returns the ISO timestamp of the most recent successful Gmail sync, or None."""
    return _get_sync_state(conn, "last_gmail_sync")
