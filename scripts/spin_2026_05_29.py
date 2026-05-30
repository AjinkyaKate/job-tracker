"""Spin (manual trigger) 2026-05-29: net-new fresh hiring data across sources.

LinkedIn (fantastic-jobs, 24h, IN, 50-1000, ≤5yr): 6 returned, 4 already in DB
  → 2 net-new (Xurrent, E2M).
Naukri (memo23, 3-day, employer, IN, min-exp ≤3): 50 returned, mostly senior
  → 11 net-new in-band (≤~6 yrs, PM/Tech).
Indeed (misceres, "associate product manager", IN): 25 returned, mostly Sr/Lead
  → 5 net-new in-band (Mid PM/PO).

Total: 18 net-new in-band jobs. STRONG = clear domain/lane match at low YoE.
Dropped: 4 Sr/Lead/Principal, 2 brand-PM/pharma, 1 tier-1-IIT-gate (Vbeyond),
1 support-not-PM (AirAsia), 1 dup (Saleshandy API has same role on LinkedIn).
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
    # ── LinkedIn fantastic-jobs (2 net-new) ─────────────────────────────────
    ("apify-linkedin", "Product Manager", "Xurrent",
     "https://in.linkedin.com/jobs/view/product-manager-at-xurrent-4420431103",
     "India", "51-200 employees", "Software Development", "On-site", "", "Mid-Senior level",
     "2-4 yrs", "2026-05-28T12:55:20",
     "2-4 yrs as PM in B2B SaaS. 3+ yrs with ITAM tools. Bachelor's required; MBA plus. "
     "Network scanning, device discovery, KPI-driven analysis, cross-functional connectivity.",
     ["Product Management", "B2B SaaS", "ITAM", "Network Scanning",
      "Analytical Reporting", "KPI-Driven Analysis", "Cross-Functional", "Compliance", "Customer Success"],
     "STRONG",
     "2-4yr band, B2B SaaS PM, ITSM/ITAM lane. Recruiter named (Vijayalakshmi R) — direct DM channel."),
    ("apify-linkedin", "Product Manager", "E2M",
     "https://in.linkedin.com/jobs/view/product-manager-at-e2m-4420402925",
     "Ahmedabad", "201-500 employees", "IT Services and IT Consulting", "On-site", "", "Mid-Senior level",
     "2-4 yrs", "2026-05-28T12:30:14",
     "2-4 yrs in product management. Agile, AI/ML product familiarity, GenAI exposure. "
     "Tools: Jira, Confluence, Notion, Figma, SQL.",
     ["Product Management", "Agile", "AI/ML", "GenAI", "Stakeholder Management",
      "User Research", "Jira", "Confluence", "Notion", "Figma", "SQL"],
     "STRONG",
     "2-4yr band, AI/ML product lane, Ahmedabad on-site, exact tool match (Jira/Figma/SQL/Notion)."),

    # ── Indeed (5 net-new in-band) ─────────────────────────────────────────
    ("indeed", "Product Manager - TV Shopping", "InMobi",
     "https://in.indeed.com/viewjob?jk=287ceacdb3540c60",
     "Bengaluru, Karnataka", "", "AdTech", "", "", "Mid", "", "2026-05-28T18:32:23",
     "Mid-level PM for InMobi's TV Shopping product line. Consumer + adtech crossover.",
     ["Product Management", "Consumer Product", "AdTech", "TV/Streaming"],
     "MAYBE",
     "InMobi is a strong India adtech brand; consumer PM lane fits."),
    ("indeed", "Product Owner - Cash Management (SME)", "Luxoft",
     "https://in.indeed.com/viewjob?jk=e4574ab6786e95fe",
     "Bengaluru, Karnataka", "", "IT Services", "", "", "Mid", "", "2026-05-28T06:21:49",
     "PO for Cash Management SME at Luxoft. BFSI fintech, payments domain knowledge.",
     ["Product Owner", "BFSI", "Cash Management", "Payments", "Agile", "Scrum"],
     "MAYBE",
     "PO lane is Ajinkya's CSPO sweet spot; BFSI domain (his D·engage exposure: RCS Banking)."),
    ("indeed", "Sr. Associate Product - Cross Sell", "Hero FinCorp",
     "https://in.indeed.com/viewjob?jk=cc17b8a624b50190",
     "Gurugram, Haryana", "", "Financial Services", "", "", "Mid", "", "2026-05-27T04:19:19",
     "Associate Product role for Cross Sell at Hero FinCorp. Lending product growth.",
     ["Product Management", "Cross-Sell", "Lending", "Growth", "Financial Services"],
     "MAYBE",
     "Associate Product level (mid-IC); lending/cross-sell is product-growth lane."),
    ("indeed", "Product Owner", "Ameriprise India",
     "https://in.indeed.com/viewjob?jk=057f9a3c18123a2e",
     "Gurugram, Haryana", "", "Financial Services", "", "", "Mid", "", "2026-05-28T19:54:43",
     "PO at Ameriprise India. Wealth-management financial services product ownership.",
     ["Product Owner", "Wealth Management", "Financial Services", "Agile"],
     "MAYBE",
     "PO role at large NBFC/wealth player; CSPO direct fit; Gurugram."),
    ("indeed", "Product Manager I", "Principal Global Services",
     "https://in.indeed.com/viewjob?jk=8b9afe4e7e321b16",
     "Pune, Maharashtra", "", "Financial Services", "", "", "Mid", "", "2026-05-27T00:16:06",
     "PM I (entry-mid level) at Principal Global Services. Retirement/insurance financial products.",
     ["Product Management", "Retirement", "Insurance", "Financial Services"],
     "MAYBE",
     "PM I = entry-mid PM level; large stable employer; Pune."),

    # ── Naukri (11 net-new in-band) ────────────────────────────────────────
    ("naukri", "Product Manager", "Bajaj Finserv Health",
     "https://www.nma.mobi/post/v4/job/260526016728?src=jobsearchios&brandedJd=true&xp=0&brandedConsultantJd=true",
     "India", "", "Health Insurance", "", "", "", "2-4 Yrs", "2026-05-26 11:59:03",
     "2-4 yrs. Product discovery, PRD creation, API/system integrations, insurance lifecycle. "
     "Own insurer product roadmap, convert business needs to PRDs, manage go-live + lifecycle.",
     ["Product Discovery", "PRD", "API Integrations", "Insurance Lifecycle", "Roadmap"],
     "STRONG",
     "2-4 Yrs · exact 'product discovery + PRD + APIs' phrasing matches his About. AmbitionBox 3.6."),
    ("naukri", "Product Manager", "E2M Solutions",
     "https://www.nma.mobi/post/v4/job/260526505851?src=jobsearchios&brandedJd=true&xp=0&brandedConsultantJd=true",
     "India", "", "Product Management - Technology", "", "", "", "3-4 Yrs", "2026-05-26 17:59:39",
     "3-4 yrs PM at E2M Solutions (also posting on LinkedIn — same role family).",
     ["Product Management", "Agile", "Cross-functional"],
     "MAYBE",
     "3-4 Yrs · same employer as LinkedIn E2M listing; Naukri pipeline copy. AmbitionBox 3.6."),
    ("naukri", "Product Manager (Mobile Field Ops)", "Itron",
     "https://www.nma.mobi/post/v4/job/260526504981?src=jobsearchios&brandedJd=true&xp=0&brandedConsultantJd=true",
     "India", "", "Product Management - Other", "", "", "", "3-8 Yrs", "2026-05-26 17:57:05",
     "3-8 yrs. Bachelor's tech-related. Mobile applications for field operations across "
     "smartphone + tablet platforms. Disclaimer: aggregated.",
     ["Product Management", "Mobile Applications", "Field Operations", "iOS/Android"],
     "STRONG",
     "3-8 Yrs band fits lower edge; mobile field-ops PM = applied product (matches his hands-on lane). AmbitionBox 4.4."),
    ("naukri", "Product Manager", "Dataflow",
     "https://www.nma.mobi/post/v4/job/171025023099?src=jobsearchios&brandedJd=true&xp=0&brandedConsultantJd=true",
     "India", "", "Product Management - Technology", "", "", "", "2-5 Yrs", "2026-05-26 14:36:49",
     "2-5 yrs PM with expertise in data management or verification industries. "
     "Develop + execute roadmap, market analysis, lifecycle.",
     ["Product Management", "Data Management", "Verification", "Roadmap"],
     "MAYBE",
     "2-5 Yrs · data/verification industry · open enough to apply."),
    ("naukri", "Product Manager", "ti Steps",
     "https://www.nma.mobi/post/v4/job/280526017660?src=jobsearchios&brandedJd=true&xp=0&brandedConsultantJd=true",
     "India", "", "Product Management - Technology", "", "3.75-7 Lacs", "", "4-7 Yrs", "2026-05-28 13:22:03",
     "4-7 yrs. Product lifecycle, PRDs, roadmaps, GA/Mixpanel/Amplitude analytics. "
     "Agile ceremonies, cross-functional. ₹3.75-7 LPA disclosed.",
     ["Product Management", "PRD", "Roadmap", "Google Analytics", "Mixpanel", "Amplitude", "Agile"],
     "MAYBE",
     "4-7 Yrs · disclosed comp (below market but transparent) · analytics-tool match."),
    ("naukri", "Product Manager", "Turno",
     "https://www.nma.mobi/post/v4/job/220526500265?src=jobsearchios&brandedJd=true&xp=0&brandedConsultantJd=true",
     "India", "", "Product Management - Technology", "", "", "", "2-6 Yrs", "2026-05-22 15:56:15",
     "2-6 yrs PM at Turno (EV mobility startup). Light JD on Naukri.",
     ["Product Management", "Startup", "Mobility"],
     "MAYBE",
     "2-6 Yrs · EV mobility startup · light JD but accessible band. AmbitionBox 3.6."),
    ("naukri", "Product Manager (Android, Agile)", "SOTI",
     "https://www.nma.mobi/post/v4/job/280526503985?src=jobsearchios&brandedJd=true&xp=0&brandedConsultantJd=true",
     "India", "", "Product Management - Technology", "", "", "", "2-7 Yrs", "2026-05-28 18:25:55",
     "2+ yrs TPM/PM in Agile Scrum. Android + Agile Scrum experience. Tech credibility, "
     "evaluating tech, collaborating with engineers.",
     ["Product Management", "Android", "Agile Scrum", "Technical PM", "Engineering Collab"],
     "STRONG",
     "2+ Yrs lower bar · Technical PM Android Scrum · matches Atlassian/Jira/Agile experience."),
    ("naukri", "Product Manager (FinTech PCI DSS)", "Olx",
     "https://www.nma.mobi/post/v4/job/220526026809?src=jobsearchios&brandedJd=true&xp=0&brandedConsultantJd=true",
     "India", "", "Product Management - Technology", "", "", "", "3-6 Yrs", "2026-05-22 16:18:39",
     "3-6 yrs PM in FinTech/Payments with PCI DSS + agile expertise. Roadmaps, "
     "feature prioritization, market trends.",
     ["Product Management", "FinTech", "Payments", "PCI DSS", "Agile"],
     "MAYBE",
     "3-6 Yrs · PCI DSS niche · OLX = strong consumer brand. AmbitionBox 3.7."),
    ("naukri", "Product Manager (SaaS / Creative Tech)", "Clarovate",
     "https://www.nma.mobi/post/v4/job/260526033855?src=jobsearchios&brandedJd=true&xp=0&brandedConsultantJd=true",
     "India", "", "Product Management - Technology", "", "", "", "3-6 Yrs", "2026-05-26 17:59:36",
     "3-6 yrs PM at SaaS or creative tech startup. Simplify + streamline product experience. "
     "Hands-on, identify opportunities.",
     ["Product Management", "SaaS", "Creative Tech", "Startup", "UX Simplification"],
     "MAYBE",
     "3-6 Yrs · SaaS startup · hands-on PM phrasing matches his style."),
    ("naukri", "Product Manager (Consumer)", "Coupondunia",
     "https://www.nma.mobi/post/v4/job/270526502796?src=jobsearchios&brandedJd=true&xp=0&brandedConsultantJd=true",
     "India", "", "Product Management - Other", "", "", "", "3-8 Yrs", "2026-05-27 17:29:03",
     "2-3+ yrs PM with consumer-facing/tech product ownership. BTech + MBA preferred. "
     "Every feature must come with a story about what was measured. Mumbai preferred.",
     ["Product Management", "Consumer Product", "Metrics-Driven", "Mumbai"],
     "MAYBE",
     "2-3+ yrs lower bar · 'measured + story' phrasing matches metric storytelling. AmbitionBox 4.7."),
    ("naukri", "Product Manager (Trading APIs / Algo)", "Dhani Loans and Services (DLSL)",
     "https://www.nma.mobi/post/v4/job/260526023681?src=jobsearchios&brandedJd=true&xp=0&brandedConsultantJd=true",
     "India", "", "BFSI Trading", "", "", "", "3-8 Yrs", "2026-05-26 14:55:44",
     "2-5 yrs PM in Indian trading tech. Open APIs, algo approval, derivatives. "
     "Own Open Trading APIs roadmap, algo approval lifecycle, retail algo trading.",
     ["Product Management", "Trading APIs", "Algo Approval", "Derivatives", "Indian Markets"],
     "MAYBE",
     "2-5 Yrs (low end) · niche but APIs-PM lane fits."),
    ("naukri", "Product Manager (Fraud / Data)", "Avant-Garde Corporate Services",
     "https://www.nma.mobi/post/v4/job/220526919071?src=jobsearchios&brandedJd=true&xp=0&brandedConsultantJd=true",
     "India", "", "Product Management - Other", "", "", "", "3-5 Yrs", "2026-05-22 12:39:05",
     "3-5 yrs PM or related tech roles. Data-led product thinking. Fraud analytics, "
     "underwriting, BI. End-to-end lifecycle, translate business needs to data solutions.",
     ["Product Management", "Fraud Analytics", "Underwriting", "BI", "Data-Led"],
     "MAYBE",
     "3-5 Yrs · data-led PM phrasing · BFSI risk space."),
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
