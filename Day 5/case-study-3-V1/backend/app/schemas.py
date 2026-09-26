"""Shared Pydantic response/request shapes used across routers.

Kept in one place (rather than duplicated per-router) since several of
these are used by more than one router (e.g. FieldOut by both extraction.py
and qa.py).
"""
from __future__ import annotations

from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str


class LogoutResponse(BaseModel):
    status: str


class SpecOut(BaseModel):
    element_name: str
    doc_type: str
    strategy: str
    requires_llm: bool
    threshold: float


class FieldOut(BaseModel):
    field_id: str
    element_name: str
    value: str | None
    confidence: float
    extraction_method: str
    status: str
    rationale: str
    # Additive: `status` never flips after a QA correction (only a separate
    # AbstractorCorrection row records that), so `resolved` is the one
    # boolean a frontend consumer can rely on for "this field's current
    # value is final" - true when status == "straight_through" OR the field
    # has a correction on file. `status` itself keeps its original meaning.
    resolved: bool


class ExtractRequest(BaseModel):
    llm_api_key: str | None = None
    llm_model: str | None = None
    llm_base_url: str | None = None


class ExtractResponse(BaseModel):
    document_id: str
    fields: list[FieldOut]


class QAQueueItem(BaseModel):
    field_id: str
    document_id: str
    element_name: str
    current_value: str | None
    confidence: float
    rationale: str
    source_excerpt: str


class CorrectRequest(BaseModel):
    corrected_value: str
    abstractor_id: str


class CorrectResponse(BaseModel):
    field_id: str
    status: str


class SubmissionResponse(BaseModel):
    submission_id: str
    status: str
    record: dict[str, str | None]


class AccuracyAudit(BaseModel):
    straight_through_rate: float
    total_fields: int
    straight_through_count: int
    qa_count: int
