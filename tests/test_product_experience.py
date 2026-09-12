from __future__ import annotations

import unittest
from pydantic import ValidationError

from app.schemas.product_experience import (
    ChatDisplayResult, EvidenceDrawerItem, PlanDisplayState, ProductMode, ViewState,
    WeeklyHomeView,
)
from app.services.product_experience import (
    DEMO_WORKSPACE, authentic_failed_trace, demo_documents, demo_story_results,
    demo_weekly_home, load_evaluator_metrics, load_runtime_config,
    personal_empty_home, reset_demo_state_keys, run_compass, simulated_review,
)


class Stage9ProductExperienceTests(unittest.TestCase):
    def test_runtime_configuration_fails_personal_mode_clearly(self):
        config = load_runtime_config({})
        self.assertFalse(config.personal_mode_available)
        self.assertEqual(config.missing_fields, [
            "NESTLINE_SUPABASE_URL", "NESTLINE_SUPABASE_PUBLISHABLE_KEY"
        ])
        self.assertTrue(config.demo_mode_available)
        self.assertFalse(config.public_health_routing_available)

    def test_placeholder_configuration_is_not_accepted(self):
        config = load_runtime_config({
            "NESTLINE_SUPABASE_URL": "https://YOUR_PROJECT_REF.supabase.co",
            "NESTLINE_SUPABASE_PUBLISHABLE_KEY": "YOUR_PUBLISHABLE_KEY",
        })
        self.assertFalse(config.personal_mode_available)

    def test_personal_mode_begins_empty(self):
        home = personal_empty_home()
        self.assertEqual(home.mode, ProductMode.PERSONAL)
        self.assertEqual(home.state, ViewState.EMPTY)
        self.assertIsNone(home.journey)
        self.assertEqual(home.confirmed_context, [])

    def test_empty_personal_mode_rejects_demo_context(self):
        with self.assertRaises(ValidationError):
            WeeklyHomeView(
                mode=ProductMode.PERSONAL, fictional=False,
                journey=demo_weekly_home().journey,
                hero_title="empty", hero_body="empty", hero_alt="empty",
                confirmed_context=["peanut"], sections=[],
                plan_state=PlanDisplayState.NONE, state=ViewState.EMPTY,
            )

    def test_demo_home_is_exact_and_does_not_claim_unreleased_size(self):
        home = demo_weekly_home()
        self.assertTrue(home.journey.exact)
        self.assertEqual(home.journey.position_start, 24)
        self.assertEqual(home.agent_fanout_count, 0)
        self.assertIn("No public weekly-development profile", home.hero_body)
        self.assertNotIn("cm", home.hero_body)
        self.assertTrue(home.fictional)

    def test_approximate_header_does_not_present_exact_week(self):
        home = demo_weekly_home(approximate=True)
        self.assertFalse(home.journey.exact)
        self.assertEqual((home.journey.position_start, home.journey.position_end), (23, 25))
        self.assertIn("approximate", home.journey.display_label)

    def test_home_orders_required_sections(self):
        headings = [section.heading for section in demo_weekly_home().sections]
        self.assertEqual(headings[:4], [
            "What may be changing now", "Nutrition focus", "Movement focus", "Well-being focus"
        ])
        for required in ["Consider", "Avoid", "Ask first", "Reported symptoms"]:
            self.assertIn(required, headings)

    def test_nutrition_reaches_stage8_display_gate(self):
        execution = run_compass("Show meal options")
        self.assertEqual(execution.display.route, "validated")
        self.assertTrue(execution.display.validation_display_allowed)
        self.assertIn("Public guidance says", execution.display.provenance_sections)
        self.assertIsNotNone(execution.stage8)
        self.assertTrue(execution.stage8.validation_report.display_allowed)

    def test_record_origin_stays_visibly_separate(self):
        execution = run_compass("Show what my document says")
        self.assertEqual(execution.display.route, "validated")
        self.assertIn("Your uploaded record says", execution.display.provenance_sections)
        self.assertTrue(all(item.source_type == "personal_document_fixture" for item in execution.display.citations))
        self.assertTrue(all(item.workspace_id == DEMO_WORKSPACE for item in execution.display.citations))

    def test_medication_stays_record_only(self):
        execution = run_compass("List my medication record")
        self.assertEqual(execution.display.route, "validated")
        worker = execution.stage7.worker_results[0]
        self.assertTrue(worker.medication_timeline)
        self.assertTrue(all(item.record_only for item in worker.medication_timeline))
        self.assertFalse(worker.contributions)

    def test_movement_preserves_restriction(self):
        execution = run_compass("Show movement options")
        self.assertEqual(execution.display.route, "validated")
        self.assertTrue(any("high impact" in item for item in execution.display.applied_constraints))

    def test_holistic_plan_is_validated_and_proposal_only(self):
        execution = run_compass("Show my weekly plan", horizon="week")
        schedule = execution.stage7.proposed_schedule
        self.assertEqual(execution.display.route, "validated")
        self.assertIsNotNone(schedule)
        self.assertTrue(schedule.proposal_only)
        self.assertFalse(schedule.persistent_write_performed)
        self.assertTrue(any(item.record_only for item in schedule.items))
        self.assertTrue(any("peanut" in value for value in schedule.applied_constraints))

    def test_single_domain_plan_does_not_invoke_unrelated_specialists(self):
        execution = run_compass("Show my nutrition weekly plan", horizon="week")
        workers = [item.value for item in execution.stage7.route_plan.selected_workers]
        self.assertEqual(workers, ["nutrition_agent", "plan_composer_agent"])

    def test_urgent_bypasses_stage7_and_stage8_generation(self):
        execution = run_compass("I cannot breathe. Show my weekly plan.", horizon="week")
        self.assertEqual(execution.display.route, "urgent")
        self.assertEqual(execution.display.ordinary_generation_calls, 0)
        self.assertFalse(execution.stage7.worker_results)
        self.assertIsNone(execution.stage8)

    def test_ambiguous_symptom_clarifies_before_generation(self):
        execution = run_compass("I feel dizzy")
        self.assertEqual(execution.display.route, "clarification")
        self.assertEqual(execution.display.ordinary_generation_calls, 0)
        self.assertTrue(execution.display.summary)

    def test_unsupported_intent_is_honest(self):
        execution = run_compass("Open the billing settings")
        self.assertEqual(execution.display.route, "unsupported")
        self.assertFalse(execution.display.validation_display_allowed)

    def test_evidence_scope_contract_rejects_public_private_mixing(self):
        common = {
            "evidence_id": "e1", "source_id": "s1", "source_title": "fixture",
            "publisher": "fixture", "review_status": "controlled",
            "current_status": "current", "locator": "page 1",
            "supporting_passage": "fictional exact span", "supports_claim": True,
        }
        with self.assertRaises(ValidationError):
            EvidenceDrawerItem(
                **common, source_type="personal_document_fixture",
                workspace_id=None,
            )
        with self.assertRaises(ValidationError):
            EvidenceDrawerItem(
                **common, source_type="public_fixture",
                workspace_id=DEMO_WORKSPACE,
            )
    def test_contradictory_safety_display_is_rejected(self):
        with self.assertRaises(ValidationError):
            ChatDisplayResult(
                request_id="r", route="urgent", title="urgent", summary="fixed",
                ordinary_generation_calls=1, validation_display_allowed=True,
                fixture_only=True, state=ViewState.BLOCKED,
            )

    def test_document_states_and_recovery_are_complete(self):
        documents = demo_documents()
        states = {item.status for item in documents}
        self.assertTrue({
            "ready", "low_confidence", "conflict", "locked", "corrupt", "unsupported", "wrong_person"
        } <= states)
        self.assertTrue(all(item.fictional and item.recovery for item in documents))
        self.assertTrue(any(field.record_only for doc in documents for field in doc.fields))

    def test_untrusted_document_text_is_plain_typed_data(self):
        documents = demo_documents()
        self.assertFalse(any("<script" in field.exact_span.casefold() for doc in documents for field in doc.fields))

    def test_simulated_review_never_claims_persistence_or_urgent_delay(self):
        for status in ["offered", "consented", "queued", "responded", "declined", "unavailable", "timed_out"]:
            view = simulated_review(status)
            self.assertEqual(view.label, "Simulated review")
            self.assertFalse(view.persistence_available)
            self.assertFalse(view.can_delay_urgent_route)

    def test_evaluator_metrics_are_read_from_generated_artifacts(self):
        metrics = load_evaluator_metrics()
        self.assertEqual([item.stage for item in metrics], ["Stage 5", "Stage 6", "Stage 7", "Stage 8"])
        self.assertTrue(all(item.passed == item.total for item in metrics))
        self.assertTrue(all(not item.live_provider_run for item in metrics))

    def test_authentic_failed_trace_is_not_hidden(self):
        trace = authentic_failed_trace()
        self.assertEqual(trace["first_pass"]["passed"], 55)
        self.assertEqual(trace["first_pass"]["total"], 62)
        self.assertIn("finding", trace["finding"])

    def test_demo_reset_cannot_clear_personal_keys(self):
        state = {
            "stage9_demo_chat_history": [1],
            "stage9_demo_plan_execution": "x",
            "auth_session": "personal",
            "workspace_id": "personal-workspace",
        }
        reset_demo_state_keys(state)
        self.assertNotIn("stage9_demo_chat_history", state)
        self.assertEqual(state["auth_session"], "personal")
        self.assertEqual(state["workspace_id"], "personal-workspace")

    def test_three_demo_stories_pass_three_reset_runs(self):
        outcomes = demo_story_results()
        self.assertEqual(len(outcomes), 9)
        self.assertTrue(all(item["passed"] for item in outcomes))
        urgent = [item for item in outcomes if item["story"] == "urgent-bypass"]
        self.assertTrue(all(item["ordinary_generation_calls"] == 0 for item in urgent))
        self.assertTrue(all(item["stage10_persistence"] == "unavailable" for item in outcomes))


if __name__ == "__main__":
    unittest.main()
