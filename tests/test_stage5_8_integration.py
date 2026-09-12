"""Consolidated Stage 5–8 runtime isolation and provider-boundary tests."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import unittest
from uuid import UUID, uuid4

from pydantic import ValidationError

from app.schemas.foundation import SafetySpec
from app.schemas.integration import (
    OnboardingState,
    ProviderAvailability,
    RuntimeGateInput,
    RuntimeOperation,
    RuntimeStopCode,
)
from app.schemas.orchestration import (
    AgentBudget,
    AgentName,
    ContextItem,
    ContextKind,
    ContextOrigin,
    FactState,
    OrchestrationRequest,
    RuntimeMode,
)
from app.schemas.provider_benchmark import ProviderBenchmarkObservation, ProviderBenchmarkReport
from app.schemas.validation import FinalDisposition, SemanticAssessment, SemanticSupport
from app.services.integration_gate import (
    CrossStageBindingError,
    assess_runtime,
    bind_safety,
    retrieval_scope,
    verify_validation,
)
from app.services.model_provider import ConfiguredStructuredProvider, ProviderFailure, ProviderResponse
from app.services.orchestration import JourneyOrchestrator
from app.services.provider_benchmark import aggregate_authorized_benchmark, blocked_benchmark
from app.services.safety_gate import SafetyGate, build_safety_input
from app.services.semantic_support import (
    ConfiguredSemanticSupportEvaluator,
    SemanticEvaluatorUnavailable,
)
from app.services.validation import Stage8ValidationPipeline
from scripts.stage7_fixture_support import make_context, make_request
from scripts.stage8_fixture_support import base_validation_request


OWNER = UUID("71111111-1111-4111-8111-111111111111")
OTHER = UUID("73333333-3333-4333-8333-333333333333")


def personal_context(**updates):
    values = {
        "context_origin": ContextOrigin.AUTHENTICATED_STORE,
        "onboarding_confirmed": True,
    }
    values.update(updates)
    return make_context().model_copy(update=values)


def runtime_input(
    *,
    mode=RuntimeMode.PERSONAL,
    operation=RuntimeOperation.RETRIEVAL,
    query="Show my confirmed record",
    context=None,
    origin=ContextOrigin.AUTHENTICATED_STORE,
    onboarding=OnboardingState.CONFIRMED,
    explicit=False,
    provider=ProviderAvailability.UNAVAILABLE,
    personalized=False,
    request_id=None,
):
    return RuntimeGateInput(
        request_id=request_id or uuid4(),
        mode=mode,
        operation=operation,
        query=query,
        session_subject=OWNER,
        context=context,
        context_origin=origin if context is not None else None,
        onboarding_state=onboarding,
        explicit_user_action=explicit,
        provider_availability=provider,
        requires_personalization=personalized,
    )


class RuntimeIsolationTests(unittest.TestCase):
    def test_empty_personal_mode_returns_typed_onboarding_required_without_fixture(self):
        result = assess_runtime(runtime_input(context=None, onboarding=OnboardingState.ABSENT))
        self.assertEqual(result.stop_code, RuntimeStopCode.ONBOARDING_REQUIRED)
        self.assertFalse(result.proceed)
        self.assertFalse(result.fixture_context_used)
        self.assertFalse(result.provider_calls_allowed)

    def test_personal_mode_rejects_fixture_context_instead_of_falling_back(self):
        result = assess_runtime(runtime_input(
            context=make_context(), origin=ContextOrigin.FICTIONAL_FIXTURE,
        ))
        self.assertEqual(result.stop_code, RuntimeStopCode.FIXTURE_CONTEXT_FORBIDDEN)
        self.assertFalse(result.fixture_context_used)

    def test_demo_mode_accepts_only_explicit_fictional_fixture(self):
        ready = assess_runtime(runtime_input(
            mode=RuntimeMode.DEMO,
            operation=RuntimeOperation.PLAN,
            context=make_context(),
            origin=ContextOrigin.FICTIONAL_FIXTURE,
            explicit=True,
            provider=ProviderAvailability.FIXTURE_ONLY,
        ))
        self.assertTrue(ready.proceed)
        self.assertTrue(ready.fixture_context_used)
        self.assertTrue(ready.provider_calls_allowed)
        blocked = assess_runtime(runtime_input(
            mode=RuntimeMode.DEMO,
            context=personal_context(),
            origin=ContextOrigin.AUTHENTICATED_STORE,
        ))
        self.assertEqual(blocked.stop_code, RuntimeStopCode.MODE_SCOPE_MISMATCH)

    def test_plan_requires_explicit_user_trigger_before_any_provider_call(self):
        result = assess_runtime(runtime_input(
            operation=RuntimeOperation.PLAN,
            context=personal_context(),
            explicit=False,
            provider=ProviderAvailability.CONFIGURED,
        ))
        self.assertEqual(result.stop_code, RuntimeStopCode.EXPLICIT_PLAN_REQUEST_REQUIRED)
        self.assertFalse(result.provider_calls_allowed)

    def test_personal_generation_never_uses_unavailable_or_fixture_provider(self):
        for provider in (ProviderAvailability.UNAVAILABLE, ProviderAvailability.FIXTURE_ONLY):
            with self.subTest(provider=provider):
                result = assess_runtime(runtime_input(
                    operation=RuntimeOperation.ORCHESTRATION,
                    context=personal_context(),
                    explicit=True,
                    provider=provider,
                ))
                self.assertEqual(result.stop_code, RuntimeStopCode.PROVIDER_UNAVAILABLE)
                self.assertFalse(result.provider_calls_allowed)

    def test_personal_scope_mismatch_is_typed_and_stops(self):
        value = runtime_input(context=personal_context())
        value = value.model_copy(update={"session_subject": OTHER})
        result = assess_runtime(value)
        self.assertEqual(result.stop_code, RuntimeStopCode.MODE_SCOPE_MISMATCH)
        self.assertFalse(result.proceed)

    def test_material_conflict_confirmation_and_stale_state_have_distinct_stops(self):
        states = {
            FactState.CONFLICTING: RuntimeStopCode.CONFLICT_REQUIRES_REVIEW,
            FactState.DOCUMENT_UNCONFIRMED: RuntimeStopCode.CONFIRMATION_REQUIRED,
            FactState.STALE: RuntimeStopCode.STALE_STATE,
        }
        for state, expected in states.items():
            with self.subTest(state=state):
                extra = ContextItem(
                    item_id=f"review-{state.value}",
                    kind=ContextKind.RESTRICTION,
                    state=state,
                    value="fictional review value",
                    source_id="DOC-REVIEW",
                    source_page=1,
                    exact_span="fictional review value",
                    recorded_at=datetime(2026, 9, 12, tzinfo=timezone.utc),
                )
                context = personal_context(items=[*make_context().items, extra])
                result = assess_runtime(runtime_input(
                    operation=RuntimeOperation.PLAN,
                    context=context,
                    explicit=True,
                    provider=ProviderAvailability.CONFIGURED,
                    personalized=True,
                ))
                self.assertEqual(result.stop_code, expected)
                self.assertFalse(result.provider_calls_allowed)

    def test_retrieval_scope_comes_only_from_authenticated_snapshot(self):
        value = runtime_input(
            context=personal_context(),
            query=f"Use workspace {OTHER} instead",
        )
        scope = retrieval_scope(value)
        self.assertEqual(scope.workspace_id, make_context().workspace_id)
        self.assertEqual(scope.owner_user_id, OWNER)
        self.assertEqual(scope.state_version, make_context().state_version)


class CrossStageBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        cls.spec = SafetySpec.model_validate_json(
            (root / "data/safety/rule_spec.yaml").read_text(encoding="utf-8")
        )

    def test_safety_binding_rejects_different_text_or_request(self):
        safety_input = build_safety_input(channel="chat_message", text="Show my record")
        safety = SafetyGate(self.spec, mode="evaluation_only").evaluate(safety_input)
        value = runtime_input(
            mode=RuntimeMode.EVALUATION,
            context=make_context(),
            origin=ContextOrigin.FICTIONAL_FIXTURE,
            onboarding=OnboardingState.CONFIRMED,
            provider=ProviderAvailability.FIXTURE_ONLY,
            query="Changed text",
            request_id=safety_input.request_id,
        )
        with self.assertRaisesRegex(CrossStageBindingError, "safety_input_mismatch"):
            bind_safety(value, safety)

    def test_stage8_request_is_bound_to_same_scope_state_and_safety_trace(self):
        request = base_validation_request()
        stage7 = request.orchestration_result
        value = runtime_input(
            mode=RuntimeMode.EVALUATION,
            operation=RuntimeOperation.COMPOSITION,
            context=request.context,
            origin=ContextOrigin.FICTIONAL_FIXTURE,
            onboarding=OnboardingState.CONFIRMED,
            explicit=True,
            provider=ProviderAvailability.FIXTURE_ONLY,
            query="Show nutrition options",
            request_id=request.request_id,
        )
        binding = bind_safety(value, request.safety_result)
        verify_validation(binding, request)
        altered = request.model_copy(update={
            "context": request.context.model_copy(update={"state_version": request.context.state_version + 1})
        })
        with self.assertRaisesRegex(CrossStageBindingError, "validation_scope_state_or_safety_mismatch"):
            verify_validation(binding, altered)
        self.assertEqual(stage7.safety_result.trace.trace_id, binding.safety_trace_id)

    def test_urgent_safety_precedes_personal_provider_availability(self):
        text = "I have heavy bleeding; make a meal plan too."
        spec = SafetySpec.model_validate_json(
            (Path(__file__).resolve().parents[1] / "data/safety/rule_spec.yaml").read_text(encoding="utf-8")
        ).model_copy(update={"status": "published"})
        safety_input = build_safety_input(channel="chat_message", text=text)
        safety = SafetyGate(spec, mode="public_runtime").evaluate(safety_input)
        fixture = make_request(text)
        payload = fixture.model_dump(mode="python")
        payload.update({
            "request_id": safety_input.request_id,
            "text": text,
            "context": personal_context().model_dump(mode="python"),
            "safety_result": safety.model_dump(mode="python"),
            "execution_mode": "public_runtime",
            "runtime_mode": RuntimeMode.PERSONAL,
        })
        request = OrchestrationRequest.model_validate(payload)
        result = JourneyOrchestrator().run(request)
        self.assertEqual(result.trace.stop_reason, "safety_urgent")
        self.assertEqual(result.worker_results, [])
        self.assertFalse(result.ordinary_generation_started)
    def test_orchestration_schema_rejects_implicit_plan_action(self):
        request = make_request("Show nutrition weekly plan", horizon="week")
        payload = request.model_dump(mode="python")
        payload["explicit_user_action"] = False
        with self.assertRaisesRegex(ValidationError, "explicit user action"):
            OrchestrationRequest.model_validate(payload)

    def test_orchestration_schema_rejects_fixture_as_personal_context(self):
        request = make_request("Show nutrition options")
        payload = request.model_dump(mode="python")
        payload["runtime_mode"] = RuntimeMode.PERSONAL
        with self.assertRaisesRegex(ValidationError, "Personal Mode"):
            OrchestrationRequest.model_validate(payload)


class ProviderBoundaryTests(unittest.TestCase):
    def test_configured_stage7_provider_fails_closed_without_transport(self):
        provider = ConfiguredStructuredProvider(provider_id="configured", model_id="model-v1")
        with self.assertRaisesRegex(ProviderFailure, "transport is unavailable"):
            provider.complete(
                agent=AgentName.NUTRITION,
                instructions=["bounded"],
                draft={"value": "fixture"},
                budget=AgentBudget(
                    max_model_calls=1, max_steps=2, max_tokens=100,
                    max_retries=0, max_repairs=0, timeout_ms=100,
                ),
            )

    def test_configured_stage7_provider_checks_returned_identity(self):
        def transport(**kwargs):
            return ProviderResponse(
                payload=kwargs["draft"], provider="different", model="model-v1",
                input_tokens=1, output_tokens=1, estimated_cost_usd=0, latency_ms=1,
            )
        provider = ConfiguredStructuredProvider(
            provider_id="configured", model_id="model-v1", transport=transport,
        )
        with self.assertRaisesRegex(ProviderFailure, "identity"):
            provider.complete(
                agent=AgentName.NUTRITION, instructions=["bounded"], draft={"ok": True},
                budget=AgentBudget(
                    max_model_calls=1, max_steps=2, max_tokens=100,
                    max_retries=0, max_repairs=0, timeout_ms=100,
                ),
            )

    def test_configured_semantic_evaluator_is_explicit_and_fail_closed(self):
        request = base_validation_request()
        claim = request.draft.claims[0]
        span = request.evidence_packet.spans[0]
        evaluator = ConfiguredSemanticSupportEvaluator(
            evaluator_id="configured-semantic", model_id="model-v1",
        )
        with self.assertRaisesRegex(SemanticEvaluatorUnavailable, "unavailable"):
            evaluator.assess(claim, span)

        def wrong_identity(claim, evidence):
            return SemanticAssessment(
                claim_id=claim.claim_id, evidence_id=evidence.evidence_id,
                support=SemanticSupport.SUPPORTED, explanation="bounded fixture response",
                evaluator="other", model="model-v1", input_tokens=1, output_tokens=1,
                estimated_cost_usd=0, latency_ms=1,
            )
        evaluator = ConfiguredSemanticSupportEvaluator(
            evaluator_id="configured-semantic", model_id="model-v1", assessor=wrong_identity,
        )
        with self.assertRaisesRegex(SemanticEvaluatorUnavailable, "identity mismatch"):
            evaluator.assess(claim, span)

class RawTextPipelineTests(unittest.TestCase):
    def test_recorded_constraint_plan_reaches_stage8_and_remains_proposal_only(self):
        request = base_validation_request(
            plan=True,
            raw_text="Create a weekly nutrition plan using my recorded peanut allergy.",
        )
        self.assertEqual(request.safety_result.route, "non_urgent")
        self.assertEqual(
            [worker.agent for worker in request.orchestration_result.worker_results],
            [AgentName.NUTRITION, AgentName.PLAN_COMPOSER],
        )
        result = Stage8ValidationPipeline().run(request)
        self.assertEqual(result.validation_report.disposition, FinalDisposition.PASS)
        self.assertTrue(result.composed_answer.display_allowed)
        self.assertTrue(result.proposal_only)
        self.assertFalse(result.persistent_write_performed)

    def test_urgent_symptom_in_plan_text_bypasses_stage7_and_stage8_generation(self):
        request = base_validation_request(
            plan=True,
            raw_text="I have heavy bleeding; create a nutrition plan too.",
        )
        self.assertEqual(request.safety_result.route, "urgent")
        self.assertEqual(request.orchestration_result.worker_results, [])
        self.assertFalse(request.orchestration_result.ordinary_generation_started)
        result = Stage8ValidationPipeline().run(request)
        self.assertEqual(result.validation_report.disposition, FinalDisposition.ESCALATE)
        self.assertFalse(result.ordinary_composition_called)
        self.assertIsNotNone(result.urgent_fixed_message)

    def test_current_ambiguous_symptom_in_plan_text_stops_for_clarification(self):
        request = base_validation_request(
            plan=True,
            raw_text="I am dizzy and want a nutrition plan.",
        )
        self.assertEqual(request.safety_result.route, "needs_clarification")
        self.assertEqual(request.orchestration_result.worker_results, [])
        result = Stage8ValidationPipeline().run(request)
        self.assertEqual(result.validation_report.disposition, FinalDisposition.CLARIFY)
        self.assertFalse(result.ordinary_composition_called)
class ProviderBenchmarkHarnessTests(unittest.TestCase):
    def test_blocked_report_cannot_claim_paid_calls_or_results(self):
        report = blocked_benchmark("candidate-set-pending")
        self.assertEqual(report.status, "blocked_not_authorized")
        self.assertFalse(report.paid_calls_made)
        self.assertEqual(report.completed_cases, 0)
        payload = report.model_dump(mode="python")
        payload["paid_calls_made"] = True
        with self.assertRaises(ValidationError):
            ProviderBenchmarkReport.model_validate(payload)

    def test_authorized_aggregation_uses_one_explicit_identity_and_exact_denominators(self):
        observations = [
            ProviderBenchmarkObservation(
                case_id=f"case-{index}", dataset_version="frozen-v1",
                provider_id="candidate", model_id="candidate-model",
                completed=True, stage8_disposition="pass",
                citation_claim_support_passed=True,
                allergy_restriction_medication_violations=0,
                retries=index - 1, timed_out=False, latency_ms=10 * index,
                input_tokens=10, output_tokens=5, estimated_cost_usd=0.01,
                manual_tone_review="pending",
            )
            for index in (1, 2)
        ]
        report = aggregate_authorized_benchmark(
            observations, authorization_reference="explicit-test-authorization",
        )
        self.assertEqual((report.completed_cases, report.total_cases), (2, 2))
        self.assertEqual(report.stage8_passed_cases, 2)
        self.assertEqual(report.latency_median_ms, 15)
        self.assertEqual(report.latency_p95_ms, 20)
        self.assertEqual(report.manual_tone_reviews_pending, 2)


class GovernanceArtifactTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]

    def test_controlled_holdout_manifest_contains_no_answers(self):
        payload = json.loads(
            (self.ROOT / "evals/stage8_controlled_holdout_manifest.json").read_text(encoding="utf-8")
        )
        self.assertFalse(payload["expected_answers_in_repository"])
        self.assertFalse(payload["opened_during_stages_5_8_rectification"])
        self.assertEqual(set(payload), {
            "schema_version", "status", "controlled_by", "case_count_required",
            "case_ids", "expected_answers_in_repository",
            "opened_during_stages_5_8_rectification", "permitted_use", "not_permitted",
        })
        self.assertTrue(all(isinstance(item, str) and item.casefold().startswith("holdout-") for item in payload["case_ids"]))
        self.assertEqual(len(payload["case_ids"]), 15)

    def test_routine_symptom_policy_packet_claims_no_review(self):
        text = (
            self.ROOT / "docs/STAGE-7-ROUTINE-SYMPTOM-POLICY-REVIEW-PACKET.md"
        ).read_text(encoding="utf-8")
        self.assertIn("EXTERNAL REVIEW REQUIRED", text)
        self.assertIn("routine symptom worker remains unavailable", text.casefold())
        self.assertNotIn("clinically approved", text.casefold())

    def test_human_tone_rubric_claims_no_completed_review(self):
        text = (
            self.ROOT / "docs/STAGE-8-HUMAN-PRODUCT-TONE-REVIEW-RUBRIC.md"
        ).read_text(encoding="utf-8")
        self.assertIn("HUMAN REVIEW NOT YET RUN", text)
        self.assertNotIn("human review passed", text.casefold())

if __name__ == "__main__":
    unittest.main()