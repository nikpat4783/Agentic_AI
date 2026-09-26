"""Regression tests for two review-driven fixes:

1. POST /qa/{field_id}/correct rejects correcting a field that isn't
   pending_qa, and rejects a second correction on an already-corrected
   field, instead of silently accepting either.
2. POST /documents/{id}/extract picks up a DataElementSpec added *after*
   a document's first extraction, rather than permanently freezing that
   document's field set to whatever specs existed at first-extract time.
"""
from __future__ import annotations

from app.db import SessionLocal
from app.models import DataElementSpec


def test_correct_rejects_field_not_pending_qa(client):
    doc = client.post(
        "/documents", json={"doc_type": "discharge_summary", "content": "Diagnosis I21.4. Discharged home."}
    ).json()
    fields = client.post(f"/documents/{doc['document_id']}/extract", json={}).json()["fields"]
    straight_through = next(f for f in fields if f["status"] == "straight_through")

    resp = client.post(
        f"/qa/{straight_through['field_id']}/correct",
        json={"corrected_value": "X", "abstractor_id": "ab_1"},
    )
    assert resp.status_code == 409


def test_correct_rejects_duplicate_correction(client):
    doc = client.post(
        "/documents", json={"doc_type": "discharge_summary", "content": "No extractable diagnosis here."}
    ).json()
    fields = client.post(f"/documents/{doc['document_id']}/extract", json={}).json()["fields"]
    pending = next(f for f in fields if f["status"] == "pending_qa")

    first = client.post(f"/qa/{pending['field_id']}/correct", json={"corrected_value": "A", "abstractor_id": "ab_1"})
    assert first.status_code == 200

    second = client.post(f"/qa/{pending['field_id']}/correct", json={"corrected_value": "B", "abstractor_id": "ab_1"})
    assert second.status_code == 409


def test_extract_picks_up_spec_added_after_first_extraction(client):
    # A private doc_type with no seeded specs, so this test can't be
    # polluted by (or pollute) the shared discharge_summary/cath_report
    # doc_types other tests in this session-scoped DB rely on.
    doc_type = "test_reextraction_doc_type"

    doc = client.post("/documents", json={"doc_type": doc_type, "content": "irrelevant content"}).json()
    document_id = doc["document_id"]

    first_fields = client.post(f"/documents/{document_id}/extract", json={}).json()["fields"]
    assert first_fields == []

    db = SessionLocal()
    try:
        db.add(
            DataElementSpec(
                element_name="test_late_added_element",
                doc_type=doc_type,
                strategy="rule",
                requires_llm=False,
                threshold=0.9,
                spec_text_path="app/rag/specs/primary_diagnosis_code.md",
            )
        )
        db.commit()
    finally:
        db.close()

    second_fields = client.post(f"/documents/{document_id}/extract", json={}).json()["fields"]
    assert {f["element_name"] for f in second_fields} == {"test_late_added_element"}

    # Re-extracting again must not duplicate the field it already resolved.
    third_fields = client.post(f"/documents/{document_id}/extract", json={}).json()["fields"]
    assert {f["field_id"] for f in third_fields} == {f["field_id"] for f in second_fields}
