"""Deterministic Stage 3 journey calculations.

The resolver has no model or network dependency. Dates are calculated from an
injected clock so the same input can be replayed in tests and evaluations.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol
from zoneinfo import ZoneInfo

from app.schemas.onboarding import (
    ApproximateMonthTiming,
    DatingConflict,
    DeliveryDateTiming,
    EstimatedDueDateTiming,
    JourneyResolution,
    JourneyTimingInput,
    ManualWeekDayTiming,
    PossiblePregnancyTiming,
    PostpartumWeekTiming,
)
from app.schemas.storage import JourneyState
from app.services.content_selection import MONTH_RANGES


PREGNANCY_DUE_DAY = 280
MIN_PREGNANCY_POSITION_DAY = 7       # 1 week + 0 days
MAX_PREGNANCY_POSITION_DAY = 42 * 7 + 6
MAX_POSTPARTUM_TOTAL_DAY = 12 * 7 - 1
INDIA = ZoneInfo("Asia/Kolkata")


class JourneyResolutionError(ValueError):
    """Input cannot be represented safely inside Nestline's journey scope."""


class Clock(Protocol):
    def today(self) -> date: ...

    def now(self) -> datetime: ...


@dataclass(frozen=True)
class SystemClock:
    """Production clock aligned with the product and database date boundary."""

    def today(self) -> date:
        return datetime.now(INDIA).date()

    def now(self) -> datetime:
        return datetime.now(INDIA)


@dataclass(frozen=True)
class FixedClock:
    current: datetime

    def __post_init__(self) -> None:
        if self.current.tzinfo is None:
            raise ValueError("fixed clock must be timezone-aware")

    def today(self) -> date:
        return self.current.date()

    def now(self) -> datetime:
        return self.current


def _require_not_future(value: date, calculation_date: date, label: str) -> None:
    if value > calculation_date:
        raise JourneyResolutionError(f"{label} cannot be in the future")


def _pregnancy_week_day(position_day: int) -> tuple[int, int]:
    if not MIN_PREGNANCY_POSITION_DAY <= position_day <= MAX_PREGNANCY_POSITION_DAY:
        raise JourneyResolutionError(
            "calculated pregnancy timing is outside supported weeks 1 through 42"
        )
    return divmod(position_day, 7)


def _postpartum_week_day(total_day: int) -> tuple[int, int]:
    if not 0 <= total_day <= MAX_POSTPARTUM_TOTAL_DAY:
        raise JourneyResolutionError(
            "calculated postpartum timing is outside supported weeks 1 through 12"
        )
    week_index, day = divmod(total_day, 7)
    return week_index + 1, day


def _pregnancy_display(week: int, day: int) -> str:
    return f"Pregnancy week {week}, day {day}"


def _postpartum_display(week: int, day: int) -> str:
    return f"Postpartum week {week}, day {day}"


