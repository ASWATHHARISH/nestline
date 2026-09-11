"""Stage 2 storage contracts shared by application and migration checks."""

from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field, model_validator

from app.schemas.content import Contract, Stage, Text


PUBLIC_KNOWLEDGE_TABLES = {
    "content_releases", "public_sources", "source_artifacts", "source_blocks",
    "weekly_profiles", "guidance_fragments", "guideline_chunks",
}

ADMIN_ONLY_TABLES = {
    "ingestion_runs", "evidence_review_tasks", "evidence_review_decisions",
}

USER_OWNED_TABLES = {
    "journey_states", "private_documents", "document_chunks", "document_facts",
    "health_facts", "medication_mentions", "symptom_events", "appointments",
    "appointment_questions", "plans", "plan_items", "graph_nodes", "graph_edges",
    "human_review_cases", "notifications", "feedback",
}

STAGE2_TABLES = PUBLIC_KNOWLEDGE_TABLES | ADMIN_ONLY_TABLES | USER_OWNED_TABLES | {
    "workspaces", "workspace_members",
}


class Workspace(Contract):
    id: UUID
    owner_user_id: UUID
    mode: Literal["personal_empty", "fictional_demo"]
    display_name: Text
    demo_session_key: str | None = None
    demo_seed_version: Literal["maya-v1"] | None = None
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def demo_identity_matches_mode(self):
        values = (self.demo_session_key, self.demo_seed_version)
        if self.mode == "personal_empty" and any(value is not None for value in values):
            raise ValueError("personal workspace cannot contain demo identity")
        if self.mode == "fictional_demo" and any(value is None for value in values):
            raise ValueError("fictional workspace requires session and seed identity")
        return self


class WorkspaceMember(Contract):
    workspace_id: UUID
    user_id: UUID
    role: Literal["owner"]
    created_at: datetime


class JourneyState(Contract):
    id: UUID
    workspace_id: UUID
    stage: Stage
    timing_source: Literal[
        "user_reported_possible_pregnancy",
        "document_estimated_due_date", "user_estimated_due_date",
        "manual_week_day", "approximate_month_range",
        "delivery_date", "postpartum_week",
    ]
    gestational_week: int | None = Field(default=None, ge=1, le=42)
    gestational_day: int | None = Field(default=None, ge=0, le=6)
    postpartum_week: int | None = Field(default=None, ge=1, le=12)
    postpartum_day: int | None = Field(default=None, ge=0, le=6)
    estimated_due_date: date | None = None
    delivery_date: date | None = None
    approximate_month_min: int | None = Field(default=None, ge=1, le=10)
    approximate_month_max: int | None = Field(default=None, ge=1, le=10)
    user_confirmed: bool
    has_dating_conflict: bool
    is_current: bool
    version: int = Field(ge=1)
    derived_from_fact_ids: list[UUID] = Field(default_factory=list)
    effective_date: date | None = None
    calculation_date: date | None = None
    confirmed_at: datetime | None = None
    confirmed_by_user_id: UUID | None = None
    conflicts_with_state_id: UUID | None = None
    dating_difference_days: int | None = Field(default=None, ge=0)
    onboarding_submission_key: str | None = None
    onboarding_payload_sha256: str | None = Field(
        default=None, pattern=r"^[a-f0-9]{64}$"
    )
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def timing_matches_stage_and_source(self):
        dates = (self.effective_date, self.calculation_date)
        if (dates[0] is None) != (dates[1] is None):
            raise ValueError("effective and calculation dates must be stored together")
        if dates[0] is not None and dates[0] > dates[1]:
            raise ValueError("effective date cannot follow calculation date")
        submission = (self.onboarding_submission_key, self.onboarding_payload_sha256)
        if (submission[0] is None) != (submission[1] is None):
            raise ValueError("onboarding idempotency key and payload hash must be stored together")
        conflict = (self.conflicts_with_state_id, self.dating_difference_days)
        if any(value is not None for value in conflict) and not self.has_dating_conflict:
            raise ValueError("conflict provenance requires has_dating_conflict")
        approximate = (self.approximate_month_min, self.approximate_month_max)
        if ((approximate[0] is None) != (approximate[1] is None)
                or (approximate[0] is not None and approximate[0] > approximate[1])):
            raise ValueError("approximate month range must be complete and ordered")

        if self.stage == "possible_pregnancy":
            if self.timing_source != "user_reported_possible_pregnancy" or any((
                self.gestational_week is not None,
                self.gestational_day is not None,
                self.postpartum_week is not None,
                self.postpartum_day is not None,
                self.estimated_due_date is not None,
                self.delivery_date is not None,
                self.approximate_month_min is not None,
                self.approximate_month_max is not None,
            )):
                raise ValueError("possible pregnancy cannot claim resolved timing")
            return self

        if self.stage == "pregnancy":
            if any((self.postpartum_week is not None, self.postpartum_day is not None,
                    self.delivery_date is not None)):
                raise ValueError("pregnancy state cannot contain postpartum timing")
            if self.timing_source == "manual_week_day":
                valid = (self.gestational_week is not None
                         and self.gestational_day is not None
                         and self.estimated_due_date is None
                         and self.approximate_month_min is None
                         and self.approximate_month_max is None)
            elif self.timing_source in {
                    "document_estimated_due_date", "user_estimated_due_date"}:
                valid = (self.gestational_week is not None
                         and self.gestational_day is not None
                         and self.estimated_due_date is not None
                         and self.approximate_month_min is None
                         and self.approximate_month_max is None)
            elif self.timing_source == "approximate_month_range":
                valid = (self.gestational_week is None
                         and self.gestational_day is None
                         and self.estimated_due_date is None
                         and self.approximate_month_min is not None
                         and self.approximate_month_max is not None)
            else:
                valid = False
            if not valid:
                raise ValueError("pregnancy fields do not match the timing source")
            return self

        valid = (
            self.timing_source in {"delivery_date", "postpartum_week"}
            and self.gestational_week is None
            and self.gestational_day is None
            and self.estimated_due_date is None
            and self.approximate_month_min is None
            and self.approximate_month_max is None
            and self.postpartum_week is not None
            and self.postpartum_day is not None
            and ((self.timing_source == "delivery_date")
                 == (self.delivery_date is not None))
        )
        if not valid:
            raise ValueError("postpartum fields do not match the timing source")
        return self


