"""Run frozen Stage 5 purpose-aware retrieval experiments without paid models."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
from time import perf_counter
from uuid import UUID

from app.schemas.retrieval import AuthenticatedRetrievalScope, RetrievalRequest
from app.services.embeddings import DeterministicTestEmbeddingProvider
from app.services.retrieval import FixtureRetrievalRepository, RetrievalGateway
from app.services.retrieval_policy import build_evidence_policy, build_trusted_query

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data/synthetic/stage5_retrieval_fixtures.json"
DEVSET = ROOT / "evals/stage5_retrieval_development.jsonl"
REPORT = ROOT / "docs/STAGE-5-RETRIEVAL-METRICS.json"
PACKETS = ROOT / "docs/STAGE-5-RECTIFICATION-EVIDENCE-PACKETS.json"
PROPOSAL_IDS = {"a3333333-3333-4333-8333-333333333333",
                "a4444444-4444-4444-8444-444444444444",
                "a5555555-5555-4555-8555-555555555555"}


def load_inputs():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    cases = [json.loads(line) for line in DEVSET.read_text(
        encoding="utf-8").splitlines() if line.strip()]
    return payload, cases


def request_for(case, *, graph=None):
    return RetrievalRequest.model_validate({
        "question": case["question"], "domain": case["domain"],
        "journey": case["journey"], "jurisdiction": case["jurisdiction"],
        "include_graph": case["include_graph"] if graph is None else graph,
        "max_candidates": 5,
    })


def scope_for(case):
    return AuthenticatedRetrievalScope(
        workspace_id=UUID(case["workspace_id"]),
        care_episode_id=UUID(case["workspace_id"]),
        owner_user_id=UUID(case["owner_id"]),
        session_subject=UUID(case["owner_id"]),
        state_version=case["caller_state_version"],
        authenticated_at=datetime.now(timezone.utc))


def empty_observation(case):
    return {"case_id": case["case_id"], "public": [], "facts": [],
            "paths": [], "personal_passages": [], "abstained": True,
            "abstention_reason": "no_eligible_evidence",
            "support_state": "unsupported", "journey_relation": None,
            "components": {}}


def vector_only(payload, cases):
    provider = DeterministicTestEmbeddingProvider()
    observations = []
    for case in cases:
        repo = FixtureRetrievalRepository(payload)
        request = request_for(case, graph=False)
        scope = repo.authenticated_scope(scope_for(case))
        exact = repo.exact_personal_context(scope, request)
        policy = build_evidence_policy(case["purpose"], case["domain"])
        _, query = build_trusted_query(request, scope_for(case), scope, exact, policy)
        started = perf_counter()
        hits = repo.public_vector(query, provider.embed([query.question])[0], 5)
        observation = empty_observation(case)
        observation["public"] = [hit.candidate.evidence_id for hit in hits]
        observation["abstained"] = not bool(hits)
        observation["components"] = {
            "public_vector": (perf_counter() - started) * 1000}
        observations.append(observation)
    return observations


def gateway_run(payload, cases, *, graph_override=None, improvement=False,
                include_packets=False):
    observations, packets = [], {}
    for case in cases:
        repo = FixtureRetrievalRepository(payload)
        service = RetrievalGateway(
            repo, embedding_provider=DeterministicTestEmbeddingProvider(),
            corpus_version="stage5-fixture-v2",
            release_version="fixture-release-v2",
            apply_ranking_improvement=improvement)
        request = request_for(case, graph=graph_override)
        result = service.retrieve(
            request, scope_for(case), purpose=case["purpose"]
        )
        packet = result.packet
        observations.append({
            "case_id": case["case_id"],
            "public": [item.evidence_id for item in packet.approved_guideline_passages],
            "facts": [str(item.fact_id) for item in packet.confirmed_personal_facts],
            "paths": [item.path_id for item in packet.graph_paths],
            "personal_passages": [item.candidate_id for item in packet.permitted_personal_passages],
            "abstained": packet.abstention.should_abstain,
            "abstention_reason": packet.abstention.reason,
            "support_state": packet.answerability.support_state,
            "journey_relation": packet.trusted_state.journey_relation,
            "effective_journey": packet.journey.model_dump(mode="json"),
            "caller_state_version_was_stale": packet.trusted_state.caller_state_version_was_stale,
            "resolved_state_version": result.trace.resolved_state_version,
            "conflicts": [str(item.conflict_id) for item in packet.unresolved_conflicts],
            "missing": [item.field for item in packet.missing_information],
            "order_digest": result.trace.deterministic_order_digest,
            "components": {item.component: item.latency_ms
                           for item in result.trace.component_results},
        })
        if include_packets and case["case_id"].startswith("S5-DEFECT-"):
            packets[case["case_id"]] = packet.model_dump(mode="json")
    return observations, packets


def metrics(cases, observations):
    expected_public = public_hits = returned_public = 0
    expected_facts = fact_hits = returned_facts = 0
    expected_paths = path_hits = 0
    wrong_week = wrong_jurisdiction = unapproved = 0
    cross_workspace = proposal_violations = 0
    behavior_hits = support_hits = relation_hits = 0
    forbidden_seen = []
    latency = defaultdict(list)
    by_id = {item["case_id"]: item for item in observations}
    for case in cases:
        item = by_id[case["case_id"]]
        exp_public = set(case["expected_public_evidence_ids"])
        exp_facts = set(case["expected_personal_fact_ids"])
        exp_paths = set(case["expected_graph_path_ids"])
        got_public, got_facts, got_paths = (
            set(item["public"]), set(item["facts"]), set(item["paths"]))
        expected_public += len(exp_public)
        public_hits += len(exp_public & got_public)
        returned_public += len(got_public)
        expected_facts += len(exp_facts)
        fact_hits += len(exp_facts & got_facts)
        returned_facts += len(got_facts)
        expected_paths += len(exp_paths)
        path_hits += len(exp_paths & got_paths)
        forbidden = got_public & set(case["forbidden_evidence_ids"])
        forbidden_seen.extend(sorted(forbidden))
        wrong_week += sum("WEEK" in value or "POSTPARTUM" in value for value in forbidden)
        wrong_jurisdiction += sum("US" in value for value in forbidden)
        unapproved += sum(any(word in value for word in ("DRAFT", "REJECTED", "RETIRED")) for value in forbidden)
        proposal_violations += len(got_facts & PROPOSAL_IDS)
        if case["workspace_id"] != "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa":
            cross_workspace += len(got_facts & {
                "a1111111-1111-4111-8111-111111111111",
                "a2222222-2222-4222-8222-222222222222"})
            cross_workspace += sum(value.startswith("personal-b111")
                                   for value in item["personal_passages"])
        expected_abstained = case["expected_behavior"] != "evidence"
        behavior_hits += int(
            item["abstained"] == expected_abstained
            and item["abstention_reason"] == case["expected_abstention_reason"])
        support_hits += int(item["support_state"] == case["expected_support_state"])
        relation_hits += int(item["journey_relation"] == case["expected_journey_relation"])
        for component, value in item["components"].items():
            latency[component].append(value)
    def ratio(num, den):
        return {"value": round(num / den, 6) if den else 1.0,
                "numerator": num, "denominator": den}
    return {
        "recall_at_5": ratio(public_hits, expected_public),
        "citation_evidence_precision": ratio(public_hits, returned_public),
        "wrong_week_retrieval_count": wrong_week,
        "wrong_jurisdiction_retrieval_count": wrong_jurisdiction,
        "unapproved_source_retrieval_count": unapproved,
        "cross_workspace_leakage_count": cross_workspace,
        "confirmed_personal_fact_precision": ratio(fact_hits, returned_facts),
        "conflict_proposal_personalization_violations": proposal_violations,
        "graph_path_correctness": ratio(path_hits, expected_paths),
        "expected_behavior_accuracy": ratio(behavior_hits, len(cases)),
        "support_state_accuracy": ratio(support_hits, len(cases)),
        "journey_relation_accuracy": ratio(relation_hits, len(cases)),
        "forbidden_evidence_ids_seen": sorted(set(forbidden_seen)),
        "latency_ms_by_component": {
            key: {"count": len(values), "mean": round(sum(values) / len(values), 6),
                  "max": round(max(values), 6)}
            for key, values in sorted(latency.items())},
    }


def run(write_report=False):
    payload, cases = load_inputs()
    baseline = vector_only(payload, cases)
    hybrid, corrected_packets = gateway_run(payload, cases, include_packets=True)
    trial, _ = gateway_run(payload, cases, improvement=True)
    graph_on, _ = gateway_run(payload, cases, graph_override=True)
    graph_off, _ = gateway_run(payload, cases, graph_override=False)
    adopted = metrics(cases, hybrid)
    graph_case = "S5-GRAPH-ON-001"
    sql_case = "S5-PERSONAL-ALLERGY-001"
    on = {row["case_id"]: row for row in graph_on}
    off = {row["case_id"]: row for row in graph_off}
    report = {
        "schema_version": "stage5-metrics-v3",
        "generated_from_frozen_development_truth": True,
        "fixture_only": True, "paid_model_required": False,
        "development_cases": len(cases),
        "experiments_in_order": [
            {"order": 1, "name": "vector_only_same_filters", "metrics": metrics(cases, baseline)},
            {"order": 2, "name": "hybrid_sql_full_text_vector", "metrics": adopted},
            {"order": 3, "name": "single_ranking_trial", "metrics": metrics(cases, trial), "adopted": False},
            {"order": 4, "name": "graph_ablation"},
        ],
        "adopted_metrics": adopted,
        "graph_ablation": {
            "graph_required_case": graph_case,
            "with_graph": on[graph_case]["paths"],
            "without_graph": off[graph_case]["paths"],
            "adds_required_relationship_information": bool(on[graph_case]["paths"] and not off[graph_case]["paths"]),
            "sql_sufficient_case": sql_case,
            "sql_answer_same_with_graph_on_and_off": on[sql_case]["facts"] == off[sql_case]["facts"],
            "sql_sufficient_case_claims_graph_benefit": False,
            "ranking_trial_adopted": False,
        },
        "honest_limitation": (f"Deterministic fixture embeddings and {len(cases)} synthetic "
                              "questions verify control flow, isolation and filters; "
                              "they do not establish production retrieval quality."),
        "observations": hybrid,
    }
    evidence = {
        "original_defect_reviewed_commit": "448eb6d2ab7b4e8cc7db9fc42ce5c523a7fe10a7",
        "cache_policy_reviewed_commit": "3991896135eca094bc0ab0462f3e87c615469978",
        "reproduced_before": {
            "S5-DEFECT-PUBLIC-001": {"public_count": 0, "personal_fact_count": 2, "personal_passage_count": 1, "should_abstain": False, "reason": "none"},
            "S5-DEFECT-CONFLICT-001": {"public_count": 0, "personal_fact_count": 2, "personal_passage_count": 1, "unresolved_conflict_count": 1, "should_abstain": False, "reason": "none"},
        },
        "corrected_after": corrected_packets,
    }
    if write_report:
        REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
        PACKETS.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8", newline="\n")
    return report


def main() -> int:
    report = run(write_report=True)
    print(json.dumps({"valid": all((
        report["adopted_metrics"]["wrong_week_retrieval_count"] == 0,
        report["adopted_metrics"]["wrong_jurisdiction_retrieval_count"] == 0,
        report["adopted_metrics"]["unapproved_source_retrieval_count"] == 0,
        report["adopted_metrics"]["cross_workspace_leakage_count"] == 0,
        report["adopted_metrics"]["conflict_proposal_personalization_violations"] == 0,
        report["adopted_metrics"]["expected_behavior_accuracy"]["value"] == 1.0,
        report["adopted_metrics"]["support_state_accuracy"]["value"] == 1.0,
        report["adopted_metrics"]["journey_relation_accuracy"]["value"] == 1.0,
    )), "development_cases": report["development_cases"],
        "adopted_metrics": report["adopted_metrics"]}, indent=2))
    return 0 if json.loads(json.dumps({"ok": report["adopted_metrics"]["expected_behavior_accuracy"]["value"] == 1.0}))["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
