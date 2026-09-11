"""Golden deterministic cases for Stage 3 journey resolution."""

from datetime import date, datetime, timedelta, timezone
import unittest
from uuid import uuid4

from app.schemas.onboarding import (
    ApproximateMonthTiming,
    DeliveryDateTiming,
    EstimatedDueDateTiming,
    ManualWeekDayTiming,
    PossiblePregnancyTiming,
    PostpartumWeekTiming,
)
from app.schemas.storage import JourneyState
from app.services.content_selection import postpartum_day_context
from app.services.journey import FixedClock, JourneyResolutionError, JourneyResolver, SystemClock


NOW = datetime(2026, 9, 11, 12, 0, tzinfo=timezone.utc)
TODAY = NOW.date()


def stored_state(**changes) -> JourneyState:
    values = {
        "id": uuid4(),
        "workspace_id": uuid4(),
        "stage": "pregnancy",
        "timing_source": "manual_week_day",
        "gestational_week": 24,
        "gestational_day": 2,
        "postpartum_week": None,
        "postpartum_day": None,
        "estimated_due_date": None,
        "delivery_date": None,
        "approximate_month_min": None,
        "approximate_month_max": None,
        "user_confirmed": True,
        "has_dating_conflict": False,
        "is_current": True,
        "version": 1,
        "derived_from_fact_ids": [],
        "effective_date": TODAY,
        "calculation_date": TODAY,
        "confirmed_at": NOW,
        "confirmed_by_user_id": uuid4(),
        "created_at": NOW,
        "updated_at": NOW,
    }
    values.update(changes)
    return JourneyState(**values)


