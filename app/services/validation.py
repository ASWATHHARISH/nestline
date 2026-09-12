"""Stage 8 seven-validator display gate and constrained answer composer."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import re
from time import perf_counter
from typing import Callable

from app.schemas.orchestration import ContextKind, FactState
from app.schemas.retrieval import EvidencePacket
from app.schemas.validation import (
    AnswerDraft,
    Claim,
    ClaimAction,
    ClaimKind,
    ClaimOrigin,
    ComposedAnswer,
    ComposedCitation,
    ComposedSection,
    EligibleEvidenceSpan,
    FinalDisposition,
    FindingCode,
    FindingSeverity,
    ProvenanceCategory,
    RetryStopTrace,
    SemanticAssessment,
    SemanticSupport,
    Stage8Result,
    ValidationEvidencePacket,
    ValidationFinding,
    ValidationReport,
    ValidationRequest,
    ValidationStatus,
    ValidationTrace,
    ValidatorCheckResult,
    ValidatorName,
    VALIDATOR_ORDER,
)
from app.services.semantic_support import (
    DeterministicSemanticSupportEvaluator,
    SemanticEvaluatorUnavailable,
    SemanticSupportEvaluator,
)


RetrievalRetry = Callable[[ValidationRequest], ValidationRequest]
MechanicalRepair = Callable[[ValidationRequest], ValidationRequest]

DIAGNOSIS_PATTERNS = (
    r"\byou (?:have|definitely have|must have)\b",
    r"\bthis (?:means|proves) you have\b",
    r"\bdiagnos(?:e|ed|is)\b",
)
MEDICATION_CHANGE_PATTERNS = (
    r"\b(?:start|stop|increase|decrease|double|halve|skip|replace|substitute|combine|reschedule)\b.{0,50}\b(?:medicine|medication|tablet|dose|supplement)\b",
    r"\b(?:medicine|medication|tablet|dose|supplement)\b.{0,50}\b(?:start|stop|increase|decrease|double|halve|skip|replace|substitute|combine|reschedule)\b",
)
CLEARANCE_PATTERNS = (
    r"\b(?:you are|you're) (?:cleared|safe) to (?:exercise|work out|train)\b",
    r"\bmedical clearance (?:is|was) not needed\b",
)
REASSURANCE_PATTERNS = (
    r"\byou are safe\b", r"\bnothing to worry about\b",
    r"\bthis is normal\b", r"\bdefinitely harmless\b",
)
FAKE_REVIEW_PATTERNS = (
    r"\ba doctor (?:reviewed|approved) this\b",
    r"\bclinically (?:validated|approved)\b",
    r"\bour medical team (?:reviewed|approved)\b",
)


def canonical_provenance(origin: ClaimOrigin) -> ProvenanceCategory | None:
    return {
        ClaimOrigin.CONFIRMED_PERSONAL: ProvenanceCategory.CONFIRMED,
        ClaimOrigin.UPLOADED_RECORD: ProvenanceCategory.UPLOADED_RECORD,
        ClaimOrigin.USER_REPORTED: ProvenanceCategory.USER_REPORTED,
        ClaimOrigin.PUBLIC_GUIDANCE: ProvenanceCategory.PUBLIC_GUIDANCE,
        ClaimOrigin.NEEDS_CONFIRMATION: ProvenanceCategory.NEEDS_CONFIRMATION,
        ClaimOrigin.PRODUCT: None,
    }[origin]


def _norm(value: object) -> str:
    return " ".join(str(value).casefold().split())


def _unsafe_value_mention(text: str, value: str) -> bool:
    """Find an included constraint term without treating explicit exclusions as use."""

    normalized = _norm(text)
    safe_forms = (
        f"{value}-free", f"{value} free", f"without {value}",
        f"avoid {value}", f"exclude {value}",
    )
    if any(form in normalized for form in safe_forms):
        return False
    return bool(re.search(rf"\b{re.escape(value)}\b", normalized))


def _journey_covers(container, target) -> bool:
    if container is None:
        return True
    if container.stage != target.stage or container.unit != target.unit:
        return False
    if target.unit == "none":
        return True
    return (
        container.start is not None and target.start is not None
        and container.end is not None and target.end is not None
        and container.start <= target.start <= target.end <= container.end
    )


def _stable_span_id(evidence_id: str, source_id: str, span_hash: str) -> str:
    value = f"{evidence_id}|{source_id}|{span_hash}"
    return "span-" + sha256(value.encode("utf-8")).hexdigest()[:20]


def _allowed_packet_claim_types(claim: Claim) -> set[str]:
    if claim.origin == ClaimOrigin.PUBLIC_GUIDANCE:
        return {"approved_guideline_paraphrase", "published_weekly_profile"}
    if claim.kind == ClaimKind.MEDICATION_RECORD:
        return {"record_only_medication"}
    if claim.origin in {ClaimOrigin.CONFIRMED_PERSONAL, ClaimOrigin.UPLOADED_RECORD}:
        return {"confirmed_personal_record"}
    if claim.origin == ClaimOrigin.USER_REPORTED:
        return {"evaluation_only_symptom_record"}
    if claim.origin == ClaimOrigin.NEEDS_CONFIRMATION:
        return {"clarification_required"}
    return set()


def _finding(
    validator: ValidatorName,
    code: FindingCode,
    detail: str,
    *,
    severity: FindingSeverity = FindingSeverity.ERROR,
    deterministic: bool = True,
    claim_id: str | None = None,
    evidence_id: str | None = None,
    schedule_item_id: str | None = None,
    repair_allowed: bool = False,
    retrieval_retry_allowed: bool = False,
) -> ValidationFinding:
    key = "|".join(filter(None, (validator.value, code.value, claim_id, evidence_id, schedule_item_id)))
    return ValidationFinding(
        finding_id="finding-" + sha256(key.encode("utf-8")).hexdigest()[:16],
        validator=validator,
        code=code,
        severity=severity,
        deterministic=deterministic,
        detail=detail,
        claim_id=claim_id,
        evidence_id=evidence_id,
        schedule_item_id=schedule_item_id,
        repair_allowed=repair_allowed,
        retrieval_retry_allowed=retrieval_retry_allowed,
    )


def mechanical_provenance_repair(request: ValidationRequest) -> ValidationRequest:
    """Apply the only allowed repair: an unambiguous missing provenance label."""

    claims = []
    changed = False
    for claim in request.draft.claims:
        expected = canonical_provenance(claim.origin)
        if claim.provenance_category is None and expected is not None:
            claim = claim.model_copy(update={"provenance_category": expected})
            changed = True
        claims.append(claim)
    if not changed:
        raise ValueError("no safe provenance repair is available")
    draft = request.draft.model_copy(update={"claims": claims})
    return request.model_copy(update={"draft": draft})


def validation_packet_from_retrieval(packet: EvidencePacket) -> ValidationEvidencePacket:
    """Create the strict Stage 8 span inventory from a validated Stage 5 packet.

    Facts without exact source text remain outside the span inventory and cannot
    support a material displayed claim until their provenance supplies that span.
    """

    spans: list[EligibleEvidenceSpan] = []
    for candidate in packet.approved_guideline_passages:
        for source_span in candidate.spans:
            spans.append(EligibleEvidenceSpan(
                span_id=_stable_span_id(
                    candidate.evidence_id, candidate.source_id, source_span.text_sha256
                ),
                evidence_id=candidate.evidence_id,
                source_id=candidate.source_id,
                exact_span=source_span.exact_text,
                span_sha256=source_span.text_sha256,
                approval_state=("controlled_fixture" if candidate.provenance.fixture_only else "approved"),
                fixture_only=candidate.provenance.fixture_only,
                journey=candidate.journey,
                jurisdictions=candidate.jurisdictions,
                evidence_version=candidate.provenance.source_version or "unversioned",
                allowed_claim_kinds=[ClaimKind.HEALTH_GUIDANCE, ClaimKind.PLAN_ITEM],
            ))
    for candidate in packet.permitted_personal_passages:
        source_span = candidate.span
        personal_evidence_id = f"personal-passage:{candidate.chunk_id}"
        spans.append(EligibleEvidenceSpan(
            span_id=_stable_span_id(
                personal_evidence_id, source_span.source_id, source_span.text_sha256
            ),
            evidence_id=personal_evidence_id,
            source_id=source_span.source_id,
            exact_span=source_span.exact_text,
            span_sha256=source_span.text_sha256,
            approval_state="confirmed_personal",
            workspace_id=packet.workspace_id,
            evidence_version=candidate.provenance.source_version or "unversioned",
            allowed_claim_kinds=[ClaimKind.PERSONAL_RECORD, ClaimKind.MEDICATION_RECORD],
        ))
    mode = "personal_only" if packet.corpus_mode == "no_public_release" else packet.corpus_mode
    return ValidationEvidencePacket(
        request_id=packet.request_id,
        workspace_id=packet.workspace_id,
        care_episode_id=packet.care_episode_id,
        state_version=packet.trusted_state.cache_state_version,
        journey=packet.journey,
        jurisdiction=packet.jurisdiction,
        retrieval_policy_id=packet.retrieval_policy.policy_id,
        retrieval_policy_version=packet.retrieval_policy.policy_version,
        support_state=packet.answerability.support_state,
        ordinary_generation_allowed=packet.answerability.ordinary_generation_allowed,
        unresolved_conflict_ids=packet.answerability.relevant_conflict_ids,
        missing_information_fields=packet.answerability.relevant_missing_fields,
        allowed_claim_types=list(packet.allowed_claim_types),
        required_citation_ids=list(packet.required_citations),
        spans=spans,
        corpus_mode=mode,
    )


@dataclass(frozen=True)
class _Attempt:
    findings: list[ValidationFinding]
    checks: list[ValidatorCheckResult]
    assessments: list[SemanticAssessment]


class Stage8ValidationPipeline:
    """Validate once, permit one bounded repair/retrieval retry, then stop."""

    def __init__(self, evaluator: SemanticSupportEvaluator | None = None) -> None:
        self.evaluator = evaluator or DeterministicSemanticSupportEvaluator()

    def run(
        self,
        request: ValidationRequest,
        *,
        repairer: MechanicalRepair | None = mechanical_provenance_repair,
        retrieval_retry: RetrievalRetry | None = None,
    ) -> Stage8Result:
        started = perf_counter()
        if request.safety_result.route != "non_urgent":
            urgent = request.safety_result.route == "urgent"
            finding = _finding(
                ValidatorName.BOUNDARY,
                (FindingCode.URGENT_COMPOSITION_BLOCKED if urgent
                 else FindingCode.SAFETY_CLARIFICATION_BLOCKED),
                ("The exact Stage 6 urgent message bypassed ordinary composition."
                 if urgent else
                 "The unresolved Stage 6 clarification bypassed ordinary composition."),
                severity=FindingSeverity.CRITICAL,
            )
            checks = [
                ValidatorCheckResult(
                    validator=name,
                    status=(ValidationStatus.FAIL if name == ValidatorName.BOUNDARY else
                            ValidationStatus.PASS if name == ValidatorName.SCHEMA else
                            ValidationStatus.NOT_RUN),
                    finding_codes=[finding.code] if name == ValidatorName.BOUNDARY else [],
                ) for name in VALIDATOR_ORDER
            ]
            report = self._report(
                request, _Attempt([finding], checks, []), started,
                (FinalDisposition.ESCALATE if urgent else FinalDisposition.CLARIFY),
                RetryStopTrace(
                    action="none", attempt_count=0, second_attempt_prevented=False,
                    reason=("urgent Stage 6 route is immutable" if urgent else
                            "Stage 6 safety clarification must resolve before composition"),
                ),
                retry_count=0, repair_count=0, composition_calls=0,
            )
            return Stage8Result(
                request_id=request.request_id,
                safety_result=request.safety_result,
                validation_report=report,
                urgent_fixed_message=(request.safety_result.fixed_message if urgent else None),
                ordinary_composition_called=False,
            )

        attempt = self._validate(request)
        repair_count = retry_count = 0
        retry_trace = RetryStopTrace(
            action="none", attempt_count=0, second_attempt_prevented=False,
            reason="no bounded correction was required",
        )
        repairable = bool(attempt.findings) and all(item.repair_allowed for item in attempt.findings)
        retriable = bool(attempt.findings) and all(item.retrieval_retry_allowed for item in attempt.findings)
        if repairable and repairer is not None:
            repair_count = 1
            try:
                request = repairer(request)
                attempt = self._validate(request)
                retry_trace = RetryStopTrace(
                    action="mechanical_repair", attempt_count=1,
                    second_attempt_prevented=bool(attempt.findings),
                    reason=("safe provenance repair passed" if not attempt.findings
                            else "repair remained invalid; a second repair was prevented"),
                )
            except (ValueError, TypeError):
                extra = _finding(
                    ValidatorName.SCHEMA, FindingCode.REPAIR_FAILED,
                    "The one permitted mechanical repair failed.",
                )
                attempt = self._append_finding(attempt, extra)
                retry_trace = RetryStopTrace(
                    action="mechanical_repair", attempt_count=1,
                    second_attempt_prevented=True,
                    reason="repair failed; a second repair was prevented",
                )
        elif retriable and retrieval_retry is not None:
            retry_count = 1
            try:
                replacement = retrieval_retry(request)
                if replacement.request_id != request.request_id:
                    raise ValueError("retrieval retry changed request identity")
                request = replacement
                attempt = self._validate(request)
                retry_trace = RetryStopTrace(
                    action="retrieval_retry", attempt_count=1,
                    second_attempt_prevented=bool(attempt.findings),
                    reason=("one retrieval retry supplied eligible support" if not attempt.findings
                            else "retrieval remained insufficient; a second retry was prevented"),
                )
            except (ValueError, TypeError):
                extra = _finding(
                    ValidatorName.EVIDENCE, FindingCode.REPAIR_FAILED,
                    "The one permitted retrieval retry failed closed.",
                )
                attempt = self._append_finding(attempt, extra)
                retry_trace = RetryStopTrace(
                    action="retrieval_retry", attempt_count=1,
                    second_attempt_prevented=True,
                    reason="retrieval retry failed; a second retry was prevented",
                )

        disposition = self._disposition(attempt.findings, request)
        composition_calls = 1 if disposition == FinalDisposition.PASS else 0
        report = self._report(
            request, attempt, started, disposition, retry_trace,
            retry_count=retry_count, repair_count=repair_count,
            composition_calls=composition_calls,
        )
        answer = self._compose(request, report) if report.display_allowed else None
        return Stage8Result(
            request_id=request.request_id,
            safety_result=request.safety_result,
            validation_report=report,
            composed_answer=answer,
            ordinary_composition_called=answer is not None,
        )

    def _validate(self, request: ValidationRequest) -> _Attempt:
        by_validator: dict[ValidatorName, list[ValidationFinding]] = {
            name: [] for name in VALIDATOR_ORDER
        }
        assessments: list[SemanticAssessment] = []
        self._state_journey(request, by_validator[ValidatorName.STATE_JOURNEY])
        self._constraints(request, by_validator[ValidatorName.PERSONAL_CONSTRAINT])
        self._evidence(request, by_validator[ValidatorName.EVIDENCE])
        self._boundary(request, by_validator[ValidatorName.BOUNDARY])
        self._citations(
            request,
            by_validator[ValidatorName.CITATION],
            assessments,
            semantic_allowed=(
                not by_validator[ValidatorName.PERSONAL_CONSTRAINT]
                and not by_validator[ValidatorName.BOUNDARY]
            ),
        )
        self._consistency(request, by_validator[ValidatorName.CONSISTENCY])
        findings = [item for name in VALIDATOR_ORDER for item in by_validator[name]]
        checks = [
            ValidatorCheckResult(
                validator=name,
                status=ValidationStatus.FAIL if by_validator[name] else ValidationStatus.PASS,
                finding_codes=[item.code for item in by_validator[name]],
            ) for name in VALIDATOR_ORDER
        ]
        return _Attempt(findings, checks, assessments)

    @staticmethod
    def _state_journey(request: ValidationRequest, findings: list[ValidationFinding]) -> None:
        context = request.context
        packet = request.evidence_packet
        draft = request.draft
        if draft.journey_state_version != context.state_version or packet.state_version != context.state_version:
            findings.append(_finding(
                ValidatorName.STATE_JOURNEY, FindingCode.STALE_STATE_VERSION,
                "Draft and packet must use the authenticated current state version.",
                severity=FindingSeverity.CRITICAL,
            ))
        for worker in request.orchestration_result.worker_results:
            if worker.journey_state_version != context.state_version:
                findings.append(_finding(
                    ValidatorName.STATE_JOURNEY, FindingCode.STALE_STATE_VERSION,
                    "Stage 7 worker output uses a stale authenticated state version.",
                    severity=FindingSeverity.CRITICAL,
                ))
        if packet.journey != context.journey:
            findings.append(_finding(
                ValidatorName.STATE_JOURNEY, FindingCode.JOURNEY_MISMATCH,
                "Evidence packet journey differs from the authenticated journey.",
                severity=FindingSeverity.CRITICAL,
            ))
        if draft.proposed_schedule is not None and draft.proposed_schedule.state_version != context.state_version:
            findings.append(_finding(
                ValidatorName.STATE_JOURNEY, FindingCode.STALE_STATE_VERSION,
                "Proposed schedule uses a stale journey-state version.",
                severity=FindingSeverity.CRITICAL,
            ))
        for span in packet.spans:
            if span.journey is not None and not _journey_covers(span.journey, context.journey):
                findings.append(_finding(
                    ValidatorName.STATE_JOURNEY, FindingCode.WRONG_WEEK,
                    "Cited evidence does not cover the authenticated journey position.",
                    severity=FindingSeverity.CRITICAL, evidence_id=span.evidence_id,
                ))
            jurisdictions = {value.upper() for value in span.jurisdictions}
            if jurisdictions and packet.jurisdiction not in jurisdictions and "GLOBAL" not in jurisdictions:
                findings.append(_finding(
                    ValidatorName.STATE_JOURNEY, FindingCode.WRONG_JURISDICTION,
                    "Cited evidence does not apply to the packet jurisdiction.",
                    severity=FindingSeverity.CRITICAL, evidence_id=span.evidence_id,
                ))

    @staticmethod
    def _constraints(request: ValidationRequest, findings: list[ValidationFinding]) -> None:
        relevant_kinds = {
            ContextKind.ALLERGY, ContextKind.INTOLERANCE, ContextKind.CONDITION,
            ContextKind.RESTRICTION, ContextKind.CLINICIAN_INSTRUCTION,
        }
        constraints = {
            item.item_id: item for item in request.context.items
            if item.kind in relevant_kinds and item.state == FactState.CONFIRMED and item.current
        }
        actionable = [
            claim for claim in request.draft.claims
            if claim.material_health_claim and claim.action in {
                ClaimAction.INCLUDE, ClaimAction.EXCLUDE, ClaimAction.RECOMMEND,
            }
        ]
        if actionable:
            applied = set(request.draft.applied_context_ids)
            for item_id, item in constraints.items():
                if item_id not in applied:
                    code = (
                        FindingCode.CONDITION_CONTEXT_DROPPED
                        if item.kind == ContextKind.CONDITION
                        else FindingCode.REQUIRED_CONSTRAINT_DROPPED
                    )
                    findings.append(_finding(
                        ValidatorName.PERSONAL_CONSTRAINT, code,
                        f"Confirmed {item.kind.value} {item_id} was not applied.",
                        severity=FindingSeverity.CRITICAL, claim_id=actionable[0].claim_id,
                    ))
        for claim in request.draft.claims:
            tags = {_norm(value) for value in claim.risk_tags}
            for item_id, item in constraints.items():
                value = _norm(item.value)
                if (claim.action in {ClaimAction.INCLUDE, ClaimAction.RECOMMEND}
                        and value and (value in tags or _unsafe_value_mention(claim.text, value))):
                    if item.kind in {ContextKind.ALLERGY, ContextKind.INTOLERANCE}:
                        code = FindingCode.ALLERGY_VIOLATION
                    elif item.kind == ContextKind.CLINICIAN_INSTRUCTION:
                        code = FindingCode.CONFIRMED_INSTRUCTION_VIOLATION
                    else:
                        code = FindingCode.RESTRICTION_VIOLATION
                    findings.append(_finding(
                        ValidatorName.PERSONAL_CONSTRAINT, code,
                        f"Claim conflicts with confirmed {item.kind.value} {item_id}.",
                        severity=FindingSeverity.CRITICAL, claim_id=claim.claim_id,
                    ))
                if item_id in claim.overrides_context_ids:
                    code = (FindingCode.CONFIRMED_INSTRUCTION_VIOLATION
                            if item.kind == ContextKind.CLINICIAN_INSTRUCTION
                            else FindingCode.RESTRICTION_VIOLATION)
                    findings.append(_finding(
                        ValidatorName.PERSONAL_CONSTRAINT, code,
                        f"Claim attempts to override confirmed context {item_id}.",
                        severity=FindingSeverity.CRITICAL, claim_id=claim.claim_id,
                    ))

    @staticmethod
    def _evidence(request: ValidationRequest, findings: list[ValidationFinding]) -> None:
        packet = request.evidence_packet
        if packet.unresolved_conflict_ids:
            findings.append(_finding(
                ValidatorName.EVIDENCE, FindingCode.RELEVANT_CONFLICT,
                "The evidence packet contains a relevant unresolved conflict.",
                severity=FindingSeverity.CRITICAL,
            ))
        if packet.missing_information_fields:
            findings.append(_finding(
                ValidatorName.EVIDENCE, FindingCode.REQUIRED_INFORMATION_MISSING,
                "The evidence packet is missing information required for this answer.",
                severity=FindingSeverity.ERROR,
            ))
        if packet.support_state == "unsupported":
            findings.append(_finding(
                ValidatorName.EVIDENCE, FindingCode.UNSUPPORTED_EVIDENCE_PACKET,
                "The Evidence Packet does not support the requested answer.",
                retrieval_retry_allowed=True,
            ))
        elif packet.support_state == "partially_supported":
            findings.append(_finding(
                ValidatorName.EVIDENCE, FindingCode.PARTIAL_EVIDENCE_PACKET,
                "The Evidence Packet supports only part of the requested answer.",
                retrieval_retry_allowed=True,
            ))
        elif packet.support_state == "clarification_required" and not (
            packet.unresolved_conflict_ids or packet.missing_information_fields
        ):
            findings.append(_finding(
                ValidatorName.EVIDENCE, FindingCode.REQUIRED_INFORMATION_MISSING,
                "The Evidence Packet requires clarification.",
            ))
        allowed = set(packet.allowed_claim_types)
        for claim in request.draft.claims:
            required_types = _allowed_packet_claim_types(claim)
            if claim.material_health_claim and required_types and not (allowed & required_types):
                findings.append(_finding(
                    ValidatorName.EVIDENCE, FindingCode.CLAIM_TYPE_NOT_ALLOWED,
                    "The Evidence Packet does not permit this material claim type.",
                    severity=FindingSeverity.CRITICAL, claim_id=claim.claim_id,
                ))
            if claim.material_health_claim and not claim.evidence_links:
                findings.append(_finding(
                    ValidatorName.EVIDENCE, FindingCode.MATERIAL_CLAIM_WITHOUT_EVIDENCE,
                    "Every material health claim requires an exact evidence link.",
                    claim_id=claim.claim_id, retrieval_retry_allowed=True,
                ))

    def _citations(
        self,
        request: ValidationRequest,
        findings: list[ValidationFinding],
        assessments: list[SemanticAssessment],
        *,
        semantic_allowed: bool,
    ) -> None:
        spans = {span.span_id: span for span in request.evidence_packet.spans}
        active_condition_ids = {
            item.item_id for item in request.context.items
            if item.kind == ContextKind.CONDITION
            and item.state == FactState.CONFIRMED and item.current
        }
        stage7_evidence_ids = {
            citation.evidence_id
            for result in request.orchestration_result.worker_results
            for citation in result.citations
        }
        if request.orchestration_result.proposed_schedule is not None:
            stage7_evidence_ids.update(
                evidence_id
                for item in request.orchestration_result.proposed_schedule.items
                for evidence_id in item.evidence_ids
            )
        for claim in request.draft.claims:
            for link in claim.evidence_links:
                span = spans.get(link.span_id)
                if span is None:
                    findings.append(_finding(
                        ValidatorName.CITATION, FindingCode.FABRICATED_CITATION,
                        "Citation ID is absent from the trusted Evidence Packet.",
                        severity=FindingSeverity.CRITICAL, claim_id=claim.claim_id,
                        evidence_id=link.evidence_id,
                    ))
                    continue
                if link.evidence_id != span.evidence_id:
                    findings.append(_finding(
                        ValidatorName.CITATION, FindingCode.FABRICATED_CITATION,
                        "Citation evidence ID does not match the trusted span identity.",
                        severity=FindingSeverity.CRITICAL, claim_id=claim.claim_id,
                        evidence_id=link.evidence_id,
                    ))
                    continue
                if (request.evidence_packet.required_citation_ids
                        and link.evidence_id not in request.evidence_packet.required_citation_ids):
                    findings.append(_finding(
                        ValidatorName.CITATION, FindingCode.CITATION_NOT_IN_PACKET,
                        "Citation is outside the Stage 5 required-citation inventory.",
                        severity=FindingSeverity.CRITICAL, claim_id=claim.claim_id,
                        evidence_id=link.evidence_id,
                    ))
                    continue
                if link.evidence_id not in stage7_evidence_ids:
                    findings.append(_finding(
                        ValidatorName.CITATION, FindingCode.CITATION_NOT_IN_PACKET,
                        "Citation evidence was not supplied to the producing Stage 7 worker.",
                        severity=FindingSeverity.CRITICAL, claim_id=claim.claim_id,
                        evidence_id=link.evidence_id,
                    ))
                    continue
                deterministic_failed = False
                if link.source_id != span.source_id:
                    deterministic_failed = True
                    findings.append(_finding(
                        ValidatorName.CITATION, FindingCode.CITATION_SOURCE_MISMATCH,
                        "Citation source does not match the trusted span.",
                        claim_id=claim.claim_id, evidence_id=link.evidence_id,
                    ))
                if link.exact_span != span.exact_span:
                    deterministic_failed = True
                    findings.append(_finding(
                        ValidatorName.CITATION, FindingCode.SPAN_TEXT_MISMATCH,
                        "Citation exact span text does not match the trusted span.",
                        severity=FindingSeverity.CRITICAL, claim_id=claim.claim_id,
                        evidence_id=link.evidence_id,
                    ))
                elif link.span_sha256 != span.span_sha256 or sha256(link.exact_span.encode("utf-8")).hexdigest() != link.span_sha256:
                    deterministic_failed = True
                    findings.append(_finding(
                        ValidatorName.CITATION, FindingCode.SPAN_HASH_MISMATCH,
                        "Citation span checksum does not match the trusted exact span.",
                        severity=FindingSeverity.CRITICAL, claim_id=claim.claim_id,
                        evidence_id=link.evidence_id,
                    ))
                if not span.current:
                    deterministic_failed = True
                    findings.append(_finding(
                        ValidatorName.CITATION, FindingCode.EVIDENCE_RETIRED,
                        "Citation uses retired or superseded evidence.",
                        severity=FindingSeverity.CRITICAL, claim_id=claim.claim_id,
                        evidence_id=link.evidence_id,
                    ))
                if span.approval_state not in {"approved", "confirmed_personal", "controlled_fixture"}:
                    deterministic_failed = True
                    findings.append(_finding(
                        ValidatorName.CITATION, FindingCode.EVIDENCE_UNAPPROVED,
                        "Citation is not approved for its declared lane.",
                        severity=FindingSeverity.CRITICAL, claim_id=claim.claim_id,
                        evidence_id=link.evidence_id,
                    ))
                if span.fixture_only and request.execution_mode != "evaluation_only":
                    deterministic_failed = True
                    findings.append(_finding(
                        ValidatorName.CITATION, FindingCode.EVIDENCE_UNAPPROVED,
                        "Controlled fixture evidence cannot enter public composition.",
                        severity=FindingSeverity.CRITICAL, claim_id=claim.claim_id,
                        evidence_id=link.evidence_id,
                    ))
                if span.workspace_id is not None and span.workspace_id != request.context.workspace_id:
                    deterministic_failed = True
                    findings.append(_finding(
                        ValidatorName.CITATION, FindingCode.EVIDENCE_WRONG_WORKSPACE,
                        "Personal citation belongs to another workspace.",
                        severity=FindingSeverity.CRITICAL, claim_id=claim.claim_id,
                        evidence_id=link.evidence_id,
                    ))
                if claim.kind not in span.allowed_claim_kinds:
                    deterministic_failed = True
                    findings.append(_finding(
                        ValidatorName.CITATION, FindingCode.CITATION_IRRELEVANT,
                        "Evidence is not eligible for this claim type.",
                        claim_id=claim.claim_id, evidence_id=link.evidence_id,
                    ))
                if (not set(span.required_condition_ids) <= active_condition_ids
                        or set(span.excluded_condition_ids) & active_condition_ids):
                    deterministic_failed = True
                    findings.append(_finding(
                        ValidatorName.CITATION, FindingCode.CITATION_IRRELEVANT,
                        "Evidence condition applicability does not match confirmed state.",
                        claim_id=claim.claim_id, evidence_id=link.evidence_id,
                    ))
                if deterministic_failed or not semantic_allowed:
                    continue
                try:
                    assessment = self.evaluator.assess(claim, span)
                    assessments.append(assessment)
                except TimeoutError:
                    findings.append(_finding(
                        ValidatorName.CITATION, FindingCode.SEMANTIC_EVALUATOR_TIMEOUT,
                        "Semantic support assessment timed out and remains uncertain.",
                        deterministic=False, claim_id=claim.claim_id,
                        evidence_id=link.evidence_id,
                    ))
                    continue
                except (SemanticEvaluatorUnavailable, RuntimeError):
                    findings.append(_finding(
                        ValidatorName.CITATION, FindingCode.SEMANTIC_EVALUATOR_UNAVAILABLE,
                        "Semantic support assessment was unavailable and cannot be treated as PASS.",
                        deterministic=False, claim_id=claim.claim_id,
                        evidence_id=link.evidence_id,
                    ))
                    continue
                code = {
                    SemanticSupport.PARTIAL: FindingCode.CITATION_PARTIAL_SUPPORT,
                    SemanticSupport.WEAKER: FindingCode.CITATION_WEAKER_SUPPORT,
                    SemanticSupport.IRRELEVANT: FindingCode.CITATION_IRRELEVANT,
                    SemanticSupport.UNCERTAIN: FindingCode.SEMANTIC_SUPPORT_UNCERTAIN,
                }.get(assessment.support)
                if code is not None:
                    findings.append(_finding(
                        ValidatorName.CITATION, code,
                        assessment.explanation,
                        deterministic=False, claim_id=claim.claim_id,
                        evidence_id=link.evidence_id,
                    ))

    @staticmethod
    def _boundary(request: ValidationRequest, findings: list[ValidationFinding]) -> None:
        for claim in request.draft.claims:
            text = claim.text.casefold()
            checks = (
                (FindingCode.DIAGNOSIS, DIAGNOSIS_PATTERNS, ClaimAction.DIAGNOSE),
                (FindingCode.PRESCRIBING_OR_MEDICATION_CHANGE, MEDICATION_CHANGE_PATTERNS,
                 {ClaimAction.PRESCRIBE_START, ClaimAction.PRESCRIBE_STOP, ClaimAction.PRESCRIBE_CHANGE}),
                (FindingCode.INFERRED_CLEARANCE, CLEARANCE_PATTERNS, ClaimAction.ASSERT_CLEARANCE),
                (FindingCode.UNSAFE_REASSURANCE, REASSURANCE_PATTERNS, ClaimAction.REASSURE),
                (FindingCode.FAKE_PROFESSIONAL_REVIEW, FAKE_REVIEW_PATTERNS, None),
            )
            for code, patterns, action in checks:
                action_match = claim.action in action if isinstance(action, set) else claim.action == action
                if action_match or any(re.search(pattern, text) for pattern in patterns):
                    findings.append(_finding(
                        ValidatorName.BOUNDARY, code,
                        f"Claim violates the deterministic {code.value} boundary.",
                        severity=FindingSeverity.CRITICAL, claim_id=claim.claim_id,
                    ))
            if claim.kind == ClaimKind.MEDICATION_RECORD and (
                claim.action != ClaimAction.RECORD_ONLY
                or claim.origin not in {ClaimOrigin.CONFIRMED_PERSONAL, ClaimOrigin.UPLOADED_RECORD}
            ):
                findings.append(_finding(
                    ValidatorName.BOUNDARY, FindingCode.PRESCRIBING_OR_MEDICATION_CHANGE,
                    "Medication content must remain a documented/recorded-as statement.",
                    severity=FindingSeverity.CRITICAL, claim_id=claim.claim_id,
                ))
        if request.draft.unauthorized_action_requested:
            findings.append(_finding(
                ValidatorName.BOUNDARY, FindingCode.UNAUTHORIZED_ACTION,
                "The draft requests an unauthorized persistent or privileged action.",
                severity=FindingSeverity.CRITICAL,
            ))
        combined_text = [request.draft.summary]
        if request.draft.proposed_schedule is not None:
            combined_text.extend(item.item for item in request.draft.proposed_schedule.items)
        for value in combined_text:
            lowered = value.casefold()
            for code, patterns in (
                (FindingCode.DIAGNOSIS, DIAGNOSIS_PATTERNS),
                (FindingCode.PRESCRIBING_OR_MEDICATION_CHANGE, MEDICATION_CHANGE_PATTERNS),
                (FindingCode.INFERRED_CLEARANCE, CLEARANCE_PATTERNS),
                (FindingCode.UNSAFE_REASSURANCE, REASSURANCE_PATTERNS),
                (FindingCode.FAKE_PROFESSIONAL_REVIEW, FAKE_REVIEW_PATTERNS),
            ):
                if any(re.search(pattern, lowered) for pattern in patterns):
                    findings.append(_finding(
                        ValidatorName.BOUNDARY, code,
                        "Unstructured summary/schedule text violates a deterministic boundary.",
                        severity=FindingSeverity.CRITICAL,
                    ))

    @staticmethod
    def _consistency(request: ValidationRequest, findings: list[ValidationFinding]) -> None:
        produced_agents = {result.agent for result in request.orchestration_result.worker_results}
        if request.draft.agent not in produced_agents:
            findings.append(_finding(
                ValidatorName.CONSISTENCY, FindingCode.REQUEST_ID_MISMATCH,
                "The draft agent is absent from the authenticated Stage 7 route.",
                severity=FindingSeverity.CRITICAL,
            ))
        for claim in request.draft.claims:
            expected = canonical_provenance(claim.origin)
            if expected is not None and claim.provenance_category is None:
                findings.append(_finding(
                    ValidatorName.CONSISTENCY, FindingCode.PROVENANCE_LABEL_MISSING,
                    "The visible provenance label is missing but unambiguous.",
                    claim_id=claim.claim_id, repair_allowed=True,
                ))
            elif expected is not None and claim.provenance_category != expected:
                findings.append(_finding(
                    ValidatorName.CONSISTENCY, FindingCode.PROVENANCE_LABEL_INVALID,
                    "The visible provenance category contradicts the claim origin.",
                    claim_id=claim.claim_id,
                ))
            if claim.origin == ClaimOrigin.PUBLIC_GUIDANCE and claim.overrides_context_ids:
                findings.append(_finding(
                    ValidatorName.CONSISTENCY, FindingCode.PUBLIC_OVERRIDES_PERSONAL,
                    "Public guidance attempts to override personal context.",
                    severity=FindingSeverity.CRITICAL, claim_id=claim.claim_id,
                ))
        schedule = request.draft.proposed_schedule
        edited_schedule = bool(request.draft.plan_item_links) and all(
            link.user_edited for link in request.draft.plan_item_links
        )
        if schedule != request.orchestration_result.proposed_schedule and not edited_schedule:
            findings.append(_finding(
                ValidatorName.CONSISTENCY, FindingCode.PLAN_ITEM_UNVALIDATED,
                "A schedule changed after Stage 7 without explicit user-edit markers.",
                severity=FindingSeverity.CRITICAL,
            ))
        if schedule is None:
            return
        if not schedule.proposal_only or schedule.persistent_write_performed:
            findings.append(_finding(
                ValidatorName.CONSISTENCY, FindingCode.PLAN_NOT_PROPOSAL_ONLY,
                "Stage 8 can validate only proposal-only, unsaved plans.",
                severity=FindingSeverity.CRITICAL,
            ))
        items = {item.schedule_item_id: item for item in schedule.items}
        links = {item.schedule_item_id: item for item in request.draft.plan_item_links}
        if set(items) != set(links):
            findings.append(_finding(
                ValidatorName.CONSISTENCY, FindingCode.PLAN_ITEM_UNVALIDATED,
                "Every schedule item must have one reusable validation link.",
                severity=FindingSeverity.CRITICAL,
            ))
        claims = {claim.claim_id: claim for claim in request.draft.claims}
        for item_id, item in items.items():
            link = links.get(item_id)
            if link is None:
                continue
            claim = claims.get(link.claim_id)
            expected_kind = ClaimKind.MEDICATION_RECORD if item.record_only else ClaimKind.PLAN_ITEM
            if (claim is None or claim.kind != expected_kind
                    or claim.schedule_item_id != (None if item.record_only else item_id)
                    or claim.text != item.item):
                findings.append(_finding(
                    ValidatorName.CONSISTENCY, FindingCode.PLAN_ITEM_UNVALIDATED,
                    "Schedule item is not linked to the correct typed claim.",
                    severity=FindingSeverity.CRITICAL, schedule_item_id=item_id,
                ))
            if set(link.evidence_ids) != set(item.evidence_ids):
                findings.append(_finding(
                    ValidatorName.CONSISTENCY, FindingCode.PLAN_EVIDENCE_MISMATCH,
                    "Schedule-item evidence differs from its validation link.",
                    severity=FindingSeverity.CRITICAL, schedule_item_id=item_id,
                ))
            if claim is not None and {
                value.evidence_id for value in claim.evidence_links
            } != set(link.evidence_ids):
                findings.append(_finding(
                    ValidatorName.CONSISTENCY, FindingCode.PLAN_EVIDENCE_MISMATCH,
                    "Plan claim evidence differs from its schedule validation link.",
                    severity=FindingSeverity.CRITICAL, schedule_item_id=item_id,
                ))
            if claim is not None and {
                value.span_id for value in claim.evidence_links
            } != set(link.span_ids):
                findings.append(_finding(
                    ValidatorName.CONSISTENCY, FindingCode.PLAN_EVIDENCE_MISMATCH,
                    "Plan claim exact spans differ from its schedule validation link.",
                    severity=FindingSeverity.CRITICAL, schedule_item_id=item_id,
                ))
            if claim is not None and not set(link.applied_context_ids) <= set(claim.applied_context_ids):
                findings.append(_finding(
                    ValidatorName.CONSISTENCY, FindingCode.REQUIRED_CONSTRAINT_DROPPED,
                    "Plan claim dropped a constraint carried by its item validation link.",
                    severity=FindingSeverity.CRITICAL, schedule_item_id=item_id,
                ))
        if schedule.conflicts or schedule.unresolved_uncertainties or schedule.stale:
            findings.append(_finding(
                ValidatorName.CONSISTENCY, FindingCode.PLAN_COMBINED_CONSTRAINT_FAILURE,
                "The combined schedule is conflicted, uncertain, or stale.",
                severity=FindingSeverity.CRITICAL,
            ))

    @staticmethod
    def _append_finding(attempt: _Attempt, extra: ValidationFinding) -> _Attempt:
        by_name = {check.validator: list(check.finding_codes) for check in attempt.checks}
        by_name[extra.validator].append(extra.code)
        checks = [
            ValidatorCheckResult(
                validator=name,
                status=ValidationStatus.FAIL if by_name[name] else ValidationStatus.PASS,
                finding_codes=by_name[name],
            ) for name in VALIDATOR_ORDER
        ]
        findings = []
        for name in VALIDATOR_ORDER:
            findings.extend(item for item in attempt.findings if item.validator == name)
            if extra.validator == name:
                findings.append(extra)
        return _Attempt(findings, checks, attempt.assessments)

    @staticmethod
    def _disposition(findings: list[ValidationFinding], request: ValidationRequest) -> FinalDisposition:
        if request.safety_result.route == "urgent":
            return FinalDisposition.ESCALATE
        codes = {item.code for item in findings}
        if codes & {FindingCode.RELEVANT_CONFLICT, FindingCode.REQUIRED_INFORMATION_MISSING}:
            return FinalDisposition.CLARIFY
        return FinalDisposition.PASS if not findings else FinalDisposition.ABSTAIN

    def _report(
        self,
        request: ValidationRequest,
        attempt: _Attempt,
        started: float,
        disposition: FinalDisposition,
        retry_trace: RetryStopTrace,
        *,
        retry_count: int,
        repair_count: int,
        composition_calls: int,
    ) -> ValidationReport:
        evidence_ids = sorted({
            link.evidence_id for claim in request.draft.claims for link in claim.evidence_links
        })
        semantic_evaluator = getattr(self.evaluator, "evaluator_id", "unavailable")
        semantic_model = getattr(self.evaluator, "model_id", "unavailable")
        trace = ValidationTrace(
            request_id=request.request_id,
            stage7_trace_id=request.orchestration_result.trace.trace_id,
            safety_trace_id=request.safety_result.trace.trace_id,
            workspace_id=request.context.workspace_id,
            state_version=request.context.state_version,
            retrieval_policy_id=request.evidence_packet.retrieval_policy_id,
            retrieval_policy_version=request.evidence_packet.retrieval_policy_version,
            draft_providers=sorted({
                result.trace.provider for result in request.orchestration_result.worker_results
            }),
            draft_models=sorted({
                result.trace.model for result in request.orchestration_result.worker_results
            }),
            draft_agent_versions=sorted({
                result.trace.agent_version for result in request.orchestration_result.worker_results
            }),
            safety_specification_version=request.safety_result.fixed_message.specification_version,
            safety_message_version=request.safety_result.fixed_message.message_version,
            evidence_ids=evidence_ids,
            span_ids=sorted({
                link.span_id for claim in request.draft.claims
                for link in claim.evidence_links
            }),
            finding_codes=[item.code for item in attempt.findings],
            semantic_evaluator=semantic_evaluator,
            semantic_model=semantic_model,
            semantic_assessments=attempt.assessments,
            latency_ms=(perf_counter() - started) * 1000,
            input_tokens=sum(item.input_tokens for item in attempt.assessments),
            output_tokens=sum(item.output_tokens for item in attempt.assessments),
            estimated_cost_usd=sum(item.estimated_cost_usd for item in attempt.assessments),
            retry_count=retry_count,
            repair_count=repair_count,
            final_disposition=disposition,
            ordinary_composition_call_count=composition_calls,
        )
        return ValidationReport(
            request_id=request.request_id,
            workspace_id=request.context.workspace_id,
            state_version=request.context.state_version,
            checks=attempt.checks,
            findings=attempt.findings,
            disposition=disposition,
            display_allowed=disposition == FinalDisposition.PASS,
            repair_trace=retry_trace,
            trace=trace,
        )

    @staticmethod
    def _compose(request: ValidationRequest, report: ValidationReport) -> ComposedAnswer:
        groups: dict[ProvenanceCategory, list[Claim]] = {}
        for claim in request.draft.claims:
            label = claim.provenance_category
            if label is None:
                # Product-only copy is kept with Needs confirmation rather than
                # inventing a sixth health provenance category.
                label = ProvenanceCategory.NEEDS_CONFIRMATION
            groups.setdefault(label, []).append(claim)
        sections = []
        for label in ProvenanceCategory:
            claims = groups.get(label)
            if not claims:
                continue
            sections.append(ComposedSection(
                provenance=label,
                statements=[claim.text for claim in claims],
                citations=[
                    ComposedCitation(
                        claim_id=claim.claim_id,
                        span_id=link.span_id,
                        evidence_id=link.evidence_id,
                        source_id=link.source_id,
                        exact_span=link.exact_span,
                    )
                    for claim in claims for link in claim.evidence_links
                ],
            ))
        return ComposedAnswer(
            request_id=request.request_id,
            workspace_id=request.context.workspace_id,
            state_version=request.context.state_version,
            summary="I checked this draft against its evidence, citations, journey state and confirmed constraints.",
            sections=sections,
            proposed_schedule=request.draft.proposed_schedule,
            validation_trace_id=report.trace.trace_id,
        )
