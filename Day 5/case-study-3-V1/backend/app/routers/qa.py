"""GET /qa/queue, POST /qa/{field_id}/correct."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import AbstractorCorrection, ExtractedField, SourceDocument, latest_by_field
from app.schemas import CorrectRequest, CorrectResponse, QAQueueItem

router = APIRouter(tags=["qa"])

_SOURCE_EXCERPT_MAX_CHARS = 280


def _source_excerpt(content: str) -> str:
    text = " ".join(content.split())
    return text if len(text) <= _SOURCE_EXCERPT_MAX_CHARS else text[:_SOURCE_EXCERPT_MAX_CHARS].rstrip() + "..."


@router.get("/qa/queue", response_model=list[QAQueueItem])
def get_qa_queue(db: Session = Depends(get_db)) -> list[QAQueueItem]:
    pending = (
        db.query(ExtractedField).filter(ExtractedField.status == "pending_qa").all()
    )
    corrected_field_ids = set(latest_by_field(db, [f.id for f in pending]).keys())

    doc_ids = {f.document_id for f in pending}
    docs_by_id = {
        doc.id: doc
        for doc in db.query(SourceDocument).filter(SourceDocument.id.in_(doc_ids)).all()
    }

    items: list[QAQueueItem] = []
    for field in pending:
        if field.id in corrected_field_ids:
            continue
        doc = docs_by_id.get(field.document_id)
        excerpt = _source_excerpt(doc.content) if doc else ""
        items.append(
            QAQueueItem(
                field_id=field.id,
                document_id=field.document_id,
                element_name=field.element_name,
                current_value=field.value,
                confidence=field.confidence,
                rationale=field.rationale,
                source_excerpt=excerpt,
            )
        )
    return items


@router.post("/qa/{field_id}/correct", response_model=CorrectResponse)
def correct_field(field_id: str, payload: CorrectRequest, db: Session = Depends(get_db)) -> CorrectResponse:
    field = db.get(ExtractedField, field_id)
    if field is None:
        raise HTTPException(status_code=404, detail=f"field '{field_id}' not found")
    if field.status != "pending_qa":
        raise HTTPException(
            status_code=409,
            detail=f"field '{field_id}' is not pending QA (status='{field.status}') -- refusing to correct",
        )
    already_corrected = (
        db.query(AbstractorCorrection).filter(AbstractorCorrection.field_id == field_id).first()
    )
    if already_corrected is not None:
        raise HTTPException(
            status_code=409, detail=f"field '{field_id}' already has a correction -- refusing a duplicate"
        )

    # Additive-only: the original ExtractedField row is never modified, so
    # the audit trail (model output vs. abstractor correction) survives.
    correction = AbstractorCorrection(
        field_id=field_id,
        abstractor_id=payload.abstractor_id,
        corrected_value=payload.corrected_value,
    )
    db.add(correction)
    db.commit()

    return CorrectResponse(field_id=field_id, status="corrected")
