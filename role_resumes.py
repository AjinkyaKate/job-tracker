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
    "senior-pm": {
        "summary": (
            "Senior Product Manager candidate with 2+ years owning B2B SaaS product delivery at D·engage — "
            "discovery, PRDs, sprint cadence, AI feature shipping for enterprise customers in banking, "
            "retail, telecom. Ready to step up to Senior PM scope: own a product area end-to-end, mentor "
            "APMs, lead multi-team initiatives, set quarterly OKRs. CSPO certified. Targeting Senior PM "
            "seats at B2B SaaS, MarTech, or AI-product companies."
        ),
        "skills": (
            "**Product Leadership:** Product strategy, Multi-team coordination, Roadmap ownership, OKR-setting, Stakeholder alignment, Mentoring junior PMs\n"
            "**Delivery:** PRDs, Sprint cadence, Backlog management, Release management, Cross-functional delivery\n"
            "**AI Product:** LLM feature design, Prompt engineering, Evaluation, AI roadmap planning\n"
            "**Data:** SQL, A/B testing, Funnel analysis, Cohort analysis, Amplitude, Mixpanel\n"
            "**Tools:** Jira, Notion, Figma, Confluence, Miro\n"
            "**Domain:** B2B SaaS, MarTech, Customer Engagement, Enterprise (Banking/Retail/Telecom)"
        ),
    },
    "technical-pm": {
        "summary": (
            "Technical Product Manager — PM with hands-on code comfort. 2+ years at D·engage as Product "
            "Owner shipping B2B SaaS marketing automation + AI-powered features for enterprise customers. "
            "Code on weekends: built personal AI job-tracker in Python/FastAPI/Postgres with Gemini email "
            "classification, deployed on Render, in daily use (github.com/AjinkyaKate/job-tracker). "
            "Comfortable in eng standups, reading PRs, scoping integrations, debating architectural "
            "trade-offs. Targeting Technical PM / TPM / Platform PM roles where the PM owns technical "
            "decisions alongside engineering."
        ),
        "skills": (
            "**Technical PM:** API design reviews, Architecture trade-offs, Integration scoping, Engineering effort estimation, Technical PRDs\n"
            "**Code:** Python (intermediate), FastAPI, SQL/PostgreSQL, REST APIs, Git/GitHub, basic Jinja2/HTMX\n"
            "**AI APIs:** Gemini, OpenAI, Anthropic Claude (familiar via personal projects)\n"
            "**Product:** Roadmap planning, Cross-functional delivery, Customer discovery, PRDs, Backlog management\n"
            "**Tools:** Jira, Notion, Figma, Postman, GitHub, GitHub Actions\n"
            "**Domain:** B2B SaaS, MarTech, AI-product, Customer Engagement, Enterprise SaaS"
        ),
    },
    "forward-deployed-engineer": {
        "summary": (
            "Forward-Deployed Engineer candidate — code-leaning generalist who lives with enterprise "
            "customers and ships integrations end-to-end. 2+ years at D·engage on the product side "
            "(B2B SaaS, AI marketing automation for enterprise clients in banking, retail, telecom) gave "
            "me deep instinct for customer pain → product fit. Personal projects in production: AI "
            "job-tracker (FastAPI + Postgres + Gemini, deployed on Render, in daily use) and AI QA agent. "
            "Targeting Forward Deployed Engineer roles at AI-native vendors where I own 2-3 enterprise "
            "accounts end-to-end and ship code alongside the customer."
        ),
        "skills": (
            "**Customer-Embedded Eng:** Enterprise integration scoping, Customer-pain → code translation, On-site iteration cycles, Customer training, Adoption tracking\n"
            "**Code:** Python (intermediate), FastAPI, SQL/PostgreSQL, Git/GitHub, REST APIs, Render/Vercel deploy, basic Jinja2/HTMX/Tailwind\n"
            "**AI APIs:** Gemini, OpenAI, Anthropic Claude (via personal projects), Prompt design, RAG basics\n"
            "**Product Instinct:** Customer discovery, PRDs, Roadmap reasoning, Cross-functional delivery (from D·engage Product Owner role)\n"
            "**Domain:** B2B SaaS, MarTech, Customer Engagement, Enterprise (Banking/Retail/Telecom)"
        ),
    },
    "founding-engineer": {
        "summary": (
            "Founding Engineer candidate at AI-native seed / Series-A startups. 2+ years on the product "
            "side at D·engage (B2B SaaS, enterprise customer engagement, AI feature shipping). Side-project "
            "track record: built personal AI job-tracker solo (FastAPI + PostgreSQL + Gemini email "
            "classification + GitHub Actions cron, deployed on Render, currently in daily use — "
            "github.com/AjinkyaKate/job-tracker), and AI QA agent for ticket-driven test automation. "
            "Wear engineer + PM + customer-success hats simultaneously. CSPO certified. Pune-based, "
            "immediate joiner."
        ),
        "skills": (
            "**0-to-1 Engineering:** Solo full-stack builds, Rapid prototyping, MVP design, Production deploys, Owning the whole stack, Async writing\n"
            "**Code:** Python (intermediate, growing), FastAPI, SQL/PostgreSQL, Git/GitHub, Render/Vercel, REST APIs, Jinja2/HTMX/Tailwind\n"
            "**AI:** Gemini, OpenAI, Anthropic Claude APIs (familiar), Prompt engineering, RAG basics, Agent loops\n"
            "**Product:** Customer discovery, PRDs (when needed), MVP scoping, Cross-functional delivery\n"
            "**Domain:** B2B SaaS, MarTech, AI-product"
        ),
    },
    "customer-engineer": {
        "summary": (
            "Customer Engineer with 2+ years at the intersection of B2B SaaS product and enterprise "
            "customer support. At D·engage owned product delivery for cross-functional team serving "
            "enterprise clients in banking, retail, telecom — discovery, customization scoping, AI feature "
            "design, customer onboarding & training, escalation triage. Comfortable reading code, scoping "
            "integrations, debugging API issues. Targeting Customer Engineer / Customer Success Engineer "
            "/ Technical Customer Manager roles at AI-native B2B vendors where I own a portfolio of "
            "enterprise accounts post-sale."
        ),
        "skills": (
            "**Customer Eng:** Enterprise customer onboarding, Integration support, Escalation triage, Customer success collaboration, Training delivery, Health monitoring\n"
            "**Code:** Python (intermediate), SQL/PostgreSQL, REST APIs, Postman/curl, basic JS, Git/GitHub\n"
            "**AI APIs:** Gemini, OpenAI, Anthropic Claude (via personal projects)\n"
            "**Product:** PRDs, Roadmap input, Cross-functional delivery, Customer discovery\n"
            "**Domain:** B2B SaaS, MarTech, Customer Engagement, Enterprise (Banking/Retail/Telecom)"
        ),
    },
    "implementation-consultant": {
        "summary": (
            "Implementation Consultant / Engineer with 2+ years at D·engage owning the product side of "
            "enterprise B2B SaaS deployment — requirements gathering, customization scoping, AI feature "
            "configuration, onboarding & training, success monitoring. Worked with enterprise customers in "
            "banking, retail, telecom — translating business needs into product configurations and tracking "
            "adoption. CSPO certified. Targeting Implementation Consultant / Implementation Engineer roles "
            "at B2B SaaS / AI-product vendors selling to enterprise customers."
        ),
        "skills": (
            "**Implementation:** Requirements gathering, Customer customization, Project management, Configuration design, Onboarding & training, Adoption monitoring\n"
            "**Technical:** Python (intermediate), SQL, REST APIs, Postman, basic data mapping, ETL concepts\n"
            "**Product:** PRDs, User stories, Acceptance criteria, Stakeholder management, Cross-functional delivery\n"
            "**AI:** LLM feature configuration, Prompt design, Evaluation basics (Gemini/OpenAI familiar)\n"
            "**Domain:** B2B SaaS, MarTech, Customer Engagement, Enterprise (Banking/Retail/Telecom)"
        ),
    },
    "applied-ai-engineer": {
        "summary": (
            "Applied AI Engineer — PM-engineer hybrid focused on shipping LLM-powered features into "
            "production. 2+ years at D·engage shipping AI-powered marketing engagement features "
            "(LLM-assisted content generation, smart segmentation, personalization journeys) — partnering "
            "with engineering on model selection, prompt design, and evaluation. Personal AI projects in "
            "production: job-tracker using Gemini for email classification (deployed on Render, in daily "
            "use) and AI QA agent for ticket-native testing. Strong product instinct combined with "
            "fast-iterating engineering. Targeting Applied AI Engineer / AI Engineer (Product-leaning) / "
            "GenAI Engineer roles at AI-native B2B SaaS."
        ),
        "skills": (
            "**AI Engineering:** LLM API integration (Gemini, OpenAI, Anthropic), Prompt engineering, RAG basics, Evaluation pipelines, AI agent design\n"
            "**Code:** Python (intermediate, growing), FastAPI, SQL/PostgreSQL, Git/GitHub, REST APIs, Render/Vercel deploy\n"
            "**Product Sensibility:** Customer-pain → AI-feature scoping, MVP-first thinking, Evaluation-driven iteration, Async writing\n"
            "**AI Domain:** LLM features in B2B SaaS, MarTech AI, Customer Engagement AI, Enterprise AI deployment\n"
            "**Build Style:** Ship fast, measure, iterate. Side-project track: github.com/AjinkyaKate"
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

def detect_family_from_title(title: str) -> str:
    """Map a free-text job title to the most-relevant resume family (1 of 15).

    Order matters — match the MOST SPECIFIC patterns first so e.g.
    'Senior Technical Product Manager' routes to technical-pm (not senior-pm
    or generic pm-apm), and 'AI Product Manager' beats 'Product Manager'.
    Default falls back to pm-apm (generic Product Manager) since that's the
    broadest match for unknown titles.
    """
    if not title:
        return "pm-apm"
    t = title.lower()

    # ── AI / ML cluster — match BEFORE plain product manager ────────────────
    if any(kw in t for kw in ("ai product manager", "ai pm", "genai pm",
                              "gen ai pm", "gen-ai pm", "ml pm",
                              "machine learning pm",
                              "machine learning product",
                              "applied ai pm", "applied-ai pm")):
        return "ai-product-manager"
    if any(kw in t for kw in ("applied ai engineer", "applied-ai engineer",
                              "ai engineer", "genai engineer", "gen ai engineer",
                              "ml engineer (product", "llm engineer",
                              "ai/ml engineer")):
        return "applied-ai-engineer"

    # ── Founding cluster — engineer vs PM split ─────────────────────────────
    if "founding" in t and any(kw in t for kw in ("engineer", "developer", "dev")):
        return "founding-engineer"
    if "founding" in t:
        return "founding"  # founding pm / founding member / founding (generic)

    # ── Forward Deployed cluster — engineer vs PM split ─────────────────────
    if any(kw in t for kw in ("forward deployed engineer", "forward-deployed engineer",
                              "deployed engineer", "fde")):
        return "forward-deployed-engineer"
    if any(kw in t for kw in ("forward deployed", "forward-deployed", "deployed pm",
                              "deployed product manager")):
        return "forward-deployed"

    # ── Customer-side technical roles ──────────────────────────────────────
    if any(kw in t for kw in ("customer engineer", "customer success engineer",
                              "technical customer manager", "customer engineering")):
        return "customer-engineer"
    if any(kw in t for kw in ("implementation consultant", "implementation engineer",
                              "implementation specialist", "deployment consultant",
                              "professional services engineer")):
        return "implementation-consultant"
    if any(kw in t for kw in ("solutions engineer", "solution engineer",
                              "solutions architect", "solution architect",
                              "sales engineer", "pre-sales engineer", "presales engineer")):
        return "solutions-engineer"

    # ── Product engineer (full-stack-leaning IC track) ──────────────────────
    if "product engineer" in t:
        return "product-engineer"

    # ── Business / Systems Analyst ──────────────────────────────────────────
    if any(kw in t for kw in ("business analyst", "business systems analyst",
                              "systems analyst", "bsa", "data analyst (product")):
        return "business-analyst"

    # ── Product Owner cluster ───────────────────────────────────────────────
    if any(kw in t for kw in ("product owner", "scrum product owner",
                              "agile product owner", " po ", " po,")):
        return "product-owner"

    # ── Technical PM / TPM (must come BEFORE senior PM since "Senior
    # Technical PM" should route to technical-pm, not senior-pm) ────────────
    if any(kw in t for kw in ("technical product manager", "technical pm", "tpm",
                              "platform product manager", "platform pm",
                              "infrastructure pm")):
        return "technical-pm"

    # ── Senior PM cluster ───────────────────────────────────────────────────
    if any(kw in t for kw in ("senior product manager", "sr. product manager",
                              "sr product manager", "lead product manager",
                              "principal product manager", "staff product manager",
                              "group product manager", "head of product",
                              "director of product", "senior pm", "sr pm",
                              "lead pm", "principal pm")):
        return "senior-pm"

    # ── Generic PM / APM cluster — broad fallback ───────────────────────────
    if any(kw in t for kw in ("product manager", "associate product manager",
                              "junior product manager", "apm")):
        return "pm-apm"
    if t == "pm" or t.endswith(" pm") or t.startswith("pm "):
        return "pm-apm"

    return "pm-apm"


# Human-readable labels for the download button (per family).
# These also become the PDF filename slug — keep them short, no slashes,
# no parens. Stable across sessions so the user downloads each file once
# and reuses (no duplicate-on-disk problem).
FAMILY_LABELS = {
    "product-owner":             "Product Owner",
    "pm-apm":                    "Product Manager",
    "senior-pm":                 "Senior Product Manager",
    "technical-pm":              "Technical Product Manager",
    "ai-product-manager":        "AI Product Manager",
    "forward-deployed":          "Forward Deployed PM",
    "forward-deployed-engineer": "Forward Deployed Engineer",
    "founding":                  "Founding PM",
    "founding-engineer":         "Founding Engineer",
    "solutions-engineer":        "Solutions Engineer",
    "customer-engineer":         "Customer Engineer",
    "implementation-consultant": "Implementation Consultant",
    "product-engineer":          "Product Engineer",
    "applied-ai-engineer":       "Applied AI Engineer",
    "business-analyst":          "Business Analyst",
}
