"""One-shot insert of the experience-filtered Apify v2 scrape (25 jobs).

Source: fantastic-jobs run leYulXx3tTw6fXaD9 (dataset LwSUexHAEV7JkFIRz).
Filters: ai_experience_level in {0-2, 2-5}, all-India, 50-1000 employees,
last 7d, full-time. Keywords: AI PM / APM / PM / PO / Solutions Engineer /
Customer Success+Service Engineer.

Inserts into jobs (status='discovered', source='apify-linkedin'), dedups by
link, attaches recruiter as a contacts row. Auto-scores fit (STRONG/MAYBE/SKIP)
weighted toward Ajinkya's lane: junior experience band, target titles,
practical location (Pune/Mumbai/remote), reachable recruiter.

Idempotent: re-running skips any job whose link already exists for the user.
"""
import sys
from datetime import datetime, timezone

sys.path.insert(0, "/Users/ajinkya/Desktop/Ajinkya Kate/job-tracker")
from db import get_connection  # noqa: E402

USER_ID = 1


def s(v):
    """Coerce any scraped value to a clean string for SQLite binding."""
    if v is None:
        return ""
    if isinstance(v, (list, tuple)):
        return ", ".join(str(x) for x in v if x not in (None, ""))
    return str(v)


def fmt_salary(mn, mx, cur):
    if not mn and not mx:
        return ""
    cur = (cur or "").upper()
    if cur == "INR":
        def lpa(n):
            return f"{n / 100000:.0f}"
        if mn and mx:
            return f"₹{lpa(mn)}-{lpa(mx)} LPA"
        return f"₹{lpa(mn or mx)} LPA"
    if mn and mx:
        return f"{cur} {mn:,}-{mx:,}"
    return f"{cur} {mn or mx:,}"


TARGET_LANE = ("ai product", "associate product", "solutions engineer",
               "solution engineer", "customer success", "customer service",
               "customer engineer", "presales", "pre-sales", "product owner")


def score(exp, seniority, title, location, work, has_rec):
    sc = 6.0
    parts = []
    if exp == "0-2":
        sc += 2.0; parts.append("0-2yr band")
    elif exp == "2-5":
        sc += 1.0; parts.append("2-5yr band")
    sl = (seniority or "").lower()
    if "entry" in sl or "associate" in sl:
        sc += 1.0; parts.append(f"{seniority} level")
    elif seniority:
        parts.append(seniority)
    tl = (title or "").lower()
    lane_hit = next((k for k in TARGET_LANE if k in tl), None)
    if lane_hit:
        sc += 1.0; parts.append("target lane")
    loc = (location or "").lower()
    if "pune" in loc or "mumbai" in loc:
        sc += 1.0; parts.append(location)
    elif (work or "").lower().startswith("remote"):
        sc += 0.5; parts.append("remote")
    elif location:
        parts.append(location)
    if has_rec:
        sc += 0.5; parts.append("recruiter listed")
    if sc >= 8.5:
        tier = "STRONG"
    elif sc >= 6.5:
        tier = "MAYBE"
    else:
        tier = "SKIP"
    return tier, ", ".join(parts) + "."


