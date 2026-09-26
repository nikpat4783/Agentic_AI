"""POST /documents/{document_id}/submission.

A SubmissionRecord can only be built once every field for the document is
either straight_through or has an AbstractorCorrection - never build a
partial submission silently (see .claude/agents/backend.md).
"""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import DataElementSpec, ExtractedField, SourceDocument, SubmissionRecord, latest_by_field
from app.schemas import SubmissionResponse

router = APIRouter(tags=["submissions"])


@router.post("/documents/{document_id}/submission", response_model=SubmissionResponse)
def build_submission(document_id: str, db: Session = Depends(get_db)) -> SubmissionResponse:
    doc = db.get(SourceDocument, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail=f"document '{document_id}' not found")

    # Idempotent: if this document already has a SubmissionRecord, return it
    # rather than inserting a duplicate row with identical record_json.
    existing_submission = (
        db.query(SubmissionRecord)
        .filter(SubmissionRecord.document_id == document_id)
        .order_by(SubmissionRecord.created_at.desc())
        .first()
    )
    if existing_submission is not None:
        return SubmissionResponse(
            submission_id=existing_submission.id,
            status=existing_submission.status,
            record=json.loads(existing_submission.record_json),
        )

    specs = db.query(DataElementSpec).filter(DataElementSpec.doc_type == doc.doc_type).all()
    fields = db.query(ExtractedField).filter(ExtractedField.document_id == document_id).all()
    fields_by_element = {f.element_name: f for f in fields}
    corrections_by_field = latest_by_field(db, [f.id for f in fields])

    unresolved: list[str] = []
    record: dict[str, str | None] = {}

    for spec in specs:
        field = fields_by_element.get(spec.element_name)
        if field is None:
            unresolved.append(spec.element_name)
            continue

        correction = corrections_by_field.get(field.id)
        if correction is not None:
            record[spec.element_name] = correction.corrected_value
        elif field.status == "straight_through":
            record[spec.element_name] = field.value
        else:
            unresolved.append(spec.element_name)

    if unresolved:
        raise HTTPException(
            status_code=409,
            detail=f"unresolved fields: [{', '.join(unresolved)}]",
        )

    submission = SubmissionRecord(
        document_id=document_id,
        status="submission_ready",
        record_json=json.dumps(record),
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    return SubmissionResponse(
        submission_id=submission.id,
        status=submission.status,
        record=record,
    )
