"""Deterministic Stage 8 completion checker."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.schemas.validation import FindingCode, VALIDATOR_ORDER
from scripts.build_stage8_evals import build_devset
from scripts.export_validation_schema import coverage_bundle, schema_bundle
from scripts.run_stage8_evals import run as run_evals


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/STAGE-8-CHECK-RESULTS.json"
SCHEMA = ROOT / "data/schemas/validation.schema.json"
COVERAGE = ROOT / "docs/STAGE-8-COVERAGE-MANIFEST.json"
DEVSET = ROOT / "evals/stage8_validation_development.jsonl"


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def check():
    errors: list[str] = []
    required_files = [
        ROOT / "app/schemas/validation.py",
        ROOT / "app/services/semantic_support.py",
        ROOT / "app/services/validation.py",
        ROOT / "scripts/stage8_fixture_support.py",
        ROOT / "scripts/build_stage8_evals.py",
        ROOT / "scripts/run_stage8_evals.py",
        ROOT / "tests/test_validation.py",
        DEVSET,
        SCHEMA,
        COVERAGE,
    ]
    for path in required_files:
        if not path.is_file():
            errors.append(f"missing Stage 8 artifact: {path.relative_to(ROOT)}")

    if not errors:
        tracked = [
            json.loads(line)
            for line in DEVSET.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if tracked != build_devset():
            errors.append("Stage 8 development truth is stale")
        if _json(SCHEMA) != schema_bundle():
            errors.append("Stage 8 exported schemas are stale")
        if _json(COVERAGE) != coverage_bundle():
            errors.append("Stage 8 coverage manifest is stale")

    service_sources = "\n".join(
        (ROOT / relative).read_text(encoding="utf-8")
        for relative in (
            "app/services/semantic_support.py",
            "app/services/validation.py",
        )
    ).casefold()
    for dependency in ("import openai", "import langchain", "import grok", "import fireworks"):
        if dependency in service_sources:
            errors.append(f"Stage 8 deterministic path imports a paid provider: {dependency}")
    for database_import in ("from supabase", "import supabase", "psycopg", "postgrest"):
        if database_import in service_sources:
            errors.append(f"Stage 8 validation path has a direct database client: {database_import}")

    eval_result = run_evals(write_report=False)
    if not eval_result["valid"]:
        errors.append("Stage 8 visible development evaluation failed")
    for field in ("cases", "critical_cases", "zero_persistent_writes"):
        metric = eval_result[field]
        if metric["passed"] != metric["total"]:
            errors.append(f"Stage 8 metric is below its tested gate: {field}")
    for group, metric in eval_result["groups"].items():
        if metric["passed"] != metric["total"]:
            errors.append(f"Stage 8 scenario group failed: {group}")

    validator_names = {item.value for item in VALIDATOR_ORDER}
    if set(eval_result["validator_coverage"]) != validator_names:
        errors.append("Stage 8 evaluation does not report all seven validators")
    for validator, counts in eval_result["validator_coverage"].items():
        if not counts["positive"] or not counts["negative"]:
            errors.append(f"Stage 8 validator lacks positive/negative evidence: {validator}")

    observed_codes = {
        code
        for case in eval_result["case_results"]
        for code in case["observed_finding_codes"]
    }
    required_rejections = {
        FindingCode.FABRICATED_CITATION.value,
        FindingCode.MATERIAL_CLAIM_WITHOUT_EVIDENCE.value,
        FindingCode.WRONG_WEEK.value,
        FindingCode.ALLERGY_VIOLATION.value,
        FindingCode.RESTRICTION_VIOLATION.value,
        FindingCode.PRESCRIBING_OR_MEDICATION_CHANGE.value,
        FindingCode.CITATION_IRRELEVANT.value,
    }
    missing_rejections = sorted(required_rejections - observed_codes)
    if missing_rejections:
        errors.append(f"Stage 8 exit rejections are untested: {missing_rejections}")

    attempts = eval_result["bounded_attempts"]
    if attempts["maximum_retrieval_retries_observed"] > 1:
        errors.append("Stage 8 exceeded one retrieval retry")
    if attempts["maximum_repairs_observed"] > 1:
        errors.append("Stage 8 exceeded one mechanical repair")
    if attempts["composition_calls_on_failed_validation"]:
        errors.append("A failed Stage 8 validation called answer composition")
    if attempts["urgent_ordinary_composition_calls"]:
        errors.append("An urgent Stage 6 result entered ordinary composition")

    spec = json.loads((ROOT / "data/safety/rule_spec.yaml").read_text(encoding="utf-8"))
    if spec.get("status") != "draft":
        errors.append("Stage 8 must not publish the draft safety specification")

    return {
        "valid": not errors,
        "stage": 8,
        "schema_version": "8.0.0",
        "deterministic_critical_gates": True,
        "paid_model_required": False,
        "database_migration_required": False,
        "public_or_clinical_release_ready": False,
        "controlled_engineering_stage9_ready": not errors,
        "verified": {
            "validators": len(VALIDATOR_ORDER),
            "development_cases": eval_result["cases"],
            "critical_cases": eval_result["critical_cases"],
            "validator_coverage": eval_result["validator_coverage"],
            "scenario_groups": eval_result["groups"],
            "bounded_attempts": attempts,
            "zero_persistent_writes": eval_result["zero_persistent_writes"],
            "required_rejection_codes": sorted(required_rejections),
            "observed_rejection_codes": sorted(observed_codes),
        },
        "limitations": eval_result["limitations"],
        "errors": errors,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args(argv)
    result = check()
    if args.write_report:
        REPORT.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
