"""JD Analysis — extracts structured insights from a job description.

Given a JD + the user's profile, returns: match score (STRONG/MAYBE/SKIP),
one-sentence reason, required-skills list, HR email if mentioned, plain
summary. Result caches on the jobs row so re-opening a card never re-hits
Gemini unless the user explicitly clicks Re-analyze.

See JD_ANALYSIS_PLAN.md for the full feature spec.
"""
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel

import llm_helpers
from db import Connection


# Default profile used when the user has no row in user_profile yet.
# First /profile visit seeds with this; user can edit freely from there.
DEFAULT_PROFILE = """Product Owner at D·engage (B2B SaaS, ~2 yrs).

Customer-facing work: integration coordination, release management, vendor partner liaison.

Strong with AI tools (Claude, Gemini), B2B SaaS, enterprise integrations. CSPO certified.

Looking for: PM, PO, Customer Engineer, Solutions Engineer, Vibe Coding Engineer roles.

Open to: Mumbai, Pune, Bengaluru, remote India. Available immediately."""


class JDAnalysis(BaseModel):
    """Structured output schema for one JD analysis call.

    Gemini fills this via response_schema. Kept flat (no nested objects)
    because Gemini's schema enforcement is more reliable on simple shapes.
    """
    score: str                      # "STRONG" | "MAYBE" | "SKIP"
    score_reason: str               # one sentence why, max ~30 words
    required_skills: List[str]      # 5-8 top skills from the JD
    hr_email: Optional[str] = None  # extracted from JD if explicitly present
    summary: str                    # 2-3 sentence role summary


JD_ANALYSIS_PROMPT = """You're analyzing a job description for a candidate.

Return JSON matching the schema with these fields:

- score: one of "STRONG", "MAYBE", "SKIP"
- score_reason: one sentence why, max 25 words. Be specific (mention years gap, domain match, or skills overlap).
- required_skills: 5-8 top skills from the JD, focused on what the candidate would need on day one. Use short tags ("Product Management", "REST APIs", "B2B SaaS", etc.).
- hr_email: email address explicitly mentioned in the JD ("send to careers@x.com", "contact hr@y.com"). null if not present. Do NOT invent.
- summary: 2-3 plain-English sentences. What the role is + the seniority + the must-have skills. Don't repeat the candidate profile.

Scoring rubric:
- STRONG: profile matches the core asks AND no hard blockers. Years gap of 3 or less is fine. Domain learnable in 1-3 months is fine.
- MAYBE: roughly half the asks match, OR strong match with one stretchy gap (years short by more than 3, hard domain like deep security or low-level systems, location not workable).
- SKIP: hard mismatch on years (gap > 5), explicit must-have the profile can't claim (e.g. specific certifications), or wrong role type entirely.

Be honest. The candidate uses this to triage 100+ leads a week. False STRONGs waste their time more than false SKIPs."""


VALID_SCORES = {"STRONG", "MAYBE", "SKIP"}


