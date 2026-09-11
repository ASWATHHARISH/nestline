"""Deterministic Stage 7 completion checker."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.schemas.orchestration import AgentName
from app.services.orchestration_catalogue import AGENT_CATALOGUE, CONTEXT_POLICY
from scripts.build_stage7_evals import build_devset
from scripts.export_orchestration_schema import coverage_bundle, schema_bundle
from scripts.run_stage7_evals import run as run_evals


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/STAGE-7-CHECK-RESULTS.json"
SCHEMA = ROOT / "data/schemas/orchestration.schema.json"
COVERAGE = ROOT / "docs/STAGE-7-COVERAGE-MANIFEST.json"
DEVSET = ROOT / "evals/stage7_orchestration_development.jsonl"


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def check():
    errors = []
    required_files = [
        ROOT / "app/schemas/orchestration.py",
        ROOT / "app/services/model_provider.py",
        ROOT / "app/services/orchestration_catalogue.py",
        ROOT / "app/services/agents.py",
        ROOT / "app/services/schedule_builder.py",
        ROOT / "app/services/orchestration.py",
        ROOT / "tests/test_orchestration.py",
        DEVSET, SCHEMA, COVERAGE,
    ]
    for path in required_files:
        if not path.is_file():
            errors.append(f"missing Stage 7 artifact: {path.relative_to(ROOT)}")
    if not errors:
        tracked = [json.loads(line) for line in DEVSET.read_text(encoding="utf-8").splitlines()
                   if line.strip()]
        if tracked != build_devset():
            errors.append("Stage 7 development truth is stale")
        if _json(SCHEMA) != schema_bundle():
            errors.append("Stage 7 exported schemas are stale")
        if _json(COVERAGE) != coverage_bundle():
            errors.append("Stage 7 coverage manifest is stale")

    if set(AGENT_CATALOGUE) != set(AgentName) or len(AGENT_CATALOGUE) != 8:
        errors.append("Stage 7 catalogue does not contain exactly all eight planned workers")
    for agent, definition in AGENT_CATALOGUE.items():
        if definition.direct_persistent_write_allowed or definition.service_role_allowed:
            errors.append(f"{agent.value} has an unauthorized write/credential capability")
        if definition.may_call_other_agent:
            errors.append(f"{agent.value} can call another agent")
        if definition.budget.max_model_calls > 1 or definition.budget.max_repairs > 1:
            errors.append(f"{agent.value} exceeds the bounded call/repair policy")
        if not CONTEXT_POLICY.get(agent):
            errors.append(f"{agent.value} has no minimum-context policy")

    service_sources = "\n".join(
        (ROOT / relative).read_text(encoding="utf-8") for relative in (
            "app/services/agents.py", "app/services/orchestration.py",
            "app/services/schedule_builder.py", "app/services/model_provider.py",
        )
    ).casefold()
    for dependency in ("import openai", "import langchain", "import grok", "import fireworks"):
        if dependency in service_sources:
            errors.append(f"Stage 7 deterministic path imports a paid provider: {dependency}")
    for database_import in ("from supabase", "import supabase", "psycopg", "postgrest"):
        if database_import in service_sources:
            errors.append(f"Stage 7 worker path has a direct database client: {database_import}")

    eval_result = run_evals(write_report=False)
    if not eval_result["valid"]:
        errors.append("Stage 7 visible development evaluation failed")
    for field in (
        "cases", "critical_cases", "urgent_zero_agent_generation",
        "single_domain_minimal_routing", "communication_contract",
        "zero_unauthorized_writes",
    ):
        metric = eval_result[field]
        if metric["passed"] != metric["total"]:
            errors.append(f"Stage 7 metric is below its tested gate: {field}")
    for group, metric in eval_result["scenario_groups"].items():
        if metric["passed"] != metric["total"]:
            errors.append(f"Stage 7 scenario group failed: {group}")

    expected_agents = {agent.value for agent in AgentName}
    if set(eval_result["per_agent"]) != expected_agents:
        errors.append("development evaluation does not report every worker")

    spec = json.loads((ROOT / "data/safety/rule_spec.yaml").read_text(encoding="utf-8"))
    if spec.get("status") != "draft":
        errors.append("Stage 7 must not publish the draft safety specification")

    return {
        "valid": not errors,
        "stage": 7,
        "schema_version": "7.0.0",
        "deterministic": True,
        "paid_model_required": False,
        "database_migration_required": False,
        "public_or_clinical_release_ready": False,
        "controlled_engineering_stage8_ready": not errors,
        "verified": {
            "catalogue_workers": len(AGENT_CATALOGUE),
            "development_cases": eval_result["cases"],
            "critical_cases": eval_result["critical_cases"],
            "urgent_zero_agent_generation": eval_result["urgent_zero_agent_generation"],
            "single_domain_minimal_routing": eval_result["single_domain_minimal_routing"],
            "communication_contract": eval_result["communication_contract"],
            "zero_unauthorized_writes": eval_result["zero_unauthorized_writes"],
            "per_agent": eval_result["per_agent"],
            "scenario_groups": eval_result["scenario_groups"],
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
        REPORT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
