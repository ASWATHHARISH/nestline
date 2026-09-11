"""Typed Stage 4 contracts for private-document processing and confirmation."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import Field, model_validator

from app.schemas.foundation import Contract, Text


DOCUMENT_SCHEMA_VERSION = "stage4-document-v1"
MAX_DOCUMENT_BYTES = 10 * 1024 * 1024


class DocumentKind(StrEnum):
    INTAKE_SUMMARY = "intake_summary"
    LAB_REPORT = "lab_report"
    MEDICATION_NOTE = "medication_note"
    VISIT_SUMMARY = "visit_summary"
    MOVEMENT_NOTE = "movement_note"
    FOLLOW_UP = "follow_up"
    DISCHARGE_SUMMARY = "discharge_summary"
    OTHER = "other"


class CandidateFactType(StrEnum):
    SUBJECT = "subject"
    JOURNEY_TIMING = "journey_timing"
    ALLERGY = "allergy"
    CONDITION = "condition"
    CLINICIAN = "clinician"
    MEDICATION = "medication"
    MEDICATION_INSTRUCTION = "medication_instruction"
    RESTRICTION = "restriction"
    APPOINTMENT = "appointment"
    TEST_RESULT = "test_result"
    FOLLOW_UP = "follow_up"
    OTHER = "other"


class SourceSpan(Contract):
    """Exact source evidence; coordinates are optional for OCR/text adapters."""

    page: int = Field(ge=1)
    exact_text: Text
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    line: int | None = Field(default=None, ge=1)
    coordinates: list[list[float]] = Field(default_factory=list)
    coordinate_system: str | None = None

    @model_validator(mode="after")
    def valid_offsets(self):
        if self.end <= self.start:
            raise ValueError("source span end must be after start")
        return self


class ParsedPage(Contract):
    page: int = Field(ge=1)
    text: str
    extraction_method: Literal["embedded_text", "ocr"]
    text_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class DocumentCandidate(Contract):
    """A proposal only. It cannot personalize anything until confirmation."""

    candidate_key: Text
    field_name: Text
    fact_type: CandidateFactType
    value: Any
    source: SourceSpan
    confidence: float = Field(ge=0, le=1)
    completeness: Literal["complete", "partial", "missing", "uncertain"]
    disposition: Literal["extract_verbatim", "abstain", "manual_review"]
    status: Literal["proposed"] = "proposed"
    record_only: bool = False
    source_value_matches: bool = True
    conflict_document_keys: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def safety_invariants(self):
        if self.completeness == "missing" and self.disposition != "abstain":
            raise ValueError("missing source values must abstain")
        if self.disposition == "abstain" and self.confidence > 0.5:
            raise ValueError("abstentions cannot claim high extraction confidence")
        if self.fact_type in {
            CandidateFactType.MEDICATION,
            CandidateFactType.MEDICATION_INSTRUCTION,
        } and not self.record_only:
            raise ValueError("medication content must remain record-only")
        return self


class ExtractionProviderTrace(Contract):
    provider: Text
    model: Text
    schema_version: Text = DOCUMENT_SCHEMA_VERSION
    trace_id: str = ""
    latency_ms: int | None = Field(default=None, ge=0)
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    estimated_cost_usd: float | None = Field(default=None, ge=0)


class DocumentExtractionPacket(Contract):
    schema_version: Literal["stage4-document-v1"] = DOCUMENT_SCHEMA_VERSION
    document_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    document_kind: DocumentKind
    classification_confidence: float = Field(ge=0, le=1)
    subject_as_written: str | None = None
    fictional: bool
    pages: list[ParsedPage] = Field(min_length=1, max_length=100)
    candidates: list[DocumentCandidate] = Field(max_length=100)
    untrusted_instruction_text: list[str] = Field(default_factory=list)
    provider_trace: ExtractionProviderTrace


class UploadValidationResult(Contract):
    original_filename: Text
    safe_filename: Text
    media_type: Literal["application/pdf", "image/png", "image/jpeg"]
    byte_size: int = Field(gt=0, le=MAX_DOCUMENT_BYTES)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    page_count: int = Field(ge=1, le=100)
    scan_status: Literal["fixture_verified", "clean"]
    scan_provider: Text
    scan_version: Text
    expected_subject: str | None = None
    subject_as_written: str | None = None
    identity_status: Literal[
        "not_required", "matched_document_subject", "verified_fixture_binding"
    ]


class ConfirmationDecision(Contract):
    candidate_key: Text
    action: Literal["confirm", "edit_and_confirm", "reject", "keep_conflict", "supersede"]
    edited_value: Any | None = None
    supersedes_fact_id: UUID | None = None

    @model_validator(mode="after")
    def action_fields_match(self):
        if (self.action == "edit_and_confirm") != (self.edited_value is not None):
            raise ValueError("edited_value is required only for edit_and_confirm")
        if (self.action == "supersede") != (self.supersedes_fact_id is not None):
            raise ValueError("supersedes_fact_id is required only for supersede")
        return self


class DocumentReviewRequest(Contract):
    workspace_id: UUID
    document_id: UUID
    expected_review_version: int = Field(ge=1)
    submission_key: str = Field(min_length=16, max_length=128)
    decisions: list[ConfirmationDecision] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def unique_candidate_decisions(self):
        keys = [item.candidate_key for item in self.decisions]
        if len(keys) != len(set(keys)):
            raise ValueError("each candidate may have only one decision")
        return self


class DocumentReviewResult(Contract):
    document_id: UUID
    review_version: int = Field(ge=1)
    confirmed_fact_ids: list[UUID] = Field(default_factory=list)
    conflict_fact_ids: list[UUID] = Field(default_factory=list)
    rejected_candidate_keys: list[str] = Field(default_factory=list)
    stale_plan_ids: list[UUID] = Field(default_factory=list)
    idempotent_replay: bool
    committed_at: datetime
