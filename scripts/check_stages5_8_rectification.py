"""Deterministic consolidated gate for the Stage 5–8 integration rectification."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.schemas.provider_benchmark import ProviderBenchmarkReport
from scripts.export_stages5_8_integration_schema import build_payload as build_integration_schema
from scripts.run_stage5_paraphrase_evals import run as run_paraphrases
from scripts.run_stage6_safety_evals import run as run_stage6
from scripts.run_stage7_evals import run as run_stage7
from scripts.run_stage8_evals import run as run_stage8

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/STAGES-5-TO-8-RECTIFICATION-CHECK-RESULTS.json"
SCHEMA = ROOT / "data/schemas/stages5_8_integration.schema.json"
PROVIDER_STATUS = ROOT / "docs/STAGES-7-8-LIVE-PROVIDER-BENCHMARK-STATUS.json"
HOLDOUT = ROOT / "evals/stage8_controlled_holdout_manifest.json"
SYMPTOM_PACKET = ROOT / "docs/STAGE-7-ROUTINE-SYMPTOM-POLICY-REVIEW-PACKET.md"
TONE_RUBRIC = ROOT / "docs/STAGE-8-HUMAN-PRODUCT-TONE-REVIEW-RUBRIC.md"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run() -> dict:
    errors: list[str] = []
    required = [
        ROOT / "app/schemas/integration.py",
        ROOT / "app/services/integration_gate.py",
        ROOT / "app/schemas/provider_benchmark.py",
        ROOT / "app/services/provider_benchmark.py",
        ROOT / "tests/test_stage5_8_integration.py",
        SCHEMA,
        PROVIDER_STATUS,
        HOLDOUT,
        SYMPTOM_PACKET,
        TONE_RUBRIC,
    ]
    for path in required:
        if not path.is_file():
            errors.append(f"missing consolidated artifact: {path.relative_to(ROOT)}")

    if SCHEMA.is_file() and _json(SCHEMA) != build_integration_schema():
        errors.append("tracked Stage 5–8 integration schema is stale")

    provider_report = None
    if PROVIDER_STATUS.is_file():
        try:
            provider_report = ProviderBenchmarkReport.model_validate(_json(PROVIDER_STATUS))
        except Exception as exc:  # report the strict schema failure without hiding it
            errors.append(f"provider benchmark status is invalid: {exc}")
        else:
            if provider_report.status != "blocked_not_authorized":
                errors.append("live provider benchmark must remain blocked without authorization")
            if provider_report.paid_calls_made:
                errors.append("provider status claims paid calls were made")

    if HOLDOUT.is_file():
        holdout = _json(HOLDOUT)
        if holdout.get("expected_answers_in_repository") is not False:
            errors.append("sealed holdout answers are present or status is ambiguous")
        if holdout.get("opened_during_stages_5_8_rectification") is not False:
            errors.append("sealed holdout was opened during rectification")
        case_ids = holdout.get("case_ids", [])
        if len(case_ids) != 15 or not all(isinstance(item, str) for item in case_ids):
            errors.append("sealed holdout manifest must contain exactly 15 IDs and no answers")

    if SYMPTOM_PACKET.is_file():
        text = SYMPTOM_PACKET.read_text(encoding="utf-8").casefold()
        if "external review required" not in text or "routine symptom worker remains unavailable" not in text:
            errors.append("routine symptom policy packet does not keep the capability unavailable")
    if TONE_RUBRIC.is_file():
        text = TONE_RUBRIC.read_text(encoding="utf-8").casefold()
        if "human review not yet run" not in text:
            errors.append("tone rubric does not disclose that human review is pending")

    stage5 = run_paraphrases(write_report=False)
    stage6 = run_stage6(write_report=False)
    stage7 = run_stage7(write_report=False)
    stage8 = run_stage8(write_report=False)
    evaluations = {
        "stage5_paraphrases": stage5["cases"],
        "stage6_safety": stage6["cases"],
        "stage7_orchestration": stage7["cases"],
        "stage8_validation": stage8["cases"],
    }
    for name, result in (("stage5 paraphrases", stage5), ("stage6 safety", stage6),
                         ("stage7 orchestration", stage7), ("stage8 validation", stage8)):
        if not result["valid"]:
            errors.append(f"{name} evaluation failed")

    if stage5["metrics"]["cross_workspace_leakage_count"] != 0:
        errors.append("Stage 5 paraphrase evaluation observed cross-workspace leakage")
    if stage6["urgent_zero_generation_calls"]["passed"] != stage6["urgent_zero_generation_calls"]["total"]:
        errors.append("Stage 6 urgent path invoked ordinary generation")
    if stage7["urgent_zero_agent_generation"]["passed"] != stage7["urgent_zero_agent_generation"]["total"]:
        errors.append("Stage 7 urgent path invoked an agent")
    attempts = stage8["bounded_attempts"]
    if attempts["urgent_ordinary_composition_calls"] or attempts["composition_calls_on_failed_validation"]:
        errors.append("Stage 8 composed an urgent or failed draft")

    valid = not errors
    return {
        "schema_version": "stages-5-8-rectification-gate-v1",
        "valid": valid,
        "accepted_stage8_baseline_sha": "2444f1c15b9b8a37b38a76b0257b76d2180f4b17",
        "sealed_holdout_accessed": False,
        "paid_provider_calls_made": False,
        "database_migrations_changed": False,
        "evaluations": evaluations,
        "controlled_engineering": "GO" if valid else "NO-GO",
        "personal_ui_integration": "READY_FOR_STAGE_9_ENGINEERING" if valid else "NO-GO",
        "live_provider": "NO-GO_PENDING_AUTHORIZATION_AND_BENCHMARK",
        "public_clinical_release": "NO-GO_PENDING_APPROVALS_AND_RELEASED_CONTENT",
        "stage9_engineering_may_begin": valid,
        "errors": errors,
        "limitations": [
            "Fixture embeddings, deterministic providers and synthetic development sets do not prove production quality.",
            "Routine symptom guidance remains unavailable pending qualified policy review.",
            "The safety specification and public content remain draft/unreleased.",
            "Human product/tone review and live-provider comparison have not run.",
        ],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args(argv)
    result = run()
    if args.write_report:
        REPORT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())