"""Submission-build precondition: rejects unresolved fields (409), and
only succeeds once every field is straight_through or corrected.

Runs against the real app/DB via the `client` fixture. No LLM API key is
supplied, so the two llm-strategy elements resolve to
extraction_method="llm_unavailable" / status="pending_qa" (never an error),
while the rule element (troponin_level) resolves straight-through - giving
a genuine mix of resolved/unresolved fields to exercise the precondition.
"""
from __future__ import annotations

CATH_TEXT = (
    "Cath report. LVEF estimated at 35%. Severe stenosis of the LAD. "
    "Troponin 0.04 ng/mL on admission."
)


def test_submission_rejects_unresolved_then_succeeds_after_correction(client):
    doc_resp = client.post("/documents", json={"doc_type": "cath_report", "content": CATH_TEXT})
    assert doc_resp.status_code == 200
    document_id = doc_resp.json()["document_id"]

    extract_resp = client.post(f"/documents/{document_id}/extract", json={})
    assert extract_resp.status_code == 200
    fields = extract_resp.json()["fields"]
    assert len(fields) == 3

    pending = [f for f in fields if f["status"] == "pending_qa"]
    straight_through = [f for f in fields if f["status"] == "straight_through"]
    assert pending, "expected at least one llm_unavailable field queued for QA"
    assert straight_through, "expected the rule-based troponin_level field straight-through"
    assert all(f["extraction_method"] == "llm_unavailable" for f in pending)

    # Precondition: must reject while any field is unresolved.
    blocked_resp = client.post(f"/documents/{document_id}/submission")
    assert blocked_resp.status_code == 409
    detail = blocked_resp.json()["detail"]
    assert "unresolved fields" in detail
    for f in pending:
        assert f["element_name"] in detail

    # Resolve every pending field via QA correction.
    for f in pending:
        correct_resp = client.post(
            f"/qa/{f['field_id']}/correct",
            json={"corrected_value": "corrected-value", "abstractor_id": "ab_test"},
        )
        assert correct_resp.status_code == 200
        assert correct_resp.json()["status"] == "corrected"

    ok_resp = client.post(f"/documents/{document_id}/submission")
    assert ok_resp.status_code == 200
    body = ok_resp.json()
    assert body["status"] == "submission_ready"
    assert "submission_id" in body
    for f in pending:
        assert body["record"][f["element_name"]] == "corrected-value"