class JourneyResolverTests(unittest.TestCase):
    def setUp(self):
        self.resolver = JourneyResolver(FixedClock(NOW))

    def test_system_clock_uses_the_india_product_date_boundary(self):
        current = SystemClock().now()
        self.assertEqual(getattr(current.tzinfo, "key", None), "Asia/Kolkata")
        self.assertIsNotNone(current.utcoffset())

    def test_due_date_uses_verified_280_day_formula(self):
        result = self.resolver.resolve(EstimatedDueDateTiming(
            effective_date=TODAY,
            estimated_due_date=TODAY,
        ))
        self.assertEqual((result.gestational_week, result.gestational_day), (40, 0))
        self.assertEqual(result.position_day_min, 280)
        self.assertEqual(result.calculation_date, TODAY)

    def test_due_date_representation_boundaries(self):
        earliest = self.resolver.resolve(EstimatedDueDateTiming(
            effective_date=TODAY,
            estimated_due_date=TODAY + timedelta(days=273),
        ))
        latest = self.resolver.resolve(EstimatedDueDateTiming(
            effective_date=TODAY,
            estimated_due_date=TODAY - timedelta(days=20),
        ))
        self.assertEqual((earliest.gestational_week, earliest.gestational_day), (1, 0))
        self.assertEqual((latest.gestational_week, latest.gestational_day), (42, 6))
        with self.assertRaises(JourneyResolutionError):
            self.resolver.resolve(EstimatedDueDateTiming(
                effective_date=TODAY,
                estimated_due_date=TODAY + timedelta(days=274),
            ))
        with self.assertRaises(JourneyResolutionError):
            self.resolver.resolve(EstimatedDueDateTiming(
                effective_date=TODAY,
                estimated_due_date=TODAY - timedelta(days=21),
            ))

    def test_manual_week_rolls_forward_from_effective_date(self):
        result = self.resolver.resolve(ManualWeekDayTiming(
            effective_date=TODAY - timedelta(days=9),
            gestational_week=24,
            gestational_day=2,
        ))
        self.assertEqual((result.gestational_week, result.gestational_day), (25, 4))

    def test_manual_future_date_and_roll_past_week_42_are_rejected(self):
        with self.assertRaisesRegex(JourneyResolutionError, "future"):
            self.resolver.resolve(ManualWeekDayTiming(
                effective_date=TODAY + timedelta(days=1),
                gestational_week=24,
            ))
        with self.assertRaisesRegex(JourneyResolutionError, "outside supported"):
            self.resolver.resolve(ManualWeekDayTiming(
                effective_date=TODAY - timedelta(days=1),
                gestational_week=42,
                gestational_day=6,
            ))

    def test_month_input_stays_an_approximate_range(self):
        result = self.resolver.resolve(ApproximateMonthTiming(
            effective_date=TODAY,
            pregnancy_month=5,
        ))
        self.assertEqual(result.certainty, "approximate")
        self.assertEqual((result.approximate_month_min, result.approximate_month_max), (5, 5))
        self.assertEqual((result.approximate_week_min, result.approximate_week_max), (18, 22))
        self.assertIsNone(result.gestational_week)

    def test_month_range_rolls_forward_without_becoming_exact(self):
        result = self.resolver.resolve(ApproximateMonthTiming(
            effective_date=TODAY - timedelta(days=7),
            pregnancy_month=5,
        ))
        self.assertEqual((result.approximate_week_min, result.approximate_week_max), (19, 23))
        self.assertEqual(result.certainty, "approximate")

    def test_possible_pregnancy_never_claims_a_week(self):
        result = self.resolver.resolve(PossiblePregnancyTiming(effective_date=TODAY))
        self.assertEqual(result.stage, "possible_pregnancy")
        self.assertEqual(result.certainty, "unknown")
        self.assertIsNone(result.position_day_min)
        self.assertTrue(result.early_pregnancy_caution)

    def test_delivery_date_postpartum_boundaries_use_seven_day_groups(self):
        cases = [(0, 1, 0), (6, 1, 6), (7, 2, 0), (83, 12, 6)]
        for elapsed, week, day in cases:
            with self.subTest(elapsed=elapsed):
                result = self.resolver.resolve(DeliveryDateTiming(
                    delivery_date=TODAY - timedelta(days=elapsed)
                ))
                self.assertEqual((result.postpartum_week, result.postpartum_day), (week, day))
        with self.assertRaises(JourneyResolutionError):
            self.resolver.resolve(DeliveryDateTiming(
                delivery_date=TODAY - timedelta(days=84)
            ))
        with self.assertRaisesRegex(JourneyResolutionError, "future"):
            self.resolver.resolve(DeliveryDateTiming(
                delivery_date=TODAY + timedelta(days=1)
            ))

    def test_postpartum_week_rolls_forward(self):
        result = self.resolver.resolve(PostpartumWeekTiming(
            effective_date=TODAY - timedelta(days=9),
            postpartum_week=2,
            postpartum_day=5,
        ))
        self.assertEqual((result.postpartum_week, result.postpartum_day), (4, 0))

    def test_day_seven_overlay_remains_available_with_week_two_state(self):
        self.assertEqual(
            postpartum_day_context(7),
            {"profile_id": "PP01", "overlay_id": "PPD7"},
        )

    def test_different_exact_timing_creates_a_conflict(self):
        current = stored_state()
        proposed = self.resolver.resolve(ManualWeekDayTiming(
            effective_date=TODAY,
            gestational_week=25,
            gestational_day=2,
        ))
        conflict = self.resolver.compare_with_current(current, proposed)
        self.assertTrue(conflict.has_conflict)
        self.assertEqual(conflict.reason, "different_exact_day")
        self.assertEqual(conflict.difference_days, 7)
        self.assertTrue(conflict.requires_user_choice)

    def test_exact_value_inside_month_range_is_not_a_conflict(self):
        current = stored_state(
            timing_source="approximate_month_range",
            gestational_week=None,
            gestational_day=None,
            approximate_month_min=5,
            approximate_month_max=5,
        )
        proposed = self.resolver.resolve(ManualWeekDayTiming(
            effective_date=TODAY,
            gestational_week=20,
            gestational_day=0,
        ))
        conflict = self.resolver.compare_with_current(current, proposed)
        self.assertFalse(conflict.has_conflict)

    def test_postpartum_to_pregnancy_requires_a_new_episode(self):
        current = stored_state(
            stage="postpartum",
            timing_source="postpartum_week",
            gestational_week=None,
            gestational_day=None,
            postpartum_week=2,
            postpartum_day=0,
        )
        proposed = self.resolver.resolve(ManualWeekDayTiming(
            effective_date=TODAY,
            gestational_week=8,
        ))
        conflict = self.resolver.compare_with_current(current, proposed)
        self.assertTrue(conflict.has_conflict)
        self.assertEqual(conflict.reason, "episode_stage_regression")
        self.assertTrue(conflict.commit_blocked)
        self.assertFalse(conflict.requires_user_choice)

    def test_pregnancy_to_postpartum_is_an_allowed_forward_transition(self):
        current = stored_state()
        proposed = self.resolver.resolve(DeliveryDateTiming(delivery_date=TODAY))
        conflict = self.resolver.compare_with_current(current, proposed)
        self.assertFalse(conflict.has_conflict)


if __name__ == "__main__":
    unittest.main()