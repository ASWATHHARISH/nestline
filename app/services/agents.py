"""Bounded, proposal-only Stage 7 specialist workers.

The workers consume minimum typed context and an evidence plan chosen outside the
model boundary.  The included deterministic provider supports offline contract
testing only; public health generation remains closed while evidence is draft.
"""

from __future__ import annotations

from time import perf_counter
from typing import Any
from uuid import UUID

from pydantic import ValidationError

from app.schemas.orchestration import (
    AgentName,
    AgentTrace,
    ContextItem,
    ContextKind,
    EvidenceLane,
    EvidenceReference,
    FactState,
    FollowupTask,
    MedicationLifecycle, MedicationTimelineEntry,
    MinimalWorkerContext,
    PlanContribution,
    ProposedAction,
    RecordFinding,
    SymptomNavigation,
    WorkerEvidence,
    WorkerRequest,
    WorkerResult,
    WorkerStatus,
)
from app.schemas.safety import SafetyGateResult
from app.services.model_provider import ProviderFailure, StructuredProvider
from app.services.orchestration_catalogue import definition_for


MEDICATION_CHANGE_TERMS = (
    "start", "stop", "change", "replace", "substitute", "combine", "skip",
    "double", "reschedule", "missed dose", "increase", "decrease",
)
DIAGNOSIS_TERMS = ("diagnose", "diagnosis", "what disease", "what condition do i have", "must have")
CLINICAL_DIET_TERMS = ("treat", "cure", "reverse", "clinical diet", "therapeutic diet")
UNSAFE_MOVEMENT_TERMS = ("heavy", "maximum", "max intensity", "push through", "ignore pain")
WELLBEING_ESCALATION_TERMS = ("persistent", "worsening", "cannot function", "can't function")
FORBIDDEN_OUTPUT_CLAIMS = ("you are safe", "nothing to worry about", "this is normal", "must have", "we are monitoring", "i am monitoring")


def build_minimal_context(
    *,
    agent: AgentName,
    snapshot,
) -> MinimalWorkerContext:
    """Reduce trusted context before a worker/provider receives it."""

    from app.services.orchestration_catalogue import CONTEXT_POLICY

    allowed = list(CONTEXT_POLICY[agent])
    items = [item for item in snapshot.items if item.kind in allowed]
    return MinimalWorkerContext(
        workspace_id=snapshot.workspace_id,
        care_episode_id=snapshot.care_episode_id,
        state_version=snapshot.state_version,
        journey=snapshot.journey,
        allowed_kinds=allowed,
        items=items,
    )


def _constraints(context: MinimalWorkerContext) -> list[ContextItem]:
    return [item for item in context.items if item.kind in {
        ContextKind.ALLERGY, ContextKind.INTOLERANCE, ContextKind.RESTRICTION,
        ContextKind.CLINICIAN_INSTRUCTION, ContextKind.CONDITION,
    }]


def _visible_constraint(item: ContextItem) -> str:
    return f"{item.kind.value}: {item.value} ({item.state.value})"


def _citations(evidence: WorkerEvidence) -> list[EvidenceReference]:
    return list(evidence.references)


def _schedule_values(
    context: MinimalWorkerContext,
    domain: str,
    reference: EvidenceReference,
) -> tuple[int, int, str, list[str]]:
    """Use explicit evidence metadata and a compatible confirmed user cadence."""

    if reference.duration_minutes is None or reference.cadence_per_week is None:
        raise WorkerStop("missing_evidence_schedule_metadata")
    desired: int | None = None
    for item in context.items:
        if item.kind != ContextKind.PREFERENCE or item.state != FactState.CONFIRMED:
            continue
        if not isinstance(item.value, dict) or item.value.get("domain") != domain:
            continue
        value = item.value.get("cadence_per_week")
        if isinstance(value, int) and 1 <= value <= 7:
            desired = value
            break
    if desired is None:
        return (
            reference.duration_minutes,
            reference.cadence_per_week,
            "evidence",
            [],
        )
    applied = min(desired, reference.cadence_per_week)
    note = [] if desired <= reference.cadence_per_week else [
        f"Requested cadence {desired}/week was limited to the cited fixture cadence "
        f"{reference.cadence_per_week}/week pending stronger evidence."
    ]
    return reference.duration_minutes, applied, "user_preference", note


