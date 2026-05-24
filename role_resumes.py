"""Pre-generated tailored resumes per role family.

Maps each LinkedIn-alert role family (Forward Deployed, AI PM, Founding, etc.)
to a resume markdown tuned for that role. Shares experience/education/certs;
varies the Summary + Skills order per role to mirror what recruiters scanning
those roles want to see first.

Used by /leads filter chips: clicking [Forward Deployed] surfaces a "Resume
for this role ready → Download" link pointing at /resumes/role/forward-deployed.
"""

# ─── Shared resume parts ────────────────────────────────────────────────────

HEADER = """# Ajinkya Kate

Pune District, Maharashtra, India · Available immediately · CSPO Certified
[LinkedIn](https://linkedin.com/in/ajinkya-kate) · [GitHub](https://github.com/AjinkyaKate)
"""

EXPERIENCE = """## Experience

**Product Owner** · D·engage · Jan 2025 – May 2026 · Remote (India)

- Owned end-to-end product delivery for a cross-functional team (engineering, design, QA) shipping marketing-automation features for enterprise clients across banking, retail, and telecom.
- Drove product discovery — customer interviews, competitor scans, hypothesis-driven prototypes — that fed directly into PRDs and sprint commitments.
- Shipped AI-powered features inside the engagement platform: LLM-assisted content generation, smart segmentation, personalization journeys — partnering with engineering on model selection, prompt design, and evaluation criteria.
- Ran 2-week sprint cadence: planning, backlog grooming, sprint reviews, release notes. Balanced new build vs technical debt vs production support based on customer impact.
- Translated enterprise customer feedback into prioritized roadmap items, working closely with CSM and Implementation teams to separate causing-churn from nice-to-have.
- Built quick prototypes (no-code + AI-assisted code) to validate ideas before engineering invested in proper builds.

**Product Analyst** · Denner.in · May 2024 – Dec 2024 · Pune (Hybrid)

- Owned product analytics + competitive research feeding into PM decisions; ran A/B test analysis, funnel deep-dives, and user-research synthesis.
"""

PROJECTS = """## Projects

**Personal Job-Application Tracker (AI-powered)** · May 2026 – ongoing · [github.com/AjinkyaKate/job-tracker](https://github.com/AjinkyaKate/job-tracker)
- Full-stack web app built during my own job search. FastAPI + PostgreSQL + Gemini email classification, deployed on Render with GitHub Actions cron for auto-sync.
- Features: LinkedIn job-alert email ingestion → leads inbox with chip filters, per-job tailored resume generation via Gemini, Gmail-triggered status auto-advance (saved → applied → interview → offer/rejected), per-contact LinkedIn-DM drafting.
- Real shipped product, used daily.

**Ticket-Native AI QA Agent** · 2026 – in progress (3-weekend v0) · [github.com/AjinkyaKate/qa-agent](https://github.com/AjinkyaKate/qa-agent)
- Small AI agent that reads ticket acceptance criteria → browses the system-under-test → asserts UI + API behavior → attaches results back to the ticket.
- Inspired by D·engage's manual QA loop. Using the job-tracker app as the v0 SUT.
"""

EDUCATION = """## Education

**Savitribai Phule Pune University** — Bachelor of Business Administration (BBA), Pune, India
"""

CERTIFICATIONS = """## Certifications

**Certified Scrum Product Owner (CSPO)** — Scrum Alliance · Nov 2025
"""


# ─── Per-role Summary + Skills ──────────────────────────────────────────────

