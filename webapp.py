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
from starlette.middleware.sessions import SessionMiddleware

import gmail_integration
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


PUBLIC_PATHS = {
    "/healthz",                  # Render liveness probe
    "/login",                    # public sign-in screen
    "/extension/capture",        # has its own X-Extension-Token auth
    "/auth/gmail/start",         # OAuth handshake start (user not signed in yet)
    "/auth/gmail/callback",      # OAuth handshake return (user authenticating)
}


def require_auth(
    request: Request,
    credentials: Optional[HTTPBasicCredentials] = Depends(security),
):
    """Auth gate. Checks in this order:
      1. Public paths (healthz, login, OAuth start/callback, extension capture)
      2. Session cookie set by Google OAuth callback — primary auth in v2
      3. HTTP Basic Auth fallback — admin/legacy only
    If none match, raise 401 (browsers will show Basic Auth dialog) — or
    we could redirect to /login. For now keep 401 to avoid breaking API calls.
    """
    if request.url.path in PUBLIC_PATHS:
        return

    # 1. Session-cookie auth (the new path: user signed in via Google OAuth)
    user_id = request.session.get("user_id")
    if user_id:
        return  # session valid; allow through

    # 2. Local dev escape hatch: no admin creds configured
    if not ADMIN_USERNAME or not ADMIN_PASSWORD:
        return

    # 3. HTTP Basic Auth fallback (legacy / admin debugging)
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

# Session middleware — must be added BEFORE any route is hit so request.session
# is available in require_auth. Uses itsdangerous under the hood. SESSION_SECRET
# env var should be a long random string in production; for local dev we
# generate a stable one from the ADMIN_PASSWORD if not set.
SESSION_SECRET = (
    os.environ.get("SESSION_SECRET")
    or (ADMIN_PASSWORD or "local-dev-session-secret-change-me") + "::session-key"
)
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    session_cookie="jt_session",
    max_age=60 * 60 * 24 * 30,   # 30 days
    # Force HTTPS-only cookie in production (Render sets $PORT) so the
    # session ID can never leak over plain HTTP. In local dev we leave it
    # off so http://localhost:8000 sessions actually work.
    https_only=bool(PORT_ENV),
    same_site="lax",
)


def current_user_id(request: Request) -> int:
    """Return the logged-in user's id for query-scoping.

    Defaults to 1 when a request has no session — this keeps two paths working:
      (a) HTTP Basic Auth fallback (legacy / admin), where there is no OAuth
          session but all existing data belongs to user 1.
      (b) Local dev with no admin creds configured (require_auth lets through).
    When the project goes truly multi-tenant (constraint rework on
    oauth_tokens) the default can be tightened to raise instead of returning 1.
    """
    return request.session.get("user_id") or 1


@app.get("/healthz")
def healthz():
    """Public liveness probe for Render. Auth-bypassed via PUBLIC_PATHS."""
    return {"ok": True}


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    """Public sign-in screen. Auth-bypassed via PUBLIC_PATHS so users can
    actually reach it. Renders the Welcome card with the Continue-with-Google
    button. Once Google OAuth wiring lands, the button will route to
    /auth/google/start which exchanges the code for tokens, creates a user
    row, sets a session cookie, and redirects to the homepage."""
    return TEMPLATES.TemplateResponse("login.html", {"request": request})


def _find_job_posting_in_ld(node):
    """Recurse into JSON-LD data (which can be nested in @graph arrays)
    to find a JobPosting schema entry. Returns the JobPosting dict or None."""
    if isinstance(node, dict):
        t = node.get("@type")
        if t == "JobPosting" or (isinstance(t, list) and "JobPosting" in t):
            return node
        for v in node.values():
            found = _find_job_posting_in_ld(v)
            if found:
                return found
    elif isinstance(node, list):
        for item in node:
            found = _find_job_posting_in_ld(item)
            if found:
                return found
    return None


