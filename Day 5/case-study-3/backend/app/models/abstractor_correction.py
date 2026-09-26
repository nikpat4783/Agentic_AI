from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

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
