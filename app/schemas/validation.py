"""Strict Stage 8 contracts for validation and constrained composition.

The models in this module describe a display gate.  They do not authorize a
persistent write, provide medical clearance, or turn fixture evidence into a
public release.
"""

from __future__ import annotations

from enum import StrEnum
from hashlib import sha256
from typing import Literal, Self
from uuid import UUID, uuid4

from pydantic import Field, model_validator

from app.schemas.content import Contract, Text
from app.schemas.orchestration import (
    AgentName,
    AuthenticatedContextSnapshot,
    OrchestrationResult,
    ProposedAction,
    ProposedSchedule,
)
from app.schemas.retrieval import JourneyPosition, SupportState
from app.schemas.safety import FixedSafetyMessage, SafetyGateResult


VALIDATION_SCHEMA_VERSION = "8.0.0"
VALIDATION_POLICY_VERSION = "stage8-validation-v1"
COMPOSITION_VERSION = "stage8-composition-v1"
SEMANTIC_EVALUATOR_VERSION = "stage8-semantic-contract-v1"


class ValidatorName(StrEnum):
    SCHEMA = "schema_validator"
    STATE_JOURNEY = "state_journey_validator"
    PERSONAL_CONSTRAINT = "personal_constraint_validator"
    EVIDENCE = "evidence_verifier"
    CITATION = "citation_validator"
    BOUNDARY = "boundary_validator"
    CONSISTENCY = "consistency_validator"


VALIDATOR_ORDER = list(ValidatorName)


class ValidationStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    NOT_RUN = "not_run"


class FindingSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class FinalDisposition(StrEnum):
    PASS = "pass"
    CLARIFY = "clarify"
    ABSTAIN = "abstain"
    ESCALATE = "escalate"


class FindingCode(StrEnum):
    SCHEMA_INVALID = "schema_invalid"
    REQUEST_ID_MISMATCH = "request_id_mismatch"
    WORKSPACE_MISMATCH = "workspace_mismatch"
    CARE_EPISODE_MISMATCH = "care_episode_mismatch"
    STALE_STATE_VERSION = "stale_state_version"
    JOURNEY_MISMATCH = "journey_mismatch"
    WRONG_WEEK = "wrong_week"
    WRONG_JURISDICTION = "wrong_jurisdiction"
    ALLERGY_VIOLATION = "allergy_violation"
    RESTRICTION_VIOLATION = "restriction_violation"
    CONDITION_CONTEXT_DROPPED = "condition_context_dropped"
    CONFIRMED_INSTRUCTION_VIOLATION = "confirmed_instruction_violation"
    REQUIRED_CONSTRAINT_DROPPED = "required_constraint_dropped"
    MATERIAL_CLAIM_WITHOUT_EVIDENCE = "material_claim_without_evidence"
    UNSUPPORTED_EVIDENCE_PACKET = "unsupported_evidence_packet"
    PARTIAL_EVIDENCE_PACKET = "partial_evidence_packet"
    RELEVANT_CONFLICT = "relevant_conflict"
    CLAIM_TYPE_NOT_ALLOWED = "claim_type_not_allowed"
    SAFETY_CLARIFICATION_BLOCKED = "safety_clarification_blocked"
    REQUIRED_INFORMATION_MISSING = "required_information_missing"
    FABRICATED_CITATION = "fabricated_citation"
    CITATION_NOT_IN_PACKET = "citation_not_in_packet"
    CITATION_SOURCE_MISMATCH = "citation_source_mismatch"
    SPAN_TEXT_MISMATCH = "span_text_mismatch"
    SPAN_HASH_MISMATCH = "span_hash_mismatch"
    EVIDENCE_UNAPPROVED = "evidence_unapproved"
    EVIDENCE_RETIRED = "evidence_retired"
    EVIDENCE_WRONG_WORKSPACE = "evidence_wrong_workspace"
    CITATION_IRRELEVANT = "citation_irrelevant"
    CITATION_PARTIAL_SUPPORT = "citation_partial_support"
    CITATION_WEAKER_SUPPORT = "citation_weaker_support"
    SEMANTIC_SUPPORT_UNCERTAIN = "semantic_support_uncertain"
    SEMANTIC_EVALUATOR_UNAVAILABLE = "semantic_evaluator_unavailable"
    SEMANTIC_EVALUATOR_TIMEOUT = "semantic_evaluator_timeout"
    DIAGNOSIS = "diagnosis"
    PRESCRIBING_OR_MEDICATION_CHANGE = "prescribing_or_medication_change"
    INFERRED_CLEARANCE = "inferred_clearance"
    UNSAFE_REASSURANCE = "unsafe_reassurance"
    FAKE_PROFESSIONAL_REVIEW = "fake_professional_review"
    UNAUTHORIZED_ACTION = "unauthorized_action"
    PUBLIC_OVERRIDES_PERSONAL = "public_overrides_personal"
    PROVENANCE_LABEL_MISSING = "provenance_label_missing"
    PROVENANCE_LABEL_INVALID = "provenance_label_invalid"
    URGENT_COMPOSITION_BLOCKED = "urgent_composition_blocked"
    PLAN_ITEM_UNVALIDATED = "plan_item_unvalidated"
    PLAN_COMBINED_CONSTRAINT_FAILURE = "plan_combined_constraint_failure"
    PLAN_EVIDENCE_MISMATCH = "plan_evidence_mismatch"
    PLAN_NOT_PROPOSAL_ONLY = "plan_not_proposal_only"
    REPAIR_FAILED = "repair_failed"
    SECOND_REPAIR_PREVENTED = "second_repair_prevented"