@app.post("/jobs/from-url")
def jobs_from_url(request: Request, payload: dict = Body(...)):
    """Agent endpoint: paste any URL, the backend fetches the page,
    parses structured data (JSON-LD JobPosting if present), falls back to
    raw text + Gemini extraction. Creates a lead with all fields populated.

    No Chrome extension needed. User pastes URL, gets a lead.

    Flow:
      1. Dedup by URL (skip if already in tracker)
      2. If LinkedIn URL: use linkedin_fetch.py (public guest endpoint)
      3. Otherwise: HTTP GET with browser User-Agent, parse JSON-LD
      4. If structured data still thin, use Gemini to extract from raw text
      5. Insert into jobs with status=lead, source=agent
    """
    import urllib.request
    import urllib.error
    import re
    import json as _json

    url = (payload.get("url") or "").strip()
    if not url:
        return JSONResponse(status_code=400, content={"error": "missing_url"})
    if not (url.startswith("http://") or url.startswith("https://")):
        return JSONResponse(status_code=400, content={"error": "invalid_url",
                            "message": "URL must start with http or https."})

    tracker.init_db()
    uid = current_user_id(request)

    # Dedup: same URL already a job for THIS user? Return existing.
    # Scoped by user_id so two users can each save the same URL independently.
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id, title, company, status FROM jobs WHERE link = ? AND user_id = ? LIMIT 1",
            (url, uid),
        ).fetchone()
        if existing:
            return {
                "ok": True,
                "job_id": existing["id"],
                "title": existing["title"],
                "company": existing["company"],
                "status": existing["status"],
                "deduped": True,
                "message": "Already in your tracker. Returning existing job.",
            }

    # Extraction state
    extracted_title = ""
    extracted_company = ""
    extracted_location = ""
    extracted_jd = ""
    source_used = []

    # ── LinkedIn-specific path: use the guest endpoint we already have ──
    is_linkedin_job = (
        "linkedin.com/jobs/view/" in url
        or "linkedin.com/comm/jobs/view/" in url
        or ("linkedin.com/jobs" in url and "currentJobId=" in url)
    )
    if is_linkedin_job:
        try:
            import linkedin_fetch
            ln = linkedin_fetch.fetch_job_details(url)
            if ln:
                extracted_title = (ln.get("title") or "").strip()
                extracted_company = (ln.get("company") or "").strip()
                extracted_location = (ln.get("location") or "").strip()
                extracted_jd = (ln.get("jd_text") or "")[:80000]
                source_used.append("linkedin_guest")
        except Exception:
            pass

    # ── Generic path: HTTP GET + JSON-LD parsing ──
    if not extracted_jd or not extracted_title:
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
                "Accept-Language": "en-US,en;q=0.9",
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status != 200:
                    return JSONResponse(
                        status_code=502,
                        content={"error": "fetch_failed",
                                 "message": f"Target site returned HTTP {resp.status}"},
                    )
                html = resp.read().decode("utf-8", errors="replace")

            # Parse all JSON-LD <script> blocks and look for a JobPosting
            ld_pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
            for raw_block in re.findall(ld_pattern, html, re.DOTALL | re.IGNORECASE):
                try:
                    data = _json.loads(raw_block.strip())
                    jp = _find_job_posting_in_ld(data)
                    if jp:
                        if not extracted_title:
                            extracted_title = (jp.get("title") or "").strip()
                        if not extracted_company:
                            org = jp.get("hiringOrganization") or {}
                            if isinstance(org, dict):
                                extracted_company = (org.get("name") or "").strip()
                            elif isinstance(org, str):
                                extracted_company = org.strip()
                        if not extracted_location:
                            loc = jp.get("jobLocation")
                            loc_to_parse = None
                            if isinstance(loc, dict):
                                loc_to_parse = loc
                            elif isinstance(loc, list) and loc:
                                first = loc[0]
                                if isinstance(first, dict):
                                    loc_to_parse = first
                            if loc_to_parse:
                                addr = loc_to_parse.get("address") or {}
                                if isinstance(addr, dict):
                                    parts = [addr.get("addressLocality"),
                                             addr.get("addressRegion"),
                                             addr.get("addressCountry")]
                                    extracted_location = ", ".join(p for p in parts if p)
                        if not extracted_jd:
                            desc = jp.get("description") or ""
                            if desc:
                                # Strip HTML from the description string
                                desc_clean = re.sub(r"<[^>]+>", " ", desc)
                                desc_clean = re.sub(r"\s+", " ", desc_clean).strip()
                                extracted_jd = desc_clean[:80000]
                        source_used.append("html_jsonld")
                        break
                except (ValueError, TypeError):
                    continue

            # If still no JD text, fall back to stripping all HTML and using body text
            if not extracted_jd:
                html_text = re.sub(r"<script[^>]*>.*?</script>", " ",
                                   html, flags=re.DOTALL | re.IGNORECASE)
                html_text = re.sub(r"<style[^>]*>.*?</style>", " ",
                                   html_text, flags=re.DOTALL | re.IGNORECASE)
                html_text = re.sub(r"<[^>]+>", " ", html_text)
                html_text = re.sub(r"\s+", " ", html_text).strip()
                extracted_jd = html_text[:80000]
                source_used.append("html_text")

            # Title fallback: <title> tag from HTML
            if not extracted_title:
                title_match = re.search(r"<title>([^<]+)</title>", html, re.IGNORECASE)
                if title_match:
                    extracted_title = title_match.group(1).strip()

            # Company fallback: og:site_name meta tag
            if not extracted_company:
                site_match = re.search(
                    r'<meta\s+property=["\']og:site_name["\']\s+content=["\']([^"\']+)["\']',
                    html, re.IGNORECASE,
                )
                if site_match:
                    extracted_company = site_match.group(1).strip()

        except urllib.error.HTTPError as e:
            return JSONResponse(
                status_code=502,
                content={"error": "fetch_failed",
                         "message": f"Target site returned HTTP {e.code}"},
            )
        except urllib.error.URLError as e:
            return JSONResponse(
                status_code=502,
                content={"error": "fetch_failed",
                         "message": f"Could not reach target site: {str(e.reason)[:120]}"},
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"error": "fetch_failed", "message": str(e)[:200]},
            )

    # Defaults for required fields
    final_title = (extracted_title or "Untitled job").strip()[:200]
    final_company = (extracted_company or "").strip()[:200]
    final_location = (extracted_location or "").strip()[:200]
    source_label = "+".join(source_used) if source_used else "unknown"

    now = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        new_id = insert_returning_id(
            conn,
            "INSERT INTO jobs (title, company, link, jd_raw_text, location, status, "
            "source, added_at, last_activity_at, user_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (final_title, final_company, url, extracted_jd[:80000], final_location,
             "lead", f"agent:{source_label}", now, now, uid),
        )
        conn.execute(
            "INSERT INTO events (job_id, event_type, body, occurred_at, recorded_at, user_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (new_id, "note",
             f"Captured via /jobs/from-url. Sources: {source_label}. "
             f"JD length: {len(extracted_jd)} chars.",
             now, now),
        )

    return {
        "ok": True,
        "job_id": new_id,
        "title": final_title,
        "company": final_company,
        "location": final_location,
        "source": source_label,
        "jd_chars": len(extracted_jd),
        "deduped": False,
    }


