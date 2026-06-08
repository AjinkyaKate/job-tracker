"""Seed the hiring_signals table — research-surfaced hiring signals (2026-06-06).

IMPORTANT — honest provenance: this data is NOT LinkedIn-scraped. It is curated
from PUBLIC web research (funding trackers, startup lists, job boards) during the
2026-06-06 session. LinkedIn scraping is deliberately out of scope (ToS + account
risk — see CLAUDE.md). Each row carries a source link + a verify/apply search and
a "find the hiring manager" LinkedIn *people-search* link the user opens while
logged in as themselves. Treat funding/level fields as leads to VERIFY, not facts.

Idempotent: dedups by (company, role_target). Run again to top up.
"""
import sys
from datetime import datetime, timezone
sys.path.insert(0, "/Users/ajinkya/Desktop/Ajinkya Kate/job-tracker")
from db import get_connection  # noqa: E402

USER_ID = 1

DDL = """
CREATE TABLE IF NOT EXISTS hiring_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    company TEXT NOT NULL,
    location TEXT,
    domain TEXT,
    funding_signal TEXT,
    why_relevant TEXT,
    role_target TEXT,
    role_level TEXT,
    who_to_reach TEXT,
    search_url TEXT,
    source_url TEXT,
    fit_tier TEXT,
    signal_date TEXT,
    added_at TEXT,
    status TEXT DEFAULT 'open'
)
"""

# (company, location, domain, funding_signal, why_relevant, role_target,
#  role_level, who_to_reach, search_url, source_url, fit_tier, signal_date)
SIGNALS = [
    ("CargoFL", "Pune", "Logistics / Supply Chain (AI)",
     "AI-driven logistics ecosystem, 4+ yrs operating, enterprise clients (Tata Group, Westside). Verify latest funding round.",
     "Pune-based logistics-tech — direct hit on your logistics-domain target, and enterprise B2B SaaS like your D·engage work.",
     "Product Manager / Associate PM", "Mid · verify ≤3 yrs",
     "Head of Product / Founder",
     "https://www.google.com/search?q=CargoFL+product+manager+careers",
     "https://tracxn.com/d/explore/supply-chain-services-startups-in-pune-india/",
     "STRONG", "2026-06"),
    ("Easebuzz", "Pune", "Fintech / Payments",
     "Funded Pune fintech, among the city's higher-funded startups; scaling team.",
     "Pune fintech B2B SaaS payments — your B2B SaaS PO experience transfers, strong home-city anchor.",
     "Associate PM / Product Manager", "1–3 yrs roles common",
     "Product Lead / Hiring Manager",
     "https://www.google.com/search?q=Easebuzz+product+manager+careers",
     "https://wellfound.com/startups/location/pune",
     "STRONG", "2026-06"),
    ("FPL Technologies (OneCard)", "Pune", "Fintech (consumer credit)",
     "Well-funded Pune consumer-fintech with a large product org; verify latest round.",
     "Pune consumer fintech at scale — runs APM/PM tracks; product-driven culture good for an entry-mid PM.",
     "Associate PM / Product Manager", "APM/entry tracks exist",
     "Group PM / Talent team",
     "https://www.google.com/search?q=OneCard+FPL+Technologies+associate+product+manager",
     "https://www.failory.com/startups/pune",
     "MAYBE", "2026-06"),
    ("Zinnia", "Pune", "Insurtech / Workflow Automation",
     "Active PM posting: 'Product Manager II (Technical) – Compliance Workflow Automation', Pune, posted ~May 12 2026.",
     "Concrete, recent Pune PM opening; workflow-automation + technical angle fits your AI-product framing.",
     "Product Manager II (Technical)", "Mid · verify YoE",
     "Hiring manager named on the JD",
     "https://www.google.com/search?q=Zinnia+Product+Manager+II+Compliance+Workflow+Automation+Pune",
     "https://jobs.punestartups.org/",
     "STRONG", "2026-05-12"),
    ("Modulr", "Pune", "Fintech (payments / cards)",
     "Active posting: 'Senior Product Manager – Cards', Pune, posted ~May 15 2026.",
     "Pune fintech actively hiring PMs — Senior is above your ≤3-yr band, so monitor for their mid/PM reqs.",
     "Senior PM – Cards (watch for PM/APM)", "Senior · above band — monitor",
     "PM Lead",
     "https://www.google.com/search?q=Modulr+Senior+Product+Manager+Cards+Pune",
     "https://wellfound.com/startups/location/pune",
     "MAYBE", "2026-05-15"),
    ("Intugine Technologies", "Bengaluru / India (remote-friendly)", "Logistics / Supply-chain visibility",
     "Multimodal supply-chain visibility provider; growing. Verify funding + Pune/Mumbai/remote roles.",
     "Logistics-domain match; even if HQ is Bengaluru, remote/India PM roles fit your logistics target.",
     "Product Manager", "Mid · verify",
     "Head of Product",
     "https://www.google.com/search?q=Intugine+Technologies+product+manager+careers",
     "https://www.startus-insights.com/innovators-guide/logistics-startups-and-companies/",
     "MAYBE", "2026-06"),
    ("ClickPost", "Delhi NCR / India", "Logistics intelligence (post-purchase)",
     "Asia's large logistics-intelligence platform; reported profitable and scaling.",
     "Logistics-domain match; B2B SaaS for e-commerce logistics — adjacent to your retail/commerce experience.",
     "Product Manager / APM", "Mid · verify",
     "Product Lead",
     "https://www.google.com/search?q=ClickPost+product+manager+careers",
     "https://www.startus-insights.com/innovators-guide/logistics-startups-and-companies/",
     "MAYBE", "2026-06"),
    ("FreightFox", "India (verify Pune/Mumbai/remote)", "B2B Logistics tech",
     "Funded B2B logistics startup; public listing states they are hiring Product Managers.",
     "Logistics-domain match AND explicitly hiring PMs — high-intent signal; confirm location/remote.",
     "Product Manager", "Mid · verify ≤3 yrs",
     "Founder / Head of Product",
     "https://www.google.com/search?q=FreightFox+product+manager+careers",
     "https://www.startus-insights.com/innovators-guide/logistics-startups-and-companies/",
     "MAYBE", "2026-06"),
]


def main():
    now = datetime.now(timezone.utc).isoformat()
    inserted = dup = 0
    with get_connection() as conn:
        conn.execute(DDL)
        for (company, location, domain, funding, why, role, level, who,
             search_url, source_url, tier, sig_date) in SIGNALS:
            exists = conn.execute(
                "SELECT id FROM hiring_signals WHERE user_id=? AND company=? AND role_target=?",
                (USER_ID, company, role)).fetchone()
            if exists:
                dup += 1
                continue
            conn.execute(
                "INSERT INTO hiring_signals (user_id,company,location,domain,"
                "funding_signal,why_relevant,role_target,role_level,who_to_reach,"
                "search_url,source_url,fit_tier,signal_date,added_at,status) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (USER_ID, company, location, domain, funding, why, role, level,
                 who, search_url, source_url, tier, sig_date, now, "open"))
            inserted += 1
        conn.commit()
        total = conn.execute(
            "SELECT COUNT(*) AS n FROM hiring_signals WHERE user_id=?",
            (USER_ID,)).fetchone()["n"]
    print(f"Inserted: {inserted}  Deduped: {dup}  Total signals: {total}")


if __name__ == "__main__":
    main()
