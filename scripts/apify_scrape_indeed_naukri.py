"""Scrape Indeed (misceres) + Naukri (memo23) via Apify and ingest into jobs.

Adds source='indeed' and source='naukri' rows (status='discovered') so they join
the LinkedIn jobs on /board and /discover with apply links. Defensive field
mapping (job-board output schemas vary); prints first-item keys per source so the
mapping can be verified/tuned. Dedups by link. Last 7 days, India, PM/APM/PO.

Run:  export APIFY_TOKEN=...  &&  python scripts/apify_scrape_indeed_naukri.py
"""
import sys
from datetime import datetime, timezone

sys.path.insert(0, "/Users/ajinkya/Desktop/Ajinkya Kate/job-tracker")
from db import get_connection  # noqa: E402
from apify_client import run_actor_sync  # noqa: E402

USER_ID = 1
SENIOR_KW = ("senior", "sr.", " lead", "principal", "director", "head of",
             "staff", " vp", "vice president", "group product")


def s(v):
    if v is None:
        return ""
    if isinstance(v, (list, tuple)):
        return ", ".join(str(x) for x in v if x not in (None, ""))
    return str(v)


def clean_url(u):
    return (str(u) or "").split("?")[0]


def first(item, *keys):
    for k in keys:
        cur, ok = item, True
        for part in k.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                ok = False
                break
        if ok and cur not in (None, "", [], {}):
            return cur
    return ""


def fit(title, level, loc):
    t = f"{title} {level or ''}".lower()
    locl = (loc or "").lower()
    geo = ("pune" in locl) or ("mumbai" in locl)
    if any(k in t for k in SENIOR_KW):
        return "SKIP", "Senior/lead band — above the ≤3-yr target."
    if geo:
        return "STRONG", "Entry–mid PM in Pune/Mumbai — your target geo."
    return "MAYBE", "Entry–mid PM in India — verify location / remote."


def extract(it):
    title = s(first(it, "positionName", "title", "jobTitle"))
    company = s(first(it, "company", "companyName", "organization"))
    loc = s(first(it, "location", "jobLocation", "place", "city"))
    url = clean_url(first(it, "url", "jobUrl", "jdURL", "link", "jobPostUrl",
                          "jobUrlDirect"))
    apply_url = clean_url(first(it, "externalApplyLink", "applyUrl",
                                "apply_link", "url", "jobUrl"))
    posted = s(first(it, "postedAt", "postingDateParsed", "postedDate",
                     "date", "footerPlaceholderLabel"))
    salary = s(first(it, "salary", "salaryRange", "salary_raw"))
    level = s(first(it, "experience", "experienceLevel", "jobType"))
    desc = s(first(it, "description", "jobDescription", "descriptionText",
                   "jobDescriptionText"))
    skills = s(first(it, "tagsAndSkills", "skills", "keywords"))
    return title, company, loc, url, apply_url, posted, salary, level, desc, skills


def extract_naukri(it):
    """Naukri (memo23) nests fields differently: company=companyDetail.name,
    link=staticUrl, location=locations[], experience=experienceText."""
    cd = it.get("companyDetail") or {}
    company = (cd.get("name") if isinstance(cd, dict) else "") or s(it.get("staticCompanyName"))
    title = s(it.get("title"))
    L = it.get("locations")
    if isinstance(L, list) and L:
        loc = ", ".join(s(x.get("label") or x.get("title") or x.get("name"))
                        if isinstance(x, dict) else str(x) for x in L)
    else:
        loc = ""
    link = clean_url(s(it.get("staticUrl")) or s(it.get("url")))
    sal = it.get("salaryDetail")
    salary = sal.get("label") if isinstance(sal, dict) else s(sal)
    level = s(it.get("experienceText"))
    ks = it.get("keySkills")
    skills = (", ".join(s(k.get("label") if isinstance(k, dict) else k) for k in ks)
              if isinstance(ks, list) else s(ks))
    desc = s(it.get("description"))
    return title, company, loc, link, link, s(it.get("createdDate")), salary, level, desc, skills


def ingest(items, source, conn, now, extract_fn=None):
    extract_fn = extract_fn or extract
    ins = dup = skip = 0
    if items:
        print(f"  [{source}] first-item keys: {list(items[0].keys())[:18]}")
    for it in items:
        title, company, loc, url, apply_url, posted, salary, level, desc, skills = extract_fn(it)
        if not url or not title:
            skip += 1
            continue
        if conn.execute("SELECT id FROM jobs WHERE user_id=? AND link=?",
                        (USER_ID, url)).fetchone():
            dup += 1
            continue
        tier, reason = fit(title, level, loc)
        conn.execute(
            "INSERT INTO jobs (user_id,title,company,link,location,comp_range,"
            "level,posted_at,source,jd_summary,must_have_skills,jd_raw_text,"
            "ai_score,ai_score_reason,external_apply_url,status,added_at) VALUES "
            "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (USER_ID, title, company, url, loc, salary, level, posted, source,
             desc[:600], skills, desc, tier, reason, apply_url or url,
             "discovered", now))
        ins += 1
    print(f"  [{source}] Inserted: {ins}  Deduped: {dup}  Skipped: {skip}")
    return ins


def main():
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        # Indeed
        print("Running Indeed (misceres/indeed-scraper)...")
        try:
            indeed = run_actor_sync("misceres/indeed-scraper", {
                "position": "product manager", "country": "IN",
                "location": "India", "maxItemsPerSearch": 40,
                "followApplyRedirects": True, "parseCompanyDetails": False,
                "saveOnlyUniqueItems": True}, timeout=600)
            print(f"  scraped {len(indeed)}")
            ingest(indeed, "indeed", conn, now)
        except Exception as e:
            print(f"  ✖ Indeed failed: {e}")

        # Naukri
        print("Running Naukri (memo23/naukri-scraper)...")
        try:
            naukri = run_actor_sync("memo23/naukri-scraper", {
                "searchQuery": "product manager", "location": "india",
                "platform": "naukri", "timeFilter": "7d", "maximumJobs": 40,
                "includeDescription": True, "cleanHtml": True}, timeout=600)
            print(f"  scraped {len(naukri)}")
            ingest(naukri, "naukri", conn, now, extract_naukri)
        except Exception as e:
            print(f"  ✖ Naukri failed: {e}")

        conn.commit()
        total = conn.execute("SELECT COUNT(*) AS n FROM jobs WHERE user_id=? AND status='discovered'",
                             (USER_ID,)).fetchone()["n"]
    print(f"Total discovered jobs: {total}")


if __name__ == "__main__":
    main()
