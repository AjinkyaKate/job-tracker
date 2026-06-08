"""Fresh LinkedIn job scrape via Apify (fantastic-jobs/advanced-linkedin-job-search-api).

Pulls the LATEST PM/APM/PO/Product-Analyst job postings in India (last 7 days),
with real apply URLs + company size + seniority + AI-extracted skills/HM email,
and ingests them into the jobs table (source='apify-linkedin', status='discovered')
so they appear on /discover and /board with clickable apply links.

Run:  export APIFY_TOKEN=...  &&  python scripts/apify_scrape_jobs.py
      REUSE_LAST=1 ...  -> re-ingest last run's dataset free (no new credits).
"""
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, "/Users/ajinkya/Desktop/Ajinkya Kate/job-tracker")
from db import get_connection  # noqa: E402
from apify_client import run_actor_sync  # noqa: E402

USER_ID = 1
ACTOR = "fantastic-jobs/advanced-linkedin-job-search-api"


def s(v):
    if v is None:
        return ""
    if isinstance(v, (list, tuple)):
        return ", ".join(str(x) for x in v if x not in (None, ""))
    return str(v)


def clean_url(u):
    return (str(u) or "").split("?")[0]


SENIOR_KW = ("senior", "sr.", " lead", "principal", "director", "head of",
             "staff", " vp", "vice president", "group product", "director-")


def fit(title, seniority, exp, loc):
    t = f"{title} {seniority or ''} {exp or ''}".lower()
    locl = (loc or "").lower()
    geo = ("pune" in locl) or ("mumbai" in locl)
    if any(k in t for k in SENIOR_KW):
        return "SKIP", "Senior/lead band — above the ≤3-yr target."
    if geo:
        return "STRONG", "Entry–mid PM in Pune/Mumbai — your target geo + band."
    return "MAYBE", "Entry–mid PM in India — verify exact location / remote."


def main():
    inp = {
        "timeRange": "7d", "limit": 50,
        "titleSearch": ["Product Manager", "Associate Product Manager",
                        "Product Owner", "Product Analyst"],
        "locationSearch": ["India"],
        "removeAgency": True, "descriptionType": "text",
        "populateExternalApplyURL": True, "excludeATSDuplicate": True,
    }
    if os.environ.get("REUSE_LAST"):
        from apify_client import list_actor_runs, get_dataset_items
        runs = list_actor_runs(ACTOR, limit=1)
        ds = runs[0]["defaultDatasetId"]
        print(f"Reusing dataset {ds} (no new scrape).")
        items = get_dataset_items(ds)
    else:
        try:
            items = run_actor_sync(ACTOR, inp, timeout=600)
        except Exception as e:
            print(f"✖ Apify failed: {e}")
            return
    print(f"Scraped {len(items)} jobs.")

    now = datetime.now(timezone.utc).isoformat()
    ins = dup = 0
    tiers = {"STRONG": 0, "MAYBE": 0, "SKIP": 0}
    with get_connection() as conn:
        for it in items:
            link = clean_url(it.get("url"))
            if not link:
                continue
            if conn.execute("SELECT id FROM jobs WHERE user_id=? AND link=?",
                            (USER_ID, link)).fetchone():
                dup += 1
                continue
            title = s(it.get("title"))
            company = s(it.get("organization"))
            loc = s(it.get("locations_derived") or it.get("locations_raw"))
            seniority = s(it.get("seniority"))
            exp = s(it.get("ai_experience_level"))
            tier, reason = fit(title, seniority, exp, loc)
            tiers[tier] += 1
            conn.execute(
                "INSERT INTO jobs (user_id,title,company,link,location,"
                "company_size,company_industry,company_url,work_arrangement,"
                "employment_type,comp_range,level,posted_at,source,jd_summary,"
                "must_have_skills,jd_raw_text,ai_score,ai_score_reason,ai_hr_email,"
                "external_apply_url,status,added_at) VALUES "
                "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (USER_ID, title, company, link, loc,
                 s(it.get("linkedin_org_size")), s(it.get("linkedin_org_industry")),
                 s(it.get("organization_url") or it.get("linkedin_org_url")),
                 s(it.get("ai_work_arrangement") or it.get("location_type")),
                 s(it.get("employment_type")),
                 s(it.get("salary_raw") or it.get("ai_salary_value")),
                 seniority or exp, s(it.get("date_posted")), "apify-linkedin",
                 s(it.get("ai_requirements_summary"))[:600],
                 s(it.get("ai_key_skills")), s(it.get("description_text")),
                 tier, reason, s(it.get("ai_hiring_manager_email_address")),
                 clean_url(it.get("external_apply_url") or it.get("url")),
                 "discovered", now))
            ins += 1
        conn.commit()
        total = conn.execute("SELECT COUNT(*) AS n FROM jobs WHERE user_id=? AND status='discovered'",
                             (USER_ID,)).fetchone()["n"]
    print(f"Inserted: {ins}  Deduped: {dup}  Tiers: {tiers}")
    print(f"Total discovered jobs: {total}")


if __name__ == "__main__":
    main()