def _action(action_id: str, text: str) -> ProposedAction:
    return ProposedAction(action_id=action_id, description=text)


class BoundedWorker:
    """Base boundary that enforces policy, timeout, one call and one repair."""

    agent: AgentName

    def __init__(self, provider: StructuredProvider) -> None:
        self.provider = provider
        self.definition = definition_for(self.agent)

    def run(
        self,
        *,
        request_id: UUID,
        query: str,
        context: MinimalWorkerContext,
        evidence: WorkerEvidence,
        safety_result: SafetyGateResult,
        evaluation_only: bool,
        timeout_ms: int | None = None,
    ) -> WorkerResult:
        started = perf_counter()
        try:
            WorkerRequest(
                request_id=request_id, agent=self.agent, query=query, context=context,
                evidence=evidence, safety_result=safety_result, evaluation_only=evaluation_only,
            )
        except ValidationError:
            return self._stopped(
                request_id, context, evidence, evaluation_only,
                WorkerStatus.FAILED, "invalid_worker_input_contract", started,
            )
        if evidence.retrieval_purpose != self.definition.retrieval_purpose:
            return self._stopped(
                request_id, context, evidence, evaluation_only,
                WorkerStatus.FAILED, "retrieval_policy_mismatch", started,
            )
        disallowed = [
            reference.lane for reference in evidence.references
            if reference.lane not in self.definition.allowed_evidence_lanes
        ]
        if disallowed:
            return self._stopped(
                request_id, context, evidence, evaluation_only,
                WorkerStatus.FAILED, "disallowed_evidence_lane", started,
            )
        if not safety_result.ordinary_generation_allowed:
            return self._stopped(
                request_id, context, evidence, evaluation_only,
                WorkerStatus.ESCALATED, f"safety_{safety_result.route}", started,
            )
        try:
            draft = self.build_draft(
                request_id=request_id, query=query, context=context,
                evidence=evidence, evaluation_only=evaluation_only,
            )
        except WorkerStop as stop:
            return self._stopped(
                request_id, context, evidence, evaluation_only,
                stop.status, stop.reason, started,
            )

        effective_budget = self.definition.budget.model_copy(update={
            "timeout_ms": min(self.definition.budget.timeout_ms, timeout_ms)
        }) if timeout_ms is not None else self.definition.budget
        provider_started = perf_counter()
        try:
            response = self.provider.complete(
                agent=self.agent,
                instructions=self.definition.model_instructions,
                draft=draft,
                budget=effective_budget,
            )
        except TimeoutError:
            return self._stopped(
                request_id, context, evidence, evaluation_only,
                WorkerStatus.FAILED, "provider_timeout", started,
                provider=getattr(self.provider, "provider_id", "unavailable"),
                model=getattr(self.provider, "model_id", "unavailable"),
                model_calls=1,
            )
        except (ProviderFailure, RuntimeError):
            return self._stopped(
                request_id, context, evidence, evaluation_only,
                WorkerStatus.FAILED, "provider_failure", started,
                provider=getattr(self.provider, "provider_id", "unavailable"),
                model=getattr(self.provider, "model_id", "unavailable"),
                model_calls=1,
            )

        measured_provider_ms = (perf_counter() - provider_started) * 1000
        if (response.input_tokens + response.output_tokens > effective_budget.max_tokens
                or response.latency_ms > effective_budget.timeout_ms
                or measured_provider_ms > effective_budget.timeout_ms):
            return self._stopped(
                request_id, context, evidence, evaluation_only,
                WorkerStatus.FAILED, "provider_budget_exhausted", started,
                provider=response.provider, model=response.model, model_calls=1,
            )

        base_trace = self._trace(
            request_id=request_id,
            evidence=evidence,
            started=started,
            provider=response.provider,
            model=response.model,
            model_calls=1,
            steps=2,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            cost=response.estimated_cost_usd,
            stop_reason="completed",
        )
        payload = dict(response.payload)
        payload["trace"] = base_trace
        try:
            result = WorkerResult.model_validate(payload)
        except ValidationError:
            # One safe mechanical repair: replace only the generated trace with the
            # trusted trace. No semantic field, evidence or constraint is invented.
            payload["trace"] = base_trace.model_copy(update={"repair_count": 1})
            try:
                result = WorkerResult.model_validate(payload)
            except ValidationError:
                return self._stopped(
                    request_id, context, evidence, evaluation_only,
                    WorkerStatus.FAILED, "schema_invalid_after_one_repair", started,
                    provider=response.provider, model=response.model,
                    model_calls=1, repair_count=1,
                )
        semantic_failure = self.validate_result(result, context, evidence)
        if semantic_failure:
            return self._stopped(
                request_id, context, evidence, evaluation_only,
                WorkerStatus.FAILED, semantic_failure, started,
                provider=response.provider, model=response.model, model_calls=1,
                repair_count=result.trace.repair_count,
            )
        return result

    def validate_result(
        self,
        result: WorkerResult,
        context: MinimalWorkerContext,
        evidence: WorkerEvidence,
    ) -> str | None:
        """Reapply Stage 7 identity, provenance and hard constraints after generation."""

        confirmed_ids = {item.item_id for item in context.items if item.state == FactState.CONFIRMED}
        expected_constraints = {_visible_constraint(item) for item in _constraints(context)}
        evidence_ids = {reference.evidence_id for reference in evidence.references}
        citation_ids = {reference.evidence_id for reference in result.citations}
        contribution_ids = {
            evidence_id for contribution in result.contributions
            for evidence_id in contribution.evidence_ids
        }
        if not set(result.facts_used) <= confirmed_ids:
            return "structured_output_used_unconfirmed_fact"
        if not expected_constraints <= set(result.applied_constraints):
            return "structured_output_dropped_personal_constraint"
        if not citation_ids <= evidence_ids or not contribution_ids <= citation_ids:
            return "structured_output_changed_evidence_provenance"
        if any(claim in result.summary.casefold() for claim in FORBIDDEN_OUTPUT_CLAIMS):
            return "structured_output_unsafe_or_misleading_claim"
        return None

    def build_draft(self, **kwargs: Any) -> dict[str, Any]:
        raise NotImplementedError

    def _trace(
        self,
        *,
        request_id: UUID,
        evidence: WorkerEvidence,
        started: float,
        provider: str,
        model: str,
        model_calls: int,
        steps: int,
        stop_reason: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost: float = 0.0,
        repair_count: int = 0,
    ) -> AgentTrace:
        return AgentTrace(
            request_id=request_id,
            agent=self.agent,
            agent_version=self.definition.version,
            provider=provider,
            model=model,
            evidence_ids=[reference.evidence_id for reference in evidence.references],
            model_call_count=model_calls,
            step_count=steps,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=cost,
            retry_count=0,
            repair_count=repair_count,
            latency_ms=(perf_counter() - started) * 1000,
            stop_reason=stop_reason,
        )

    def _stopped(
        self,
        request_id: UUID,
        context: MinimalWorkerContext,
        evidence: WorkerEvidence,
        evaluation_only: bool,
        status: WorkerStatus,
        reason: str,
        started: float,
        *,
        provider: str = "not_called",
        model: str = "not_called",
        model_calls: int = 0,
        repair_count: int = 0,
    ) -> WorkerResult:
        return WorkerResult(
            request_id=request_id,
            agent=self.agent,
            status=status,
            journey_state_version=context.state_version,
            summary=self.stop_summary(reason),
            uncertainties=[reason],
            requires_human_review=reason in {
                "conflicting_record", "medication_or_instruction_conflict",
                "possible_reaction_requires_safety_gate", "missing_required_clearance",
            },
            stop_reason=reason,
            evaluation_only=evaluation_only,
            public_eligible=False,
            trace=self._trace(
                request_id=request_id, evidence=evidence, started=started,
                provider=provider, model=model, model_calls=model_calls,
                steps=1, repair_count=repair_count, stop_reason=reason,
            ),
        )

    @staticmethod
    def stop_summary(reason: str) -> str:
        friendly = reason.replace("_", " ")
        return f"I cannot complete this safely yet because of {friendly}."


