"""Spin (manual trigger) 2026-05-28: net-new fresh hiring data across sources.

LinkedIn (fantastic-jobs, 24h, India, 50-1000, ≤5yr): 8 returned, 4 net-new.
Naukri (memo23, 3-day freshness, employer-only, India, min-exp <=3): 50 returned,
4 net-new clean fits.
Indeed (misceres, "associate product manager", IN): 25 returned, 1 net-new.

Total: 9 net-new jobs. STRONG if min<=2 OR strong domain match.
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
    # ── LinkedIn (4) ─────────────────────────────────────────────────────────
    ("apify-linkedin", "Product Manager, API, Integrations & Platform", "Saleshandy", "https://in.linkedin.com/jobs/view/product-manager-api-integrations-platform-at-saleshandy-at-saleshandy-4417612323", "Ahmedabad", "51-200 employees", "Software Development", "On-site", "", "Mid-Senior level", "2-5 yrs", "2026-05-28T06:31:40",
     "Demonstrated history of shipping platform, API, or integration products on B2B SaaS. Hands-on technical fluency, direct user research, comfort defining/reading product metrics. REST, OAuth, webhooks, SQL, Postman.",
     ["Product Management", "API", "Integrations", "SaaS", "REST", "OAuth", "Webhooks", "SQL", "Postman", "Developer Experience"],
     "STRONG", "2-5yr band, Mid-Senior, target lane (API/Platform PM), Ahmedabad, technical PM fit."),
    ("apify-linkedin", "Technical Product Manager, Email Deliverability & Infrastructure", "Saleshandy", "https://in.linkedin.com/jobs/view/technical-product-manager-email-deliverability-infrastructure-at-saleshandy-at-saleshandy-4417614256", "Ahmedabad", "51-200 employees", "Software Development", "On-site", "", "Mid-Senior level", "2-5 yrs", "2026-05-28T06:22:59",
     "Strong technical fluency in SMTP and IMAP. SPF/DKIM/DMARC, email deliverability, SQL, debugging. Curiosity about email systems + customer success exposure.",
     ["SMTP", "IMAP", "SPF/DKIM/DMARC", "Email Deliverability", "SQL", "Debugging", "Product Management", "Customer Success"],
     "STRONG", "2-5yr band, Mid-Senior, technical PM lane, niche-but-customer-facing tech."),
    ("apify-linkedin", "Product Manager - B2C", "Noise", "https://in.linkedin.com/jobs/view/product-manager-b2c-at-noise-4418880112", "Gurugram", "201-500 employees", "Computers and Electronics Manufacturing", "On-site", "", "Mid-Senior level", "1-3 yrs", "2026-05-28T00:49:49",
     "1-3 years consumer-app PM, wireframing + prototyping in Figma. Background in Bluetooth/connected-device technology preferred. Consumer technology awareness.",
     ["Product Management", "Consumer App", "Figma", "Wireframing", "Prototyping", "AI Tools", "Analytics", "User Interviews", "Bluetooth Devices"],
     "MAYBE", "1-3yr band, consumer + hardware focus (B2C, electronics manufacturing), not core lane but accessible."),
    ("apify-linkedin", "Product Manager", "Signzy", "https://in.linkedin.com/jobs/view/product-manager-at-signzy-4418857204", "Bengaluru", "201-500 employees", "Financial Services", "On-site", "", "Mid-Senior level", "3+ yrs", "2026-05-27T20:59:10",
     "3+ years as PM with engineering background. Original research, structured thinking, empathy, communication.",
     ["Product Management", "Communication", "Empathy", "Structured Thinking", "Research"],
     "MAYBE", "3+yr ask is borderline, but strong fintech identity-verification company (Signzy = KYC/identity SaaS)."),
    # ── Naukri (4) ───────────────────────────────────────────────────────────
    ("naukri", "Product Manager", "Talentsavvy Software", "https://www.nma.mobi/post/v4/job/280526501963?src=jobsearchios&brandedJd=true&xp=0&brandedConsultantJd=true", "India", "", "Product Management - Technology", "", "", "", "3-5 Yrs", "2026-05-28 17:48:46",
     "3-5 years in management consulting (references required).",
     ["Product Management", "Consulting"],
     "MAYBE", "3-5 Yrs · Product Management - Technology · light JD."),
    ("naukri", "Product Manager (IAM / IGA)", "Farsighted Systems", "https://www.nma.mobi/post/v4/job/260526024187?src=jobsearchios&brandedJd=true&xp=0&brandedConsultantJd=true", "India", "", "Product Management - Technology", "Hybrid", "10-12 LPA", "", "3-4 Yrs", "2026-05-26 15:10:05",
     "3-4 years PM in B2B SaaS or Cybersecurity with IAM & IGA. Familiarity with SailPoint, Saviynt, Okta, ForgeRock, CyberArk, or Entra ID. Define + execute product roadmap.",
     ["Product Management", "IAM", "IGA", "B2B SaaS", "Cybersecurity", "SailPoint", "Saviynt", "Okta", "Identity Governance"],
     "STRONG", "3-4 Yrs · IAM/IGA cybersecurity (mirrors Tech Prescient role) · Hybrid · ₹10-12 LPA disclosed · AmbitionBox 4.0."),
    ("naukri", "Product Manager", "Skillzi", "https://www.nma.mobi/post/v4/job/160526009431?src=jobsearchios&brandedJd=true&xp=0&brandedConsultantJd=true", "India", "", "Product Management - Technology", "", "", "", "3-4 Yrs", "2026-05-16 09:14:26",
     "3-4 years PM with strong analytical skills and technical proficiency. Lead product definition concept-to-launch, requirements, cross-functional collaboration, UX focus.",
     ["Product Management", "Analytical Skills", "Technical Proficiency", "Cross-functional", "UX"],
     "MAYBE", "3-4 Yrs · Product Management - Technology · AmbitionBox 4.5."),
    ("naukri", "Product Manager (FinTech / NBFC Lending)", "Ofb Tech", "https://www.nma.mobi/post/v4/job/190526030136?src=jobsearchios&brandedJd=true&xp=0&brandedConsultantJd=true", "India", "", "Product Management - Technology", "", "", "", "3-6 Yrs", "2026-05-19 16:54:37",
     "3-6 years in Product Management within Fintech NBFC lending. MBA/PGDM preferred. Manage product lifecycle, own P&L, analyze product performance.",
     ["Product Management", "Fintech", "NBFC", "Lending", "P&L", "Product Lifecycle"],
     "MAYBE", "3-6 Yrs · FinTech NBFC lending."),
    # ── Indeed (1) ───────────────────────────────────────────────────────────
    ("indeed", "Product Manager (AI)", "Kodo Technologies", "https://in.indeed.com/viewjob?jk=7cd5584e9751f9ef", "Mumbai", "", "", "", "", "", "", "2026-05-28T10:59:47",
     "AI Product Manager role at Kodo (Mumbai). Indeed listing - open to view full JD on Indeed.",
     ["Product Management", "AI"],
     "MAYBE", "Indeed listing · Mumbai · AI PM (open Indeed for full JD)."),
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