class JourneyResolver:
    """Resolve all supported timing inputs using one explicit reference date."""

    def __init__(self, clock: Clock | None = None):
        self.clock = clock or SystemClock()

    def resolve(
        self,
        timing: JourneyTimingInput,
        *,
        calculation_date: date | None = None,
    ) -> JourneyResolution:
        resolved_on = calculation_date or self.clock.today()

        if isinstance(timing, PossiblePregnancyTiming):
            _require_not_future(timing.effective_date, resolved_on, "effective date")
            return JourneyResolution(
                stage="possible_pregnancy",
                timing_source="user_reported_possible_pregnancy",
                effective_date=timing.effective_date,
                calculation_date=resolved_on,
                certainty="unknown",
                display_label="Pregnancy timing not confirmed",
                early_pregnancy_caution=True,
                limitations=[
                    "Nestline does not infer pregnancy or assign a week from this input."
                ],
            )

        if isinstance(timing, EstimatedDueDateTiming):
            _require_not_future(timing.effective_date, resolved_on, "effective date")
            position_day = PREGNANCY_DUE_DAY - (
                timing.estimated_due_date - resolved_on
            ).days
            week, day = _pregnancy_week_day(position_day)
            return JourneyResolution(
                stage="pregnancy",
                timing_source=timing.provenance,
                effective_date=timing.effective_date,
                calculation_date=resolved_on,
                gestational_week=week,
                gestational_day=day,
                estimated_due_date=timing.estimated_due_date,
                position_day_min=position_day,
                position_day_max=position_day,
                source_fact_ids=timing.source_fact_ids,
                certainty="exact",
                display_label=_pregnancy_display(week, day),
                early_pregnancy_caution=week <= 2,
                limitations=[
                    "This is a date calculation from the confirmed estimated due date, not a new clinical estimate."
                ],
            )

        if isinstance(timing, ManualWeekDayTiming):
            _require_not_future(timing.effective_date, resolved_on, "effective date")
            elapsed = (resolved_on - timing.effective_date).days
            position_day = timing.gestational_week * 7 + timing.gestational_day + elapsed
            week, day = _pregnancy_week_day(position_day)
            return JourneyResolution(
                stage="pregnancy",
                timing_source="manual_week_day",
                effective_date=timing.effective_date,
                calculation_date=resolved_on,
                gestational_week=week,
                gestational_day=day,
                position_day_min=position_day,
                position_day_max=position_day,
                certainty="exact",
                display_label=_pregnancy_display(week, day),
                early_pregnancy_caution=week <= 2,
                limitations=[
                    "This rolls forward the week and day you reported; it does not verify clinical dating."
                ],
            )

        if isinstance(timing, ApproximateMonthTiming):
            return self.resolve_approximate_month_range(
                timing.pregnancy_month,
                timing.pregnancy_month,
                effective_date=timing.effective_date,
                calculation_date=resolved_on,
            )

        if isinstance(timing, DeliveryDateTiming):
            _require_not_future(timing.delivery_date, resolved_on, "delivery date")
            total_day = (resolved_on - timing.delivery_date).days
            week, day = _postpartum_week_day(total_day)
            return JourneyResolution(
                stage="postpartum",
                timing_source="delivery_date",
                effective_date=timing.delivery_date,
                calculation_date=resolved_on,
                postpartum_week=week,
                postpartum_day=day,
                delivery_date=timing.delivery_date,
                position_day_min=total_day,
                position_day_max=total_day,
                certainty="exact",
                display_label=_postpartum_display(week, day),
                limitations=[
                    "This is elapsed time from the reported delivery date; it does not infer delivery details."
                ],
            )

        if isinstance(timing, PostpartumWeekTiming):
            _require_not_future(timing.effective_date, resolved_on, "effective date")
            elapsed = (resolved_on - timing.effective_date).days
            total_day = (
                (timing.postpartum_week - 1) * 7 + timing.postpartum_day + elapsed
            )
            week, day = _postpartum_week_day(total_day)
            return JourneyResolution(
                stage="postpartum",
                timing_source="postpartum_week",
                effective_date=timing.effective_date,
                calculation_date=resolved_on,
                postpartum_week=week,
                postpartum_day=day,
                position_day_min=total_day,
                position_day_max=total_day,
                certainty="exact",
                display_label=_postpartum_display(week, day),
                limitations=[
                    "This rolls forward the postpartum week and day you reported."
                ],
            )

        raise TypeError(f"unsupported timing input: {type(timing).__name__}")

    def resolve_approximate_month_range(
        self,
        month_min: int,
        month_max: int,
        *,
        effective_date: date,
        calculation_date: date | None = None,
    ) -> JourneyResolution:
        resolved_on = calculation_date or self.clock.today()
        _require_not_future(effective_date, resolved_on, "effective date")
        if type(month_min) is not int or type(month_max) is not int:
            raise JourneyResolutionError("pregnancy month range must use integers")
        if month_min not in MONTH_RANGES or month_max not in MONTH_RANGES:
            raise JourneyResolutionError("pregnancy month must be from 1 through 9")
        if month_min > month_max:
            raise JourneyResolutionError("pregnancy month range must be ordered")

        elapsed = (resolved_on - effective_date).days
        first_week = MONTH_RANGES[month_min][0]
        last_week = MONTH_RANGES[month_max][1]
        position_min = first_week * 7 + elapsed
        position_max = last_week * 7 + 6 + elapsed
        if (
            position_min < MIN_PREGNANCY_POSITION_DAY
            or position_max > MAX_PREGNANCY_POSITION_DAY
        ):
            raise JourneyResolutionError(
                "approximate month range now crosses the supported pregnancy boundary; confirm updated timing"
            )
        current_week_min = position_min // 7
        current_week_max = position_max // 7
        return JourneyResolution(
            stage="pregnancy",
            timing_source="approximate_month_range",
            effective_date=effective_date,
            calculation_date=resolved_on,
            approximate_month_min=month_min,
            approximate_month_max=month_max,
            approximate_week_min=current_week_min,
            approximate_week_max=current_week_max,
            position_day_min=position_min,
            position_day_max=position_max,
            certainty="approximate",
            display_label=(
                f"Approximately pregnancy weeks {current_week_min}–{current_week_max}"
            ),
            early_pregnancy_caution=current_week_min <= 2,
            limitations=[
                "A pregnancy month is approximate, so Nestline will not select one exact weekly profile until timing is confirmed."
            ],
        )

    def refresh_stored_state(
        self,
        state: JourneyState,
        *,
        calculation_date: date | None = None,
    ) -> JourneyResolution:
        resolved_on = calculation_date or self.clock.today()
        effective_date = state.effective_date or state.updated_at.date()

        if state.stage == "possible_pregnancy":
            timing: JourneyTimingInput = PossiblePregnancyTiming(
                effective_date=effective_date
            )
        elif state.timing_source in {
            "user_estimated_due_date", "document_estimated_due_date"
        }:
            if state.estimated_due_date is None:
                raise JourneyResolutionError("stored due-date state is incomplete")
            timing = EstimatedDueDateTiming(
                effective_date=effective_date,
                estimated_due_date=state.estimated_due_date,
                provenance=state.timing_source,
                source_fact_ids=state.derived_from_fact_ids,
            )
        elif state.timing_source == "manual_week_day":
            if state.gestational_week is None or state.gestational_day is None:
                raise JourneyResolutionError("stored week/day state is incomplete")
            timing = ManualWeekDayTiming(
                effective_date=effective_date,
                gestational_week=state.gestational_week,
                gestational_day=state.gestational_day,
            )
        elif state.timing_source == "approximate_month_range":
            if (
                state.approximate_month_min is None
                or state.approximate_month_max is None
            ):
                raise JourneyResolutionError("stored month-range state is incomplete")
            return self.resolve_approximate_month_range(
                state.approximate_month_min,
                state.approximate_month_max,
                effective_date=effective_date,
                calculation_date=resolved_on,
            )
        elif state.timing_source == "delivery_date":
            if state.delivery_date is None:
                raise JourneyResolutionError("stored delivery-date state is incomplete")
            timing = DeliveryDateTiming(delivery_date=state.delivery_date)
        elif state.timing_source == "postpartum_week":
            if state.postpartum_week is None or state.postpartum_day is None:
                raise JourneyResolutionError("stored postpartum state is incomplete")
            timing = PostpartumWeekTiming(
                effective_date=effective_date,
                postpartum_week=state.postpartum_week,
                postpartum_day=state.postpartum_day,
            )
        else:
            raise JourneyResolutionError("stored journey timing source is unsupported")
        return self.resolve(timing, calculation_date=resolved_on)

    def compare_with_current(
        self,
        current: JourneyState | None,
        proposed: JourneyResolution,
    ) -> DatingConflict:
        if current is None:
            return DatingConflict(
                has_conflict=False,
                reason="none",
                proposed_display=proposed.display_label,
                requires_user_choice=False,
            )

        refreshed = self.refresh_stored_state(
            current, calculation_date=proposed.calculation_date
        )
        base = {
            "current_state_id": current.id,
            "current_version": current.version,
            "current_display": refreshed.display_label,
            "proposed_display": proposed.display_label,
        }

        if current.stage == "postpartum" and proposed.stage != "postpartum":
            return DatingConflict(
                **base,
                has_conflict=True,
                reason="episode_stage_regression",
                requires_user_choice=False,
                commit_blocked=True,
            )
        if current.stage == "pregnancy" and proposed.stage == "possible_pregnancy":
            return DatingConflict(
                **base,
                has_conflict=True,
                reason="episode_stage_regression",
                requires_user_choice=False,
                commit_blocked=True,
            )
        if current.stage != proposed.stage:
            return DatingConflict(
                **base,
                has_conflict=False,
                reason="none",
                requires_user_choice=False,
            )
        if current.stage == "possible_pregnancy":
            return DatingConflict(
                **base,
                has_conflict=False,
                reason="none",
                requires_user_choice=False,
            )

        current_min = refreshed.position_day_min
        current_max = refreshed.position_day_max
        proposed_min = proposed.position_day_min
        proposed_max = proposed.position_day_max
        if None in (current_min, current_max, proposed_min, proposed_max):
            raise JourneyResolutionError("cannot compare incomplete resolved timing")

        if current_min == current_max and proposed_min == proposed_max:
            difference = abs(current_min - proposed_min)
            return DatingConflict(
                **base,
                has_conflict=difference != 0,
                reason="different_exact_day" if difference else "none",
                difference_days=difference,
                requires_user_choice=difference != 0,
            )

        overlaps = max(current_min, proposed_min) <= min(current_max, proposed_max)
        if overlaps:
            return DatingConflict(
                **base,
                has_conflict=False,
                reason="none",
                difference_days=0,
                requires_user_choice=False,
            )
        difference = max(current_min, proposed_min) - min(current_max, proposed_max)
        reason = (
            "outside_approximate_range"
            if (current_min == current_max) != (proposed_min == proposed_max)
            else "non_overlapping_ranges"
        )
        return DatingConflict(
            **base,
            has_conflict=True,
            reason=reason,
            difference_days=difference,
            requires_user_choice=True,
        )