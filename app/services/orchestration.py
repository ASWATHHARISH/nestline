"""Stage 7 Journey Orchestrator with deterministic routing and bounded workers."""

from __future__ import annotations

import re
from time import perf_counter
from pydantic import ValidationError

from app.schemas.orchestration import (
    AgentName,
    AgentTrace,
    AvailabilityWindow,
    ContextKind,
    EvidencePlanItem,
    FixedAppointment,
    Intent,
    OrchestrationRequest,
    OrchestrationResult,
    OrchestrationTrace,
    ProposedSchedule,
    RecordedReminder,
    RoutePlan,
    RuntimeMode,
    ScheduleRequest,
    WorkerEvidence,
    WorkerResult,
    WorkerStatus,
)
from app.services.agents import build_minimal_context, worker_for
from app.services.model_provider import (
    DeterministicFixtureProvider, ProviderFailure, StructuredProvider,
)
from app.services.orchestration_catalogue import AGENT_CATALOGUE, definition_for
from app.services.schedule_builder import ScheduleBuilder


INTENT_KEYWORDS: dict[Intent, tuple[str, ...]] = {
    Intent.MEDICATION: ("medication", "medicine", "supplement", "tablet", "dose", "pill"),
    Intent.RECORD: ("record", "document", "report", "lab result", "extraction"),
    Intent.SYMPTOM: ("symptom", "pain", "bleeding", "dizzy", "breathing", "fever", "swelling"),
    Intent.NUTRITION: ("nutrition", "meal", "diet", "food", "eat"),
    Intent.MOVEMENT: ("movement", "exercise", "fitness", "walk", "yoga", "activity"),
    Intent.WELLBEING: ("wellbeing", "well-being", "grounding", "reflection", "support plan", "mental health"),
    Intent.FOLLOWUP: ("follow-up", "follow up", "appointment", "brief", "reminder", "questions"),
}
AGENT_FOR_INTENT = {
    Intent.RECORD: AgentName.RECORD,
    Intent.MEDICATION: AgentName.MEDICATION,
    Intent.SYMPTOM: AgentName.SYMPTOM,
    Intent.NUTRITION: AgentName.NUTRITION,
    Intent.MOVEMENT: AgentName.MOVEMENT,
    Intent.WELLBEING: AgentName.WELLBEING,
    Intent.FOLLOWUP: AgentName.FOLLOWUP,
}
PLAN_CONTRIBUTORS = {
    Intent.NUTRITION: AgentName.NUTRITION,
    Intent.MOVEMENT: AgentName.MOVEMENT,
    Intent.WELLBEING: AgentName.WELLBEING,
    Intent.FOLLOWUP: AgentName.FOLLOWUP,
}


def _default_evidence(agent: AgentName, evaluation_only: bool) -> WorkerEvidence:
    return WorkerEvidence(
        retrieval_purpose=definition_for(agent).retrieval_purpose,
        references=[],
        corpus_mode="controlled_fixture" if evaluation_only else "production_release",
        public_routing_eligible=not evaluation_only,
    )


def _contains_keyword(text: str, keyword: str) -> bool:
    """Match whole words/phrases so `eat` cannot match inside `peanut`."""

    return re.search(r"(?<!\w)" + re.escape(keyword) + r"(?!\w)", text) is not None


def classify_intents(text: str) -> list[Intent]:
    lower = text.casefold()
    matches: list[Intent] = []
    for intent, words in INTENT_KEYWORDS.items():
        if any(_contains_keyword(lower, word) for word in words):
            matches.append(intent)
    if Intent.MEDICATION in matches and Intent.RECORD in matches:
        return [Intent.MEDICATION]
    # Record phrasing owns category lookups such as "medications in my record".
    if Intent.RECORD in matches and any(word in lower for word in ("in my record", "record says", "document says")):
        if Intent.MEDICATION in matches:
            return [Intent.MEDICATION]
        return [Intent.RECORD]
    return matches


