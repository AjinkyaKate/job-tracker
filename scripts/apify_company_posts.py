"""Company-first hiring-signal scrape via Apify.

Flow the user asked for:
  1. Curated target companies — Pune/Mumbai, IT/software-SaaS, ~100-200 employees.
  2. ONE batched Apify post-search scoped to those companies (authorsCompanies)
     — i.e. only posts written by people who work at the target companies.
  3. Keep the PM/APM hiring posts; attribute each to its company via author.info
     (the LinkedIn headline, e.g. "Founder @CometChat").
  4. Enrich with curated size + recent-funding notes; ingest into hiring_signals.

Honesty: employee size + funding are PUBLIC-research estimates — VERIFY. The
target list is a strong sample, not "every" 100-200-person firm (that would be
hundreds of companies + huge Apify cost). Add companies to TARGETS and re-run.

Run:  export APIFY_TOKEN=...  &&  python scripts/apify_company_posts.py
"""
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, "/Users/ajinkya/Desktop/Ajinkya Kate/job-tracker")
from db import get_connection  # noqa: E402
from apify_client import run_actor_sync  # noqa: E402

USER_ID = 1
ACTOR = "harvestapi/linkedin-post-search"

# Curated targets — (name, city, size_estimate, domain, funding_note). Sizes/
# funding are public-research estimates to VERIFY, not confirmed facts.
TARGETS = [
    ("CometChat", "Mumbai", "51-200", "Comms API SaaS (chat/voice/video)", "Prior VC-backed (Series B-era); verify latest round."),
    ("Kennect", "Mumbai", "51-200", "Sales performance / incentive-comp SaaS", "VC-funded; verify last 6-month round."),
    ("Tartan", "Mumbai", "51-200", "Unified API + AI-agent platform", "Seed/early VC; verify recent round."),
    ("Drivetrain", "Mumbai", "~100-200", "B2B FP&A / finance SaaS", "Series A/B-era; verify recent round."),
    ("CargoFL", "Pune", "~50-200", "Logistics / supply-chain SaaS (AI)", "Enterprise clients (Tata, Westside); verify funding."),
    ("Thinkitive Technologies", "Pune", "~200-300", "Healthtech / custom software", "Bootstrapped/services; size slightly above band."),
    ("Seclore", "Mumbai", "~200-500", "Data-security / DRM SaaS", "VC-funded; size above band — verify."),
    ("Locobuzz", "Mumbai", "~200-500", "CX / social-listening SaaS", "VC-funded; size above band — verify."),
    ("Velotio Technologies", "Pune", "~200-500", "Product-engineering services", "Bootstrapped; size above band."),
]
TARGET_NAMES = [t[0] for t in TARGETS]
TARGET_BY_LC = {t[0].lower(): t for t in TARGETS}

QUERIES = ["hiring product manager", "hiring product", "we are hiring product owner"]

ROLE_KW = ("product manager", "product owner", "associate product",
           "product analyst", "product associate", " apm ")
HIRING_KW = ("hiring", "we're hiring", "we are hiring", "join", "open role",
             "now hiring", "apply", "looking for")

_SIGNALS_DDL = """CREATE TABLE IF NOT EXISTS hiring_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
    company TEXT NOT NULL, location TEXT, domain TEXT, funding_signal TEXT,
    why_relevant TEXT, role_target TEXT, role_level TEXT, who_to_reach TEXT,
    search_url TEXT, source_url TEXT, fit_tier TEXT, signal_date TEXT,
    added_at TEXT, status TEXT DEFAULT 'open')"""


def clean_url(u):
    return (str(u) or "").split("?")[0]


def detect_role(text):
    t = text.lower()
    for label, kw in [("Associate Product Manager", "associate product"),
                      ("Product Owner", "product owner"),
                      ("Product Analyst", "product analyst"),
                      ("Product Manager", "product manager"),
                      ("APM", " apm ")]:
        if kw in t:
            return label
    return ""


def attribute_company(author_info, content):
    blob = (author_info + " " + content).lower()
    for name_lc, t in TARGET_BY_LC.items():
        # match "cometchat" even when written "@CometChat"
        if name_lc in blob or name_lc.replace(" ", "") in blob.replace(" ", ""):
            return t
    return None


def main():
    inp = {"searchQueries": QUERIES, "authorsCompanies": TARGET_NAMES,
           "maxPosts": 10, "postedLimit": "month", "sortBy": "date"}
    print(f"Scoped to {len(TARGET_NAMES)} companies, queries={QUERIES}")
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
    print(f"Scraped {len(items)} raw items.")

    now = datetime.now(timezone.utc).isoformat()
    inserted = dup = skipped = 0
    with get_connection() as conn:
        conn.execute(_SIGNALS_DDL)
        for it in items:
            content = str(it.get("content") or "")
            au = it.get("author") or {}
            author = au.get("name") or ""
            info = au.get("info") or ""
            url = clean_url(it.get("linkedinUrl") or it.get("shareLinkedinUrl"))
            author_url = clean_url(au.get("linkedinUrl"))
            t = content.lower()
            role = detect_role(content)
            if not url or not any(k in t for k in HIRING_KW) or not role:
                skipped += 1
                continue
            tgt = attribute_company(info, content)
            if not tgt:
                skipped += 1
                continue
            name, city, size, domain, funding = tgt
            if conn.execute("SELECT id FROM hiring_signals WHERE user_id=? AND source_url=?",
                            (USER_ID, url)).fetchone():
                dup += 1
                continue
            tier = "STRONG" if city in ("Pune", "Mumbai") else "MAYBE"
            snippet = " ".join(content.split())[:300]
            conn.execute(
                "INSERT INTO hiring_signals (user_id,company,location,domain,"
                "funding_signal,why_relevant,role_target,role_level,who_to_reach,"
                "search_url,source_url,fit_tier,signal_date,added_at,status) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (USER_ID, name, city, f"{domain} · ~{size} emp",
                 f"Funding (verify): {funding}", snippet, role,
                 "Entry–mid · verify in post",
                 f"{author} — {info}"[:160], author_url or url, url, tier,
                 now[:10], now, "open"))
            inserted += 1
        conn.commit()
        total = conn.execute("SELECT COUNT(*) AS n FROM hiring_signals WHERE user_id=?",
                             (USER_ID,)).fetchone()["n"]
    print(f"Inserted: {inserted}  Deduped: {dup}  Skipped: {skipped}")
    print(f"Total signals now: {total}")


if __name__ == "__main__":
    main()
