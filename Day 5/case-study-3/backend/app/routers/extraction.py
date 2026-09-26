"""POST /documents/{id}/extract, GET /documents/{id}/fields,
GET /documents/{id}/accuracy-audit."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.extraction.confidence import resolve_field
from app.metrics import record_confidence, record_field
from app.models import DataElementSpec, ExtractedField, SourceDocument
from app.schemas import AccuracyAudit, ExtractRequest, ExtractResponse, FieldOut

router = APIRouter(tags=["extraction"])


def _field_to_out(field: ExtractedField) -> FieldOut:
    return FieldOut(
        field_id=field.id,
        element_name=field.element_name,
        value=field.value,
        confidence=field.confidence,
        extraction_method=field.extraction_method,
        status=field.status,
        rationale=field.rationale,
    )


def _get_document_or_404(db: Session, document_id: str) -> SourceDocument:
    doc = db.get(SourceDocument, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail=f"document '{document_id}' not found")
    return doc


@router.post("/documents/{document_id}/extract", response_model=ExtractResponse)
def extract_document(
    document_id: str,
    payload: ExtractRequest | None = None,
    db: Session = Depends(get_db),
) -> ExtractResponse:
    doc = _get_document_or_404(db, document_id)
    payload = payload or ExtractRequest()

    # Idempotent per element, not per document: re-running extract must never
    # duplicate a row for an element already resolved (that would corrupt the
    # QA queue and submission-build precondition), but it must still pick up
    # any DataElementSpec added for this doc_type *after* the first extract
    # call -- otherwise a document extracted before a new element existed
    # could never satisfy the submission precondition again (SPEC.md KPI 7
    # promises adding an element is a config change, not a per-document one).
    existing = (
        db.query(ExtractedField).filter(ExtractedField.document_id == document_id).all()
    )
    existing_element_names = {f.element_name for f in existing}

    specs = db.query(DataElementSpec).filter(DataElementSpec.doc_type == doc.doc_type).all()
    new_specs = [s for s in specs if s.element_name not in existing_element_names]

    new_fields: list[ExtractedField] = []
    for spec in new_specs:
        resolved = resolve_field(
            spec,
            doc.content,
            llm_api_key=payload.llm_api_key,
            llm_model=payload.llm_model,
            llm_base_url=payload.llm_base_url,
        )
        field = ExtractedField(document_id=document_id, **resolved)
        db.add(field)
        new_fields.append(field)
        record_field(resolved["status"], resolved["element_name"])
        record_confidence(resolved["confidence"], resolved["element_name"])

    if new_fields:
        db.commit()
        for field in new_fields:
            db.refresh(field)

    all_fields = existing + new_fields
    return ExtractResponse(document_id=document_id, fields=[_field_to_out(f) for f in all_fields])


@router.get("/documents/{document_id}/fields", response_model=list[FieldOut])
def get_fields(document_id: str, db: Session = Depends(get_db)) -> list[FieldOut]:
    _get_document_or_404(db, document_id)
    fields = db.query(ExtractedField).filter(ExtractedField.document_id == document_id).all()
    return [_field_to_out(f) for f in fields]


@router.get("/documents/{document_id}/accuracy-audit", response_model=AccuracyAudit)
def accuracy_audit(document_id: str, db: Session = Depends(get_db)) -> AccuracyAudit:
    _get_document_or_404(db, document_id)
    fields = db.query(ExtractedField).filter(ExtractedField.document_id == document_id).all()
    total = len(fields)
    straight_through = sum(1 for f in fields if f.status == "straight_through")
    qa = sum(1 for f in fields if f.status == "pending_qa")
    rate = (straight_through / total) if total else 0.0
    return AccuracyAudit(
        straight_through_rate=rate,
        total_fields=total,
        straight_through_count=straight_through,
        qa_count=qa,
    )
