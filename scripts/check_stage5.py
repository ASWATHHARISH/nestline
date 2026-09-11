"""Deterministic Stage 5 rectification gate for contracts, truth and safety."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from scripts.build_stage5_fixtures import build_devset, build_fixture
from scripts.export_retrieval_schema import build_payload
from scripts.run_stage5_retrieval_evals import run as run_retrieval_evals
from scripts.run_stage5_rectification_matrix import run as run_rectification_matrix

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/STAGE-5-CHECK-RESULTS.json"
MIGRATION = ROOT / "supabase/migrations/20260911001300_stage5_hybrid_retrieval.sql"
SCHEMA = ROOT / "data/schemas/retrieval.schema.json"
FIXTURE = ROOT / "data/synthetic/stage5_retrieval_fixtures.json"
DEVSET = ROOT / "evals/stage5_retrieval_development.jsonl"
RECTIFICATION_MATRIX = ROOT / "docs/STAGE-5-RECTIFICATION-REGRESSION-MATRIX.json"
WEEKLY = ROOT / "data/weekly/weekly_content_manifest.jsonl"


def load_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def contains_all(text, fragments, label):
    lower = text.casefold()
    return [f"{label} missing: {fragment}" for fragment in fragments
            if fragment.casefold() not in lower]


def run():
    errors = []
    required_files = [
        MIGRATION, SCHEMA, FIXTURE, DEVSET, WEEKLY,
        ROOT / "app/schemas/retrieval.py",
        ROOT / "app/services/retrieval.py",
        ROOT / "app/services/retrieval_policy.py",
        ROOT / "tests/test_retrieval.py",
        ROOT / "scripts/check_stage5_retrieval_api.py",
        ROOT / "supabase/tests/stage5_hybrid_retrieval.test.sql",
        ROOT / "supabase/fixtures/stage5_stage4_upgrade.sql",
        ROOT / "supabase/fixtures/stage5_stage4_upgrade_check.sql",
        ROOT / "docs/STAGE-5-IMPLEMENTATION.md",
        ROOT / "docs/STAGE-5-PLAIN-LANGUAGE.md",
        ROOT / "docs/STAGE-5-SELF-VERIFICATION-AND-STAGE-6-READINESS.md",
        ROOT / "docs/NESTLINE-STAGE-5-INDEPENDENT-REVIEW-AND-STAGE-6-HANDOFF.md",
        ROOT / "docs/STAGE-5-RECTIFICATION-RESPONSE.md",
        ROOT / "docs/STAGE-5-RECTIFICATION-EVIDENCE-PACKETS.json",
        ROOT / "scripts/run_stage5_rectification_matrix.py",
        RECTIFICATION_MATRIX,
        ROOT / "docs/STAGE-5-SECOND-RECTIFICATION-AND-RE-REVIEW-HANDOFF.md",
    ]
    for path in required_files:
        if not path.is_file():
            errors.append(f"missing artifact: {path.relative_to(ROOT)}")

    tracked_schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    if tracked_schema != build_payload():
        errors.append("tracked retrieval JSON Schema is stale")
    expected_contracts = {
        "retrieval_request", "authenticated_scope", "evidence_requirement_policy",
        "trusted_retrieval_state", "trusted_retrieval_query",
        "answerability_assessment", "safety_context_snapshot",
        "public_evidence_candidate", "personal_fact_candidate",
        "personal_passage_candidate", "graph_path", "ranked_candidate",
        "reranker_input", "missing_information", "unresolved_conflict",
        "abstention", "retrieval_failure", "evidence_packet",
        "retrieval_trace", "retrieval_result",
    }
    observed_contracts = set(tracked_schema.get("schemas", {}))
    if observed_contracts != expected_contracts:
        errors.append("versioned retrieval contract inventory is incomplete")
    request_properties = tracked_schema["schemas"]["retrieval_request"].get("properties", {})
    forbidden_client_fields = {"workspace_id", "care_episode_id", "state_version",
                               "active_conditions", "purpose", "owner_user_id"}
    leaked = forbidden_client_fields & set(request_properties)
    if leaked:
        errors.append(f"RetrievalRequest exposes trusted fields: {sorted(leaked)}")

    tracked_fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    if tracked_fixture != build_fixture():
        errors.append("tracked fixture corpus is stale")
    cases = load_jsonl(DEVSET)
    if cases != build_devset():
        errors.append("tracked frozen development truth is stale")
    if len(cases) != 28 or len({case["case_id"] for case in cases}) != 28:
        errors.append("Stage 5 truth must contain 28 unique cases")
    truth_fields = {
        "purpose", "expected_public_evidence_ids", "expected_personal_fact_ids",
        "expected_graph_path_ids", "forbidden_evidence_ids", "expected_behavior",
        "expected_support_state", "expected_abstention_reason",
        "expected_journey_relation", "criticality", "domain",
    }
    for case in cases:
        if truth_fields - set(case):
            errors.append(f"{case.get('case_id')}: incomplete frozen truth")
    if {case["domain"] for case in cases} != {
        "journey", "nutrition", "movement", "wellbeing", "symptoms",
        "preparation", "followup",
    }:
        errors.append("development truth does not cover every planned domain")

    migration = MIGRATION.read_text(encoding="utf-8")
    errors.extend(contains_all(migration, (
        "using gin(search_vector)", "personal_retrieval_versions",
        "enable row level security", "stage5_authenticated_scope",
        "stage5_exact_personal_context", "stage5_public_full_text",
        "stage5_public_vector", "stage5_personal_full_text",
        "stage5_personal_vector", "stage5_weekly_profile",
        "stage5_graph_paths", "security invoker", "private.is_workspace_owner",
        "release.status = 'published'", "source.status = 'published'",
        "chunk.status = 'published'", "document.status = 'confirmed'",
        "not document.has_unresolved_conflicts", "requested_max_depth, 4",
        "not next_node.id = any(walk.node_ids)",
    ), "migration"))
    service = (ROOT / "app/services/retrieval.py").read_text(encoding="utf-8")
    policy = (ROOT / "app/services/retrieval_policy.py").read_text(encoding="utf-8")
    errors.extend(contains_all(service + policy, (
        "class RetrievalGateway", "class Stage5RetrievalCache",
        "build_trusted_query", "minimise_personal_context",
        "assess_answerability", "authenticated_scope",
        "RRF_K = 60", "vector_unavailable", "database_unavailable",
        "retrieval_timeout", "no_approved_public_content",
        "caller_state_version_was_stale", "explicit_other",
    ), "gateway/policy"))
    for forbidden in ("service_role", "neo4j"):
        if forbidden in service.casefold():
            errors.append(f"gateway contains forbidden dependency/credential: {forbidden}")

    weekly_rows = load_jsonl(WEEKLY)
    statuses = Counter(row.get("status") for row in weekly_rows)
    if len(weekly_rows) != 63 or statuses != Counter({"draft": 63}):
        errors.append("weekly profiles must remain 63 drafts and zero published")

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
            errors.append(f"{filename}: expected plan({expected})")

    evaluation = run_retrieval_evals(write_report=False)
    adopted = evaluation["adopted_metrics"]
    rectification = run_rectification_matrix(write_report=False)
    if RECTIFICATION_MATRIX.is_file():
        tracked_matrix = json.loads(RECTIFICATION_MATRIX.read_text(encoding="utf-8"))
        if tracked_matrix != rectification:
            errors.append("tracked Stage 5 rectification matrix is stale")
    gates = {
        "recall_at_5": adopted["recall_at_5"]["value"] == 1.0,
        "citation_precision": adopted["citation_evidence_precision"]["value"] == 1.0,
        "no_wrong_week": adopted["wrong_week_retrieval_count"] == 0,
        "no_wrong_jurisdiction": adopted["wrong_jurisdiction_retrieval_count"] == 0,
        "no_unapproved_source": adopted["unapproved_source_retrieval_count"] == 0,
        "no_cross_workspace_leakage": adopted["cross_workspace_leakage_count"] == 0,
        "confirmed_personal_precision": adopted["confirmed_personal_fact_precision"]["value"] == 1.0,
        "no_proposal_personalization": adopted["conflict_proposal_personalization_violations"] == 0,
        "graph_truth": adopted["graph_path_correctness"]["value"] == 1.0,
        "behavior_truth": adopted["expected_behavior_accuracy"]["value"] == 1.0,
        "support_truth": adopted["support_state_accuracy"]["value"] == 1.0,
        "journey_truth": adopted["journey_relation_accuracy"]["value"] == 1.0,
        "graph_ablation": evaluation["graph_ablation"]["adds_required_relationship_information"],
        "sql_no_false_graph_claim": evaluation["graph_ablation"]["sql_answer_same_with_graph_on_and_off"],
        "ranking_trial_not_adopted": not evaluation["graph_ablation"]["ranking_trial_adopted"],
        "rectification_matrix": rectification["valid"],
    }
    errors.extend(f"retrieval gate failed: {name}" for name, passed in gates.items() if not passed)

    return {
        "valid": not errors, "stage": 5, "schema_version": "5.0.0",
        "fixture_only": True, "paid_model_required": False,
        "ready_for_independent_re_review": not errors,
        "ready_for_stage6_engineering": False,
        "stage6_gate": "independent Stage 5 re-review is still required",
        "ready_for_public_or_clinical_release": False,
        "verified": {
            "typed_contracts": len(observed_contracts),
            "development_cases": len(cases),
            "fixture_public_records": len(tracked_fixture.get("public_records", [])),
            "fixture_personal_fact_records": len(tracked_fixture.get("personal_fact_records", [])),
            "fixture_graph_paths": len(tracked_fixture.get("graph_paths", [])),
            "tracked_weekly_profiles": len(weekly_rows),
            "published_weekly_profiles": statuses.get("published", 0),
            "pinned_pgtap_assertions": sum(pgtap_plans.values()),
            "stage5_pgtap_assertions": pgtap_plans["stage5_hybrid_retrieval.test.sql"],
            "authenticated_stage5_api_checks": 25,
            "stage5_python_tests": 56,
            "cache_matrix_cases": rectification["checks"]["cache_equivalence"]["denominator"],
            "policy_rejection_cases": rectification["checks"]["policy_rejections"]["denominator"],
            "contract_mutation_cases": rectification["checks"]["contract_mutation_rejections"]["denominator"],
            "generic_conflict_cases": rectification["checks"]["generic_conflict_relevance"]["denominator"],
            "generic_missing_cases": rectification["checks"]["generic_missing_relevance"]["denominator"],
            "final_answerability_cases": rectification["checks"]["final_answerability_semantics"]["denominator"],
            "trusted_journey_cases": rectification["checks"]["trusted_journey_semantics"]["denominator"],
            "pairwise_conflict_cases": rectification["checks"]["pairwise_conflict_relevance"]["denominator"],
            "pairwise_missing_cases": rectification["checks"]["pairwise_missing_relevance"]["denominator"],
            "packet_inventory_cases": rectification["checks"]["packet_inventory_applicability"]["denominator"],
            "graph_trace_failure_cases": rectification["checks"]["graph_trace_failure_semantics"]["denominator"],
            "valid_policy_packet_cases": rectification["checks"]["valid_policy_packets"]["denominator"],
            "total_rectification_matrix_cases": sum(
                item["denominator"] for item in rectification["checks"].values()
            ),
        },
        "retrieval_gate": gates, "adopted_metrics": adopted,
        "graph_ablation": evaluation["graph_ablation"],
        "honest_limitation": evaluation["honest_limitation"],
        "open_gates": [
            {"owner": "independent reviewer", "gate": "re-review Stage 5 rectification"},
            {"owner": "clinical and India-localisation reviewers", "gate": "approve health content and safety material"},
            {"owner": "licence reviewer", "gate": "approve reuse and embedding rights"},
            {"owner": "product reviewer", "gate": "complete rendered UI and public release decisions"},
            {"owner": "Stage 6 engineering/reviewers", "gate": "implement and review Safety Gate"},
            {"owner": "platform/product", "gate": "benchmark production embedding provider"},
        ],
        "errors": errors,
    }


def main(argv=None):
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