@app.post("/extension/capture")
def extension_capture(request: Request, payload: dict = Body(...)):
    """Chrome extension capture endpoint.

    Captures any job posting the user is browsing. Receives URL + title +
    page text from the extension popup, stores as a new lead in the jobs
    table with status='lead' and the raw page text in jd_raw_text. The user
    can then open the job detail page and run resume tailoring or pursue
    actions.

    Auth: validates X-Extension-Token header against EXTENSION_API_TOKEN env
    var. This is a single shared token for now — when per-user auth lands,
    we'll move to per-user tokens that map to user_id.
    """
    # Auth: single shared token via header
    token = request.headers.get("X-Extension-Token", "")
    expected = os.environ.get("EXTENSION_API_TOKEN", "")
    if not expected:
        return JSONResponse(
            status_code=503,
            content={"error": "extension_not_configured",
                     "message": "EXTENSION_API_TOKEN env var is not set on the server."},
        )
    if token != expected:
        return JSONResponse(
            status_code=401,
            content={"error": "invalid_token",
                     "message": "X-Extension-Token header is missing or wrong."},
        )

    url = (payload.get("url") or "").strip()
    title = (payload.get("title") or "").strip() or "Captured job"
    text = (payload.get("text") or "").strip()  # innerText - clean formatting
    text_all = (payload.get("text_all") or "").strip()  # textContent - includes hidden DOM
    json_ld = payload.get("json_ld") or []  # structured JobPosting data, when site provides it
    meta = payload.get("meta") or {}  # OpenGraph + meta tags

    if not url:
        return JSONResponse(status_code=400, content={"error": "missing_url"})
    if not text and not text_all:
        return JSONResponse(status_code=400, content={"error": "missing_text"})

    # Pick the richest text we got. textContent (text_all) includes hidden DOM
    # content like "Show more" JD blocks that LinkedIn collapses by default,
    # so it's usually a richer signal than innerText. Prefer it when present.
    if text_all and len(text_all) > len(text):
        primary_text = text_all
    else:
        primary_text = text

    # Look for a JobPosting in the JSON-LD blocks. schema.org JobPosting is
    # the cleanest source: most major job sites (LinkedIn, Indeed, Wellfound,
    # most company career pages on Greenhouse/Lever/Ashby) embed this.
    extracted_title = title
    extracted_company = ""
    extracted_location = ""
    extracted_jd = primary_text
    structured_source = None

    def _find_job_posting(node):
        """Recurse into JSON-LD blocks (sometimes nested in @graph arrays)
        to find a JobPosting schema entry."""
        if isinstance(node, dict):
            t = node.get("@type")
            if t == "JobPosting" or (isinstance(t, list) and "JobPosting" in t):
                return node
            for v in node.values():
                found = _find_job_posting(v)
                if found:
                    return found
        elif isinstance(node, list):
            for item in node:
                found = _find_job_posting(item)
                if found:
                    return found
        return None

    for block in json_ld:
        jp = _find_job_posting(block)
        if jp:
            extracted_title = (jp.get("title") or extracted_title).strip()
            hiring_org = jp.get("hiringOrganization") or {}
            if isinstance(hiring_org, dict):
                extracted_company = (hiring_org.get("name") or "").strip()
            elif isinstance(hiring_org, str):
                extracted_company = hiring_org.strip()
            loc = jp.get("jobLocation")
            if isinstance(loc, dict):
                addr = loc.get("address") or {}
                if isinstance(addr, dict):
                    parts = [addr.get("addressLocality"), addr.get("addressRegion"),
                             addr.get("addressCountry")]
                    extracted_location = ", ".join(p for p in parts if p)
            elif isinstance(loc, list) and loc:
                first = loc[0]
                if isinstance(first, dict):
                    addr = first.get("address") or {}
                    if isinstance(addr, dict):
                        parts = [addr.get("addressLocality"), addr.get("addressRegion"),
                                 addr.get("addressCountry")]
                        extracted_location = ", ".join(p for p in parts if p)
            desc = jp.get("description") or ""
            if desc:
                # JSON-LD description is often HTML; we keep it raw, can strip later
                extracted_jd = desc[:80000]
                structured_source = "json_ld"
            break

    # Cap the raw text we store
    extracted_jd = (extracted_jd or "")[:80000]

    # Fallback: if no JSON-LD company, try OpenGraph site_name as a hint
    if not extracted_company:
        extracted_company = (meta.get("og:site_name") or "").strip()

    # LinkedIn-specific backend fallback: LinkedIn's signed-in /jobs/view/
    # pages don't always expose clean JSON-LD or full JD text (the page is
    # heavily React-rendered and lazy-loads). We already have a working
    # public-guest-endpoint fetcher in linkedin_fetch.py — use it to
    # supplement whatever the extension captured. The guest endpoint
    # returns clean title, company, location, full JD.
    # URL shapes LinkedIn uses for jobs:
    #   /jobs/view/12345
    #   /comm/jobs/view/12345
    #   /jobs/search-results/?currentJobId=12345
    #   /jobs/collections/.../?currentJobId=12345
    is_linkedin_job = (
        "linkedin.com/jobs/view/" in url
        or "linkedin.com/comm/jobs/view/" in url
        or ("linkedin.com/jobs" in url and "currentJobId=" in url)
    )
    if is_linkedin_job:
        try:
            import linkedin_fetch
            guest = linkedin_fetch.fetch_job_details(url)
            if guest:
                # Use guest data to fill in gaps. Prefer extension extraction
                # when extension data is richer (e.g. user is signed in and
                # sees fields guest doesn't), otherwise use guest.
                if not extracted_company and guest.get("company"):
                    extracted_company = guest["company"]
                if not extracted_location and guest.get("location"):
                    extracted_location = guest["location"]
                # If extension's JD looks too thin (< 500 chars), guest is
                # almost certainly richer
                if guest.get("jd_text") and len(guest["jd_text"]) > len(extracted_jd):
                    extracted_jd = guest["jd_text"][:80000]
                    structured_source = (structured_source or "") + "+linkedin_guest"
                # Use guest title if extension's title is just "LinkedIn" or
                # the generic page title
                ext_title_low = extracted_title.lower()
                if guest.get("title") and ("linkedin" in ext_title_low or len(extracted_title) < 10):
                    extracted_title = guest["title"]
        except Exception:
            # Non-fatal: extension data alone is fine, just less rich
            pass

    tracker.init_db()
    # Extension uses a single shared token, not a per-user session — so we
    # tag captures to user_id=1 (Ajinkya, the only token holder today).
    # When per-user extension tokens land, this becomes a token→user_id lookup.
    uid = 1
    now = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        # Dedup: same URL already a job for this user? Return existing.
        existing = conn.execute(
            "SELECT id, title, company, status FROM jobs WHERE link = ? AND user_id = ? LIMIT 1",
            (url, uid),
        ).fetchone()
        if existing:
            return {
                "ok": True,
                "job_id": existing["id"],
                "title": existing["title"],
                "company": existing["company"],
                "status": existing["status"],
                "deduped": True,
                "message": "Already captured. Returning existing job.",
            }

        # Try to infer location from text if JSON-LD didn't have it.
        # Cheap heuristic: most JDs mention city + (Hybrid)/(Remote)/(On-site)
        # in the top section.
        location = extracted_location

        new_id = insert_returning_id(
            conn,
            "INSERT INTO jobs (title, company, link, jd_raw_text, location, status, source, "
            "notes, added_at, last_activity_at, user_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (extracted_title, extracted_company, url, extracted_jd, location,
             "lead", "extension",
             f"Captured via Chrome extension. Extraction source: "
             f"{structured_source or 'page text'}. "
             f"Length of JD captured: {len(extracted_jd)} chars.",
             now, now, uid),
        )
        event_body = (
            f"Captured from {url} via Chrome extension. "
            f"{'Structured data (JSON-LD JobPosting) found.' if structured_source else 'Used page text fallback.'} "
            f"Title: {extracted_title}. "
            f"Company: {extracted_company or 'unknown (will extract later)'}. "
            f"Location: {location or 'unknown'}."
        )
        conn.execute(
            "INSERT INTO events (job_id, event_type, body, occurred_at, recorded_at, user_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (new_id, "note", event_body, now, now, uid),
        )

    return {
        "ok": True,
        "job_id": new_id,
        "title": extracted_title,
        "company": extracted_company,
        "location": location,
        "deduped": False,
        "structured_source": structured_source,
        "message": f"Captured. Job #{new_id} added to your leads.",
    }


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
    uid = current_user_id(request)

    # Filter state from URL: ?status=applied,saved&flag=stale
    qp = request.query_params
    active_statuses = [s for s in (qp.get("status", "").split(",")) if s]
    active_flags = [f for f in (qp.get("flag", "").split(",")) if f]

    with get_connection() as conn:
        jobs_rows = conn.execute(
            "SELECT * FROM jobs WHERE user_id = ? ORDER BY id", (uid,)
        ).fetchall()
        contacts_rows = conn.execute(
            "SELECT * FROM contacts WHERE user_id = ? ORDER BY job_id, id", (uid,)
        ).fetchall()
        drafts_rows = conn.execute(
            """
            SELECT job_id, COUNT(*) AS n FROM events
            WHERE user_id = ?
              AND event_type = 'note'
              AND (body LIKE 'SUGGESTED%' OR body LIKE 'OPTIONAL%')
            GROUP BY job_id
            """,
            (uid,),
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

    # Leads waiting in the inbox — surfaced as a top banner on the pipeline so
    # the user lands after login and immediately sees "you have N to triage"
    # rather than discovering the leads page on their own.
    leads_waiting = sum(1 for j in jobs if j["status"] == "lead")

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
            creds = gmail_integration.load_credentials(conn, user_id=uid)
            gmail_state["authorized"] = creds is not None
            last_sync = gmail_integration.get_last_sync(conn, user_id=uid)
            gmail_state["last_sync"] = last_sync
            gmail_state["last_sync_rel"] = _format_relative_time(last_sync)
            gmail_state["last_sync_summary"] = gmail_integration.get_last_sync_summary(conn, user_id=uid)

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
            "leads_waiting": leads_waiting,
        },
    )


