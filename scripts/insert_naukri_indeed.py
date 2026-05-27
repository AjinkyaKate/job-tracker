"""Insert curated Naukri + Indeed jobs into Discover (source-tagged).

Naukri (memo23/naukri-scraper run 2ui36y9cy1hEnsicf): 40 PM jobs pulled,
filtered to those where Ajinkya meets the floor (min experience <= 3, software/
tech PM, not closed, deduped vs LinkedIn). Rich data: experience band, salary,
role category, AmbitionBox rating.

Indeed (misceres/indeed-scraper run 3hYtI4buW6X4xjv43): 30 pulled but mostly
senior / non-tech 'product manager' noise (no experience filter on Indeed).
Only the 3 clearly-junior software ones kept.

Idempotent: dedups by link. min-exp<=2 -> STRONG, else MAYBE.
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


# Naukri picks: (title, company, min, max, exp_text, salary_label, role_cat, rating, desc, url)
NAUKRI = [
    ("Product Manager", "Dataflow", 2, 5, "2-5 Yrs", "", "Product Management - Technology", "2.9",
     "2-5 yrs PM with data-management or verification-industry expertise. Own product strategy and roadmap, cross-functional collaboration, market analysis, lifecycle management, customer advocacy.",
     "https://www.nma.mobi/post/v4/job/171025023099"),
    ("Product Manager (GenAI / Agentic AI - Lending)", "Turno", 2, 6, "2-6 Yrs", "15-28 Lacs", "Product Management - Technology", "3.6",
     "2-6 yrs in Fintech/NBFC/digital lending with GenAI, Agentic AI, RAG frameworks, prompt engineering, workflow automation. Lead end-to-end productization of AI-driven LOS/LMS workflows.",
     "https://www.nma.mobi/post/v4/job/200526027037"),
    ("Product Manager", "Wells Fargo", 2, 7, "2-7 Yrs", "", "Product Management - Other", "3.6",
     "2+ yrs Product Management / product development with SQL, regulatory compliance, banking-systems integration. Manage product lifecycle, market analysis, agile delivery.",
     "https://www.nma.mobi/post/v4/job/140526913730"),
    ("Product Manager", "Bajaj Finserv Health", 2, 4, "2-4 Yrs", "", "Product Management - Technology", "3.6",
     "Product discovery, PRD creation, API/system integrations, insurance-lifecycle knowledge. Own insurer product roadmap, convert business needs into PRDs, coordinate with engineering and QA.",
     "https://www.nma.mobi/post/v4/job/260526016728"),
    ("Product Manager (Retail Lending)", "Newgen", 2, 6, "2-6 Yrs", "10-15 Lacs", "Product Management - Technology", "4.1",
     "Retail Lending domain with Loan Origination System and Credit Appraisal. Design and enhance retail lending products, gather requirements, coordinate with cross-functional teams and clients.",
     "https://www.nma.mobi/post/v4/job/250526006232"),
    ("Product Manager", "Coupondunia", 3, 8, "3-8 Yrs", "", "Product Management - Other", "4.7",
     "2/3+ yrs PM owning consumer-facing or tech products. Every feature shipped should come with a story about what you measured. Mumbai-based preferred. MBA a plus.",
     "https://www.nma.mobi/post/v4/job/270526502796"),
    ("Product Manager (Field-Ops Mobile)", "Itron", 3, 8, "3-8 Yrs", "", "Product Management - Other", "4.4",
     "Develop and deploy mobile applications for field operations across smartphone and tablet platforms. Bachelor's in a technology-related field or equivalent.",
     "https://www.nma.mobi/post/v4/job/260526504981"),
    ("Product Manager (FinTech / Payments)", "OLX", 3, 6, "3-6 Yrs", "", "Product Management - Technology", "3.7",
     "3-6 yrs as PM in FinTech/Payments with PCI DSS and agile expertise. Develop and maintain product roadmaps, prioritize features, analyze market trends, manage multiple projects.",
     "https://www.nma.mobi/post/v4/job/220526026809"),
    ("Product Manager", "Clarovate", 3, 6, "3-6 Yrs", "", "Product Management - Technology", "",
     "3-6 yrs PM, ideally at a SaaS or creative-tech startup. Hands-on role: identify opportunities to simplify and streamline the product experience.",
     "https://www.nma.mobi/post/v4/job/260526033855"),
    ("Product Manager", "Sumo Logic", 3, 8, "3-8 Yrs", "", "Product Management - Other", "3.3",
     "CS/Engineering degree (MBA a plus). Contribute to go-to-market strategies, collaborate with product marketing and sales to communicate UX and dashboarding value.",
     "https://www.nma.mobi/post/v4/job/200526503991"),
    ("Product Manager (Trading Tech)", "Dhani Loans and Services", 3, 8, "3-8 Yrs", "", "BFSI, Investments & Trading", "3.9",
     "2-5 yrs PM in Indian trading tech with Open APIs, algo approval, Indian derivatives. Own roadmap for Open Trading APIs, manage algo-approval lifecycle, work with tech and compliance.",
     "https://www.nma.mobi/post/v4/job/260526023681"),
    ("Product Manager (Conversational AI)", "Leena AI", 2, 9, "2+ yrs PM (4 overall)", "", "Product Management - Other", "3.7",
     "Min 2 yrs in product management (4 yrs overall). Tier-1 engineering background. Strong B2B SaaS background preferred. Understanding of AI and conversational technologies a plus.",
     "https://www.nma.mobi/post/v4/job/270526501414"),
]

# Indeed picks: (title, company, location, url, rating)
INDEED = [
    ("Product Manager - Data and Quality (Associate)", "JPMorgan Chase", "Bengaluru", "https://in.indeed.com/viewjob?jk=92218f0582523fd4", "3.9"),
    ("Product Manager I (L50)", "Deloitte", "Bengaluru", "https://in.indeed.com/viewjob?jk=051474e367dcc373", "3.9"),
    ("Product Manager", "Resilience InfoTech", "Bengaluru", "https://in.indeed.com/viewjob?jk=0623940753ba55be", "0"),
]


def main():
    now = datetime.now(timezone.utc).isoformat()
    ins = dup = 0
    tiers = {"STRONG": 0, "MAYBE": 0}
    with get_connection() as conn:
        def insert(title, company, link, location, size, industry, work, comp,
                   yoe, posted, source, summary, skills, tier, reason):
            nonlocal ins, dup
            if conn.execute("SELECT id FROM jobs WHERE user_id=? AND link=?",
                            (USER_ID, link)).fetchone():
                dup += 1
                return
            conn.execute(
                "INSERT INTO jobs (user_id,title,company,link,location,company_size,"
                "company_industry,work_arrangement,comp_range,level,yoe_required,"
                "posted_at,source,jd_summary,must_have_skills,jd_raw_text,ai_score,"
                "ai_score_reason,status,added_at) VALUES "
                "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (USER_ID, s(title), s(company), s(link), s(location), s(size),
                 s(industry), s(work), s(comp), "", s(yoe), s(posted), source,
                 s(summary), s(skills), s(summary), tier, reason, "discovered", now))
            ins += 1
            tiers[tier] = tiers.get(tier, 0) + 1

        for (title, comp_name, mn, mx, exp, sal, role, rating, desc, url) in NAUKRI:
            tier = "STRONG" if mn <= 2 else "MAYBE"
            reason = f"{exp} · {role}" + (f" · AmbitionBox {rating}" if rating else "")
            insert(title, comp_name, url, "India", "", role, "",
                   (sal + " (PA)") if sal else "", exp, "", "naukri", desc, "", tier, reason)

        for (title, comp_name, loc, url, rating) in INDEED:
            reason = "Indeed listing" + (f" · rating {rating}" if rating and rating != "0" else "") + " · open to view full JD"
            insert(title, comp_name, url, loc, "", "", "", "", "", "", "indeed",
                   "Indeed listing. Open on Indeed for the full JD and requirements.", "", "MAYBE", reason)

        conn.commit()
        total = conn.execute("SELECT COUNT(*) AS n FROM jobs WHERE user_id=? AND status='discovered'", (USER_ID,)).fetchone()["n"]
        by_src = conn.execute("SELECT source, COUNT(*) AS n FROM jobs WHERE user_id=? AND status='discovered' GROUP BY source", (USER_ID,)).fetchall()
    print(f"Inserted: {ins}  Deduped: {dup}  Tiers: {tiers}")
    print(f"Total discovered: {total}")
    print("By source:", {r["source"]: r["n"] for r in by_src})


if __name__ == "__main__":
    main()
