"""Export canonical Stage 9 schemas and coverage inventory."""

from __future__ import annotations

import json
from pathlib import Path

from app.schemas.product_experience import (
    ChatDisplayResult, DocumentView, EvaluatorMetric, EvidenceDrawerItem,
    JourneyHeader, RuntimeConfig, SimulatedReviewView, WeeklyHomeView,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "data/schemas/product_experience.schema.json"
COVERAGE = ROOT / "docs/STAGE-9-COVERAGE-MANIFEST.json"


def schema_bundle():
    models = [
        RuntimeConfig, JourneyHeader, WeeklyHomeView, EvidenceDrawerItem,
        ChatDisplayResult, DocumentView, SimulatedReviewView, EvaluatorMetric,
    ]
    return {
        "schema_version": "9.0.0",
        "models": {model.__name__: model.model_json_schema() for model in models},
    }


def coverage_bundle():
    return {
        "schema_version": "9.0.0",
        "pages": [
            "Weekly Home", "Compass", "Records", "Plan", "Evidence",
            "Simulated review", "Evaluator view",
        ],
        "modes": ["Personal Mode", "Demo Mode"],
        "view_states": [
            "loading", "empty", "success", "validation_error",
            "recoverable_error", "blocked_safety", "stale_conflict",
            "unavailable_disabled",
        ],
        "provenance_labels": [
            "Your confirmed information", "Your uploaded record says",
            "You reported", "Public guidance says", "Needs confirmation",
        ],
        "document_states": [
            "ready", "low_confidence", "conflict", "locked", "corrupt",
            "unsupported", "wrong_person",
        ],
        "plan_states": [
            "none", "draft", "saved", "stale", "conflict", "invalid", "unavailable",
        ],
        "stage10_disabled": [
            "durable plan save", "durable fact confirmation", "review submission",
            "automation", "deployment",
        ],
        "provider_boundary": "deterministic controlled fixtures; no live paid provider run",
    }


def main() -> int:
    SCHEMA.parent.mkdir(parents=True, exist_ok=True)
    SCHEMA.write_text(json.dumps(schema_bundle(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    COVERAGE.write_text(json.dumps(coverage_bundle(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"schema": str(SCHEMA.relative_to(ROOT)), "coverage": str(COVERAGE.relative_to(ROOT))}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
