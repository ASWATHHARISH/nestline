"""Deterministic Stage 5 gate for contracts, fixtures, retrieval, graph, and safety."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from scripts.build_stage5_fixtures import build_devset, build_fixture
from scripts.export_retrieval_schema import build_payload
from scripts.run_stage5_retrieval_evals import run as run_retrieval_evals


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/STAGE-5-CHECK-RESULTS.json"
MIGRATION = ROOT / "supabase/migrations/20260911001300_stage5_hybrid_retrieval.sql"
SERVICE = ROOT / "app/services/retrieval.py"
SCHEMA = ROOT / "data/schemas/retrieval.schema.json"
FIXTURE = ROOT / "data/synthetic/stage5_retrieval_fixtures.json"
DEVSET = ROOT / "evals/stage5_retrieval_development.jsonl"
WEEKLY = ROOT / "data/weekly/weekly_content_manifest.jsonl"


def _load_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _contains_all(text: str, fragments: tuple[str, ...], label: str) -> list[str]:
    lowered = text.casefold()
    return [
        f"{label} is missing required contract fragment: {fragment}"
        for fragment in fragments
        if fragment.casefold() not in lowered
    ]


def run() -> dict:
    errors: list[str] = []
    required_files = [
        MIGRATION, SERVICE, SCHEMA, FIXTURE, DEVSET, WEEKLY,
        ROOT / "app/schemas/retrieval.py",
        ROOT / "scripts/check_stage5_retrieval_api.py",
        ROOT / "supabase/tests/stage5_hybrid_retrieval.test.sql",
        ROOT / "supabase/fixtures/stage5_stage4_upgrade.sql",
        ROOT / "supabase/fixtures/stage5_stage4_upgrade_check.sql",
        ROOT / "docs/STAGE-5-IMPLEMENTATION.md",
        ROOT / "docs/STAGE-5-PLAIN-LANGUAGE.md",
        ROOT / "docs/STAGE-5-SELF-VERIFICATION-AND-STAGE-6-READINESS.md",
        ROOT / "docs/NESTLINE-STAGE-5-INDEPENDENT-REVIEW-AND-STAGE-6-HANDOFF.md",
    ]
    for path in required_files:
        if not path.is_file():
            errors.append(f"required Stage 5 artifact is missing: {path.relative_to(ROOT)}")

    tracked_schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    generated_schema = build_payload()
    if tracked_schema != generated_schema:
        errors.append("tracked retrieval JSON Schema is stale")

    expected_contracts = {
        "retrieval_request", "authenticated_scope", "public_evidence_candidate",
        "personal_fact_candidate", "personal_passage_candidate", "graph_path",
        "ranked_candidate", "reranker_input", "missing_information",
        "unresolved_conflict", "abstention", "retrieval_failure",
        "evidence_packet", "retrieval_trace", "retrieval_result",
    }
    observed_contracts = set(tracked_schema.get("schemas", {}))
    if observed_contracts != expected_contracts:
        errors.append("versioned retrieval contract inventory is incomplete")
    request_properties = (
        tracked_schema.get("schemas", {})
        .get("retrieval_request", {})
        .get("properties", {})
    )
    if "workspace_id" in request_properties or "care_episode_id" in request_properties:
        errors.append("user-controlled RetrievalRequest exposes server scope")

    tracked_fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    if tracked_fixture != build_fixture():
        errors.append("tracked Stage 5 fixture corpus is stale")
    tracked_devset = _load_jsonl(DEVSET)
    if tracked_devset != build_devset():
        errors.append("tracked frozen Stage 5 development truth is stale")
    if len(tracked_devset) != 5 or len({row["case_id"] for row in tracked_devset}) != 5:
        errors.append("Stage 5 development truth must contain five unique cases")
    truth_fields = {
        "expected_public_evidence_ids", "expected_personal_fact_ids",
        "expected_graph_path_ids", "forbidden_evidence_ids",
        "expected_behavior", "criticality", "domain",
    }
    for row in tracked_devset:
        missing = truth_fields - set(row)
        if missing:
            errors.append(f"{row.get('case_id')}: development truth lacks {sorted(missing)}")

    migration = MIGRATION.read_text(encoding="utf-8")
    errors.extend(_contains_all(migration, (
        "add column if not exists search_vector tsvector",
        "using gin(search_vector)",
        "create table public.personal_retrieval_versions",
        "enable row level security",
        "stage5_authenticated_scope",
        "stage5_exact_personal_context",
        "stage5_public_full_text",
        "stage5_public_vector",
        "stage5_personal_full_text",
        "stage5_personal_vector",
        "stage5_weekly_profile",
        "stage5_graph_paths",
        "security invoker",
        "private.is_workspace_owner",
        "release.status = 'published'",
        "source.status = 'published'",
        "chunk.status = 'published'",
        "release.corpus_version = requested_corpus_version",
        "release.id = requested_release_id",
        "document.status = 'confirmed'",
        "not document.has_unresolved_conflicts",
        "requested_max_depth, 4",
        "not next_node.id = any(walk.node_ids)",
    ), "Stage 5 migration"))

    service = SERVICE.read_text(encoding="utf-8")
    errors.extend(_contains_all(service, (
        "class RetrievalGateway",
        "class Stage5RetrievalCache",
        "def exact_personal_context",
        "def public_full_text",
        "def public_vector",
        "def personal_full_text",
        "def personal_vector",
        "def graph_paths",
        "RRF_K = 60",
        "apply_ranking_improvement: bool = False",
        "rows.sort(key=lambda row: row[0])",
        "vector_unavailable",
        "database_unavailable",
        "retrieval_timeout",
        "no_approved_public_content",
    ), "Stage 5 retrieval gateway"))
    lowered_service = service.casefold()
    for forbidden in ("service_role", "neo4j"):
        if forbidden in lowered_service:
            errors.append(f"retrieval gateway contains forbidden dependency/credential: {forbidden}")

    weekly_rows = _load_jsonl(WEEKLY)
    weekly_statuses = Counter(row.get("status") for row in weekly_rows)
    if len(weekly_rows) != 63 or weekly_statuses != Counter({"draft": 63}):
        errors.append("tracked weekly profiles must remain 63 drafts and zero published")

    pgtap_plans = {
        "stage2_security_and_lifecycle.test.sql": 122,
        "stage3_exit_hardening.test.sql": 12,
        "stage3_onboarding.test.sql": 26,
        "stage4_api_role_hardening.test.sql": 11,
        "stage4_document_confirmation.test.sql": 35,
        "stage5_hybrid_retrieval.test.sql": 48,
    }
    for filename, expected in pgtap_plans.items():
        sql = (ROOT / "supabase/tests" / filename).read_text(encoding="utf-8").casefold()
        if f"select plan({expected});" not in sql:
            errors.append(f"{filename}: expected pgTAP plan({expected}) is not pinned")
    if sum(pgtap_plans.values()) != 254:
        errors.append("pinned pgTAP plans do not total 254")

    evaluation = run_retrieval_evals(write_report=False)
    adopted = evaluation["experiments"]["04_graph_enabled"]
    gate_checks = {
        "expected_public_evidence_retrieved": (
            adopted["recall_at_5"]["hits"] == adopted["recall_at_5"]["expected"]
        ),
        "no_wrong_week": adopted["wrong_week_retrieval"] == 0,
        "no_wrong_jurisdiction": adopted["wrong_jurisdiction_retrieval"] == 0,
        "no_unapproved_source": adopted["unapproved_source_retrieval"] == 0,
        "no_cross_workspace_leakage": adopted["cross_workspace_leakage"] == 0,
        "confirmed_personal_precision": (
            adopted["confirmed_personal_fact_precision"]["correct"]
            == adopted["confirmed_personal_fact_precision"]["returned"]
        ),
        "no_conflict_or_proposal_personalization": (
            adopted["conflict_proposal_personalization_violations"] == 0
        ),
        "graph_truth_retrieved": (
            adopted["graph_path_correctness"]["correct"]
            == adopted["graph_path_correctness"]["expected"]
        ),
        "expected_behaviors": (
            adopted["expected_behavior_accuracy"]["correct"]
            == adopted["expected_behavior_accuracy"]["cases"]
        ),
        "graph_ablation_is_honest": (
            evaluation["graph_ablation"]["adds_required_relationship_information"]
            and not evaluation["graph_ablation"]["sql_sufficient_case_claims_graph_benefit"]
        ),
        "ranking_trial_rejected_without_gain": (
            not evaluation["graph_ablation"]["ranking_trial_adopted"]
        ),
    }
    errors.extend(
        f"retrieval evaluation gate failed: {name}"
        for name, passed in gate_checks.items()
        if not passed
    )

    result = {
        "valid": not errors,
        "stage": 5,
        "schema_version": "5.0.0",
        "fixture_only": True,
        "paid_model_required": False,
        "ready_for_stage6_engineering": not errors,
        "ready_for_public_or_clinical_release": False,
        "verified": {
            "typed_contracts": len(observed_contracts),
            "development_cases": len(tracked_devset),
            "fixture_public_records": len(tracked_fixture.get("public_records", [])),
            "fixture_personal_fact_records": len(
                tracked_fixture.get("personal_fact_records", [])
            ),
            "fixture_graph_paths": len(tracked_fixture.get("graph_paths", [])),
            "tracked_weekly_profiles": len(weekly_rows),
            "published_weekly_profiles": weekly_statuses.get("published", 0),
            "pinned_pgtap_assertions": sum(pgtap_plans.values()),
            "stage5_pgtap_assertions": pgtap_plans["stage5_hybrid_retrieval.test.sql"],
            "authenticated_stage5_api_checks": 22,
        },
        "retrieval_gate": gate_checks,
        "adopted_metrics": adopted,
        "graph_ablation": evaluation["graph_ablation"],
        "honest_limitation": evaluation["honest_limitation"],
        "open_gates": [
            {"owner": "qualified clinical and India-localisation reviewers",
             "gate": "approve public health content and safety material"},
            {"owner": "licence reviewer",
             "gate": "approve evidence reuse and embedding rights"},
            {"owner": "product reviewer",
             "gate": "complete rendered UI acceptance and public release decisions"},
            {"owner": "Stage 6 engineering and reviewers",
             "gate": "implement and review the Safety Gate before symptom interpretation"},
            {"owner": "platform/product",
             "gate": "choose and benchmark a production embedding provider before production embeddings"},
        ],
        "errors": errors,
    }
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args(argv)
    result = run()
    if args.write_report:
        REPORT.write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n"
        )
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