# ── Scraped data (25 jobs) ──────────────────────────────────────────────────
DATA = [
    {"title": "Growth Product Manager", "org": "Arré", "city": "New Delhi", "url": "https://in.linkedin.com/jobs/view/growth-product-manager-at-arr%C3%A9-4418814274", "size": "51-200 employees", "industry": "Technology, Information and Media", "org_url": "http://www.arre.co.in", "work": "On-site", "smin": None, "smax": None, "scur": None, "posted": "2026-05-27T14:40:02", "sen": "Entry level", "exp": "0-2", "skills": ["Partnerships", "Communication", "Operations Management", "Community Building", "Content Creation", "User Engagement", "Social Media", "Networking"], "req": "Experience in partnerships, PR, or community building with digital/UGC products. Strong communication and detail-oriented operations. Hindi fluency.", "rname": "Pulkit Tiwari", "rtitle": "CTO & Founder | Ex-Google | IIT Delhi | ML Products at Scale", "rurl": "https://in.linkedin.com/in/pulkit-tiwari", "remail": None},
    {"title": "Associate Product Manager", "org": "Leucine - AI for Pharma", "city": "Bengaluru", "url": "https://in.linkedin.com/jobs/view/associate-product-manager-at-leucine-ai-for-pharma-4419874004", "size": "51-200 employees", "industry": "Pharmaceutical Manufacturing", "org_url": "https://www.leucine.io", "work": "On-site", "smin": None, "smax": None, "scur": None, "posted": "2026-05-27T12:30:21", "sen": "Associate", "exp": "2-5", "skills": ["Product Management", "React", "Node.js", "AI", "ML", "User Stories", "Customer Discovery", "Workflow Automation"], "req": "B.Tech from Tier-1/Tier-2 institute + 2-4 yrs PM, ideally B2B SaaS or AI/ML. Must demonstrate coding ability in React and Node.js.", "rname": "Ruppal Agarwal", "rtitle": "Senior Manager - HR | Talent Acquisition & HRBP | SaaS", "rurl": "https://in.linkedin.com/in/ruppal-agarwal", "remail": None},
    {"title": "Product Manager – Bancassurance & SaaS", "org": "Zopper", "city": "Noida", "url": "https://in.linkedin.com/jobs/view/product-manager-%E2%80%93-bancassurance-saas-at-zopper-4417204463", "size": "501-1,000 employees", "industry": "Insurance", "org_url": "https://www.zopper.com", "work": "On-site", "smin": None, "smax": None, "scur": None, "posted": "2026-05-27T10:23:58", "sen": "Mid-Senior level", "exp": "2-5", "skills": ["Product Management", "Stakeholder Management", "API Integration", "Insurance", "Bancassurance", "FinTech", "SaaS", "Data Analytics"], "req": "Bachelor's + 3-5 yrs PM. Insurance/bancassurance/FinTech preferred. API-based platforms and automation.", "rname": "Archana Sahu", "rtitle": "Associate Senior Manager - Talent Acquisition", "rurl": "https://in.linkedin.com/in/sahuarchana", "remail": None},
    {"title": "Associate Product Manager (AI Products)", "org": "Credgenics", "city": "Noida", "url": "https://in.linkedin.com/jobs/view/associate-product-manager-ai-products-at-credgenics-4419808259", "size": "501-1,000 employees", "industry": "Financial Services", "org_url": "https://credgenics.com", "work": "On-site", "smin": None, "smax": None, "scur": None, "posted": "2026-05-27T07:01:36", "sen": "Associate", "exp": "0-2", "skills": ["Data Science", "AI", "Machine Learning", "Product Management", "SQL", "Analytics", "User Research", "Experimentation"], "req": "B.Tech + strong data science understanding. AI/ML product exposure and strong analytical skills preferred.", "rname": None, "rtitle": None, "rurl": None, "remail": None},
    {"title": "Product Manager- Plum", "org": "Xoxoday", "city": "Bengaluru", "url": "https://in.linkedin.com/jobs/view/product-manager-plum-at-xoxoday-4418536376", "size": "501-1,000 employees", "industry": "Software Development", "org_url": "www.xoxoday.com", "work": "On-site", "smin": None, "smax": None, "scur": None, "posted": "2026-05-27T00:51:23", "sen": "Mid-Senior level", "exp": "2-5", "skills": ["Product Management", "API", "Technical Specifications", "Cross-Functional Collaboration", "Market Research", "Feature Development", "Prioritization"], "req": "2-5 yrs PM in a product-led company, hands-on with APIs. Strong communication and cross-functional working.", "rname": None, "rtitle": None, "rurl": None, "remail": None},
    {"title": "Data Product Owner", "org": "The Standard India", "city": "Bengaluru", "url": "https://in.linkedin.com/jobs/view/data-product-owner-at-the-standard-india-4418503792", "size": "51-200 employees", "industry": "IT Services and IT Consulting", "org_url": "https://www.stancorpglobalservices.in", "work": "On-site", "smin": None, "smax": None, "scur": None, "posted": "2026-05-26T21:48:09", "sen": "Entry level", "exp": "2-5", "skills": ["Product Owner", "Agile", "Data Engineering", "Data Analysis", "Business Intelligence", "SAFe Agile", "User Stories"], "req": "Bachelor's + min 2 yrs as Product Owner in Agile. Data engineering/analysis/BI strongly preferred.", "rname": None, "rtitle": None, "rurl": None, "remail": None},
    {"title": "CLAT Product Manager", "org": "iQuanta", "city": "Gurugram", "url": "https://in.linkedin.com/jobs/view/clat-product-manager-at-iquanta-4419195006", "size": "51-200 employees", "industry": "E-Learning Providers", "org_url": "https://www.iquanta.in", "work": "On-site", "smin": None, "smax": None, "scur": None, "posted": "2026-05-26T11:32:37", "sen": "Entry level", "exp": "2-5", "skills": ["Product Management", "EdTech", "Stakeholder Management", "Analytical Thinking", "Team Management", "LMS Management", "Content Workflows"], "req": "3-6 yrs PM, preferably EdTech/competitive-exam prep. Strong CLAT-ecosystem understanding, coordination and analytical skills.", "rname": None, "rtitle": None, "rurl": None, "remail": None},
    {"title": "Product Manager — NPS (National Pension System)", "org": "INDmoney", "city": "Gurugram", "url": "https://in.linkedin.com/jobs/view/product-manager-%E2%80%94-nps-national-pension-system-at-indmoney-4419181056", "size": "201-500 employees", "industry": "Financial Services", "org_url": "https://www.indmoney.com", "work": "On-site", "smin": None, "smax": None, "scur": None, "posted": "2026-05-26T10:51:31", "sen": "Mid-Senior level", "exp": "2-5", "skills": ["Product Management", "Consumer Fintech", "NPS", "SQL", "Mixpanel", "A/B Testing", "KYC", "PRD Writing"], "req": "2-3 yrs consumer fintech. Solid NPS understanding, comfort with data tools, compliance-heavy systems.", "rname": None, "rtitle": None, "rurl": None, "remail": None},
    {"title": "Product Manager (Adtech or Media)", "org": "DXFactor", "city": "", "url": "https://in.linkedin.com/jobs/view/product-manager-adtech-or-media-at-dxfactor-4415275373", "size": "51-200 employees", "industry": "IT Services and IT Consulting", "org_url": "http://www.dxfactor.com", "work": "Remote Solely", "smin": None, "smax": None, "scur": None, "posted": "2026-05-26T07:37:18", "sen": "Mid-Senior level", "exp": "2-5", "skills": ["Product Management", "AdTech", "Media", "Performance Marketing", "AI Tools", "Product Delivery", "Market Feedback"], "req": "2-5 yrs PM, particularly AdTech/Media. Meta Ads/TikTok Ads understanding plus AI-tool familiarity.", "rname": "Ishan Rohera", "rtitle": "Head - Talent Acquisition | Startup & Tech Hiring", "rurl": "https://in.linkedin.com/in/ishanrohera", "remail": None},
    {"title": "Product Manager", "org": "E2M", "city": "Ahmedabad", "url": "https://in.linkedin.com/jobs/view/product-manager-at-e2m-4419126976", "size": "201-500 employees", "industry": "IT Services and IT Consulting", "org_url": "https://www.e2msolutions.com", "work": "On-site", "smin": None, "smax": None, "scur": None, "posted": "2026-05-26T06:13:36", "sen": "Mid-Senior level", "exp": "2-5", "skills": ["Product Management", "Agile", "AI/ML", "Data Analysis", "Jira", "Confluence", "Figma", "SQL", "LLMs", "GenAI", "SaaS"], "req": "2-4 yrs PM, strong product-lifecycle + Agile understanding. Working knowledge of AI/ML products.", "rname": "Kawaljeet Singh", "rtitle": "Tech Talent Partner | Hiring in the WP Ecosystem", "rurl": "https://in.linkedin.com/in/kawaljeet-singh-913203123", "remail": None},
    {"title": "Associate Product Manager", "org": "Kaabil Finance", "city": "Jaipur", "url": "https://in.linkedin.com/jobs/view/associate-product-manager-at-kaabil-finance-private-limited-4417883260", "size": "501-1,000 employees", "industry": "Financial Services", "org_url": "https://kaabilfinance.com", "work": "On-site", "smin": None, "smax": None, "scur": None, "posted": "2026-05-25T13:28:03", "sen": "Entry level", "exp": "0-2", "skills": ["Product Management", "Product Development", "Business Analysis", "Strategic Thinking", "Market Research", "Requirement Gathering"], "req": "Product management + development, business analysis and strategic thinking. Bachelor's required; financial-services exposure a plus.", "rname": "Bhola Meena", "rtitle": "Tech - AI | Ex-Microsoft | IIT Kanpur", "rurl": "https://in.linkedin.com/in/bhola-meena", "remail": None},
    {"title": "Security Solutions Engineer", "org": "SQ1 Security", "city": "Chennai", "url": "https://in.linkedin.com/jobs/view/security-solutions-engineer-at-sq1-security-4418918880", "size": "201-500 employees", "industry": "Computer and Network Security", "org_url": "https://sq1.security", "work": "On-site", "smin": None, "smax": None, "scur": None, "posted": "2026-05-25T09:16:10", "sen": "Entry level", "exp": "0-2", "skills": ["Cybersecurity", "Firewalls", "EDR", "XDR", "SIEM", "Vulnerability Management", "Threat Detection", "Product Demonstrations"], "req": "Deploy and manage cybersecurity solutions, integrate with enterprise infra. Stay current on threats; maintain technical docs.", "rname": None, "rtitle": None, "rurl": None, "remail": None},
    {"title": "Associate Product Manager", "org": "ixigo", "city": "Gurugram", "url": "https://in.linkedin.com/jobs/view/associate-product-manager-at-ixigo-4418917750", "size": "201-500 employees", "industry": "Technology, Information and Internet", "org_url": "https://www.ixigo.com", "work": "On-site", "smin": None, "smax": None, "scur": None, "posted": "2026-05-25T08:16:43", "sen": "Associate", "exp": "0-2", "skills": ["Product Management", "Data Analysis", "User Experience", "Competitive Analysis", "A/B Testing", "Funnel Optimization"], "req": "1-3 yrs PM, preferably B2C e-commerce/travel. Strong analytical skills, customer-centric, PM + data-analysis tools.", "rname": None, "rtitle": None, "rurl": None, "remail": None},
    {"title": "AI Product Manager", "org": "Zoca", "city": "Bengaluru", "url": "https://in.linkedin.com/jobs/view/ai-product-manager-at-zoca-4417872272", "size": "51-200 employees", "industry": "Software Development", "org_url": "www.zoca.com", "work": "On-site", "smin": None, "smax": None, "scur": None, "posted": "2026-05-25T07:13:06", "sen": "Associate", "exp": "2-5", "skills": ["Customer Centric Solutions", "API Integration", "Machine Learning Workflows", "Product Management", "Agents", "Automation"], "req": "2-4 yrs PM or AI/ML product dev. Strong ML-workflow understanding, hands-on building AI-powered products, LLM and conversational-AI familiarity.", "rname": None, "rtitle": None, "rurl": None, "remail": None},
    {"title": "Product Manager (SaaS / Software Products)", "org": "Infosec Ventures", "city": "Gurugram", "url": "https://in.linkedin.com/jobs/view/product-manager-saas-software-products-at-infosec-ventures-4417858245", "size": "51-200 employees", "industry": "Computer and Network Security", "org_url": "https://www.infosecventures.com", "work": "On-site", "smin": None, "smax": None, "scur": None, "posted": "2026-05-25T06:54:11", "sen": "Mid-Senior level", "exp": "2-5", "skills": ["Product Management", "SaaS", "Cloud Platforms", "AI Tools", "PRDs", "APIs", "B2B SaaS", "Agile", "Scrum"], "req": "SaaS/software product experience, strong cloud-platform understanding, hands-on AI tools, clear PRDs and user stories.", "rname": None, "rtitle": None, "rurl": None, "remail": None},
    {"title": "AI UI/UX Designer And Product Manager", "org": "Growify Digital", "city": "New Delhi", "url": "https://in.linkedin.com/jobs/view/ai-ui-ux-designer-and-product-manager-in-delhi-at-growify-digital-4418619988", "size": "51-200 employees", "industry": "Advertising Services", "org_url": "http://growify.in", "work": "On-site", "smin": None, "smax": None, "scur": None, "posted": "2026-05-24T00:06:28", "sen": "Entry level", "exp": "0-2", "skills": ["UI Design", "UX Design", "Wireframing", "Prototyping", "AI Design Tools", "Product Management", "Agile"], "req": "Strong UX/UI design plus product management and documentation. AI design-tool familiarity and user-research ability.", "rname": None, "rtitle": None, "rurl": None, "remail": None},
    {"title": "Product Manager", "org": "CoreTek Labs", "city": "Hyderabad", "url": "https://in.linkedin.com/jobs/view/product-manager-at-coretek-labs-4417153272", "size": "51-200 employees", "industry": "Software Development", "org_url": "http://www.coretek.io", "work": "Hybrid", "smin": None, "smax": None, "scur": None, "posted": "2026-05-22T13:11:05", "sen": "Mid-Senior level", "exp": "2-5", "skills": ["Product Management", "AI", "Machine Learning", "Agile", "Scrum", "Jira", "NLP", "Conversational AI"], "req": "3-4 yrs as PO/PM, hands-on AI/ML or data-driven products. Strong Agile/Scrum understanding.", "rname": None, "rtitle": None, "rurl": None, "remail": None},
    {"title": "Associate Product Manager", "org": "peopleHum", "city": "Bengaluru", "url": "https://in.linkedin.com/jobs/view/associate-product-manager-at-peoplehum-4414099526", "size": "201-500 employees", "industry": "Human Resources Services", "org_url": "https://peoplehum.com", "work": "On-site", "smin": None, "smax": None, "scur": None, "posted": "2026-05-22T10:53:06", "sen": "Entry level", "exp": "2-5", "skills": ["Product Management", "B2B SaaS", "User Acceptance Testing", "AI Tools", "SQL", "Roadmap Execution", "Agile"], "req": "1-3 yrs PM in B2B SaaS, quality-obsessed mindset. CS/Engineering degree or equivalent; MBA a plus.", "rname": None, "rtitle": None, "rurl": None, "remail": None},
    {"title": "Product Manager (CarTrade Tech Mumbai)", "org": "OLX India", "city": "Mumbai", "url": "https://in.linkedin.com/jobs/view/product-manager-cartrade-tech-mumbai-at-olx-india-4414083825", "size": "501-1,000 employees", "industry": "Technology, Information and Internet", "org_url": "https://www.olx.in", "work": "On-site", "smin": None, "smax": None, "scur": None, "posted": "2026-05-22T08:35:57", "sen": "Associate", "exp": "2-5", "skills": ["Product Management", "Market Analysis", "AI", "Generative AI", "Agile", "Data Analysis", "Experimentation"], "req": "Postgraduate degree + 3+ yrs PM. Strong analytical/communication skills, AI/ML familiarity.", "rname": None, "rtitle": None, "rurl": None, "remail": None},
    {"title": "AI Solutions Engineer | 2-4 Years", "org": "Neuron7.ai", "city": "Bengaluru", "url": "https://in.linkedin.com/jobs/view/ai-solutions-engineer-2-4-years-at-neuron7-ai-4416386694", "size": "51-200 employees", "industry": "Software Development", "org_url": "https://www.neuron7.ai", "work": "On-site", "smin": None, "smax": None, "scur": None, "posted": "2026-05-21T19:39:41", "sen": "Entry level", "exp": "2-5", "skills": ["Python", "LLM & Agent Frameworks", "Prompt Engineering", "Async & Distributed Systems", "Databases & Search", "Cloud", "Customer Communication"], "req": "2-5 yrs, strong software engineering + hands-on AI/LLM. Python, LLM frameworks, customer-facing problem-solving.", "rname": "Rajesh Kumar Singh", "rtitle": "Human Resources, Operations & Talent Acquisition", "rurl": "https://in.linkedin.com/in/rajeshkrsinghhr", "remail": None},
    {"title": "Product Manager – IAM / IGA", "org": "Tech Prescient", "city": "Pune", "url": "https://in.linkedin.com/jobs/view/product-manager-%C3%A2%C2%80%C2%93-iam-iga-at-tech-prescient-4414010608", "size": "51-200 employees", "industry": "IT Services and IT Consulting", "org_url": "https://www.techprescient.com", "work": "On-site", "smin": 700000, "smax": 1200000, "scur": "INR", "posted": "2026-05-21T14:52:39", "sen": "Associate", "exp": "2-5", "skills": ["Product Management", "Product Roadmap", "PRD", "User Stories", "Agile", "Scrum", "Identity and Access Management", "Identity Governance"], "req": "3-4 yrs PM, ideally B2B SaaS or Cybersecurity. Strong IAM & IGA understanding, Agile/Scrum.", "rname": None, "rtitle": None, "rurl": None, "remail": None},
    {"title": "Product Manager - Android", "org": "Primebook India", "city": "New Delhi", "url": "https://in.linkedin.com/jobs/view/product-manager-android-at-primebook-india-4413696481", "size": "51-200 employees", "industry": "Computer Hardware Manufacturing", "org_url": "https://www.primebook.in", "work": "On-site", "smin": None, "smax": None, "scur": None, "posted": "2026-05-21T11:57:58", "sen": "Mid-Senior level", "exp": "2-5", "skills": ["Product Strategy", "Product Management", "Mobile Applications", "Analytics Platforms", "MySQL", "Android", "Scaling Mobile Apps"], "req": "Product strategy + management focused on mobile apps. Strong analytical skills, project management, analytics platforms.", "rname": None, "rtitle": None, "rurl": None, "remail": None},
    {"title": "Presales Specialist / Solutions Engineer", "org": "Kambaa Inc", "city": "", "url": "https://in.linkedin.com/jobs/view/presales-specialist-solutions-engineer-at-kambaa-inc-4416512069", "size": "11-50 employees", "industry": "IT Services and IT Consulting", "org_url": "kambaa.com", "work": "Remote Solely", "smin": None, "smax": None, "scur": "INR", "posted": "2026-05-21T09:13:04", "sen": "Associate", "exp": "2-5", "skills": ["Pre-Sales", "Solution Consulting", "SaaS Implementation", "CRM", "ITSM", "Demo Delivery", "Proposal Authoring", "Discovery Calls"], "req": "Min 2 yrs presales/solution consulting, Freshworks/HubSpot preferred. Exceptional communication, explain complex solutions to stakeholders.", "rname": "Roehan Rengadurai", "rtitle": "30u30 winner | Growth through Technology & AI", "rurl": "https://in.linkedin.com/in/iamroehan", "remail": "roehan@kambaa.in"},
    {"title": "Associate Product Manager | Gurgaon", "org": "FieldAssist", "city": "Gurugram", "url": "https://in.linkedin.com/jobs/view/associate-product-manager-gurgaon-at-fieldassist-4416353302", "size": "201-500 employees", "industry": "Software Development", "org_url": "https://www.fieldassist.com", "work": "On-site", "smin": None, "smax": None, "scur": None, "posted": "2026-05-21T00:49:54", "sen": "Mid-Senior level", "exp": "2-5", "skills": ["Product Management", "SQL", "User Acceptance Testing", "Data Analysis", "Agile", "SaaS", "Feature Prioritization"], "req": "Engineering/CS/Business degree + 2-3 yrs product, preferably SaaS. Strong analytical/problem-solving, drive adoption, resolve escalations.", "rname": None, "rtitle": None, "rurl": None, "remail": None},
    {"title": "Product Manager 1 - Mutual Fund", "org": "smallcase", "city": "Bengaluru", "url": "https://in.linkedin.com/jobs/view/product-manager-1-mutual-fund-at-smallcase-4416170542", "size": "201-500 employees", "industry": "Financial Services", "org_url": "http://smallcase.com", "work": "On-site", "smin": None, "smax": None, "scur": None, "posted": "2026-04-29T09:04:41", "sen": "Mid-Senior level", "exp": "2-5", "skills": ["Product Management", "A/B Testing", "Capital Markets", "Fintech", "Wealth Tech", "Consumer-Facing Products", "Competitive Intelligence"], "req": "2+ yrs PM with consumer-facing track record, ideally fintech/capital markets. Deep investing/markets understanding.", "rname": None, "rtitle": None, "rurl": None, "remail": None},
]