@app.get("/jobs/{job_id}", response_class=HTMLResponse)
def job_detail(job_id: int, request: Request):
    tracker.init_db()
    uid = current_user_id(request)
    with get_connection() as conn:
        job = conn.execute(
            "SELECT * FROM jobs WHERE id = ? AND user_id = ?", (job_id, uid),
        ).fetchone()
        if not job:
            return HTMLResponse(
                f"<h1>Job #{job_id} not found</h1><a href='/'>back</a>",
                status_code=404,
            )
        contacts = conn.execute(
            "SELECT * FROM contacts WHERE job_id = ? AND user_id = ? ORDER BY id",
            (job_id, uid),
        ).fetchall()
        events = conn.execute(
            "SELECT * FROM events WHERE job_id = ? AND user_id = ? ORDER BY occurred_at",
            (job_id, uid),
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
    uid = current_user_id(request)
    with get_connection() as conn:
        job = conn.execute(
            "SELECT * FROM jobs WHERE id = ? AND user_id = ?", (job_id, uid),
        ).fetchone()
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
            "pdf_url": f"/jobs/{job_id}/resume/pdf",
        },
    )


def _render_resume_pdf(resume_html: str, pdf_filename: str, request: Request):
    """Shared helper: render the clean PDF template + Playwright → PDF Response.

    Returns a FastAPI Response with the PDF bytes and a Content-Disposition
    that downloads as the stable per-role filename. On any Playwright failure
    returns a 503 JSON so the rest of the app stays healthy.
    """
    import pdf_export
    html = TEMPLATES.get_template("resume_pdf.html").render(
        request=request, resume_html=resume_html, pdf_filename=pdf_filename,
    )
    try:
        pdf_bytes = pdf_export.html_to_pdf(html)
    except RuntimeError as exc:
        return JSONResponse(
            status_code=503,
            content={"error": "pdf_unavailable", "message": str(exc)},
        )
    from fastapi import Response
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{pdf_filename}"'},
    )


