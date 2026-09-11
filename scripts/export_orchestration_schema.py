"""Export canonical Stage 7 schemas and coverage from Python source."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

from app.schemas.orchestration import (
    AgentDefinition, AgentTrace, AuthenticatedContextSnapshot, MinimalWorkerContext,
    OrchestrationRequest, OrchestrationResult, ProposedSchedule, RoutePlan,
    ScheduleRequest, WorkerEvidence, WorkerRequest, WorkerResult,
)
from app.services.orchestration_catalogue import AGENT_CATALOGUE, CONTEXT_POLICY
from scripts.build_stage7_evals import build_devset


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "data/schemas/orchestration.schema.json"
COVERAGE = ROOT / "docs/STAGE-7-COVERAGE-MANIFEST.json"
MODELS = (
    AgentDefinition, AuthenticatedContextSnapshot, MinimalWorkerContext,
    WorkerEvidence, WorkerRequest, RoutePlan, WorkerResult, AgentTrace,
    ScheduleRequest, ProposedSchedule, OrchestrationRequest, OrchestrationResult,
)


def schema_bundle():
    return {
        "schema_version": "7.0.0",
        "generated_from": "app.schemas.orchestration",
        "schemas": {model.__name__: model.model_json_schema() for model in MODELS},
    }


def coverage_bundle():
    cases = build_devset()
    kinds = Counter(row["kind"] for row in cases)
    criticality = Counter(row["criticality"] for row in cases)
    named = [row["case_id"] for row in cases]
    return {
        "stage": 7,
        "schema_version": "7.0.0",
        "fixture_only": True,
        "sealed_holdout_accessed": False,
        "development_cases": len(cases),
        "cases_by_kind": dict(sorted(kinds.items())),
        "cases_by_criticality": dict(sorted(criticality.items())),
        "case_ids": named,
        "catalogue": {
            agent.value: {
                **definition.model_dump(mode="json"),
                "minimum_context_kinds": [kind.value for kind in CONTEXT_POLICY[agent]],
            }
            for agent, definition in AGENT_CATALOGUE.items()
        },
        "controls": {
            "safety_gate_first": True,
            "direct_agent_calls": False,
            "direct_persistent_writes": False,
            "service_role": False,
            "maximum_total_model_calls": 5,
            "maximum_specialist_calls_for_full_plan": 4,
            "maximum_composition_calls": 1,
            "maximum_worker_repairs": 1,
            "deterministic_schedule": True,
        },
    }


def main() -> int:
    SCHEMA.write_text(json.dumps(schema_bundle(), indent=2, sort_keys=True) + "\n",
                      encoding="utf-8", newline="\n")
    COVERAGE.write_text(json.dumps(coverage_bundle(), indent=2, sort_keys=True) + "\n",
                        encoding="utf-8", newline="\n")
    print(f"wrote {SCHEMA.relative_to(ROOT)}")
    print(f"wrote {COVERAGE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