class ProvenanceCategory(StrEnum):
    CONFIRMED = "Your confirmed information"
    UPLOADED_RECORD = "Your uploaded record says"
    USER_REPORTED = "You reported"
    PUBLIC_GUIDANCE = "Public guidance says"
    NEEDS_CONFIRMATION = "Needs confirmation"


class ClaimOrigin(StrEnum):
    CONFIRMED_PERSONAL = "confirmed_personal"
    UPLOADED_RECORD = "uploaded_record"
    USER_REPORTED = "user_reported"
    PUBLIC_GUIDANCE = "public_guidance"
    NEEDS_CONFIRMATION = "needs_confirmation"
    PRODUCT = "product"


class ClaimKind(StrEnum):
    HEALTH_GUIDANCE = "health_guidance"
    PERSONAL_RECORD = "personal_record"
    MEDICATION_RECORD = "medication_record"
    USER_REPORT = "user_report"
    PLAN_ITEM = "plan_item"
    PRODUCT_HELP = "product_help"


class ClaimAction(StrEnum):
    DESCRIBE = "describe"
    RECORD_ONLY = "record_only"
    INCLUDE = "include"
    EXCLUDE = "exclude"
    RECOMMEND = "recommend"
    DIAGNOSE = "diagnose"
    PRESCRIBE_START = "prescribe_start"
    PRESCRIBE_STOP = "prescribe_stop"
    PRESCRIBE_CHANGE = "prescribe_change"
    ASSERT_CLEARANCE = "assert_clearance"
    REASSURE = "reassure"


class SemanticSupport(StrEnum):
    SUPPORTED = "supported"
    PARTIAL = "partial"
    WEAKER = "weaker"
    IRRELEVANT = "irrelevant"
    UNCERTAIN = "uncertain"


class ClaimEvidenceLink(Contract):
    span_id: Text
    evidence_id: Text
    source_id: Text
    exact_span: Text
    span_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def span_hash_matches(self) -> Self:
        # A draft may carry a bad hash so the independent citation validator can
        # report it.  Only the shape is enforced here.
        return self


