from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class ExtractedField(Base):
    """One extraction result for one element on one document.

    This row is never overwritten/deleted after a QA correction - the
    correction is recorded additively in AbstractorCorrection so the audit
    trail (model output vs. human-corrected) survives. `extraction_method`
    and `confidence` are always set together.
    """

    __tablename__ = "extracted_fields"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    document_id: Mapped[str] = mapped_column(
        String, ForeignKey("source_documents.id"), nullable=False, index=True
    )
    element_name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    extraction_method: Mapped[str] = mapped_column(String, nullable=False)
    # "straight_through" | "pending_qa"
    status: Mapped[str] = mapped_column(String, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False, default="")
