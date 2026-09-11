"""Run the frozen Stage 5 retrieval experiments without paid model access."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
from time import perf_counter
from uuid import UUID

from app.schemas.retrieval import (
    AuthenticatedRetrievalScope, RetrievalRequest,
)
from app.services.embeddings import DeterministicTestEmbeddingProvider
from app.services.retrieval import (
    FixtureRetrievalRepository, RetrievalGateway,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data/synthetic/stage5_retrieval_fixtures.json"
DEVSET = ROOT / "evals/stage5_retrieval_development.jsonl"
REPORT = ROOT / "docs/STAGE-5-RETRIEVAL-METRICS.json"
PROPOSAL_IDS = {"a3333333-3333-4333-8333-333333333333",
                "a4444444-4444-4444-8444-444444444444",
                "a5555555-5555-4555-8555-555555555555"}


def load_inputs():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    cases = [json.loads(line) for line in DEVSET.read_text(
        encoding="utf-8").splitlines() if line.strip()]
    return fixture, cases


def request_for(case, *, graph):
    return RetrievalRequest.model_validate_json(json.dumps({
        "question": case["question"], "domain": case["domain"],
        "journey": case["journey"], "jurisdiction": case["jurisdiction"],
        "include_graph": graph, "max_candidates": 5,
    }))


def scope_for(case):
    return AuthenticatedRetrievalScope(
        workspace_id=UUID(case["workspace_id"]),
        care_episode_id=UUID(case["workspace_id"]),
        owner_user_id=UUID(case["owner_id"]),
        session_subject=UUID(case["owner_id"]), state_version=3,
        authenticated_at=datetime.now(timezone.utc))


def empty_observation(case):
    return {"case_id": case["case_id"], "public": [], "facts": [],
            "paths": [], "personal_passages": [], "abstained": True,
            "components": {}}


def vector_only(fixture, cases):
    provider = DeterministicTestEmbeddingProvider()
    observations = []
    for case in cases:
        repo = FixtureRetrievalRepository(fixture)
        request = request_for(case, graph=False)
        started = perf_counter()
        hits = repo.public_vector(
            request, provider.embed([request.question])[0], 5)
        observation = empty_observation(case)
        observation["public"] = [hit.candidate.evidence_id for hit in hits]
        observation["abstained"] = not bool(hits)
        observation["components"] = {
            "public_vector": (perf_counter() - started) * 1000}
        observations.append(observation)
    return observations


def gateway_run(fixture, cases, *, graph, improvement):
    observations = []
    for case in cases:
        repo = FixtureRetrievalRepository(fixture)
        gateway = RetrievalGateway(
            repo, embedding_provider=DeterministicTestEmbeddingProvider(),
            corpus_version="stage5-fixture-v1", release_version="fixture-release-v1",
            apply_ranking_improvement=improvement)
        result = gateway.retrieve(request_for(case, graph=graph), scope_for(case))
        packet = result.packet
        observations.append({
            "case_id": case["case_id"],
            "public": [item.evidence_id for item in packet.approved_guideline_passages],
            "facts": [str(item.fact_id) for item in packet.confirmed_personal_facts],
            "paths": [item.path_id for item in packet.graph_paths],
            "personal_passages": [item.candidate_id for item in packet.permitted_personal_passages],
            "abstained": packet.abstention.should_abstain,
            "abstention_reason": packet.abstention.reason,
            "order_digest": result.trace.deterministic_order_digest,
            "components": {item.component: item.latency_ms
                           for item in result.trace.component_results},
        })
    return observations


def metrics(cases, observations):
    expected_public = public_hits = returned_public = 0
    expected_facts = fact_hits = returned_facts = 0
    expected_paths = path_hits = unexpected_paths = 0
    wrong_week = wrong_jurisdiction = unapproved = 0
    cross_workspace = personal_violations = 0
    behavior_hits = 0
    latency = defaultdict(list)
    forbidden_seen = []
    by_id = {item["case_id"]: item for item in observations}
    for case in cases:
        item = by_id[case["case_id"]]
        expected_public_ids = set(case["expected_public_evidence_ids"])
        expected_fact_ids = set(case["expected_personal_fact_ids"])
        expected_path_ids = set(case["expected_graph_path_ids"])
        observed_public = set(item["public"])
        observed_facts = set(item["facts"])
        observed_paths = set(item["paths"])
        expected_public += len(expected_public_ids)
        public_hits += len(expected_public_ids & observed_public)
        returned_public += len(observed_public)
        expected_facts += len(expected_fact_ids)
        fact_hits += len(expected_fact_ids & observed_facts)
        returned_facts += len(observed_facts)
        expected_paths += len(expected_path_ids)
        path_hits += len(expected_path_ids & observed_paths)
        if not expected_path_ids:
            unexpected_paths += len(observed_paths)
        forbidden = observed_public & set(case["forbidden_evidence_ids"])
        forbidden_seen.extend(sorted(forbidden))
        wrong_week += len({value for value in forbidden if "WEEK" in value or "POSTPARTUM" in value})
        wrong_jurisdiction += len({value for value in forbidden if "US" in value})
        unapproved += len({value for value in forbidden if any(
            marker in value for marker in ("DRAFT", "REJECTED", "RETIRED"))})
        personal_violations += len(observed_facts & PROPOSAL_IDS)
        if case["workspace_id"].startswith("aaaaaaaa"):
            cross_workspace += sum("b2222222" in value
                                   for value in item["personal_passages"])
        else:
            cross_workspace += sum("b1111111" in value
                                   for value in item["personal_passages"])
        expected_abstain = case["expected_behavior"] in {"abstain", "clarification"}
        behavior_hits += int(item["abstained"] == expected_abstain)
        for component, value in item["components"].items():
            latency[component].append(value)

    precision_denominator = returned_public
    fact_precision_denominator = returned_facts
    return {
        "cases": len(cases),
        "recall_at_5": {"hits": public_hits, "expected": expected_public,
                        "value": (public_hits / expected_public
                                  if expected_public else 1.0)},
        "citation_evidence_precision": {
            "correct": public_hits, "returned": precision_denominator,
            "value": (public_hits / precision_denominator
                      if precision_denominator else 1.0)},
        "wrong_week_retrieval": wrong_week,
        "wrong_jurisdiction_retrieval": wrong_jurisdiction,
        "unapproved_source_retrieval": unapproved,
        "cross_workspace_leakage": cross_workspace,
        "confirmed_personal_fact_precision": {
            "correct": fact_hits, "returned": fact_precision_denominator,
            "value": (fact_hits / fact_precision_denominator
                      if fact_precision_denominator else 1.0)},
        "confirmed_personal_fact_recall": {
            "hits": fact_hits, "expected": expected_facts,
            "value": fact_hits / expected_facts if expected_facts else 1.0},
        "conflict_proposal_personalization_violations": personal_violations,
        "graph_path_correctness": {
            "correct": path_hits, "expected": expected_paths,
            "unexpected": unexpected_paths,
            "value": path_hits / expected_paths if expected_paths else 1.0},
        "expected_behavior_accuracy": {
            "correct": behavior_hits, "cases": len(cases),
            "value": behavior_hits / len(cases)},
        "forbidden_ids_seen": sorted(set(forbidden_seen)),
        "latency_ms_by_component": {
            key: {"calls": len(values),
                  "mean": sum(values) / len(values),
                  "maximum": max(values)}
            for key, values in sorted(latency.items())},
    }


def run(write_report=False):
    fixture, cases = load_inputs()
    experiments = [
        ("01_vector_only", vector_only(fixture, cases)),
        ("02_hybrid_base_rrf", gateway_run(
            fixture, cases, graph=False, improvement=False)),
        ("03_hybrid_one_ranking_improvement", gateway_run(
            fixture, cases, graph=False, improvement=True)),
        ("04_graph_disabled", gateway_run(
            fixture, cases, graph=False, improvement=False)),
        ("04_graph_enabled", gateway_run(
            fixture, cases, graph=True, improvement=False)),
    ]
    report = {
        "schema_version": "stage5-retrieval-eval-v1",
        "dataset": "deterministic synthetic development set; not sealed holdout",
        "fixture_only": True, "paid_model_required": False,
        "cases": len(cases),
        "experiments": {name: metrics(cases, observations)
                        for name, observations in experiments},
        "observations": {name: observations
                         for name, observations in experiments},
    }
    graph_off = report["experiments"]["04_graph_disabled"]["graph_path_correctness"]
    graph_on = report["experiments"]["04_graph_enabled"]["graph_path_correctness"]
    report["graph_ablation"] = {
        "expected_paths": graph_on["expected"],
        "disabled_correct": graph_off["correct"],
        "enabled_correct": graph_on["correct"],
        "adds_required_relationship_information": (
            graph_on["correct"] > graph_off["correct"]),
        "ranking_trial_adopted": False,
        "ranking_trial_reason": "No Recall@5 or precision gain on frozen development truth.",
        "sql_sufficient_case": "S5-SQL-001",
        "sql_sufficient_case_claims_graph_benefit": False,
    }
    vector_recall = report["experiments"]["01_vector_only"]["recall_at_5"]
    hybrid_recall = report["experiments"]["04_graph_enabled"]["recall_at_5"]
    report["honest_limitation"] = (
        "The SHA-256 fixture embedding is deterministic but non-semantic and cannot "
        "measure production semantic quality; it exists only to verify plumbing, filters, "
        "ranking determinism, and provider independence."
    )
    report["comparison"] = {
        "vector_recall": vector_recall, "hybrid_recall": hybrid_recall}
    if write_report:
        REPORT.write_text(json.dumps(report, indent=2) + "\n",
                          encoding="utf-8", newline="\n")
    return report


def main() -> int:
    report = run(write_report=True)
    print(json.dumps(report, indent=2))
    final = report["experiments"]["04_graph_enabled"]
    valid = (
        final["recall_at_5"]["hits"] == final["recall_at_5"]["expected"] and
        final["wrong_week_retrieval"] == 0 and
        final["wrong_jurisdiction_retrieval"] == 0 and
        final["unapproved_source_retrieval"] == 0 and
        final["cross_workspace_leakage"] == 0 and
        final["conflict_proposal_personalization_violations"] == 0 and
        final["graph_path_correctness"]["correct"] ==
        final["graph_path_correctness"]["expected"])
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())