ROLE_RESUMES = {
    "product-owner": {
        "summary": (
            "Product Owner with 2+ years building B2B SaaS — discovery → PRDs → sprints → ship → measure. "
            "Most recently at D·engage shipping marketing automation and AI-powered engagement features "
            "for enterprise clients in banking, retail, telecom. CSPO certified. Open to Product Owner "
            "roles in B2B SaaS, Pune-local, immediate joiner."
        ),
        "skills": (
            "**Product:** Agile/Scrum, Backlog grooming, Sprint planning, PRDs, User stories, Stakeholder management\n"
            "**Tools:** Jira, Notion, Confluence, Figma, Miro\n"
            "**Data:** SQL (basic), Amplitude, Mixpanel, A/B testing fundamentals\n"
            "**Domain:** B2B SaaS, MarTech, Customer Engagement Platforms, Enterprise (Banking/Retail/Telecom)"
        ),
    },
    "pm-apm": {
        "summary": (
            "Associate Product Manager / Product Manager with 2+ years owning B2B SaaS product delivery "
            "end-to-end. Most recently at D·engage shipping marketing-automation and AI-powered engagement "
            "features for enterprise customers in banking, retail, telecom. CSPO certified. Open to "
            "APM / PM / Senior PM seats in customer engagement, MarTech, AI-product SaaS."
        ),
        "skills": (
            "**Product:** Product discovery, PRDs, Roadmap planning, Cross-functional delivery, OKRs\n"
            "**Agile:** Scrum, Backlog management, Sprint planning, Release management\n"
            "**Tools:** Jira, Notion, Figma, Amplitude, Mixpanel, SQL\n"
            "**Domain:** B2B SaaS, MarTech, Customer Engagement, Enterprise SaaS (Banking/Retail/Telecom)"
        ),
    },
    "ai-product-manager": {
        "summary": (
            "AI Product Manager with 2+ years shipping AI-powered features in production B2B SaaS. "
            "At D·engage built LLM-driven engagement journeys, AI-powered content generation, smart "
            "segmentation — partnering with engineering on model selection, prompt design, and evaluation. "
            "Active builder of AI side projects: Gemini-powered email classification, AI agent for QA. "
            "Targeting AI Product Manager / Applied AI Product roles at AI-native or AI-forward B2B SaaS."
        ),
        "skills": (
            "**AI Product:** LLM feature design, Prompt engineering, RAG architecture (basics), Evaluation frameworks, AI-feature roadmapping\n"
            "**AI APIs:** Gemini, OpenAI, Anthropic Claude (familiar via personal projects)\n"
            "**Product:** PRDs, Discovery, Sprint planning, Cross-functional delivery\n"
            "**Data:** SQL, A/B testing, Funnel analysis, Cohort analysis\n"
            "**Code:** Python (intermediate), FastAPI, basic SQL/PostgreSQL\n"
            "**Domain:** B2B SaaS, Customer Engagement, MarTech, Enterprise AI"
        ),
    },
    "forward-deployed": {
        "summary": (
            "Forward-Deployed Product Builder with 2+ years end-to-end ownership of enterprise B2B SaaS "
            "customer outcomes. At D·engage owned product delivery for cross-functional team serving "
            "enterprise clients in banking, retail, telecom — discovery, customization, AI feature shipping, "
            "customer training, retention. Active code-side builder: shipped personal AI-powered job tracker "
            "(FastAPI + Postgres + Gemini, deployed) and AI QA agent. Targeting Forward Deployed Engineer / "
            "Forward Deployed PM / Customer Engineer (AI) roles where I own a few enterprise accounts "
            "end-to-end and ship code alongside customers."
        ),
        "skills": (
            "**Customer Ownership:** Enterprise customer discovery, Pain-point synthesis, Integration scoping, Onboarding & training, Health monitoring\n"
            "**AI Product:** LLM feature shipping, Prompt design, RAG basics, Evaluation, Gemini/OpenAI APIs\n"
            "**Code:** Python (intermediate), FastAPI, SQL/PostgreSQL, Git/GitHub, REST API integration\n"
            "**Product:** PRDs, Backlog management, Sprint planning, Cross-functional delivery\n"
            "**Domain:** B2B SaaS, MarTech, Customer Engagement, Enterprise (Banking/Retail/Telecom)"
        ),
    },
    "founding": {
        "summary": (
            "Builder-PM exploring Founding Engineer / Founding PM seats at AI-native seed/Series-A startups. "
            "2+ years shipping B2B SaaS at D·engage (customer engagement / MarTech for enterprise customers), "
            "plus shipped AI side projects in production: personal job-search tracker (FastAPI + Postgres + "
            "Gemini email classification, deployed on Render, in daily use) and a ticket-native AI QA agent. "
            "Comfortable wearing PM + engineer + customer-success hats simultaneously. CSPO certified. "
            "Pune-based, immediate joiner."
        ),
        "skills": (
            "**0-to-1 Building:** End-to-end product ownership, Rapid prototyping, Customer discovery, MVP design, Async writing\n"
            "**Code:** Python (intermediate), FastAPI, SQL/PostgreSQL, Git/GitHub, Render/Vercel deploy\n"
            "**AI:** Gemini/OpenAI/Anthropic APIs (familiar), Prompt engineering, RAG basics, Agent design\n"
            "**Product:** PRDs, Sprint planning, Cross-functional delivery, Customer-discovery interviews\n"
            "**Domain:** B2B SaaS, MarTech, Customer Engagement, AI-product"
        ),
    },
    "solutions-engineer": {
        "summary": (
            "Customer-facing technical product professional with 2+ years at D·engage (B2B marketing "
            "automation, enterprise clients in banking, retail, telecom). Lived at the intersection of "
            "customer needs, engineering capacity, and AI capabilities — translated customer pain into "
            "product specs, partnered with engineering on AI feature design, supported customer integration "
            "and onboarding. Targeting Solutions Engineer / Customer Engineer / Implementation Engineer "
            "(AI) roles at AI-native vendors where I scope customer integrations and deploy AI into real "
            "enterprise workflows."
        ),
        "skills": (
            "**Customer-Facing:** Customer discovery, Technical demos, Pre-sales support, Integration scoping, Onboarding, Training\n"
            "**AI Product:** LLM feature understanding, Prompt design, Evaluation basics, Gemini/OpenAI APIs\n"
            "**Code:** Python (intermediate), FastAPI, SQL, REST API integration, basic Postman/curl\n"
            "**Product:** PRDs, Backlog grooming, Cross-functional delivery, Customer success collaboration\n"
            "**Domain:** B2B SaaS, MarTech, Customer Engagement, Enterprise (Banking/Retail/Telecom)"
        ),
    },
    "product-engineer": {
        "summary": (
            "Product Engineer — full-stack builder who owns features end-to-end. 2+ years at D·engage as "
            "Product Owner (B2B SaaS, AI-powered engagement features for enterprise). Code on weekends — "
            "built personal AI-powered job tracker in Python/FastAPI/Postgres with Gemini integration, "
            "deployed on Render, currently in daily use (github.com/AjinkyaKate/job-tracker). Comfortable "
            "blurring PM / eng line. Targeting Product Engineer roles (Linear / Vercel / Statsig style) where "
            "craft + autonomy matter more than narrow specialization."
        ),
        "skills": (
            "**Code:** Python (intermediate), FastAPI, SQL/PostgreSQL, Git/GitHub, Render/Vercel deploy, REST APIs, basic Jinja2 templates\n"
            "**AI APIs:** Gemini, OpenAI, Anthropic Claude (via personal projects)\n"
            "**Product:** PRDs, Sprint planning, Cross-functional delivery, Customer discovery\n"
            "**Build Style:** Ship-fast / iterate-fast, Async writing, Direct user-feedback loops\n"
            "**Domain:** B2B SaaS, MarTech, AI-product, Customer Engagement"
        ),
    },
    "business-analyst": {
        "summary": (
            "Business / Product Analyst with 2+ years across product and analytics roles. At D·engage as "
            "Product Owner: drove product discovery, A/B test analysis, funnel deep-dives, requirements "
            "writing. At Denner.in: Product Analyst owning competitive research + analytics dashboards. "
            "CSPO certified. Open to BA / Product Analyst roles in B2B SaaS, Pune-local or remote."
        ),
        "skills": (
            "**Analytics:** SQL, A/B testing, Funnel analysis, Cohort analysis, Amplitude, Mixpanel\n"
            "**Requirements:** User stories, Acceptance criteria, PRDs, Process flows, BPMN basics\n"
            "**Tools:** Jira, Notion, Confluence, Figma\n"
            "**Domain:** B2B SaaS, MarTech, Customer Engagement, Enterprise (Banking/Retail/Telecom)"
        ),
    },
}


