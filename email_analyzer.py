"""LLM-powered email classification for the job tracker.

Sends each email (subject + sender + body + current job context) to Google
Gemini 2.5 Flash and gets back a structured classification: is this email
about a job in the user's tracker? which one? what's the event type? should
the job's status change?

Why Gemini: free tier (1500 requests/day, no credit card), good enough quality
for this classification task, fast (~1s/email). Switchable to Claude later by
adding ANTHROPIC_API_KEY + a parallel _analyze_with_claude() function.

Set GEMINI_API_KEY env var to enable. Get a key at
https://aistudio.google.com/app/apikey — no card required.
"""
import os
from typing import Optional, List, Literal

from pydantic import BaseModel

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

try:
    from google import genai
    from google.genai import types as genai_types
    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False


# Event types Gemini may return. Must mirror what gmail_integration logs to events.event_type.
EventType = Literal[
    "application_acknowledged",
    "application_sent",
    "application_viewed",
    "application_interest",
    "recruiter_interest",
    "interview_invited",
    "interview_scheduled",
    "offer_received",
    "application_rejected",
    "connection_accepted",
    "message_received",
    "inmail_received",
    "profile_viewed",
    "other_job_related",
    "not_job_related",
]

Status = Literal["saved", "applied", "replied", "interview", "offer", "rejected"]


class EmailClassification(BaseModel):
    """Structured output schema we ask Gemini to fill."""
    is_job_related: bool
    matched_job_id: Optional[int] = None
    event_type: EventType
    target_status: Optional[Status] = None
    summary: str
    confidence: float


def is_available() -> bool:
    """True when both the SDK is installed and a Gemini API key is present."""
    return _GENAI_AVAILABLE and bool(GEMINI_API_KEY)


def _format_jobs_context(jobs: List[dict]) -> str:
    """Compact one-line-per-job list for the system prompt."""
    if not jobs:
        return "(no jobs in tracker yet — user hasn't added any companies)"
    lines = []
    for j in jobs:
        company = j.get("company") or "?"
        title = j.get("title") or "?"
        status = j.get("status") or "?"
        lines.append(f"- id={j['id']} | {company} | {title} | status={status}")
    return "\n".join(lines)


SYSTEM_PROMPT_TEMPLATE = """You are an email classifier for a personal job tracker.

The user is actively job-hunting. Their tracker has these jobs (one row per
company/role they're tracking):

{jobs_context}

For each email you receive, decide:

1. is_job_related: true if this email is about ANY of these — a job application
   acknowledgement, recruiter cold mail, interview invitation/schedule, offer,
   rejection, LinkedIn connection accepted, LinkedIn message, InMail, or any
   other recruiting / hiring touchpoint. Otherwise false (newsletter, personal,
   transactional like banking, etc.)

2. matched_job_id: the integer id from the list above if you can confidently
   match this email to one of the user's tracker jobs (by company name appearing
   in the subject/body/sender domain). If the email is clearly job-related but
   the company isn't in the tracker, return null. If unsure, return null.

3. event_type: pick one from this exact list:
   application_acknowledged, application_sent, application_viewed,
   application_interest, recruiter_interest, interview_invited,
   interview_scheduled, offer_received, application_rejected,
   connection_accepted, message_received, inmail_received, profile_viewed,
   other_job_related, not_job_related

4. target_status: which pipeline status the job should ADVANCE to. Map:
   - application_acknowledged or application_sent -> "applied"
   - recruiter_interest or application_interest -> "replied"
   - interview_invited or interview_scheduled -> "interview"
   - offer_received -> "offer"
   - application_rejected -> "rejected"
   - All other event types -> null (no status change)
   Use null for LinkedIn relationship events (connection_accepted etc.).

5. summary: one or two sentences in plain English summarising what the email
   actually says. Skip greetings/boilerplate. Capture the action/news.

6. confidence: 0.0 to 1.0 — how confident you are that matched_job_id is
   correct. If the email is from "Acme Recruiting" but you matched to "Acme
   Corp" in the tracker, use lower confidence.

Rules:
- Be conservative on matching. If two tracker jobs have similar company names,
  set confidence below 0.7 and pick the most likely OR set matched_job_id=null.
- Sender domain is a strong signal: no-reply@disco.com -> company is DISCO.
- "Thank you for applying to X" pattern is unambiguous: match X to tracker.
- Don't promote a job to a status earlier in the pipeline than current
  (handled by caller — just give honest target_status).
"""


def analyze_email(subject: str, sender: str, body: str,
                  jobs: List[dict]) -> Optional[EmailClassification]:
    """Classify a single email. Returns None on Gemini failure / config missing.

    body should be the cleaned plain-text body. Truncated to 3000 chars before
    sending to Gemini (most ATS emails are well under that).
    """
    if not is_available():
        return None

    client = genai.Client(api_key=GEMINI_API_KEY)
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        jobs_context=_format_jobs_context(jobs)
    )

    user_msg = (
        f"Email to classify:\n\n"
        f"Subject: {subject}\n"
        f"From: {sender}\n\n"
        f"Body (truncated to 3000 chars):\n{body[:3000]}"
    )

    try:
        # gemini-2.0-flash-lite has higher RPM cap (30/min) than 2.5-flash (20/min)
        # — important for sync runs that touch many emails.
        response = client.models.generate_content(
            model="gemini-2.0-flash-lite-001",
            contents=[user_msg],
            config=genai_types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=EmailClassification,
                temperature=0.1,
            ),
        )
        # Newer SDK exposes .parsed for schema-based responses
        if getattr(response, "parsed", None) is not None:
            return response.parsed
        # Fallback: parse JSON text manually
        return EmailClassification.model_validate_json(response.text)
    except Exception as exc:
        # Caller treats None as "fallback to regex / skip"
        print(f"[email_analyzer] Gemini call failed: {type(exc).__name__}: {exc}")
        return None
