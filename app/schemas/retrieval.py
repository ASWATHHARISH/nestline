"""Versioned Stage 5 contracts for read-only hybrid retrieval.

The request deliberately has no workspace identifier.  A trusted server layer
creates :class:`AuthenticatedRetrievalScope` from the authenticated session and
passes it to the gateway separately from user-controlled input.
"""

from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json
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
RuntimeBlocker = Literal["database_unavailable", "retrieval_timeout"]
AbstentionReason = Literal[
    "none", "no_eligible_evidence", "no_approved_public_content",
    "database_unavailable", "retrieval_timeout", "unresolved_conflict",
    "missing_information", "partial_support",
]
CorpusMode = Literal[
    "production_release", "controlled_fixture", "no_public_release",
]
AllowedClaimType = Literal[
    "confirmed_personal_record", "record_only_medication",
    "approved_guideline_paraphrase", "published_weekly_profile",
    "clarification_required", "evaluation_only_symptom_record",
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
    def trusted_state_is_structurally_consistent(self) -> Self:
        if self.cache_state_version != self.scope.state_version:
            raise ValueError("cache state version must come from authenticated scope")
        current = self.current_journey
        requested = self.requested_journey
        effective = self.effective_journey
        relation = self.journey_relation
        if relation == "current":
            valid = current is not None and requested == effective == current
        elif relation == "explicit_other":
            valid = (current is not None and effective == requested
                     and requested != current)
        elif relation == "overridden_to_current":
            valid = (current is not None and effective == current
                     and requested != current)
        else:
            valid = current is None and effective == requested
        if not valid:
            raise ValueError(
                "trusted journey relation contradicts current/requested/effective state"
            )
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


def derive_answerability_values(
    required_support: list[SupportKind],
    *,
    public_guidance_supported: bool,
    personal_record_supported: bool,
    personal_constraints_present: bool,
    graph_relationship_supported: bool,
    relevant_conflict_ids: list[str],
    relevant_missing_fields: list[str],
    blocking_reasons: list[RuntimeBlocker],
) -> dict[str, Any]:
    """Derive the only coherent answerability state from trusted observations."""

    support = {
        "public_guidance": public_guidance_supported,
        "personal_record": personal_record_supported,
        "personal_constraint": personal_constraints_present,
        "graph_relationship": graph_relationship_supported,
    }
    satisfied = [kind for kind in required_support if support[kind]]
    missing = [kind for kind in required_support if not support[kind]]
    if relevant_conflict_ids or relevant_missing_fields:
        state: SupportState = "clarification_required"
    elif not missing:
        state = "fully_supported"
    elif satisfied:
        state = "partially_supported"
    else:
        state = "unsupported"
    generation_allowed = (
        state == "fully_supported"
        and not blocking_reasons
        and not relevant_conflict_ids
        and not relevant_missing_fields
    )
    return {
        "satisfied_support": satisfied,
        "missing_support": missing,
        "support_state": state,
        "ordinary_generation_allowed": generation_allowed,
    }


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
    blocking_reasons: list[RuntimeBlocker] = Field(default_factory=list)

    @model_validator(mode="after")
    def generation_matches_derived_support(self) -> Self:
        expected = derive_answerability_values(
            self.required_support,
            public_guidance_supported=self.public_guidance_supported,
            personal_record_supported=self.personal_record_supported,
            personal_constraints_present=self.personal_constraints_present,
            graph_relationship_supported=self.graph_relationship_supported,
            relevant_conflict_ids=self.relevant_conflict_ids,
            relevant_missing_fields=self.relevant_missing_fields,
            blocking_reasons=self.blocking_reasons,
        )
        observed = {
            "satisfied_support": self.satisfied_support,
            "missing_support": self.missing_support,
            "support_state": self.support_state,
            "ordinary_generation_allowed": self.ordinary_generation_allowed,
        }
        if observed != expected:
            raise ValueError("answerability fields must equal their canonical derivation")
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
        for index, edge in enumerate(self.edges):
            if (edge.from_node_id != self.nodes[index].node_id or
                    edge.to_node_id != self.nodes[index + 1].node_id):
                raise ValueError("graph edge must connect adjacent declared nodes")
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

    @model_validator(mode="after")
    def status_and_failure_agree(self) -> Self:
        if self.status == "failed" and self.failure is None:
            raise ValueError("failed retrieval component requires a failure")
        if self.status in {"ok", "skipped"} and self.failure is not None:
            raise ValueError("successful or skipped component cannot carry a failure")
        if (self.status == "degraded" and self.failure is None
                and self.rejected_by_filters == 0):
            raise ValueError("degraded component requires a failure or filtered results")
        if (self.failure is not None and self.failure.component is not None
                and self.failure.component != self.component):
            raise ValueError("retrieval failure belongs to a different component")
        return self


class AbstentionState(Contract):
    should_abstain: bool
    reason: AbstentionReason = "none"
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


def normalize_retrieval_query(value: str) -> str:
    return " ".join(value.casefold().split())


def ranked_candidate_digest(candidates: list[RankedRetrievalCandidate]) -> str:
    payload = [item.candidate_id for item in candidates]
    raw = json.dumps(payload, separators=(",", ":"))
    return sha256(raw.encode("utf-8")).hexdigest()


def derive_abstention_reason(
    answerability: AnswerabilityAssessment, corpus_mode: CorpusMode,
) -> AbstentionReason:
    blockers = set(answerability.blocking_reasons)
    if "database_unavailable" in blockers:
        return "database_unavailable"
    if "retrieval_timeout" in blockers:
        return "retrieval_timeout"
    if answerability.relevant_conflict_ids:
        return "unresolved_conflict"
    if answerability.relevant_missing_fields:
        return "missing_information"
    if answerability.support_state == "fully_supported":
        return "none"
    if answerability.support_state == "partially_supported":
        return "partial_support"
    if ("public_guidance" in answerability.required_support
            and not answerability.public_guidance_supported
            and corpus_mode == "no_public_release"):
        return "no_approved_public_content"
    return "no_eligible_evidence"


def derive_packet_inventory(
    *,
    confirmed_facts: list[PersonalFactCandidate],
    personal_passages: list[PersonalPassageCandidate],
    medications: list[MedicationRecord],
    symptoms: list[SymptomRecord],
    appointments: list[AppointmentSnapshot],
    plan_states: list[PlanStateSnapshot],
    open_questions: list[ClarificationQuestion],
    public_passages: list[PublicEvidenceCandidate],
    weekly_profile: WeeklyProfileCandidate | None,
    unresolved_conflicts: list[UnresolvedConflict],
    missing_information: list[MissingInformation],
) -> dict[str, Any]:
    evidence_ids = sorted({item.evidence_id for item in public_passages})
    source_ids = sorted({item.source_id for item in public_passages})
    spans = (
        [span for item in public_passages for span in item.spans]
        + [item.span for item in personal_passages]
    )
    citations = sorted(set(
        evidence_ids
        + [f"personal-passage:{item.chunk_id}" for item in personal_passages]
        + [f"personal-fact:{item.fact_id}" for item in confirmed_facts]
        + [f"medication-record:{item.medication_id}" for item in medications]
        + [f"appointment:{item.appointment_id}" for item in appointments]
    ))
    claims: list[AllowedClaimType] = []
    if (confirmed_facts or personal_passages or appointments
            or plan_states or open_questions):
        claims.append("confirmed_personal_record")
    if medications:
        claims.append("record_only_medication")
    if symptoms:
        claims.append("evaluation_only_symptom_record")
    if public_passages:
        claims.append("approved_guideline_paraphrase")
    if weekly_profile is not None:
        claims.append("published_weekly_profile")
    if unresolved_conflicts or missing_information:
        claims.append("clarification_required")
    corpus_mode: CorpusMode = (
        "controlled_fixture"
        if any(item.provenance.fixture_only for item in public_passages)
        or (weekly_profile is not None and weekly_profile.fixture_only)
        else "production_release"
        if public_passages or weekly_profile is not None
        else "no_public_release"
    )
    return {
        "evidence_ids": evidence_ids,
        "source_ids": source_ids,
        "exact_spans": spans,
        "required_citations": citations,
        "allowed_claim_types": claims,
        "corpus_mode": corpus_mode,
    }


def _journey_covers(container: JourneyPosition, target: JourneyPosition) -> bool:
    if container.stage != target.stage or container.unit != target.unit:
        return False
    if target.unit == "none":
        return True
    return (container.start is not None and target.start is not None
            and container.end is not None and target.end is not None
            and container.start <= target.start <= target.end <= container.end)


def _span_hash_is_valid(span: SourceSpan) -> bool:
    return sha256(span.exact_text.encode("utf-8")).hexdigest() == span.text_sha256


class EvidencePacket(Contract):
    schema_version: Literal["5.0.0"] = RETRIEVAL_SCHEMA_VERSION
    request_id: UUID
    workspace_id: UUID
    care_episode_id: UUID
    question: Text
    domain: Domain
    journey: JourneyPosition
    jurisdiction: Text
    evidence_lanes: list[EvidenceLane] = Field(min_length=1)
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
    allowed_claim_types: list[AllowedClaimType] = Field(default_factory=list)
    required_citations: list[Text] = Field(default_factory=list)
    component_results: list[RetrievalComponentResult]
    failures: list[RetrievalFailure] = Field(default_factory=list)
    corpus_mode: CorpusMode
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
        if self.jurisdiction != self.jurisdiction.upper():
            raise ValueError("packet jurisdiction must be canonical uppercase")
        if len(set(self.evidence_lanes)) != len(self.evidence_lanes):
            raise ValueError("packet evidence lanes must be unique")
        if (answer.policy_id != policy.policy_id or
                answer.purpose != policy.purpose or
                answer.required_support != policy.required_support):
            raise ValueError("packet policy and answerability contract disagree")

        conflict_ids = [str(item.conflict_id) for item in self.unresolved_conflicts]
        missing_fields = [item.field for item in self.missing_information]
        if answer.relevant_conflict_ids != conflict_ids:
            raise ValueError("packet conflicts and answerability conflicts disagree")
        if answer.relevant_missing_fields != missing_fields:
            raise ValueError("packet missing information and answerability disagree")
        expected_reason = derive_abstention_reason(answer, self.corpus_mode)
        if (self.abstention.reason != expected_reason or
                self.abstention.should_abstain != (expected_reason != "none")):
            raise ValueError("packet abstention must equal its canonical derivation")

        expected = derive_packet_inventory(
            confirmed_facts=self.confirmed_personal_facts,
            personal_passages=self.permitted_personal_passages,
            medications=self.medication_records, symptoms=self.symptom_records,
            appointments=self.appointments, plan_states=self.plan_states,
            open_questions=self.open_questions,
            public_passages=self.approved_guideline_passages,
            weekly_profile=self.weekly_profile,
            unresolved_conflicts=self.unresolved_conflicts,
            missing_information=self.missing_information,
        )
        for field, value in expected.items():
            if getattr(self, field) != value:
                raise ValueError(f"packet {field} does not match selected evidence")

        ranked_ids = [item.candidate_id for item in self.ranked_candidates]
        selected = {item.candidate_id: "public_evidence"
                    for item in self.approved_guideline_passages}
        selected.update({item.candidate_id: "personal_passage"
                         for item in self.permitted_personal_passages})
        if len(selected) != (len(self.approved_guideline_passages)
                             + len(self.permitted_personal_passages)):
            raise ValueError("selected candidate IDs must be unique")
        if ranked_ids != list(dict.fromkeys(ranked_ids)) or set(ranked_ids) != set(selected):
            raise ValueError("ranked candidates must equal selected candidates")
        if [item.rank for item in self.ranked_candidates] != list(range(1, len(ranked_ids) + 1)):
            raise ValueError("ranked candidate ranks must be contiguous and ordered")
        ranked_by_id = {item.candidate_id: item for item in self.ranked_candidates}
        for item in self.ranked_candidates:
            if item.candidate_kind != selected[item.candidate_id]:
                raise ValueError("ranked candidate kind contradicts selected candidate")
            if item.stable_tie_breaker != item.candidate_id:
                raise ValueError("stable tie breaker must equal candidate ID")
            if (set(item.component_ranks) != set(item.component_scores)
                    or any(rank < 1 for rank in item.component_ranks.values())):
                raise ValueError("ranked component score/rank inventories disagree")

        versions = self.provenance_versions
        if set(versions) != {"schema", "filter", "ranking", "policy", "corpus", "release"}:
            raise ValueError("packet provenance version inventory is incomplete")
        if (versions["schema"] != RETRIEVAL_SCHEMA_VERSION or
                versions["policy"] != policy.policy_version or
                any(not value for value in versions.values())):
            raise ValueError("packet provenance versions are inconsistent")

        active = set(self.trusted_state.active_conditions)
        for item in self.approved_guideline_passages:
            if (item.domain != self.domain or item.evidence_lane not in self.evidence_lanes
                    or not _journey_covers(item.journey, self.journey)
                    or (self.jurisdiction not in {value.upper() for value in item.jurisdictions}
                        and "GLOBAL" not in {value.upper() for value in item.jurisdictions})
                    or not set(item.conditions_required).issubset(active)
                    or bool(set(item.conditions_excluded) & active)
                    or "display" not in item.allowed_use):
                raise ValueError("public candidate contradicts packet applicability")
            ranked = ranked_by_id[item.candidate_id]
            if (ranked.authority_score != item.authority_score
                    or ranked.applicability_score != item.applicability_score
                    or ranked.exact_position_fit != (item.journey.start == item.journey.end)
                    or ranked.source_version != item.provenance.source_version
                    or ("public_vector" in ranked.component_ranks
                        and "embed" not in item.allowed_use)):
                raise ValueError("public candidate and ranking metadata disagree")
            if item.provenance.filter_version != versions["filter"]:
                raise ValueError("public candidate filter version disagrees with packet")
            if (item.provenance.corpus_version is not None
                    and item.provenance.corpus_version != versions["corpus"]):
                raise ValueError("public candidate corpus version disagrees with packet")
            for span in item.spans:
                if (span.source_id != item.source_id
                        or span.evidence_id != item.evidence_id
                        or not _span_hash_is_valid(span)):
                    raise ValueError("public source span contradicts its parent candidate")
        for item in self.permitted_personal_passages:
            ranked = ranked_by_id[item.candidate_id]
            if (item.provenance.filter_version != versions["filter"]
                    or not _span_hash_is_valid(item.span)
                    or ranked.authority_score != 1.0
                    or ranked.applicability_score != 1.0
                    or not ranked.exact_position_fit
                    or ranked.source_version != item.provenance.source_version):
                raise ValueError("personal passage provenance or ranking metadata is invalid")
        if self.weekly_profile is not None:
            profile = self.weekly_profile
            jurisdictions = {value.upper() for value in profile.jurisdiction}
            if (not _journey_covers(profile.journey, self.journey)
                    or (self.jurisdiction not in jurisdictions and "GLOBAL" not in jurisdictions)
                    or profile.corpus_version != versions["corpus"]):
                raise ValueError("weekly profile contradicts packet applicability")
        if any(path.workspace_id != self.workspace_id for path in self.graph_paths):
            raise ValueError("graph path belongs to a different workspace")

        component_map = {item.component: item for item in self.component_results}
        if len(component_map) != len(self.component_results):
            raise ValueError("retrieval components must be unique")
        component_failures = [item.failure for item in self.component_results
                              if item.failure is not None]
        for failure in component_failures:
            if failure not in self.failures:
                raise ValueError("component failure is missing from packet failures")
        for failure in self.failures:
            if failure.component is not None:
                owner = component_map.get(failure.component)
                if owner is None or owner.failure != failure:
                    raise ValueError("packet failure contradicts its owning component")
        exact_failure = component_map.get("exact_sql")
        database_blocked = bool(
            exact_failure and exact_failure.failure
            and exact_failure.failure.code == "database_unavailable"
        )
        timeout_failed = any(item.code == "timeout" for item in self.failures)
        no_public_expected = (
            "public_guidance" in answer.required_support
            and not answer.public_guidance_supported
            and self.corpus_mode == "no_public_release"
        )
        no_public_recorded = any(
            item.code == "no_approved_public_content" for item in self.failures
        )
        if any(item.code == "invalid_candidate" for item in self.failures):
            raise ValueError("malformed candidates must fail closed before packet creation")
        if database_blocked != ("database_unavailable" in answer.blocking_reasons):
            raise ValueError("database blocker contradicts exact-state component")
        if timeout_failed != ("retrieval_timeout" in answer.blocking_reasons):
            raise ValueError("timeout blocker contradicts packet failures")
        if no_public_expected != no_public_recorded:
            raise ValueError("public-release failure state contradicts packet evidence")
        if (any(item.code == "no_eligible_evidence" for item in self.failures)
                and expected_reason != "no_eligible_evidence"):
            raise ValueError("no-eligible-evidence failure contradicts answerability")
        return self


class RetrievalTrace(Contract):
    schema_version: Literal["5.0.0"] = RETRIEVAL_SCHEMA_VERSION
    request_id: UUID
    started_at: datetime
    completed_at: datetime
    total_latency_ms: float = Field(ge=0)
    normalized_query: Text
    jurisdiction: Text
    public_cache_key: Text
    personal_cache_key: Text
    filter_version: Text
    ranking_version: Text
    policy_id: Text
    policy_version: Text
    corpus_version: Text
    release_version: Text
    resolved_state_version: int = Field(ge=1)
    journey_relation: JourneyRelation
    component_results: list[RetrievalComponentResult]
    rejected_candidate_ids: list[Text] = Field(default_factory=list)
    deterministic_order_digest: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def trace_is_canonical(self) -> Self:
        if self.completed_at < self.started_at:
            raise ValueError("retrieval trace completion precedes its start")
        if self.normalized_query != normalize_retrieval_query(self.normalized_query):
            raise ValueError("retrieval trace query is not normalized")
        if self.jurisdiction != self.jurisdiction.upper():
            raise ValueError("retrieval trace jurisdiction is not canonical uppercase")
        return self


class RetrievalResult(Contract):
    packet: EvidencePacket
    trace: RetrievalTrace

    @model_validator(mode="after")
    def packet_and_trace_agree(self) -> Self:
        packet = self.packet
        trace = self.trace
        if packet.request_id != trace.request_id:
            raise ValueError("packet and trace request IDs disagree")
        if packet.retrieval_policy.policy_id != trace.policy_id:
            raise ValueError("packet and trace policy IDs disagree")
        if packet.retrieval_policy.policy_version != trace.policy_version:
            raise ValueError("packet and trace policy versions disagree")
        if packet.trusted_state.journey_relation != trace.journey_relation:
            raise ValueError("packet and trace journey relations disagree")
        if packet.trusted_state.cache_state_version != trace.resolved_state_version:
            raise ValueError("packet and trace state versions disagree")
        if packet.component_results != trace.component_results:
            raise ValueError("packet and trace component results disagree")
        if normalize_retrieval_query(packet.question) != trace.normalized_query:
            raise ValueError("packet question and trace normalized query disagree")
        if packet.jurisdiction != trace.jurisdiction:
            raise ValueError("packet and trace jurisdictions disagree")
        if ranked_candidate_digest(packet.ranked_candidates) != trace.deterministic_order_digest:
            raise ValueError("trace deterministic order digest is invalid")
        versions = packet.provenance_versions
        if (versions["filter"] != trace.filter_version
                or versions["ranking"] != trace.ranking_version
                or versions["policy"] != trace.policy_version
                or versions["corpus"] != trace.corpus_version
                or versions["release"] != trace.release_version):
            raise ValueError("packet provenance and trace versions disagree")
        return self
