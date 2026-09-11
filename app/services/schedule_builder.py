"""Deterministic one-day/one-week scheduler used by the Plan Composer."""

from __future__ import annotations

from collections import defaultdict
from hashlib import sha256

from app.schemas.orchestration import (
    AgentName,
    PlanContribution,
    ProposedSchedule,
    ScheduleRequest,
    ScheduledItem,
    Weekday,
)


DAY_ORDER = list(Weekday)
WINDOWS = {
    "morning": ("06:00", "12:00"),
    "afternoon": ("12:00", "17:00"),
    "evening": ("17:00", "22:00"),
}
CONTRIBUTOR_ORDER = {
    AgentName.NUTRITION: 0,
    AgentName.MOVEMENT: 1,
    AgentName.WELLBEING: 2,
    AgentName.FOLLOWUP: 3,
}


def _minutes(value: str) -> int:
    hour, minute = (int(part) for part in value.split(":"))
    return hour * 60 + minute


def _clock(value: int) -> str:
    return f"{value // 60:02d}:{value % 60:02d}"


def _overlaps(start: int, end: int, busy: list[tuple[int, int]]) -> bool:
    return any(start < other_end and other_start < end for other_start, other_end in busy)


def _stable_id(*parts: str) -> str:
    return "schedule-" + sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]