class Claim(Contract):
    claim_id: Text
    text: Text
    kind: ClaimKind
    origin: ClaimOrigin
    provenance_category: ProvenanceCategory | None = None
    material_health_claim: bool
    action: ClaimAction = ClaimAction.DESCRIBE
    evidence_links: list[ClaimEvidenceLink] = Field(default_factory=list)
    applied_context_ids: list[Text] = Field(default_factory=list)
    risk_tags: list[Text] = Field(default_factory=list)
    overrides_context_ids: list[Text] = Field(default_factory=list)
    schedule_item_id: str | None = None

    @model_validator(mode="after")
    def claim_shape(self) -> Self:
        link_ids = [item.span_id for item in self.evidence_links]
        if len(link_ids) != len(set(link_ids)):
            raise ValueError("claim span IDs must be unique")
        if self.kind == ClaimKind.MEDICATION_RECORD and self.action not in {
            ClaimAction.RECORD_ONLY,
            ClaimAction.PRESCRIBE_START,
            ClaimAction.PRESCRIBE_STOP,
            ClaimAction.PRESCRIBE_CHANGE,
        }:
            raise ValueError("medication claims must be record-only or an explicitly rejectable change")
        if self.kind == ClaimKind.PLAN_ITEM and not self.schedule_item_id:
            raise ValueError("plan-item claims require a schedule item ID")
        if self.kind != ClaimKind.PLAN_ITEM and self.schedule_item_id is not None:
            raise ValueError("only plan-item claims may reference a schedule item")
        return self


class EligibleEvidenceSpan(Contract):
    span_id: Text
    evidence_id: Text
    source_id: Text
    exact_span: Text
    span_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    approval_state: Literal[
        "approved", "controlled_fixture", "confirmed_personal",
        "draft", "unapproved", "rejected",
    ]
    current: bool = True
    retired: bool = False
    fixture_only: bool = False
    workspace_id: UUID | None = None
    journey: JourneyPosition | None = None
    jurisdictions: list[Text] = Field(default_factory=list)
    evidence_version: Text
    allowed_claim_kinds: list[ClaimKind] = Field(min_length=1)
    required_condition_ids: list[Text] = Field(default_factory=list)
    excluded_condition_ids: list[Text] = Field(default_factory=list)

    @model_validator(mode="after")
    def evidence_lane_invariants(self) -> Self:
        if sha256(self.exact_span.encode("utf-8")).hexdigest() != self.span_sha256:
            raise ValueError("trusted evidence span checksum does not match")
        if self.approval_state == "confirmed_personal" and self.workspace_id is None:
            raise ValueError("personal evidence requires its authenticated workspace")
        if self.approval_state != "confirmed_personal" and self.workspace_id is not None:
            raise ValueError("public evidence cannot carry a personal workspace")
        if self.approval_state == "controlled_fixture" and not self.fixture_only:
            raise ValueError("controlled fixture evidence must remain visibly fixture-only")
        if self.fixture_only and self.approval_state != "controlled_fixture":
            raise ValueError("fixture-only evidence cannot claim another approval state")
        if self.retired and self.current:
            raise ValueError("retired evidence cannot also be current")
        return self


class ValidationEvidencePacket(Contract):
    packet_version: Literal["8.0.0"] = VALIDATION_SCHEMA_VERSION
    packet_id: UUID = Field(default_factory=uuid4)
    request_id: UUID
    workspace_id: UUID
    care_episode_id: UUID
    state_version: int = Field(ge=1)
    journey: JourneyPosition
    jurisdiction: Text
    retrieval_policy_id: Text
    retrieval_policy_version: Text
    support_state: SupportState
    ordinary_generation_allowed: bool
    unresolved_conflict_ids: list[Text] = Field(default_factory=list)
    missing_information_fields: list[Text] = Field(default_factory=list)
    allowed_claim_types: list[Text] = Field(default_factory=list)
    required_citation_ids: list[Text] = Field(default_factory=list)
    spans: list[EligibleEvidenceSpan] = Field(default_factory=list)
    corpus_mode: Literal["production_release", "controlled_fixture", "personal_only", "no_public_release"]
    trusted_server_created: Literal[True] = True

    @model_validator(mode="after")
    def packet_state_is_coherent(self) -> Self:
        if self.jurisdiction != self.jurisdiction.upper():
            raise ValueError("packet jurisdiction must be canonical uppercase")
        if self.ordinary_generation_allowed != (
            self.support_state == "fully_supported"
            and not self.unresolved_conflict_ids
            and not self.missing_information_fields
        ):
            raise ValueError("packet generation permission contradicts support/conflict state")
        ids = [span.span_id for span in self.spans]
        if len(ids) != len(set(ids)):
            raise ValueError("packet span IDs must be unique")
        if len(self.required_citation_ids) != len(set(self.required_citation_ids)):
            raise ValueError("required citation IDs must be unique")
        if self.corpus_mode != "controlled_fixture" and any(span.fixture_only for span in self.spans):
            raise ValueError("fixture evidence requires controlled-fixture packet mode")
        return self


