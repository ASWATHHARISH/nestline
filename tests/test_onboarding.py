"""Onboarding confirmation, safety handoff, and idempotency tests."""

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import unittest
from uuid import uuid4

from pydantic import ValidationError

from app.schemas.foundation import SafetySpec
from app.schemas.onboarding import (
    AppointmentInput,
    ManualWeekDayTiming,
    OnboardingCommitResult,
    OnboardingDetails,
    ReportedFactInput,
    SymptomInput,
)
from app.schemas.storage import JourneyState
from app.services.journey import FixedClock
from app.services.onboarding import (
    OnboardingError,
    build_onboarding_payload,
    commit_onboarding,
    prepare_onboarding,
)


ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 9, 11, 12, 0, tzinfo=timezone.utc)
TODAY = NOW.date()


class FakeGateway:
    def __init__(self):
        self.payloads = []
        self.result = OnboardingCommitResult(
            journey_state_id=uuid4(),
            version=1,
            fact_ids=[uuid4()],
            symptom_event_ids=[uuid4()],
            appointment_ids=[uuid4()],
        )

    def fetch_current_journey_state(self, workspace_id):
        return None

    def complete_onboarding(self, payload):
        self.payloads.append(payload)
        return self.result


def current_state(**changes) -> JourneyState:
    values = {
        "id": uuid4(), "workspace_id": uuid4(), "stage": "pregnancy",
        "timing_source": "manual_week_day", "gestational_week": 24,
        "gestational_day": 2, "postpartum_week": None, "postpartum_day": None,
        "estimated_due_date": None, "delivery_date": None,
        "approximate_month_min": None, "approximate_month_max": None,
        "user_confirmed": True, "has_dating_conflict": False, "is_current": True,
        "version": 3, "derived_from_fact_ids": [], "effective_date": TODAY,
        "calculation_date": TODAY, "confirmed_at": NOW,
        "confirmed_by_user_id": uuid4(), "created_at": NOW, "updated_at": NOW,
    }
    values.update(changes)
    return JourneyState(**values)


class OnboardingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = SafetySpec.model_validate_json(
            (ROOT / "data/safety/rule_spec.yaml").read_text(encoding="utf-8")
        )
        cls.clock = FixedClock(NOW)

    def details(self):
        return OnboardingDetails(
            facts=[
                ReportedFactInput(category="allergy", label="Peanut allergy"),
                ReportedFactInput(category="movement_restriction", label="Avoid lifting"),
            ],
            symptoms=[SymptomInput(
                description="I have difficulty breathing",
                reported_at=NOW - timedelta(minutes=5),
            )],
            appointments=[AppointmentInput(
                scheduled_for=NOW + timedelta(days=10),
                appointment_type="Routine follow-up",
                location="Fictional clinic",
            )],
        )

    def test_draft_safety_rules_escalate_match_and_are_labelled_evaluation_only(self):
        draft = prepare_onboarding(
            ManualWeekDayTiming(
                effective_date=TODAY, gestational_week=24, gestational_day=2,
            ),
            self.details(), self.spec, clock=self.clock,
        )
        symptom = draft.prepared_symptoms[0]
        self.assertEqual(symptom.safety_route, "urgent")
        self.assertIn("S-BREATHING", symptom.matched_rule_ids)
        self.assertTrue(symptom.safety_evaluation_only)
        self.assertEqual(symptom.safety_spec_version, self.spec.version)

    def test_unmatched_draft_symptom_uses_canonical_clarification_route(self):
        details = OnboardingDetails(symptoms=[SymptomInput(
            description="A new symptom I cannot categorise",
            reported_at=NOW,
        )])
        draft = prepare_onboarding(
            ManualWeekDayTiming(effective_date=TODAY, gestational_week=24),
            details, self.spec, clock=self.clock,
        )
        self.assertEqual(draft.prepared_symptoms[0].safety_route, "needs_clarification")
        self.assertTrue(draft.prepared_symptoms[0].safety_evaluation_only)
        payload = build_onboarding_payload(uuid4(), "stage6-legacy-route-boundary", draft)
        self.assertEqual(payload["requested_symptoms"][0]["safety_route"], "clarify")

    def test_future_symptom_and_past_next_appointment_are_rejected(self):
        with self.assertRaisesRegex(OnboardingError, "symptom time"):
            prepare_onboarding(
                ManualWeekDayTiming(effective_date=TODAY, gestational_week=24),
                OnboardingDetails(symptoms=[SymptomInput(
                    description="Synthetic symptom", reported_at=NOW + timedelta(seconds=1),
                )]), self.spec, clock=self.clock,
            )
        with self.assertRaisesRegex(OnboardingError, "next appointment"):
            prepare_onboarding(
                ManualWeekDayTiming(effective_date=TODAY, gestational_week=24),
                OnboardingDetails(appointments=[AppointmentInput(
                    scheduled_for=NOW - timedelta(seconds=1),
                    appointment_type="Old appointment",
                )]), self.spec, clock=self.clock,
            )

    def test_duplicate_reported_facts_are_rejected(self):
        with self.assertRaises(ValidationError):
            OnboardingDetails(facts=[
                ReportedFactInput(category="allergy", label="Peanut"),
                ReportedFactInput(category="allergy", label="  PEANUT  "),
            ])

    def test_commit_requires_confirmation(self):
        gateway = FakeGateway()
        draft = prepare_onboarding(
            ManualWeekDayTiming(effective_date=TODAY, gestational_week=24),
            self.details(), self.spec, clock=self.clock,
        )
        with self.assertRaisesRegex(OnboardingError, "explicit user confirmation"):
            commit_onboarding(
                gateway, uuid4(), "stage3-submission-0001", draft,
                user_confirmed=False,
            )
        self.assertEqual(gateway.payloads, [])

    def test_conflicting_timing_requires_explicit_choice(self):
        gateway = FakeGateway()
        draft = prepare_onboarding(
            ManualWeekDayTiming(effective_date=TODAY, gestational_week=25, gestational_day=2),
            OnboardingDetails(), self.spec, current_state=current_state(), clock=self.clock,
        )
        self.assertTrue(draft.conflict.has_conflict)
        with self.assertRaisesRegex(OnboardingError, "conflicting timing"):
            commit_onboarding(
                gateway, draft.conflict.current_state_id,
                "stage3-submission-0002", draft, user_confirmed=True,
            )
        result = commit_onboarding(
            gateway, draft.conflict.current_state_id,
            "stage3-submission-0002", draft, user_confirmed=True,
            accept_conflicting_timing=True,
        )
        self.assertEqual(result, gateway.result)
        self.assertTrue(gateway.payloads[0]["requested_has_dating_conflict"])

    def test_episode_regression_cannot_be_committed(self):
        gateway = FakeGateway()
        state = current_state(
            stage="postpartum", timing_source="postpartum_week",
            gestational_week=None, gestational_day=None,
            postpartum_week=2, postpartum_day=0,
        )
        draft = prepare_onboarding(
            ManualWeekDayTiming(effective_date=TODAY, gestational_week=8),
            OnboardingDetails(), self.spec, current_state=state, clock=self.clock,
        )
        self.assertTrue(draft.conflict.commit_blocked)
        with self.assertRaisesRegex(OnboardingError, "care episode backwards"):
            commit_onboarding(
                gateway, state.workspace_id, "stage3-submission-regression",
                draft, user_confirmed=True, accept_conflicting_timing=True,
            )
        self.assertEqual(gateway.payloads, [])

    def test_payload_preserves_source_timing_and_maps_optional_details(self):
        workspace_id = uuid4()
        draft = prepare_onboarding(
            ManualWeekDayTiming(
                effective_date=TODAY - timedelta(days=9),
                gestational_week=24,
                gestational_day=2,
            ),
            self.details(), self.spec, clock=self.clock,
        )
        payload = build_onboarding_payload(
            workspace_id, "stage3-submission-0003", draft
        )
        self.assertEqual(payload["requested_journey"]["gestational_week"], 24)
        self.assertEqual(payload["requested_journey"]["gestational_day"], 2)
        self.assertEqual(payload["requested_journey"]["effective_date"], str(TODAY - timedelta(days=9)))
        self.assertEqual(payload["requested_facts"][1]["fact_type"], "other")
        self.assertEqual(
            payload["requested_facts"][1]["value"]["category"],
            "movement_restriction",
        )
        self.assertEqual(len(payload["requested_payload_sha256"]), 64)

    def test_payload_hash_is_stable_and_changes_with_input(self):
        workspace_id = uuid4()
        timing = ManualWeekDayTiming(effective_date=TODAY, gestational_week=24)
        first = prepare_onboarding(timing, OnboardingDetails(), self.spec, clock=self.clock)
        second = prepare_onboarding(timing, OnboardingDetails(), self.spec, clock=self.clock)
        first_payload = build_onboarding_payload(workspace_id, "stage3-submission-0004", first)
        second_payload = build_onboarding_payload(workspace_id, "stage3-submission-0004", second)
        self.assertEqual(
            first_payload["requested_payload_sha256"],
            second_payload["requested_payload_sha256"],
        )
        changed = prepare_onboarding(
            ManualWeekDayTiming(effective_date=TODAY, gestational_week=25),
            OnboardingDetails(), self.spec, clock=self.clock,
        )
        changed_payload = build_onboarding_payload(
            workspace_id, "stage3-submission-0004", changed
        )
        self.assertNotEqual(
            first_payload["requested_payload_sha256"],
            changed_payload["requested_payload_sha256"],
        )


if __name__ == "__main__":
    unittest.main()