class WorkerStop(Exception):
    def __init__(self, reason: str, status: WorkerStatus = WorkerStatus.ABSTAINED):
        super().__init__(reason)
        self.reason = reason
        self.status = status


def _base_draft(
    *,
    request_id: UUID,
    agent: AgentName,
    context: MinimalWorkerContext,
    evidence: WorkerEvidence,
    evaluation_only: bool,
    summary: str,
) -> dict[str, Any]:
    return {
        "request_id": request_id,
        "agent": agent,
        "status": WorkerStatus.COMPLETED,
        "journey_state_version": context.state_version,
        "summary": summary,
        "facts_used": [item.item_id for item in context.items if item.state == FactState.CONFIRMED],
        "citations": _citations(evidence),
        "applied_constraints": [_visible_constraint(item) for item in _constraints(context)],
        "uncertainties": [],
        "proposed_actions": [],
        "proposed_state_changes": [],
        "record_findings": [],
        "medication_timeline": [],
        "symptom_navigation": None,
        "contributions": [],
        "followup_tasks": [],
        "requires_human_review": False,
        "stop_reason": None,
        "evaluation_only": evaluation_only,
        "public_eligible": not evaluation_only and evidence.public_routing_eligible,
    }


class RecordAgent(BoundedWorker):
    agent = AgentName.RECORD

    def build_draft(self, *, request_id, query, context, evidence, evaluation_only):
        findings = [item for item in context.items if item.kind == ContextKind.DOCUMENT_FACT]
        if not findings:
            raise WorkerStop("missing_record", WorkerStatus.NEEDS_CLARIFICATION)
        if any(item.state == FactState.CONFLICTING for item in findings):
            raise WorkerStop("conflicting_record", WorkerStatus.NEEDS_CLARIFICATION)
        if any(item.confidence is not None and item.confidence < 0.6 for item in findings):
            raise WorkerStop("poor_ocr_requires_confirmation", WorkerStatus.NEEDS_CLARIFICATION)
        draft = _base_draft(
            request_id=request_id, agent=self.agent, context=context, evidence=evidence,
            evaluation_only=evaluation_only,
            summary="This document says the following. Please check the source details and confirmation state.",
        )
        draft["record_findings"] = [RecordFinding(
            item_id=item.item_id,
            wording=f"This document says: {item.value}",
            state=item.state,
            source_id=item.source_id or "personal-record",
            source_page=item.source_page,
            exact_span=item.exact_span or str(item.value),
            confidence=item.confidence,
            freshness=item.recorded_at.isoformat() if item.recorded_at else None,
        ) for item in findings]
        draft["proposed_actions"] = [
            _action("record-confirm", "Confirm or correct the extracted record detail."),
            _action("record-question", "Add a specific question for the next appointment."),
        ]
        return draft