def load_profile_text(conn: Connection, user_id: int) -> str:
    """Return the saved profile text for a user, or DEFAULT_PROFILE if none."""
    row = conn.execute(
        "SELECT profile_text FROM user_profile WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    if row and (row["profile_text"] or "").strip():
        return row["profile_text"]
    return DEFAULT_PROFILE


def save_profile_text(conn: Connection, user_id: int, profile_text: str) -> None:
    """Upsert the profile_text for a user. Empty / whitespace-only is rejected."""
    if not (profile_text or "").strip():
        raise ValueError("Profile text cannot be empty.")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    existing = conn.execute(
        "SELECT user_id FROM user_profile WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE user_profile SET profile_text = ?, updated_at = ? "
            "WHERE user_id = ?",
            (profile_text, now, user_id),
        )
    else:
        conn.execute(
            "INSERT INTO user_profile (user_id, profile_text, updated_at) "
            "VALUES (?, ?, ?)",
            (user_id, profile_text, now),
        )
    conn.commit()


def _cached_result(row: dict) -> dict:
    """Build the response dict from cached row columns."""
    skills_raw = row.get("ai_required_skills") or ""
    skills = [s.strip() for s in skills_raw.split(",") if s.strip()]
    return {
        "score": row.get("ai_score"),
        "score_reason": row.get("ai_score_reason"),
        "required_skills": skills,
        "hr_email": row.get("ai_hr_email"),
        "summary": row.get("ai_jd_summary"),
        "analyzed_at": row.get("ai_analyzed_at"),
        "from_cache": True,
    }


def analyze_jd(conn: Connection, job_id: int, user_id: int,
               force: bool = False) -> dict:
    """Analyze the JD for one job. Returns the result dict.

    Caching: if ai_analyzed_at is set and force is False, returns the cached
    result without calling Gemini. Pass force=True for a re-analyze.

    Raises:
      ValueError: job not found for this user, or job has no JD text
      RuntimeError: Gemini not configured AND we'd need to call it (cache miss)
      Other exceptions from Gemini bubble up (quota exhausted, network, etc.)
    """
    row = conn.execute(
        "SELECT id, title, company, location, jd_raw_text, "
        "ai_score, ai_score_reason, ai_required_skills, ai_hr_email, "
        "ai_jd_summary, ai_analyzed_at "
        "FROM jobs WHERE id = ? AND user_id = ?",
        (job_id, user_id),
    ).fetchone()
    if not row:
        raise ValueError(
            f"Job {job_id} not found, or doesn't belong to user {user_id}."
        )
    job = dict(row)

    # Cache hit — return without needing Gemini at all. This lets the UI
    # render previously-analyzed cards even if the API key is misconfigured.
    if not force and job.get("ai_analyzed_at"):
        return _cached_result(job)

    # From here on we'll call Gemini, so it must be configured.
    if not llm_helpers.is_available():
        raise RuntimeError(
            "Gemini API not configured. Set GEMINI_API_KEY env var."
        )

    # JD must be fetched before we can analyze
    jd_text = (job.get("jd_raw_text") or "").strip()
    if not jd_text:
        raise ValueError(
            "No JD text on this job yet. The Gmail sync usually fetches the "
            "JD automatically. If it hasn't, try Re-fetch JD from the card "
            "or open the original posting first."
        )

    # Cap JD at 10K chars to keep the Gemini call cheap. Most JDs are 3-6K;
    # the truncation only kicks in for unusually long career-page docs.
    jd_for_prompt = jd_text[:10000]
    profile_text = load_profile_text(conn, user_id)

    user_content = (
        f"# Candidate Profile\n{profile_text}\n\n"
        f"# Job Description\n"
        f"Title: {job.get('title') or 'unknown'}\n"
        f"Company: {job.get('company') or 'unknown'}\n"
        f"Location: {job.get('location') or 'unknown'}\n\n"
        f"{jd_for_prompt}"
    )

    analysis = llm_helpers.gemini_json(
        JD_ANALYSIS_PROMPT,
        user_content,
        schema=JDAnalysis,
        temperature=0.2,
    )

    # Coerce unexpected score values to MAYBE (safe middle bucket). Gemini
    # almost always respects the rubric, but enums-via-string isn't strictly
    # enforced by the schema layer, so we belt-and-braces here.
    score = analysis.score if analysis.score in VALID_SCORES else "MAYBE"
    skills = analysis.required_skills[:8]
    skills_str = ",".join(s.strip() for s in skills if s and s.strip())

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    conn.execute(
        "UPDATE jobs SET ai_score = ?, ai_score_reason = ?, "
        "ai_required_skills = ?, ai_hr_email = ?, ai_jd_summary = ?, "
        "ai_analyzed_at = ? WHERE id = ? AND user_id = ?",
        (score, analysis.score_reason, skills_str,
         analysis.hr_email, analysis.summary, now, job_id, user_id),
    )
    conn.commit()

    return {
        "score": score,
        "score_reason": analysis.score_reason,
        "required_skills": [s for s in skills if s],
        "hr_email": analysis.hr_email,
        "summary": analysis.summary,
        "analyzed_at": now,
        "from_cache": False,
    }