def build_route_plan(request: OrchestrationRequest) -> RoutePlan:
    """Create a stable route without a model call or unbounded fan-out."""

    if request.safety_result.route != "non_urgent":
        return RoutePlan(
            intent=Intent.SYMPTOM if request.safety_result.route == "urgent" else Intent.AMBIGUOUS_MULTI_INTENT,
            selected_workers=[],
            reason=f"Stage 6 returned {request.safety_result.route}; every ordinary worker is blocked.",
            evidence_plan=[], routing_call_count=0, total_call_budget=0,
            total_step_budget=1, requires_clarification=request.safety_result.route == "needs_clarification",
        )

    intents = classify_intents(request.text)
    lower = request.text.casefold()
    plan_requested = request.requested_horizon != "none" or any(
        phrase in lower for phrase in ("full plan", "holistic plan", "daily plan", "day plan", "weekly plan", "week plan")
    )
    if plan_requested:
        contributors = [PLAN_CONTRIBUTORS[intent] for intent in intents if intent in PLAN_CONTRIBUTORS]
        if not contributors and any(phrase in lower for phrase in ("full plan", "holistic plan", "weekly plan", "week plan", "daily plan", "day plan")):
            contributors = list(PLAN_CONTRIBUTORS.values())
        contributors = list(dict.fromkeys(contributors))
        if not contributors:
            return RoutePlan(
                intent=Intent.AMBIGUOUS_MULTI_INTENT, selected_workers=[],
                reason="The requested plan has no supported domain.", evidence_plan=[],
                routing_call_count=0, total_call_budget=0, total_step_budget=2,
                requires_clarification=True,
            )
        selected = [*contributors, AgentName.PLAN_COMPOSER]
        return RoutePlan(
            intent=Intent.FULL_PLAN,
            selected_workers=selected,
            reason="The request explicitly asks for a bounded day/week plan.",
            evidence_plan=[EvidencePlanItem(
                agent=agent,
                purpose=definition_for(agent).retrieval_purpose,
                allowed_lanes=definition_for(agent).allowed_evidence_lanes,
            ) for agent in selected],
            routing_call_count=0,
            total_call_budget=len(selected),
            total_step_budget=min(request.max_total_steps, 8 + 4 * len(selected)),
        )
    if not intents:
        return RoutePlan(
            intent=Intent.OUT_OF_SCOPE, selected_workers=[],
            reason="No supported Stage 7 intent was identified.", evidence_plan=[],
            routing_call_count=0, total_call_budget=0, total_step_budget=2,
        )
    if len(intents) > 1:
        return RoutePlan(
            intent=Intent.AMBIGUOUS_MULTI_INTENT, selected_workers=[],
            reason="Multiple domains were identified without an explicit plan request.",
            evidence_plan=[], routing_call_count=0, total_call_budget=0,
            total_step_budget=2, requires_clarification=True,
        )
    intent = intents[0]
    agent = AGENT_FOR_INTENT[intent]
    definition = definition_for(agent)
    return RoutePlan(
        intent=intent, selected_workers=[agent],
        reason=f"One {intent.value} specialist is sufficient.",
        evidence_plan=[EvidencePlanItem(
            agent=agent, purpose=definition.retrieval_purpose,
            allowed_lanes=definition.allowed_evidence_lanes,
        )],
        routing_call_count=0, total_call_budget=1,
        total_step_budget=min(request.max_total_steps, 8),
    )