def main():
    now = datetime.now(timezone.utc).isoformat()
    inserted = dup = 0
    tiers = {"STRONG": 0, "MAYBE": 0, "SKIP": 0}
    rec_links = 0
    with get_connection() as conn:
        for j in DATA:
            link = j["url"]
            exists = conn.execute(
                "SELECT id FROM jobs WHERE user_id = ? AND link = ?",
                (USER_ID, link),
            ).fetchone()
            if exists:
                dup += 1
                continue
            has_rec = bool(j.get("rname"))
            tier, reason = score(j["exp"], j["sen"], j["title"], j["city"],
                                 j["work"], has_rec)
            tiers[tier] += 1
            cur = conn.execute(
                "INSERT INTO jobs (user_id, title, company, link, location, "
                "company_size, company_industry, company_url, work_arrangement, "
                "comp_range, level, yoe_required, posted_at, source, jd_summary, "
                "must_have_skills, jd_raw_text, ai_score, ai_score_reason, "
                "status, added_at) VALUES "
                "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (USER_ID, s(j["title"]), s(j["org"]), s(link), s(j["city"]),
                 s(j["size"]), s(j["industry"]), s(j["org_url"]), s(j["work"]),
                 fmt_salary(j["smin"], j["smax"], j["scur"]), s(j["sen"]),
                 s(j["exp"]) + " yrs", s(j["posted"]), "apify-linkedin",
                 s(j["req"]), s(j["skills"]), s(j["req"]), tier, reason,
                 "discovered", now),
            )
            job_id = cur.lastrowid
            if has_rec:
                rec_links += 1
                conn.execute(
                    "INSERT INTO contacts (user_id, job_id, name, role, "
                    "linkedin_url, email, added_at) VALUES (?,?,?,?,?,?,?)",
                    (USER_ID, job_id, s(j["rname"]), s(j["rtitle"]),
                     s(j["rurl"]), s(j.get("remail")), now),
                )
            inserted += 1
        conn.commit()

    print(f"Inserted: {inserted}  Deduped: {dup}")
    print(f"Tiers: {tiers}")
    print(f"Recruiter links attached: {rec_links}")
    with get_connection() as conn:
        total = conn.execute(
            "SELECT COUNT(*) AS n FROM jobs WHERE user_id = ? AND status = 'discovered'",
            (USER_ID,),
        ).fetchone()["n"]
    print(f"Total discovered jobs now: {total}")


if __name__ == "__main__":
    main()