class PrivateDocument(Contract):
    id: UUID
    workspace_id: UUID
    storage_object_path: Text
    original_filename: Text
    media_type: Text
    byte_size: int = Field(gt=0)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    status: Literal["uploaded", "processing", "needs_confirmation", "confirmed", "failed"]
    contains_real_medical_data: bool
    failure_code: str | None = None
    fixture_document_key: str | None = Field(default=None, pattern=r"^DOC-[0-9]{3}$")
    scan_status: Literal["pending", "fixture_verified", "clean", "failed"] = "pending"
    scan_provider: str | None = None
    scan_version: str | None = None
    scan_completed_at: datetime | None = None
    document_kind: str | None = None
    classification_confidence: float | None = Field(default=None, ge=0, le=1)
    subject_as_written: str | None = None
    extraction_schema_version: str | None = None
    extraction_payload_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    extraction_provider: str | None = None
    extraction_model: str | None = None
    extraction_trace_id: str | None = None
    review_version: int = Field(default=0, ge=0)
    confirmed_at: datetime | None = None
    confirmed_by_user_id: UUID | None = None
    has_unresolved_conflicts: bool = False
    uploaded_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def governed_document_state(self):
        scan_values = (self.scan_provider, self.scan_version, self.scan_completed_at)
        if self.scan_status == "pending" and any(value is not None for value in scan_values):
            raise ValueError("pending scan cannot claim scanner provenance")
        if self.scan_status != "pending" and any(value is None for value in scan_values):
            raise ValueError("completed scan requires provider, version, and timestamp")
        if (self.confirmed_at is None) != (self.confirmed_by_user_id is None):
            raise ValueError("document confirmation provenance is incomplete")
        if self.status == "confirmed" and self.confirmed_at is None:
            raise ValueError("confirmed document requires confirmation provenance")
        return self


