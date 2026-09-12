"""Strict Stage 9 view contracts for the local Streamlit product experience.

These models contain display-ready, fictional or authenticated data only. They
do not authorize durable writes, publication, medical advice, or Stage 10 work.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal, Self

from pydantic import Field, model_validator

from app.schemas.content import Contract, Text


STAGE9_SCHEMA_VERSION = "9.0.0"


class ProductMode(StrEnum):
    PERSONAL = "Personal Mode"
    DEMO = "Demo Mode"


class ProductPage(StrEnum):
    HOME = "Weekly Home"
    COMPASS = "Compass"
    RECORDS = "Records"
    PLAN = "Plan"
    EVIDENCE = "Evidence"
    REVIEW = "Simulated review"
    EVALUATOR = "Evaluator view"


class ViewState(StrEnum):
    LOADING = "loading"
    EMPTY = "empty"
    SUCCESS = "success"
    VALIDATION_ERROR = "validation_error"
    RECOVERABLE_ERROR = "recoverable_error"
    BLOCKED = "blocked_safety"
    STALE = "stale_conflict"
    UNAVAILABLE = "unavailable_disabled"


class PlanDisplayState(StrEnum):
    NONE = "none"
    DRAFT = "draft"
    SAVED = "saved"
    STALE = "stale"
    CONFLICT = "conflict"
    INVALID = "invalid"
    UNAVAILABLE = "unavailable"


class RuntimeConfig(Contract):
    schema_version: Literal["9.0.0"] = STAGE9_SCHEMA_VERSION
    supabase_configured: bool
    personal_mode_available: bool
    demo_mode_available: Literal[True] = True
    missing_fields: list[Text] = Field(default_factory=list)
    fixture_only: Literal[True] = True
    public_health_routing_available: Literal[False] = False


class JourneyHeader(Contract):
    stage: Literal["pregnancy", "postpartum", "possible_pregnancy"]
    display_label: Text
    exact: bool
    position_start: int | None = Field(default=None, ge=0)
    position_end: int | None = Field(default=None, ge=0)
    unit: Literal["week", "day", "none"]
    state_version: int = Field(ge=1)

    @model_validator(mode="after")
    def range_is_coherent(self) -> Self:
        if self.unit == "none" and (self.position_start is not None or self.position_end is not None):
            raise ValueError("journey without a unit cannot carry a position")
        if self.unit != "none" and (self.position_start is None or self.position_end is None):
            raise ValueError("journey position requires a complete exact/range value")
        if self.exact and self.position_start != self.position_end:
            raise ValueError("exact journey position must use one value")
        if self.position_start is not None and self.position_end is not None and self.position_start > self.position_end:
            raise ValueError("journey range must be ordered")
        return self


class HomeSection(Contract):
    heading: Text
    items: list[Text] = Field(default_factory=list)
    state: ViewState = ViewState.SUCCESS
    primary_action: str | None = None


class WeeklyHomeView(Contract):
    schema_version: Literal["9.0.0"] = STAGE9_SCHEMA_VERSION
    mode: ProductMode
    fictional: bool
    journey: JourneyHeader | None = None
    hero_title: Text
    hero_body: Text
    hero_asset: str | None = None
    hero_alt: Text
    confirmed_context: list[Text] = Field(default_factory=list)
    sections: list[HomeSection]
    plan_state: PlanDisplayState
    unresolved_items: list[Text] = Field(default_factory=list)
    agent_fanout_count: Literal[0] = 0
    state: ViewState

    @model_validator(mode="after")
    def personal_empty_is_really_empty(self) -> Self:
        if self.mode == ProductMode.PERSONAL and self.state == ViewState.EMPTY:
            if self.journey is not None or self.confirmed_context:
                raise ValueError("empty Personal Mode cannot inherit demo journey or context")
        if self.mode == ProductMode.DEMO and not self.fictional:
            raise ValueError("Demo Mode must be visibly fictional")
        return self


class EvidenceDrawerItem(Contract):
    evidence_id: Text
    source_id: Text
    source_title: Text
    publisher: Text
    source_type: Literal["public_fixture", "personal_document_fixture"]
    review_status: Text
    current_status: Text
    journey_applicability: str | None = None
    locator: Text
    supporting_passage: Text
    supports_claim: bool
    workspace_id: str | None = None
    fixture_only: Literal[True] = True

    @model_validator(mode="after")
    def private_source_is_scoped(self) -> Self:
        if self.source_type == "personal_document_fixture" and not self.workspace_id:
            raise ValueError("personal evidence requires an authenticated workspace")
        if self.source_type == "public_fixture" and self.workspace_id is not None:
            raise ValueError("public evidence cannot carry private workspace scope")
        return self


class ChatDisplayResult(Contract):
    schema_version: Literal["9.0.0"] = STAGE9_SCHEMA_VERSION
    request_id: Text
    route: Literal["urgent", "clarification", "validated", "abstained", "unsupported"]
    title: Text
    summary: Text
    provenance_sections: dict[Text, list[Text]] = Field(default_factory=dict)
    citations: list[EvidenceDrawerItem] = Field(default_factory=list)
    uncertainties: list[Text] = Field(default_factory=list)
    applied_constraints: list[Text] = Field(default_factory=list)
    proposed_actions: list[Text] = Field(default_factory=list)
    ordinary_generation_calls: int = Field(ge=0, le=5)
    validation_display_allowed: bool
    trace_id: str | None = None
    fixture_only: Literal[True] = True
    state: ViewState

    @model_validator(mode="after")
    def safety_route_is_immutable(self) -> Self:
        if self.route in {"urgent", "clarification"}:
            if self.ordinary_generation_calls != 0 or self.validation_display_allowed:
                raise ValueError("safety-blocked routes cannot expose ordinary generation")
        if self.route == "validated" and not self.validation_display_allowed:
            raise ValueError("validated UI output requires the Stage 8 display gate")
        return self


class RecordFieldView(Contract):
    label: Text
    value: Text
    status: Literal["confirmed", "unconfirmed", "conflicting", "missing"]
    source_id: Text
    locator: Text
    exact_span: Text
    confidence: float = Field(ge=0, le=1)
    record_only: bool = False


class DocumentView(Contract):
    document_id: Text
    label: Text
    status: Literal["ready", "low_confidence", "conflict", "locked", "corrupt", "unsupported", "wrong_person"]
    subject: Text
    fields: list[RecordFieldView] = Field(default_factory=list)
    recovery: Text
    fictional: Literal[True] = True


class SimulatedReviewView(Contract):
    status: Literal["offered", "consented", "queued", "responded", "declined", "unavailable", "timed_out"]
    label: Literal["Simulated review"] = "Simulated review"
    context_proposed: list[Text] = Field(default_factory=list)
    persistence_available: Literal[False] = False
    can_delay_urgent_route: Literal[False] = False


class EvaluatorMetric(Contract):
    stage: Text
    artifact: Text
    passed: int = Field(ge=0)
    total: int = Field(ge=0)
    failed: int = Field(ge=0)
    skipped: int = Field(ge=0)
    dataset_version: Text
    live_provider_run: bool = False

    @model_validator(mode="after")
    def totals_agree(self) -> Self:
        if self.passed + self.failed + self.skipped != self.total:
            raise ValueError("evaluator metric denominator is inconsistent")
        return self
