"""Deterministic regex-based extractors, one function per rule element.

Each function takes the full document text and returns a dict:
    {"value": str | None, "raw_confidence": float, "error": str | None}
Never raises - a non-match returns value=None / raw_confidence=0.0 rather
than an exception, so one bad field never fails the whole document.
"""
from __future__ import annotations

import re

_TROPONIN_RE = re.compile(
    r"troponin(?:\s+\w+)?\s*(?:level)?\s*:?\s*(?P<num>\d+(?:\.\d+)?)\s*(?P<unit>ng/mL|ug/L|mcg/L)",
    re.IGNORECASE,
)

_ICD10_RE = re.compile(r"\b(?P<code>[A-Za-z]\d{2}(?:\.\d+)?)\b")


def extract_troponin_level(text: str) -> dict:
    try:
        match = _TROPONIN_RE.search(text)
        if not match:
            return {"value": None, "raw_confidence": 0.0, "error": None}
        value = f"{match.group('num')} {match.group('unit')}"
        return {"value": value, "raw_confidence": 0.95, "error": None}
    except Exception as exc:  # pragma: no cover - regex on str can't really raise
        return {"value": None, "raw_confidence": 0.0, "error": str(exc)}


def extract_primary_diagnosis_code(text: str) -> dict:
    try:
        match = _ICD10_RE.search(text)
        if not match:
            return {"value": None, "raw_confidence": 0.0, "error": None}
        return {"value": match.group("code").upper(), "raw_confidence": 0.95, "error": None}
    except Exception as exc:  # pragma: no cover
        return {"value": None, "raw_confidence": 0.0, "error": str(exc)}


# Dict keyed by element_name, as required by the registry dispatch contract.
RULE_EXTRACTORS = {
    "troponin_level": extract_troponin_level,
    "primary_diagnosis_code": extract_primary_diagnosis_code,
}