class MedicationRecordAgent(BoundedWorker):
    agent = AgentName.MEDICATION

    def build_draft(self, *, request_id, query, context, evidence, evaluation_only):
        lower = query.casefold()
        if any(term in lower for term in MEDICATION_CHANGE_TERMS):
            raise WorkerStop("medication_change_request_refused")
        if any(term in lower for term in ("reaction", "swelling", "cannot breathe", "rash now")):
            raise WorkerStop("possible_reaction_requires_safety_gate", WorkerStatus.ESCALATED)
        records = [item for item in context.items if item.kind in {
            ContextKind.MEDICATION, ContextKind.SUPPLEMENT,
        }]
        if not records:
            raise WorkerStop("missing_medication_record", WorkerStatus.NEEDS_CLARIFICATION)
        related_instructions = [item for item in context.items if item.kind in {
            ContextKind.CLINICIAN_INSTRUCTION, ContextKind.DOCUMENT_FACT,
        }]
        if any(item.state in {FactState.CONFLICTING, FactState.STALE} for item in [*records, *related_instructions]):
            raise WorkerStop("medication_or_instruction_conflict", WorkerStatus.NEEDS_CLARIFICATION)
        draft = _base_draft(
            request_id=request_id, agent=self.agent, context=context, evidence=evidence,
            evaluation_only=evaluation_only,
            summary="Here is the chronological medication and supplement information documented in your record.",
        )
        timeline = []
        uncertainties: list[str] = []
        for item in sorted(records, key=lambda row: (
            row.recorded_at.isoformat() if row.recorded_at else "", row.item_id,
        )):
            value = item.value if isinstance(item.value, dict) else {"name": str(item.value)}
            name = value.get("name") or value.get("name_as_written") or "Recorded item"
            timeline.append(MedicationTimelineEntry(
                item_id=item.item_id, name=name, dose=value.get("dose"), unit=value.get("unit"),
                route=value.get("route"), frequency=value.get("frequency"), timing=value.get("timing"),
                start_date=value.get("start_date"), stop_date=value.get("stop_date"),
                prescriber_or_source=value.get("prescriber") or item.source_id,
                state=item.state,
                lifecycle=(
                    MedicationLifecycle.CONFLICTING if item.state == FactState.CONFLICTING
                    else MedicationLifecycle.UNCONFIRMED if item.state != FactState.CONFIRMED
                    else MedicationLifecycle.STOPPED if value.get("stop_date")
                    else MedicationLifecycle.HISTORICAL if not item.current
                    else MedicationLifecycle.CURRENT
                ),
            ))
            for field in ("dose", "frequency", "timing"):
                if not value.get(field):
                    uncertainties.append(f"{name}: {field} is not documented.")
        names = [entry.name.casefold() for entry in timeline]
        for name in sorted(set(names)):
            if names.count(name) > 1:
                uncertainties.append(f"Duplicate recorded entries need confirmation: {name}.")
        draft["medication_timeline"] = timeline
        draft["uncertainties"] = uncertainties
        draft["proposed_actions"] = [
            _action("medication-confirm", "Confirm the documented timeline with your clinician or pharmacist."),
        ]
        return draft


