"""Fetch LinkedIn job-detail pages from the guest (unauthenticated) endpoint.

LinkedIn serves a stripped-down version of each job page to crawlers/SEO bots.
This works WITHOUT logging in — it's intended for search-engine indexing — so
no account-ban risk. We only use it on user-triggered actions (clicking Pursue
on a lead), never in bulk scraping, to stay polite + under any rate limits.
"""
import re
import urllib.request
import urllib.error
import html as html_module
from typing import Optional, Dict

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _to_guest_url(link: str) -> str:
    """Convert any LinkedIn job URL to the guest-detail endpoint."""
    m = re.search(r"linkedin\.com/(?:comm/)?jobs/view/(\d+)", link)
    if not m:
        return link
    return f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{m.group(1)}"


def fetch_job_details(link: str, timeout: int = 15) -> Optional[Dict[str, str]]:
    """Fetch a LinkedIn job page and extract title, company, location, JD.

    Returns dict with title, company, location, jd_text, raw_html_length.
    Returns None on any failure (rate limit, 404, network, etc.).
    """
    if not link:
        return None
    url = _to_guest_url(link)
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                return None
            html = resp.read().decode("utf-8", errors="replace")
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, Exception):
        return None

    if not html or len(html) < 1000:
        return None

    return _parse_guest_html(html)


def _parse_guest_html(html: str) -> Dict[str, str]:
    """Extract structured fields from the LinkedIn guest job-detail HTML."""
    def _decode(s):
        return html_module.unescape(s).strip() if s else ""

    def _strip_tags(s):
        if not s:
            return ""
        # Remove script + style first (their content shouldn't show)
        s = re.sub(r"<script[^>]*>.*?</script>", " ", s, flags=re.DOTALL | re.IGNORECASE)
        s = re.sub(r"<style[^>]*>.*?</style>", " ", s, flags=re.DOTALL | re.IGNORECASE)
        # Tags → whitespace
        s = re.sub(r"<[^>]+>", " ", s)
        s = _decode(s)
        return " ".join(s.split())

    # Title — usually in the page <title> AND in an h1/h2 with topcard__title-link
    title = ""
    t_match = re.search(r'<h\d[^>]*class="[^"]*topcard__title[^"]*"[^>]*>([^<]+)</h\d>', html, re.IGNORECASE)
    if t_match:
        title = _decode(t_match.group(1))
    if not title:
        t_match = re.search(r'<title>([^<]+)</title>', html, re.IGNORECASE)
        if t_match:
            title = _decode(t_match.group(1).split("|")[0].split("hiring")[0])

    # Company name
    company = ""
    c_match = re.search(
        r'<a[^>]*class="[^"]*topcard__org-name-link[^"]*"[^>]*>([^<]+)</a>',
        html, re.IGNORECASE,
    )
    if c_match:
        company = _decode(c_match.group(1))
    if not company:
        c_match = re.search(
            r'<(?:span|a)[^>]*class="[^"]*(?:topcard__flavor|company-name)[^"]*"[^>]*>([^<]+)</',
            html, re.IGNORECASE,
        )
        if c_match:
            company = _decode(c_match.group(1))

    # Location
    location = ""
    l_match = re.search(
        r'<span[^>]*class="[^"]*topcard__flavor--bullet[^"]*"[^>]*>([^<]+)</span>',
        html, re.IGNORECASE,
    )
    if l_match:
        location = _decode(l_match.group(1))

    # Full JD — inside a div with class "description__text" or "show-more-less-html__markup"
    jd_text = ""
    jd_match = re.search(
        r'<div[^>]*class="[^"]*(?:show-more-less-html__markup|description__text)[^"]*"[^>]*>(.+?)</div>\s*(?:<button|</section)',
        html, re.IGNORECASE | re.DOTALL,
    )
    if jd_match:
        jd_text = _strip_tags(jd_match.group(1))[:6000]
    if not jd_text:
        # Fallback: any div with "description" in the class
        jd_match = re.search(
            r'<div[^>]*class="[^"]*description[^"]*"[^>]*>(.{500,8000}?)</div>',
            html, re.IGNORECASE | re.DOTALL,
        )
        if jd_match:
            jd_text = _strip_tags(jd_match.group(1))[:6000]

    return {
        "title": title or "",
        "company": company or "",
        "location": location or "",
        "jd_text": jd_text or "",
        "raw_html_length": str(len(html)),
    }
