"""Typed inputs and outputs for Stage 3 onboarding and journey resolution."""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, TypeAdapter, model_validator

from app.schemas.content import Contract, Stage, Text
from app.schemas.safety import SafetyRoute


TimingSource = Literal[
    "user_reported_possible_pregnancy",
    "document_estimated_due_date",
    "user_estimated_due_date",
    "manual_week_day",
    "approximate_month_range",
    "delivery_date",
    "postpartum_week",
]


class PossiblePregnancyTiming(Contract):
    kind: Literal["possible_pregnancy"] = "possible_pregnancy"
    effective_date: date


class EstimatedDueDateTiming(Contract):
    kind: Literal["estimated_due_date"] = "estimated_due_date"
    effective_date: date
    estimated_due_date: date
    provenance: Literal[
        "user_estimated_due_date", "document_estimated_due_date"
    ] = "user_estimated_due_date"
    source_fact_ids: list[UUID] = Field(default_factory=list)


class ManualWeekDayTiming(Contract):
    kind: Literal["manual_week_day"] = "manual_week_day"
    effective_date: date
    gestational_week: int = Field(ge=1, le=42)
    gestational_day: int = Field(default=0, ge=0, le=6)


class ApproximateMonthTiming(Contract):
    kind: Literal["approximate_month"] = "approximate_month"
    effective_date: date
    pregnancy_month: int = Field(ge=1, le=9)


class DeliveryDateTiming(Contract):
    kind: Literal["delivery_date"] = "delivery_date"
    delivery_date: date


class PostpartumWeekTiming(Contract):
    kind: Literal["postpartum_week"] = "postpartum_week"
    effective_date: date
    postpartum_week: int = Field(ge=1, le=12)
    postpartum_day: int = Field(default=0, ge=0, le=6)


JourneyTimingInput = Annotated[
    PossiblePregnancyTiming
    | EstimatedDueDateTiming
    | ManualWeekDayTiming
    | ApproximateMonthTiming
    | DeliveryDateTiming
    | PostpartumWeekTiming,
    Field(discriminator="kind"),
]
JOURNEY_TIMING_ADAPTER = TypeAdapter(JourneyTimingInput)


class JourneyResolution(Contract):
    stage: Stage
    timing_source: TimingSource
    effective_date: date
    calculation_date: date
    gestational_week: int | None = Field(default=None, ge=1, le=42)
    gestational_day: int | None = Field(default=None, ge=0, le=6)
    postpartum_week: int | None = Field(default=None, ge=1, le=12)
    postpartum_day: int | None = Field(default=None, ge=0, le=6)
    estimated_due_date: date | None = None
    delivery_date: date | None = None
    approximate_month_min: int | None = Field(default=None, ge=1, le=9)
    approximate_month_max: int | None = Field(default=None, ge=1, le=9)
    approximate_week_min: int | None = Field(default=None, ge=1, le=42)
    approximate_week_max: int | None = Field(default=None, ge=1, le=42)
    position_day_min: int | None = Field(default=None, ge=0)
    position_day_max: int | None = Field(default=None, ge=0)
    source_fact_ids: list[UUID] = Field(default_factory=list)
    certainty: Literal["unknown", "exact", "approximate"]
    display_label: Text
    requires_confirmation: bool = True
    early_pregnancy_caution: bool = False
    limitations: list[Text] = Field(default_factory=list)

    @model_validator(mode="after")
    def ordered_position(self):
        values = (self.position_day_min, self.position_day_max)
        if (values[0] is None) != (values[1] is None):
            raise ValueError("journey position interval must be complete")
        if values[0] is not None and values[0] > values[1]:
            raise ValueError("journey position interval must be ordered")
        if self.certainty == "unknown" and values[0] is not None:
            raise ValueError("unknown timing cannot claim a journey position")
        if self.certainty != "unknown" and values[0] is None:
            raise ValueError("resolved timing requires a journey position")
        return self


class DatingConflict(Contract):
    has_conflict: bool
    reason: Literal[
        "none", "different_exact_day", "outside_approximate_range",
        "non_overlapping_ranges", "episode_stage_regression",
    ]
    current_state_id: UUID | None = None
    current_version: int = Field(default=0, ge=0)
    current_display: str = ""
    proposed_display: str = ""
    difference_days: int | None = Field(default=None, ge=0)
    requires_user_choice: bool
    commit_blocked: bool = False


class ReportedFactInput(Contract):
    category: Literal[
        "allergy", "medical_history", "dietary_restriction",
        "movement_restriction", "other_restriction",
    ]
    label: Text


class SymptomInput(Contract):
    description: Text
    reported_at: datetime


class AppointmentInput(Contract):
    scheduled_for: datetime
    appointment_type: Text
    location: str = ""


class OnboardingDetails(Contract):
    facts: list[ReportedFactInput] = Field(default_factory=list, max_length=40)
    symptoms: list[SymptomInput] = Field(default_factory=list, max_length=10)
    appointments: list[AppointmentInput] = Field(default_factory=list, max_length=10)

    @model_validator(mode="after")
    def reject_duplicate_facts(self):
        keys = [(fact.category, " ".join(fact.label.casefold().split())) for fact in self.facts]
        if len(keys) != len(set(keys)):
            raise ValueError("onboarding contains a duplicate reported fact")
        return self


class PreparedSymptom(Contract):
    description: Text
    reported_at: datetime
    safety_route: SafetyRoute
    matched_rule_ids: list[str] = Field(default_factory=list)
    safety_message: Text
    safety_spec_version: Text
    safety_evaluation_only: bool
    safety_trace_id: UUID


class OnboardingDraft(Contract):
    timing: JourneyTimingInput
    resolution: JourneyResolution
    conflict: DatingConflict
    details: OnboardingDetails
    prepared_symptoms: list[PreparedSymptom] = Field(default_factory=list)


class OnboardingCommitResult(Contract):
    journey_state_id: UUID
    version: int = Field(ge=1)
    fact_ids: list[UUID] = Field(default_factory=list)
    symptom_event_ids: list[UUID] = Field(default_factory=list)
    appointment_ids: list[UUID] = Field(default_factory=list)
    idempotent_replay: bool = False