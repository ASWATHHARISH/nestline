"""Generate Stage 5 cache/policy/contract rectification evidence.

All data is synthetic. The runner uses deterministic fixture embeddings and writes
its report only when --write-report is supplied.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from uuid import UUID, uuid4

from pydantic import ValidationError

from app.schemas.retrieval import (
    AuthenticatedRetrievalScope,
    EvidencePacket,
    EvidenceRequirementPolicy,
    JourneyPosition,
    RetrievalRequest,
    RetrievalResult,
    canonical_evidence_policy_values,
)
from app.services.embeddings import DeterministicTestEmbeddingProvider
from app.services.retrieval import (
    FixtureRetrievalRepository,
    RetrievalGateway,
    Stage5RetrievalCache,
)
from app.services.retrieval_policy import build_evidence_policy
from scripts.build_stage5_fixtures import build_fixture

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/STAGE-5-RECTIFICATION-REGRESSION-MATRIX.json"
REVIEWED_COMMIT = "3991896135eca094bc0ab0462f3e87c615469978"
WORKSPACE_A = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
OWNER_A = UUID("11111111-1111-4111-8111-111111111111")


def scope(version: int = 3) -> AuthenticatedRetrievalScope:
    return AuthenticatedRetrievalScope(
        workspace_id=WORKSPACE_A,
        care_episode_id=WORKSPACE_A,
        owner_user_id=OWNER_A,
        session_subject=OWNER_A,
        state_version=version,
        authenticated_at=datetime.now(timezone.utc),
    )


def request(
    question: str,
    domain: str,
    *,
    max_candidates: int = 5,
    include_graph: bool = True,
) -> RetrievalRequest:
    return RetrievalRequest(
        question=question,
        domain=domain,
        journey=JourneyPosition(stage="pregnancy", unit="week", exact=24),
        jurisdiction="IN",
        max_candidates=max_candidates,
        include_graph=include_graph,
    )


def gateway(payload: dict | None = None, cache: Stage5RetrievalCache | None = None):
    return RetrievalGateway(
        FixtureRetrievalRepository(payload or build_fixture()),
        embedding_provider=DeterministicTestEmbeddingProvider(),
        cache=cache,
        corpus_version="stage5-fixture-v2",
        release_version="fixture-release-v2",
    )


def retrieve(service, req, purpose, auth_scope=None):
    return service.retrieve(req, auth_scope or scope(), purpose=purpose)


def semantic(result) -> dict:
    packet = result.packet
    return {
        "evidence_ids": [item.evidence_id for item in packet.approved_guideline_passages],
        "personal_fact_ids": [str(item.fact_id) for item in packet.confirmed_personal_facts],
        "personal_passage_ids": [item.candidate_id for item in packet.permitted_personal_passages],
        "graph_path_ids": [item.path_id for item in packet.graph_paths],
        "conflict_ids": [str(item.conflict_id) for item in packet.unresolved_conflicts],
        "missing_fields": [item.field for item in packet.missing_information],
        "answerability": packet.answerability.support_state,
        "ordinary_generation_allowed": packet.answerability.ordinary_generation_allowed,
        "should_abstain": packet.abstention.should_abstain,
        "abstention_reason": packet.abstention.reason,
        "required_citations": packet.required_citations,
        "policy_id": packet.retrieval_policy.policy_id,
        "resolved_state_version": result.trace.resolved_state_version,
    }


def expanded_fixture() -> dict:
    payload = build_fixture()
    public_base = next(
        row for row in payload["public_records"]
        if row["candidate"]["evidence_id"] == "EV-NUT-24"
    )
    for index in range(1, 5):
        row = deepcopy(public_base)
        candidate = row["candidate"]
        candidate["candidate_id"] = f"PUB-NUT-24-X{index}"
        candidate["evidence_id"] = f"EV-NUT-24-X{index}"
        candidate["source_id"] = f"SRC-NUT-24-X{index}"
        candidate["source_title"] = f"Synthetic nutrition source {index}"
        payload["public_records"].append(row)

    passage_base = next(
        row for row in payload["personal_passages"]
        if row["candidate"]["candidate_id"].startswith("personal-b111")
    )
    for index in range(1, 5):
        row = deepcopy(passage_base)
        candidate = row["candidate"]
        text = f"Maya fictional record {index} states a confirmed peanut allergy."
        candidate["candidate_id"] = f"personal-allergy-extra-{index}"
        candidate["chunk_id"] = f"b100000{index}-1111-4111-8111-111111111111"
        candidate["document_id"] = f"d100000{index}-1111-4111-8111-111111111111"
        candidate["text"] = text
        candidate["span"].update({
            "source_id": f"private:{candidate['document_id']}",
            "exact_text": text,
            "end_char": len(text),
            "text_sha256": sha256(text.encode()).hexdigest(),
        })
        payload["personal_passages"].append(row)
    return payload


def cache_matrix() -> list[dict]:
    graph_question = request(
        "Why is my movement plan stale after the restriction?", "movement"
    )
    mixed_question = request(
        "How should my peanut allergy affect week 24 nutrition guidance?",
        "nutrition",
    )
    rows = []
    for first_purpose, second_purpose, req in (
        ("public_guidance", "causal_explanation", graph_question),
        ("causal_explanation", "public_guidance", graph_question),
        ("personal_record_lookup", "mixed_personalized_guidance", mixed_question),
        ("mixed_personalized_guidance", "personal_record_lookup", mixed_question),
    ):
        shared = gateway(cache=Stage5RetrievalCache())
        first = retrieve(shared, req, first_purpose)
        cached = retrieve(shared, req, second_purpose)
        fresh = retrieve(gateway(), req, second_purpose)
        rows.append({
            "kind": "policy_order",
            "first": first_purpose,
            "second": second_purpose,
            "keys_separated": first.trace.personal_cache_key != cached.trace.personal_cache_key,
            "cached": semantic(cached),
            "fresh": semantic(fresh),
            "equivalent": semantic(cached) == semantic(fresh),
        })

    payload = expanded_fixture()
    limit_rows = (
        ("public_guidance", request("What protein foods matter at week 24?", "nutrition", max_candidates=1), request("What protein foods matter at week 24?", "nutrition", max_candidates=5)),
        ("public_guidance", request("What protein foods matter at week 24?", "nutrition", max_candidates=5), request("What protein foods matter at week 24?", "nutrition", max_candidates=1)),
        ("personal_record_lookup", request("What allergies are in my confirmed record?", "nutrition", max_candidates=1), request("What allergies are in my confirmed record?", "nutrition", max_candidates=5)),
        ("personal_record_lookup", request("What allergies are in my confirmed record?", "nutrition", max_candidates=5), request("What allergies are in my confirmed record?", "nutrition", max_candidates=1)),
    )
    for purpose, first_req, second_req in limit_rows:
        shared = gateway(payload, Stage5RetrievalCache())
        first = retrieve(shared, first_req, purpose)
        cached = retrieve(shared, second_req, purpose)
        fresh = retrieve(gateway(payload), second_req, purpose)
        rows.append({
            "kind": "max_candidates",
            "purpose": purpose,
            "first": first_req.max_candidates,
            "second": second_req.max_candidates,
            "public_keys_separated": first.trace.public_cache_key != cached.trace.public_cache_key,
            "personal_keys_separated": first.trace.personal_cache_key != cached.trace.personal_cache_key,
            "cached": semantic(cached),
            "fresh": semantic(fresh),
            "equivalent": semantic(cached) == semantic(fresh),
        })

    payload = build_fixture()
    repo = FixtureRetrievalRepository(payload)
    shared = RetrievalGateway(
        repo,
        embedding_provider=DeterministicTestEmbeddingProvider(),
        cache=Stage5RetrievalCache(),
        corpus_version="stage5-fixture-v2",
        release_version="fixture-release-v2",
    )
    req = request("What protein foods matter at week 24?", "nutrition")
    current = retrieve(shared, req, "public_guidance", scope(3))
    stale = retrieve(shared, req, "public_guidance", scope(999))
    rows.append({
        "kind": "caller_state_version",
        "first": 3,
        "second": 999,
        "same_server_key": current.trace.personal_cache_key == stale.trace.personal_cache_key,
        "resolved_state_version": stale.trace.resolved_state_version,
        "equivalent": semantic(current) == semantic(stale),
    })
    repo.payload["personal_state_versions"][str(WORKSPACE_A)] = 4
    changed = retrieve(shared, req, "public_guidance", scope(3))
    fresh = retrieve(gateway(repo.payload), req, "public_guidance", scope(4))
    rows.append({
        "kind": "server_state_invalidation",
        "first": 3,
        "second": 4,
        "keys_separated": current.trace.personal_cache_key != changed.trace.personal_cache_key,
        "cached": semantic(changed),
        "fresh": semantic(fresh),
        "equivalent": semantic(changed) == semantic(fresh),
    })
    return rows


def policy_rejections() -> list[dict]:
    baseline = canonical_evidence_policy_values("public_guidance", "nutrition")
    mutations = [
        ("public_requires_personal", {"required_support": ["personal_constraint"]}),
        ("personal_requires_public", {"purpose": "personal_record_lookup", "required_support": ["public_guidance"]}),
        ("causal_without_graph", {"purpose": "causal_explanation", "required_support": ["personal_record"]}),
        ("mixed_missing_constraint", {"purpose": "mixed_personalized_guidance", "required_support": ["public_guidance"]}),
        ("incorrect_domain", {"domain": "movement"}),
        ("fabricated_id", {"policy_id": "fabricated"}),
        ("fabricated_version", {"policy_version": "stage5-answerability-v2"}),
        ("extra_support", {"required_support": ["public_guidance", "personal_record"]}),
        ("incorrect_context", {"personal_context_kinds": ["allergies"]}),
    ]
    rows = []
    for name, mutation in mutations:
        try:
            EvidenceRequirementPolicy.model_validate({**baseline, **mutation})
            rejected = False
        except ValidationError:
            rejected = True
        rows.append({"case": name, "rejected": rejected})
    service = gateway()
    try:
        service.retrieve(
            request("What protein foods matter at week 24?", "nutrition"),
            scope(),
            policy=build_evidence_policy("public_guidance", "nutrition"),
        )
        rejected = False
    except TypeError:
        rejected = True
    rows.append({
        "case": "gateway_rejects_policy_object",
        "rejected": rejected,
        "repository_calls_before_rejection": service.repository.call_counts,
    })
    return rows


def contract_mutations() -> list[dict]:
    packet_result = retrieve(
        gateway(),
        request("What allergy is in my confirmed record?", "nutrition"),
        "personal_record_lookup",
    )
    base_packet = packet_result.packet.model_dump(mode="python")
    packet_mutations = []
    for state in ("unsupported", "partially_supported", "clarification_required"):
        def change(payload, value=state):
            answer = payload["answerability"]
            answer.update({
                "support_state": value,
                "ordinary_generation_allowed": False,
                "satisfied_support": [],
                "missing_support": list(answer["required_support"]),
            })
        packet_mutations.append((f"{state}_without_abstention", change))
    packet_mutations.extend([
        ("generation_and_abstention_both_true", lambda p: p["abstention"].update({"should_abstain": True, "reason": "partial_support"})),
        ("answerability_policy_id", lambda p: p["answerability"].update({"policy_id": "wrong"})),
        ("answerability_purpose", lambda p: p["answerability"].update({"purpose": "public_guidance"})),
        ("answerability_required_support", lambda p: p["answerability"].update({"required_support": ["public_guidance"], "satisfied_support": ["public_guidance"]})),
        ("packet_domain", lambda p: p.update({"domain": "movement"})),
        ("packet_journey", lambda p: p.update({"journey": JourneyPosition(stage="pregnancy", unit="week", exact=25).model_dump(mode="python")})),
        ("packet_workspace", lambda p: p.update({"workspace_id": UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")})),
        ("packet_care_episode", lambda p: p.update({"care_episode_id": UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")})),
        ("packet_conflict_alignment", lambda p: p.update({"unresolved_conflicts": [{"conflict_id": UUID("c7777777-7777-4777-8777-777777777777"), "fact_type": "allergy", "proposed_values": ["x"], "source_document_ids": [], "clarification_question_ids": [], "state": "requires_clarification"}]})),
    ])
    rows = []
    for name, mutate in packet_mutations:
        payload = deepcopy(base_packet)
        mutate(payload)
        try:
            EvidencePacket.model_validate(payload)
            rejected = False
        except ValidationError:
            rejected = True
        rows.append({"contract": "EvidencePacket", "case": name, "rejected": rejected})

    result = retrieve(
        gateway(), request("What protein foods matter at week 24?", "nutrition"),
        "public_guidance",
    )
    base_result = result.model_dump(mode="python")
    result_mutations = [
        ("request_id", lambda p: p["trace"].update({"request_id": uuid4()})),
        ("policy_id", lambda p: p["trace"].update({"policy_id": "wrong"})),
        ("journey_relation", lambda p: p["trace"].update({"journey_relation": "explicit_other"})),
        ("state_version", lambda p: p["trace"].update({"resolved_state_version": 99})),
        ("component_results", lambda p: p["trace"].update({"component_results": p["trace"]["component_results"][:-1]})),
    ]
    for name, mutate in result_mutations:
        payload = deepcopy(base_result)
        mutate(payload)
        try:
            RetrievalResult.model_validate(payload)
            rejected = False
        except ValidationError:
            rejected = True
        rows.append({"contract": "RetrievalResult", "case": name, "rejected": rejected})
    return rows


def relevance_matrix(kind: str) -> list[dict]:
    cases = [
        ("allergy", "allergy_detail", [{"substance": "sesame"}], "What allergies are in my record?", "nutrition"),
        ("restriction", "dietary_restriction", [{"restriction": "avoid lifting"}], "What restrictions are in my record?", "movement"),
        ("medication", "medication_list", [{"name": "fictional tablet"}], "What medications are in my record?", "followup"),
        ("condition", "medical_condition", [{"condition": "fictional condition"}], "What conditions are in my record?", "wellbeing"),
        ("appointment", "appointment_date", [{"date": "2026-10-01"}], "What appointments are in my record?", "preparation"),
        ("journey", "journey_week", [{"week": 23}, {"week": 24}], "What week am I in?", "journey"),
    ]
    rows = []
    conflict_types = {
        "allergy": "allergy", "restriction": "dietary_restriction",
        "medication": "medication", "condition": "medical_history",
        "appointment": "appointment", "journey": "journey_state",
    }
    for index, (category, field, values, question, domain) in enumerate(cases, 1):
        payload = build_fixture()
        context = payload["personal_contexts"][str(WORKSPACE_A)]
        if kind == "conflict":
            expected = f"c800000{index}-7777-4777-8777-777777777777"
            context["unresolved_conflicts"].append({
                "conflict_id": expected,
                "fact_type": conflict_types[category],
                "proposed_values": values,
                "source_document_ids": [],
                "clarification_question_ids": [],
                "state": "requires_clarification",
            })
        else:
            expected = field
            context["missing_information"].append({
                "field": field,
                "reason": "Required fictional detail is missing.",
                "required_for": [field],
            })
        result = retrieve(gateway(payload), request(question, domain), "personal_record_lookup")
        packet = result.packet
        observed = ([str(item.conflict_id) for item in packet.unresolved_conflicts]
                    if kind == "conflict" else
                    [item.field for item in packet.missing_information])
        rows.append({
            "category": category,
            "expected": expected,
            "observed": observed,
            "support_state": packet.answerability.support_state,
            "abstention_reason": packet.abstention.reason,
            "passed": expected in observed and
                      packet.answerability.support_state == "clarification_required" and
                      packet.abstention.should_abstain,
        })
    return rows


def run(write_report: bool = False) -> dict:
    cache = cache_matrix()
    policies = policy_rejections()
    contracts = contract_mutations()
    conflicts = relevance_matrix("conflict")
    missing = relevance_matrix("missing")
    checks = {
        "cache_equivalence": {"numerator": sum(row["equivalent"] for row in cache), "denominator": len(cache)},
        "policy_rejections": {"numerator": sum(row["rejected"] for row in policies), "denominator": len(policies)},
        "contract_mutation_rejections": {"numerator": sum(row["rejected"] for row in contracts), "denominator": len(contracts)},
        "generic_conflict_relevance": {"numerator": sum(row["passed"] for row in conflicts), "denominator": len(conflicts)},
        "generic_missing_relevance": {"numerator": sum(row["passed"] for row in missing), "denominator": len(missing)},
    }
    valid = all(value["numerator"] == value["denominator"] for value in checks.values())
    report = {
        "schema_version": "stage5-rectification-matrix-v1",
        "reviewed_commit": REVIEWED_COMMIT,
        "fixture_only": True,
        "contains_real_medical_data": False,
        "reproduced_before": {
            "public_then_causal": {"cached_paths": [], "fresh_paths": ["PATH-DOC-RESTRICTION-STALE-PLAN"], "equivalent": False},
            "causal_then_public": {"cached_paths": ["PATH-DOC-RESTRICTION-STALE-PLAN"], "fresh_paths": [], "equivalent": False},
            "public_max_1_then_5": {"cached_count": 2, "fresh_count": 5, "equivalent": False},
            "personal_max_1_then_5": {"cached_count": 2, "fresh_count": 5, "equivalent": False},
            "fabricated_policy": {"accepted": True, "ordinary_generation_allowed": True, "should_abstain": False},
            "contradictory_packet": {"accepted": True},
            "generic_allergy_conflict": {"surfaced": False, "support_state": "fully_supported", "should_abstain": False},
        },
        "corrected_after": {
            "cache_matrix": cache,
            "policy_rejections": policies,
            "contract_mutations": contracts,
            "generic_conflicts": conflicts,
            "generic_missing_information": missing,
        },
        "checks": checks,
        "valid": valid,
    }
    if write_report:
        REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args(argv)
    report = run(args.write_report)
    print(json.dumps({"valid": report["valid"], "checks": report["checks"]}, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())