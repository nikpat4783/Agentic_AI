from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.db import Base


class AbstractorCorrection(Base):
    """Additive-only correction record for one ExtractedField.

    Never overwrites or deletes the original ExtractedField row.
    """

    __tablename__ = "abstractor_corrections"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    field_id: Mapped[str] = mapped_column(
        String, ForeignKey("extracted_fields.id"), nullable=False, index=True
    )
    abstractor_id: Mapped[str] = mapped_column(String, nullable=False)
    corrected_value: Mapped[str] = mapped_column(Text, nullable=False)
    corrected_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


def latest_by_field(db: Session, field_ids: list[str]) -> dict[str, "AbstractorCorrection"]:
    """Fetches every AbstractorCorrection for the given field_ids in one
    query and reduces it to the latest (by corrected_at) row per field_id.

    Shared by qa.py (corrected-ids check), submissions.py (record-building),
    and extraction.py (the `resolved` flag on FieldOut) so the "latest
    correction wins" reduction logic lives in exactly one place.
    """
    if not field_ids:
        return {}
    corrections = (
        db.query(AbstractorCorrection)
        .filter(AbstractorCorrection.field_id.in_(field_ids))
        .all()
    )
    latest: dict[str, AbstractorCorrection] = {}
    for correction in corrections:
        current = latest.get(correction.field_id)
        if current is None or correction.corrected_at > current.corrected_at:
            latest[correction.field_id] = correction
    return latest