@app.get("/jobs/{job_id}/resume/pdf")
def job_resume_pdf(job_id: int, request: Request):
    """Download a job's tailored resume as a real PDF (clickable links,
    selectable text) via Playwright. See pdf_export.py for the why."""
    tracker.init_db()
    uid = current_user_id(request)
    with get_connection() as conn:
        job = conn.execute(
            "SELECT * FROM jobs WHERE id = ? AND user_id = ?", (job_id, uid),
        ).fetchone()
    if not job:
        return JSONResponse(status_code=404, content={"error": "not_found"})
    job_dict = dict(job)
    resume_md = (job_dict.get("resume_md") or "").strip()
    if not resume_md:
        return JSONResponse(
            status_code=400,
            content={"error": "no_resume", "message": "No tailored resume on this job yet."},
        )
    resume_html = md_lib.markdown(resume_md, extensions=["extra", "sane_lists"])
    company_slug = _slugify_for_filename(job_dict.get("company") or "company")
    title_slug = _slugify_for_filename(job_dict.get("title") or "role")
    pdf_filename = f"Ajinkya_Kate_{company_slug}_{title_slug}.pdf"
    return _render_resume_pdf(resume_html, pdf_filename, request)


# ─────────────────────────────────────────────────────────────────────────────
# Job mutations (used by kanban drag-and-drop + future Add Job modal)
# ─────────────────────────────────────────────────────────────────────────────


