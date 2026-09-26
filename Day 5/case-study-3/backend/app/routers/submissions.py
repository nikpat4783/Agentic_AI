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
from app.models import AbstractorCorrection, DataElementSpec, ExtractedField, SourceDocument, SubmissionRecord
from app.schemas import SubmissionResponse

router = APIRouter(tags=["submissions"])


@router.post("/documents/{document_id}/submission", response_model=SubmissionResponse)
def build_submission(document_id: str, db: Session = Depends(get_db)) -> SubmissionResponse:
    doc = db.get(SourceDocument, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail=f"document '{document_id}' not found")

    specs = db.query(DataElementSpec).filter(DataElementSpec.doc_type == doc.doc_type).all()
    fields = db.query(ExtractedField).filter(ExtractedField.document_id == document_id).all()
    fields_by_element = {f.element_name: f for f in fields}

    unresolved: list[str] = []
    record: dict[str, str | None] = {}

    for spec in specs:
        field = fields_by_element.get(spec.element_name)
        if field is None:
            unresolved.append(spec.element_name)
            continue

        corrections = (
            db.query(AbstractorCorrection)
            .filter(AbstractorCorrection.field_id == field.id)
            .order_by(AbstractorCorrection.corrected_at.desc())
            .all()
        )
        if corrections:
            record[spec.element_name] = corrections[0].corrected_value
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