class ScheduleBuilder:
    """Greedy stable scheduler with fixed 30-minute tie-breaking increments."""

    def build(self, request: ScheduleRequest) -> ProposedSchedule:
        allowed_days = [request.selected_day] if request.horizon == "day" else DAY_ORDER
        availability: dict[Weekday, list[tuple[int, int]]] = defaultdict(list)
        for window in request.availability:
            if window.day in allowed_days:
                availability[window.day].append((_minutes(window.start), _minutes(window.end)))
        for values in availability.values():
            values.sort()

        busy: dict[Weekday, list[tuple[int, int]]] = defaultdict(list)
        for appointment in request.appointments:
            if appointment.day in allowed_days:
                busy[appointment.day].append((_minutes(appointment.start), _minutes(appointment.end)))
        for values in busy.values():
            values.sort()

        items: list[ScheduledItem] = []
        conflicts: list[str] = []

        # Exact clinician-recorded reminders are read-only and never shifted.
        for reminder in sorted(request.recorded_reminders, key=lambda r: (
            DAY_ORDER.index(r.day), r.time, r.reminder_id,
        )):
            if reminder.day not in allowed_days:
                continue
            start = _minutes(reminder.time)
            end = start + 5
            if _overlaps(start, end, busy[reminder.day]):
                conflicts.append(
                    f"Recorded reminder {reminder.reminder_id} overlaps a fixed appointment; "
                    "the recorded instruction was not moved."
                )
                continue
            busy[reminder.day].append((start, end))
            items.append(ScheduledItem(
                schedule_item_id=_stable_id(reminder.reminder_id, reminder.day, reminder.time),
                day=reminder.day,
                start=reminder.time,
                end=_clock(end),
                domain="record_reminder",
                item=reminder.wording,
                contributor="recorded_instruction",
                evidence_ids=[reminder.source_id],
                constraint_notes=[
                    "Read-only reminder copied from an exact clinician-recorded instruction.",
                    reminder.exact_instruction,
                ],
                record_only=True,
            ))

        unique_contributions: dict[str, PlanContribution] = {}
        for contribution in request.contributions:
            previous = unique_contributions.get(contribution.contribution_id)
            if previous is None:
                unique_contributions[contribution.contribution_id] = contribution
            elif previous != contribution:
                conflicts.append(
                    f"Contradictory contributions share ID {contribution.contribution_id}."
                )

        ordered = sorted(unique_contributions.values(), key=lambda c: (
            CONTRIBUTOR_ORDER[c.contributor], c.contribution_id,
        ))
        for contribution in ordered:
            duration = contribution.duration_minutes
            repetitions = min(contribution.cadence_per_week, len(allowed_days))
            used_days: set[Weekday] = set()
            for repetition in range(repetitions):
                placed = self._place(
                    contribution, duration, allowed_days, availability, busy, used_days,
                )
                if placed is None:
                    conflicts.append(
                        f"No non-overlapping available time for {contribution.contribution_id} "
                        f"occurrence {repetition + 1}."
                    )
                    continue
                day, start, end = placed
                used_days.add(day)
                busy[day].append((start, end))
                busy[day].sort()
                items.append(ScheduledItem(
                    schedule_item_id=_stable_id(
                        contribution.contribution_id, str(repetition), day, _clock(start),
                    ),
                    day=day,
                    start=_clock(start),
                    end=_clock(end),
                    domain=contribution.domain,
                    item=contribution.item,
                    contributor=contribution.contributor,
                    evidence_ids=contribution.evidence_ids,
                    constraint_notes=contribution.constraint_notes,
                    optional=contribution.optional,
                    flexible=contribution.flexible,
                    cadence_source=contribution.cadence_source,
                    flexible_alternatives=contribution.flexible_alternatives,
                    rest_recovery_notes=contribution.rest_recovery_notes,
                ))

        items.sort(key=lambda item: (
            DAY_ORDER.index(item.day), item.start, item.domain, item.schedule_item_id,
        ))
        uncertainties = list(dict.fromkeys(request.unresolved_uncertainties))
        constraints = list(dict.fromkeys(request.applied_constraints))
        return ProposedSchedule(
            horizon=request.horizon,
            state_version=request.state_version,
            items=items,
            conflicts=conflicts,
            assumptions=list(dict.fromkeys(
                f"{item.contribution_id}: cadence came from {item.cadence_source}."
                for item in ordered
            )),
            applied_constraints=constraints,
            unresolved_uncertainties=uncertainties,
            verified_context_summary=request.verified_context_summary,
            save_eligible=not conflicts and not uncertainties,
            stale=False,
            recomposition_count=0,
        )

    @staticmethod
    def _place(
        contribution: PlanContribution,
        duration: int,
        allowed_days: list[Weekday],
        availability: dict[Weekday, list[tuple[int, int]]],
        busy: dict[Weekday, list[tuple[int, int]]],
        used_days: set[Weekday],
    ) -> tuple[Weekday, int, int] | None:
        preferred_days = [day for day in contribution.preferred_days if day in allowed_days]
        days = preferred_days + [day for day in allowed_days if day not in preferred_days]
        # Repetitions prefer different days. Weekend remains explicit in DAY_ORDER.
        days = [day for day in days if day not in used_days] + [day for day in days if day in used_days]
        preferred_windows = [WINDOWS[name] for name in contribution.preferred_time_windows]
        for day in days:
            for outer_start, outer_end in availability.get(day, []):
                ranges = list(preferred_windows)
                if contribution.flexible or not ranges:
                    ranges.append(("00:00", "23:59"))
                for preferred_start, preferred_end in ranges:
                    start = max(outer_start, _minutes(preferred_start))
                    last = min(outer_end, _minutes(preferred_end))
                    start = ((start + 29) // 30) * 30
                    while start + duration <= last:
                        end = start + duration
                        if not _overlaps(start, end, busy[day]):
                            return day, start, end
                        start += 30
        return None

    def mark_stale(
        self,
        schedule: ProposedSchedule,
        *,
        current_state_version: int,
        changed_material_items: list[str],
    ) -> ProposedSchedule:
        """Return an in-memory stale proposal; durable invalidation is Stage 10."""

        if current_state_version == schedule.state_version and not changed_material_items:
            return schedule
        value = schedule.model_dump(mode="python")
        value["stale"] = True
        value["save_eligible"] = False
        value["unresolved_uncertainties"] = list(dict.fromkeys(
            [*schedule.unresolved_uncertainties,
             *(f"Material state changed: {item}" for item in changed_material_items)]
        ))
        return ProposedSchedule.model_validate(value)
