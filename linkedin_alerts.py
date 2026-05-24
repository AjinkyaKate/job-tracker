"""LinkedIn job-alert email parser.

LinkedIn sends two relevant email formats from `jobalerts-noreply@linkedin.com`:
1. Digest: "N new jobs for <search-term>" — multiple jobs in one email
2. Featured: "<job title> at <company>" — one primary + N recommended jobs

Both formats use the same HTML structure for each listing:
- `<a href=".../jobs/view/<ID>/?...trk=eml-...-jobcard_body...">TITLE</a>`
- `<p ...>Company &middot; Location</p>`

This parser extracts every listed job from either format. Returns a list of
dicts with title, company, location, link, job_id. Caller dedupes on link
when inserting into the jobs table.
"""
import re
import html as html_module
from typing import List, Dict


# Detect if an email is a LinkedIn job alert (sender + subject check).
LINKEDIN_ALERT_SENDERS = [
    r"jobalerts-noreply@linkedin\.com",
    r"jobs-listings@linkedin\.com",
    r"jobs-noreply@linkedin\.com",
]

LINKEDIN_ALERT_SUBJECT_PATTERNS = [
    r"new jobs? for",          # "10 new jobs for 'business analyst'"
    r"\d+ jobs? you may be",   # "10 jobs you may be interested in"
    r"job alert",
    r"\bat\b",                 # "<title> at <company>" — featured-job format
]


def is_linkedin_alert(headers: dict) -> bool:
    """Check if an email is a LinkedIn job-alert (suitable for parse_alert)."""
    sender = headers.get("From", "").lower()
    subject = headers.get("Subject", "").lower()
    if not any(re.search(p, sender, re.IGNORECASE) for p in LINKEDIN_ALERT_SENDERS):
        return False
    return any(re.search(p, subject, re.IGNORECASE) for p in LINKEDIN_ALERT_SUBJECT_PATTERNS)


# Job-card link pattern — matches links with the "jobcard_body" trk parameter
# (the visible click target with title inside). Excludes logo links and tracking pixels.
JOB_CARD_LINK_RE = re.compile(
    r'<a\s+[^>]*href="(https?://www\.linkedin\.com/comm/jobs/view/(\d+)[^"]*?'
    r'(?:jobcard_body|job_card|job-card)[^"]*)"[^>]*>\s*([^<]{3,200})\s*</a>',
    re.IGNORECASE | re.DOTALL,
)

# Company · Location pattern — the <p> that follows the job-title anchor.
# Captures everything inside the first <p> after the anchor.
COMPANY_LOCATION_RE = re.compile(
    r'<p\s+[^>]*>([^<]{3,200}?)</p>',
    re.IGNORECASE,
)


def _decode_entities(s: str) -> str:
    """Unescape HTML entities (&amp; &middot; &nbsp; etc.) and collapse whitespace."""
    if not s:
        return ""
    return " ".join(html_module.unescape(s).split())


def _strip_query(url: str) -> str:
    """Drop tracking query string from a LinkedIn job-view URL.

    Keeps just `https://www.linkedin.com/jobs/view/<ID>/` (canonical form for dedup)."""
    m = re.search(r"linkedin\.com/(?:comm/)?jobs/view/(\d+)", url)
    if not m:
        return url
    return f"https://www.linkedin.com/jobs/view/{m.group(1)}/"


def parse_alert(html: str) -> List[Dict]:
    """Extract job listings from a LinkedIn alert email HTML body.

    Returns list of dicts: {job_id, title, company, location, link}.
    Empty list if no jobs found.
    """
    if not html:
        return []

    # Find all job-card links (link + job_id + raw title)
    cards = JOB_CARD_LINK_RE.findall(html)
    if not cards:
        # Fallback: looser match — any anchor wrapping a non-empty title that goes to /jobs/view/
        cards = re.findall(
            r'<a\s+[^>]*href="(https?://www\.linkedin\.com/comm/jobs/view/(\d+)[^"]*)"[^>]*>\s*([^<]{3,200})\s*</a>',
            html, re.IGNORECASE,
        )

    # Dedup by job_id, keeping the first (usually the cleanest) match
    seen = set()
    results = []

    for full_url, job_id, raw_title in cards:
        if job_id in seen:
            continue
        title = _decode_entities(raw_title)
        if not title or len(title) < 3:
            continue
        # Skip obvious non-titles (LinkedIn's own brand links, "See all jobs", etc.)
        if title.lower() in {"linkedin", "see all jobs", "view job", "apply now", "see jobs"}:
            continue
        seen.add(job_id)

        # Look for the company · location <p> tag immediately after this anchor in the HTML
        anchor_end_idx = html.find(raw_title, html.find(f'jobs/view/{job_id}'))
        if anchor_end_idx == -1:
            company, location = "", ""
        else:
            tail = html[anchor_end_idx:anchor_end_idx + 1500]
            p_match = COMPANY_LOCATION_RE.search(tail)
            raw_meta = _decode_entities(p_match.group(1)) if p_match else ""
            # Split on " · " (middot) — common LinkedIn pattern
            parts = re.split(r"\s+·\s+|\s+·\s+", raw_meta, maxsplit=1)
            if len(parts) == 2:
                company, location = parts[0].strip(), parts[1].strip()
            elif raw_meta:
                company, location = raw_meta.strip(), ""
            else:
                company, location = "", ""

        results.append({
            "job_id": job_id,
            "title": title,
            "company": company,
            "location": location,
            "link": _strip_query(full_url),
        })

    return results