@app.post("/jobs/{job_id}/status")
def update_job_status(job_id: int, request: Request, payload: dict = Body(...)):
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
    uid = current_user_id(request)
    now = datetime.now().isoformat(timespec="seconds")

    with get_connection() as conn:
        job = conn.execute(
            "SELECT id, status FROM jobs WHERE id = ? AND user_id = ?", (job_id, uid),
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
                "applied_at = COALESCE(applied_at, ?) WHERE id = ? AND user_id = ?",
                (new_status, now, today, job_id, uid),
            )
        else:
            conn.execute(
                "UPDATE jobs SET status = ?, last_activity_at = ? WHERE id = ? AND user_id = ?",
                (new_status, now, job_id, uid),
            )
        conn.execute(
            "INSERT INTO events (job_id, event_type, body, occurred_at, recorded_at, user_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (job_id, "status_change", f"{old_status} -> {new_status}", now, now, uid),
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
def gmail_oauth_callback(request: Request, code: str = "", state: str = "", error: str = ""):
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

            # Fetch user identity from Google's userinfo endpoint. This is
            # what makes "Sign in with Google" actually identify a user
            # (separate from Gmail access). With the new openid+email+profile
            # scopes, the access_token is authorized for userinfo.
            userinfo = gmail_integration.fetch_userinfo(creds)
            email = (userinfo.get("email") or "").strip().lower()
            google_sub = (userinfo.get("sub") or "").strip()
            name = (userinfo.get("name") or "").strip()
            picture = (userinfo.get("picture") or "").strip()

            if not email:
                return JSONResponse(
                    status_code=500,
                    content={"error": "userinfo_failed",
                             "message": "Could not read user identity from Google. Try again."},
                )

            # Upsert user row. We dedupe by email first (the most stable
            # identifier from the user's perspective); google_sub is the
            # cryptographically stable identifier per Google docs.
            now = datetime.now().isoformat(timespec="seconds")
            existing = conn.execute(
                "SELECT id FROM users WHERE email = ? OR google_user_id = ?",
                (email, google_sub),
            ).fetchone()
            if existing:
                user_id = existing["id"]
                conn.execute(
                    "UPDATE users SET google_user_id = ?, name = ?, "
                    "picture_url = ?, last_login_at = ? WHERE id = ?",
                    (google_sub, name, picture, now, user_id),
                )
            else:
                user_id = insert_returning_id(
                    conn,
                    "INSERT INTO users (email, google_user_id, name, "
                    "picture_url, created_at, last_login_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (email, google_sub, name, picture, now, now),
                )

            # Store OAuth credentials tagged with the user_id so Gmail sync
            # can load the right tokens per user.
            gmail_integration.store_credentials(
                conn, creds, user_email=email, user_id=user_id,
            )

        # Set the session cookie. From this point, the user is "logged in"
        # and require_auth will allow every request through without the
        # HTTP Basic Auth prompt.
        request.session["user_id"] = user_id
        request.session["email"] = email
        request.session["name"] = name

        # Best-effort: kick off an initial sync so the user lands on the
        # leads inbox with their Gmail-derived jobs already populated.
        # Swallow errors — the login itself succeeded, sync failures
        # shouldn't bounce the user back to the OAuth screen.
        try:
            with get_connection() as conn:
                gmail_integration.sync_to_tracker(conn, user_id=user_id)
        except Exception as sync_exc:
            print(f"[oauth_callback] initial sync failed (non-fatal): {sync_exc}")

        # Send the user to the Leads inbox — that's the actionable view of
        # "jobs you can apply to" derived from your Gmail. The Pipeline is
        # the secondary view (everything you've already started pursuing).
        return RedirectResponse(url="/leads", status_code=303)
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"error": "exchange_failed", "message": str(exc)},
        )


@app.post("/gmail/sync")
def gmail_sync_now(request: Request):
    """Manually trigger a Gmail → tracker sync of LinkedIn notification emails
    for the currently-signed-in user.
    """
    if not gmail_integration.is_configured():
        return _gmail_not_configured_response()
    try:
        tracker.init_db()
        uid = current_user_id(request)
        with get_connection() as conn:
            result = gmail_integration.sync_to_tracker(conn, user_id=uid)
        if not result.get("ok"):
            return JSONResponse(status_code=400, content=result)
        return result
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"error": "sync_failed", "message": str(exc)},
        )


@app.get("/gmail/status")
def gmail_status(request: Request):
    """Reports Gmail integration state — used by the dashboard's Sync widget."""
    configured = gmail_integration.is_configured()
    authorized = False
    last_sync = None
    if configured:
        tracker.init_db()
        uid = current_user_id(request)
        with get_connection() as conn:
            creds = gmail_integration.load_credentials(conn, user_id=uid)
            authorized = creds is not None
            last_sync = gmail_integration.get_last_sync(conn, user_id=uid)
    return {
        "configured": configured,
        "authorized": authorized,
        "last_sync": last_sync,
    }





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