def render_role_resume(family: str) -> str:
    """Compose the full markdown resume for the given role family.

    Returns empty string if family unknown.
    """
    config = ROLE_RESUMES.get(family)
    if not config:
        return ""
    return "\n".join([
        HEADER,
        "## Summary",
        config["summary"],
        "",
        EXPERIENCE,
        PROJECTS,
        "## Skills",
        config["skills"],
        "",
        EDUCATION,
        CERTIFICATIONS,
    ])


# Map chip key → role-family slug (used by /leads chips for download link)
CHIP_TO_RESUME_FAMILY = {
    "po": "product-owner",
    "pm": "pm-apm",
    "apm": "pm-apm",
    "spm": "pm-apm",  # senior PM uses pm-apm resume with the same forward-leaning summary
    "ai-pm": "ai-product-manager",
    "fd": "forward-deployed",
    "ai-eng": "ai-product-manager",
    "founding": "founding",
    "sol-eng": "solutions-engineer",
    "prod-eng": "product-engineer",
    "ba": "business-analyst",
}

# Human-readable labels for the download button (per family)
FAMILY_LABELS = {
    "product-owner": "Product Owner",
    "pm-apm": "Product Manager / APM",
    "ai-product-manager": "AI Product Manager",
    "forward-deployed": "Forward Deployed (PM / Engineer / AI)",
    "founding": "Founding Engineer / PM",
    "solutions-engineer": "Solutions / Customer / Implementation Engineer",
    "product-engineer": "Product Engineer",
    "business-analyst": "Business Analyst",
}