class DocumentChunk(Contract):
    id: UUID
    workspace_id: UUID
    document_id: UUID
    page: int | None = Field(default=None, ge=1)
    source_span: dict[str, Any]
    text: Text
    text_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    embedding_provider: str | None = None
    embedding_model: str | None = None
    embedding_dimensions: int | None = Field(default=None, gt=0)
    embedding: list[float] | None = None
    extraction_method: Literal["embedded_text", "ocr"] = "embedded_text"
    created_at: datetime

    @model_validator(mode="after")
    def embedding_matches_dimensions(self):
        if (self.embedding is None) != (self.embedding_dimensions is None):
            raise ValueError("embedding and dimensions must be present together")
        if self.embedding is not None and len(self.embedding) != self.embedding_dimensions:
            raise ValueError("embedding length must match embedding_dimensions")
        return self


class DocumentFact(Contract):
    id: UUID
    workspace_id: UUID
    document_id: UUID
    field_name: Text
    value: Any
    source_page: int | None = Field(default=None, ge=1)
    source_text: str = ""
    confidence: float = Field(ge=0, le=1)
    status: Literal["proposed", "confirmed", "rejected", "conflict", "superseded"]
    confirmed_at: datetime | None = None
    candidate_key: str | None = None
    fact_type: str | None = None
    source_span: dict[str, Any] | None = None
    completeness: Literal["complete", "partial", "missing", "uncertain"] | None = None
    disposition: Literal["extract_verbatim", "abstain", "manual_review"] | None = None
    record_only: bool = False
    source_value_matches: bool = True
    conflict_document_keys: list[str] = Field(default_factory=list)
    edited_value: Any | None = None
    decided_at: datetime | None = None
    decided_by_user_id: UUID | None = None
    committed_health_fact_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class HealthFact(Contract):
    id: UUID
    workspace_id: UUID
    fact_type: Literal[
        "allergy", "dietary_restriction", "medical_history", "medication",
        "clinician_instruction", "feeding_status", "delivery_history", "other",
    ]
    value: Any
    source_kind: Literal["user_reported", "document_extracted", "human_reviewed"]
    confirmation_status: Literal["proposed", "confirmed", "rejected", "conflict", "superseded"]
    source_document_id: UUID | None = None
    source_document_fact_id: UUID | None = None
    document_review_submission_key: str | None = None
    record_only: bool = False
    provenance: dict[str, Any] = Field(default_factory=dict)
    supersedes_fact_id: UUID | None = None
    valid_from: datetime
    valid_to: datetime | None = None
    created_at: datetime
    updated_at: datetime


class MedicationMention(Contract):
    id: UUID
    workspace_id: UUID
    document_id: UUID | None = None
    name_as_written: Text
    context_text: str = ""
    status: Literal["proposed", "confirmed", "rejected", "conflict", "superseded"]
    candidate_key: str | None = None
    decided_at: datetime | None = None
    decided_by_user_id: UUID | None = None
    created_at: datetime


class SymptomEvent(Contract):
    id: UUID
    workspace_id: UUID
    description: Text
    reported_at: datetime
    safety_route: Literal["urgent", "clarify", "no_match"]
    matched_rule_ids: list[str] = Field(default_factory=list)
    user_confirmed: bool
    input_source: Literal["onboarding", "chat", "check_in", "document"] = "onboarding"
    safety_spec_version: str | None = None
    safety_evaluation_only: bool = True
    created_at: datetime


class Appointment(Contract):
    id: UUID
    workspace_id: UUID
    scheduled_for: datetime | None = None
    scheduled_date: date | None = None
    appointment_type: str = ""
    location: str = ""
    status: Literal["planned", "confirmed", "completed", "cancelled"]
    source_fact_id: UUID | None = None
    source_document_fact_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def has_schedule_precision(self):
        if self.scheduled_for is None and self.scheduled_date is None:
            raise ValueError("appointment requires a date or timestamp")
        return self