@app.get("/discover", response_class=HTMLResponse)
def discover(request: Request):
    """Separate list of jobs sourced from external scrapes (Apify LinkedIn,
    etc.), kept OUT of the Gmail-alert /leads inbox. Ranked by fit score
    (STRONG first), shows company meta + salary + recruiter contact. Pursue
    moves a job into the pipeline (status=saved); Dismiss hides it."""
    tracker.init_db()
    uid = current_user_id(request)
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, title, company, link, location, company_size, "
            "company_industry, company_url, work_arrangement, comp_range, "
            "level, yoe_required, posted_at, source, jd_summary, "
            "must_have_skills, jd_raw_text, ai_score, ai_score_reason "
            "FROM jobs WHERE user_id = ? AND status = 'discovered' "
            "ORDER BY CASE ai_score WHEN 'STRONG' THEN 0 WHEN 'MAYBE' THEN 1 "
            "WHEN 'SKIP' THEN 2 ELSE 3 END, posted_at DESC",
            (uid,),
        ).fetchall()
        # Recruiter contacts keyed by job_id (one query, grouped in Python)
        contact_rows = conn.execute(
            "SELECT job_id, name, role, linkedin_url, email, "
            "connect_note, followup_msg, contact_type, priority, seniority, about "
            "FROM contacts WHERE user_id = ? "
            "ORDER BY COALESCE(priority, 1), id", (uid,),
        ).fetchall()
    contacts_by_job = {}
    for c in contact_rows:
        contacts_by_job.setdefault(c["job_id"], []).append(dict(c))

    import role_resumes as _rr
    jobs = []
    for r in rows:
        d = dict(r)
        d["added_rel"] = _relative_time(d.get("posted_at", "") or "")
        d["recruiters"] = contacts_by_job.get(d["id"], [])
        jd_raw = " ".join((d.get("jd_raw_text") or "").split()).strip()
        d["jd_full"] = jd_raw
        d["jd_char_count"] = len(jd_raw)
        d["must_have_list"] = [
            s.strip() for s in (d.get("must_have_skills") or "").split(",") if s.strip()
        ][:8]
        # Suggested resume: auto-route the job title to its best-fit resume
        # family so each card links straight to the right tailored resume to
        # send. Same detection used on /leads — one source of truth.
        # Human-readable source badge for the card.
        d["source_label"] = {
            "apify-linkedin": "LinkedIn", "linkedin-post": "LinkedIn post",
            "naukri": "Naukri", "indeed": "Indeed", "glassdoor": "Glassdoor",
        }.get(d.get("source") or "", (d.get("source") or "").title())
        fam = _rr.detect_family_from_title(d.get("title") or "")
        # Company-specific overrides: a JD tailored for one company beats the
        # generic title-based family for that company's cards.
        if "augnito" in (d.get("company") or "").lower():
            fam = "augnito-pm"
        d["resume_family"] = fam
        d["resume_label"] = _rr.FAMILY_LABELS.get(fam, fam)
        d["resume_url"] = f"/resumes/role/{fam}"
        jobs.append(d)

    strong = sum(1 for j in jobs if j.get("ai_score") == "STRONG")
    maybe = sum(1 for j in jobs if j.get("ai_score") == "MAYBE")
    return TEMPLATES.TemplateResponse("discover.html", {
        "request": request, "jobs": jobs,
        "total": len(jobs), "strong": strong, "maybe": maybe,
    })


@app.get("/leads", response_class=HTMLResponse)
def leads_inbox(request: Request, show: str = "", title: str = "", loc: str = ""):
    """Triage list of leads, filtered by chip-style title + location selectors.

    Both `title` and `loc` are comma-separated keys (e.g. ?title=po,pm&loc=pune,remote).
    """
    tracker.init_db()
    uid = current_user_id(request)
    show_dismissed = (show == "dismissed")
    status_filter = "lead-dismissed" if show_dismissed else "lead"

    selected_titles = [t for t in (title or "").split(",") if t.strip()]
    selected_locs = [l for l in (loc or "").split(",") if l.strip()]

    title_clause, title_params = _build_chip_clause(TITLE_CHIPS, selected_titles, "title")
    loc_clause, loc_params = _build_chip_clause(LOC_CHIPS, selected_locs, "location")

    where_parts = ["user_id = ?", "status = ?"]
    params = [uid, status_filter]
    if title_clause:
        where_parts.append(title_clause)
        params.extend(title_params)
    if loc_clause:
        where_parts.append(loc_clause)
        params.extend(loc_params)
    where_sql = " AND ".join(where_parts)

    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT id, title, company, link, location, added_at, "
            f"jd_raw_text, jd_summary, level, yoe_required, "
            f"must_have_skills, nice_to_have_skills, "
            f"company_size, company_industry, work_arrangement, comp_range, "
            f"posted_at, source "
            f"FROM jobs WHERE {where_sql} ORDER BY added_at DESC LIMIT 200",
            tuple(params),
        ).fetchall()
        total_unfiltered = conn.execute(
            "SELECT COUNT(*) AS n FROM jobs WHERE user_id = ? AND status = ?",
            (uid, status_filter),
        ).fetchone()["n"]
        dismissed_row = conn.execute(
            "SELECT COUNT(*) AS n FROM jobs WHERE user_id = ? AND status = 'lead-dismissed'",
            (uid,),
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

        # JD content for the expandable card section. Send the FULL JD so the
        # user can read everything in-app (no need to bounce to LinkedIn just
        # to scan requirements). The template renders it in a height-limited
        # scrollable box, with a "Show full JD" toggle that expands the box
        # to fit the entire text comfortably.
        jd_raw = " ".join((d.get("jd_raw_text") or "").split()).strip()
        jd_summary = (d.get("jd_summary") or "").strip()
        d["jd_full"] = jd_raw
        d["jd_summary_text"] = jd_summary
        d["jd_char_count"] = len(jd_raw)
        d["has_jd"] = bool(jd_raw)
        # Skills split for chip-style display
        d["must_have_list"] = [
            s.strip() for s in (d.get("must_have_skills") or "").split(",")
            if s.strip()
        ][:8]
        d["nice_to_have_list"] = [
            s.strip() for s in (d.get("nice_to_have_skills") or "").split(",")
            if s.strip()
        ][:6]
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
def leads_pursue(lead_id: int, request: Request):
    """Promote a lead to status='saved'. Tries to fetch full JD from LinkedIn
    guest page so Resume Studio can tailor immediately.
    """
    import linkedin_fetch
    tracker.init_db()
    uid = current_user_id(request)
    now_iso = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, link, jd_raw_text, company, title, location "
            "FROM jobs WHERE id = ? AND user_id = ?",
            (lead_id, uid),
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
                "last_activity_at = ? WHERE id = ? AND user_id = ?",
                (fetched_jd["jd_text"], fetched_jd.get("title") or row["title"],
                 fetched_jd.get("company") or row["company"],
                 fetched_jd.get("location") or row["location"],
                 now_iso, lead_id, uid),
            )
            conn.execute(
                "INSERT INTO events (job_id, event_type, body, occurred_at, recorded_at, user_id) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (lead_id, "note",
                 f"Auto-fetched JD from LinkedIn guest page ({len(fetched_jd['jd_text'])} chars). "
                 "Resume Studio can now tailor against the real JD.",
                 now_iso, now_iso, uid),
            )
        else:
            conn.execute(
                "UPDATE jobs SET status = 'saved', worth_pursuing = 'yes', last_activity_at = ? WHERE id = ? AND user_id = ?",
                (now_iso, lead_id, uid),
            )

        conn.execute(
            "INSERT INTO events (job_id, event_type, body, occurred_at, recorded_at, user_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (lead_id, "status_change", "lead -> saved (promoted from Leads inbox)", now_iso, now_iso, uid),
        )
    return RedirectResponse(f"/jobs/{lead_id}", status_code=303)