class SymptomNavigationAgent(BoundedWorker):
    agent = AgentName.SYMPTOM

    def build_draft(self, *, request_id, query, context, evidence, evaluation_only):
        if any(term in query.casefold() for term in DIAGNOSIS_TERMS):
            raise WorkerStop("diagnosis_request_refused")
        if evidence.missing_information:
            raise WorkerStop("minimum_symptom_details_required", WorkerStatus.NEEDS_CLARIFICATION)
        if not evidence.references:
            raise WorkerStop("approved_symptom_policy_unavailable")
        draft = _base_draft(
            request_id=request_id, agent=self.agent, context=context, evidence=evidence,
            evaluation_only=evaluation_only,
            summary="I can help organize a cautious next step, but I cannot diagnose or confirm that a symptom is safe.",
        )
        draft["symptom_navigation"] = SymptomNavigation(
            route="routine_professional_follow_up",
            what_to_do_now=["Use the cited guidance to prepare a concise symptom timeline for a professional."],
            actions_to_avoid=["Do not use this result as medical clearance or a diagnosis."],
            escalation_triggers=["If the symptom becomes severe, worsens, or you feel unsafe, rerun the Safety Gate immediately."],
            professional_route="Contact the appropriate pregnancy or postpartum professional when supported by the cited policy.",
        )
        draft["proposed_actions"] = [
            _action("symptom-handoff", "Prepare a symptom and timeline summary to share with a professional."),
        ]
        return draft


