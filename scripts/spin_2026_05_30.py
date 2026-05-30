"""Spin (manual trigger) 2026-05-30: net-new fresh hiring data.

LinkedIn (fantastic-jobs): 40 returned, but location_filter="India" failed —
got global noise (Mexico/UK/US/Bolivia). Dropped entirely from this spin;
needs filter rework before next firing.
Naukri (memo23, 3-day, employer, IN, ≤3): 48 returned, 6 net-new in-band
  (≤6 yrs, PM lane). Dropped 30+ senior/non-tech.
Indeed (misceres, "associate product manager", IN): 25 returned, 9 net-new
  in-band (Mid PM/PO/APM). Dropped Sr/Lead/Principal/AVP and pharma/dental.

Total: 15 net-new in-band jobs. STRONG = brand or low-YoE + clear lane.
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
    # ── Naukri (6 net-new in-band) ──────────────────────────────────────────
    ("naukri", "Product Manager", "Cyces Innovation Labs",
     "https://www.nma.mobi/post/v4/job/290526504352?src=jobsearchios&brandedJd=true&xp=0&brandedConsultantJd=true",
     "India", "", "Product Management - Technology", "", "", "", "2-3 Yrs", "2026-05-29 17:13:36",
     "2-3 yrs PM at Cyces Innovation Labs. Lowest YoE band in today's spin.",
     ["Product Management", "Tech Startup"],
     "STRONG",
     "2-3 Yrs · lowest YoE band in today's spin · entry-mid PM. AmbitionBox 3.6."),
    ("naukri", "Product Manager", "Inorvia Global Tech",
     "https://www.nma.mobi/post/v4/job/300526012019?src=jobsearchios&brandedJd=true&xp=0&brandedConsultantJd=true",
     "India", "", "Product Management - Technology", "", "6-9 Lacs", "", "4-8 Yrs", "2026-05-30 14:53:46",
     "Product roadmapping, feature prioritisation, user journey mapping, "
     "analytics using Jira/Notion/Figma/GA/Mixpanel. Define roadmap, translate "
     "business needs to specs, launch features, analyse feedback + performance.",
     ["Product Management", "Roadmap", "Feature Prioritisation", "User Journey",
      "Jira", "Notion", "Figma", "Google Analytics", "Mixpanel"],
     "STRONG",
     "4-8 Yrs (lower edge fits) · exact tool match (Jira+Notion+Figma+GA+Mixpanel) · ₹6-9 LPA disclosed."),
    ("naukri", "Product Manager", "Star Health Insurance",
     "https://www.nma.mobi/post/v4/job/270426005859?src=jobsearchios&brandedJd=true&xp=0&brandedConsultantJd=true",
     "India", "", "Health Insurance", "", "", "", "4-6 Yrs", "2026-05-29 11:31:45",
     "4+ yrs PM with Agile, product lifecycle, user research, A/B testing, "
     "Jira and Asana. Lead end-to-end digital product development, "
     "define roadmaps, prioritise features, drive launches, monitor performance.",
     ["Product Management", "Agile", "Product Lifecycle", "User Research",
      "A/B Testing", "Jira", "Asana", "Health Insurance"],
     "STRONG",
     "4-6 Yrs · tight band match · BFSI/Health Insurance domain · Jira+Agile stack. AmbitionBox 3.5."),
    ("naukri", "Product Manager", "Lodha",
     "https://www.nma.mobi/post/v4/job/300426024121?src=jobsearchios&brandedJd=true&xp=0&brandedConsultantJd=true",
     "India", "", "Software Development", "", "", "", "3-8 Yrs", "2026-05-28 17:25:08",
     "3+ yrs PM with product roadmap, requirement analysis, consumer-facing products. "
     "Lead lifecycle vision to launch, market research, backlog, cross-functional collab.",
     ["Product Management", "Roadmap", "Requirements", "Consumer Product", "Backlog"],
     "MAYBE",
     "3-8 Yrs (lower edge fits) · Lodha = top India RE brand. AmbitionBox 4.2 (high)."),
    ("naukri", "Product Manager", "Fablead Developers Technolab",
     "https://www.nma.mobi/post/v4/job/290526507616?src=jobsearchios&brandedJd=true&xp=0&brandedConsultantJd=true",
     "India", "", "Product Management - Other", "", "", "", "2-7 Yrs", "2026-05-29 17:23:12",
     "PM role at Fablead Developers Technolab. Light JD on Naukri.",
     ["Product Management"],
     "MAYBE",
     "2-7 Yrs band · light JD but YoE band fits."),
    ("naukri", "Product Manager", "Trinet Group",
     "https://www.nma.mobi/post/v4/job/290526506014?src=jobsearchios&brandedJd=true&xp=0&brandedConsultantJd=true",
     "India", "", "Product Management - Other", "", "", "", "2-7 Yrs", "2026-05-29 17:17:07",
     "Build products from existing ideas or develop new ones. Represent interests "
     "of customers, prospects, partners. Bachelor's degree or equivalent.",
     ["Product Management", "Customer Research", "Cross-functional"],
     "MAYBE",
     "2-7 Yrs · open Bachelor's gate · customer-rep phrasing. AmbitionBox 3.0."),

    # ── Indeed (9 net-new in-band) ──────────────────────────────────────────
    ("indeed", "Product Owner — Salesforce", "Bridgenext",
     "https://in.indeed.com/viewjob?jk=d0d800b7d4f711e4",
     "Pune, Maharashtra", "", "IT Services", "", "", "Mid", "", "2026-05-30T11:36:03",
     "PO role at Bridgenext, Salesforce CRM platform. Pune location.",
     ["Product Owner", "Salesforce", "CRM", "Agile", "Scrum"],
     "STRONG",
     "Pune-based PO (his city) · Salesforce CRM lane · CSPO direct fit. AmbitionBox 4.1."),
    ("indeed", "Product Owner - MoMa Conventional", "Schneider Electric",
     "https://in.indeed.com/viewjob?jk=158021d329f6fa92",
     "Bengaluru, Karnataka", "", "Industrial Automation", "", "", "Mid", "", "2026-05-30T01:32:13",
     "PO at Schneider Electric, MoMa Conventional product line. Industrial automation.",
     ["Product Owner", "Industrial Automation", "Agile"],
     "STRONG",
     "Schneider = enterprise B2B brand · PO lane · CSPO direct fit. AmbitionBox 3.9."),
    ("indeed", "Product Manager", "Booking Holdings",
     "https://in.indeed.com/viewjob?jk=bd0d3ae0107f6ca3",
     "Bengaluru, Karnataka", "", "Travel Tech", "", "", "Mid", "", "2026-05-29T09:35:12",
     "PM role at Booking Holdings (Booking.com parent). Travel-tech SaaS at scale.",
     ["Product Management", "Travel Tech", "Consumer Product", "SaaS"],
     "STRONG",
     "Booking.com = global travel-tech leader · standard PM (not Sr/Lead) · Bengaluru."),
    ("indeed", "Product Manager", "Tesco India",
     "https://in.indeed.com/viewjob?jk=fd26b8fbdca8a5ed",
     "Bengaluru, Karnataka", "", "Retail Tech", "", "", "Mid", "", "2026-05-29T10:15:11",
     "PM at Tesco India tech hub. Retail-tech product (his RCS retail commerce experience fits).",
     ["Product Management", "Retail Tech", "Consumer Product"],
     "STRONG",
     "Tesco = global retail brand · standard PM (not Sr) · retail-tech matches his D·engage retail RCS work. AmbitionBox 3.5."),
    ("indeed", "Associate Product Development Owner", "CSC (Corporation Service Company)",
     "https://in.indeed.com/viewjob?jk=ae7214c04bed8d43",
     "Mumbai, Maharashtra", "", "Business Services / SaaS", "", "", "Associate", "", "2026-05-29T15:48:55",
     "Assoc PDO at CSC. Mumbai. Associate-level explicit in title.",
     ["Product Owner", "Associate", "Business Services", "Agile"],
     "STRONG",
     "Associate-level explicit (his exact level) · CSPO fit · Mumbai. AmbitionBox 3.3."),
    ("indeed", "Digital Product Manager", "PepsiCo",
     "https://in.indeed.com/viewjob?jk=e3d639bd8ff6b9a0",
     "Gurugram, Haryana", "", "CPG/FMCG Digital", "", "", "Mid", "", "2026-05-30T00:30:42",
     "Digital PM at PepsiCo Gurugram. Consumer digital products inside a CPG giant.",
     ["Digital Product Management", "Consumer", "Mobile/Web"],
     "MAYBE",
     "PepsiCo brand · standard Digital PM (not Sr/Lead) · Gurugram. AmbitionBox 3.7."),
    ("indeed", "Data Product Manager", "Carrier",
     "https://in.indeed.com/viewjob?jk=988ac3e59aa0671d",
     "Bengaluru, Karnataka", "", "Industrial / IoT", "", "", "Mid", "", "2026-05-29T14:02:53",
     "Data PM at Carrier (HVAC IoT leader). Data products inside enterprise IoT.",
     ["Data Product Management", "IoT", "Analytics"],
     "MAYBE",
     "Standard PM tier · Carrier = global industrial IoT brand · Bengaluru. AmbitionBox 3.8."),
    ("indeed", "Manager - Digital Product Management", "American Express",
     "https://in.indeed.com/viewjob?jk=2a80d51d1ee0922c",
     "Gurugram, Haryana", "", "Financial Services / Fintech", "", "", "Mid-Senior", "", "2026-05-29T11:46:24",
     "Manager - Digital PM at American Express. Mid-senior IC / first-line manager band.",
     ["Digital Product Management", "Fintech", "Cards/Payments"],
     "MAYBE",
     "Manager band (borderline senior but accessible) · AmEx fintech brand · Gurugram. AmbitionBox 4.1."),
    ("indeed", "Product Manager", "Sagility",
     "https://in.indeed.com/viewjob?jk=4a56ca69a6c581a0",
     "Bengaluru, Karnataka", "", "Healthcare BPM", "", "", "Mid", "", "2026-05-29T18:55:07",
     "PM at Sagility (healthcare BPM / tech-enabled services). Bengaluru.",
     ["Product Management", "Healthcare", "BPM"],
     "MAYBE",
     "Standard PM tier · healthcare BPM domain. AmbitionBox 3.1."),
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
