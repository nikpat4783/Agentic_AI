from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class DataElementSpec(Base):
    """Config-driven definition of one extractable data element.

    Adding a new element is a matter of inserting a row here (plus a spec
    text file under app/rag/specs/) - never a pipeline code change, per
    SPEC.md KPI 7.
    """

    __tablename__ = "data_element_specs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    element_name: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    doc_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    strategy: Mapped[str] = mapped_column(String, nullable=False)  # "rule" | "llm"
    requires_llm: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0.75)
    spec_text_path: Mapped[str] = mapped_column(String, nullable=False)