class PlanItemValidationLink(Contract):
    schedule_item_id: Text
    claim_id: Text
    evidence_ids: list[Text] = Field(min_length=1)
    span_ids: list[Text] = Field(min_length=1)
    applied_context_ids: list[Text] = Field(default_factory=list)
    user_edited: bool = False


class AnswerDraft(Contract):
    schema_version: Literal["8.0.0"] = VALIDATION_SCHEMA_VERSION
    request_id: UUID
    agent: AgentName
    journey_state_version: int = Field(ge=1)
    summary: Text
    claims: list[Claim] = Field(min_length=1)
    applied_context_ids: list[Text] = Field(default_factory=list)
    proposed_actions: list[ProposedAction] = Field(default_factory=list)
    unauthorized_action_requested: bool = False
    proposed_schedule: ProposedSchedule | None = None
    plan_item_links: list[PlanItemValidationLink] = Field(default_factory=list)
    evaluation_only: bool
    public_eligible: bool

    @model_validator(mode="after")
    def draft_is_structurally_consistent(self) -> Self:
        claim_ids = [claim.claim_id for claim in self.claims]
        if len(claim_ids) != len(set(claim_ids)):
            raise ValueError("draft claim IDs must be unique")
        if self.evaluation_only and self.public_eligible:
            raise ValueError("evaluation-only draft cannot be public eligible")
        if self.proposed_schedule is None and self.plan_item_links:
            raise ValueError("plan links require a proposed schedule")
        if self.proposed_schedule is not None:
            schedule_ids = {item.schedule_item_id for item in self.proposed_schedule.items}
            link_ids = [item.schedule_item_id for item in self.plan_item_links]
            if len(link_ids) != len(set(link_ids)) or not set(link_ids) <= schedule_ids:
                raise ValueError("plan links must uniquely reference schedule items")
        return self


class ValidationRequest(Contract):
    schema_version: Literal["8.0.0"] = VALIDATION_SCHEMA_VERSION
    request_id: UUID
    context: AuthenticatedContextSnapshot
    safety_result: SafetyGateResult
    orchestration_result: OrchestrationResult
    draft: AnswerDraft
    evidence_packet: ValidationEvidencePacket
    execution_mode: Literal["evaluation_only", "public_runtime"]
    max_evidence_retries: Literal[1] = 1
    max_repairs: Literal[1] = 1

    @model_validator(mode="after")
    def request_identity_is_bound(self) -> Self:
        if any(value != self.request_id for value in (
            self.safety_result.request_id,
            self.orchestration_result.request_id,
            self.draft.request_id,
            self.evidence_packet.request_id,
        )):
            raise ValueError("Stage 5–8 request IDs must agree")
        if self.context.workspace_id != self.evidence_packet.workspace_id:
            raise ValueError("validation packet must belong to the authenticated workspace")
        if self.context.care_episode_id != self.evidence_packet.care_episode_id:
            raise ValueError("validation packet must belong to the authenticated care episode")
        if self.orchestration_result.safety_result != self.safety_result:
            raise ValueError("Stage 7 and Stage 8 must use the identical Safety Gate result")
        if self.draft.evaluation_only != self.safety_result.evaluation_only:
            raise ValueError("draft execution mode must agree with the Safety Gate")
        if self.draft.public_eligible != self.orchestration_result.public_eligible:
            raise ValueError("draft and orchestration public eligibility must agree")
        if self.execution_mode == "public_runtime" and (
            self.safety_result.evaluation_only
            or self.draft.evaluation_only
            or self.evidence_packet.corpus_mode == "controlled_fixture"
        ):
            raise ValueError("fixture/evaluation artifacts cannot enter public composition")
        return self


class SemanticAssessment(Contract):
    claim_id: Text
    evidence_id: Text
    support: SemanticSupport
    explanation: Text
    evaluator: Text
    model: Text
    evaluator_version: Literal["stage8-semantic-contract-v1"] = SEMANTIC_EVALUATOR_VERSION
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    estimated_cost_usd: float = Field(ge=0)
    latency_ms: float = Field(ge=0)