class JourneyOrchestrator:
    """Coordinates workers through typed state; workers never call each other."""

    def __init__(
        self,
        *,
        provider: StructuredProvider | None = None,
        schedule_builder: ScheduleBuilder | None = None,
    ) -> None:
        self.provider = provider or DeterministicFixtureProvider()
        self.schedule_builder = schedule_builder or ScheduleBuilder()

    def run(self, request: OrchestrationRequest) -> OrchestrationResult:
        started = perf_counter()
        route = build_route_plan(request)
        if request.safety_result.route != "non_urgent":
            return self._result(request, route, [], None, started, f"safety_{request.safety_result.route}")
        if request.runtime_mode == RuntimeMode.PERSONAL and getattr(self.provider, "fixture_only", True):
            blocked = route.model_copy(update={
                "selected_workers": [],
                "evidence_plan": [],
                "requires_clarification": True,
                "reason": "Personal Mode cannot fall back to the deterministic fixture provider.",
                "total_call_budget": 0,
            })
            return self._result(
                request, blocked, [], None, started, "personal_provider_unavailable",
            )
        if not route.selected_workers:
            reason = "clarification_required" if route.requires_clarification else "unsupported_intent"
            return self._result(request, route, [], None, started, reason)
        if route.total_call_budget > request.max_total_model_calls:
            # Fail before any worker/provider is called.
            blocked = route.model_copy(update={
                "selected_workers": [], "evidence_plan": [],
                "requires_clarification": True,
                "reason": "The requested workflow exceeds the caller's total call budget.",
                "total_call_budget": 0,
            })
            return self._result(request, blocked, [], None, started, "budget_exhausted_before_execution")

        results: list[WorkerResult] = []
        schedule: ProposedSchedule | None = None
        for index, agent in enumerate(route.selected_workers):
            remaining_ms = request.timeout_ms - int((perf_counter() - started) * 1000)
            if remaining_ms < 50:
                partial = self._executed_route(route, results, "Total orchestration timeout reached.")
                return self._result(
                    request, partial, results, schedule, started, "orchestration_timeout",
                )
            evidence = request.evidence_by_agent.get(
                agent, _default_evidence(agent, request.execution_mode == "evaluation_only")
            )
            context = build_minimal_context(agent=agent, snapshot=request.context)
            if agent == AgentName.PLAN_COMPOSER:
                result, schedule = self._compose(
                    request, context, evidence, results, started, remaining_ms,
                )
            else:
                result = worker_for(agent, self.provider).run(
                    request_id=request.request_id, query=request.text,
                    context=context, evidence=evidence,
                    safety_result=request.safety_result,
                    evaluation_only=request.execution_mode == "evaluation_only",
                    timeout_ms=remaining_ms,
                )
            results.append(result)
            if result.status != WorkerStatus.COMPLETED:
                partial = self._executed_route(
                    route, results, f"Stopped after {agent.value}: {result.stop_reason}.",
                )
                return self._result(
                    request, partial, results, schedule, started, "worker_stopped",
                )
            if index < len(route.selected_workers) - 1 and (
                (perf_counter() - started) * 1000 >= request.timeout_ms
            ):
                partial = self._executed_route(route, results, "Total orchestration timeout reached.")
                return self._result(
                    request, partial, results, schedule, started, "orchestration_timeout",
                )
        return self._result(request, route, results, schedule, started, "completed")

    @staticmethod
    def _executed_route(route: RoutePlan, results: list[WorkerResult], reason: str) -> RoutePlan:
        return route.model_copy(update={
            "selected_workers": [result.agent for result in results],
            "evidence_plan": route.evidence_plan[:len(results)],
            "total_call_budget": len(results),
            "reason": reason,
            "requires_clarification": False,
        })

    def _compose(self, request, context, evidence, previous, started, remaining_ms):
        contributor_results = [result for result in previous if result.agent in {
            AgentName.NUTRITION, AgentName.MOVEMENT, AgentName.WELLBEING, AgentName.FOLLOWUP,
        }]
        if not contributor_results or any(result.status != WorkerStatus.COMPLETED for result in contributor_results):
            return self._composer_stop(request, context, evidence, "contributor_not_completed", started), None
        contributions = [item for result in contributor_results for item in result.contributions]
        if not contributions:
            return self._composer_stop(request, context, evidence, "no_validated_contributions", started), None
        availability = self._availability(context.items)
        if not availability:
            return self._composer_stop(request, context, evidence, "missing_user_availability", started), None
        appointments = self._appointments(context.items)
        reminders = self._recorded_reminders(context.items)
        constraints = [
            f"{item.kind.value}: {item.value} ({item.state.value})"
            for item in context.items if item.kind in {
                ContextKind.ALLERGY, ContextKind.INTOLERANCE, ContextKind.RESTRICTION,
                ContextKind.CLINICIAN_INSTRUCTION,
            }
        ]
        uncertainties = [
            f"{item.kind.value} {item.item_id} is {item.state.value}"
            for item in context.items if item.state.value in {
                "conflicting", "stale", "document_derived_unconfirmed",
            }
        ]
        horizon = request.requested_horizon if request.requested_horizon != "none" else "week"
        context_summary = [
            f"{item.kind.value}: {item.value} ({item.state.value})"
            for item in context.items if item.kind in {
                ContextKind.CONDITION, ContextKind.DOCUMENT_FACT, ContextKind.MEDICATION,
                ContextKind.SUPPLEMENT, ContextKind.CLINICIAN_INSTRUCTION,
            }
        ]
        schedule = self.schedule_builder.build(ScheduleRequest(
            horizon=horizon,
            selected_day=request.selected_day,
            state_version=context.state_version,
            availability=availability,
            appointments=appointments,
            contributions=contributions,
            recorded_reminders=reminders,
            applied_constraints=constraints,
            unresolved_uncertainties=uncertainties,
            verified_context_summary=context_summary,
        ))
        definition = definition_for(AgentName.PLAN_COMPOSER)
        draft = {
            "request_id": request.request_id,
            "agent": AgentName.PLAN_COMPOSER,
            "status": WorkerStatus.COMPLETED if schedule.save_eligible else WorkerStatus.NEEDS_CLARIFICATION,
            "journey_state_version": context.state_version,
            "summary": "I arranged the validated contributions into an editable proposal. "
                       "Please review every constraint and uncertainty before choosing what to do next.",
            "facts_used": [item.item_id for item in context.items if item.state.value == "confirmed"],
            "citations": [citation for result in contributor_results for citation in result.citations],
            "applied_constraints": constraints,
            "uncertainties": [*uncertainties, *schedule.conflicts],
            "proposed_actions": [], "proposed_state_changes": [],
            "record_findings": [], "medication_timeline": [], "symptom_navigation": None,
            "contributions": [], "followup_tasks": [],
            "requires_human_review": bool(uncertainties),
            "stop_reason": None if schedule.save_eligible else "schedule_requires_clarification",
            "evaluation_only": request.execution_mode == "evaluation_only",
            "public_eligible": False,
        }
        effective_budget = definition.budget.model_copy(update={
            "timeout_ms": min(definition.budget.timeout_ms, remaining_ms),
        })
        provider_started = perf_counter()
        try:
            response = self.provider.complete(
                agent=AgentName.PLAN_COMPOSER,
                instructions=definition.model_instructions,
                draft=draft,
                budget=effective_budget,
            )
        except TimeoutError:
            return self._composer_stop(
                request, context, evidence, "provider_timeout", started,
                status=WorkerStatus.FAILED, provider=getattr(self.provider, "provider_id", "unavailable"),
                model=getattr(self.provider, "model_id", "unavailable"), model_calls=1,
            ), None
        except (ProviderFailure, RuntimeError):
            return self._composer_stop(
                request, context, evidence, "provider_failure", started,
                status=WorkerStatus.FAILED, provider=getattr(self.provider, "provider_id", "unavailable"),
                model=getattr(self.provider, "model_id", "unavailable"), model_calls=1,
            ), None
        measured_provider_ms = (perf_counter() - provider_started) * 1000
        if (
            response.input_tokens + response.output_tokens > effective_budget.max_tokens
            or response.latency_ms > effective_budget.timeout_ms
            or measured_provider_ms > effective_budget.timeout_ms
        ):
            return self._composer_stop(
                request, context, evidence, "provider_budget_exhausted", started,
                status=WorkerStatus.FAILED, provider=response.provider,
                model=response.model, model_calls=1,
            ), None
        expected_evidence_ids = sorted({
            citation.evidence_id for result in contributor_results for citation in result.citations
        })
        trace = AgentTrace(
            request_id=request.request_id, agent=AgentName.PLAN_COMPOSER,
            agent_version=definition.version, provider=response.provider,
            model=response.model, evidence_ids=expected_evidence_ids,
            model_call_count=1, step_count=3,
            input_tokens=response.input_tokens, output_tokens=response.output_tokens,
            estimated_cost_usd=response.estimated_cost_usd,
            retry_count=0, repair_count=0,
            latency_ms=(perf_counter() - started) * 1000,
            stop_reason="completed" if schedule.save_eligible else "schedule_requires_clarification",
        )
        payload = {**response.payload, "trace": trace}
        try:
            result = WorkerResult.model_validate(payload)
        except ValidationError:
            payload["trace"] = trace.model_copy(update={"repair_count": 1})
            try:
                result = WorkerResult.model_validate(payload)
            except ValidationError:
                return self._composer_stop(
                    request, context, evidence, "schema_invalid_after_one_repair", started,
                    status=WorkerStatus.FAILED, provider=response.provider,
                    model=response.model, model_calls=1, repair_count=1,
                ), None
        confirmed_ids = {item.item_id for item in context.items if item.state.value == "confirmed"}
        result_evidence_ids = {citation.evidence_id for citation in result.citations}
        schedule_evidence_ids = {
            value for item in schedule.items if item.domain != "record_reminder"
            for value in item.evidence_ids
        }
        forbidden_claims = (
            "you are safe", "nothing to worry about", "this is normal",
            "must have", "we are monitoring", "i am monitoring",
        )
        if (
            not set(result.facts_used) <= confirmed_ids
            or not set(constraints) <= set(result.applied_constraints)
            or not schedule_evidence_ids <= result_evidence_ids
            or not result_evidence_ids <= set(expected_evidence_ids)
            or any(claim in result.summary.casefold() for claim in forbidden_claims)
        ):
            return self._composer_stop(
                request, context, evidence, "structured_output_failed_composer_boundary", started,
                status=WorkerStatus.FAILED, provider=response.provider,
                model=response.model, model_calls=1,
            ), None
        return result, schedule

    @staticmethod
    def _availability(items) -> list[AvailabilityWindow]:
        values = []
        for item in items:
            if item.kind != ContextKind.PREFERENCE or not isinstance(item.value, dict):
                continue
            if {"day", "start", "end"} <= set(item.value):
                values.append(AvailabilityWindow(
                    day=__import__("app.schemas.orchestration", fromlist=["Weekday"]).Weekday(item.value["day"]), start=item.value["start"], end=item.value["end"],
                ))
        return values

    @staticmethod
    def _appointments(items) -> list[FixedAppointment]:
        values = []
        for item in items:
            if item.kind != ContextKind.APPOINTMENT or not isinstance(item.value, dict):
                continue
            if {"day", "start", "end", "label"} <= set(item.value):
                values.append(FixedAppointment(
                    appointment_id=item.item_id, day=__import__("app.schemas.orchestration", fromlist=["Weekday"]).Weekday(item.value["day"]),
                    start=item.value["start"], end=item.value["end"], label=item.value["label"],
                ))
        return values

    @staticmethod
    def _recorded_reminders(items) -> list[RecordedReminder]:
        values = []
        for item in items:
            if item.kind not in {ContextKind.MEDICATION, ContextKind.SUPPLEMENT}:
                continue
            if item.state.value != "confirmed" or not item.record_only or not isinstance(item.value, dict):
                continue
            if {"day", "time", "exact_instruction"} <= set(item.value):
                values.append(RecordedReminder(
                    reminder_id=f"reminder-{item.item_id}", item_id=item.item_id,
                    wording=f"Recorded reminder: {item.value.get('name', 'documented item')}",
                    day=__import__("app.schemas.orchestration", fromlist=["Weekday"]).Weekday(item.value["day"]), time=item.value["time"],
                    source_id=item.source_id or item.item_id,
                    exact_instruction=item.value["exact_instruction"],
                ))
        return values

    @staticmethod
    def _composer_stop(
        request, context, evidence, reason, started, *,
        status=WorkerStatus.NEEDS_CLARIFICATION,
        provider="not_called", model="not_called", model_calls=0, repair_count=0,
    ):
        definition = definition_for(AgentName.PLAN_COMPOSER)
        return WorkerResult(
            request_id=request.request_id, agent=AgentName.PLAN_COMPOSER,
            status=status,
            journey_state_version=context.state_version,
            summary=f"I cannot compose the plan yet because of {reason.replace('_', ' ')}.",
            uncertainties=[reason], requires_human_review=False,
            stop_reason=reason,
            evaluation_only=request.execution_mode == "evaluation_only",
            public_eligible=False,
            trace=AgentTrace(
                request_id=request.request_id, agent=AgentName.PLAN_COMPOSER,
                agent_version=definition.version, provider=provider, model=model,
                evidence_ids=[r.evidence_id for r in evidence.references],
                model_call_count=model_calls, step_count=1, input_tokens=0, output_tokens=0,
                estimated_cost_usd=0, retry_count=0, repair_count=repair_count,
                latency_ms=(perf_counter() - started) * 1000, stop_reason=reason,
            ),
        )

    @staticmethod
    def _result(request, route, results, schedule, started, stop_reason):
        model_calls = sum(result.trace.model_call_count for result in results)
        steps = 1 + sum(result.trace.step_count for result in results)
        return OrchestrationResult(
            request_id=request.request_id,
            safety_result=request.safety_result,
            route_plan=route,
            worker_results=results,
            proposed_schedule=schedule,
            ordinary_generation_started=model_calls > 0,
            public_eligible=(
                request.execution_mode == "public_runtime"
                and request.safety_result.public_routing_eligible
                and bool(results)
                and all(result.public_eligible for result in results)
            ),
            trace=OrchestrationTrace(
                request_id=request.request_id, selected_workers=[result.agent for result in results],
                worker_call_count=len(results), total_model_calls=model_calls,
                total_steps=steps, total_tokens=sum(
                    result.trace.input_tokens + result.trace.output_tokens for result in results
                ), estimated_cost_usd=sum(result.trace.estimated_cost_usd for result in results),
                retry_count=sum(result.trace.retry_count for result in results),
                latency_ms=(perf_counter() - started) * 1000, stop_reason=stop_reason,
            ),
        )


def agent_catalogue() -> dict[AgentName, object]:
    """Return the immutable typed catalogue for checkers and future UI inspection."""

    return dict(AGENT_CATALOGUE)
