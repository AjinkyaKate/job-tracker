"""Spin (manual trigger) 2026-06-03: net-new fresh hiring data.

Source this run: live web search across LinkedIn / Naukri / Wellfound / Indeed /
Cutshort / Foundit (June 2026). Reality check — the sweep surfaced mostly
aggregator LANDING pages (search-result URLs, not individual postings), which
have no stable per-job link to dedup on. Only postings with a verifiable apply
link are loaded here; aggregator entry-points are kept as bookmarks, not rows,
so the system of record stays clean.

  LinkedIn (free-text PM/PO/APM, IN): 1 net-new in-band with stable link
    (Checkmate, Pune). Whatfix APM-Full-Stack returned but link had EXPIRED
    (301 → company jobs page) — dropped.
  Naukri / Wellfound / Indeed / Cutshort / Foundit: landing pages only this
    run, no individual JD links extractable → 0 rows, bookmarked instead.
  User-supplied (pasted JDs this session): DBMCI One PM (real lnkd.in apply
    link + HR email) loaded. Continental D&A PO (SCM, Bengaluru) NOT loaded —
    no clean apply URL captured; tracked offline (resume already tailored).

Total: 2 net-new in-band jobs. STRONG = brand/backing or low-YoE + clear lane.
Idempotent: dedups by link.
"""
import sys
from datetime import datetime, timezone
sys.path.insert(0, "/Users/ajinkya/Desktop/Ajinkya Kate/job-tracker")
from db import get_connection  # noqa: E402

USER_ID = 1


def s(v):
    if v is None:
        return ""
    if isinstance(v, (list, tuple)):
        return ", ".join(str(x) for x in v if x not in (None, ""))
    return str(v)


# (source, title, company, link, location, size, industry, work, comp, level,
#  yoe, posted, summary, skills_list, tier, reason)
JOBS = [
    # ── LinkedIn (1 net-new, stable link) ───────────────────────────────────
    ("linkedin", "Associate Product Manager", "Checkmate",
     "https://in.linkedin.com/jobs/view/associate-product-manager-at-checkmate-4397541926",
     "Pune, Maharashtra", "", "Restaurant Tech / B2B SaaS", "US EST hours (till ~5 PM EST)", "",
     "Associate", "2-3 Yrs", "",
     "Restaurant-tech product co. Own product lifecycle discovery → launch. "
     "Improve funnel metrics (traffic → conversion → revenue → repeat usage), "
     "drive experimentation + AI-powered optimization, user-journey work across "
     "engineering/design/ops. ~180 applicants at listing.",
     ["Product Management", "APM", "Funnel Optimization", "A/B Testing",
      "Conversion", "AI Optimization", "Restaurant Tech"],
     "STRONG",
     "Pune (his city) · Associate-level + 2-3 Yrs = exact band · funnel/AB/AI lane "
     "fits. CAVEAT: requires US EST working hours (late-evening IST) — confirm "
     "before applying."),

    # ── User-supplied paste (real apply link + HR email) ─────────────────────
    ("linkedin", "Product Manager", "DBMCI One (Neuroglia Health / NHPL)",
     "https://lnkd.in/gnsx3PR9",
     "Bengaluru, Karnataka", "", "EdTech / Healthcare Learning",
     "On-site Bangalore", "", "Mid", "", "",
     "Backed by M3 Inc. Japan; part of the Marrow medical-learning ecosystem "
     "(one of India's largest healthcare-learning platforms). Build products "
     "thousands of medical students use daily — at the intersection of product, "
     "behaviour & growth, tech, and fast experimentation. First-principles, "
     "ownership, user-obsessed, fast-moving env.",
     ["Product Management", "EdTech", "Behaviour & Growth", "Experimentation",
      "Consumer Product", "First Principles"],
     "STRONG",
     "Strong PM lane + serious backing (M3 Inc. / Marrow ecosystem) · consumer "
     "learning product at scale. Apply: https://lnkd.in/gnsx3PR9 · HR direct: "
     "isha.patnaik@dbmi.edu.in (cold email already drafted this session)."),
]


def main():
    now = datetime.now(timezone.utc).isoformat()
    inserted = dup = 0
    by_src = {}
    tiers = {"STRONG": 0, "MAYBE": 0}
    with get_connection() as conn:
        for (src, title, company, link, location, size, industry, work, comp,
             level, yoe, posted, summary, skills, tier, reason) in JOBS:
            if conn.execute("SELECT id FROM jobs WHERE user_id=? AND link=?",
                            (USER_ID, link)).fetchone():
                dup += 1
                continue
            conn.execute(
                "INSERT INTO jobs (user_id,title,company,link,location,company_size,"
                "company_industry,work_arrangement,comp_range,level,yoe_required,"
                "posted_at,source,jd_summary,must_have_skills,jd_raw_text,ai_score,"
                "ai_score_reason,status,added_at) VALUES "
                "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (USER_ID, s(title), s(company), s(link), s(location), s(size),
                 s(industry), s(work), s(comp), s(level), s(yoe), s(posted), src,
                 s(summary), s(skills), s(summary), tier, reason, "discovered", now))
            inserted += 1
            tiers[tier] = tiers.get(tier, 0) + 1
            by_src[src] = by_src.get(src, 0) + 1
        conn.commit()
        total = conn.execute("SELECT COUNT(*) AS n FROM jobs WHERE user_id=? AND status='discovered'", (USER_ID,)).fetchone()["n"]
    print(f"Inserted: {inserted}  Deduped: {dup}")
    print(f"By source: {by_src}")
    print(f"Tiers: {tiers}")
    print(f"Total discovered: {total}")


if __name__ == "__main__":
    main()