class ValidationFinding(Contract):
    finding_id: Text
    validator: ValidatorName
    code: FindingCode
    severity: FindingSeverity
    deterministic: bool
    detail: Text
    claim_id: str | None = None
    evidence_id: str | None = None
    schedule_item_id: str | None = None
    repair_allowed: bool = False
    retrieval_retry_allowed: bool = False

    @model_validator(mode="after")
    def only_safe_findings_are_repairable(self) -> Self:
        if self.repair_allowed and self.code != FindingCode.PROVENANCE_LABEL_MISSING:
            raise ValueError("only an unambiguous missing provenance label is mechanically repairable")
        if self.retrieval_retry_allowed and self.code not in {
            FindingCode.MATERIAL_CLAIM_WITHOUT_EVIDENCE,
            FindingCode.UNSUPPORTED_EVIDENCE_PACKET,
            FindingCode.PARTIAL_EVIDENCE_PACKET,
        }:
            raise ValueError("retrieval retry is limited to missing/insufficient support")
        return self


class ValidatorCheckResult(Contract):
    validator: ValidatorName
    status: ValidationStatus
    finding_codes: list[FindingCode] = Field(default_factory=list)

    @model_validator(mode="after")
    def status_matches_findings(self) -> Self:
        if self.status == ValidationStatus.FAIL and not self.finding_codes:
            raise ValueError("failed validator requires findings")
        if self.status != ValidationStatus.FAIL and self.finding_codes:
            raise ValueError("passing/not-run validator cannot carry findings")
        return self


class RetryStopTrace(Contract):
    action: Literal["none", "mechanical_repair", "retrieval_retry"] = "none"
    attempt_count: int = Field(default=0, ge=0, le=1)
    second_attempt_prevented: bool = False
    reason: Text

    @model_validator(mode="after")
    def retry_shape(self) -> Self:
        if (self.action == "none") != (self.attempt_count == 0):
            raise ValueError("retry action and attempt count disagree")
        return self