class AppointmentQuestion(Contract):
    id: UUID
    workspace_id: UUID
    appointment_id: UUID
    question: Text
    source_fact_ids: list[UUID] = Field(default_factory=list)
    status: Literal["draft", "saved", "asked", "stale", "archived"]
    stale_reasons: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class SavedPlan(Contract):
    id: UUID
    workspace_id: UUID
    version: int = Field(ge=1)
    journey_state_id: UUID
    source_release_id: UUID
    status: Literal["draft", "user_reviewed", "saved", "active", "stale", "replaced", "archived"]
    stale_reasons: list[str] = Field(default_factory=list)
    user_confirmed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def confirmed_status_has_timestamp(self):
        if self.status in {"saved", "active"} and self.user_confirmed_at is None:
            raise ValueError("saved or active plan requires user confirmation")
        return self


class PlanItem(Contract):
    id: UUID
    workspace_id: UUID
    plan_id: UUID
    catalogue_item_id: str | None = None
    guidance_fragment_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(min_length=1)
    confirmed_fact_ids: list[UUID] = Field(default_factory=list)
    category: Literal[
        "nutrition", "movement", "wellbeing", "preparation",
        "followup", "consider", "avoid",
    ]
    title: Text
    body: Text
    state: Literal["proposed", "confirmed", "stale"]
    position: int = Field(ge=0)
    created_at: datetime
    updated_at: datetime


class GraphNode(Contract):
    id: UUID
    workspace_id: UUID
    node_type: Literal[
        "document", "fact", "restriction", "symptom",
        "appointment", "question", "plan", "plan_item", "person",
        "journey_state", "weekly_profile", "document_fact",
        "medication_mention", "allergy", "condition", "guideline_evidence",
        "human_review_case", "symptom_event",
    ]
    entity_id: UUID | None = None
    entity_release_id: UUID | None = None
    entity_key: str | None = None
    label: Text
    source_document_id: UUID | None = None
    created_at: datetime

    @model_validator(mode="after")
    def typed_entity_reference(self):
        public_type = self.node_type in {"weekly_profile", "guideline_evidence"}
        if public_type and (self.entity_id is not None or
                            self.entity_release_id is None or
                            not (self.entity_key or "").strip()):
            raise ValueError("public graph nodes require a release and text key")
        if not public_type and (self.entity_id is None or
                                self.entity_release_id is not None or
                                self.entity_key is not None):
            raise ValueError("personal graph nodes require exactly one UUID entity")
        return self


class GraphEdge(Contract):
    id: UUID
    workspace_id: UUID
    from_node_id: UUID
    to_node_id: UUID
    relation: Literal[
        "supports", "IN_WEEK", "EXTRACTED_FROM", "CONFLICTS_WITH", "SUPERSEDES",
        "CONSTRAINS", "SUPPORTED_BY", "TRIGGERED", "SCHEDULED_FOR",
        "NEEDS_CLARIFICATION", "REVIEWED_BY",
    ]
    created_at: datetime


class HumanReviewCase(Contract):
    id: UUID
    workspace_id: UUID
    state: Literal[
        "not_required", "offered", "consented", "queued", "reviewed",
        "resumed", "declined", "timed_out", "unavailable",
    ]
    reason: Text
    packet: Any | None = None
    simulated: bool = True
    consented_at: datetime | None = None
    reviewed_at: datetime | None = None
    reviewer_label: str | None = None
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def consent_and_review_dates_match_state(self):
        if self.state in {"consented", "queued", "reviewed", "resumed"} and self.consented_at is None:
            raise ValueError("consent-aware review states require a consent timestamp")
        if self.state in {"reviewed", "resumed"} and self.reviewed_at is None:
            raise ValueError("completed review states require a review timestamp")
        return self


class Notification(Contract):
    id: UUID
    workspace_id: UUID
    kind: Text
    status: Literal["pending", "sent", "failed", "cancelled"]
    idempotency_key: Text
    payload: dict[str, Any] = Field(default_factory=dict)
    scheduled_for: datetime | None = None
    sent_at: datetime | None = None
    attempt_count: int = Field(default=0, ge=0)
    last_error_code: str | None = None
    created_at: datetime
    updated_at: datetime


class Feedback(Contract):
    id: UUID
    workspace_id: UUID
    rating: int | None = Field(default=None, ge=1, le=5)
    category: Text
    comment: str = ""
    langsmith_trace_id: str = ""
    created_at: datetime