class NutritionAgent(BoundedWorker):
    agent = AgentName.NUTRITION

    def build_draft(self, *, request_id, query, context, evidence, evaluation_only):
        if any(term in query.casefold() for term in CLINICAL_DIET_TERMS):
            raise WorkerStop("individualized_clinical_diet_request")
        if evidence.missing_information:
            raise WorkerStop("missing_applicable_evidence")
        relevant_conflicts = [item for item in context.items if item.kind in {
            ContextKind.ALLERGY, ContextKind.INTOLERANCE, ContextKind.RESTRICTION,
        } and item.state in {FactState.CONFLICTING, FactState.DOCUMENT_UNCONFIRMED, FactState.STALE}]
        record_conflicts = [
            item for item in context.items if item.kind == ContextKind.DOCUMENT_FACT
            and item.state in {FactState.CONFLICTING, FactState.STALE}
        ]
        if evidence.unresolved_conflicts or relevant_conflicts or record_conflicts:
            raise WorkerStop("allergy_or_restriction_conflict", WorkerStatus.NEEDS_CLARIFICATION)
        hard_values = " ".join(str(item.value).casefold() for item in _constraints(context))
        usable = [reference for reference in evidence.references if not any(
            tag.casefold() in hard_values for tag in reference.constraint_tags
        )]
        if not usable:
            raise WorkerStop("all_candidates_excluded_by_hard_constraints")
        reference = usable[0]
        duration, cadence, cadence_source, cadence_notes = _schedule_values(
            context, "nutrition", reference,
        )
        label = reference.candidate_label or "an evidence-linked meal framework option"
        draft = _base_draft(
            request_id=request_id, agent=self.agent, context=context, evidence=evidence,
            evaluation_only=evaluation_only,
            summary="Here is a practical option after applying your confirmed food constraints.",
        )
        draft["citations"] = usable
        draft["contributions"] = [PlanContribution(
            contribution_id=f"nutrition-{reference.evidence_id}",
            contributor=self.agent, domain="nutrition", item=label,
            duration_minutes=duration, cadence_per_week=cadence,
            preferred_time_windows=["morning"],
            evidence_ids=[reference.evidence_id],
            constraint_notes=[*[_visible_constraint(item) for item in _constraints(context)], *cadence_notes],
            optional=False, flexible=True, flexible_alternatives=reference.flexible_alternatives,
            rest_recovery_notes=reference.rest_recovery_notes, cadence_source=cadence_source,
            state_version=context.state_version,
        )]
        return draft

    def validate_result(self, result, context, evidence):
        failure = super().validate_result(result, context, evidence)
        if failure:
            return failure
        hard_values = " ".join(str(item.value).casefold() for item in _constraints(context))
        for citation in result.citations:
            if any(tag.casefold() in hard_values for tag in citation.constraint_tags):
                return "structured_output_reintroduced_excluded_food"
        return None


