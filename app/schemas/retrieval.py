"""Versioned Stage 5 contracts for read-only hybrid retrieval.

The request deliberately has no workspace identifier.  A trusted server layer
creates :class:`AuthenticatedRetrievalScope` from the authenticated session and
passes it to the gateway separately from user-controlled input.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Self
from uuid import UUID, uuid4

from pydantic import Field, model_validator

from app.schemas.content import ConditionKey, Contract, Domain, Stage, Text


RETRIEVAL_SCHEMA_VERSION = "5.0.0"
EvidenceLane = Literal["guideline", "weekly_profile"]
JourneyUnit = Literal["none", "week", "day"]
ComponentName = Literal[
    "exact_sql", "public_full_text", "public_vector",
    "personal_full_text", "personal_vector", "graph", "weekly_profile",
]

RetrievalPurpose = Literal[
    "public_guidance", "personal_record_lookup", "causal_explanation",
    "mixed_personalized_guidance",
]
SupportKind = Literal[
    "public_guidance", "personal_record", "personal_constraint",
    "graph_relationship",
]
PersonalContextKind = Literal[
    "allergies", "conditions", "restrictions", "medications", "symptoms",
    "appointments", "plans", "questions", "journey", "documents",
]
JourneyRelation = Literal[
    "current", "explicit_other", "overridden_to_current", "unconfirmed_current",
]
SupportState = Literal[
    "unsupported", "partially_supported", "fully_supported",
    "clarification_required",
]

POLICY_VERSION = "stage5-answerability-v3"
DOMAIN_PERSONAL_CONTEXTS: dict[Domain, tuple[PersonalContextKind, ...]] = {
    "journey": ("journey", "documents"),
    "nutrition": ("allergies", "conditions", "restrictions", "documents"),
    "movement": ("conditions", "restrictions", "plans", "documents"),
    "wellbeing": ("conditions", "questions", "documents"),
    "symptoms": ("conditions", "restrictions", "documents"),
    "preparation": ("appointments", "plans", "questions", "documents"),
    "followup": ("appointments", "plans", "questions", "documents"),
}


def canonical_evidence_policy_values(
    purpose: RetrievalPurpose, domain: Domain,
) -> dict[str, Any]:
    """Return the only valid Stage 5 policy fields for one trusted purpose."""

    required: dict[RetrievalPurpose, list[SupportKind]] = {
        "public_guidance": ["public_guidance"],
        "personal_record_lookup": ["personal_record"],
        "causal_explanation": ["graph_relationship"],
        "mixed_personalized_guidance": [
            "public_guidance", "personal_constraint",
        ],
    }
    contexts = list(DOMAIN_PERSONAL_CONTEXTS[domain])
    if purpose == "personal_record_lookup":
        contexts = [
            "allergies", "conditions", "restrictions", "medications",
            "symptoms", "appointments", "plans", "questions", "journey",
            "documents",
        ]
    elif purpose == "causal_explanation":
        contexts = ["restrictions", "plans", "questions", "documents"]
    return {
        "policy_version": POLICY_VERSION,
        "policy_id": f"{POLICY_VERSION}:{purpose}:{domain}",
        "purpose": purpose,
        "domain": domain,
        "required_support": required[purpose],
        "personal_context_kinds": contexts,
        "trusted_server_created": True,
    }


class JourneyPosition(Contract):
    stage: Stage
    unit: JourneyUnit
    exact: int | None = None
    range_start: int | None = None
    range_end: int | None = None

    @model_validator(mode="after")
    def validate_position(self) -> Self:
        if self.stage == "possible_pregnancy":
            if self.unit != "none" or any(
                value is not None for value in (self.exact, self.range_start, self.range_end)
            ):
                raise ValueError("possible pregnancy cannot assert a week or day")
            return self
        if self.unit == "none":
            raise ValueError("pregnancy and postpartum require a week or day")
        has_exact = self.exact is not None
        has_range = self.range_start is not None or self.range_end is not None
        if has_exact == has_range:
            raise ValueError("provide exactly one exact position or one complete range")
        start = self.exact if has_exact else self.range_start
        end = self.exact if has_exact else self.range_end
        if start is None or end is None or start > end:
            raise ValueError("journey range must be complete and ordered")
        if self.stage == "pregnancy":
            valid = self.unit == "week" and 1 <= start <= end <= 42
        elif self.unit == "week":
            valid = 1 <= start <= end <= 12
        else:
            valid = 0 <= start <= end <= 7
        if not valid:
            raise ValueError("journey position is outside the supported range")
        return self

    @property
    def start(self) -> int | None:
        return self.exact if self.exact is not None else self.range_start

    @property
    def end(self) -> int | None:
        return self.exact if self.exact is not None else self.range_end


class RetrievalRequest(Contract):
    """User-controlled retrieval input; workspace scope is intentionally absent."""

    schema_version: Literal["5.0.0"] = RETRIEVAL_SCHEMA_VERSION
    request_id: UUID = Field(default_factory=uuid4)
    question: Text
    domain: Domain
    journey: JourneyPosition
    jurisdiction: Text
    evidence_lanes: list[EvidenceLane] = Field(
        default_factory=lambda: ["guideline", "weekly_profile"], min_length=1
    )
    include_graph: bool = True
    max_candidates: int = Field(default=5, ge=1, le=20)
    timeout_ms: int = Field(default=2_000, ge=10, le=10_000)


class AuthenticatedRetrievalScope(Contract):
    """Trusted scope resolved from a verified user session by server code."""

    schema_version: Literal["5.0.0"] = RETRIEVAL_SCHEMA_VERSION
    workspace_id: UUID
    care_episode_id: UUID
    owner_user_id: UUID
    session_subject: UUID
    state_version: int = Field(ge=1)
    authenticated_at: datetime

    @model_validator(mode="after")
    def require_owner_session(self) -> Self:
        if self.owner_user_id != self.session_subject:
            raise ValueError("retrieval scope must belong to the authenticated owner")
        if self.care_episode_id != self.workspace_id:
            raise ValueError("owner-only v1 uses the workspace as its care-episode boundary")
        return self


class EvidenceRequirementPolicy(Contract):
    """Canonical server policy; independent policy fields cannot be fabricated."""

    policy_version: Literal["stage5-answerability-v3"]
    policy_id: Text
    purpose: RetrievalPurpose
    domain: Domain
    required_support: list[SupportKind] = Field(min_length=1)
    personal_context_kinds: list[PersonalContextKind] = Field(default_factory=list)
    trusted_server_created: Literal[True] = True

    @model_validator(mode="after")
    def require_canonical_policy(self) -> Self:
        expected = canonical_evidence_policy_values(self.purpose, self.domain)
        observed = self.model_dump(mode="python")
        if observed != expected:
            raise ValueError(
                "retrieval policy fields must exactly match the canonical "
                "purpose/domain policy"
            )
        return self


class TrustedRetrievalState(Contract):
    """Database-derived scope/applicability used before cache or filtering."""

    scope: AuthenticatedRetrievalScope
    current_journey: JourneyPosition | None = None
    requested_journey: JourneyPosition
    effective_journey: JourneyPosition
    journey_relation: JourneyRelation
    active_conditions: list[ConditionKey] = Field(default_factory=list)
    caller_state_version_was_stale: bool
    cache_state_version: int = Field(ge=1)
    jurisdiction_source: Literal["request_profile"]

    @model_validator(mode="after")
    def cache_version_is_server_version(self) -> Self:
        if self.cache_state_version != self.scope.state_version:
            raise ValueError("cache state version must come from authenticated scope")
        return self


class TrustedRetrievalQuery(Contract):
    """Internal query built from user text plus trusted state and policy."""

    request_id: UUID
    question: Text
    domain: Domain
    journey: JourneyPosition
    jurisdiction: Text
    evidence_lanes: list[EvidenceLane] = Field(min_length=1)
    active_conditions: list[ConditionKey] = Field(default_factory=list)
    include_graph: bool
    max_candidates: int = Field(ge=1, le=20)
    timeout_ms: int = Field(ge=10, le=10_000)
    policy: EvidenceRequirementPolicy
    trusted_state: TrustedRetrievalState

    @model_validator(mode="after")
    def trusted_fields_agree(self) -> Self:
        if self.domain != self.policy.domain:
            raise ValueError("trusted query domain and policy domain disagree")
        if self.journey != self.trusted_state.effective_journey:
            raise ValueError("trusted query journey must equal effective journey")
        if self.active_conditions != self.trusted_state.active_conditions:
            raise ValueError("trusted query conditions must come from trusted state")
        return self


class SourceSpan(Contract):
    source_id: Text
    evidence_id: Text | None = None
    source_block_ids: list[Text] = Field(default_factory=list)
    page: int | None = Field(default=None, ge=1)
    locator: str = ""
    start_char: int | None = Field(default=None, ge=0)
    end_char: int | None = Field(default=None, ge=0)
    exact_text: Text
    text_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def ordered_character_span(self) -> Self:
        if (self.start_char is None) != (self.end_char is None):
            raise ValueError("character offsets must be present together")
        if self.start_char is not None and self.start_char >= self.end_char:
            raise ValueError("source span end must follow its start")
        return self


class CandidateProvenance(Contract):
    corpus_version: str | None = None
    release_id: UUID | None = None
    release_fingerprint: str | None = None
    source_version: str | None = None
    embedding_provider: str | None = None
    embedding_model: str | None = None
    filter_version: Text = "stage5-filter-v1"
    fixture_only: bool = False


class PublicEvidenceCandidate(Contract):
    candidate_id: Text
    evidence_id: Text
    source_id: Text
    source_title: Text
    text: Text
    evidence_lane: EvidenceLane
    domain: Domain
    journey: JourneyPosition
    jurisdictions: list[Text] = Field(min_length=1)
    conditions_required: list[ConditionKey] = Field(default_factory=list)
    conditions_excluded: list[ConditionKey] = Field(default_factory=list)
    release_status: Literal["published"] = "published"
    source_status: Literal["published"] = "published"
    candidate_status: Literal["published"] = "published"
    allowed_use: list[Literal["store", "embed", "display"]] = Field(min_length=1)
    spans: list[SourceSpan] = Field(min_length=1)
    authority_score: float = Field(ge=0, le=1)
    applicability_score: float = Field(ge=0, le=1)
    provenance: CandidateProvenance


class PersonalFactCandidate(Contract):
    fact_id: UUID
    fact_type: Literal[
        "allergy", "dietary_restriction", "medical_history", "medication",
        "clinician_instruction", "feeding_status", "delivery_history", "other",
    ]
    value: Any
    source_kind: Literal["user_reported", "document_extracted", "human_reviewed"]
    confirmation_status: Literal["confirmed"] = "confirmed"
    record_only: bool = False
    source_document_id: UUID | None = None
    source_document_fact_id: UUID | None = None
    valid_from: datetime
    valid_to: datetime | None = None
    provenance: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def medication_is_record_only(self) -> Self:
        if self.fact_type == "medication" and not self.record_only:
            raise ValueError("medication facts must remain record-only")
        return self


class PersonalPassageCandidate(Contract):
    candidate_id: Text
    chunk_id: UUID
    document_id: UUID
    document_status: Literal["confirmed"] = "confirmed"
    text: Text
    span: SourceSpan
    provenance: CandidateProvenance


class JourneyStateSnapshot(Contract):
    state_id: UUID
    stage: Stage
    timing_source: Text
    gestational_week: int | None = Field(default=None, ge=1, le=42)
    gestational_day: int | None = Field(default=None, ge=0, le=6)
    postpartum_week: int | None = Field(default=None, ge=1, le=12)
    postpartum_day: int | None = Field(default=None, ge=0, le=7)
    approximate_month_min: int | None = Field(default=None, ge=1, le=10)
    approximate_month_max: int | None = Field(default=None, ge=1, le=10)
    user_confirmed: bool
    has_dating_conflict: bool
    version: int = Field(ge=1)


class AppointmentSnapshot(Contract):
    appointment_id: UUID
    scheduled_for: datetime | None = None
    appointment_type: str = ""
    status: Literal["planned", "confirmed", "completed", "cancelled"]


class MedicationRecord(Contract):
    medication_id: UUID
    name_as_written: Text
    context_text: str = ""
    status: Literal["confirmed"] = "confirmed"
    record_only: Literal[True] = True


class SymptomRecord(Contract):
    symptom_id: UUID
    description: Text
    reported_at: datetime
    safety_route: Literal["urgent", "clarify", "no_match"]
    matched_rule_ids: list[str] = Field(default_factory=list)
    safety_evaluation_only: Literal[True] = True


class PlanStateSnapshot(Contract):
    plan_id: UUID
    version: int = Field(ge=1)
    status: Literal["draft", "user_reviewed", "saved", "active", "stale", "replaced", "archived"]
    stale_reasons: list[str] = Field(default_factory=list)


class ClarificationQuestion(Contract):
    question_id: UUID
    question: Text
    status: Literal["draft", "saved", "stale"]
    source_fact_ids: list[UUID] = Field(default_factory=list)
    stale_reasons: list[str] = Field(default_factory=list)


class UnresolvedConflict(Contract):
    conflict_id: UUID
    fact_type: str
    proposed_values: list[Any] = Field(min_length=1)
    source_document_ids: list[UUID] = Field(default_factory=list)
    clarification_question_ids: list[UUID] = Field(default_factory=list)
    state: Literal["requires_clarification"] = "requires_clarification"


class MissingInformation(Contract):
    field: Text
    reason: Text
    required_for: list[Text] = Field(min_length=1)


class AnswerabilityAssessment(Contract):
    policy_id: Text
    purpose: RetrievalPurpose
    support_state: SupportState
    ordinary_generation_allowed: bool
    public_guidance_supported: bool
    personal_record_supported: bool
    personal_constraints_present: bool
    graph_relationship_supported: bool
    required_support: list[SupportKind] = Field(min_length=1)
    satisfied_support: list[SupportKind] = Field(default_factory=list)
    missing_support: list[SupportKind] = Field(default_factory=list)
    relevant_conflict_ids: list[str] = Field(default_factory=list)
    relevant_missing_fields: list[Text] = Field(default_factory=list)
    blocking_reasons: list[Text] = Field(default_factory=list)

    @model_validator(mode="after")
    def generation_matches_support(self) -> Self:
        if self.ordinary_generation_allowed != (
            self.support_state == "fully_supported" and not self.blocking_reasons
        ):
            raise ValueError("ordinary generation requires full support and no runtime block")
        if set(self.satisfied_support) & set(self.missing_support):
            raise ValueError("support cannot be both satisfied and missing")
        if set(self.satisfied_support) | set(self.missing_support) != set(self.required_support):
            raise ValueError("every required support kind needs a decision")
        return self


class ExactPersonalContext(Contract):
    journey_state: JourneyStateSnapshot | None = None
    confirmed_facts: list[PersonalFactCandidate] = Field(default_factory=list)
    medications: list[MedicationRecord] = Field(default_factory=list)
    symptoms: list[SymptomRecord] = Field(default_factory=list)
    appointments: list[AppointmentSnapshot] = Field(default_factory=list)
    plan_states: list[PlanStateSnapshot] = Field(default_factory=list)
    open_questions: list[ClarificationQuestion] = Field(default_factory=list)
    unresolved_conflicts: list[UnresolvedConflict] = Field(default_factory=list)
    missing_information: list[MissingInformation] = Field(default_factory=list)


class SafetyContextSnapshot(Contract):
    """Separate future Stage 6 input; never accidental answer support."""

    journey_state: JourneyStateSnapshot | None = None
    active_restrictions: list[PersonalFactCandidate] = Field(default_factory=list)
    medications: list[MedicationRecord] = Field(default_factory=list)
    symptoms: list[SymptomRecord] = Field(default_factory=list)
    unresolved_conflicts: list[UnresolvedConflict] = Field(default_factory=list)
    excluded_from_stage5_answerability: Literal[True] = True


class GraphPathNode(Contract):
    node_id: UUID
    node_type: Literal[
        "document", "fact", "restriction", "symptom", "appointment",
        "question", "plan", "plan_item", "person", "journey_state",
        "weekly_profile", "document_fact", "medication_mention", "allergy",
        "condition", "guideline_evidence", "human_review_case", "symptom_event",
    ]
    entity_id: UUID | None = None
    entity_release_id: UUID | None = None
    entity_key: str | None = None
    label: Text
    source_document_id: UUID | None = None

    @model_validator(mode="after")
    def typed_entity_reference(self) -> Self:
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


class GraphPathEdge(Contract):
    edge_id: UUID
    relation: Literal[
        "supports", "IN_WEEK", "EXTRACTED_FROM", "CONFLICTS_WITH",
        "SUPERSEDES", "CONSTRAINS", "SUPPORTED_BY", "TRIGGERED",
        "SCHEDULED_FOR", "NEEDS_CLARIFICATION", "REVIEWED_BY",
    ]
    from_node_id: UUID
    to_node_id: UUID


class GraphPath(Contract):
    path_id: Text
    workspace_id: UUID
    nodes: list[GraphPathNode] = Field(min_length=1, max_length=9)
    edges: list[GraphPathEdge] = Field(default_factory=list, max_length=8)
    depth: int = Field(ge=0, le=8)
    provenance: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def path_shape_matches_depth(self) -> Self:
        if len(self.edges) != self.depth or len(self.nodes) != self.depth + 1:
            raise ValueError("graph path nodes and edges do not match depth")
        if len({node.node_id for node in self.nodes}) != len(self.nodes):
            raise ValueError("graph path cannot contain a cycle")
        return self


class RankedRetrievalCandidate(Contract):
    candidate_id: Text
    candidate_kind: Literal["public_evidence", "personal_passage"]
    rank: int = Field(ge=1)
    final_score: float = Field(ge=0)
    component_ranks: dict[str, int] = Field(default_factory=dict)
    component_scores: dict[str, float] = Field(default_factory=dict)
    authority_score: float = Field(ge=0, le=1)
    applicability_score: float = Field(ge=0, le=1)
    exact_position_fit: bool
    source_version: str | None = None
    stable_tie_breaker: Text


class RerankerInput(Contract):
    schema_version: Literal["5.0.0"] = RETRIEVAL_SCHEMA_VERSION
    request_id: UUID
    question: Text
    candidates: list[RankedRetrievalCandidate]
    learned_reranker_enabled: Literal[False] = False


class RetrievalFailure(Contract):
    code: Literal[
        "database_unavailable", "vector_unavailable", "timeout",
        "invalid_candidate", "no_eligible_evidence", "no_approved_public_content",
        "malformed_response",
    ]
    recoverable: bool
    component: ComponentName | None = None
    detail: Text


class RetrievalComponentResult(Contract):
    component: ComponentName
    status: Literal["ok", "degraded", "failed", "skipped"]
    attempted: int = Field(ge=0)
    returned: int = Field(ge=0)
    rejected_by_filters: int = Field(ge=0)
    latency_ms: float = Field(ge=0)
    retries: int = Field(default=0, ge=0, le=1)
    failure: RetrievalFailure | None = None


class AbstentionState(Contract):
    should_abstain: bool
    reason: Literal[
        "none", "no_eligible_evidence", "no_approved_public_content",
        "database_unavailable", "retrieval_timeout", "unresolved_conflict",
        "missing_information", "partial_support",
    ] = "none"
    detail: str = ""

    @model_validator(mode="after")
    def abstention_reason_matches(self) -> Self:
        if self.should_abstain == (self.reason == "none"):
            raise ValueError("abstention flag and reason disagree")
        return self


class WeeklyProfileCandidate(Contract):
    profile_id: Text
    release_id: UUID
    corpus_version: Text
    journey: JourneyPosition
    jurisdiction: list[Text] = Field(min_length=1)
    hero: dict[str, Any]
    card_slots: dict[str, Any]
    evidence_ids: list[Text] = Field(default_factory=list)
    status: Literal["published"] = "published"
    fixture_only: bool = False


class EvidencePacket(Contract):
    schema_version: Literal["5.0.0"] = RETRIEVAL_SCHEMA_VERSION
    request_id: UUID
    workspace_id: UUID
    care_episode_id: UUID
    question: Text
    domain: Domain
    journey: JourneyPosition
    jurisdiction: Text
    retrieval_policy: EvidenceRequirementPolicy
    trusted_state: TrustedRetrievalState
    answerability: AnswerabilityAssessment
    personal_context_minimized: Literal[True] = True
    safety_context_is_separate: Literal[True] = True
    confirmed_personal_facts: list[PersonalFactCandidate] = Field(default_factory=list)
    permitted_personal_passages: list[PersonalPassageCandidate] = Field(default_factory=list)
    medication_records: list[MedicationRecord] = Field(default_factory=list)
    symptom_records: list[SymptomRecord] = Field(default_factory=list)
    appointments: list[AppointmentSnapshot] = Field(default_factory=list)
    plan_states: list[PlanStateSnapshot] = Field(default_factory=list)
    open_questions: list[ClarificationQuestion] = Field(default_factory=list)
    weekly_profile: WeeklyProfileCandidate | None = None
    approved_guideline_passages: list[PublicEvidenceCandidate] = Field(default_factory=list)
    graph_paths: list[GraphPath] = Field(default_factory=list)
    ranked_candidates: list[RankedRetrievalCandidate] = Field(default_factory=list)
    source_ids: list[Text] = Field(default_factory=list)
    evidence_ids: list[Text] = Field(default_factory=list)
    exact_spans: list[SourceSpan] = Field(default_factory=list)
    provenance_versions: dict[str, str] = Field(default_factory=dict)
    missing_information: list[MissingInformation] = Field(default_factory=list)
    unresolved_conflicts: list[UnresolvedConflict] = Field(default_factory=list)
    allowed_claim_types: list[Literal[
        "confirmed_personal_record", "record_only_medication",
        "approved_guideline_paraphrase", "published_weekly_profile",
        "clarification_required", "evaluation_only_symptom_record",
    ]] = Field(default_factory=list)
    required_citations: list[Text] = Field(default_factory=list)
    component_results: list[RetrievalComponentResult]
    failures: list[RetrievalFailure] = Field(default_factory=list)
    corpus_mode: Literal["production_release", "controlled_fixture", "no_public_release"]
    abstention: AbstentionState

    @model_validator(mode="after")
    def packet_fields_agree(self) -> Self:
        scope = self.trusted_state.scope
        policy = self.retrieval_policy
        answer = self.answerability
        if self.workspace_id != scope.workspace_id or self.care_episode_id != scope.care_episode_id:
            raise ValueError("packet workspace/care episode must equal trusted scope")
        if self.journey != self.trusted_state.effective_journey:
            raise ValueError("packet journey must equal trusted effective journey")
        if self.domain != policy.domain:
            raise ValueError("packet domain and retrieval policy domain disagree")
        if (answer.policy_id != policy.policy_id or
                answer.purpose != policy.purpose or
                answer.required_support != policy.required_support):
            raise ValueError("packet policy and answerability contract disagree")
        if self.abstention.should_abstain == answer.ordinary_generation_allowed:
            raise ValueError("abstention must be inverse of ordinary generation permission")
        if answer.support_state != "fully_supported" and not self.abstention.should_abstain:
            raise ValueError("incomplete support requires abstention")
        if (answer.support_state == "fully_supported" and
                not answer.blocking_reasons and
                not answer.relevant_conflict_ids and
                not answer.relevant_missing_fields and
                self.abstention.should_abstain):
            raise ValueError("fully supported unblocked evidence must not abstain")
        conflict_ids = [str(item.conflict_id) for item in self.unresolved_conflicts]
        missing_fields = [item.field for item in self.missing_information]
        if answer.relevant_conflict_ids != conflict_ids:
            raise ValueError("packet conflicts and answerability conflicts disagree")
        if answer.relevant_missing_fields != missing_fields:
            raise ValueError("packet missing information and answerability disagree")
        return self


class RetrievalTrace(Contract):
    schema_version: Literal["5.0.0"] = RETRIEVAL_SCHEMA_VERSION
    request_id: UUID
    started_at: datetime
    completed_at: datetime
    total_latency_ms: float = Field(ge=0)
    normalized_query: Text
    public_cache_key: Text
    personal_cache_key: Text
    filter_version: Text
    ranking_version: Text
    policy_id: Text
    resolved_state_version: int = Field(ge=1)
    journey_relation: JourneyRelation
    component_results: list[RetrievalComponentResult]
    rejected_candidate_ids: list[Text] = Field(default_factory=list)
    deterministic_order_digest: str = Field(pattern=r"^[a-f0-9]{64}$")


class RetrievalResult(Contract):
    packet: EvidencePacket
    trace: RetrievalTrace

    @model_validator(mode="after")
    def packet_and_trace_agree(self) -> Self:
        if self.packet.request_id != self.trace.request_id:
            raise ValueError("packet and trace request IDs disagree")
        if self.packet.retrieval_policy.policy_id != self.trace.policy_id:
            raise ValueError("packet and trace policy IDs disagree")
        if self.packet.trusted_state.journey_relation != self.trace.journey_relation:
            raise ValueError("packet and trace journey relations disagree")
        if self.packet.trusted_state.cache_state_version != self.trace.resolved_state_version:
            raise ValueError("packet and trace state versions disagree")
        if self.packet.component_results != self.trace.component_results:
            raise ValueError("packet and trace component results disagree")
        return self
