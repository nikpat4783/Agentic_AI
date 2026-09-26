"""POST /documents - ingest a source document."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import SourceDocument

router = APIRouter(tags=["documents"])


class DocumentIn(BaseModel):
    doc_type: str
    content: str


class DocumentOut(BaseModel):
    document_id: str


@router.post("/documents", response_model=DocumentOut)
def create_document(payload: DocumentIn, db: Session = Depends(get_db)) -> DocumentOut:
    doc = SourceDocument(doc_type=payload.doc_type, content=payload.content)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return DocumentOut(document_id=doc.id)
