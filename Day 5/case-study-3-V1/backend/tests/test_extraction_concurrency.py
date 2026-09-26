"""Concurrency correctness for POST /documents/{id}/extract.

new_specs (specs not yet resolved for this document) are now resolved via a
bounded ThreadPoolExecutor rather than a sequential for-loop, since each
resolve_field() call for an llm-strategy element may make a synchronous LLM
HTTP call. This test proves the parallelization doesn't scramble or drop
results: each field must end up with the value for *its own* element_name,
and the response's field order must match the specs' order, regardless of
which worker thread finished first.

The LLM extractor call is monkeypatched (existing pattern from
tests/test_confidence.py / tests/test_e2e.py) so this test never makes a
real network call or depends on timing.
"""
from __future__ import annotations

from app.extraction import llm_extractor

from .conftest import read_fixture

# cath_report has two requires_llm=True elements (ejection_fraction,
# stenosis_severity) plus one rule element (troponin_level) -- see
# tests/test_e2e.py, which relies on the same doc_type/spec seeding.
_MOCK_LLM_RESULTS = {
    "ejection_fraction": {"value": "EF-VALUE", "raw_confidence": 0.9, "extraction_method": "llm", "error": None},
    "stenosis_severity": {"value": "STENOSIS-VALUE", "raw_confidence": 0.9, "extraction_method": "llm", "error": None},
}


def _fake_llm_extract(element_name, document_text, spec_text, api_key, model=None, base_url=None):
    # Distinct, element-keyed return value so a scrambled/dropped result
    # would surface as a wrong value in a specific slot, not just a missing
    # field.
    return dict(_MOCK_LLM_RESULTS[element_name])


def test_extract_parallel_resolution_preserves_order_and_values(client, monkeypatch):
    monkeypatch.setattr(llm_extractor, "extract", _fake_llm_extract)

    cath_text = read_fixture("sample_cath_report.txt")
    doc = client.post("/documents", json={"doc_type": "cath_report", "content": cath_text}).json()
    document_id = doc["document_id"]

    specs = client.get("/specs").json()
    cath_specs = [s for s in specs if s["doc_type"] == "cath_report"]
    expected_order = [s["element_name"] for s in cath_specs]

    resp = client.post(
        f"/documents/{document_id}/extract",
        json={"llm_api_key": "fake-byok-key"},
    )
    assert resp.status_code == 200
    fields = resp.json()["fields"]

    # Field order matches the specs' order, not LLM-call completion order.
    assert [f["element_name"] for f in fields] == expected_order

    by_element = {f["element_name"]: f for f in fields}
    assert by_element["ejection_fraction"]["value"] == "EF-VALUE"
    assert by_element["stenosis_severity"]["value"] == "STENOSIS-VALUE"
    assert by_element["ejection_fraction"]["resolved"] is True
    assert by_element["stenosis_severity"]["resolved"] is True