@app.post("/leads/{lead_id}/applied")
def leads_already_applied(lead_id: int, request: Request):
    """User opened LinkedIn from the lead, found they already applied earlier.
    Skips the Saved → Applied dance: status straight to 'applied' + applied_at=today.
    """
    tracker.init_db()
    uid = current_user_id(request)
    now_iso = datetime.now().isoformat(timespec="seconds")
    today = datetime.now().date().isoformat()
    with get_connection() as conn:
        conn.execute(
            "UPDATE jobs SET status = 'applied', worth_pursuing = 'yes', "
            "applied_at = COALESCE(applied_at, ?), last_activity_at = ? WHERE id = ? AND user_id = ?",
            (today, now_iso, lead_id, uid),
        )
        conn.execute(
            "INSERT INTO events (job_id, event_type, body, occurred_at, recorded_at, user_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (lead_id, "status_change",
             "lead -> applied (already-applied path from Leads triage)",
             now_iso, now_iso, uid),
        )
    return RedirectResponse("/leads", status_code=303)


@app.post("/leads/{lead_id}/dismiss")
def leads_dismiss(lead_id: int, request: Request):
    """Hide a lead — stays in DB so future LinkedIn emails dedup against it."""
    tracker.init_db()
    uid = current_user_id(request)
    now_iso = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        conn.execute(
            "UPDATE jobs SET status = 'lead-dismissed', last_activity_at = ? WHERE id = ? AND user_id = ?",
            (now_iso, lead_id, uid),
        )
    return RedirectResponse("/leads", status_code=303)


@app.post("/leads/{lead_id}/restore")
def leads_restore(lead_id: int, request: Request):
    """Undo a dismiss — bring back to active leads."""
    tracker.init_db()
    uid = current_user_id(request)
    now_iso = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        conn.execute(
            "UPDATE jobs SET status = 'lead', last_activity_at = ? WHERE id = ? AND user_id = ?",
            (now_iso, lead_id, uid),
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
    pdf_url = f"/resumes/role/{family}/pdf"
    if company:
        from urllib.parse import quote
        pdf_url += f"?company={quote(company)}"
    return TEMPLATES.TemplateResponse(
        "resume.html",
        {
            "request": request,
            "job": {"id": 0, "company": display_company, "title": display_title,
                    "resume_md": md, "link": "", "company_slug": company_slug or label_slug},
            "resume_html": resume_html,
            "pdf_filename": pdf_filename,
            "pdf_url": pdf_url,
        },
    )


@app.get("/resumes/role/{family}/pdf")
def role_resume_pdf(family: str, request: Request):
    """Download a role-family resume as a real PDF (clickable links,
    selectable text) via Playwright. Mirrors role_resume_page's filename
    logic so the downloaded file matches the on-screen hint."""
    import role_resumes
    md = role_resumes.render_role_resume(family)
    if not md:
        return JSONResponse(status_code=404, content={"error": "unknown_family"})
    resume_html = md_lib.markdown(md, extensions=["extra", "sane_lists"])
    label = role_resumes.FAMILY_LABELS.get(family, family)
    company = (request.query_params.get("company") or "").strip()
    company_slug = _slugify_for_filename(company) if company else ""
    label_slug = label.replace(" / ", "_").replace(" ", "_")
    if company_slug:
        pdf_filename = f"Ajinkya_Kate_{company_slug}_{label_slug}.pdf"
    else:
        pdf_filename = f"Ajinkya_Kate_{label_slug}.pdf"
    return _render_resume_pdf(resume_html, pdf_filename, request)
