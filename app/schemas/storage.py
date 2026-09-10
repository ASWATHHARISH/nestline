"""Stage 2 storage contracts shared by the app and Supabase migration checks."""

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
    created_at: datetime
    updated_at: datetime


class JourneyState(Contract):
    id: UUID
    workspace_id: UUID
    stage: Stage
    timing_source: Literal[
        "document_estimated_due_date", "user_estimated_due_date", "manual_week_day",
        "approximate_month_range", "delivery_date", "postpartum_week",
    ]
    gestational_week: int | None = Field(default=None, ge=1, le=42)
    gestational_day: int | None = Field(default=None, ge=0, le=6)
    postpartum_week: int | None = Field(default=None, ge=1, le=12)
    postpartum_day: int | None = Field(default=None, ge=0, le=7)
    estimated_due_date: date | None = None
    delivery_date: date | None = None
    approximate_month_min: int | None = Field(default=None, ge=1, le=10)
    approximate_month_max: int | None = Field(default=None, ge=1, le=10)
    user_confirmed: bool
    has_dating_conflict: bool
    is_current: bool
    version: int = Field(ge=1)

    @model_validator(mode="after")
    def timing_matches_stage(self):
        if self.stage == "possible_pregnancy" and any((
                self.gestational_week, self.postpartum_week, self.postpartum_day,
                self.delivery_date)):
            raise ValueError("possible pregnancy cannot claim a confirmed week or delivery")
        if self.stage == "pregnancy" and self.postpartum_week is not None:
            raise ValueError("pregnancy state cannot contain a postpartum week")
        if self.stage == "postpartum" and self.gestational_week is not None:
            raise ValueError("postpartum state cannot contain a gestational week")
        if ((self.approximate_month_min is None) != (self.approximate_month_max is None)
                or (self.approximate_month_min is not None
                    and self.approximate_month_min > self.approximate_month_max)):
            raise ValueError("approximate month range must be complete and ordered")
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
    uploaded_at: datetime


class DocumentFact(Contract):
    id: UUID
    workspace_id: UUID
    document_id: UUID
    field_name: Text
    value: Any
    source_page: int | None = Field(default=None, ge=1)
    source_text: str = ""
    confidence: float = Field(ge=0, le=1)
    status: Literal["proposed", "confirmed", "rejected", "conflict"]


class HealthFact(Contract):
    id: UUID
    workspace_id: UUID
    fact_type: Literal[
        "allergy", "dietary_restriction", "medical_history", "medication",
        "clinician_instruction", "feeding_status", "delivery_history", "other",
    ]
    value: Any
    source_kind: Literal["user_reported", "document_extracted", "human_reviewed"]
    confirmation_status: Literal["proposed", "confirmed", "rejected", "conflict"]
    source_document_id: UUID | None = None
    supersedes_fact_id: UUID | None = None


class Appointment(Contract):
    id: UUID
    workspace_id: UUID
    scheduled_for: datetime | None = None
    appointment_type: str = ""
    location: str = ""
    status: Literal["planned", "confirmed", "completed", "cancelled"]


class SavedPlan(Contract):
    id: UUID
    workspace_id: UUID
    version: int = Field(ge=1)
    journey_state_id: UUID
    source_release_id: UUID
    status: Literal["draft", "user_reviewed", "saved", "active", "stale", "replaced", "archived"]
    stale_reasons: list[str] = Field(default_factory=list)
    user_confirmed_at: datetime | None = None


class HumanReviewCase(Contract):
    id: UUID
    workspace_id: UUID
    state: Literal[
        "not_required", "offered", "consented", "queued", "reviewed",
        "resumed", "declined", "timed_out", "unavailable",
    ]
    reason: Text
    simulated: bool = True
    consented_at: datetime | None = None
    reviewed_at: datetime | None = None

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
    scheduled_for: datetime | None = None
    sent_at: datetime | None = None


class Feedback(Contract):
    id: UUID
    workspace_id: UUID
    rating: int | None = Field(default=None, ge=1, le=5)
    category: Text
    comment: str = ""
    langsmith_trace_id: str = ""
