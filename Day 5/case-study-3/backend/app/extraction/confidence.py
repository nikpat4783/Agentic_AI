"""Confidence calibration + routing.

Calibrates a raw extractor score into the field's final `confidence`, cites
the RAG-retrieved spec excerpt in the rationale, and applies the
per-element threshold to decide straight_through vs. pending_qa.
"""
from __future__ import annotations

from app.extraction.registry import run_extraction


def calibrate(raw_confidence: float) -> float:
    """POC calibration layer: clamp to [0, 1].

    Kept as its own function (rather than inlined) so a real calibration
    model - normalizing scores across extraction model types per the LLD's
    confidence-calibration-service - can be dropped in later without
    touching call sites.
    """
    try:
        return max(0.0, min(1.0, float(raw_confidence)))
    except (TypeError, ValueError):
        return 0.0


def build_rationale(
    element_name: str,
    excerpt: str,
    value: str | None,
    extraction_method: str,
    confidence: float,
    error: str | None,
    source_phrase: str | None = None,
) -> str:
    value_repr = value if value is not None else "<no value extracted>"
    rationale = (
        f"Per spec: {excerpt}. Extracted '{value_repr}' via {extraction_method} "
        f"at confidence {confidence:.2f}."
    )
    if source_phrase:
        rationale += f' Source: "{source_phrase}".'
    if extraction_method == "llm_unavailable":
        rationale += " No LLM API key was supplied for this request; queued for QA."
    elif extraction_method == "llm_error":
        rationale += " The LLM call failed; queued for QA."
        if error:
            rationale += f" ({error})"
    elif value is None:
        rationale += " No match found in document; queued for QA."
    return rationale


def resolve_field(
    spec,
    document_text: str,
    llm_api_key: str | None = None,
    llm_model: str | None = None,
    llm_base_url: str | None = None,
) -> dict:
    """Runs extraction for one DataElementSpec against one document's text
    and returns the fully-resolved field dict (matching ExtractedField
    columns, minus id/document_id which the caller assigns).
    """
    raw = run_extraction(
        spec,
        document_text,
        llm_api_key=llm_api_key,
        llm_model=llm_model,
        llm_base_url=llm_base_url,
    )
    value = raw.get("value")
    extraction_method = raw.get("extraction_method", "unknown")
    error = raw.get("error")
    confidence = calibrate(raw.get("raw_confidence", 0.0))

    excerpt = raw.get("spec_excerpt", "")
    rationale = build_rationale(
        spec.element_name, excerpt, value, extraction_method, confidence, error, raw.get("source_phrase")
    )

    is_resolved_confidently = value is not None and confidence >= spec.threshold
    status = "straight_through" if is_resolved_confidently else "pending_qa"

    return {
        "element_name": spec.element_name,
        "value": value,
        "confidence": confidence,
        "extraction_method": extraction_method,
        "status": status,
        "rationale": rationale,
    }
