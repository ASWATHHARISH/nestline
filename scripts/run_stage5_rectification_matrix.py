"""Generate Stage 5 cache/policy/contract rectification evidence.

All data is synthetic. The runner uses deterministic fixture embeddings and writes
its report only when --write-report is supplied.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import time
from pathlib import Path
from uuid import UUID, uuid4

from pydantic import ValidationError

from app.schemas.retrieval import (
    AuthenticatedRetrievalScope,
    EvidencePacket,
    EvidenceRequirementPolicy,
    JourneyPosition,
    RetrievalRequest,
    RetrievalResult, TrustedRetrievalState,
    canonical_evidence_policy_values,
)
from app.services.embeddings import DeterministicTestEmbeddingProvider
from app.services.retrieval import (
    FixtureRetrievalRepository, RetrievalDatabaseUnavailable,
    RetrievalGateway, RetrievalInvalidCandidate,
    Stage5RetrievalCache,
)
from app.services.retrieval_policy import build_evidence_policy
from scripts.build_stage5_fixtures import build_fixture

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/STAGE-5-RECTIFICATION-REGRESSION-MATRIX.json"
REVIEWED_COMMIT = "2a067945986d68f85fba6234b9cb59be90a90eab"
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
        candidate["spans"][0]["source_id"] = candidate["source_id"]
        candidate["spans"][0]["evidence_id"] = candidate["evidence_id"]
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



def _rejected(model, payload: dict) -> bool:
    try:
        model.model_validate_json(json.dumps(payload, default=str))
        return False
    except ValidationError:
        return True


def final_answerability_matrix() -> list[dict]:
    rows = []
    supported = retrieve(
        gateway(), request("What nutrition guidance applies at week 24?", "nutrition"),
        "public_guidance",
    ).packet
    unsupported_request = RetrievalRequest(
        question="What documents should I prepare at week 25?", domain="preparation",
        journey=JourneyPosition(stage="pregnancy", unit="week", exact=25),
        jurisdiction="IN",
    )
    unsupported = retrieve(gateway(), unsupported_request, "public_guidance").packet
    partial_request = RetrievalRequest(
        question="How should my allergy change week 25 guidance?", domain="nutrition",
        journey=JourneyPosition(stage="pregnancy", unit="week", exact=25),
        jurisdiction="IN",
    )
    partial = retrieve(
        gateway(), partial_request, "mixed_personalized_guidance",
    ).packet

    base = supported.model_dump(mode="python")
    mutations = [
        ("fully_supported_with_missing_support", lambda p: p["answerability"].update({
            "satisfied_support": [], "missing_support": list(p["answerability"]["required_support"]),
        })),
        ("satisfied_support_boolean_false", lambda p: p["answerability"].update({
            "public_guidance_supported": False,
        })),
    ]
    def conflict_while_generating(payload):
        identifier = UUID("c7777777-7777-4777-8777-777777777777")
        payload["unresolved_conflicts"] = [{
            "conflict_id": identifier, "fact_type": "allergy",
            "proposed_values": ["sesame"], "source_document_ids": [],
            "clarification_question_ids": [], "state": "requires_clarification",
        }]
        payload["answerability"]["relevant_conflict_ids"] = [str(identifier)]
        payload["allowed_claim_types"].append("clarification_required")
    mutations.append(("generation_allowed_with_conflict", conflict_while_generating))
    def clarification_without_issue(payload):
        payload["answerability"].update({
            "support_state": "clarification_required", "ordinary_generation_allowed": False,
        })
        payload["abstention"] = {
            "should_abstain": True, "reason": "partial_support", "detail": "invalid",
        }
    mutations.append(("clarification_without_issue", clarification_without_issue))
    for name, mutate in mutations:
        payload = deepcopy(base); mutate(payload)
        rows.append({"kind": "invalid_answerability", "case": name,
                     "passed": _rejected(EvidencePacket, payload)})
    payload = unsupported.model_dump(mode="python")
    payload["abstention"]["reason"] = "unresolved_conflict"
    rows.append({"kind": "invalid_answerability",
                 "case": "conflict_reason_without_conflict",
                 "passed": _rejected(EvidencePacket, payload)})

    missing_payload = build_fixture()
    missing_payload["personal_contexts"][str(WORKSPACE_A)]["missing_information"] = [{
        "field": "allergy_detail", "reason": "Missing allergy detail.",
        "required_for": ["personal_record"],
    }]
    missing = retrieve(
        gateway(missing_payload), request("What allergies are in my record?", "nutrition"),
        "personal_record_lookup",
    ).packet
    conflict_payload = build_fixture()
    conflict_payload["personal_contexts"][str(WORKSPACE_A)]["unresolved_conflicts"] = [{
        "conflict_id": "c8111111-7777-4777-8777-777777777777",
        "fact_type": "allergy", "proposed_values": ["sesame", "none"],
        "source_document_ids": [], "clarification_question_ids": [],
        "state": "requires_clarification",
    }]
    conflict = retrieve(
        gateway(conflict_payload), request("What allergies are in my record?", "nutrition"),
        "personal_record_lookup",
    ).packet
    no_graph = retrieve(
        gateway(), request("Why is my plan stale?", "movement", include_graph=False),
        "causal_explanation",
    ).packet

    class BrokenRepository(FixtureRetrievalRepository):
        def authenticated_scope(self, requested_scope):
            raise RetrievalDatabaseUnavailable("synthetic outage")
    database = retrieve(
        RetrievalGateway(
            BrokenRepository(build_fixture()),
            embedding_provider=DeterministicTestEmbeddingProvider(),
            corpus_version="stage5-fixture-v2", release_version="fixture-release-v2",
        ), request("What nutrition guidance applies at week 24?", "nutrition"),
        "public_guidance",
    ).packet
    class SlowRepository(FixtureRetrievalRepository):
        def exact_personal_context(self, requested_scope, requested):
            time.sleep(0.02)
            return super().exact_personal_context(requested_scope, requested)
    # Force the measured timeout case with the contract's minimum bounded budget.
    timeout = retrieve(
        RetrievalGateway(
            SlowRepository(build_fixture()),
            embedding_provider=DeterministicTestEmbeddingProvider(),
            corpus_version="stage5-fixture-v2", release_version="fixture-release-v2",
        ), RetrievalRequest(
            question="What nutrition guidance applies at week 24?", domain="nutrition",
            journey=JourneyPosition(stage="pregnancy", unit="week", exact=24),
            jurisdiction="IN", timeout_ms=10,
        ), "public_guidance",
    ).packet
    valid_reasons = [
        (supported, "none"), (unsupported, "no_approved_public_content"),
        (no_graph, "no_eligible_evidence"), (partial, "partial_support"),
        (missing, "missing_information"), (conflict, "unresolved_conflict"),
        (database, "database_unavailable"), (timeout, "retrieval_timeout"),
    ]
    for packet, expected in valid_reasons:
        rows.append({"kind": "valid_abstention", "case": expected,
                     "passed": packet.abstention.reason == expected})
        payload = packet.model_dump(mode="python")
        payload["abstention"]["reason"] = (
            "partial_support" if expected != "partial_support" else "no_eligible_evidence"
        )
        payload["abstention"]["should_abstain"] = True
        rows.append({"kind": "invalid_abstention_inverse", "case": expected,
                     "passed": _rejected(EvidencePacket, payload)})
    combined_payload = build_fixture()
    combined_context = combined_payload["personal_contexts"][str(WORKSPACE_A)]
    combined_context["unresolved_conflicts"] = [{
        "conflict_id": "c8222222-7777-4777-8777-777777777777",
        "fact_type": "allergy", "proposed_values": ["sesame", "none"],
        "source_document_ids": [], "clarification_question_ids": [],
        "state": "requires_clarification",
    }]
    combined_context["missing_information"] = [{
        "field": "allergy_detail", "reason": "Missing allergy detail.",
        "required_for": ["personal_record"],
    }]
    combined = retrieve(
        gateway(combined_payload), request("What allergies are in my record?", "nutrition"),
        "personal_record_lookup",
    ).packet
    rows.append({"kind": "abstention_precedence", "case": "conflict_before_missing",
                 "passed": combined.abstention.reason == "unresolved_conflict"})

    class SlowBrokenRepository(FixtureRetrievalRepository):
        def authenticated_scope(self, requested_scope):
            time.sleep(0.02)
            raise RetrievalDatabaseUnavailable("synthetic outage")
    db_timeout = retrieve(
        RetrievalGateway(
            SlowBrokenRepository(build_fixture()),
            embedding_provider=DeterministicTestEmbeddingProvider(),
            corpus_version="stage5-fixture-v2", release_version="fixture-release-v2",
        ), RetrievalRequest(
            question="What nutrition guidance applies at week 24?", domain="nutrition",
            journey=JourneyPosition(stage="pregnancy", unit="week", exact=24),
            jurisdiction="IN", timeout_ms=10,
        ), "public_guidance",
    ).packet
    rows.append({"kind": "abstention_precedence", "case": "database_before_timeout",
                 "passed": db_timeout.abstention.reason == "database_unavailable"})
    return rows


def journey_semantic_matrix() -> list[dict]:
    rows = []
    current = retrieve(
        gateway(), request("What nutrition applies now?", "nutrition"),
        "public_guidance",
    ).packet.trusted_state
    explicit_request = RetrievalRequest(
        question="What should I prepare at week 30?", domain="preparation",
        journey=JourneyPosition(stage="pregnancy", unit="week", exact=30),
        jurisdiction="IN",
    )
    explicit = retrieve(
        gateway(), explicit_request, "public_guidance",
    ).packet.trusted_state
    overridden_request = RetrievalRequest(
        question="What nutrition applies to me now?", domain="nutrition",
        journey=JourneyPosition(stage="pregnancy", unit="week", exact=12),
        jurisdiction="IN",
    )
    overridden = retrieve(gateway(), overridden_request, "public_guidance").packet.trusted_state
    unconfirmed_payload = current.model_dump(mode="python")
    unconfirmed_payload.update({
        "current_journey": None, "effective_journey": unconfirmed_payload["requested_journey"],
        "journey_relation": "unconfirmed_current",
    })
    unconfirmed = TrustedRetrievalState.model_validate_json(
        json.dumps(unconfirmed_payload, default=str)
    )
    valid = {"current": current, "explicit_other": explicit,
             "overridden_to_current": overridden, "unconfirmed_current": unconfirmed}
    for name, state in valid.items():
        rows.append({"kind": "valid_journey_relation", "case": name,
                     "passed": state.journey_relation == name})
    current_payload = current.model_dump(mode="python")
    explicit_payload = explicit.model_dump(mode="python")
    overridden_payload = overridden.model_dump(mode="python")
    unconfirmed_payload = unconfirmed.model_dump(mode="python")
    invalid = [
        ("current_without_current", {**current_payload, "current_journey": None}),
        ("current_mismatch", {**current_payload, "effective_journey": JourneyPosition(stage="pregnancy", unit="week", exact=25)}),
        ("explicit_equal_current", {**current_payload, "journey_relation": "explicit_other"}),
        ("explicit_effective_not_requested", {**explicit_payload, "effective_journey": explicit_payload["current_journey"]}),
        ("override_without_current", {**overridden_payload, "current_journey": None}),
        ("override_effective_requested", {**overridden_payload, "effective_journey": overridden_payload["requested_journey"]}),
        ("unconfirmed_with_current", {**unconfirmed_payload, "current_journey": current_payload["current_journey"]}),
        ("unconfirmed_effective_mismatch", {**unconfirmed_payload, "effective_journey": JourneyPosition(stage="pregnancy", unit="week", exact=25)}),
    ]
    for name, payload in invalid:
        rows.append({"kind": "invalid_journey_relation", "case": name,
                     "passed": _rejected(TrustedRetrievalState, payload)})
    return rows


def pairwise_relevance_matrix(kind: str) -> list[dict]:
    categories = [
        ("allergy", "allergy_detail", "allergy", ["sesame"], "What allergies are in my record?", "nutrition"),
        ("restriction", "restriction_detail", "dietary_restriction", ["avoid lifting"], "What restrictions are in my record?", "movement"),
        ("medication", "medication_list", "medication", ["fictional tablet"], "What medications are in my record?", "followup"),
        ("condition", "medical_condition", "medical_history", ["fictional condition"], "What conditions are in my record?", "wellbeing"),
        ("appointment", "appointment_date", "appointment", ["2026-10-01"], "What appointments are in my record?", "preparation"),
        ("journey", "journey_week", "journey_state", [23, 24], "What week am I in?", "journey"),
    ]
    rows = []
    for index, (category, field, fact_type, values, question, domain) in enumerate(categories, 1):
        payload = build_fixture()
        context = payload["personal_contexts"][str(WORKSPACE_A)]
        context["unresolved_conflicts"] = []
        context["missing_information"] = []
        if kind == "conflict":
            expected = f"c900000{index}-7777-4777-8777-777777777777"
            context["unresolved_conflicts"] = [{
                "conflict_id": expected, "fact_type": fact_type,
                "proposed_values": values, "source_document_ids": [],
                "clarification_question_ids": [], "state": "requires_clarification",
            }]
        else:
            expected = field
            context["missing_information"] = [{
                "field": field, "reason": "Required fictional detail is missing.",
                "required_for": ["personal_record"],
            }]
        positive = retrieve(gateway(payload), request(question, domain), "personal_record_lookup").packet
        observed = ([str(item.conflict_id) for item in positive.unresolved_conflicts]
                    if kind == "conflict" else [item.field for item in positive.missing_information])
        rows.append({"kind": f"{kind}_positive", "case": category,
                     "passed": expected in observed and positive.abstention.should_abstain})
        for other_category, _, _, _, other_question, other_domain in categories:
            if other_category == category:
                continue
            negative = retrieve(
                gateway(payload), request(other_question, other_domain),
                "personal_record_lookup",
            ).packet
            observed = (negative.unresolved_conflicts if kind == "conflict"
                        else negative.missing_information)
            rows.append({"kind": f"{kind}_pairwise_negative",
                         "case": f"{category}_vs_{other_category}",
                         "passed": observed == []})
    return rows


def packet_inventory_matrix() -> list[dict]:
    rows = []
    base = retrieve(
        gateway(), request("What nutrition guidance applies at week 24?", "nutrition"),
        "public_guidance",
    ).packet.model_dump(mode="python")
    mutations = [
        ("remove_evidence_ids", lambda p: p.update({"evidence_ids": []})),
        ("remove_source_ids", lambda p: p.update({"source_ids": []})),
        ("remove_exact_spans", lambda p: p.update({"exact_spans": []})),
        ("remove_required_citations", lambda p: p.update({"required_citations": []})),
        ("remove_allowed_claim_types", lambda p: p.update({"allowed_claim_types": []})),
        ("remove_ranked_candidates", lambda p: p.update({"ranked_candidates": []})),
        ("remove_selected_passages", lambda p: p.update({"approved_guideline_passages": []})),
        ("wrong_corpus_mode", lambda p: p.update({"corpus_mode": "production_release"})),
        ("wrong_domain", lambda p: p["approved_guideline_passages"][0].update({"domain": "movement"})),
        ("wrong_week", lambda p: p["approved_guideline_passages"][0].update({"journey": {"stage": "pregnancy", "unit": "week", "exact": 25, "range_start": None, "range_end": None}})),
        ("wrong_jurisdiction", lambda p: p["approved_guideline_passages"][0].update({"jurisdictions": ["US"]})),
        ("wrong_condition", lambda p: p["approved_guideline_passages"][0].update({"conditions_required": ["home_birth"]})),
        ("wrong_lane", lambda p: (p.update({"evidence_lanes": ["guideline"]}), p["approved_guideline_passages"][0].update({"evidence_lane": "weekly_profile"}))),
        ("wrong_span_hash", lambda p: p["approved_guideline_passages"][0]["spans"][0].update({"text_sha256": "0" * 64})),
        ("wrong_span_source", lambda p: p["approved_guideline_passages"][0]["spans"][0].update({"source_id": "OTHER"})),
        ("wrong_span_evidence", lambda p: p["approved_guideline_passages"][0]["spans"][0].update({"evidence_id": "OTHER"})),
        ("missing_display_permission", lambda p: p["approved_guideline_passages"][0].update({"allowed_use": ["store", "embed"]})),
        ("candidate_ranking_authority", lambda p: p["approved_guideline_passages"][0].update({"authority_score": 0.1})),
        ("ranked_source_version", lambda p: p["ranked_candidates"][0].update({"source_version": "wrong"})),
        ("component_rank_score_keys", lambda p: p["ranked_candidates"][0]["component_scores"].update({"fabricated": 1.0})),
    ]
    for name, mutate in mutations:
        payload = deepcopy(base); mutate(payload)
        rows.append({"kind": "packet_inventory", "case": name,
                     "passed": _rejected(EvidencePacket, payload)})
    expanded = retrieve(
        gateway(expanded_fixture()),
        request("What nutrition guidance applies at week 24?", "nutrition", max_candidates=5),
        "public_guidance",
    ).packet.model_dump(mode="python")
    rank_mutations = [
        ("duplicate_rank", lambda p: p["ranked_candidates"][1].update({"rank": 1})),
        ("wrong_kind", lambda p: p["ranked_candidates"][0].update({"candidate_kind": "personal_passage"})),
        ("wrong_tie_breaker", lambda p: p["ranked_candidates"][0].update({"stable_tie_breaker": "OTHER"})),
    ]
    for name, mutate in rank_mutations:
        payload = deepcopy(expanded); mutate(payload)
        rows.append({"kind": "ranking_inventory", "case": name,
                     "passed": _rejected(EvidencePacket, payload)})
    personal = retrieve(
        gateway(), request("What allergies are in my record?", "nutrition"),
        "personal_record_lookup",
    ).packet.model_dump(mode="python")
    personal["permitted_personal_passages"][0]["span"]["text_sha256"] = "0" * 64
    rows.append({"kind": "personal_inventory", "case": "personal_span_hash",
                 "passed": _rejected(EvidencePacket, personal)})

    weekly = deepcopy(base)
    weekly["weekly_profile"] = {
        "profile_id": "P24-FIXTURE",
        "release_id": "55555555-5555-4555-8555-555555555555",
        "corpus_version": "stage5-fixture-v2",
        "journey": {"stage": "pregnancy", "unit": "week", "exact": 24,
                    "range_start": None, "range_end": None},
        "jurisdiction": ["IN"], "hero": {"title": "fixture"},
        "card_slots": {}, "evidence_ids": [], "status": "published",
        "fixture_only": True,
    }
    weekly["allowed_claim_types"].append("published_weekly_profile")
    try:
        EvidencePacket.model_validate_json(json.dumps(weekly, default=str))
        weekly_valid = True
    except ValidationError:
        weekly_valid = False
    rows.append({"kind": "weekly_profile", "case": "valid_fixture",
                 "passed": weekly_valid})
    wrong_weekly = deepcopy(weekly)
    wrong_weekly["weekly_profile"]["jurisdiction"] = ["US"]
    rows.append({"kind": "weekly_profile", "case": "wrong_jurisdiction",
                 "passed": _rejected(EvidencePacket, wrong_weekly)})
    return rows


def graph_trace_failure_matrix() -> list[dict]:
    rows = []
    graph_result = retrieve(
        gateway(), request("Why is my movement plan stale after the restriction?", "movement"),
        "causal_explanation",
    )
    graph_mutations = [
        ("wrong_workspace", lambda p: p["graph_paths"][0].update({"workspace_id": UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")})),
        ("disconnected_edge", lambda p: p["graph_paths"][0]["edges"][0].update({"to_node_id": uuid4()})),
        ("reversed_edge", lambda p: p["graph_paths"][0]["edges"][0].update({"from_node_id": p["graph_paths"][0]["nodes"][1]["node_id"]})),
    ]
    for name, mutate in graph_mutations:
        payload = graph_result.packet.model_dump(mode="python"); mutate(payload)
        rows.append({"kind": "graph", "case": name,
                     "passed": _rejected(EvidencePacket, payload)})
    path = graph_result.packet.graph_paths[0]
    rows.extend([
        {"kind": "graph_bound", "case": "depth", "passed": path.depth <= 4},
        {"kind": "graph_bound", "case": "path_count",
         "passed": len(graph_result.packet.graph_paths) <= 8},
        {"kind": "graph_bound", "case": "adjacent_edges",
         "passed": all(edge.from_node_id == path.nodes[index].node_id
                       and edge.to_node_id == path.nodes[index + 1].node_id
                       for index, edge in enumerate(path.edges))},
    ])
    cycle = retrieve(
        gateway(), request("Why is my plan stale after restriction cycle?", "movement"),
        "causal_explanation",
    ).packet
    rows.append({"kind": "graph_bound", "case": "cycle_excluded",
                 "passed": "DECOY-CYCLE" not in {item.path_id for item in cycle.graph_paths}})

    result = retrieve(
        gateway(), request("What nutrition guidance applies at week 24?", "nutrition"),
        "public_guidance",
    )
    trace_mutations = [
        ("question", lambda p: p["packet"].update({"question": "Different question"})),
        ("normalized_query", lambda p: p["trace"].update({"normalized_query": "different query"})),
        ("jurisdiction", lambda p: p["trace"].update({"jurisdiction": "US"})),
        ("timestamps", lambda p: p["trace"].update({"completed_at": p["trace"]["started_at"] - timedelta(seconds=1)})),
        ("ranking_digest", lambda p: p["trace"].update({"deterministic_order_digest": "0" * 64})),
        ("filter_version", lambda p: p["trace"].update({"filter_version": "wrong"})),
        ("ranking_version", lambda p: p["trace"].update({"ranking_version": "wrong"})),
        ("policy_version", lambda p: p["trace"].update({"policy_version": "wrong"})),
        ("corpus_version", lambda p: p["trace"].update({"corpus_version": "wrong"})),
        ("release_version", lambda p: p["trace"].update({"release_version": "wrong"})),
    ]
    for name, mutate in trace_mutations:
        payload = result.model_dump(mode="python"); mutate(payload)
        rows.append({"kind": "trace", "case": name,
                     "passed": _rejected(RetrievalResult, payload)})

    base = result.model_dump(mode="python")
    payload = deepcopy(base)
    payload["packet"]["component_results"][0].update({"status": "failed", "failure": None})
    payload["trace"]["component_results"] = deepcopy(payload["packet"]["component_results"])
    rows.append({"kind": "component", "case": "failed_without_failure",
                 "passed": _rejected(RetrievalResult, payload)})
    payload = deepcopy(base)
    failure = {"code": "database_unavailable", "recoverable": True,
               "component": "exact_sql", "detail": "synthetic"}
    payload["packet"]["component_results"][0]["failure"] = failure
    payload["packet"]["failures"].append(failure)
    payload["trace"]["component_results"] = deepcopy(payload["packet"]["component_results"])
    rows.append({"kind": "component", "case": "ok_with_failure",
                 "passed": _rejected(RetrievalResult, payload)})
    payload = deepcopy(base)
    payload["packet"]["answerability"]["blocking_reasons"] = ["database_unavailable"]
    rows.append({"kind": "blocker", "case": "database_without_exact_failure",
                 "passed": _rejected(RetrievalResult, payload)})

    payload = deepcopy(base)
    payload["packet"]["component_results"][1].update({
        "status": "degraded", "failure": None, "rejected_by_filters": 0,
    })
    payload["trace"]["component_results"] = deepcopy(payload["packet"]["component_results"])
    rows.append({"kind": "component", "case": "degraded_without_failure_or_filters",
                 "passed": _rejected(RetrievalResult, payload)})

    degraded = retrieve(
        RetrievalGateway(
            FixtureRetrievalRepository(build_fixture()), embedding_provider=None,
            corpus_version="stage5-fixture-v2", release_version="fixture-release-v2",
        ), request("What nutrition guidance applies at week 24?", "nutrition"),
        "public_guidance",
    ).model_dump(mode="python")
    wrong_owner = deepcopy(degraded)
    personal_component = next(
        item for item in wrong_owner["packet"]["component_results"]
        if item["component"] == "personal_vector"
    )
    personal_component["failure"]["component"] = "public_vector"
    wrong_owner["trace"]["component_results"] = deepcopy(
        wrong_owner["packet"]["component_results"]
    )
    rows.append({"kind": "component", "case": "wrong_failure_owner",
                 "passed": _rejected(RetrievalResult, wrong_owner)})
    missing_failure = deepcopy(degraded)
    missing_failure["packet"]["failures"] = []
    rows.append({"kind": "component", "case": "component_failure_missing_from_packet",
                 "passed": _rejected(RetrievalResult, missing_failure)})

    arbitrary = deepcopy(base)
    arbitrary["packet"]["answerability"]["blocking_reasons"] = ["invented_blocker"]
    rows.append({"kind": "blocker", "case": "arbitrary_blocker",
                 "passed": _rejected(RetrievalResult, arbitrary)})

    no_public_request = RetrievalRequest(
        question="What documents should I prepare at week 25?", domain="preparation",
        journey=JourneyPosition(stage="pregnancy", unit="week", exact=25),
        jurisdiction="IN",
    )
    no_public = retrieve(gateway(), no_public_request, "public_guidance").model_dump(mode="python")
    no_public["packet"]["failures"] = [
        item for item in no_public["packet"]["failures"]
        if item["code"] != "no_approved_public_content"
    ]
    rows.append({"kind": "packet_failure", "case": "missing_no_public_failure",
                 "passed": _rejected(RetrievalResult, no_public)})

    class MalformedRepository(FixtureRetrievalRepository):
        def public_full_text(self, requested, limit):
            self._called("public_full_text")
            return [{"not": "a candidate hit"}]
    try:
        retrieve(
            RetrievalGateway(
                MalformedRepository(build_fixture()),
                embedding_provider=DeterministicTestEmbeddingProvider(),
                corpus_version="stage5-fixture-v2", release_version="fixture-release-v2",
            ), request("What nutrition guidance applies at week 24?", "nutrition"),
            "public_guidance",
        )
        malformed_rejected = False
    except RetrievalInvalidCandidate:
        malformed_rejected = True
    rows.append({"kind": "malformed_candidate", "case": "wrong_repository_shape",
                 "passed": malformed_rejected})
    return rows


def valid_policy_packet_matrix() -> list[dict]:
    rows = []
    cases = [
        ("public_guidance", request("What nutrition guidance applies at week 24?", "nutrition")),
        ("personal_record_lookup", request("What allergies are in my record?", "nutrition")),
        ("causal_explanation", request("Why is my movement plan stale after the restriction?", "movement")),
        ("mixed_personalized_guidance", request("How should my allergy affect week 24 nutrition guidance?", "nutrition")),
    ]
    for purpose, req in cases:
        result = retrieve(gateway(), req, purpose)
        try:
            RetrievalResult.model_validate_json(result.model_dump_json())
            accepted = True
        except ValidationError:
            accepted = False
        rows.append({"kind": "valid_policy_packet", "case": purpose,
                     "passed": accepted})
    return rows

def run(write_report: bool = False) -> dict:
    cache = cache_matrix()
    policies = policy_rejections()
    contracts = contract_mutations()
    conflicts = relevance_matrix("conflict")
    missing = relevance_matrix("missing")
    answerability = final_answerability_matrix()
    journey = journey_semantic_matrix()
    pairwise_conflicts = pairwise_relevance_matrix("conflict")
    pairwise_missing = pairwise_relevance_matrix("missing")
    inventory = packet_inventory_matrix()
    graph_trace_failure = graph_trace_failure_matrix()
    valid_packets = valid_policy_packet_matrix()
    checks = {
        "cache_equivalence": {"numerator": sum(row["equivalent"] for row in cache), "denominator": len(cache)},
        "policy_rejections": {"numerator": sum(row["rejected"] for row in policies), "denominator": len(policies)},
        "contract_mutation_rejections": {"numerator": sum(row["rejected"] for row in contracts), "denominator": len(contracts)},
        "generic_conflict_relevance": {"numerator": sum(row["passed"] for row in conflicts), "denominator": len(conflicts)},
        "generic_missing_relevance": {"numerator": sum(row["passed"] for row in missing), "denominator": len(missing)},
        "final_answerability_semantics": {"numerator": sum(row["passed"] for row in answerability), "denominator": len(answerability)},
        "trusted_journey_semantics": {"numerator": sum(row["passed"] for row in journey), "denominator": len(journey)},
        "pairwise_conflict_relevance": {"numerator": sum(row["passed"] for row in pairwise_conflicts), "denominator": len(pairwise_conflicts)},
        "pairwise_missing_relevance": {"numerator": sum(row["passed"] for row in pairwise_missing), "denominator": len(pairwise_missing)},
        "packet_inventory_applicability": {"numerator": sum(row["passed"] for row in inventory), "denominator": len(inventory)},
        "graph_trace_failure_semantics": {"numerator": sum(row["passed"] for row in graph_trace_failure), "denominator": len(graph_trace_failure)},
        "valid_policy_packets": {"numerator": sum(row["passed"] for row in valid_packets), "denominator": len(valid_packets)},
    }
    valid = all(value["numerator"] == value["denominator"] for value in checks.values())
    report = {
        "schema_version": "stage5-rectification-matrix-v2",
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
            "final_answerability": answerability,
            "trusted_journey": journey,
            "pairwise_conflicts": pairwise_conflicts,
            "pairwise_missing_information": pairwise_missing,
            "packet_inventory_applicability": inventory,
            "graph_trace_failure_semantics": graph_trace_failure,
            "valid_policy_packets": valid_packets,
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