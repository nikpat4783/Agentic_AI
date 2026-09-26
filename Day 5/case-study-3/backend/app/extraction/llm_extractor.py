"""Generic LLM-backed extractor for narrative fields.

Given the document text, the element's RAG-retrieved spec text, and BYOK
credentials, makes an OpenAI-compatible chat-completion HTTP call asking the
model to extract the field value and self-report a 0-1 confidence, parsed
from a structured JSON response.

Hard requirement (see .claude/agents/backend.md): this function must NEVER
raise. Any HTTP/parse failure returns confidence=0.0,
extraction_method="llm_error" (a key was supplied but the call failed).
The "no key supplied" case (extraction_method="llm_unavailable") is handled
one layer up, in registry.py, so this module is never even invoked without
a key.

BYOK: `api_key` is a plain function parameter for this one call only. It is
never logged, never persisted, and never included in the returned dict.
"""
from __future__ import annotations

import json
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a clinical data abstraction assistant. You are given a source "
    "document excerpt and a specification for one data element. Extract the "
    "single value of that data element from the document, following the "
    "spec's valid value format exactly. Respond with ONLY a JSON object of "
    'the form {"value": <string or null>, "confidence": <float 0-1>, '
    '"source_phrase": <string or null>}.\n\n'
    'Set "value" to null if the element is not mentioned in the document - '
    "never guess or infer a plausible-sounding value that isn't actually "
    "stated.\n\n"
    'Set "source_phrase" to the exact substring of the document that '
    "supports the extracted value (e.g. \"LVEF estimated at 35%\"), so a "
    "human reviewer can verify the extraction against the source without "
    "re-reading the whole document. Null if value is null.\n\n"
    'Calibrate "confidence" using this rule, not vibes: use >=0.85 only when '
    "the value is stated explicitly and unambiguously in a format matching "
    "the spec; use 0.5-0.84 when the value is present but requires minor "
    "interpretation (e.g. a synonym, an inferred unit, one of several "
    "candidate mentions); use <0.5 when the value is only weakly implied, "
    "contradicted elsewhere in the text, or you are guessing."
)


def _build_messages(element_name: str, document_text: str, spec_text: str) -> list[dict]:
    user_prompt = (
        f"Data element: {element_name}\n\n"
        f"Specification:\n{spec_text}\n\n"
        f"Source document:\n{document_text}\n\n"
        "Return only the JSON object described in the system prompt."
    )
    return [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def _parse_response_json(payload: dict) -> dict:
    content = payload["choices"][0]["message"]["content"]
    parsed = json.loads(content)
    value = parsed.get("value")
    confidence = float(parsed.get("confidence", 0.0))
    confidence = max(0.0, min(1.0, confidence))
    return {
        "value": value,
        "raw_confidence": confidence,
        "extraction_method": "llm",
        "error": None,
        "source_phrase": parsed.get("source_phrase"),
    }


def extract(
    element_name: str,
    document_text: str,
    spec_text: str,
    api_key: str,
    model: str | None = None,
    base_url: str | None = None,
) -> dict:
    """Never raises. Returns a dict with value/raw_confidence/extraction_method/error."""
    model = model or settings.default_llm_model
    base_url = base_url or settings.default_llm_base_url

    try:
        messages = _build_messages(element_name, document_text, spec_text)
        body = {
            "model": model,
            "messages": messages,
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=settings.llm_timeout_seconds) as client:
            response = client.post(base_url, headers=headers, json=body)
        response.raise_for_status()
        payload = response.json()
        return _parse_response_json(payload)
    except Exception as exc:
        # Never let a bad LLM call fail the whole document extraction, and
        # never persist/log the exception's full str() - only its type name.
        # This "error" value flows into ExtractedField.rationale (persisted
        # + returned in API responses), so it must never carry anything an
        # httpx exception's message could conceivably echo back (request
        # URL, headers) even though the api_key itself is passed via the
        # Authorization header, never string-interpolated into a URL here.
        logger.warning("llm_extractor failed for element=%s error=%s", element_name, type(exc).__name__)
        return {
            "value": None,
            "raw_confidence": 0.0,
            "extraction_method": "llm_error",
            "error": f"{type(exc).__name__} calling the LLM provider",
        }
