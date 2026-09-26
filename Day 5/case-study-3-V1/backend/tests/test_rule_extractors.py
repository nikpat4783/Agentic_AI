"""Deterministic regex rule-extractor tests. No network, no DB."""
from app.extraction.rule_extractors import (
    extract_primary_diagnosis_code,
    extract_troponin_level,
)


def test_troponin_level_matches_value_and_unit():
    text = "Labs: Troponin 0.04 ng/mL on admission, repeat trending downward."
    result = extract_troponin_level(text)
    assert result["value"] == "0.04 ng/mL"
    assert result["raw_confidence"] > 0.9
    assert result["error"] is None


def test_troponin_level_alternate_unit():
    text = "Troponin I level: 1.2 ug/L drawn at 0200."
    result = extract_troponin_level(text)
    assert result["value"] == "1.2 ug/L"


def test_troponin_level_no_match_returns_none_not_raise():
    result = extract_troponin_level("No cardiac labs were drawn during this visit.")
    assert result == {"value": None, "raw_confidence": 0.0, "error": None}


def test_primary_diagnosis_code_matches_icd10_shape():
    text = "Primary diagnosis: I21.4 (Non-ST elevation myocardial infarction)."
    result = extract_primary_diagnosis_code(text)
    assert result["value"] == "I21.4"
    assert result["raw_confidence"] > 0.9


def test_primary_diagnosis_code_bare_three_digit_code():
    text = "Discharge diagnosis code I50.9 congestive heart failure."
    result = extract_primary_diagnosis_code(text)
    assert result["value"] == "I50.9"


def test_primary_diagnosis_code_no_match_returns_none_not_raise():
    result = extract_primary_diagnosis_code("Patient discharged in stable condition.")
    assert result == {"value": None, "raw_confidence": 0.0, "error": None}
