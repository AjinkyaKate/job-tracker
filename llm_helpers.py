"""LLM helpers used by Add Job, Resume Studio, and DM Generator features.

Single source of truth for Gemini call wiring so each feature shares the same
SDK setup, error handling, and rate-limit awareness. Reuses GEMINI_API_KEY env
var already configured for Gmail sync.
"""
import os
from typing import Optional, Any

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

try:
    from google import genai
    from google.genai import types as genai_types
    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False


def is_available() -> bool:
    return _GENAI_AVAILABLE and bool(GEMINI_API_KEY)


def gemini_text(system_prompt: str, user_content: str,
                model: str = "gemini-2.0-flash-lite-001",
                temperature: float = 0.3) -> str:
    """Call Gemini for unstructured text output. Returns plain string.

    Raises on any error (caller handles + surfaces in UI). Use this for
    resume-tailoring, DM-drafting, and JD-summarising where we want
    natural-language output, not structured JSON.
    """
    if not is_available():
        raise RuntimeError("GEMINI_API_KEY not configured — set env var on Render")
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model=model,
        contents=[user_content],
        config=genai_types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature,
        ),
    )
    return response.text or ""


def gemini_json(system_prompt: str, user_content: str, schema: Any,
                model: str = "gemini-2.0-flash-lite-001",
                temperature: float = 0.2) -> Any:
    """Call Gemini with a Pydantic-model response schema. Returns parsed object."""
    if not is_available():
        raise RuntimeError("GEMINI_API_KEY not configured — set env var on Render")
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model=model,
        contents=[user_content],
        config=genai_types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_schema=schema,
            temperature=temperature,
        ),
    )
    if getattr(response, "parsed", None) is not None:
        return response.parsed
    # Fallback: parse manually
    import json
    return json.loads(response.text)
