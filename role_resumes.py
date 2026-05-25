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

[+91 77588 80580](tel:+917758880580) · [ajinkyakate2001@gmail.com](mailto:ajinkyakate2001@gmail.com) · [LinkedIn](https://linkedin.com/in/ajinkya-kate) · [GitHub](https://github.com/AjinkyaKate)

Pune District, Maharashtra · Available immediately · CSPO Certified
"""

EXPERIENCE = """## Experience

**Product Owner, D·engage** (Jan 2025 - May 2026, remote from Pune)

Marketing-automation SaaS for enterprise customers in banking, retail, and telecom.

- Talked to customers, watched competitors, built quick prototypes. Wrote PRDs based on what I learned and picked what to build next sprint.
- Shipped 3 AI features: LLM-generated email content, smart audience segmentation, personalization rules. Compared Gemini and OpenAI with engineers, wrote evaluation criteria, tested edge cases.
- Ran 2-week sprints. Made calls on new build vs tech debt vs production support based on what was hurting customers most.
- Took customer feedback from CSM and Implementation teams, turned it into roadmap items. Separated churn-causing problems from nice-to-haves.
- Built prototypes with no-code tools and AI-assisted code to test ideas before engineering invested.

**Product Analyst, Denner.in** (May 2024 - Dec 2024, hybrid in Pune)

- Owned product analytics and competitive research for the PM team. Ran A/B tests, funnel deep-dives, user research syntheses.
"""

PROJECTS = """## Projects

**Personal Job Tracker** (May 2026 - ongoing)
[github.com/AjinkyaKate/job-tracker](https://github.com/AjinkyaKate/job-tracker)

- Built this during my current job search. FastAPI, PostgreSQL, Gemini for email classification, deployed on Render with a GitHub Actions cron.
- Pulls LinkedIn job-alert emails into a leads inbox with filters. Generates 15 role-tailored resumes. Auto-advances job status as Gmail picks up applied / interview / offer signals. Drafts LinkedIn DMs to recruiters.
- I use this daily. 100+ leads ingested so far.

**AI QA Agent** (2026, in progress)
[github.com/AjinkyaKate/qa-agent](https://github.com/AjinkyaKate/qa-agent)

- Small AI agent that reads a ticket's acceptance criteria, browses the app being tested, checks UI and API behavior, attaches results back to the ticket.
- Inspired by the manual QA loop I watched at D·engage. Using my own job-tracker as the test target for v0.
"""

EDUCATION = """## Education

**Savitribai Phule Pune University**, Bachelor of Business Administration (BBA), Pune
"""

CERTIFICATIONS = """## Certifications

**Certified Scrum Product Owner (CSPO)**, Scrum Alliance, Nov 2025
"""


# ─── Per-role Summary + Skills ──────────────────────────────────────────────

ROLE_RESUMES = {
    "product-owner": {
        "summary": (
            "Product Owner with 2+ years building B2B SaaS. Did discovery, wrote PRDs, ran sprints, "
            "shipped features, measured what worked. Most recently at D·engage shipping marketing "
            "automation and AI-powered engagement features for enterprise customers in banking, retail, "
            "and telecom. CSPO certified. Open to Product Owner roles in B2B SaaS, Pune-local, immediate "
            "joiner."
        ),
        "skills": (
            "Agile and Scrum, backlog grooming, sprint planning, PRDs, user stories, stakeholder "
            "management. Jira, Notion, Confluence, Figma, Miro. SQL (basic), Amplitude, Mixpanel, "
            "A/B testing. Worked in MarTech, customer engagement platforms, and enterprise SaaS "
            "(banking, retail, telecom)."
        ),
    },
    "pm-apm": {
        "summary": (
            "PM with 2+ years owning B2B SaaS product delivery. At D·engage shipped marketing-automation "
            "and AI-powered engagement features for enterprise customers in banking, retail, and telecom. "
            "CSPO certified. Open to APM, PM, or Senior PM seats in customer engagement, MarTech, or "
            "AI-product SaaS."
        ),
        "skills": (
            "Product discovery, PRDs, roadmap planning, cross-functional delivery, OKRs. Scrum, backlog "
            "management, sprint planning, release management. Jira, Notion, Figma, Amplitude, Mixpanel, "
            "SQL. Worked in B2B SaaS, MarTech, customer engagement, enterprise SaaS (banking, retail, "
            "telecom)."
        ),
    },
    "ai-product-manager": {
        "summary": (
            "PM with 2+ years shipping AI features in production B2B SaaS. At D·engage built LLM-powered "
            "engagement journeys, content generation, and smart segmentation. Worked closely with "
            "engineers on which models to use, how to write prompts, and how to evaluate output. Building "
            "AI side projects too: a Gemini-based email classifier and an AI QA agent. Looking for AI "
            "Product Manager or Applied AI Product roles at AI-first B2B SaaS."
        ),
        "skills": (
            "LLM feature design, prompt engineering, RAG basics, eval writing. PRDs, discovery, sprint "
            "planning, cross-functional delivery. SQL, A/B testing, funnel and cohort analysis, "
            "Amplitude, Mixpanel. Python (intermediate), FastAPI, PostgreSQL, Git/GitHub, Render. Worked "
            "with Gemini, OpenAI, and Anthropic Claude APIs through side projects."
        ),
    },
    "forward-deployed": {
        "summary": (
            "Forward-Deployed Product builder with 2+ years owning enterprise B2B SaaS outcomes "
            "end-to-end. At D·engage worked with enterprise customers in banking, retail, and telecom: "
            "discovery, customization, AI features, training, retention. Active code-side builder too. "
            "Shipped a personal AI job tracker (FastAPI, PostgreSQL, Gemini, deployed) and an AI QA "
            "agent. Looking for Forward Deployed Engineer, Forward Deployed PM, or Customer Engineer "
            "(AI) roles where I own a few enterprise accounts and ship code alongside customers."
        ),
        "skills": (
            "Enterprise customer discovery, pain-point synthesis, integration scoping, onboarding and "
            "training, health monitoring. LLM feature shipping, prompt design, RAG basics, eval, Gemini "
            "and OpenAI APIs. Python (intermediate), FastAPI, SQL/PostgreSQL, Git/GitHub, REST API "
            "integration. PRDs, backlog management, sprint planning, cross-functional delivery. B2B "
            "SaaS, MarTech, customer engagement, enterprise (banking, retail, telecom)."
        ),
    },
    "founding": {
        "summary": (
            "Builder-PM exploring Founding PM seats at AI-native seed and Series-A startups. 2+ years "
            "shipping B2B SaaS at D·engage (customer engagement and MarTech for enterprise customers). "
            "On the side, shipped AI projects in production: personal job-search tracker (FastAPI, "
            "PostgreSQL, Gemini email classification, deployed on Render, in daily use) and a "
            "ticket-native AI QA agent. Comfortable wearing PM, engineer, and customer-success hats "
            "together. CSPO certified. Pune-based, immediate joiner."
        ),
        "skills": (
            "End-to-end product ownership, rapid prototyping, customer discovery, MVP design, async "
            "writing. Python (intermediate), FastAPI, SQL/PostgreSQL, Git/GitHub, Render and Vercel "
            "deploys. Gemini, OpenAI, Anthropic Claude APIs (familiar), prompt engineering, RAG basics, "
            "agent design. PRDs, sprint planning, cross-functional delivery, customer-discovery "
            "interviews. B2B SaaS, MarTech, customer engagement, AI-product."
        ),
    },
    "solutions-engineer": {
        "summary": (
            "Customer-facing technical product professional with 2+ years at D·engage (B2B marketing "
            "automation for enterprise clients in banking, retail, and telecom). Lived at the "
            "intersection of customer needs, engineering capacity, and AI capabilities. Translated "
            "customer pain into product specs, partnered with engineering on AI feature design, supported "
            "customer integration and onboarding. Looking for Solutions Engineer, Customer Engineer, or "
            "Implementation Engineer roles at AI-native vendors where I scope customer integrations and "
            "deploy AI into real enterprise workflows."
        ),
        "skills": (
            "Customer discovery, technical demos, pre-sales support, integration scoping, onboarding, "
            "training. LLM feature understanding, prompt design, eval basics, Gemini and OpenAI APIs. "
            "Python (intermediate), FastAPI, SQL, REST API integration, Postman and curl. PRDs, backlog "
            "grooming, cross-functional delivery, customer success collaboration. B2B SaaS, MarTech, "
            "customer engagement, enterprise (banking, retail, telecom)."
        ),
    },
    "product-engineer": {
        "summary": (
            "Product Engineer who owns features end-to-end. 2+ years at D·engage as Product Owner "
            "shipping B2B SaaS AI-powered engagement features for enterprise customers. Code on "
            "weekends: built a personal AI job tracker in Python, FastAPI, and PostgreSQL with Gemini "
            "integration, deployed on Render, currently in daily use "
            "(github.com/AjinkyaKate/job-tracker). Comfortable blurring the PM-eng line. Looking for "
            "Product Engineer roles (Linear, Vercel, Statsig style) where craft and autonomy matter more "
            "than narrow specialization."
        ),
        "skills": (
            "Python (intermediate), FastAPI, SQL/PostgreSQL, Git/GitHub, Render and Vercel deploys, "
            "REST APIs, basic Jinja2. Worked with Gemini, OpenAI, and Anthropic Claude APIs through side "
            "projects. PRDs, sprint planning, cross-functional delivery, customer discovery. Ship-fast "
            "and iterate-fast style, async writing, direct user-feedback loops. B2B SaaS, MarTech, "
            "AI-product, customer engagement."
        ),
    },
    "business-analyst": {
        "summary": (
            "Business and Product Analyst with 2+ years across product and analytics roles. At D·engage "
            "as Product Owner: drove product discovery, A/B test analysis, funnel deep-dives, "
            "requirements writing. At Denner.in as Product Analyst: owned competitive research and "
            "analytics dashboards. CSPO certified. Open to BA or Product Analyst roles in B2B SaaS, "
            "Pune-local or remote."
        ),
        "skills": (
            "SQL, A/B testing, funnel analysis, cohort analysis, Amplitude, Mixpanel. User stories, "
            "acceptance criteria, PRDs, process flows, BPMN basics. Jira, Notion, Confluence, Figma. "
            "B2B SaaS, MarTech, customer engagement, enterprise (banking, retail, telecom)."
        ),
    },
    "senior-pm": {
        "summary": (
            "Senior Product Manager candidate with 2+ years owning B2B SaaS product delivery at D·engage. "
            "Did discovery, wrote PRDs, ran sprints, shipped AI features for enterprise customers in "
            "banking, retail, and telecom. Ready to step up to Senior PM scope: own a product area "
            "end-to-end, mentor APMs, lead multi-team initiatives, set quarterly OKRs. CSPO certified. "
            "Looking for Senior PM seats at B2B SaaS, MarTech, or AI-product companies."
        ),
        "skills": (
            "Product strategy, multi-team coordination, roadmap ownership, OKR-setting, stakeholder "
            "alignment, mentoring junior PMs. PRDs, sprint cadence, backlog management, release "
            "management, cross-functional delivery. LLM feature design, prompt engineering, eval, AI "
            "roadmap planning. SQL, A/B testing, funnel and cohort analysis, Amplitude, Mixpanel. Jira, "
            "Notion, Figma, Confluence, Miro. B2B SaaS, MarTech, customer engagement, enterprise "
            "(banking, retail, telecom)."
        ),
    },
    "technical-pm": {
        "summary": (
            "Technical Product Manager. PM with hands-on code comfort. 2+ years at D·engage as Product "
            "Owner shipping B2B SaaS marketing automation and AI-powered features for enterprise "
            "customers. Code on weekends: built a personal AI job tracker in Python, FastAPI, and "
            "PostgreSQL with Gemini email classification, deployed on Render, in daily use "
            "(github.com/AjinkyaKate/job-tracker). Comfortable in eng standups, reading PRs, scoping "
            "integrations, debating architectural trade-offs. Looking for Technical PM, TPM, or "
            "Platform PM roles where the PM owns technical decisions alongside engineering."
        ),
        "skills": (
            "API design reviews, architecture trade-offs, integration scoping, engineering effort "
            "estimation, technical PRDs. Python (intermediate), FastAPI, SQL/PostgreSQL, REST APIs, "
            "Git/GitHub, basic Jinja2 and HTMX. Worked with Gemini, OpenAI, and Anthropic Claude APIs "
            "through side projects. Roadmap planning, cross-functional delivery, customer discovery, "
            "PRDs, backlog management. Jira, Notion, Figma, Postman, GitHub, GitHub Actions. B2B SaaS, "
            "MarTech, AI-product, customer engagement, enterprise SaaS."
        ),
    },
    "forward-deployed-engineer": {
        "summary": (
            "Forward-Deployed Engineer candidate. Code-leaning generalist who lives with enterprise "
            "customers and ships integrations end-to-end. 2+ years at D·engage on the product side "
            "(B2B SaaS, AI marketing automation for enterprise clients in banking, retail, and telecom) "
            "built strong customer-pain to product-fit instincts. Personal projects in production: AI "
            "job tracker (FastAPI, PostgreSQL, Gemini, deployed on Render, in daily use) and AI QA agent. "
            "Looking for Forward Deployed Engineer roles at AI-native vendors where I own 2 to 3 "
            "enterprise accounts and ship code alongside the customer."
        ),
        "skills": (
            "Enterprise integration scoping, customer-pain to code translation, on-site iteration "
            "cycles, customer training, adoption tracking. Python (intermediate), FastAPI, "
            "SQL/PostgreSQL, Git/GitHub, REST APIs, Render and Vercel deploys, basic Jinja2 and Tailwind. "
            "Gemini, OpenAI, Anthropic Claude APIs (via personal projects), prompt design, RAG basics. "
            "Customer discovery, PRDs, roadmap reasoning, cross-functional delivery (from D·engage "
            "Product Owner role). B2B SaaS, MarTech, customer engagement, enterprise (banking, retail, "
            "telecom)."
        ),
    },
    "founding-engineer": {
        "summary": (
            "Founding Engineer candidate at AI-native seed or Series-A startups. 2+ years on the product "
            "side at D·engage (B2B SaaS, enterprise customer engagement, AI feature shipping). "
            "Side-project track: built a personal AI job tracker solo (FastAPI, PostgreSQL, Gemini email "
            "classification, GitHub Actions cron, deployed on Render, in daily use at "
            "github.com/AjinkyaKate/job-tracker), plus an AI QA agent in progress. Wear engineer, PM, "
            "and customer-success hats simultaneously. CSPO certified. Pune-based, immediate joiner."
        ),
        "skills": (
            "Solo full-stack builds, rapid prototyping, MVP design, production deploys, owning the whole "
            "stack, async writing. Python (intermediate), FastAPI, SQL/PostgreSQL, Git/GitHub, Render, "
            "Vercel, REST APIs, Jinja2, HTMX, Tailwind. Gemini, OpenAI, Anthropic Claude APIs "
            "(familiar), prompt engineering, RAG basics, agent loops. Customer discovery, PRDs when "
            "needed, MVP scoping, cross-functional delivery. B2B SaaS, MarTech, AI-product."
        ),
    },
    "customer-engineer": {
        "summary": (
            "Customer Engineer with 2+ years at the intersection of B2B SaaS product and enterprise "
            "customer support. At D·engage owned product delivery for cross-functional team serving "
            "enterprise clients in banking, retail, and telecom: discovery, customization scoping, AI "
            "feature design, customer onboarding, training, escalation triage. Comfortable reading code, "
            "scoping integrations, debugging API issues. Looking for Customer Engineer, Customer Success "
            "Engineer, or Technical Customer Manager roles at AI-native B2B vendors."
        ),
        "skills": (
            "Enterprise customer onboarding, integration support, escalation triage, customer success "
            "collaboration, training delivery, health monitoring. Python (intermediate), SQL/PostgreSQL, "
            "REST APIs, Postman and curl, basic JS, Git/GitHub. Gemini, OpenAI, Anthropic Claude APIs "
            "(via personal projects). PRDs, roadmap input, cross-functional delivery, customer "
            "discovery. B2B SaaS, MarTech, customer engagement, enterprise (banking, retail, telecom)."
        ),
    },
    "implementation-consultant": {
        "summary": (
            "Implementation Consultant or Engineer with 2+ years at D·engage owning the product side of "
            "enterprise B2B SaaS deployment. Did requirements gathering, customization scoping, AI "
            "feature configuration, onboarding and training, success monitoring. Worked with enterprise "
            "customers in banking, retail, and telecom. Translated business needs into product "
            "configurations and tracked adoption. CSPO certified. Looking for Implementation Consultant "
            "or Engineer roles at B2B SaaS or AI-product vendors selling to enterprise."
        ),
        "skills": (
            "Requirements gathering, customer customization, project management, configuration design, "
            "onboarding and training, adoption monitoring. Python (intermediate), SQL, REST APIs, "
            "Postman, basic data mapping, ETL concepts. PRDs, user stories, acceptance criteria, "
            "stakeholder management, cross-functional delivery. LLM feature configuration, prompt design, "
            "eval basics (Gemini and OpenAI familiar). B2B SaaS, MarTech, customer engagement, "
            "enterprise (banking, retail, telecom)."
        ),
    },
    "applied-ai-engineer": {
        "summary": (
            "Applied AI Engineer. PM-engineer hybrid focused on shipping LLM-powered features into "
            "production. 2+ years at D·engage shipping AI-powered marketing engagement features "
            "(LLM-assisted content generation, smart segmentation, personalization journeys). Partnered "
            "with engineering on model selection, prompt design, and evaluation. Personal AI projects in "
            "production: job tracker using Gemini for email classification (deployed on Render, in daily "
            "use) and an AI QA agent for ticket-native testing. Looking for Applied AI Engineer, AI "
            "Engineer (Product-leaning), or GenAI Engineer roles at AI-native B2B SaaS."
        ),
        "skills": (
            "LLM API integration (Gemini, OpenAI, Anthropic), prompt engineering, RAG basics, "
            "evaluation pipelines, AI agent design. Python (intermediate, growing), FastAPI, "
            "SQL/PostgreSQL, Git/GitHub, REST APIs, Render and Vercel deploys. Customer-pain to "
            "AI-feature scoping, MVP-first thinking, evaluation-driven iteration, async writing. LLM "
            "features in B2B SaaS, MarTech AI, customer engagement AI, enterprise AI deployment. Ship "
            "fast, measure, iterate. Side-project track at github.com/AjinkyaKate."
        ),
    },
}


# ─── Standalone resume: Digital Operations Coordinator ──────────────────────
# Different from the 15 PM-track families. This one is for ops/coordinator
# roles that emphasize AI-tooling usage, CRM daily-driving, and process
# automation. The Experience section is reframed away from PM language and
# toward operations + AI-workflow building. Used for Skerion and any future
# similar Digital Operations / Logistics Coordinator / Ops Associate roles.

DIGITAL_OPS_RESUME = """# Ajinkya Kate

[+91 77588 80580](tel:+917758880580) · [ajinkyakate2001@gmail.com](mailto:ajinkyakate2001@gmail.com) · [LinkedIn](https://linkedin.com/in/ajinkya-kate) · [GitHub](https://github.com/AjinkyaKate)

Pune District, Maharashtra · Available immediately · CSPO Certified


## Summary

Operations-minded professional who lives in digital tools and uses AI to make repetitive work disappear. 2+ years running cross-functional work at D·engage (B2B SaaS customer engagement platform) with hands-on CRM, dashboard, and coordination work daily. Active builder of personal AI workflows: I built my own job-search CRM using Python, FastAPI, PostgreSQL, and the Gemini API for email classification. It is in daily use. Looking for Digital Operations and Coordinator roles where AI-fluency and process-improvement instinct matter, with a path toward Product Operations over time.


## Experience

**Cross-functional Product Owner, D·engage** (Jan 2025 - May 2026, remote from Pune)

B2B SaaS customer engagement platform. The role spanned product, customer success coordination, and cross-team operations for enterprise customers in banking, retail, and telecom.

- Worked inside the platform's CRM and dashboards every day. Tracked customer activity, campaign performance, integration status, support escalations. Kept records clean so the team and customers could trust the numbers.
- Used AI tools (ChatGPT, Claude, Gemini) daily to draft customer communications, summarise customer feedback, generate evaluation reports, and automate repetitive analysis. Cut my weekly customer-feedback-synthesis time by about 60% by replacing manual summarisation with AI-assisted reports.
- Coordinated across engineering, design, QA, customer success, implementation, and sales. Ran 2-week sprints. Made priority calls based on what was hurting customers most.
- Translated stakeholder needs into clear written documentation: PRDs, release notes, customer briefs, internal updates.
- Spotted manual processes and proposed automated replacements. Example: the AI-personalisation feature I helped ship replaced a manual customer-segmentation process the marketing team was doing in spreadsheets.

**Product Analyst, Denner.in** (May 2024 - Dec 2024, hybrid in Pune)

- Owned product analytics and competitive research. Ran A/B tests, funnel deep-dives, user research syntheses. Built reporting dashboards. Maintained clean data pipelines for PM decision-making.


## Projects

**Personal AI-Powered Job-Search CRM** (May 2026 - ongoing)
[github.com/AjinkyaKate/job-tracker](https://github.com/AjinkyaKate/job-tracker)

This is the direct proof point for "build AI-assisted workflows for business tasks." I noticed my own job-search was full of manual coordination (which contact to follow up with, which resume for which role, which jobs need a status update) so I built an AI-powered CRM to automate it.

- FastAPI, PostgreSQL, Gemini for email classification, deployed on Render with a GitHub Actions cron for auto-sync.
- Functions as a CRM: tracks job leads, contacts, application status, follow-up reminders, communication history.
- Pulls LinkedIn job alerts from Gmail automatically. Classifies them, dedupes, surfaces only the relevant ones.
- Generates 15 role-tailored resumes per job family. Drafts personalised LinkedIn DMs to recruiters using LLMs.
- Daily-driver since launch. 100+ leads ingested, dozens of DM drafts sent.

This is what "use AI to automate manual operational work" looks like when you actually do it.

**AI QA Agent** (2026, in progress)
[github.com/AjinkyaKate/qa-agent](https://github.com/AjinkyaKate/qa-agent)

- AI agent that reads ticket acceptance criteria, browses the system being tested, checks UI and API behavior, attaches results back to the ticket. Pure process-automation experiment.


## Skills

Digital systems daily-driver: Jira, Notion, Confluence, Mixpanel, Amplitude, Figma, Postman, GitHub, Render. CRM platform experience: hands-on at D·engage (B2B customer engagement platform with CRM functionality). AI tools active use: ChatGPT, Claude, Gemini, used daily for drafting, summarising, and automating. SQL for data pulls and reporting. Spreadsheets (Excel, Google Sheets) for ops reporting. Python (intermediate) and FastAPI for building automation workflows. REST APIs, basic data mapping, ETL concepts. Strong written and verbal communication.


## Education

**Savitribai Phule Pune University**, Bachelor of Business Administration (BBA), Pune


## Certifications

**Certified Scrum Product Owner (CSPO)**, Scrum Alliance, Nov 2025
"""


def render_role_resume(family: str) -> str:
    """Compose the full markdown resume for the given role family.

    Returns empty string if family unknown.
    """
    # Standalone (non-PM-track) resumes that bypass the shared HEADER +
    # EXPERIENCE + PROJECTS blocks. Each is purpose-written for a different
    # role family that needs its own framing.
    if family == "digital-ops-coordinator":
        return DIGITAL_OPS_RESUME

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
    # Standalone (non-PM-track) resume for ops / coordinator roles.
    "digital-ops-coordinator":   "Digital Operations Coordinator",
}
