"""Templated outreach generator for Ajinkya's job search.

Given a job + a contact, produce four ready-to-paste messages in Ajinkya's
voice (plain, human, NO em-dashes):
  - connect_note   : LinkedIn connection-request note (Premium allows ~300 chars)
  - inmail_subject : InMail subject (<= ~120 chars)
  - inmail_body    : full InMail body (Premium, up to ~1900 chars)
  - followup_msg   : message to send once they accept the connection

Pure string templating: no LLM, no network, deterministic. Used by the
backfill (existing contacts) and the 15-min auto-pipeline (new contacts).
Tone varies by role-lane (AI-PM / PM / Product Owner / Customer Success /
Solutions Engineer) and by contact_type (founder / hiring_manager / recruiter
/ leader).
"""

PHONE = "+91 77588 80580"

# Stable positioning line — keep in sync with the resumes.
POSITIONING = ("I'm a Product Owner at D·engage (a CPaaS/martech SaaS), 2+ years, "
               "customer-facing and hands-on with product, and I build with AI "
               "(I've shipped my own tools on the Claude API)")

LANE_WORD = {
    "ai-pm": "AI Product", "pm": "Product Manager", "po": "Product Owner",
    "cs": "Customer Success", "se": "Solutions Engineer",
}
LANE_LINE = {
    "ai-pm": "Building AI-powered products is exactly where my focus is right now.",
    "pm": "End-to-end product ownership, from requirements to release to tracking adoption, is my core strength.",
    "po": "End-to-end ownership, from requirements and roadmap to release and adoption, is my core strength.",
    "cs": "The customer-facing side, onboarding, adoption and turning pain into fixes, is where I do my best work.",
    "se": "The mix of customer-facing work and explaining technical solutions is what I enjoy most.",
}
CONTACT_LINE = {
    "founder": "I really like what {company} is building, and I'd love to contribute.",
    "hiring_manager": "I'd value the chance to contribute to your team.",
    "recruiter": "I'd love to be put forward for it.",
    "leader": "I'd welcome the chance to connect and learn more.",
}


def first_name(name: str) -> str:
    return (name or "there").strip().split()[0] if (name or "").strip() else "there"


def detect_lane(title: str) -> str:
    t = (title or "").lower()
    if "ai product" in t or ("ai" in t and "product manager" in t):
        return "ai-pm"
    if any(k in t for k in ("customer success", "customer service", "customer engineer", "support engineer")):
        return "cs"
    if any(k in t for k in ("solutions engineer", "solution engineer", "presales", "pre-sales", "sales engineer")):
        return "se"
    if "product owner" in t:
        return "po"
    return "pm"


def generate(person_name, contact_type, job_title, company):
    """Return dict(connect_note, inmail_subject, inmail_body, followup_msg)."""
    first = first_name(person_name)
    lane = detect_lane(job_title)
    word = LANE_WORD[lane]
    lane_line = LANE_LINE[lane]
    ctype = (contact_type or "recruiter").lower()
    contact_line = CONTACT_LINE.get(ctype, CONTACT_LINE["recruiter"]).format(company=company)

    # ── Connection note (<=300, Premium) ────────────────────────────────────
    connect_note = (
        f"Hi {first}, saw the {word} opening at {company}. I'm a customer-facing "
        f"Product Owner (2+ yrs, CPaaS/martech) who builds with AI hands-on. "
        f"Would love to connect and explore a fit."
    )

    # ── InMail (subject + body) ──────────────────────────────────────────────
    inmail_subject = f"Interested in the {word} role at {company}"
    inmail_body = (
        f"Hi {first},\n\n"
        f"I came across the {job_title} role at {company} and it lines up well "
        f"with what I do. {POSITIONING}.\n\n"
        f"{lane_line} {contact_line}\n\n"
        f"I'd love to be considered, or to learn more about the team. Happy to "
        f"share my resume. Thanks for your time.\n\n"
        f"Ajinkya Kate\n{PHONE}"
    )

    # ── Post-accept follow-up ────────────────────────────────────────────────
    followup_msg = (
        f"Thanks for connecting, {first}. I'm interested in the {job_title} role "
        f"at {company}. {POSITIONING}. {lane_line} Happy to share my resume here "
        f"or apply however you prefer. Would love to hear more about the role."
    )

    return {
        "connect_note": connect_note,
        "inmail_subject": inmail_subject,
        "inmail_body": inmail_body,
        "followup_msg": followup_msg,
    }
