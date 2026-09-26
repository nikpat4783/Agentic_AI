"""Fixture-based end-to-end test: ingest a sample cath_report and a sample
discharge_summary through extract -> some straight-through/some queued ->
correct the queued ones -> build submission.

The LLM extractor call is monkeypatched so this test never makes a real
network call, per the brief. Rule extractors and the RAG retriever run for
real against the real spec files.
"""
from __future__ import annotations

from app.extraction import llm_extractor

from .conftest import read_fixture

# Deliberately mixed confidences so each document has both a
# straight-through and a pending_qa llm-strategy field.
_MOCK_LLM_RESULTS = {
    "ejection_fraction": {"value": "35", "raw_confidence": 0.9, "extraction_method": "llm", "error": None},
    "stenosis_severity": {"value": "severe", "raw_confidence": 0.4, "extraction_method": "llm", "error": None},
    "discharge_disposition": {"value": "home", "raw_confidence": 0.4, "extraction_method": "llm", "error": None},
}


def _fake_llm_extract(element_name, document_text, spec_text, api_key, model=None, base_url=None):
    assert api_key == "fake-byok-key"  # BYOK key was threaded through, never silently dropped
    return dict(_MOCK_LLM_RESULTS[element_name])


def test_full_pipeline_ingest_extract_qa_submit(client, monkeypatch):
    monkeypatch.setattr(llm_extractor, "extract", _fake_llm_extract)

    cath_text = read_fixture("sample_cath_report.txt")
    discharge_text = read_fixture("sample_discharge_summary.txt")

    cath_doc = client.post("/documents", json={"doc_type": "cath_report", "content": cath_text}).json()
    discharge_doc = client.post(
        "/documents", json={"doc_type": "discharge_summary", "content": discharge_text}
    ).json()
    cath_id = cath_doc["document_id"]
    discharge_id = discharge_doc["document_id"]

    extract_body = {"llm_api_key": "fake-byok-key"}
    cath_fields = client.post(f"/documents/{cath_id}/extract", json=extract_body).json()["fields"]
    discharge_fields = client.post(f"/documents/{discharge_id}/extract", json=extract_body).json()["fields"]

    cath_by_element = {f["element_name"]: f for f in cath_fields}
    discharge_by_element = {f["element_name"]: f for f in discharge_fields}

    # Rule elements: deterministic straight-through given the fixture text.
    assert cath_by_element["troponin_level"]["status"] == "straight_through"
    assert cath_by_element["troponin_level"]["value"] == "0.04 ng/mL"
    assert discharge_by_element["primary_diagnosis_code"]["status"] == "straight_through"
    assert discharge_by_element["primary_diagnosis_code"]["value"] == "I21.4"

    # LLM elements: mocked confidences split straight-through vs. queued.
    assert cath_by_element["ejection_fraction"]["status"] == "straight_through"
    assert cath_by_element["ejection_fraction"]["value"] == "35"
    assert cath_by_element["stenosis_severity"]["status"] == "pending_qa"
    assert discharge_by_element["discharge_disposition"]["status"] == "pending_qa"

    # Idempotent re-extraction: calling extract again returns the same
    # persisted fields rather than duplicating rows.
    cath_fields_again = client.post(f"/documents/{cath_id}/extract", json=extract_body).json()["fields"]
    assert {f["field_id"] for f in cath_fields_again} == {f["field_id"] for f in cath_fields}

    # GET /documents/{id}/fields reads persisted state (idempotent, no re-extraction).
    fields_from_get = client.get(f"/documents/{cath_id}/fields").json()
    assert {f["field_id"] for f in fields_from_get} == {f["field_id"] for f in cath_fields}

    # QA queue contains exactly the two pending fields (and not the resolved ones).
    queue = client.get("/qa/queue").json()
    queue_field_ids = {item["field_id"] for item in queue}
    stenosis_field_id = cath_by_element["stenosis_severity"]["field_id"]
    disposition_field_id = discharge_by_element["discharge_disposition"]["field_id"]
    assert stenosis_field_id in queue_field_ids
    assert disposition_field_id in queue_field_ids
    straight_through_ids = {
        cath_by_element["troponin_level"]["field_id"],
        cath_by_element["ejection_fraction"]["field_id"],
        discharge_by_element["primary_diagnosis_code"]["field_id"],
    }
    assert straight_through_ids.isdisjoint(queue_field_ids)

    # Submission blocked until QA-corrected.
    blocked = client.post(f"/documents/{cath_id}/submission")
    assert blocked.status_code == 409

    # Correct the queued fields.
    correct1 = client.post(
        f"/qa/{stenosis_field_id}/correct",
        json={"corrected_value": "severe", "abstractor_id": "ab_1"},
    )
    assert correct1.status_code == 200
    correct2 = client.post(
        f"/qa/{disposition_field_id}/correct",
        json={"corrected_value": "home", "abstractor_id": "ab_1"},
    )
    assert correct2.status_code == 200

    # Corrected fields drop out of the QA queue.
    queue_after = client.get("/qa/queue").json()
    queue_after_ids = {item["field_id"] for item in queue_after}
    assert stenosis_field_id not in queue_after_ids
    assert disposition_field_id not in queue_after_ids

    # Submissions now succeed for both documents.
    cath_submission = client.post(f"/documents/{cath_id}/submission")
    assert cath_submission.status_code == 200
    cath_record = cath_submission.json()["record"]
    assert cath_record == {
        "ejection_fraction": "35",
        "stenosis_severity": "severe",
        "troponin_level": "0.04 ng/mL",
    }

    discharge_submission = client.post(f"/documents/{discharge_id}/submission")
    assert discharge_submission.status_code == 200
    discharge_record = discharge_submission.json()["record"]
    assert discharge_record == {
        "primary_diagnosis_code": "I21.4",
        "discharge_disposition": "home",
    }

    # Accuracy audit: sane aggregate numbers per document.
    cath_audit = client.get(f"/documents/{cath_id}/accuracy-audit").json()
    assert cath_audit["total_fields"] == 3
    assert cath_audit["straight_through_count"] == 2
    assert cath_audit["qa_count"] == 1
    assert cath_audit["straight_through_rate"] == 2 / 3

    discharge_audit = client.get(f"/documents/{discharge_id}/accuracy-audit").json()
    assert discharge_audit["total_fields"] == 2
    assert discharge_audit["straight_through_count"] == 1
    assert discharge_audit["qa_count"] == 1
    assert discharge_audit["straight_through_rate"] == 0.5
