"""Run the frozen deterministic Stage 3 journey resolver cases."""

from __future__ import annotations

from datetime import date, datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from uuid import UUID

from app.schemas.onboarding import JOURNEY_TIMING_ADAPTER
from app.schemas.storage import JourneyState
from app.services.journey import FixedClock, JourneyResolutionError, JourneyResolver


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "evals/journey_resolver_set.jsonl"
FIXED_STATE_ID = UUID("33000000-0000-0000-0000-000000000001")
FIXED_WORKSPACE_ID = UUID("33000000-0000-0000-0000-000000000002")
FIXED_USER_ID = UUID("33000000-0000-0000-0000-000000000003")


def _contains(actual: dict, expected: dict) -> bool:
    return all(actual.get(key) == value for key, value in expected.items())


def _stored_state(resolution, reference_date: date) -> JourneyState:
    timestamp = datetime.combine(reference_date, datetime.min.time(), timezone.utc)
    return JourneyState(
        id=FIXED_STATE_ID,
        workspace_id=FIXED_WORKSPACE_ID,
        stage=resolution.stage,
        timing_source=resolution.timing_source,
        gestational_week=resolution.gestational_week,
        gestational_day=resolution.gestational_day,
        postpartum_week=resolution.postpartum_week,
        postpartum_day=resolution.postpartum_day,
        estimated_due_date=resolution.estimated_due_date,
        delivery_date=resolution.delivery_date,
        approximate_month_min=resolution.approximate_month_min,
        approximate_month_max=resolution.approximate_month_max,
        user_confirmed=True,
        has_dating_conflict=False,
        is_current=True,
        version=1,
        derived_from_fact_ids=resolution.source_fact_ids,
        effective_date=resolution.effective_date,
        calculation_date=resolution.calculation_date,
        confirmed_at=timestamp,
        confirmed_by_user_id=FIXED_USER_ID,
        created_at=timestamp,
        updated_at=timestamp,
    )


def run() -> dict:
    raw = DATASET.read_bytes()
    cases = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    errors = []
    seen = set()

    for case in cases:
        case_id = case.get("id")
        if case_id in seen:
            errors.append(f"{case_id}: duplicate case ID")
            continue
        seen.add(case_id)
        reference_date = date.fromisoformat(case["reference_date"])
        clock = FixedClock(datetime.combine(reference_date, datetime.min.time(), timezone.utc))
        resolver = JourneyResolver(clock)
        try:
            if case["kind"] in {"resolution", "resolution_error"}:
                timing = JOURNEY_TIMING_ADAPTER.validate_json(json.dumps(case["input"]))
                result = resolver.resolve(timing).model_dump(mode="json")
                if case["kind"] == "resolution_error":
                    errors.append(f"{case_id}: expected an error but resolution succeeded")
                elif not _contains(result, case["expected"]):
                    errors.append(f"{case_id}: output did not match the expected subset")
            elif case["kind"] == "conflict":
                current_input = JOURNEY_TIMING_ADAPTER.validate_json(
                    json.dumps(case["current_input"])
                )
                proposed_input = JOURNEY_TIMING_ADAPTER.validate_json(
                    json.dumps(case["proposed_input"])
                )
                current_resolution = resolver.resolve(current_input)
                proposed_resolution = resolver.resolve(proposed_input)
                result = resolver.compare_with_current(
                    _stored_state(current_resolution, reference_date),
                    proposed_resolution,
                ).model_dump(mode="json")
                if not _contains(result, case["expected"]):
                    errors.append(f"{case_id}: conflict result did not match expected subset")
            else:
                errors.append(f"{case_id}: unsupported case kind")
        except JourneyResolutionError as exc:
            expected = case.get("expected_error")
            if case.get("kind") != "resolution_error" or expected not in str(exc):
                errors.append(f"{case_id}: unexpected resolver error")
        except Exception as exc:
            errors.append(f"{case_id}: invalid case or unexpected {type(exc).__name__}")

    return {
        "valid": not errors,
        "dataset_sha256": sha256(raw).hexdigest(),
        "scope": "Deterministic journey/date/conflict software contract; no model or clinical validation",
        "total": len(cases),
        "passed": len(cases) - len(errors),
        "errors": errors,
    }


def main() -> int:
    result = run()
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())