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

London HQ B2B SaaS for customer engagement. Enterprise customers in banking, retail, and telecom.

- Owned the RCS messaging channel from requirements to production. Worked through scope, engineering coordination, customer rollout, and post-release support.
- Ran production releases on a regular cadence. Coordinated with engineering on go-live readiness, wrote release notes that customer success and support teams used to brief their clients.
- Led delivery of customer-specific feature requests on the platform. Scoped with the customer, planned sprints with engineering, signed off before release.
- Coordinated integration projects on the platform end-to-end with vendor partners. Worked with vendor side to get prerequisites, map process flows, and walk customers and internal teams through what the integration would look like before engineering invested.
- Used Claude, ChatGPT, and Gemini in daily work to automate repeat reporting, summarise long threads, and tighten communication with the engineering team. Cut about half a day of busywork per week.

**Product Analyst, Denner.in** (May 2024 - Dec 2024, hybrid in Pune)

- Owned product analytics and competitive research for the PM team. Ran A/B tests, funnel deep-dives, user research syntheses.
"""

PROJECTS = """## Projects

**Personal Job Tracker** (May 2026 - ongoing)
[github.com/AjinkyaKate/job-tracker](https://github.com/AjinkyaKate/job-tracker)

- Built this during my current job search. FastAPI, PostgreSQL, Gemini for email classification, deployed on Render with a GitHub Actions cron.
- Pulls LinkedIn job-alert emails into a leads inbox with filters. Generates 15 role-tailored resumes. Auto-advances job status as Gmail picks up applied / interview / offer signals. Drafts LinkedIn DMs to recruiters.
- I use this daily. 100+ leads ingested so far.
"""

EDUCATION = """## Education

**Pune University**, Bachelor of Business Administration (BBA), Pune
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
            "AI side projects too: a personal AI-powered job tracker built end-to-end in Python with a "
            "Gemini email classifier. Looking for AI "
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
            "shipping B2B SaaS, currently at D·engage (customer engagement and MarTech for enterprise customers). "
            "On the side, shipped AI projects in production: personal job-search tracker (FastAPI, "
            "PostgreSQL, Gemini email classification, GitHub Actions cron for auto-sync, deployed on "
            "Render, in daily use). Comfortable wearing PM, engineer, and customer-success hats "
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
            "Customer-facing technical product professional with 2+ years in B2B SaaS, currently at D·engage (B2B marketing "
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
            "Product Engineer who owns features end-to-end. 2+ years in product roles, currently as Product Owner at D·engage "
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
            "Senior Product Manager candidate with 2+ years owning B2B SaaS product delivery, currently at D·engage. "
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
            "Technical Product Manager. PM with hands-on code comfort. 2+ years in product roles, currently as "
            "Product Owner at D·engage shipping B2B SaaS marketing automation and AI-powered features for enterprise "
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
            "customers and ships integrations end-to-end. 2+ years in product roles, currently at D·engage on the product side "
            "(B2B SaaS, AI marketing automation for enterprise clients in banking, retail, and telecom) "
            "built strong customer-pain to product-fit instincts. Personal projects in production: AI "
            "job tracker (FastAPI, PostgreSQL, Gemini, deployed on Render, in daily use). "
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
            "side, currently at D·engage (B2B SaaS, enterprise customer engagement, AI feature shipping). "
            "Side-project track: built a personal AI job tracker solo (FastAPI, PostgreSQL, Gemini email "
            "classification, GitHub Actions cron, deployed on Render, in daily use at "
            "github.com/AjinkyaKate/job-tracker). Wear engineer, PM, "
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
            "Customer-side product person with 2+ years in B2B SaaS at the intersection of product and "
            "customer-facing work. Enterprise customers in banking, retail, and telecom. Looking for "
            "Customer Engineer or Customer Services Engineer roles at B2B platforms where the work is "
            "being the bridge between customer and product."
        ),
        "skills": (
            "Customer onboarding, integration coordination with vendor partners, escalation triage, "
            "customer success collaboration, release notes for customer-facing teams. AI tools in "
            "daily work: Claude, ChatGPT, Gemini for drafting, summarising, automating repeat "
            "reporting, and tightening engineering communication. CSPO certified. B2B SaaS, customer "
            "engagement, enterprise customers in banking, retail, telecom."
        ),
    },
    "implementation-consultant": {
        "summary": (
            "Implementation Consultant or Engineer with 2+ years in B2B SaaS, currently at D·engage owning the product side of "
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
            "production. 2+ years in product roles, currently at D·engage shipping AI-powered marketing engagement features "
            "(LLM-assisted content generation, smart segmentation, personalization journeys). Partnered "
            "with engineering on model selection, prompt design, and evaluation. Personal AI projects in "
            "production: job tracker using Gemini for email classification (deployed on Render, in daily "
            "use). Looking for Applied AI Engineer, AI "
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


## About Me

I'm a B2B operations professional with 2+ years coordinating cross-functional work at a SaaS company. My day-to-day has been about keeping things moving across teams: tracking operational data in CRMs and dashboards, coordinating delivery schedules across engineering and customer success, and working with vendor partners on integrations. Comfortable taking ownership and spotting inefficiencies to fix. Available immediately.


## Experience

**Product Owner, D·engage** (Jan 2025 - May 2026, remote from Pune)

B2B SaaS customer engagement platform. The role spanned operational coordination across product, customer success, and vendor partners for enterprise customers in banking, retail, and telecom.

- Tracked operational data across the platform daily. Customer activity, campaign delivery status, support escalations, integration progress. Maintained accurate records that the team and customers depended on.
- Coordinated across engineering, design, QA, customer success, and implementation. Ran 2-week delivery cadence. Made priority calls when issues stacked up.
- Worked with vendor partners and integration teams to onboard enterprise customers onto the platform. Tracked configuration progress, resolved blockers, kept stakeholders updated through every stage of onboarding.
- Translated customer feedback from support, CSM, and sales teams into prioritised work. Wrote requirements documents, release notes, and stakeholder updates.
- Used ChatGPT, Claude, and Gemini in normal work to speed up drafting and analysis. Saved about half a day per week by automating repetitive reporting tasks.

**Product Analyst, Denner.in** (May 2024 - Dec 2024, hybrid in Pune)

- Owned product analytics and competitive research. Ran A/B tests, funnel deep-dives, user research syntheses. Built and maintained reporting dashboards.


## Skills

Operations coordination across engineering, customer success, and vendor partners. Sprint planning, escalation triage, delivery scheduling, and stakeholder updates owned end-to-end.

Data tracking in CRMs and dashboards. A/B testing, funnel analysis, user research syntheses. Comfortable turning raw operational data into decisions and weekly stakeholder updates.

Day-to-day tools: Jira, Confluence, Notion, Google Workspace, Excel/Sheets, Looker.

ChatGPT, Claude, and Gemini in normal work — drafting reports, writing requirements, and automating repeat reporting tasks.

Languages: English, Hindi, Marathi.


## Education

**Pune University**, Bachelor of Business Administration (BBA), Pune


## Certifications

**Certified Scrum Product Owner (CSPO)**, Scrum Alliance, Nov 2025
"""


# ─── Standalone resume: Vibe Coding Engineer ────────────────────────────────
# For roles that hire engineers who ship working apps fast using AI-assisted
# development (Claude Code, Cursor, Lovable, Emergent etc). Different from the
# 15 PM-track families: leads with a Featured Project (the job-tracker itself,
# live link + GitHub link), has a "How I Work" section about vibe-coding
# rhythm + engineering judgment, then Experience.

VIBE_CODING_ENGINEER_RESUME = """# Ajinkya Kate

[+91 77588 80580](tel:+917758880580) · [ajinkyakate2001@gmail.com](mailto:ajinkyakate2001@gmail.com) · [LinkedIn](https://linkedin.com/in/ajinkya-kate) · [GitHub](https://github.com/AjinkyaKate)

Pune, India · Available immediately · CSPO Certified


## Summary

I'm a product person who builds. The clearest way to show this is my current side project: a live job-search CRM I built solo in 3 weeks with Claude Code as my main dev environment. It's in daily use, code is public, around 50 commits in. Before this I spent 2+ years in product roles, most recently as Product Owner at D·engage, shipping AI features in B2B SaaS for banking, retail, and telecom customers. I'm looking for a Full Stack Builder type role where the brief is "make this idea a real working app this week, not next quarter."


## Featured Project

**Job Tracker** (May 2026, in daily use)

[job-tracker-bmhy.onrender.com](https://job-tracker-bmhy.onrender.com) · [github.com/AjinkyaKate/job-tracker](https://github.com/AjinkyaKate/job-tracker)

The brief I gave myself: pull LinkedIn job alerts from my Gmail, surface them as triage cards with the full JD already fetched, track each application through to offer. Started with an empty folder and Claude Code. Shipped a working v1 in 3 weekends.

The product today:

- Reads job-alert emails from Gmail every 10 minutes via GitHub Actions, parses LinkedIn's HTML, dedupes by URL
- Pulls the full JD from LinkedIn's public guest endpoint so I read jobs in my own tool, not LinkedIn's
- Generates 15 role-tailored resumes from one Python file (this one came from that system)
- Drafts personalised LinkedIn DMs with Gemini, based on the contact's profile and the role
- Tracks status as Gmail picks up signals like applied, interview, rejected
- Multi-tenant now: this week I shipped Google sign-in plus per-user data partitioning so a friend can use it with their own Gmail

What I actually learned shipping this:

- Cost matters from day one. Whole stack is $0/month: Render free dyno, free Postgres, Gemini free tier. I designed around the rate limits, not against them. When Gemini quota runs out, regex parsing takes over so sync keeps working.
- Observability without buying a stack. The sync engine writes a one-line summary to the DB after every run (fetched count, new leads, status changes). When the cron was silently failing for three days, I noticed from this summary, not from any monitoring tool.
- A tradeoff I'd revisit if real users showed up: I used html2pdf.js for client-side PDF so I wouldn't have to install a headless browser. The output is image-based, not ATS-friendly. Fine for me, not fine for v2.


## Experience

**Product Owner, D·engage** (Jan 2025 - May 2026, remote from Pune)

London HQ B2B SaaS for customer engagement. Enterprise customers in banking, retail, telecom.

- Shipped 3 AI features into production: LLM-generated email content, smart audience segmentation, content personalisation. Worked with engineers on prompt design, eval criteria, model selection.
- Translated customer feedback from CSM, support, and sales teams into prioritised work. Wrote PRDs, release notes, customer briefs, integration trackers.
- Used Claude, ChatGPT, Gemini in daily work for drafting, summarising, automating repeat reporting. Cut about half a day of weekly busywork.
- Built quick prototypes with no-code tools and AI-assisted code to validate ideas before engineering invested heavily.

**Product Analyst, Denner.in** (May 2024 - Dec 2024, hybrid in Pune)

- Owned product analytics and competitive research. Ran A/B tests, funnel deep-dives, user research syntheses.


## How I Work

I work in a vibe-coding rhythm. AI tooling is the partner, I'm the judgment layer. Default mode is "code, ship, see what breaks, iterate."

Day-to-day stack: Claude Code as the main dev environment, Cursor for spot edits. Python with FastAPI, Jinja2, PostgreSQL on the backend. Tailwind and a little vanilla JS on the frontend. Gemini and Anthropic for the LLM work. Render for hosting, GitHub Actions for automation.

I'm careful about auth, schema, anything that touches user data. Copy, UI tweaks, one-off scripts ship fast and iterate based on real use. The call on hack vs build clean is what separates a production prototype from a throwaway demo.


## Education

**Pune University**, Bachelor of Business Administration (BBA), Pune


## Certifications

**Certified Scrum Product Owner (CSPO)**, Scrum Alliance, Nov 2025
"""


# ─── Standalone resume: General / shareable ─────────────────────────────────
# A single, role-agnostic resume for sharing on WhatsApp / Slack groups, with
# referrers, or anywhere a JD-tailored variant would be overkill. Framed
# builder-led: product person who ships code with AI as the dev partner.
# Hyperlinked throughout so anyone clicking on a PDF can reach the live app,
# GitHub, LinkedIn, phone, email in one click.

GENERAL_RESUME = """# Ajinkya Kate

[+91 77588 80580](tel:+917758880580) · [ajinkyakate2001@gmail.com](mailto:ajinkyakate2001@gmail.com) · [LinkedIn](https://linkedin.com/in/ajinkya-kate) · [GitHub](https://github.com/AjinkyaKate)

Pune, India · Available immediately · CSPO Certified


## Summary

Product person who also ships code. I work as a full-stack builder using AI tools like Claude Code as my dev environment, turning ambiguous ideas into shipped, working applications. 2+ years in product roles, currently as Product Owner at D·engage in B2B SaaS, comfortable across product calls, customer conversations, and the code itself.


## Experience

**Product Owner, D·engage** (Jan 2025 - May 2026, remote from Pune)

London HQ B2B SaaS for customer engagement. Enterprise customers in banking, retail, telecom.

- Owned the RCS messaging channel from requirements to production. Worked through scope, engineering coordination, customer rollout, and post-release support.
- Ran production releases on a regular cadence. Coordinated with engineering on go-live readiness, wrote release notes that customer success and support teams used to brief their clients.
- Led delivery of customer-specific feature requests on the platform. Scoped with the customer, planned sprints with engineering, signed off before release.
- Built quick prototypes to explain integration projects on the platform. For example, walked customers and internal teams through what a text/messaging integration would look like end-to-end before engineering invested.
- Used Claude, ChatGPT, and Gemini in daily work to automate repeat reporting, summarise long threads, and tighten communication with the engineering team. Cut about half a day of busywork per week.

**Product Analyst, Denner.in** (May 2024 - Dec 2024, hybrid in Pune)

- Owned product analytics and competitive research. Ran A/B tests, funnel deep-dives, user research syntheses. Built and maintained reporting dashboards.


## Project

**Job Tracker** (May 2026, in daily use)

[job-tracker-bmhy.onrender.com](https://job-tracker-bmhy.onrender.com) · [github.com/AjinkyaKate/job-tracker](https://github.com/AjinkyaKate/job-tracker)

A personal CRM for managing job applications end to end. Pulls job-alert emails from Gmail, parses each lead, fetches the full job description, generates a role-tailored resume, drafts personalised LinkedIn DMs to recruiters, and tracks each application from saved through to offer.

Built solo with Claude Code as my main dev environment. Around 50 commits, multi-tenant (Google sign-in, per-user data), running on free-tier infrastructure with cost designed in from day one.


## Skills

**Product:** Writing PRDs, customer briefs, customer discovery, sprint planning, requirement triage, stakeholder communication, release notes. CSPO certified. A/B testing, funnel analysis, user research.

**Building with AI:** Claude Code as my primary dev environment, with Cursor for spot edits. Comfortable working with LLMs in the loop: prompt design, structured outputs, evaluation thinking, cost-aware design. Day to day I use Claude, ChatGPT, and Gemini to automate repeat reporting, draft documentation, summarise long threads, and tighten communication with engineering.

**Tools and platforms:** GitHub, Render, Jira, Confluence, Notion, Google Workspace, Excel and Sheets.

**Languages:** English, Hindi, Marathi.


## Education

**Pune University**, Bachelor of Business Administration (BBA), Pune


## Certifications

**Certified Scrum Product Owner (CSPO)**, Scrum Alliance, Nov 2025
"""


# ─── Standalone resume: Solutions / Customer Success Engineer ───────────────
# For the SE / CSE / Forward-Deployment role family (Morphisec, CleverTap,
# CashFlo, CometChat, ElevenLabs, etc). Post-sales-CSE flavor: leads with
# customer-facing + integration + troubleshooting, frames technical depth
# honestly as "I ship working software with AI-assisted development", and
# uses the job tracker as concrete proof of hands-on technical work.

SOLUTIONS_ENGINEER_RESUME = """# Ajinkya Kate

[+91 77588 80580](tel:+917758880580) · [ajinkyakate2001@gmail.com](mailto:ajinkyakate2001@gmail.com) · [LinkedIn](https://linkedin.com/in/ajinkya-kate) · [GitHub](https://github.com/AjinkyaKate)

Pune, India · Available immediately · CSPO Certified


## Summary

Customer-facing technical person with 2+ years in B2B SaaS. I sit between the customer and the product team: onboarding, integration coordination, troubleshooting, and turning customer pain into clear requirements engineering can act on. Comfortable reading APIs and shipping working software with AI-assisted development. Looking for Customer Success Engineer, Solutions Engineer, or Forward Deployment roles where the job is making customers successful on a technical product.


## Experience

**Product Owner, D·engage** (Jan 2025 - May 2026, remote from Pune)

London HQ B2B SaaS for customer engagement. Enterprise customers in banking, retail, telecom.

- Onboarded enterprise customers onto the platform. Owned the RCS messaging channel from requirements to production, including customer rollout and post-launch support.
- Coordinated integration projects end to end with vendor partners. Gathered prerequisites, mapped process flows, and walked customers and internal teams through how an integration would work before engineering invested.
- Was the technical bridge between customers and engineering. Heard what frustrated a customer, translated it into a clear requirement, and often delivered the small fixes on the ground myself.
- Ran production releases on a regular cadence. Wrote release notes that customer success and support teams used to brief their clients.
- Used Claude, ChatGPT, and Gemini in daily work to automate repeat reporting and tighten communication with engineering.

**Product Analyst, Denner.in** (May 2024 - Dec 2024, hybrid in Pune)

- Owned product analytics and competitive research. Ran A/B tests, funnel deep-dives, user research syntheses. Built and maintained reporting dashboards.


## Project

**Job Tracker** (May 2026, in daily use)

[job-tracker-bmhy.onrender.com](https://job-tracker-bmhy.onrender.com) · [github.com/AjinkyaKate/job-tracker](https://github.com/AjinkyaKate/job-tracker)

A working app I built solo with Claude Code as my dev environment. It reads my Gmail for job-alert emails, parses each one, fetches the full job description over an API, and tracks every application through to offer.

Why it matters for this role: it is proof I work hands-on with the technical side of a product. Real API integration (Gmail, OAuth with PKCE, a public job-data endpoint), a Postgres database, deployed on cloud infra with a scheduled job, debugged when it broke. I read the logs, fix what is wrong, and ship. I do this with AI-assisted development, which is how a lot of technical work gets done now.


## Skills

**Customer-facing:** Onboarding, integration coordination with vendor partners, requirement gathering, troubleshooting, escalation triage, release notes for customer-facing teams, stakeholder communication.

**Technical:** Reading and debugging APIs (REST, JSON, webhooks), OAuth flows, reading logs, basic SQL. Ship working web apps with AI-assisted development (Claude Code, Cursor). Comfortable in a codebase even when I did not write every line.

**Tools:** Jira, Confluence, Notion, Postman, GitHub, Google Workspace, Render.

**AI in daily work:** Claude, ChatGPT, Gemini for drafting, analysis, debugging, and automating repeat work.

**Languages:** English, Hindi, Marathi.


## Education

**Pune University**, Bachelor of Business Administration (BBA), Pune


## Certifications

**Certified Scrum Product Owner (CSPO)**, Scrum Alliance, Nov 2025
"""


# ─── Standalone resume: Business Technology / Data Solutions ────────────────
# For the consulting-tech-hybrid family: ZS Business Technology Solutions
# Associate, Deloitte/Accenture/EXL/Tiger Analytics tech-consulting and
# data-solutions associate roles. 0-3 yrs, business-to-technical translation
# is the core ask. Honest framing: leads with translation + data analytics +
# AI-tooling fluency (co-pilot / SQL generation, which these JDs name),
# claims working SQL/Python without overclaiming deep data-engineering.

BIZ_TECH_SOLUTIONS_RESUME = """# Ajinkya Kate

[+91 77588 80580](tel:+917758880580) · [ajinkyakate2001@gmail.com](mailto:ajinkyakate2001@gmail.com) · [LinkedIn](https://linkedin.com/in/ajinkya-kate) · [GitHub](https://github.com/AjinkyaKate)

Pune, India · Available immediately · CSPO Certified


## Summary

Business-technology hybrid with 2+ years turning business problems into working data and software solutions. At D·engage I translated customer and operational needs into technical requirements engineering could build. At Denner.in I owned product analytics, A/B testing, and reporting dashboards. Comfortable with SQL and Python, and I lean on AI-assisted development (Claude Code, co-pilot, SQL generation) to ship faster. Looking for Business Technology and Data Solutions roles where the job is bridging business and technical delivery for clients.


## Experience

**Product Owner, D·engage** (Jan 2025 - May 2026, remote from Pune)

London HQ B2B SaaS for customer engagement. Enterprise customers in banking, retail, telecom.

- Translated business problems into technical designs. Took customer and operational needs and turned them into clear requirements and specs engineering could build against.
- Owned the RCS messaging channel and integration projects end to end: scoping, coordinating with engineering, production rollout, and post-launch support.
- Tracked operational data across the platform (customer activity, campaign delivery, integration progress) and turned it into reporting the team and customers relied on.
- Used Claude, ChatGPT, and Gemini in daily work for analysis, drafting, and automating repeat reporting, including generating and checking SQL and code with AI tools.

**Product Analyst, Denner.in** (May 2024 - Dec 2024, hybrid in Pune)

- Owned product analytics and competitive research. Ran A/B tests, funnel deep-dives, and user-research synthesis. Built and maintained the reporting dashboards the product team used to make decisions.


## Project

**Job Tracker** (May 2026, in daily use)

[job-tracker-bmhy.onrender.com](https://job-tracker-bmhy.onrender.com) · [github.com/AjinkyaKate/job-tracker](https://github.com/AjinkyaKate/job-tracker)

A working app I built solo with Claude Code as my dev environment. It reads my Gmail for job-alert emails, parses each one into structured data in PostgreSQL, fetches job descriptions over APIs, and tracks every application through to offer.

The technical surface: a PostgreSQL schema I designed and migrate, SQL queries across jobs / contacts / events tables, REST API integration, OAuth, and cloud deployment with a scheduled job. Built with AI-assisted development. It is proof I can take a problem from idea to a deployed, data-backed solution, which is the same loop as translating a client need into a working build.


## Skills

**Business and technical:** Translating business problems into technical requirements and designs, requirement gathering, stakeholder communication, agile delivery, client-facing work.

**Data and analytics:** SQL (working), PostgreSQL schema design, A/B testing, funnel analysis, reporting dashboards, data synthesis.

**Programming and AI tooling:** Python (working, AI-assisted), REST APIs, OAuth. Heavy use of Claude Code, co-pilot, and SQL-generation tools to build and ship.

**Cloud and tools:** Cloud deployment (Render), GitHub, GitHub Actions, Jira, Confluence, Notion, Excel and Sheets, Google Workspace.

**Languages:** English, Hindi, Marathi.


## Education

**Pune University**, Bachelor of Business Administration (BBA), Pune


## Certifications

**Certified Scrum Product Owner (CSPO)**, Scrum Alliance, Nov 2025
"""


# ─── Standalone resume: Augnito Product Manager (Voice AI / healthcare) ─────
# Tailored to the Augnito PM JD: end-to-end product lifecycle, B2B SaaS,
# customer obsession, cross-functional influence (design/eng/CS/sales),
# data-driven decisions, AI-driven solutions + design thinking (preferred).
# Honest on years (2+, not the 4+ they ask) but leads hard on end-to-end
# ownership and the Voice-AI/healthcare-adjacent angle.

AUGNITO_PM_RESUME = """# Ajinkya Kate

[+91 77588 80580](tel:+917758880580) · [ajinkyakate2001@gmail.com](mailto:ajinkyakate2001@gmail.com) · [LinkedIn](https://linkedin.com/in/ajinkya-kate) · [GitHub](https://github.com/AjinkyaKate)

Pune, India · Available immediately · CSPO Certified


## Summary

Product Owner with 2+ years building and shipping B2B SaaS, owning features end to end: user research and requirements, roadmap prioritization, release management, and tracking adoption after launch. I work close to customers and across design, engineering, customer success, and sales to turn real pain into product that moves the metric. Comfortable making data-driven trade-offs in ambiguous, fast-moving environments, and I build with AI hands-on. Drawn to high-impact, AI-driven SaaS like Voice AI for healthcare, where the product directly changes how professionals do their work.


## Experience

**Product Owner, D·engage** (Jan 2025 - May 2026, remote from Pune)

London HQ B2B SaaS for customer engagement. Enterprise customers in banking, retail, telecom.

- Owned the RCS messaging channel end to end: user and stakeholder research, requirements, roadmap prioritization, production release management, and tracking adoption after launch.
- Ran production releases on a regular cadence and wrote the release notes customer success and support used to brief enterprise clients, then watched adoption and fed the learnings back into the roadmap.
- Partnered across design, engineering, quality, customer success, and sales to scope features and weigh trade-offs between customer experience, performance, and operational support load.
- Stayed close to customers through the whole journey: onboarding, integration coordination, and turning recurring pain into clear, prioritized requirements engineering could act on.
- Used Claude, ChatGPT, and Gemini daily to analyze usage data, draft specs, and automate repeat reporting.

**Product Analyst, Denner.in** (May 2024 - Dec 2024, hybrid in Pune)

- Owned product analytics and competitive research. Ran A/B tests and funnel deep-dives, and built the reporting dashboards the product team used to make data-driven calls.


## Project

**Job Tracker** (May 2026, in daily use)

[job-tracker-bmhy.onrender.com](https://job-tracker-bmhy.onrender.com) · [github.com/AjinkyaKate/job-tracker](https://github.com/AjinkyaKate/job-tracker)

An AI-driven product I scoped, built, and shipped solo, end to end. It reads my Gmail for job-alert emails, parses each into structured data, fetches the full job description over an API, ranks roles by fit, and tracks every application through to offer.

Why it matters here: it is proof I take a product from user need to a deployed, data-backed build and then iterate on adoption. Real API integration, a PostgreSQL database I designed, cloud deployment, and AI features built on the Claude API. The same end-to-end ownership this role asks for, done hands-on.


## Skills

**Product management:** End-to-end lifecycle ownership, user and market research, product strategy, requirements and PRDs, roadmap prioritization, release management, adoption and outcome metrics, iteration. Design thinking and human-centered design.

**Customer and cross-functional:** Customer obsession, onboarding, working across design, engineering, quality, customer success, sales, and support, and influencing stakeholders at every level.

**Data-driven:** A/B testing, funnel analysis, reporting dashboards, SQL (working), turning usage data into product decisions.

**AI-driven solutions:** Build with the Claude API and LLMs hands-on and ship AI features; daily use of Claude, ChatGPT, and Gemini for analysis, specs, and automation.

**Tools:** Jira, Confluence, Notion, Figma, Postman, GitHub, Google Workspace.

**Languages:** English, Hindi, Marathi.


## Education

**Pune University**, Bachelor of Business Administration (BBA), Pune


## Certifications

**Certified Scrum Product Owner (CSPO)**, Scrum Alliance, Nov 2025
"""


# ─── Standalone resume: Saleshandy Platform/API/Integrations PM ─────────────
# Tailored to both Saleshandy roles (Product Manager API/Integrations/Platform
# AND Technical PM Email Deliverability) since both ask for the same shape:
# technical PM on a B2B SaaS messaging/email-adjacent platform, owning the
# API/integration surface, customer-facing, AI-tool fluency. Anchors on the
# D·engage RCS-channel + integration-delivery work which is the exact parallel.

SALESHANDY_PM_RESUME = """# Ajinkya Kate

[+91 77588 80580](tel:+917758880580) · [ajinkyakate2001@gmail.com](mailto:ajinkyakate2001@gmail.com) · [LinkedIn](https://linkedin.com/in/ajinkya-kate) · [GitHub](https://github.com/AjinkyaKate)

Pune, India · Available immediately · CSPO Certified


## Summary

Product Owner with 2+ years shipping platform and integration features on a B2B SaaS. I own the RCS messaging channel at D·engage end to end: requirements, integration delivery with vendor partners, production releases, and post-launch support. Technically fluent. Comfortable reading APIs (REST, OAuth, webhooks), debugging from logs, writing basic SQL, and shipping tools on the Claude API. The platform-PM loop, talk to users, define the API surface, ship, measure adoption, is the work I want to do full-time.


## Experience

**Product Owner, D·engage** (Jan 2025 - May 2026, remote from Pune)

London HQ B2B SaaS for customer engagement. Enterprise customers in banking, retail, telecom.

- Owned the RCS messaging channel end to end. Requirements, roadmap, production releases, adoption tracking. The same loop the Saleshandy platform/API role asks for, on a CPaaS adjacent to cold-email infrastructure.
- Coordinated integration projects end to end with vendor partners. Gathered prerequisites, mapped process flows, walked customers and internal teams through how an integration would work before engineering invested a line of code.
- Sat between customers and engineering. Heard the pain in onboarding calls, translated it into a clear requirement, and often shipped the small fixes on the ground myself.
- Read APIs, debugged from logs, used Postman daily to validate integrations before customer rollout. Wrote release notes the support team used to brief enterprise clients.
- Used Claude, ChatGPT, and Gemini in daily work to analyze usage data, draft specs, and automate repeat reporting.

**Product Analyst, Denner.in** (May 2024 - Dec 2024, hybrid in Pune)

- Owned product analytics and competitive research. Ran A/B tests and funnel deep-dives, and built the reporting dashboards the product team used to make data-driven calls.


## Project

**Job Tracker** (May 2026, in daily use)

[job-tracker-bmhy.onrender.com](https://job-tracker-bmhy.onrender.com) · [github.com/AjinkyaKate/job-tracker](https://github.com/AjinkyaKate/job-tracker)

A working platform I built solo with the Claude API as the brain. Reads Gmail via OAuth, parses LinkedIn alert emails into structured data, fetches full JDs over a third-party REST API, ranks roles by fit, and pushes to PostgreSQL on a scheduled background job.

Why it matters here: it is proof I build platform/API/integration products hands-on. Real OAuth flows, REST integration, webhooks, a Postgres schema I designed and migrate, scheduled jobs, deployed on cloud infra. The same surface a Saleshandy API/Platform PM owns, done end to end on my own.


## Skills

**Platform / API / Integrations:** Owning a channel end to end on B2B SaaS, integration coordination with vendor partners, API surface design discussions with engineering, prerequisites and process-flow mapping, customer-facing onboarding for integrations, developer-experience thinking.

**Technical fluency:** REST APIs, JSON, webhooks, OAuth flows, reading and debugging from logs, basic SQL, Postman. Ship working software with AI-assisted development (Claude Code, Cursor). Comfortable in a codebase even when I did not write every line.

**Product:** End-to-end product lifecycle, user research in onboarding and support calls, requirements and PRDs, release management, adoption tracking, metrics.

**AI in daily work:** Build with the Claude API hands-on. Daily use of Claude, ChatGPT, and Gemini for analysis, drafting, and automation.

**Tools:** Jira, Confluence, Notion, Postman, GitHub, Google Workspace, Render.

**Languages:** English, Hindi, Marathi.


## Education

**Pune University**, Bachelor of Business Administration (BBA), Pune


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
    if family == "vibe-coding-engineer":
        return VIBE_CODING_ENGINEER_RESUME
    if family == "general":
        return GENERAL_RESUME
    # Override the modular solutions-engineer config with the purpose-written
    # standalone (post-sales-CSE flavor, honest AI-build framing).
    if family == "solutions-engineer":
        return SOLUTIONS_ENGINEER_RESUME
    if family == "biz-tech-solutions":
        return BIZ_TECH_SOLUTIONS_RESUME
    if family == "augnito-pm":
        return AUGNITO_PM_RESUME
    if family == "saleshandy-pm":
        return SALESHANDY_PM_RESUME

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
    # Standalone resume for vibe-coding / rapid-prototyping engineer roles.
    "vibe-coding-engineer":      "Vibe Coding Engineer",
    # Generic shareable resume — for posting in WhatsApp / Slack groups,
    # forwarding to networks, or attaching anywhere a JD-specific version
    # would be overkill. Framed builder-led: product person who ships code.
    "general":                   "Resume",
    # Standalone resume for consulting-tech-hybrid / data-solutions roles
    # (ZS BTSA, Deloitte/Accenture/EXL/Tiger Analytics tech-consulting).
    "biz-tech-solutions":        "Business Technology Solutions",
    # Standalone resume tailored to the Augnito Voice-AI PM JD (end-to-end
    # lifecycle, B2B SaaS, customer obsession, AI-driven, healthcare-adjacent).
    "augnito-pm":                "Product Manager - Augnito",
    # Standalone resume tailored to both Saleshandy PM JDs (API/Integrations/
    # Platform AND Email Deliverability). Anchors on the D·engage RCS-channel +
    # integration-delivery work as the direct parallel.
    "saleshandy-pm":             "Product Manager - Saleshandy",
}