class MovementAgent(BoundedWorker):
    agent = AgentName.MOVEMENT

    def build_draft(self, *, request_id, query, context, evidence, evaluation_only):
        lower = query.casefold()
        symptoms = [item for item in context.items if item.kind == ContextKind.SYMPTOM and item.current]
        if symptoms:
            raise WorkerStop("current_symptom_requires_safety_gate", WorkerStatus.ESCALATED)
        restrictions = [item for item in context.items if item.kind == ContextKind.RESTRICTION]
        record_conflicts = [
            item for item in context.items if item.kind == ContextKind.DOCUMENT_FACT
            and item.state in {FactState.CONFLICTING, FactState.STALE}
        ]
        if record_conflicts:
            raise WorkerStop("movement_report_conflict", WorkerStatus.NEEDS_CLARIFICATION)
        if any(item.state != FactState.CONFIRMED for item in restrictions):
            raise WorkerStop("movement_restriction_conflict", WorkerStatus.NEEDS_CLARIFICATION)
        if any(term in lower for term in UNSAFE_MOVEMENT_TERMS):
            clearance = any(
                item.kind == ContextKind.CLINICIAN_INSTRUCTION
                and item.state == FactState.CONFIRMED
                and "clear" in str(item.value).casefold()
                for item in context.items
            )
            if not clearance:
                raise WorkerStop("missing_required_clearance", WorkerStatus.NEEDS_CLARIFICATION)
        if not evidence.references:
            raise WorkerStop("missing_stage_applicable_movement_evidence")
        reference = evidence.references[0]
        duration, cadence, cadence_source, cadence_notes = _schedule_values(
            context, "movement", reference,
        )
        if not reference.intensity_wording:
            raise WorkerStop("missing_sourced_intensity_wording")
        draft = _base_draft(
            request_id=request_id, agent=self.agent, context=context, evidence=evidence,
            evaluation_only=evaluation_only,
            summary="Here is a conservative movement option based on the cited stage-applicable material.",
        )
        draft["contributions"] = [PlanContribution(
            contribution_id=f"movement-{reference.evidence_id}",
            contributor=self.agent, domain="movement",
            item=reference.candidate_label or "Gentle evidence-linked movement",
            duration_minutes=duration, cadence_per_week=cadence,
            preferred_time_windows=["morning", "afternoon"],
            evidence_ids=[reference.evidence_id],
            constraint_notes=[
                *[_visible_constraint(item) for item in restrictions],
                f"Cited intensity: {reference.intensity_wording}.",
                "Stop if symptoms appear or worsen; this is not medical clearance.",
                *cadence_notes,
            ],
            optional=True, flexible=True, flexible_alternatives=reference.flexible_alternatives,
            rest_recovery_notes=reference.rest_recovery_notes, cadence_source=cadence_source,
            state_version=context.state_version,
        )]
        return draft

    def validate_result(self, result, context, evidence):
        failure = super().validate_result(result, context, evidence)
        if failure:
            return failure
        for contribution in result.contributions:
            notes = " ".join(contribution.constraint_notes).casefold()
            if "stop" not in notes or "clearance" not in notes:
                return "structured_output_dropped_movement_stop_boundary"
        return None


class WellbeingAgent(BoundedWorker):
    agent = AgentName.WELLBEING

    def build_draft(self, *, request_id, query, context, evidence, evaluation_only):
        if any(term in query.casefold() for term in WELLBEING_ESCALATION_TERMS):
            raise WorkerStop("persistent_or_worsening_concern_requires_professional_followup", WorkerStatus.NEEDS_CLARIFICATION)
        if not evidence.references:
            raise WorkerStop("missing_wellbeing_evidence")
        reference = evidence.references[0]
        duration, cadence, cadence_source, cadence_notes = _schedule_values(
            context, "wellbeing", reference,
        )
        draft = _base_draft(
            request_id=request_id, agent=self.agent, context=context, evidence=evidence,
            evaluation_only=evaluation_only,
            summary="It makes sense to want support. You can choose whether this brief option feels useful.",
        )
        draft["contributions"] = [PlanContribution(
            contribution_id=f"wellbeing-{reference.evidence_id}",
            contributor=self.agent, domain="wellbeing",
            item=reference.candidate_label or "Optional grounding or reflection exercise",
            duration_minutes=duration, cadence_per_week=cadence,
            preferred_time_windows=["evening"],
            evidence_ids=[reference.evidence_id],
            constraint_notes=["Optional supportive activity; not a diagnosis or continuous monitoring.", *cadence_notes],
            optional=True, flexible=True, flexible_alternatives=reference.flexible_alternatives,
            rest_recovery_notes=reference.rest_recovery_notes, cadence_source=cadence_source,
            state_version=context.state_version,
        )]
        draft["proposed_actions"] = [
            _action("wellbeing-choice", "Choose whether to try or decline this supportive exercise."),
        ]
        return draft


