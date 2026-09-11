"""Stage 7 orchestration, worker, provider, and schedule boundary tests."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import unittest
from uuid import UUID

from pydantic import ValidationError

from app.schemas.foundation import SafetySpec
from app.schemas.orchestration import (
    AgentName,
    AuthenticatedContextSnapshot,
    AvailabilityWindow,
    ContextItem,
    ContextKind,
    EvidenceLane,
    EvidenceReference,
    FactState,
    FixedAppointment,
    OrchestrationRequest,
    PlanContribution,
    ProposedSchedule,
    RecordedReminder,
    RetrievalPurpose,
    ScheduleRequest,
    Weekday,
    WorkerEvidence,
    WorkerResult,
    WorkerStatus,
)
from app.schemas.retrieval import JourneyPosition
from app.services.agents import build_minimal_context, worker_for
from app.services.model_provider import (
    DeterministicFixtureProvider, ProviderFailure, ProviderResponse, ScriptedTestProvider,
)
from app.services.orchestration import JourneyOrchestrator, agent_catalogue, build_route_plan
from app.services.orchestration_catalogue import CONTEXT_POLICY, definition_for
from app.services.safety_gate import SafetyGate, build_safety_input
from app.services.schedule_builder import ScheduleBuilder


ROOT = Path(__file__).resolve().parents[1]
OWNER = UUID("11111111-1111-4111-8111-111111111111")
WORKSPACE = UUID("22222222-2222-4222-8222-222222222222")
NOW = datetime(2026, 9, 12, 8, 0, tzinfo=timezone.utc)


def _gate(text: str):
    spec = SafetySpec.model_validate_json(
        (ROOT / "data/safety/rule_spec.yaml").read_text(encoding="utf-8")
    )
    request = build_safety_input(channel="chat_message", text=text)
    return request, SafetyGate(spec, mode="evaluation_only").evaluate(request)


def item(
    item_id: str,
    kind: ContextKind,
    value,
    *,
    state: FactState = FactState.CONFIRMED,
    source_id: str | None = None,
    span: str | None = None,
    confidence: float | None = None,
    record_only: bool = False,
    current: bool = True,
):
    return ContextItem(
        item_id=item_id, kind=kind, state=state, value=value,
        source_id=source_id, source_page=1 if source_id else None,
        exact_span=span, confidence=confidence, recorded_at=NOW,
        record_only=record_only, current=current,
    )


def context(*, state_version: int = 3, extra: list[ContextItem] | None = None):
    values = [
        item("doc-1", ContextKind.DOCUMENT_FACT, "haemoglobin recorded as 11.2",
             source_id="DOC-001", span="Hb 11.2", confidence=0.98),
        item("med-1", ContextKind.SUPPLEMENT, {
            "name": "Documented supplement", "dose": "1", "unit": "tablet",
            "frequency": "daily", "timing": "08:00", "day": "monday", "time": "08:00",
            "exact_instruction": "Take one tablet at 08:00", "prescriber": "DOC-001",
        }, source_id="DOC-001", span="Take one tablet daily", record_only=True),
        item("allergy-1", ContextKind.ALLERGY, "peanut"),
        item("restriction-1", ContextKind.RESTRICTION, "avoid high impact movement"),
        item("appointment-1", ContextKind.APPOINTMENT, {
            "day": "wednesday", "start": "10:00", "end": "11:00", "label": "Appointment",
        }),
        item("question-1", ContextKind.OPEN_QUESTION, "Ask about the documented result"),
    ]
    for day in Weekday:
        values.append(item(
            f"availability-{day.value}", ContextKind.PREFERENCE,
            {"day": day.value, "start": "08:00", "end": "12:00"},
        ))
    values.extend(extra or [])
    return AuthenticatedContextSnapshot(
        workspace_id=WORKSPACE, care_episode_id=WORKSPACE,
        owner_user_id=OWNER, session_subject=OWNER,
        state_version=state_version, captured_at=NOW,
        journey=JourneyPosition(stage="pregnancy", unit="week", exact=24),
        items=values,
    )


def reference(
    evidence_id: str,
    lane: EvidenceLane,
    *,
    label: str = "Evidence-linked option",
    tags: list[str] | None = None,
    duration: int | None = None,
    cadence: int | None = None,
    intensity: str | None = None,
    alternatives: list[str] | None = None,
    recovery: list[str] | None = None,
):
    public = lane in {
        EvidenceLane.PUBLIC_GUIDELINE, EvidenceLane.WEEKLY_PROFILE,
        EvidenceLane.STRUCTURED_CATALOGUE,
    }
    return EvidenceReference(
        evidence_id=evidence_id, source_id=f"source-{evidence_id}", lane=lane,
        exact_span=f"Synthetic exact span for {evidence_id}", candidate_label=label,
        constraint_tags=tags or [], duration_minutes=duration,
        cadence_per_week=cadence, intensity_wording=intensity,
        flexible_alternatives=alternatives or [], rest_recovery_notes=recovery or [],
        approval_state="controlled_fixture" if public else "confirmed_personal",
        journey=JourneyPosition(stage="pregnancy", unit="week", exact=24) if public else None,
        fixture_only=public,
    )


def evidence(agent: AgentName, refs: list[EvidenceReference] | None = None, **changes):
    value = {
        "retrieval_purpose": definition_for(agent).retrieval_purpose,
        "references": refs or [],
        "corpus_mode": "controlled_fixture",
        "public_routing_eligible": False,
    }
    value.update(changes)
    return WorkerEvidence(**value)


def all_evidence():
    return {
        AgentName.RECORD: evidence(AgentName.RECORD, [reference("personal-record", EvidenceLane.PERSONAL_DOCUMENT)]),
        AgentName.MEDICATION: evidence(AgentName.MEDICATION, [reference("personal-med", EvidenceLane.PERSONAL_SQL)]),
        AgentName.SYMPTOM: evidence(AgentName.SYMPTOM, [reference("symptom-policy", EvidenceLane.PUBLIC_GUIDELINE)]),
        AgentName.NUTRITION: evidence(AgentName.NUTRITION, [
            reference("food-peanut", EvidenceLane.STRUCTURED_CATALOGUE, label="Peanut snack", tags=["peanut"]),
            reference("food-safe", EvidenceLane.STRUCTURED_CATALOGUE, label="Peanut-free meal framework", duration=30, cadence=3),
        ]),
        AgentName.MOVEMENT: evidence(AgentName.MOVEMENT, [reference(
            "movement-24", EvidenceLane.PUBLIC_GUIDELINE, label="Gentle walking option",
            duration=20, cadence=3, intensity="comfortable cited intensity",
            alternatives=["Use the cited shorter-duration option"],
            recovery=["Include rest between sessions as needed"],
        )]),
        AgentName.WELLBEING: evidence(AgentName.WELLBEING, [reference(
            "wellbeing-24", EvidenceLane.PUBLIC_GUIDELINE, label="Optional grounding exercise",
            duration=10, cadence=3,
        )]),
        AgentName.FOLLOWUP: evidence(AgentName.FOLLOWUP, [reference(
            "personal-followup", EvidenceLane.PERSONAL_SQL,
        )]),
        AgentName.PLAN_COMPOSER: evidence(AgentName.PLAN_COMPOSER),
    }


def request(text: str, *, horizon="none", day=None, snapshot=None, maximum=5):
    safety_input, safety = _gate(text)
    return OrchestrationRequest(
        request_id=safety_input.request_id, text=text,
        context=snapshot or context(), safety_result=safety,
        execution_mode="evaluation_only", requested_horizon=horizon,
        selected_day=day, evidence_by_agent=all_evidence(),
        max_total_model_calls=maximum,
    )


class Stage7CatalogueTests(unittest.TestCase):
    def test_catalogue_has_exactly_eight_workers(self):
        catalogue = agent_catalogue()
        self.assertEqual(set(catalogue), set(AgentName))
        self.assertEqual(len(catalogue), 8)

    def test_every_worker_forbids_writes_service_role_and_agent_calls(self):
        for definition in agent_catalogue().values():
            self.assertFalse(definition.direct_persistent_write_allowed)
            self.assertFalse(definition.service_role_allowed)
            self.assertFalse(definition.may_call_other_agent)
            self.assertLessEqual(definition.budget.max_model_calls, 1)
            self.assertLessEqual(definition.budget.max_repairs, 1)

    def test_context_is_minimized_for_each_worker(self):
        source = context()
        for agent in AgentName:
            reduced = build_minimal_context(agent=agent, snapshot=source)
            self.assertTrue(reduced.minimized)
            self.assertTrue(all(row.kind in CONTEXT_POLICY[agent] for row in reduced.items))
        nutrition = build_minimal_context(agent=AgentName.NUTRITION, snapshot=source)
        self.assertNotIn(ContextKind.APPOINTMENT, {row.kind for row in nutrition.items})

    def test_context_rejects_non_owner_session(self):
        value = context().model_dump(mode="python")
        value["session_subject"] = UUID("33333333-3333-4333-8333-333333333333")
        with self.assertRaises(ValidationError):
            AuthenticatedContextSnapshot.model_validate(value)


class Stage7RoutingTests(unittest.TestCase):
    def test_urgent_input_invokes_zero_agents(self):
        result = JourneyOrchestrator().run(request("I cannot breathe. Show my weekly plan."))
        self.assertEqual(result.safety_result.route, "urgent")
        self.assertEqual(result.worker_results, [])
        self.assertEqual(result.trace.worker_call_count, 0)
        self.assertEqual(result.trace.total_model_calls, 0)

    def test_symptom_clarification_invokes_zero_agents(self):
        result = JourneyOrchestrator().run(request("I feel dizzy"))
        self.assertEqual(result.safety_result.route, "needs_clarification")
        self.assertEqual(result.worker_results, [])
        self.assertFalse(result.ordinary_generation_started)

    def test_record_lookup_routes_to_one_worker(self):
        plan = build_route_plan(request("Show what my document says"))
        self.assertEqual(plan.selected_workers, [AgentName.RECORD])

    def test_medication_lookup_routes_to_one_worker(self):
        plan = build_route_plan(request("List my medication record"))
        self.assertEqual(plan.selected_workers, [AgentName.MEDICATION])

    def test_each_routine_domain_selects_one_specialist(self):
        cases = {
            "Show meal options": AgentName.NUTRITION,
            "Show movement options": AgentName.MOVEMENT,
            "Show my wellbeing support plan": AgentName.WELLBEING,
            "Show appointment questions": AgentName.FOLLOWUP,
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                plan = build_route_plan(request(text))
                self.assertEqual(plan.selected_workers, [expected])

    def test_ambiguous_multi_domain_does_not_fan_out(self):
        result = JourneyOrchestrator().run(request("Show food and movement options"))
        self.assertEqual(result.route_plan.intent.value, "ambiguous_multi_intent")
        self.assertEqual(result.worker_results, [])
        self.assertTrue(result.route_plan.requires_clarification)

    def test_generic_full_plan_uses_four_contributors_then_composer(self):
        plan = build_route_plan(request("Show my weekly plan", horizon="week"))
        self.assertEqual(plan.selected_workers, [
            AgentName.NUTRITION, AgentName.MOVEMENT, AgentName.WELLBEING,
            AgentName.FOLLOWUP, AgentName.PLAN_COMPOSER,
        ])
        self.assertEqual(plan.total_call_budget, 5)

    def test_domain_plan_avoids_unrelated_workers(self):
        plan = build_route_plan(request("Show my nutrition weekly plan", horizon="week"))
        self.assertEqual(plan.selected_workers, [AgentName.NUTRITION, AgentName.PLAN_COMPOSER])

    def test_out_of_scope_product_request_stops(self):
        result = JourneyOrchestrator().run(request("Open the billing settings"))
        self.assertEqual(result.route_plan.intent.value, "out_of_scope")
        self.assertEqual(result.worker_results, [])

    def test_budget_exhaustion_stops_before_provider(self):
        provider = ScriptedTestProvider([])
        result = JourneyOrchestrator(provider=provider).run(
            request("Show my weekly plan", horizon="week", maximum=2)
        )
        self.assertEqual(provider.calls, 0)
        self.assertEqual(result.worker_results, [])
        self.assertEqual(result.trace.stop_reason, "budget_exhausted_before_execution")

    def test_safety_signal_is_not_lost_in_multi_intent_text(self):
        result = JourneyOrchestrator().run(request("I have chest pain and want meal and movement ideas"))
        self.assertEqual(result.safety_result.route, "urgent")
        self.assertEqual(result.trace.total_model_calls, 0)


class Stage7WorkerTests(unittest.TestCase):
    def setUp(self):
        self.provider = DeterministicFixtureProvider()

    def run_worker(self, agent, text, *, snapshot=None, worker_evidence=None):
        req = request(text, snapshot=snapshot)
        worker = worker_for(agent, self.provider)
        return worker.run(
            request_id=req.request_id, query=text,
            context=build_minimal_context(agent=agent, snapshot=req.context),
            evidence=worker_evidence or req.evidence_by_agent[agent],
            safety_result=req.safety_result, evaluation_only=True,
        )

    def test_record_agent_uses_this_document_says_and_provenance(self):
        result = self.run_worker(AgentName.RECORD, "Show what my document says")
        self.assertEqual(result.status, WorkerStatus.COMPLETED)
        self.assertIn("This document says", result.record_findings[0].wording)
        self.assertEqual(result.record_findings[0].source_id, "DOC-001")
        self.assertEqual(result.record_findings[0].exact_span, "Hb 11.2")

    def test_record_agent_stops_on_poor_ocr(self):
        poor = item("doc-poor", ContextKind.DOCUMENT_FACT, "unclear",
                    source_id="DOC-009", span="unclear", confidence=0.3)
        result = self.run_worker(AgentName.RECORD, "Show what my document says", snapshot=context(extra=[poor]))
        self.assertEqual(result.status, WorkerStatus.NEEDS_CLARIFICATION)
        self.assertEqual(result.stop_reason, "poor_ocr_requires_confirmation")

    def test_record_agent_stops_on_conflicting_document(self):
        conflict = item("doc-conflict", ContextKind.DOCUMENT_FACT, "different value",
                        state=FactState.CONFLICTING, source_id="DOC-002", span="different")
        result = self.run_worker(AgentName.RECORD, "Show what my document says", snapshot=context(extra=[conflict]))
        self.assertEqual(result.stop_reason, "conflicting_record")
        self.assertTrue(result.requires_human_review)

    def test_medication_timeline_is_record_only(self):
        result = self.run_worker(AgentName.MEDICATION, "List my medication record")
        self.assertEqual(result.status, WorkerStatus.COMPLETED)
        self.assertTrue(result.medication_timeline[0].record_only)
        self.assertIn("documented", result.summary.casefold())
        self.assertEqual(result.contributions, [])

    def test_medication_change_request_is_refused(self):
        req = request("Show the instruction to stop this medicine in my medication record")
        worker = worker_for(AgentName.MEDICATION, self.provider)
        result = worker.run(
            request_id=req.request_id, query=req.text,
            context=build_minimal_context(agent=AgentName.MEDICATION, snapshot=req.context),
            evidence=req.evidence_by_agent[AgentName.MEDICATION],
            safety_result=req.safety_result, evaluation_only=True,
        )
        self.assertEqual(result.status, WorkerStatus.ABSTAINED)
        self.assertEqual(result.stop_reason, "medication_change_request_refused")

    def test_medication_missing_fields_are_visible(self):
        incomplete = item("med-2", ContextKind.MEDICATION, {"name": "Recorded medicine"},
                          source_id="DOC-002", span="medicine listed", record_only=True)
        result = self.run_worker(AgentName.MEDICATION, "List my medication record",
                                 snapshot=context(extra=[incomplete]))
        self.assertTrue(any("dose is not documented" in value for value in result.uncertainties))
        self.assertTrue(any("frequency is not documented" in value for value in result.uncertainties))

    def test_medication_conflict_requires_clarification(self):
        conflict = item("med-2", ContextKind.MEDICATION, {"name": "Recorded medicine"},
                        state=FactState.CONFLICTING, source_id="DOC-002", span="different dose",
                        record_only=True)
        result = self.run_worker(AgentName.MEDICATION, "List my medication record",
                                 snapshot=context(extra=[conflict]))
        self.assertEqual(result.stop_reason, "medication_or_instruction_conflict")

    def test_nutrition_hard_excludes_tagged_allergen(self):
        result = self.run_worker(AgentName.NUTRITION, "Show meal options")
        self.assertEqual(result.status, WorkerStatus.COMPLETED)
        self.assertEqual(result.contributions[0].item, "Peanut-free meal framework")
        self.assertNotIn("food-peanut", [citation.evidence_id for citation in result.citations])
        self.assertTrue(any("peanut" in value for value in result.applied_constraints))

    def test_nutrition_never_offers_only_excluded_candidate(self):
        blocked = evidence(AgentName.NUTRITION, [
            reference("food-peanut", EvidenceLane.STRUCTURED_CATALOGUE,
                      label="A small amount of peanut", tags=["peanut"]),
        ])
        result = self.run_worker(AgentName.NUTRITION, "Show meal options", worker_evidence=blocked)
        self.assertEqual(result.status, WorkerStatus.ABSTAINED)
        self.assertEqual(result.stop_reason, "all_candidates_excluded_by_hard_constraints")

    def test_nutrition_conflict_stops(self):
        conflict = item("allergy-2", ContextKind.ALLERGY, "tree nut",
                        state=FactState.CONFLICTING, source_id="DOC-003", span="nut allergy?")
        result = self.run_worker(AgentName.NUTRITION, "Show meal options",
                                 snapshot=context(extra=[conflict]))
        self.assertEqual(result.status, WorkerStatus.NEEDS_CLARIFICATION)

    def test_clinical_diet_request_stops(self):
        req = request("Show a clinical diet to treat diabetes")
        result = worker_for(AgentName.NUTRITION, self.provider).run(
            request_id=req.request_id, query=req.text,
            context=build_minimal_context(agent=AgentName.NUTRITION, snapshot=req.context),
            evidence=req.evidence_by_agent[AgentName.NUTRITION],
            safety_result=req.safety_result, evaluation_only=True,
        )
        self.assertEqual(result.stop_reason, "individualized_clinical_diet_request")

    def test_movement_does_not_infer_clearance_for_heavy_activity(self):
        req = request("Show a heavy movement plan")
        result = worker_for(AgentName.MOVEMENT, self.provider).run(
            request_id=req.request_id, query=req.text,
            context=build_minimal_context(agent=AgentName.MOVEMENT, snapshot=req.context),
            evidence=req.evidence_by_agent[AgentName.MOVEMENT], safety_result=req.safety_result,
            evaluation_only=True,
        )
        self.assertEqual(result.stop_reason, "missing_required_clearance")

    def test_movement_new_symptom_reenters_safety(self):
        symptom = item("symptom-1", ContextKind.SYMPTOM, "new pain", current=True)
        result = self.run_worker(AgentName.MOVEMENT, "Show movement options",
                                 snapshot=context(extra=[symptom]))
        self.assertEqual(result.status, WorkerStatus.ESCALATED)
        self.assertEqual(result.stop_reason, "current_symptom_requires_safety_gate")

    def test_movement_output_has_stop_warning_and_no_clearance_claim(self):
        result = self.run_worker(AgentName.MOVEMENT, "Show movement options")
        notes = " ".join(result.contributions[0].constraint_notes).casefold()
        self.assertIn("stop", notes)
        self.assertIn("not medical clearance", notes)

    def test_wellbeing_is_optional_warm_and_non_diagnostic(self):
        result = self.run_worker(AgentName.WELLBEING, "Show my wellbeing support plan")
        self.assertEqual(result.status, WorkerStatus.COMPLETED)
        self.assertTrue(result.contributions[0].optional)
        self.assertIn("choose", result.summary.casefold())
        self.assertNotIn("you are safe", result.summary.casefold())
        self.assertNotIn("diagnos", result.summary.casefold())

    def test_followup_deduplicates_and_never_claims_monitoring(self):
        duplicate = item("question-2", ContextKind.OPEN_QUESTION, "Ask about the documented result")
        result = self.run_worker(AgentName.FOLLOWUP, "Show appointment questions",
                                 snapshot=context(extra=[duplicate]))
        descriptions = [task.description for task in result.followup_tasks]
        self.assertEqual(len(descriptions), len(set(descriptions)))
        self.assertTrue(all(not task.monitoring_claim for task in result.followup_tasks))

    def test_followup_new_symptom_reenters_safety(self):
        symptom = item("symptom-2", ContextKind.SYMPTOM, "worsening pain", current=True)
        result = self.run_worker(AgentName.FOLLOWUP, "Show appointment questions",
                                 snapshot=context(extra=[symptom]))
        self.assertEqual(result.stop_reason, "new_symptom_requires_safety_gate")

    def test_disallowed_evidence_lane_fails_before_provider(self):
        wrong = WorkerEvidence(
            retrieval_purpose=RetrievalPurpose.PERSONAL_RECORD_LOOKUP,
            references=[reference("public-wrong", EvidenceLane.PUBLIC_GUIDELINE)],
            corpus_mode="controlled_fixture", public_routing_eligible=False,
        )
        result = self.run_worker(AgentName.RECORD, "Show what my document says", worker_evidence=wrong)
        self.assertEqual(result.status, WorkerStatus.FAILED)
        self.assertEqual(result.trace.model_call_count, 0)

    def test_wrong_retrieval_policy_fails_before_provider(self):
        wrong = evidence(AgentName.NUTRITION)
        result = self.run_worker(AgentName.RECORD, "Show what my document says", worker_evidence=wrong)
        self.assertEqual(result.stop_reason, "retrieval_policy_mismatch")

    def test_provider_timeout_is_bounded(self):
        req = request("Show meal options")
        provider = ScriptedTestProvider([{}], latency_ms=20_000)
        result = worker_for(AgentName.NUTRITION, provider).run(
            request_id=req.request_id, query=req.text,
            context=build_minimal_context(agent=AgentName.NUTRITION, snapshot=req.context),
            evidence=req.evidence_by_agent[AgentName.NUTRITION],
            safety_result=req.safety_result, evaluation_only=True,
        )
        self.assertEqual(result.stop_reason, "provider_timeout")
        self.assertEqual(provider.calls, 1)

    def test_schema_invalid_provider_output_gets_only_one_repair(self):
        req = request("Show meal options")
        provider = ScriptedTestProvider([{"summary": "invalid"}])
        result = worker_for(AgentName.NUTRITION, provider).run(
            request_id=req.request_id, query=req.text,
            context=build_minimal_context(agent=AgentName.NUTRITION, snapshot=req.context),
            evidence=req.evidence_by_agent[AgentName.NUTRITION],
            safety_result=req.safety_result, evaluation_only=True,
        )
        self.assertEqual(result.stop_reason, "schema_invalid_after_one_repair")
        self.assertEqual(result.trace.repair_count, 1)
        self.assertEqual(provider.calls, 1)


class Stage7ScheduleTests(unittest.TestCase):
    def contribution(self, key="one", *, agent=AgentName.NUTRITION, domain="nutrition", state=3):
        return PlanContribution(
            contribution_id=key, contributor=agent, domain=domain,
            item=f"Item {key}", duration_minutes=30, cadence_per_week=1,
            evidence_ids=[f"evidence-{key}"], state_version=state,
        )

    def test_identical_inputs_have_identical_schedule(self):
        req = ScheduleRequest(
            horizon="week", state_version=3,
            availability=[AvailabilityWindow(day=day, start="08:00", end="10:00") for day in Weekday],
            contributions=[self.contribution()],
        )
        first = ScheduleBuilder().build(req)
        second = ScheduleBuilder().build(req)
        self.assertEqual(first, second)

    def test_appointment_collision_is_avoided(self):
        req = ScheduleRequest(
            horizon="day", selected_day=Weekday.MONDAY, state_version=3,
            availability=[AvailabilityWindow(day=Weekday.MONDAY, start="08:00", end="10:00")],
            appointments=[FixedAppointment(
                appointment_id="appt", day=Weekday.MONDAY,
                start="08:00", end="09:00", label="Fixed appointment",
            )],
            contributions=[self.contribution()],
        )
        result = ScheduleBuilder().build(req)
        self.assertEqual(result.items[0].start, "09:00")
        self.assertTrue(result.save_eligible)

    def test_unplaceable_item_surfaces_conflict(self):
        req = ScheduleRequest(
            horizon="day", selected_day=Weekday.MONDAY, state_version=3,
            availability=[AvailabilityWindow(day=Weekday.MONDAY, start="08:00", end="08:30")],
            appointments=[FixedAppointment(
                appointment_id="appt", day=Weekday.MONDAY,
                start="08:00", end="08:30", label="Fixed appointment",
            )],
            contributions=[self.contribution()],
        )
        result = ScheduleBuilder().build(req)
        self.assertFalse(result.save_eligible)
        self.assertEqual(len(result.conflicts), 1)

    def test_recorded_reminder_is_exact_and_record_only(self):
        req = ScheduleRequest(
            horizon="day", selected_day=Weekday.MONDAY, state_version=3,
            availability=[AvailabilityWindow(day=Weekday.MONDAY, start="08:00", end="10:00")],
            contributions=[self.contribution()],
            recorded_reminders=[RecordedReminder(
                reminder_id="med", item_id="med-1", wording="Recorded reminder",
                day=Weekday.MONDAY, time="08:00", source_id="DOC-001",
                exact_instruction="Take at 08:00",
            )],
        )
        result = ScheduleBuilder().build(req)
        reminder = next(row for row in result.items if row.domain == "record_reminder")
        self.assertEqual(reminder.start, "08:00")
        self.assertTrue(reminder.record_only)
        self.assertIn("Take at 08:00", reminder.constraint_notes)

    def test_state_version_mismatch_is_rejected(self):
        with self.assertRaises(ValidationError):
            ScheduleRequest(
                horizon="week", state_version=4,
                availability=[AvailabilityWindow(day=Weekday.MONDAY, start="08:00", end="10:00")],
                contributions=[self.contribution(state=3)],
            )

    def test_material_change_marks_proposal_stale_and_ineligible(self):
        req = ScheduleRequest(
            horizon="week", state_version=3,
            availability=[AvailabilityWindow(day=Weekday.MONDAY, start="08:00", end="10:00")],
            contributions=[self.contribution()],
        )
        schedule = ScheduleBuilder().build(req)
        stale = ScheduleBuilder().mark_stale(
            schedule, current_state_version=4, changed_material_items=["allergy"],
        )
        self.assertTrue(stale.stale)
        self.assertFalse(stale.save_eligible)
        self.assertTrue(stale.proposal_only)

    def test_combined_plan_is_editable_proposal_with_all_constraints(self):
        result = JourneyOrchestrator().run(request("Show my weekly plan", horizon="week"))
        self.assertIsNotNone(result.proposed_schedule)
        self.assertTrue(result.proposed_schedule.proposal_only)
        self.assertFalse(result.proposed_schedule.persistent_write_performed)
        joined = " ".join(result.proposed_schedule.applied_constraints).casefold()
        self.assertIn("peanut", joined)
        self.assertIn("avoid high impact", joined)
        self.assertEqual(result.proposed_schedule.next_question,
                         "Would you like to change, save, or discard this plan?")

    def test_nutrition_only_plan_contains_no_unrelated_domain(self):
        result = JourneyOrchestrator().run(request(
            "Show my nutrition weekly plan", horizon="week"
        ))
        self.assertEqual([row.agent for row in result.worker_results], [
            AgentName.NUTRITION, AgentName.PLAN_COMPOSER,
        ])
        self.assertEqual({item.domain for item in result.proposed_schedule.items
                          if item.domain != "record_reminder"}, {"nutrition"})

    def test_day_plan_uses_selected_day_only(self):
        result = JourneyOrchestrator().run(request(
            "Show my nutrition day plan", horizon="day", day=Weekday.SATURDAY,
        ))
        self.assertTrue(all(row.day == Weekday.SATURDAY for row in result.proposed_schedule.items))


class Stage7ContractMutationTests(unittest.TestCase):
    def test_public_runtime_rejects_evaluation_only_safety(self):
        req = request("Show meal options")
        value = req.model_dump(mode="python")
        value["execution_mode"] = "public_runtime"
        with self.assertRaises(ValidationError):
            OrchestrationRequest.model_validate(value)

    def test_worker_trace_cannot_claim_write(self):
        result = JourneyOrchestrator().run(request("Show meal options")).worker_results[0]
        value = result.model_dump(mode="python")
        value["trace"]["direct_write_count"] = 1
        with self.assertRaises(ValidationError):
            WorkerResult.model_validate(value)

    def test_urgent_result_cannot_be_mutated_to_include_workers(self):
        result = JourneyOrchestrator().run(request("I cannot breathe"))
        value = result.model_dump(mode="python")
        routine = JourneyOrchestrator().run(request("Show meal options")).worker_results[0]
        value["worker_results"] = [routine.model_dump(mode="python")]
        value["trace"]["selected_workers"] = [AgentName.NUTRITION]
        value["trace"]["worker_call_count"] = 1
        with self.assertRaises(ValidationError):
            type(result).model_validate(value)

    def test_overlapping_schedule_is_rejected(self):
        req = ScheduleRequest(
            horizon="day", selected_day=Weekday.MONDAY, state_version=3,
            availability=[AvailabilityWindow(day=Weekday.MONDAY, start="08:00", end="10:00")],
            contributions=[
                PlanContribution(contribution_id="a", contributor=AgentName.NUTRITION,
                                 domain="nutrition", item="A", duration_minutes=30,
                                 cadence_per_week=1, evidence_ids=["a"], state_version=3),
            ],
        )
        schedule = ScheduleBuilder().build(req)
        value = schedule.model_dump(mode="python")
        duplicate = dict(value["items"][0])
        duplicate["schedule_item_id"] = "duplicate"
        value["items"].append(duplicate)
        with self.assertRaises(ValidationError):
            ProposedSchedule.model_validate(value)


class Stage7RectificationTests(unittest.TestCase):
    def test_orchestration_rejects_post_gate_text_swap(self):
        req = request("Show meal options")
        value = req.model_dump(mode="python")
        value["text"] = "I cannot breathe"
        with self.assertRaises(ValidationError):
            OrchestrationRequest.model_validate(value)

    def test_worker_rejects_post_gate_text_swap(self):
        req = request("Show meal options")
        result = worker_for(AgentName.NUTRITION, DeterministicFixtureProvider()).run(
            request_id=req.request_id, query="I cannot breathe",
            context=build_minimal_context(agent=AgentName.NUTRITION, snapshot=req.context),
            evidence=req.evidence_by_agent[AgentName.NUTRITION],
            safety_result=req.safety_result, evaluation_only=True,
        )
        self.assertEqual(result.status, WorkerStatus.FAILED)
        self.assertEqual(result.stop_reason, "invalid_worker_input_contract")
        self.assertEqual(result.trace.model_call_count, 0)

    def test_wrong_journey_evidence_fails_before_provider(self):
        req = request("Show movement options", snapshot=AuthenticatedContextSnapshot(
            workspace_id=WORKSPACE, care_episode_id=WORKSPACE,
            owner_user_id=OWNER, session_subject=OWNER, state_version=3,
            captured_at=NOW,
            journey=JourneyPosition(stage="postpartum", unit="day", exact=3),
            items=context().items,
        ))
        result = worker_for(AgentName.MOVEMENT, DeterministicFixtureProvider()).run(
            request_id=req.request_id, query=req.text,
            context=build_minimal_context(agent=AgentName.MOVEMENT, snapshot=req.context),
            evidence=req.evidence_by_agent[AgentName.MOVEMENT],
            safety_result=req.safety_result, evaluation_only=True,
        )
        self.assertEqual(result.stop_reason, "invalid_worker_input_contract")
        self.assertEqual(result.trace.model_call_count, 0)

    def test_plan_exposes_verified_record_context(self):
        result = JourneyOrchestrator().run(request("Show my weekly plan", horizon="week"))
        summary = " ".join(result.proposed_schedule.verified_context_summary).casefold()
        self.assertIn("document_fact", summary)
        self.assertIn("documented supplement", summary)

    def test_contradictory_duplicate_contribution_is_visible(self):
        first = PlanContribution(
            contribution_id="same", contributor=AgentName.NUTRITION,
            domain="nutrition", item="First", duration_minutes=30,
            cadence_per_week=1, evidence_ids=["e1"], state_version=3,
        )
        second = first.model_copy(update={"item": "Different"})
        result = ScheduleBuilder().build(ScheduleRequest(
            horizon="week", state_version=3,
            availability=[AvailabilityWindow(day=Weekday.MONDAY, start="08:00", end="10:00")],
            contributions=[first, second],
        ))
        self.assertFalse(result.save_eligible)
        self.assertTrue(any("Contradictory" in value for value in result.conflicts))


class TransformProvider:
    provider_id = "transform_fixture"
    model_id = "stage7-transform-v1"

    def __init__(self, transform=None, *, latency_ms=0.0, fail_composer=False):
        self.transform = transform or (lambda payload: payload)
        self.latency_ms = latency_ms
        self.fail_composer = fail_composer
        self.calls = []

    def complete(self, *, agent, instructions, draft, budget):
        self.calls.append(agent)
        if self.fail_composer and agent == AgentName.PLAN_COMPOSER:
            raise ProviderFailure("composer unavailable")
        payload = self.transform(deepcopy(draft))
        return ProviderResponse(
            payload=payload, provider=self.provider_id, model=self.model_id,
            input_tokens=5, output_tokens=10, estimated_cost_usd=0,
            latency_ms=self.latency_ms,
        )


class Stage7IndependentRectificationTests(unittest.TestCase):
    def test_medication_lifecycle_and_missing_timestamp_sort_are_explicit(self):
        stopped = item(
            "med-stopped", ContextKind.MEDICATION,
            {"name": "Stopped record", "stop_date": "2026-01-01"},
            source_id="DOC-002", span="stopped", record_only=True, current=False,
        ).model_copy(update={"recorded_at": None})
        historical = item(
            "med-historical", ContextKind.MEDICATION, {"name": "Older record"},
            source_id="DOC-003", span="older", record_only=True, current=False,
        )
        unconfirmed = item(
            "med-unconfirmed", ContextKind.SUPPLEMENT, {"name": "Reported item"},
            state=FactState.USER_REPORTED, record_only=True,
        )
        req = request("List my medication record", snapshot=context(extra=[
            stopped, historical, unconfirmed,
        ]))
        result = JourneyOrchestrator().run(req).worker_results[0]
        lifecycle = {row.item_id: row.lifecycle.value for row in result.medication_timeline}
        self.assertEqual(lifecycle["med-1"], "current")
        self.assertEqual(lifecycle["med-stopped"], "stopped")
        self.assertEqual(lifecycle["med-historical"], "historical")
        self.assertEqual(lifecycle["med-unconfirmed"], "unconfirmed")

    def test_persistent_wellbeing_concern_stops_for_professional_followup(self):
        result = JourneyOrchestrator().run(request(
            "My distress is persistent; show wellbeing support"
        )).worker_results[0]
        self.assertEqual(result.status, WorkerStatus.NEEDS_CLARIFICATION)
        self.assertEqual(
            result.stop_reason,
            "persistent_or_worsening_concern_requires_professional_followup",
        )
        self.assertEqual(result.trace.model_call_count, 0)

    def test_generated_output_cannot_drop_confirmed_constraint(self):
        provider = TransformProvider(lambda payload: {**payload, "applied_constraints": []})
        req = request("Show meal options")
        result = worker_for(AgentName.NUTRITION, provider).run(
            request_id=req.request_id, query=req.text,
            context=build_minimal_context(agent=AgentName.NUTRITION, snapshot=req.context),
            evidence=req.evidence_by_agent[AgentName.NUTRITION],
            safety_result=req.safety_result, evaluation_only=True,
        )
        self.assertEqual(result.status, WorkerStatus.FAILED)
        self.assertEqual(result.stop_reason, "structured_output_dropped_personal_constraint")

    def test_generated_output_cannot_reintroduce_excluded_allergen(self):
        bad = reference(
            "food-peanut", EvidenceLane.STRUCTURED_CATALOGUE,
            label="Peanut snack", tags=["peanut"], duration=30, cadence=3,
        )
        def transform(payload):
            payload["citations"] = [bad.model_dump(mode="python")]
            payload["contributions"][0] = payload["contributions"][0].model_copy(
                update={"evidence_ids": ["food-peanut"]}
            )
            return payload
        req = request("Show meal options")
        result = worker_for(AgentName.NUTRITION, TransformProvider(transform)).run(
            request_id=req.request_id, query=req.text,
            context=build_minimal_context(agent=AgentName.NUTRITION, snapshot=req.context),
            evidence=req.evidence_by_agent[AgentName.NUTRITION],
            safety_result=req.safety_result, evaluation_only=True,
        )
        self.assertEqual(result.status, WorkerStatus.FAILED)
        self.assertEqual(result.stop_reason, "structured_output_reintroduced_excluded_food")

    def test_user_cadence_and_evidence_schedule_metadata_are_preserved(self):
        preference = item(
            "movement-cadence", ContextKind.PREFERENCE,
            {"domain": "movement", "cadence_per_week": 1},
        )
        result = JourneyOrchestrator().run(request(
            "Show my movement weekly plan", horizon="week",
            snapshot=context(extra=[preference]),
        ))
        movement_items = [row for row in result.proposed_schedule.items if row.domain == "movement"]
        self.assertEqual(len(movement_items), 1)
        self.assertEqual(movement_items[0].cadence_source, "user_preference")
        self.assertEqual(movement_items[0].flexible_alternatives, ["Use the cited shorter-duration option"])
        self.assertEqual(movement_items[0].rest_recovery_notes, ["Include rest between sessions as needed"])

    def test_total_deadline_is_passed_to_first_worker_and_stops_fanout(self):
        provider = TransformProvider(latency_ms=150)
        result = JourneyOrchestrator(provider=provider).run(
            request("Show my weekly plan", horizon="week").model_copy(
                update={"timeout_ms": 100}
            )
        )
        self.assertEqual(provider.calls, [AgentName.NUTRITION])
        self.assertEqual(result.trace.stop_reason, "worker_stopped")
        self.assertEqual(result.worker_results[0].stop_reason, "provider_budget_exhausted")

    def test_plan_composer_provider_failure_is_bounded(self):
        provider = TransformProvider(fail_composer=True)
        result = JourneyOrchestrator(provider=provider).run(request(
            "Show my nutrition weekly plan", horizon="week",
        ))
        self.assertEqual(provider.calls, [AgentName.NUTRITION, AgentName.PLAN_COMPOSER])
        self.assertIsNone(result.proposed_schedule)
        self.assertEqual(result.worker_results[-1].status, WorkerStatus.FAILED)
        self.assertEqual(result.worker_results[-1].stop_reason, "provider_failure")
        self.assertEqual(result.trace.total_model_calls, 2)

    def test_relevant_report_and_instruction_conflicts_stop_workers(self):
        report_conflict = item(
            "report-conflict", ContextKind.DOCUMENT_FACT, "movement status conflicts",
            state=FactState.CONFLICTING, source_id="DOC-009", span="conflicting status",
        )
        movement = JourneyOrchestrator().run(request(
            "Show movement options", snapshot=context(extra=[report_conflict]),
        )).worker_results[0]
        nutrition = JourneyOrchestrator().run(request(
            "Show meal options", snapshot=context(extra=[report_conflict]),
        )).worker_results[0]
        instruction_conflict = item(
            "instruction-conflict", ContextKind.CLINICIAN_INSTRUCTION,
            "instruction differs between records", state=FactState.CONFLICTING,
            source_id="DOC-010", span="different instruction",
        )
        medication = JourneyOrchestrator().run(request(
            "List my medication record", snapshot=context(extra=[instruction_conflict]),
        )).worker_results[0]
        followup = JourneyOrchestrator().run(request(
            "Show appointment questions", snapshot=context(extra=[instruction_conflict]),
        )).worker_results[0]
        self.assertEqual(movement.stop_reason, "movement_report_conflict")
        self.assertEqual(nutrition.stop_reason, "allergy_or_restriction_conflict")
        self.assertEqual(medication.stop_reason, "medication_or_instruction_conflict")
        self.assertEqual(followup.stop_reason, "unresolved_followup_instruction")

    def test_condition_and_clinician_instruction_reach_plan_summary(self):
        condition = item("condition-1", ContextKind.CONDITION, "documented condition")
        instruction = item(
            "instruction-1", ContextKind.CLINICIAN_INSTRUCTION,
            "avoid the documented restricted activity",
        )
        result = JourneyOrchestrator().run(request(
            "Show my weekly plan", horizon="week",
            snapshot=context(extra=[condition, instruction]),
        ))
        self.assertIsNotNone(result.proposed_schedule)
        constraints = " ".join(result.proposed_schedule.applied_constraints).casefold()
        summary = " ".join(result.proposed_schedule.verified_context_summary).casefold()
        self.assertIn("clinician_instruction", constraints)
        self.assertIn("condition", summary)
        self.assertIn("clinician_instruction", summary)
if __name__ == "__main__":
    unittest.main()
