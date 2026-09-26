"""Confidence-routing threshold logic tests.

Uses lightweight fake DataElementSpec-shaped objects (no DB needed) and
monkeypatches the LLM extractor where a test needs to control its raw
confidence - never a real network call.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.extraction import llm_extractor
from app.extraction.confidence import resolve_field


def make_spec(element_name, strategy, requires_llm, threshold):
    return SimpleNamespace(
        element_name=element_name,
        strategy=strategy,
        requires_llm=requires_llm,
        threshold=threshold,
    )


def test_rule_extraction_above_threshold_is_straight_through():
    spec = make_spec("troponin_level", "rule", False, 0.9)
    result = resolve_field(spec, "Troponin 0.04 ng/mL on admission.")
    assert result["extraction_method"] == "rule"
    assert result["value"] == "0.04 ng/mL"
    assert result["confidence"] >= spec.threshold
    assert result["status"] == "straight_through"


def test_rule_extraction_no_match_is_queued_for_qa():
    spec = make_spec("troponin_level", "rule", False, 0.9)
    result = resolve_field(spec, "Nothing relevant in this note.")
    assert result["value"] is None
    assert result["confidence"] == 0.0
    assert result["status"] == "pending_qa"


def test_llm_element_with_no_api_key_is_llm_unavailable_and_queued():
    spec = make_spec("ejection_fraction", "llm", True, 0.75)
    result = resolve_field(spec, "LVEF estimated at 35%.", llm_api_key=None)
    assert result["extraction_method"] == "llm_unavailable"
    assert result["confidence"] == 0.0
    assert result["value"] is None
    assert result["status"] == "pending_qa"


def test_llm_element_above_threshold_is_straight_through(monkeypatch):
    spec = make_spec("ejection_fraction", "llm", True, 0.75)

    def fake_extract(element_name, document_text, spec_text, api_key, model=None, base_url=None):
        return {"value": "35", "raw_confidence": 0.9, "extraction_method": "llm", "error": None}

    monkeypatch.setattr(llm_extractor, "extract", fake_extract)
    result = resolve_field(spec, "LVEF estimated at 35%.", llm_api_key="fake-key")
    assert result["value"] == "35"
    assert result["extraction_method"] == "llm"
    assert result["status"] == "straight_through"


def test_llm_element_below_threshold_is_queued_for_qa(monkeypatch):
    spec = make_spec("ejection_fraction", "llm", True, 0.75)

    def fake_extract(element_name, document_text, spec_text, api_key, model=None, base_url=None):
        return {"value": "35", "raw_confidence": 0.5, "extraction_method": "llm", "error": None}

    monkeypatch.setattr(llm_extractor, "extract", fake_extract)
    result = resolve_field(spec, "LVEF estimated at 35%.", llm_api_key="fake-key")
    assert result["value"] == "35"
    assert result["confidence"] == 0.5
    assert result["status"] == "pending_qa"


def test_llm_call_failure_never_raises_and_is_queued(monkeypatch):
    spec = make_spec("ejection_fraction", "llm", True, 0.75)

    def failing_extract(*args, **kwargs):
        return {"value": None, "raw_confidence": 0.0, "extraction_method": "llm_error", "error": "boom"}

    monkeypatch.setattr(llm_extractor, "extract", failing_extract)
    result = resolve_field(spec, "LVEF estimated at 35%.", llm_api_key="fake-key")
    assert result["extraction_method"] == "llm_error"
    assert result["status"] == "pending_qa"


def test_rule_element_never_invokes_llm_even_with_key(monkeypatch):
    """Cost-control (SPEC.md KPI 8): rule-eligible fields must never make an
    LLM call, even if a BYOK key happens to be supplied."""
    spec = make_spec("troponin_level", "rule", False, 0.9)

    def must_not_be_called(*args, **kwargs):
        raise AssertionError("llm_extractor.extract must never be called for a rule element")

    monkeypatch.setattr(llm_extractor, "extract", must_not_be_called)
    result = resolve_field(spec, "Troponin 0.04 ng/mL on admission.", llm_api_key="fake-key")
    assert result["extraction_method"] == "rule"


def test_rationale_cites_spec_excerpt():
    spec = make_spec("troponin_level", "rule", False, 0.9)
    result = resolve_field(spec, "Troponin 0.04 ng/mL on admission.")
    assert "Per spec:" in result["rationale"]
    assert "0.04 ng/mL" in result["rationale"]
    assert "rule" in result["rationale"]