class ValidationTrace(Contract):
    trace_id: UUID = Field(default_factory=uuid4)
    request_id: UUID
    validation_policy_version: Literal["stage8-validation-v1"] = VALIDATION_POLICY_VERSION
    schema_version: Literal["8.0.0"] = VALIDATION_SCHEMA_VERSION
    composition_version: Literal["stage8-composition-v1"] = COMPOSITION_VERSION
    stage7_trace_id: UUID
    safety_trace_id: UUID
    workspace_id: UUID
    state_version: int = Field(ge=1)
    retrieval_policy_id: Text
    retrieval_policy_version: Text
    evidence_packet_version: Literal["8.0.0"] = VALIDATION_SCHEMA_VERSION
    stage7_schema_version: Literal["7.0.0"] = "7.0.0"
    composition_prompt_version: Literal["stage8-constrained-composition-v1"] = (
        "stage8-constrained-composition-v1"
    )
    draft_providers: list[Text] = Field(default_factory=list)
    draft_models: list[Text] = Field(default_factory=list)
    draft_agent_versions: list[Text] = Field(default_factory=list)
    safety_specification_version: Text
    safety_message_version: Text
    evidence_ids: list[Text] = Field(default_factory=list)
    span_ids: list[Text] = Field(default_factory=list)
    finding_codes: list[FindingCode] = Field(default_factory=list)
    semantic_evaluator: Text
    semantic_model: Text
    semantic_assessments: list[SemanticAssessment] = Field(default_factory=list)
    latency_ms: float = Field(ge=0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    estimated_cost_usd: float = Field(ge=0)
    retry_count: int = Field(ge=0, le=1)
    repair_count: int = Field(ge=0, le=1)
    final_disposition: FinalDisposition
    ordinary_composition_call_count: int = Field(ge=0, le=1)
    persistent_write_count: Literal[0] = 0
    raw_personal_text_logged: Literal[False] = False


class ValidationReport(Contract):
    schema_version: Literal["8.0.0"] = VALIDATION_SCHEMA_VERSION
    request_id: UUID
    workspace_id: UUID
    state_version: int = Field(ge=1)
    checks: list[ValidatorCheckResult] = Field(min_length=7, max_length=7)
    findings: list[ValidationFinding] = Field(default_factory=list)
    disposition: FinalDisposition
    display_allowed: bool
    repair_trace: RetryStopTrace
    trace: ValidationTrace

    @model_validator(mode="after")
    def report_is_coherent(self) -> Self:
        if self.request_id != self.trace.request_id:
            raise ValueError("validation report and trace request IDs disagree")
        if self.workspace_id != self.trace.workspace_id or self.state_version != self.trace.state_version:
            raise ValueError("validation report and trace scope disagree")
        if [item.validator for item in self.checks] != VALIDATOR_ORDER:
            raise ValueError("validation checks must contain the seven validators in canonical order")
        finding_codes = [item.code for item in self.findings]
        if self.trace.finding_codes != finding_codes:
            raise ValueError("trace finding inventory must equal report findings")
        failed_codes = [code for check in self.checks for code in check.finding_codes]
        if failed_codes != finding_codes:
            raise ValueError("validator results and finding inventory disagree")
        passed = all(item.status == ValidationStatus.PASS for item in self.checks)
        if self.display_allowed != (passed and self.disposition == FinalDisposition.PASS):
            raise ValueError("display permission requires seven passing validators")
        if self.trace.final_disposition != self.disposition:
            raise ValueError("trace and report final disposition disagree")
        if self.trace.retry_count + self.trace.repair_count != self.repair_trace.attempt_count:
            raise ValueError("retry/repair trace counts disagree")
        if self.disposition != FinalDisposition.PASS and self.trace.ordinary_composition_call_count:
            raise ValueError("failed validation cannot call ordinary answer composition")
        return self


class ComposedCitation(Contract):
    claim_id: Text
    span_id: Text
    evidence_id: Text
    source_id: Text
    exact_span: Text


class ComposedSection(Contract):
    provenance: ProvenanceCategory
    statements: list[Text] = Field(min_length=1)
    citations: list[ComposedCitation] = Field(default_factory=list)


class ComposedAnswer(Contract):
    schema_version: Literal["8.0.0"] = VALIDATION_SCHEMA_VERSION
    composition_version: Literal["stage8-composition-v1"] = COMPOSITION_VERSION
    request_id: UUID
    workspace_id: UUID
    state_version: int = Field(ge=1)
    summary: Text
    sections: list[ComposedSection] = Field(min_length=1)
    proposed_schedule: ProposedSchedule | None = None
    validation_trace_id: UUID
    display_allowed: Literal[True] = True
    proposal_only: Literal[True] = True
    persistent_write_performed: Literal[False] = False

    @model_validator(mode="after")
    def provenance_sections_are_unique(self) -> Self:
        labels = [section.provenance for section in self.sections]
        if len(labels) != len(set(labels)):
            raise ValueError("composed provenance sections must be unique")
        return self


class Stage8Result(Contract):
    schema_version: Literal["8.0.0"] = VALIDATION_SCHEMA_VERSION
    request_id: UUID
    safety_result: SafetyGateResult
    validation_report: ValidationReport
    composed_answer: ComposedAnswer | None = None
    urgent_fixed_message: FixedSafetyMessage | None = None
    ordinary_composition_called: bool
    proposal_only: Literal[True] = True
    persistent_write_performed: Literal[False] = False

    @model_validator(mode="after")
    def result_boundary(self) -> Self:
        if self.request_id != self.safety_result.request_id or self.request_id != self.validation_report.request_id:
            raise ValueError("Stage 8 result identity must agree")
        if self.safety_result.route == "urgent":
            if self.composed_answer is not None or self.ordinary_composition_called:
                raise ValueError("urgent safety output cannot enter ordinary composition")
            if self.urgent_fixed_message != self.safety_result.fixed_message:
                raise ValueError("urgent output must preserve the exact Stage 6 fixed message")
        elif self.urgent_fixed_message is not None:
            raise ValueError("only an urgent route may carry the fixed urgent message")
        if self.validation_report.display_allowed != (self.composed_answer is not None):
            raise ValueError("only a passing validation report may produce an answer")
        if self.ordinary_composition_called != (self.composed_answer is not None):
            raise ValueError("composition call flag must equal answer presence")
        return self