class FollowupAgent(BoundedWorker):
    agent = AgentName.FOLLOWUP

    def build_draft(self, *, request_id, query, context, evidence, evaluation_only):
        if any(item.kind == ContextKind.SYMPTOM and item.current for item in context.items):
            raise WorkerStop("new_symptom_requires_safety_gate", WorkerStatus.ESCALATED)
        unresolved_instructions = [
            item for item in context.items
            if item.kind == ContextKind.CLINICIAN_INSTRUCTION
            and item.state in {FactState.CONFLICTING, FactState.STALE}
        ]
        if unresolved_instructions:
            raise WorkerStop("unresolved_followup_instruction", WorkerStatus.NEEDS_CLARIFICATION)
        relevant = [item for item in context.items if item.kind in {
            ContextKind.APPOINTMENT, ContextKind.OPEN_QUESTION, ContextKind.DOCUMENT_FACT,
            ContextKind.PLAN_STATE, ContextKind.CLINICIAN_INSTRUCTION,
        }]
        if not relevant:
            raise WorkerStop("missing_followup_provenance", WorkerStatus.NEEDS_CLARIFICATION)
        unique: dict[str, ContextItem] = {}
        for item in relevant:
            unique.setdefault(str(item.value).casefold(), item)
        draft = _base_draft(
            request_id=request_id, agent=self.agent, context=context, evidence=evidence,
            evaluation_only=evaluation_only,
            summary="Here is a concise appointment and follow-up brief, separated by when each task belongs.",
        )
        tasks = []
        for index, item in enumerate(unique.values()):
            phase = "during_appointment" if item.kind in {
                ContextKind.OPEN_QUESTION, ContextKind.CLINICIAN_INSTRUCTION,
            } else "before_appointment"
            tasks.append(FollowupTask(
                task_id=f"followup-{index + 1}", phase=phase,
                description=str(item.value), provenance_ids=[item.item_id],
                safety_priority=item.state == FactState.CONFLICTING,
                requires_consent="remind" in query.casefold(),
            ))
        draft["followup_tasks"] = tasks
        if evidence.references:
            draft["contributions"] = [PlanContribution(
                contribution_id=f"followup-{evidence.references[0].evidence_id}",
                contributor=self.agent, domain="followup",
                item="Review the appointment brief before the visit",
                duration_minutes=15, cadence_per_week=1,
                preferred_time_windows=["evening"],
                evidence_ids=[evidence.references[0].evidence_id],
                constraint_notes=["Organizational task only; completion and reminders require confirmation."],
                optional=False, flexible=True, cadence_source="single_proposal",
                state_version=context.state_version,
            )]
        draft["proposed_actions"] = [
            _action("followup-confirm", "Confirm any reminder or tracking action before it is saved."),
        ]
        return draft


WORKER_TYPES: dict[AgentName, type[BoundedWorker]] = {
    AgentName.RECORD: RecordAgent,
    AgentName.MEDICATION: MedicationRecordAgent,
    AgentName.SYMPTOM: SymptomNavigationAgent,
    AgentName.NUTRITION: NutritionAgent,
    AgentName.MOVEMENT: MovementAgent,
    AgentName.WELLBEING: WellbeingAgent,
    AgentName.FOLLOWUP: FollowupAgent,
}


def worker_for(agent: AgentName, provider: StructuredProvider) -> BoundedWorker:
    if agent == AgentName.PLAN_COMPOSER:
        raise ValueError("Plan Composer uses the deterministic Schedule Builder boundary")
    return WORKER_TYPES[agent](provider)
