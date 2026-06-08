"""Scrape LinkedIn hiring POSTS via Apify and ingest them into hiring_signals.

This is the LIVE Apify integration (uses apify_client -> Apify REST API).
Apify runs the scrape on its own infra/proxies, so your personal LinkedIn
account is never used. Requires APIFY_TOKEN in the environment.

Run:
    export APIFY_TOKEN=apify_api_xxxxxxxx
    python scripts/apify_scrape_signals.py

What it does:
  1. Runs a LinkedIn post-search actor for PM/APM hiring posts in Pune/Mumbai.
  2. Filters the (noisy) results down to real hiring posts in your lane.
  3. Inserts the keepers into hiring_signals (the /signals page), with the
     post author as "who to reach" and the post URL as the verify link.

Honest notes:
  - LinkedIn post scraping is NOISY (listicles/job-seeker posts). The filter
    below is conservative; tune KEEP/role/location heuristics after the first
    real run when we can see the actor's actual output schema.
  - Field names vary by actor; extraction is defensive (tries several keys).
  - Idempotent: dedups by post URL.
"""
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, "/Users/ajinkya/Desktop/Ajinkya Kate/job-tracker")
from db import get_connection  # noqa: E402
from apify_client import run_actor_sync  # noqa: E402

USER_ID = 1

# Actor previously used in this project (see scripts/apify_posts_insert.py).
ACTOR = os.environ.get("APIFY_ACTOR", "harvestapi/linkedin-post-search")

# Search queries — entry/mid PM hiring posts, Pune/Mumbai-leaning.
QUERIES = [
    "hiring product manager Pune",
    "hiring associate product manager Pune",
    "we are hiring product manager Mumbai startup",
    "hiring product manager logistics India",
]

HIRING_KW = ("hiring", "we're hiring", "we are hiring", "join our team",
             "now hiring", "open role", "apply", "looking for")
ROLE_KW = ("product manager", "product owner", "associate product",
           "apm", "product analyst", "product associate")
PUNE = ("pune",)
MUMBAI = ("mumbai",)


def _first(item, *keys):
    """Return the first non-empty value among nested-or-flat keys."""
    for k in keys:
        cur = item
        ok = True
        for part in k.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                ok = False
                break
        if ok and cur not in (None, "", [], {}):
            return cur
    return ""


def _clean_url(u):
    return (str(u) or "").split("?")[0]


def extract(item):
    # Verified against harvestapi/linkedin-post-search output: text=content,
    # post URL=linkedinUrl, author is a nested object.
    text = str(_first(item, "content", "text", "postText", "description") or "")
    au = item.get("author") or {}
    author = str(au.get("name")
                 or f"{au.get('firstName', '')} {au.get('lastName', '')}".strip()
                 or _first(item, "authorName") or "")
    company = str(au.get("companyName") or au.get("company")
                  or au.get("occupation") or author)
    url = _clean_url(_first(item, "linkedinUrl", "shareLinkedinUrl",
                            "url", "postUrl", "link"))
    author_url = _clean_url(au.get("linkedinUrl") or au.get("url")
                            or au.get("profileUrl") or "")
    return text, author, company, url, author_url


def detect_role(text):
    t = text.lower()
    for label, kw in [("Associate Product Manager", "associate product"),
                      ("Product Owner", "product owner"),
                      ("Product Analyst", "product analyst"),
                      ("Product Associate", "product associate"),
                      ("Product Manager", "product manager"),
                      ("APM", "apm")]:
        if kw in t:
            return label
    return "Product role (see post)"


def is_relevant(text):
    t = text.lower()
    has_hiring = any(k in t for k in HIRING_KW)
    has_role = any(k in t for k in ROLE_KW)
    return has_hiring and has_role


def classify(text):
    t = text.lower()
    in_pune = any(k in t for k in PUNE)
    in_mum = any(k in t for k in MUMBAI)
    loc = "Pune" if in_pune else ("Mumbai" if in_mum else "India / Remote (verify)")
    tier = "STRONG" if (in_pune or in_mum) else "MAYBE"
    return loc, tier


def main():
    print(f"Actor: {ACTOR}")
    print(f"Queries: {QUERIES}")
    # REUSE_LAST=1 re-ingests the most recent run's dataset WITHOUT scraping
    # again (free — no Apify credits). Use after a field-mapping fix.
    if os.environ.get("REUSE_LAST"):
        from apify_client import list_actor_runs, get_dataset_items
        runs = list_actor_runs(ACTOR, limit=1)
        ds = runs[0]["defaultDatasetId"]
        print(f"Reusing last run dataset {ds} (no new scrape).")
        items = get_dataset_items(ds)
    else:
        # Correct input keys for harvestapi/linkedin-post-search (verified via
        # the actor's input schema): searchQueries + postedLimit ('week' = last
        # 7 days, the user's requirement) + sortBy 'date' (newest first).
        run_input = {
            "searchQueries": QUERIES,
            "maxPosts": 15,          # per query; 4 queries -> up to ~60 posts
            "postedLimit": "week",   # last 7 days
            "sortBy": "date",
        }
        try:
            items = run_actor_sync(ACTOR, run_input)
        except Exception as e:
            print(f"\n✖ Apify run failed: {e}")
            print("If auth error, set APIFY_TOKEN. If input-schema error, paste "
                  "the actor's input fields and I'll adjust run_input.")
            return

    print(f"Scraped {len(items)} raw items.")
    now = datetime.now(timezone.utc).isoformat()
    inserted = dup = skipped = 0
    with get_connection() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS hiring_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
            company TEXT NOT NULL, location TEXT, domain TEXT, funding_signal TEXT,
            why_relevant TEXT, role_target TEXT, role_level TEXT, who_to_reach TEXT,
            search_url TEXT, source_url TEXT, fit_tier TEXT, signal_date TEXT,
            added_at TEXT, status TEXT DEFAULT 'open')""")
        for item in items:
            text, author, company, url, author_url = extract(item)
            if not url or not is_relevant(text):
                skipped += 1
                continue
            if conn.execute("SELECT id FROM hiring_signals WHERE user_id=? AND source_url=?",
                            (USER_ID, url)).fetchone():
                dup += 1
                continue
            loc, tier = classify(text)
            snippet = " ".join(text.split())[:300]
            conn.execute(
                "INSERT INTO hiring_signals (user_id,company,location,domain,"
                "funding_signal,why_relevant,role_target,role_level,who_to_reach,"
                "search_url,source_url,fit_tier,signal_date,added_at,status) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (USER_ID, company or author or "Unknown", loc,
                 "LinkedIn hiring post · Apify · last 7 days", snippet,
                 "From a live LinkedIn hiring post — read the snippet and DM the author.",
                 detect_role(text), "Entry–mid · verify in post",
                 author or "Post author", author_url or url, url, tier,
                 now[:10], now, "open"))
            inserted += 1
        conn.commit()
        total = conn.execute("SELECT COUNT(*) AS n FROM hiring_signals WHERE user_id=?",
                             (USER_ID,)).fetchone()["n"]
    print(f"Inserted: {inserted}  Deduped: {dup}  Skipped(noise): {skipped}")
    print(f"Total signals now: {total}")


if __name__ == "__main__":
    main()
