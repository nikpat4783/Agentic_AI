"""Pluggable extractor registry.

Dispatches purely off `DataElementSpec.strategy` ("rule" | "llm"). Adding a
new data element (a new DataElementSpec row + a spec text file) must never
require touching this file - only a genuinely new extraction *strategy*
would.
"""
from __future__ import annotations

from app.extraction import llm_extractor, rule_extractors
from app.rag.retriever import retrieve_spec_excerpt


def run_extraction(
    spec,
    document_text: str,
    llm_api_key: str | None = None,
    llm_model: str | None = None,
    llm_base_url: str | None = None,
) -> dict:
    """Returns {"value", "raw_confidence", "extraction_method", "error"}.

    Never raises - each branch is responsible for catching its own errors
    (rule_extractors functions already do; llm_extractor.extract already
    does), so a single bad field can never fail the whole document.
    """
    # Retrieved once here (not again in confidence.py) - every branch below
    # needs it for the rationale, and the llm branch also needs it for the
    # prompt, so fetching it once per field halves RAG/Chroma query volume
    # versus each caller retrieving its own copy.
    spec_excerpt = retrieve_spec_excerpt(spec.element_name)

    if spec.strategy == "rule":
        fn = rule_extractors.RULE_EXTRACTORS.get(spec.element_name)
        if fn is None:
            return {
                "value": None,
                "raw_confidence": 0.0,
                "extraction_method": "rule",
                "error": f"no rule extractor registered for element '{spec.element_name}'",
                "spec_excerpt": spec_excerpt,
            }
        result = fn(document_text)
        return {**result, "extraction_method": "rule", "spec_excerpt": spec_excerpt}

    if spec.strategy == "llm":
        # Cost-control guard (SPEC.md KPI 8): only requires_llm elements may
        # ever reach llm_extractor, and only when a key was actually supplied.
        if not spec.requires_llm:
            return {
                "value": None,
                "raw_confidence": 0.0,
                "extraction_method": "llm_unavailable",
                "error": "element is not marked requires_llm; refusing LLM call",
                "spec_excerpt": spec_excerpt,
            }
        if not llm_api_key:
            return {
                "value": None,
                "raw_confidence": 0.0,
                "extraction_method": "llm_unavailable",
                "error": None,
                "spec_excerpt": spec_excerpt,
            }
        result = llm_extractor.extract(
            element_name=spec.element_name,
            document_text=document_text,
            spec_text=spec_excerpt,
            api_key=llm_api_key,
            model=llm_model,
            base_url=llm_base_url,
        )
        return {**result, "spec_excerpt": spec_excerpt}

    return {
        "value": None,
        "raw_confidence": 0.0,
        "extraction_method": "unknown_strategy",
        "error": f"unknown extraction strategy '{spec.strategy}'",
        "spec_excerpt": spec_excerpt,
    }
