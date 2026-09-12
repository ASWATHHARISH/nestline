"""Strict Stage 7 contracts for bounded orchestration and proposed plans.

These contracts describe controlled engineering behavior.  They do not grant
medical clearance, authorize persistent writes, or validate health content.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal, Self
from uuid import UUID, uuid4

from pydantic import Field, model_validator

from app.schemas.content import Contract, Text
from app.schemas.retrieval import JourneyPosition
from app.schemas.safety import SafetyGateResult


ORCHESTRATION_SCHEMA_VERSION = "7.0.0"
AGENT_CATALOGUE_VERSION = "stage7-catalogue-v1"
ROUTER_VERSION = "stage7-router-v1"
SCHEDULE_VERSION = "stage7-schedule-v1"


class AgentName(StrEnum):
    RECORD = "record_agent"
    MEDICATION = "medication_record_agent"
    SYMPTOM = "symptom_navigation_agent"
    NUTRITION = "nutrition_agent"
    MOVEMENT = "movement_agent"
    WELLBEING = "wellbeing_agent"
    FOLLOWUP = "followup_agent"
    PLAN_COMPOSER = "plan_composer_agent"


class Intent(StrEnum):
    RECORD = "record"
    MEDICATION = "medication_record"
    SYMPTOM = "symptom"
    NUTRITION = "nutrition"
    MOVEMENT = "movement"
    WELLBEING = "wellbeing"
    FOLLOWUP = "followup"
    FULL_PLAN = "full_plan"
    OUT_OF_SCOPE = "out_of_scope"
    AMBIGUOUS_MULTI_INTENT = "ambiguous_multi_intent"


class WorkerStatus(StrEnum):
    COMPLETED = "completed"
    NEEDS_CLARIFICATION = "needs_clarification"
    ABSTAINED = "abstained"
    ESCALATED = "escalated"
    FAILED = "failed"


class ContextKind(StrEnum):
    JOURNEY = "journey"
    ALLERGY = "allergy"
    INTOLERANCE = "intolerance"
    CONDITION = "condition"
    RESTRICTION = "restriction"
    CLINICIAN_INSTRUCTION = "clinician_instruction"
    MEDICATION = "medication"
    SUPPLEMENT = "supplement"
    APPOINTMENT = "appointment"
    SYMPTOM = "symptom"
    PREFERENCE = "preference"
    ACCESSIBILITY = "accessibility"
    DOCUMENT_FACT = "document_fact"
    OPEN_QUESTION = "open_question"
    PLAN_STATE = "plan_state"
    CHECK_IN = "check_in"
    DELIVERY_RECOVERY = "delivery_recovery"


class FactState(StrEnum):
    CONFIRMED = "confirmed"
    USER_REPORTED = "user_reported"
    DOCUMENT_UNCONFIRMED = "document_derived_unconfirmed"
    CONFLICTING = "conflicting"
    STALE = "stale"


class RuntimeMode(StrEnum):
    """Explicit product mode; fixture data is never implicit personal state."""

    DEMO = "demo"
    PERSONAL = "personal"
    EVALUATION = "evaluation"


class ContextOrigin(StrEnum):
    AUTHENTICATED_STORE = "authenticated_store"
    FICTIONAL_FIXTURE = "fictional_fixture"

class MedicationLifecycle(StrEnum):
    CURRENT = "current"
    HISTORICAL = "historical"
    STOPPED = "stopped"
    UNCONFIRMED = "unconfirmed"
    CONFLICTING = "conflicting"


class EvidenceLane(StrEnum):
    PERSONAL_SQL = "personal_sql"
    PERSONAL_DOCUMENT = "personal_document"
    PUBLIC_GUIDELINE = "public_guideline"
    WEEKLY_PROFILE = "weekly_profile"
    STRUCTURED_CATALOGUE = "structured_catalogue"
    SAFETY_RESULT = "safety_result"


class RetrievalPurpose(StrEnum):
    PERSONAL_RECORD_LOOKUP = "personal_record_lookup"
    MEDICATION_RECORD_LOOKUP = "medication_record_lookup"
    SYMPTOM_NAVIGATION = "symptom_navigation"
    NUTRITION_GUIDANCE = "nutrition_guidance"
    MOVEMENT_GUIDANCE = "movement_guidance"
    WELLBEING_SUPPORT = "wellbeing_support"
    FOLLOWUP_ORGANISATION = "followup_organisation"
    PLAN_COMPOSITION = "plan_composition"


class Weekday(StrEnum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class AgentBudget(Contract):
    max_model_calls: int = Field(ge=0, le=1)
    max_steps: int = Field(ge=1, le=8)
    max_tokens: int = Field(ge=0, le=4_000)
    max_retries: int = Field(ge=0, le=1)
    max_repairs: int = Field(ge=0, le=1)
    timeout_ms: int = Field(ge=50, le=30_000)


class AgentDefinition(Contract):
    agent: AgentName
    version: Text
    trigger: Text
    allowed_tools: list[Text]
    allowed_evidence_lanes: list[EvidenceLane]
    retrieval_purpose: RetrievalPurpose
    prohibited_actions: list[Text] = Field(min_length=1)
    stop_conditions: list[Text] = Field(min_length=1)
    model_instructions: list[Text] = Field(default_factory=list)
    budget: AgentBudget
    direct_persistent_write_allowed: Literal[False] = False
    service_role_allowed: Literal[False] = False
    may_call_other_agent: Literal[False] = False


class EvidenceReference(Contract):
    evidence_id: Text
    source_id: Text
    lane: EvidenceLane
    exact_span: Text
    candidate_label: str | None = None
    constraint_tags: list[Text] = Field(default_factory=list)
    source_page: int | None = Field(default=None, ge=1)
    source_date: str | None = None
    approval_state: Literal["controlled_fixture", "approved", "confirmed_personal"]
    journey: JourneyPosition | None = None
    fixture_only: bool = False
    duration_minutes: int | None = Field(default=None, ge=1, le=240)
    cadence_per_week: int | None = Field(default=None, ge=1, le=7)
    intensity_wording: str | None = None
    flexible_alternatives: list[Text] = Field(default_factory=list)
    rest_recovery_notes: list[Text] = Field(default_factory=list)

    @model_validator(mode="after")
    def fixture_label_agrees(self) -> Self:
        if self.approval_state == "controlled_fixture" and not self.fixture_only:
            raise ValueError("controlled fixture evidence must be visibly fixture-only")
        if self.fixture_only and self.approval_state != "controlled_fixture":
            raise ValueError("fixture-only evidence cannot claim another approval state")
        return self


class ContextItem(Contract):
    item_id: Text
    kind: ContextKind
    state: FactState
    value: Any
    source_id: str | None = None
    source_page: int | None = Field(default=None, ge=1)
    exact_span: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    recorded_at: datetime | None = None
    current: bool = True
    record_only: bool = False

    @model_validator(mode="after")
    def provenance_and_medication_agree(self) -> Self:
        if self.state in {FactState.DOCUMENT_UNCONFIRMED, FactState.CONFLICTING}:
            if not self.source_id or not self.exact_span:
                raise ValueError("unconfirmed/conflicting document context needs source and exact span")
        if self.kind in {ContextKind.MEDICATION, ContextKind.SUPPLEMENT} and not self.record_only:
            raise ValueError("medication and supplement context must remain record-only")
        return self


class AuthenticatedContextSnapshot(Contract):
    """Trusted, server-built context. Client text contains no scope fields."""

    schema_version: Literal["7.0.0"] = ORCHESTRATION_SCHEMA_VERSION
    workspace_id: UUID
    care_episode_id: UUID
    owner_user_id: UUID
    session_subject: UUID
    state_version: int = Field(ge=1)
    captured_at: datetime
    journey: JourneyPosition
    items: list[ContextItem] = Field(default_factory=list)
    trusted_server_created: Literal[True] = True
    context_origin: ContextOrigin = ContextOrigin.FICTIONAL_FIXTURE
    onboarding_confirmed: bool = True

    @model_validator(mode="after")
    def authenticated_owner_scope(self) -> Self:
        if self.owner_user_id != self.session_subject:
            raise ValueError("Stage 7 context must belong to the authenticated owner")
        if self.care_episode_id != self.workspace_id:
            raise ValueError("owner-only v1 uses workspace as the care-episode boundary")
        ids = [item.item_id for item in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("context item IDs must be unique")
        return self


class MinimalWorkerContext(Contract):
    workspace_id: UUID
    care_episode_id: UUID
    state_version: int = Field(ge=1)
    journey: JourneyPosition
    allowed_kinds: list[ContextKind]
    items: list[ContextItem] = Field(default_factory=list)
    minimized: Literal[True] = True

    @model_validator(mode="after")
    def only_allowed_context(self) -> Self:
        allowed = set(self.allowed_kinds)
        if len(allowed) != len(self.allowed_kinds):
            raise ValueError("allowed context kinds must be unique")
        if any(item.kind not in allowed for item in self.items):
            raise ValueError("worker context contains a non-permitted item")
        return self


class WorkerEvidence(Contract):
    retrieval_purpose: RetrievalPurpose
    references: list[EvidenceReference] = Field(default_factory=list)
    missing_information: list[Text] = Field(default_factory=list)
    unresolved_conflicts: list[Text] = Field(default_factory=list)
    corpus_mode: Literal["controlled_fixture", "production_release", "personal_only"]
    public_routing_eligible: bool

    @model_validator(mode="after")
    def evidence_mode_agrees(self) -> Self:
        if self.corpus_mode == "controlled_fixture":
            if self.public_routing_eligible:
                raise ValueError("controlled fixtures cannot be public-routing eligible")
            if any(not item.fixture_only and item.lane in {
                EvidenceLane.PUBLIC_GUIDELINE, EvidenceLane.WEEKLY_PROFILE,
                EvidenceLane.STRUCTURED_CATALOGUE,
            } for item in self.references):
                raise ValueError("controlled public evidence must remain fixture-only")
        if self.corpus_mode == "personal_only" and any(
            item.lane in {EvidenceLane.PUBLIC_GUIDELINE, EvidenceLane.WEEKLY_PROFILE,
                          EvidenceLane.STRUCTURED_CATALOGUE}
            for item in self.references
        ):
            raise ValueError("personal-only evidence cannot include public lanes")
        return self


class WorkerRequest(Contract):
    """One strict minimum-context worker invocation created by the orchestrator."""

    schema_version: Literal["7.0.0"] = ORCHESTRATION_SCHEMA_VERSION
    request_id: UUID
    agent: AgentName
    query: Text
    context: MinimalWorkerContext
    evidence: WorkerEvidence
    safety_result: SafetyGateResult
    evaluation_only: bool

    @model_validator(mode="after")
    def safety_and_query_agree(self) -> Self:
        from app.services.safety_gate import normalize_safety_text
        from hashlib import sha256

        expected = sha256(normalize_safety_text(self.query).encode("utf-8")).hexdigest()
        if self.safety_result.request_id != self.request_id:
            raise ValueError("worker and Safety Gate request IDs must agree")
        if self.safety_result.trace.normalized_input_sha256 != expected:
            raise ValueError("worker query must be the exact text evaluated by the Safety Gate")
        for reference in self.evidence.references:
            if reference.journey is None:
                continue
            expected_journey = self.context.journey
            same_lane = reference.journey.stage == expected_journey.stage and reference.journey.unit == expected_journey.unit
            covers = (reference.journey.unit == "none" or (
                reference.journey.start is not None and expected_journey.start is not None
                and reference.journey.end is not None and expected_journey.end is not None
                and reference.journey.start <= expected_journey.start <= expected_journey.end <= reference.journey.end
            ))
            if not same_lane or not covers:
                raise ValueError("worker evidence must apply to the exact trusted journey state")
        if self.evaluation_only != self.safety_result.evaluation_only:
            raise ValueError("worker execution mode must agree with the Safety Gate")
        return self

class OrchestrationRequest(Contract):
    schema_version: Literal["7.0.0"] = ORCHESTRATION_SCHEMA_VERSION
    request_id: UUID = Field(default_factory=uuid4)
    text: Text
    context: AuthenticatedContextSnapshot
    safety_result: SafetyGateResult
    execution_mode: Literal["evaluation_only", "public_runtime"]
    runtime_mode: RuntimeMode = RuntimeMode.EVALUATION
    explicit_user_action: bool = True
    requested_horizon: Literal["none", "day", "week"] = "none"
    selected_day: Weekday | None = None
    evidence_by_agent: dict[AgentName, WorkerEvidence] = Field(default_factory=dict)
    max_total_model_calls: int = Field(default=5, ge=0, le=5)
    max_total_steps: int = Field(default=16, ge=1, le=32)
    timeout_ms: int = Field(default=30_000, ge=100, le=30_000)

    @model_validator(mode="after")
    def request_boundaries(self) -> Self:
        if self.safety_result.request_id != self.request_id:
            raise ValueError("Safety Gate and Stage 7 request IDs must agree")
        from hashlib import sha256
        from app.services.safety_gate import normalize_safety_text
        expected_hash = sha256(normalize_safety_text(self.text).encode("utf-8")).hexdigest()
        if self.safety_result.trace.normalized_input_sha256 != expected_hash:
            raise ValueError("Stage 7 text must be the exact text evaluated by the Safety Gate")
        if self.execution_mode == "public_runtime" and (
            self.safety_result.evaluation_only or not self.safety_result.public_routing_eligible
        ):
            raise ValueError("public Stage 7 execution requires a public-eligible Safety Gate result")
        if self.runtime_mode == RuntimeMode.PERSONAL:
            if self.context.context_origin != ContextOrigin.AUTHENTICATED_STORE:
                raise ValueError("Personal Mode cannot use fictional fixture context")
            if not self.context.onboarding_confirmed:
                raise ValueError("Personal Mode requires confirmed onboarding state")
            if self.execution_mode != "public_runtime":
                raise ValueError("Personal Mode cannot run through an evaluation-only path")
        elif self.execution_mode != "evaluation_only":
            raise ValueError("Demo/evaluation modes must remain evaluation-only")
        if (
            self.context.context_origin == ContextOrigin.FICTIONAL_FIXTURE
            and self.execution_mode != "evaluation_only"
        ):
            raise ValueError("fictional fixture context cannot enter a public runtime")
        if self.requested_horizon != "none" and not self.explicit_user_action:
            raise ValueError("plan generation requires an explicit user action")
        if self.requested_horizon == "day" and self.selected_day is None:
            raise ValueError("a one-day plan requires selected_day")
        if self.requested_horizon != "day" and self.selected_day is not None:
            raise ValueError("selected_day is only valid for a one-day plan")
        return self


class EvidencePlanItem(Contract):
    agent: AgentName
    purpose: RetrievalPurpose
    allowed_lanes: list[EvidenceLane]
    required: bool = True


class RoutePlan(Contract):
    router_version: Literal["stage7-router-v1"] = ROUTER_VERSION
    intent: Intent
    selected_workers: list[AgentName] = Field(default_factory=list)
    reason: Text
    evidence_plan: list[EvidencePlanItem] = Field(default_factory=list)
    routing_call_count: int = Field(ge=0, le=1)
    total_call_budget: int = Field(ge=0, le=5)
    total_step_budget: int = Field(ge=1, le=32)
    requires_clarification: bool = False

    @model_validator(mode="after")
    def bounded_route(self) -> Self:
        if len(self.selected_workers) != len(set(self.selected_workers)):
            raise ValueError("a worker may be selected at most once")
        if AgentName.PLAN_COMPOSER in self.selected_workers:
            contributors = [a for a in self.selected_workers if a != AgentName.PLAN_COMPOSER]
            if len(contributors) > 4:
                raise ValueError("a plan may use at most four specialist contributors")
            if self.selected_workers[-1] != AgentName.PLAN_COMPOSER:
                raise ValueError("Plan Composer must run after every contributor")
        elif len(self.selected_workers) > 1:
            raise ValueError("ordinary non-plan requests may select only one specialist")
        if len(self.selected_workers) > self.total_call_budget:
            raise ValueError("selected workers exceed the call budget")
        if self.requires_clarification and self.selected_workers:
            raise ValueError("clarification routes cannot start workers")
        planned = [item.agent for item in self.evidence_plan]
        if planned != self.selected_workers:
            raise ValueError("evidence plan must match selected worker order")
        return self


class ProposedAction(Contract):
    action_id: Text
    description: Text
    requires_user_confirmation: Literal[True] = True
    proposal_only: Literal[True] = True
    persistent_write_performed: Literal[False] = False


class RecordFinding(Contract):
    item_id: Text
    wording: Text
    state: FactState
    source_id: Text
    source_page: int | None = Field(default=None, ge=1)
    exact_span: Text
    confidence: float | None = Field(default=None, ge=0, le=1)
    freshness: str | None = None


class MedicationTimelineEntry(Contract):
    item_id: Text
    name: Text
    dose: str | None = None
    unit: str | None = None
    route: str | None = None
    frequency: str | None = None
    timing: str | None = None
    start_date: str | None = None
    stop_date: str | None = None
    prescriber_or_source: str | None = None
    state: FactState
    lifecycle: MedicationLifecycle
    record_only: Literal[True] = True


class SymptomNavigation(Contract):
    route: Literal[
        "urgent_now", "same_day_professional_contact", "routine_professional_follow_up",
        "monitor_track", "insufficient_information",
    ]
    what_to_do_now: list[Text] = Field(min_length=1)
    actions_to_avoid: list[Text] = Field(default_factory=list)
    escalation_triggers: list[Text] = Field(default_factory=list)
    professional_route: str | None = None
    diagnostic_claim_made: Literal[False] = False
    unsafe_reassurance_made: Literal[False] = False


class PlanContribution(Contract):
    contribution_id: Text
    contributor: AgentName
    domain: Literal["nutrition", "movement", "wellbeing", "followup"]
    item: Text
    duration_minutes: int = Field(ge=1, le=240)
    cadence_per_week: int = Field(ge=1, le=7)
    preferred_days: list[Weekday] = Field(default_factory=list)
    preferred_time_windows: list[Literal["morning", "afternoon", "evening"]] = Field(default_factory=list)
    evidence_ids: list[Text] = Field(min_length=1)
    constraint_notes: list[Text] = Field(default_factory=list)
    optional: bool = False
    flexible: bool = True
    flexible_alternatives: list[Text] = Field(default_factory=list)
    rest_recovery_notes: list[Text] = Field(default_factory=list)
    cadence_source: Literal["evidence", "user_preference", "single_proposal"] = "single_proposal"
    state_version: int = Field(ge=1)

    @model_validator(mode="after")
    def contributor_domain_agrees(self) -> Self:
        expected = {
            AgentName.NUTRITION: "nutrition",
            AgentName.MOVEMENT: "movement",
            AgentName.WELLBEING: "wellbeing",
            AgentName.FOLLOWUP: "followup",
        }.get(self.contributor)
        if expected != self.domain:
            raise ValueError("plan contribution domain must match its contributor")
        return self


class FollowupTask(Contract):
    task_id: Text
    phase: Literal["before_appointment", "during_appointment", "after_appointment"]
    description: Text
    provenance_ids: list[Text] = Field(min_length=1)
    safety_priority: bool = False
    requires_consent: bool = False
    monitoring_claim: Literal[False] = False


class AgentTrace(Contract):
    trace_id: UUID = Field(default_factory=uuid4)
    request_id: UUID
    agent: AgentName
    agent_version: Text
    schema_version: Literal["7.0.0"] = ORCHESTRATION_SCHEMA_VERSION
    provider: Text
    model: Text
    evidence_ids: list[Text] = Field(default_factory=list)
    model_call_count: int = Field(ge=0, le=1)
    step_count: int = Field(ge=0, le=8)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    estimated_cost_usd: float = Field(ge=0)
    retry_count: int = Field(ge=0, le=1)
    repair_count: int = Field(ge=0, le=1)
    latency_ms: float = Field(ge=0)
    stop_reason: Text
    direct_write_count: Literal[0] = 0
    service_role_used: Literal[False] = False
    raw_personal_text_logged: Literal[False] = False


class WorkerResult(Contract):
    schema_version: Literal["7.0.0"] = ORCHESTRATION_SCHEMA_VERSION
    request_id: UUID
    agent: AgentName
    status: WorkerStatus
    journey_state_version: int = Field(ge=1)
    summary: Text
    facts_used: list[Text] = Field(default_factory=list)
    citations: list[EvidenceReference] = Field(default_factory=list)
    applied_constraints: list[Text] = Field(default_factory=list)
    uncertainties: list[Text] = Field(default_factory=list)
    proposed_actions: list[ProposedAction] = Field(default_factory=list)
    proposed_state_changes: list[ProposedAction] = Field(default_factory=list)
    record_findings: list[RecordFinding] = Field(default_factory=list)
    medication_timeline: list[MedicationTimelineEntry] = Field(default_factory=list)
    symptom_navigation: SymptomNavigation | None = None
    contributions: list[PlanContribution] = Field(default_factory=list)
    followup_tasks: list[FollowupTask] = Field(default_factory=list)
    requires_human_review: bool = False
    stop_reason: str | None = None
    evaluation_only: bool
    public_eligible: bool
    trace: AgentTrace

    @model_validator(mode="after")
    def output_is_consistent(self) -> Self:
        if self.trace.request_id != self.request_id or self.trace.agent != self.agent:
            raise ValueError("worker result and trace identity must agree")
        if self.status == WorkerStatus.COMPLETED and self.stop_reason is not None:
            raise ValueError("completed output cannot claim a stop reason")
        if self.status != WorkerStatus.COMPLETED and not self.stop_reason:
            raise ValueError("non-completed output requires a stop reason")
        if self.evaluation_only and self.public_eligible:
            raise ValueError("evaluation-only worker output cannot be public eligible")
        if self.trace.direct_write_count or self.trace.service_role_used:
            raise ValueError("Stage 7 workers cannot write or use service-role credentials")
        if self.agent == AgentName.RECORD and not self.record_findings and self.status == WorkerStatus.COMPLETED:
            raise ValueError("completed Record Agent output needs record findings")
        if self.agent == AgentName.MEDICATION and self.contributions:
            raise ValueError("medication records cannot become plan contributions")
        if self.agent == AgentName.SYMPTOM and self.status == WorkerStatus.COMPLETED and self.symptom_navigation is None:
            raise ValueError("completed symptom output needs a navigation route")
        if self.agent not in {AgentName.NUTRITION, AgentName.MOVEMENT, AgentName.WELLBEING, AgentName.FOLLOWUP} and self.contributions:
            raise ValueError("only plan contributors may emit contribution items")
        return self


class AvailabilityWindow(Contract):
    day: Weekday
    start: str = Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    end: str = Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")

    @model_validator(mode="after")
    def ordered(self) -> Self:
        if self.start >= self.end:
            raise ValueError("availability window must be ordered")
        return self


class FixedAppointment(Contract):
    appointment_id: Text
    day: Weekday
    start: str = Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    end: str = Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    label: Text

    @model_validator(mode="after")
    def ordered(self) -> Self:
        if self.start >= self.end:
            raise ValueError("appointment must have positive duration")
        return self


class RecordedReminder(Contract):
    reminder_id: Text
    item_id: Text
    wording: Text
    day: Weekday
    time: str = Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    source_id: Text
    exact_instruction: Text
    record_only: Literal[True] = True


class ScheduleRequest(Contract):
    schedule_version: Literal["stage7-schedule-v1"] = SCHEDULE_VERSION
    horizon: Literal["day", "week"]
    selected_day: Weekday | None = None
    state_version: int = Field(ge=1)
    availability: list[AvailabilityWindow] = Field(min_length=1)
    appointments: list[FixedAppointment] = Field(default_factory=list)
    contributions: list[PlanContribution] = Field(min_length=1)
    recorded_reminders: list[RecordedReminder] = Field(default_factory=list)
    applied_constraints: list[Text] = Field(default_factory=list)
    unresolved_uncertainties: list[Text] = Field(default_factory=list)
    verified_context_summary: list[Text] = Field(default_factory=list)
    max_recompositions: Literal[1] = 1

    @model_validator(mode="after")
    def schedule_input_consistency(self) -> Self:
        if self.horizon == "day" and self.selected_day is None:
            raise ValueError("one-day schedule requires selected_day")
        if self.horizon == "week" and self.selected_day is not None:
            raise ValueError("weekly schedule cannot carry selected_day")
        if any(c.state_version != self.state_version for c in self.contributions):
            raise ValueError("every contribution must use the same current state version")
        return self


class ScheduledItem(Contract):
    schedule_item_id: Text
    day: Weekday
    start: str
    end: str
    domain: Literal["nutrition", "movement", "wellbeing", "followup", "record_reminder"]
    item: Text
    contributor: AgentName | Literal["recorded_instruction"]
    evidence_ids: list[Text] = Field(min_length=1)
    constraint_notes: list[Text] = Field(default_factory=list)
    optional: bool = False
    flexible: bool = False
    record_only: bool = False
    cadence_source: Literal["evidence", "user_preference", "single_proposal"] | None = None
    flexible_alternatives: list[Text] = Field(default_factory=list)
    rest_recovery_notes: list[Text] = Field(default_factory=list)


class ProposedSchedule(Contract):
    schedule_version: Literal["stage7-schedule-v1"] = SCHEDULE_VERSION
    horizon: Literal["day", "week"]
    state_version: int = Field(ge=1)
    items: list[ScheduledItem]
    conflicts: list[Text] = Field(default_factory=list)
    assumptions: list[Text] = Field(default_factory=list)
    applied_constraints: list[Text] = Field(default_factory=list)
    unresolved_uncertainties: list[Text] = Field(default_factory=list)
    verified_context_summary: list[Text] = Field(default_factory=list)
    save_eligible: bool
    stale: bool = False
    proposal_only: Literal[True] = True
    persistent_write_performed: Literal[False] = False
    recomposition_count: int = Field(ge=0, le=1)
    next_question: Literal["Would you like to change, save, or discard this plan?"] = (
        "Would you like to change, save, or discard this plan?"
    )

    @model_validator(mode="after")
    def eligibility_agrees(self) -> Self:
        if self.save_eligible and (self.conflicts or self.unresolved_uncertainties or self.stale):
            raise ValueError("conflicted, uncertain or stale schedules cannot be save-eligible")
        seen: dict[Weekday, list[tuple[str, str]]] = {}
        for item in self.items:
            for start, end in seen.setdefault(item.day, []):
                if item.start < end and start < item.end:
                    raise ValueError("scheduled items may not overlap")
            seen[item.day].append((item.start, item.end))
        return self


class OrchestrationTrace(Contract):
    trace_id: UUID = Field(default_factory=uuid4)
    request_id: UUID
    router_version: Literal["stage7-router-v1"] = ROUTER_VERSION
    selected_workers: list[AgentName]
    worker_call_count: int = Field(ge=0, le=5)
    total_model_calls: int = Field(ge=0, le=5)
    total_steps: int = Field(ge=0, le=32)
    total_tokens: int = Field(ge=0)
    estimated_cost_usd: float = Field(ge=0)
    retry_count: int = Field(ge=0, le=5)
    latency_ms: float = Field(ge=0)
    stop_reason: Text
    direct_write_count: Literal[0] = 0
    service_role_used: Literal[False] = False


class OrchestrationResult(Contract):
    schema_version: Literal["7.0.0"] = ORCHESTRATION_SCHEMA_VERSION
    request_id: UUID
    safety_result: SafetyGateResult
    route_plan: RoutePlan
    worker_results: list[WorkerResult] = Field(default_factory=list)
    proposed_schedule: ProposedSchedule | None = None
    ordinary_generation_started: bool
    proposal_only: Literal[True] = True
    public_eligible: bool
    trace: OrchestrationTrace

    @model_validator(mode="after")
    def result_invariants(self) -> Self:
        if self.safety_result.request_id != self.request_id or self.trace.request_id != self.request_id:
            raise ValueError("request identity must agree across Safety Gate and orchestration")
        workers = [result.agent for result in self.worker_results]
        if workers != self.route_plan.selected_workers or workers != self.trace.selected_workers:
            raise ValueError("route, worker results and trace must have identical ordered workers")
        if self.trace.worker_call_count != len(workers):
            raise ValueError("trace worker call count is incorrect")
        if self.safety_result.route != "non_urgent":
            if workers or self.ordinary_generation_started or self.proposed_schedule is not None:
                raise ValueError("urgent/clarification safety routes must bypass every Stage 7 worker")
        if self.ordinary_generation_started != (self.trace.total_model_calls > 0):
            raise ValueError("ordinary-generation-started must exactly reflect provider calls")
        if self.trace.total_model_calls > self.route_plan.total_call_budget:
            raise ValueError("orchestration exceeded its call budget")
        if self.trace.total_steps > self.route_plan.total_step_budget:
            raise ValueError("orchestration exceeded its step budget")
        if self.proposed_schedule is not None and AgentName.PLAN_COMPOSER not in workers:
            raise ValueError("only Plan Composer can return a proposed schedule")
        if any(result.evaluation_only for result in self.worker_results) and self.public_eligible:
            raise ValueError("fixture/evaluation worker output cannot become public eligible")
        if self.trace.direct_write_count or self.trace.service_role_used:
            raise ValueError("Stage 7 orchestration cannot write or use service-role credentials")
        return self
