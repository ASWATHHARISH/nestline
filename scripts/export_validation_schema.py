"""Export canonical Stage 8 schemas and validator coverage from Python source."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

from app.schemas.validation import (
    AnswerDraft,
    Claim,
    ClaimEvidenceLink,
    ComposedAnswer,
    ComposedCitation,
    ComposedSection,
    EligibleEvidenceSpan,
    PlanItemValidationLink,
    RetryStopTrace,
    SemanticAssessment,
    Stage8Result,
    ValidationEvidencePacket,
    ValidationFinding,
    ValidationReport,
    ValidationRequest,
    ValidationTrace,
    ValidatorCheckResult,
    VALIDATOR_ORDER,
)
from scripts.build_stage8_evals import build_devset


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "data/schemas/validation.schema.json"
COVERAGE = ROOT / "docs/STAGE-8-COVERAGE-MANIFEST.json"
MODELS = (
    ClaimEvidenceLink,
    Claim,
    EligibleEvidenceSpan,
    ValidationEvidencePacket,
    PlanItemValidationLink,
    AnswerDraft,
    ValidationRequest,
    SemanticAssessment,
    ValidationFinding,
    ValidatorCheckResult,
    RetryStopTrace,
    ValidationTrace,
    ValidationReport,
    ComposedCitation,
    ComposedSection,
    ComposedAnswer,
    Stage8Result,
)


def schema_bundle():
    return {
        "schema_version": "8.0.0",
        "generated_from": "app.schemas.validation",
        "schemas": {model.__name__: model.model_json_schema() for model in MODELS},
    }


def coverage_bundle():
    cases = build_devset()
    groups = Counter(row["group"] for row in cases)
    criticality = Counter(row["criticality"] for row in cases)
    return {
        "stage": 8,
        "schema_version": "8.0.0",
        "fixture_only": True,
        "sealed_holdout_accessed": False,
        "development_cases": len(cases),
        "cases_by_group": dict(sorted(groups.items())),
        "cases_by_criticality": dict(sorted(criticality.items())),
        "case_ids": [row["case_id"] for row in cases],
        "validators": [validator.value for validator in VALIDATOR_ORDER],
        "controls": {
            "strict_extra_fields": True,
            "deterministic_critical_gates": True,
            "bounded_semantic_evaluator": True,
            "paid_provider_required": False,
            "maximum_retrieval_retries": 1,
            "maximum_mechanical_repairs": 1,
            "failed_validation_composition_calls": 0,
            "urgent_ordinary_composition_calls": 0,
            "direct_persistent_writes": False,
            "stage9_ui_implemented": False,
            "stage10_persistence_implemented": False,
        },
    }


def main() -> int:
    SCHEMA.write_text(
        json.dumps(schema_bundle(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    COVERAGE.write_text(
        json.dumps(coverage_bundle(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"wrote {SCHEMA.relative_to(ROOT)}")
    print(f"wrote {COVERAGE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
