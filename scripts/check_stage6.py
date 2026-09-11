"""Deterministic Stage 6 implementation and generated-evidence gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.build_stage6_safety_evals import build_devset
from scripts.export_safety_schema import build_payload as build_schema
from scripts.run_stage6_safety_evals import run as run_evals


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/STAGE-6-CHECK-RESULTS.json"
SCHEMA = ROOT / "data/schemas/safety.schema.json"
DEVSET = ROOT / "evals/stage6_safety_development.jsonl"
HANDOFF = ROOT / "docs/STAGE-6-IMPLEMENTATION-SELF-VERIFICATION-AND-STAGE-7-READINESS.md"


def _jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def run() -> dict:
    errors: list[str] = []
    required = [
        ROOT / "app/schemas/safety.py",
        ROOT / "app/services/safety_gate.py",
        ROOT / "scripts/build_stage6_safety_evals.py",
        ROOT / "scripts/run_stage6_safety_evals.py",
        ROOT / "scripts/export_safety_schema.py",
        ROOT / "tests/test_safety_gate.py",
        SCHEMA,
        DEVSET,
        HANDOFF,
    ]
    for path in required:
        if not path.is_file():
            errors.append(f"missing artifact: {path.relative_to(ROOT)}")

    if SCHEMA.is_file():
        tracked_schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        if tracked_schema != build_schema():
            errors.append("tracked Stage 6 JSON Schema is stale")
        expected_contracts = {
            "safety_gate_input", "safety_rule_match", "clarification_state",
            "fixed_safety_message", "safety_trace", "safety_gate_result",
            "generation_guard_result",
        }
        if set(tracked_schema.get("schemas", {})) != expected_contracts:
            errors.append("Stage 6 typed contract inventory is incomplete")

    expected_cases = build_devset()
    if DEVSET.is_file():
        tracked_cases = _jsonl(DEVSET)
        if tracked_cases != expected_cases:
            errors.append("tracked Stage 6 development set is stale")
        if len({row["case_id"] for row in tracked_cases}) != len(tracked_cases):
            errors.append("Stage 6 development case IDs are not unique")
        observed_channels = {row["input_channel"] for row in tracked_cases}
        required_channels = {
            "onboarding_symptom", "chat_message", "symptom_check_in",
            "extracted_document_fact", "plan_generation_input",
        }
        if observed_channels != required_channels:
            errors.append("Stage 6 development set does not cover all five channels")

    spec = json.loads((ROOT / "data/safety/rule_spec.yaml").read_text(encoding="utf-8"))
    if spec.get("status") != "draft":
        errors.append("safety specification must remain draft")
    if spec.get("jurisdiction") != "IN" or spec.get("language") != "en":
        errors.append("safety specification jurisdiction/language changed unexpectedly")
    expected_urgent_rules = {
        "S-BREATHING", "S-CHEST", "S-BLEEDING", "S-FETAL", "S-SELF-HARM",
        "S-NEURO", "S-FEVER", "S-PAIN", "S-FLUID", "S-VOMITING",
    }
    urgent_rules = {row["rule_id"] for row in spec["rules"] if row["route"] == "urgent"}
    if urgent_rules != expected_urgent_rules:
        errors.append("configured urgent-rule inventory changed or is incomplete")

    service = (ROOT / "app/services/safety_gate.py").read_text(encoding="utf-8")
    required_service_fragments = (
        "class SafetyGate", "evaluate_onboarding_symptom", "evaluate_chat_message",
        "evaluate_symptom_check_in", "evaluate_extracted_document_fact",
        "evaluate_plan_generation_input", "continue_after_safety_gate",
        "draft_specification", "missing_specification", "malformed_specification",
        "unsupported_specification_version",
    )
    for fragment in required_service_fragments:
        if fragment not in service:
            errors.append(f"Safety Gate missing required implementation fragment: {fragment}")
    for forbidden in ("openai", "grok", "fireworks", "langchain", "requests.post"):
        if forbidden in service.casefold():
            errors.append(f"urgent path contains an external/model dependency: {forbidden}")

    onboarding = (ROOT / "app/services/onboarding.py").read_text(encoding="utf-8")
    if "_legacy_storage_route" not in onboarding or "needs_clarification\": \"clarify" not in onboarding:
        errors.append("canonical-to-legacy onboarding storage boundary is missing")

    evaluation = run_evals(write_report=False)
    if not evaluation["valid"]:
        errors.append("Stage 6 development evaluation failed")
    if evaluation["critical_cases"]["passed"] != evaluation["critical_cases"]["total"]:
        errors.append("critical Stage 6 development cases are below 100%")
    if evaluation["urgent_zero_generation_calls"]["passed"] != evaluation["urgent_zero_generation_calls"]["total"]:
        errors.append("an urgent case invoked ordinary generation")
    if evaluation["zero_unsafe_reassurance"]["passed"] != evaluation["zero_unsafe_reassurance"]["total"]:
        errors.append("tested safety output contained unsafe reassurance")
    if evaluation["ambiguous_or_failure_cases_conservatively_stopped"]["passed"] != evaluation["ambiguous_or_failure_cases_conservatively_stopped"]["total"]:
        errors.append("an ambiguous/failure case did not conservatively stop")

    return {
        "valid": not errors,
        "stage": 6,
        "schema_version": "6.0.0",
        "deterministic": True,
        "paid_model_required": False,
        "database_migration_required": False,
        "specification_status": spec.get("status"),
        "public_or_clinical_release_ready": False,
        "controlled_engineering_stage7_ready": not errors,
        "verified": {
            "typed_contracts": 7,
            "development_cases": len(expected_cases),
            "critical_cases": evaluation["critical_cases"],
            "urgent_zero_generation_calls": evaluation["urgent_zero_generation_calls"],
            "zero_unsafe_reassurance": evaluation["zero_unsafe_reassurance"],
            "ambiguous_or_failure_cases_stopped": evaluation[
                "ambiguous_or_failure_cases_conservatively_stopped"
            ],
            "input_channels": 5,
            "urgent_rule_categories": len(expected_urgent_rules),
        },
        "limitations": evaluation["limitations"],
        "errors": errors,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args(argv)
    result = run()
    if args.write_report:
        REPORT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
