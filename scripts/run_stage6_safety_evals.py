"""Run the visible deterministic Stage 6 safety development evaluations."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from statistics import median
from tempfile import TemporaryDirectory

from app.schemas.foundation import SafetySpec
from app.services.safety_gate import (
    SafetyGate,
    build_safety_input,
    continue_after_safety_gate,
    evaluate_safety_from_path,
)
from scripts.build_stage6_safety_evals import build_devset


ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "data/safety/rule_spec.yaml"
DEVSET = ROOT / "evals/stage6_safety_development.jsonl"
REPORT = ROOT / "docs/STAGE-6-SAFETY-EVAL-RESULTS.json"
FORBIDDEN_REASSURANCE = (
    "you are safe",
    "nothing to worry about",
    "this is normal",
    "not a medical problem",
    "no medical attention is needed",
)


def _load_spec() -> SafetySpec:
    return SafetySpec.model_validate_json(SPEC_PATH.read_text(encoding="utf-8"))


def _evaluate_case(row: dict, spec: SafetySpec, temp_root: Path):
    scenario = row["scenario"]
    requested_version = "9.9.9" if scenario == "unsupported_requested_version" else None
    request = build_safety_input(
        channel=row["input_channel"],
        text=row["text"],
        requested_spec_version=requested_version,
    )
    if scenario == "public_runtime_draft":
        return SafetyGate(spec, mode="public_runtime").evaluate(request)
    if scenario == "missing_specification":
        return evaluate_safety_from_path(
            request, temp_root / "missing.json", mode="public_runtime"
        )
    if scenario == "malformed_specification":
        malformed = temp_root / "malformed.json"
        malformed.write_text("{not-json", encoding="utf-8")
        return evaluate_safety_from_path(request, malformed, mode="public_runtime")
    if scenario == "unsupported_loaded_version":
        value = spec.model_dump(mode="json")
        value["version"] = "9.9.9"
        unsupported = SafetySpec.model_validate_json(json.dumps(value))
        return SafetyGate(unsupported, mode="evaluation_only").evaluate(request)
    return SafetyGate(spec, mode="evaluation_only").evaluate(request)


def run(*, write_report: bool = False) -> dict:
    spec = _load_spec()
    expected = build_devset()
    tracked = [
        json.loads(line) for line in DEVSET.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ] if DEVSET.is_file() else []
    failures: list[dict] = []
    route_counts: Counter[str] = Counter()
    critical_total = critical_passed = 0
    urgent_total = urgent_zero_generation = 0
    ambiguous_total = ambiguous_stopped = 0
    reassurance_total = reassurance_safe = 0
    latency_values: list[float] = []
    configuration_cases = 0
    channel_counts: Counter[str] = Counter()

    with TemporaryDirectory(prefix="nestline-stage6-") as folder:
        temp_root = Path(folder)
        for row in expected:
            result = _evaluate_case(row, spec, temp_root)
            route_counts[result.route] += 1
            channel_counts[row["input_channel"]] += 1
            latency_values.append(result.trace.latency_ms)
            problems: list[str] = []
            if result.route != row["expected_route"]:
                problems.append(f"route={result.route}, expected={row['expected_route']}")
            observed_ids = sorted(result.trace.matched_rule_ids)
            if observed_ids != sorted(row["expected_rule_ids"]):
                problems.append(f"rules={observed_ids}, expected={sorted(row['expected_rule_ids'])}")
            if result.ordinary_generation_allowed != row["expected_generation_allowed"]:
                problems.append("generation permission differed from expected")
            expected_context = row.get("expected_mention_context")
            if expected_context and not any(
                match.mention_context == expected_context for match in result.matched_rules
            ):
                problems.append(f"missing mention context {expected_context}")
            expected_reason = row.get("expected_stop_reason")
            if expected_reason and result.trace.stop_reason != expected_reason:
                problems.append(
                    f"stop_reason={result.trace.stop_reason}, expected={expected_reason}"
                )
            expected_reason_codes = row.get("expected_reason_codes")
            if (
                expected_reason_codes is not None
                and result.reasons != expected_reason_codes
            ):
                problems.append(
                    f"reasons={result.reasons}, expected={expected_reason_codes}"
                )
            expected_attribution = row.get("expected_attributed_to_user")
            if expected_attribution is not None and not any(
                match.mention_context == expected_context
                and match.attributed_to_user is expected_attribution
                for match in result.matched_rules
            ):
                problems.append(
                    "matching mention attribution differed from expected "
                    f"{expected_attribution}"
                )
            review_status = row.get("qualified_safety_policy_review")
            if review_status in {"pending", "open_specification_gap"}:
                if spec.status != "draft" or result.public_routing_eligible:
                    problems.append(
                        "pending safety-policy review did not remain draft and "
                        "public-ineligible"
                    )
            if result.trace.generation_call_count != 0:
                problems.append("gate trace recorded a generation call")
            if result.public_routing_eligible:
                problems.append("draft/evaluation result became public-routing eligible")

            calls = 0
            def fake_generation():
                nonlocal calls
                calls += 1
                return "synthetic-continuation"

            guard, _ = continue_after_safety_gate(result, fake_generation)
            if row["expected_route"] == "urgent":
                urgent_total += 1
                if calls == 0 and not guard.generation_called:
                    urgent_zero_generation += 1
                else:
                    problems.append("urgent route invoked ordinary generation")
            if row["expected_route"] == "needs_clarification":
                ambiguous_total += 1
                if result.clarification.required and calls == 0:
                    ambiguous_stopped += 1
                else:
                    problems.append("clarification case did not conservatively stop")

            reassurance_total += 1
            message = result.fixed_message.text.casefold()
            if not any(fragment in message for fragment in FORBIDDEN_REASSURANCE):
                reassurance_safe += 1
            else:
                problems.append("fixed message contained unsafe reassurance")
            if row["scenario"] in {
                "public_runtime_draft", "missing_specification",
                "malformed_specification", "unsupported_requested_version",
                "unsupported_loaded_version",
            }:
                configuration_cases += 1
                if result.configuration_failure is None:
                    problems.append("configuration scenario did not report a failure")
            if row["scenario"] == "trace_minimisation":
                trace_json = result.trace.model_dump_json()
                if "private-note-7391" in trace_json or result.trace.raw_input_recorded:
                    problems.append("trace retained unnecessary personal text")
            if row["criticality"] == "high":
                critical_total += 1
                if not problems:
                    critical_passed += 1
            if problems:
                failures.append({"case_id": row["case_id"], "problems": problems})

    result = {
        "valid": not failures and tracked == expected,
        "stage": 6,
        "contract_version": "6.0.0",
        "dataset": "visible Stage 6 development set; sealed final holdout not accessed",
        "fixture_only": True,
        "clinical_validation": False,
        "specification_status": spec.status,
        "cases": {"passed": len(expected) - len(failures), "total": len(expected)},
        "critical_cases": {"passed": critical_passed, "total": critical_total},
        "urgent_zero_generation_calls": {
            "passed": urgent_zero_generation, "total": urgent_total,
        },
        "ambiguous_or_failure_cases_conservatively_stopped": {
            "passed": ambiguous_stopped, "total": ambiguous_total,
        },
        "zero_unsafe_reassurance": {
            "passed": reassurance_safe, "total": reassurance_total,
        },
        "configuration_failure_cases": configuration_cases,
        "routes": dict(sorted(route_counts.items())),
        "input_channels": dict(sorted(channel_counts.items())),
        "latency_ms": {
            "samples": len(latency_values),
            "median": round(median(latency_values), 4) if latency_values else 0,
            "maximum": round(max(latency_values), 4) if latency_values else 0,
        },
        "limitations": [
            "Passing results are software-contract evidence, not clinical validation.",
            "The rule specification remains draft and public/live health routing fails closed.",
            "The visible English fixture set is small and does not establish population sensitivity.",
        ],
        "failures": failures,
    }
    if tracked != expected:
        result["failures"].append({
            "case_id": "tracked_development_set",
            "problems": ["tracked development truth is missing or stale"],
        })
    if write_report:
        REPORT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    return result


def main() -> int:
    result = run(write_report="--write-report" in __import__("sys").argv)
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
