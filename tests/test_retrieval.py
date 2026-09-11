"""Stage 5 contracts, answerability, security, graph, cache, and regression tests."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import time
import unittest
from uuid import UUID, uuid4

from pydantic import ValidationError

from app.schemas.retrieval import (
    AuthenticatedRetrievalScope, EvidencePacket, EvidenceRequirementPolicy,
    JourneyPosition, PublicEvidenceCandidate, RetrievalRequest, RetrievalResult,
    RerankerInput, TrustedRetrievalState, canonical_evidence_policy_values,
)
from app.services.embeddings import DeterministicTestEmbeddingProvider
from app.services.retrieval import (
    CandidateHit, FixtureRetrievalRepository, PersonalCacheEntry,
    RetrievalDatabaseUnavailable, RetrievalGateway, RetrievalInvalidCandidate,
    Stage5RetrievalCache,
)
from app.services.retrieval_policy import build_evidence_policy, build_trusted_query

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "data/synthetic/stage5_retrieval_fixtures.json"
OWNER_A = UUID("11111111-1111-4111-8111-111111111111")
OWNER_B = UUID("22222222-2222-4222-8222-222222222222")
WORKSPACE_A = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
WORKSPACE_B = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
OWNER_F = UUID("66666666-6666-4666-8666-666666666666")
WORKSPACE_F = UUID("ffffffff-ffff-4fff-8fff-ffffffffffff")
RESTRICTION = "a2222222-2222-4222-8222-222222222222"
ALLERGY = "a1111111-1111-4111-8111-111111111111"


def fixture():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def scope(workspace=WORKSPACE_A, owner=OWNER_A, version=3):
    return AuthenticatedRetrievalScope(
        workspace_id=workspace, care_episode_id=workspace,
        owner_user_id=owner, session_subject=owner, state_version=version,
        authenticated_at=datetime.now(timezone.utc))


def request(question="What protein foods matter at week 24?", domain="nutrition",
            week=24, graph=True, timeout_ms=2000, max_candidates=5, *,
            stage="pregnancy", unit="week"):
    journey = (JourneyPosition(stage="possible_pregnancy", unit="none")
               if stage == "possible_pregnancy"
               else JourneyPosition(stage=stage, unit=unit, exact=week))
    return RetrievalRequest(
        question=question, domain=domain, journey=journey,
        jurisdiction="IN", include_graph=graph, timeout_ms=timeout_ms,
        max_candidates=max_candidates)


def gateway(payload=None, *, provider=True, cache=None, improvement=False):
    return RetrievalGateway(
        FixtureRetrievalRepository(payload or fixture()),
        embedding_provider=(DeterministicTestEmbeddingProvider()
                            if provider else None),
        cache=cache, corpus_version="stage5-fixture-v2",
        release_version="fixture-release-v2",
        apply_ranking_improvement=improvement)


def retrieve(service, req, auth_scope=None, purpose="public_guidance"):
    return service.retrieve(
        req, auth_scope or scope(), purpose=purpose)


def trusted_query(req, auth_scope=None, purpose="public_guidance"):
    auth_scope = auth_scope or scope()
    repo = FixtureRetrievalRepository(fixture())
    resolved = repo.authenticated_scope(auth_scope)
    exact = repo.exact_personal_context(resolved, req)
    return build_trusted_query(
        req, auth_scope, resolved, exact,
        build_evidence_policy(purpose, req.domain))[1]


def semantic_result(result):
    """Fields that must be invariant between cached and fresh retrieval."""

    packet = result.packet
    return {
        "evidence": [item.evidence_id for item in packet.approved_guideline_passages],
        "facts": [str(item.fact_id) for item in packet.confirmed_personal_facts],
        "passages": [item.candidate_id for item in packet.permitted_personal_passages],
        "paths": [item.path_id for item in packet.graph_paths],
        "conflicts": [str(item.conflict_id) for item in packet.unresolved_conflicts],
        "missing": [item.field for item in packet.missing_information],
        "support": packet.answerability.support_state,
        "generation_allowed": packet.answerability.ordinary_generation_allowed,
        "abstain": packet.abstention.should_abstain,
        "abstention_reason": packet.abstention.reason,
        "citations": packet.required_citations,
        "policy_id": packet.retrieval_policy.policy_id,
        "resolved_state_version": result.trace.resolved_state_version,
    }


def expanded_candidate_fixture():
    """Controlled corpus with five eligible public and private candidates."""

    payload = fixture()
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
        text = (f"Maya fictional record {index} states a confirmed "
                "peanut allergy.")
        candidate["candidate_id"] = f"personal-allergy-extra-{index}"
        candidate["chunk_id"] = f"b100000{index}-1111-4111-8111-111111111111"
        candidate["document_id"] = f"d100000{index}-1111-4111-8111-111111111111"
        candidate["text"] = text
        candidate["span"].update({
            "source_id": f"private:{candidate['document_id']}",
            "exact_text": text, "end_char": len(text),
            "text_sha256": sha256(text.encode()).hexdigest(),
        })
        payload["personal_passages"].append(row)
    return payload


def payload_with_issue(kind, fact_type, values, *, identifier):
    payload = fixture()
    context = payload["personal_contexts"][str(WORKSPACE_A)]
    if kind == "conflict":
        context["unresolved_conflicts"].append({
            "conflict_id": identifier, "fact_type": fact_type,
            "proposed_values": values, "source_document_ids": [],
            "clarification_question_ids": [], "state": "requires_clarification",
        })
    else:
        context["missing_information"].append({
            "field": fact_type, "reason": "Required fictional detail is missing.",
            "required_for": [fact_type],
        })
    return payload


class Stage5ContractTests(unittest.TestCase):
    def test_request_rejects_user_workspace_state_conditions_and_purpose(self):
        for field, value in (
            ("workspace_id", str(WORKSPACE_B)), ("state_version", 999),
            ("active_conditions", ["pregnancy_confirmed"]),
            ("purpose", "personal_record_lookup"),
        ):
            payload = request().model_dump(mode="json")
            payload[field] = value
            with self.subTest(field=field), self.assertRaises(ValidationError):
                RetrievalRequest.model_validate(payload)

    def test_authenticated_scope_requires_session_owner(self):
        with self.assertRaises(ValidationError):
            AuthenticatedRetrievalScope(
                workspace_id=WORKSPACE_A, care_episode_id=WORKSPACE_A,
                owner_user_id=OWNER_A, session_subject=OWNER_B,
                state_version=1, authenticated_at=datetime.now(timezone.utc))

    def test_owner_only_care_episode_boundary_is_explicit(self):
        with self.assertRaises(ValidationError):
            AuthenticatedRetrievalScope(
                workspace_id=WORKSPACE_A, care_episode_id=WORKSPACE_B,
                owner_user_id=OWNER_A, session_subject=OWNER_A,
                state_version=1, authenticated_at=datetime.now(timezone.utc))

    def test_malformed_journey_request_fails_typed_validation(self):
        with self.assertRaises(ValidationError):
            JourneyPosition(stage="pregnancy", unit="week", exact=24,
                            range_start=23, range_end=25)

    def test_learned_reranker_cannot_be_enabled(self):
        with self.assertRaises(ValidationError):
            RerankerInput(request_id=request().request_id,
                          question="fixture", candidates=[],
                          learned_reranker_enabled=True)

    def test_inconsistent_and_fabricated_policies_are_rejected(self):
        baseline = canonical_evidence_policy_values(
            "public_guidance", "nutrition"
        )
        mutations = [
            {"required_support": ["personal_constraint"]},
            {"purpose": "personal_record_lookup",
             "required_support": ["public_guidance"]},
            {"purpose": "causal_explanation",
             "required_support": ["personal_record"]},
            {"purpose": "mixed_personalized_guidance",
             "required_support": ["public_guidance"]},
            {"domain": "movement"},
            {"policy_id": "fabricated-policy"},
            {"policy_version": "stage5-answerability-v2"},
            {"required_support": ["public_guidance", "personal_record"]},
            {"personal_context_kinds": ["allergies"]},
        ]
        for mutation in mutations:
            payload = {**baseline, **mutation}
            with self.subTest(mutation=mutation), self.assertRaises(ValidationError):
                EvidenceRequirementPolicy.model_validate(payload)

    def test_gateway_does_not_accept_caller_constructed_policy(self):
        service = gateway()
        policy = build_evidence_policy("public_guidance", "nutrition")
        with self.assertRaises(TypeError):
            service.retrieve(request(), scope(), policy=policy)
        self.assertEqual(service.repository.call_counts, {})

    def test_evidence_packet_rejects_cross_field_mutations(self):
        base = retrieve(
            gateway(), request("What allergy is in my confirmed record?"),
            purpose="personal_record_lookup",
        ).packet.model_dump(mode="python")

        def reject(label, mutate):
            payload = deepcopy(base)
            mutate(payload)
            with self.subTest(label=label), self.assertRaises(ValidationError):
                EvidencePacket.model_validate(payload)

        def incomplete(payload, state):
            answer = payload["answerability"]
            answer.update({
                "support_state": state, "ordinary_generation_allowed": False,
                "satisfied_support": [],
                "missing_support": list(answer["required_support"]),
            })

        for state in ("unsupported", "partially_supported",
                      "clarification_required"):
            reject(f"{state}_without_abstention",
                   lambda payload, state=state: incomplete(payload, state))
        reject("generation_and_abstention_both_true", lambda payload: (
            payload["abstention"].update({
                "should_abstain": True, "reason": "partial_support"
            })
        ))
        reject("answerability_policy_id", lambda payload: (
            payload["answerability"].update({"policy_id": "wrong"})
        ))
        reject("answerability_purpose", lambda payload: (
            payload["answerability"].update({"purpose": "public_guidance"})
        ))
        reject("answerability_required_support", lambda payload: (
            payload["answerability"].update({
                "required_support": ["public_guidance"],
                "satisfied_support": ["public_guidance"],
            })
        ))
        reject("packet_domain", lambda payload: payload.update({"domain": "movement"}))
        reject("packet_journey", lambda payload: payload.update({
            "journey": JourneyPosition(
                stage="pregnancy", unit="week", exact=25
            ).model_dump(mode="python")
        }))
        reject("packet_workspace", lambda payload: payload.update({
            "workspace_id": WORKSPACE_B
        }))
        reject("packet_care_episode", lambda payload: payload.update({
            "care_episode_id": WORKSPACE_B
        }))
        reject("packet_conflicts", lambda payload: payload.update({
            "unresolved_conflicts": [{
                "conflict_id": UUID("c7777777-7777-4777-8777-777777777777"),
                "fact_type": "allergy", "proposed_values": ["x"],
                "source_document_ids": [], "clarification_question_ids": [],
                "state": "requires_clarification",
            }]
        }))

    def test_retrieval_result_rejects_packet_trace_mutations(self):
        result = retrieve(gateway(), request())
        base = result.model_dump(mode="python")

        def reject(label, mutate):
            payload = deepcopy(base)
            mutate(payload)
            with self.subTest(label=label), self.assertRaises(ValidationError):
                RetrievalResult.model_validate(payload)

        reject("request_id", lambda payload: payload["trace"].update({
            "request_id": uuid4()
        }))
        reject("policy_id", lambda payload: payload["trace"].update({
            "policy_id": "wrong"
        }))
        reject("journey_relation", lambda payload: payload["trace"].update({
            "journey_relation": "explicit_other"
        }))
        reject("state_version", lambda payload: payload["trace"].update({
            "resolved_state_version": 99
        }))
        reject("component_results", lambda payload: payload["trace"].update({
            "component_results": payload["trace"]["component_results"][:-1]
        }))


class Stage5AnswerabilityAndSafetyTests(unittest.TestCase):
    def test_expected_public_evidence_survives_hard_filters(self):
        packet = retrieve(gateway(), request()).packet
        self.assertIn("EV-NUT-24", packet.evidence_ids)
        self.assertFalse(packet.abstention.should_abstain)

    def test_wrong_week_jurisdiction_lifecycle_and_stage_decoys_are_excluded(self):
        packet = retrieve(gateway(), request()).packet
        forbidden = {"EV-DECOY-WEEK-12", "EV-DECOY-US-24",
                     "EV-DECOY-POSTPARTUM", "EV-DECOY-DRAFT",
                     "EV-DECOY-REJECTED", "EV-DECOY-RETIRED"}
        self.assertTrue(forbidden.isdisjoint(packet.evidence_ids))

    def test_reported_public_guidance_defect_now_abstains(self):
        req = request("What hospital documents and finances should I prepare at week 25?", "preparation", 25)
        packet = retrieve(gateway(), req).packet
        self.assertTrue(packet.abstention.should_abstain)
        self.assertEqual(packet.abstention.reason, "no_approved_public_content")
        self.assertEqual(packet.answerability.support_state, "unsupported")
        self.assertEqual(packet.confirmed_personal_facts, [])
        self.assertEqual(packet.permitted_personal_passages, [])

    def test_personal_record_lookup_does_not_require_public_guidance(self):
        req = request("What allergy is in my confirmed record?")
        packet = retrieve(gateway(), req, purpose="personal_record_lookup").packet
        self.assertFalse(packet.abstention.should_abstain)
        self.assertEqual(packet.answerability.support_state, "fully_supported")
        self.assertEqual({str(item.fact_id) for item in packet.confirmed_personal_facts}, {ALLERGY})
        self.assertEqual(packet.approved_guideline_passages, [])

    def test_partial_mixed_support_abstains(self):
        req = request("How should my peanut allergy change week 25 nutrition guidance?", week=25)
        packet = retrieve(gateway(), req, purpose="mixed_personalized_guidance").packet
        self.assertEqual(packet.answerability.support_state, "partially_supported")
        self.assertEqual(packet.abstention.reason, "partial_support")

    def test_reported_relevant_conflict_defect_now_requires_clarification(self):
        req = request("How should my conflicting prenatal yoga record affect week 25 movement guidance?", "movement", 25)
        packet = retrieve(
            gateway(), req, scope(WORKSPACE_F, OWNER_F, 1),
            purpose="mixed_personalized_guidance",
        ).packet
        self.assertEqual(packet.answerability.support_state, "clarification_required")
        self.assertEqual(packet.abstention.reason, "unresolved_conflict")
        self.assertTrue(packet.unresolved_conflicts)
        self.assertEqual(packet.permitted_personal_passages, [])

    def test_irrelevant_conflict_does_not_block_supported_nutrition(self):
        packet = retrieve(
            gateway(), request(), scope(WORKSPACE_F, OWNER_F, 1)
        ).packet
        self.assertFalse(packet.abstention.should_abstain)
        self.assertEqual(packet.unresolved_conflicts, [])

    def test_required_missing_information_requires_clarification(self):
        req = request("What should I prepare now?", "preparation")
        packet = retrieve(gateway(), req, scope(WORKSPACE_B, OWNER_B, 999)).packet
        self.assertEqual(packet.abstention.reason, "missing_information")
        self.assertEqual(packet.approved_guideline_passages, [])

    def test_generic_personal_categories_surface_relevant_conflicts(self):
        cases = [
            ("allergy", [{"substance": "sesame"}],
             "What allergies are in my record?", "nutrition"),
            ("dietary_restriction", [{"restriction": "avoid lifting"}],
             "What restrictions are in my record?", "movement"),
            ("medication", [{"name": "fictional tablet"}],
             "What medications are in my record?", "followup"),
            ("medical_history", [{"condition": "fictional condition"}],
             "What conditions are in my record?", "wellbeing"),
            ("appointment", [{"date": "2026-10-01"}],
             "What appointments are in my record?", "preparation"),
            ("journey_state", [{"week": 23}, {"week": 24}],
             "What week am I in?", "journey"),
        ]
        for index, (fact_type, values, question, domain) in enumerate(cases, 1):
            conflict_id = f"c700000{index}-7777-4777-8777-777777777777"
            packet = retrieve(
                gateway(payload_with_issue(
                    "conflict", fact_type, values, identifier=conflict_id
                )),
                request(question, domain), purpose="personal_record_lookup",
            ).packet
            with self.subTest(fact_type=fact_type):
                self.assertEqual(
                    [str(item.conflict_id) for item in packet.unresolved_conflicts],
                    [conflict_id],
                )
                self.assertEqual(
                    packet.answerability.support_state, "clarification_required"
                )
                self.assertEqual(packet.abstention.reason, "unresolved_conflict")

    def test_named_value_and_explicit_conflict_are_relevant(self):
        payload = payload_with_issue(
            "conflict", "allergy",
            [{"substance": "sesame"}, {"substance": "tree nut"}],
            identifier="c7111111-7777-4777-8777-777777777777",
        )
        questions = ["Is sesame in my record?",
                     "Is there an allergy conflict in my record?"]
        for question in questions:
            packet = retrieve(
                gateway(payload), request(question),
                purpose="personal_record_lookup",
            ).packet
            with self.subTest(question=question):
                self.assertEqual(packet.abstention.reason, "unresolved_conflict")

    def test_generic_categories_surface_required_missing_information(self):
        cases = [
            ("allergy_detail", "What allergies are in my record?", "nutrition"),
            ("dietary_restriction", "What restrictions are in my record?", "movement"),
            ("medication_list", "What medications are in my record?", "followup"),
            ("medical_condition", "What conditions are in my record?", "wellbeing"),
            ("appointment_date", "What appointments are in my record?", "preparation"),
            ("journey_week", "What week am I in?", "journey"),
        ]
        for index, (field, question, domain) in enumerate(cases, 1):
            packet = retrieve(
                gateway(payload_with_issue(
                    "missing", field, [], identifier=f"missing-{index}"
                )),
                request(question, domain), purpose="personal_record_lookup",
            ).packet
            with self.subTest(field=field):
                self.assertEqual([item.field for item in packet.missing_information],
                                 [field])
                self.assertEqual(
                    packet.answerability.support_state, "clarification_required"
                )
                self.assertEqual(packet.abstention.reason, "missing_information")

    def test_unrelated_category_conflicts_do_not_block_supported_guidance(self):
        movement_payload = payload_with_issue(
            "conflict", "appointment", [{"date": "2026-10-01"}],
            identifier="c7222222-7777-4777-8777-777777777777",
        )
        movement = retrieve(
            gateway(movement_payload),
            request("What movement guidance applies at week 24?", "movement"),
        ).packet
        self.assertFalse(movement.abstention.should_abstain)
        self.assertEqual(movement.unresolved_conflicts, [])

        missing_payload = payload_with_issue(
            "missing", "appointment_date", [], identifier="missing-appointment"
        )
        movement_with_unrelated_missing = retrieve(
            gateway(missing_payload),
            request("What movement guidance applies at week 24?", "movement"),
        ).packet
        self.assertFalse(movement_with_unrelated_missing.abstention.should_abstain)
        self.assertEqual(movement_with_unrelated_missing.missing_information, [])

    def test_proposed_conflicted_and_superseded_facts_do_not_personalize(self):
        packet = retrieve(gateway(), request()).packet
        values = {str(item.fact_id) for item in packet.confirmed_personal_facts}
        forbidden = {"a3333333-3333-4333-8333-333333333333",
                     "a4444444-4444-4444-8444-444444444444",
                     "a5555555-5555-4555-8555-555555555555"}
        self.assertTrue(values.isdisjoint(forbidden))

    def test_medication_remains_record_only_and_minimized(self):
        req = request("What medication is in my confirmed record?", "followup")
        packet = retrieve(gateway(), req, purpose="personal_record_lookup").packet
        self.assertTrue(packet.medication_records)
        self.assertTrue(all(item.record_only for item in packet.medication_records))
        self.assertIn("record_only_medication", packet.allowed_claim_types)
        self.assertEqual(packet.confirmed_personal_facts, [])

    def test_symptom_no_match_is_evaluation_only_not_safe(self):
        req = request("What symptom is in my record?", "symptoms")
        packet = retrieve(gateway(), req, purpose="personal_record_lookup").packet
        self.assertEqual(packet.symptom_records[0].safety_route, "no_match")
        self.assertTrue(packet.symptom_records[0].safety_evaluation_only)
        self.assertNotIn("safe", packet.allowed_claim_types)

    def test_unrelated_personal_records_are_minimized(self):
        packet = retrieve(gateway(), request()).packet
        self.assertEqual(packet.medication_records, [])
        self.assertEqual(packet.symptom_records, [])
        self.assertEqual(packet.appointments, [])
        self.assertEqual(packet.plan_states, [])

    def test_cross_workspace_sql_and_vector_results_never_escape(self):
        req = request("What allergy is confirmed?")
        packet = retrieve(gateway(), req, scope(WORKSPACE_B, OWNER_B), "personal_record_lookup").packet
        self.assertEqual(packet.confirmed_personal_facts, [])
        self.assertNotIn("personal-b1111111-1111-4111-8111-111111111111",
                         {item.candidate_id for item in packet.permitted_personal_passages})

    def test_condition_positive_and_negative_filters(self):
        req = request("What movement guidance applies with my restriction?", "movement")
        packet = retrieve(gateway(), req).packet
        self.assertIn("EV-COND-POS", packet.evidence_ids)
        self.assertNotIn("EV-DECOY-COND-MISSING", packet.evidence_ids)
        self.assertNotIn("EV-DECOY-COND-EXCLUDED", packet.evidence_ids)
        self.assertEqual(packet.trusted_state.active_conditions,
                         ["movement_restriction", "pregnancy_confirmed"])

    def test_current_week_mismatch_is_overridden_from_confirmed_state(self):
        req = request("What nutrition guidance applies to me now?", week=12)
        result = retrieve(gateway(), req)
        self.assertEqual(result.trace.journey_relation, "overridden_to_current")
        self.assertEqual(result.packet.journey.exact, 24)
        self.assertIn("EV-NUT-24", result.packet.evidence_ids)

    def test_explicit_future_week_is_preserved(self):
        req = request("What should I prepare at week 30?", "preparation", 30)
        result = retrieve(gateway(), req)
        self.assertEqual(result.trace.journey_relation, "explicit_other")
        self.assertIn("EV-PREP-30", result.packet.evidence_ids)

    def test_possible_pregnancy_and_postpartum_applicability(self):
        cases = [
            (UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc"), UUID("33333333-3333-4333-8333-333333333333"), request("What follow-up applies during possible pregnancy?", "followup", stage="possible_pregnancy", unit="none"), "EV-POSSIBLE"),
            (UUID("dddddddd-dddd-4ddd-8ddd-dddddddddddd"), UUID("44444444-4444-4444-8444-444444444444"), request("What should I prepare at postpartum day 3?", "preparation", 3, stage="postpartum", unit="day"), "EV-PP-DAY3"),
            (UUID("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"), UUID("55555555-5555-4555-8555-555555555555"), request("What wellbeing applies at postpartum week 6?", "wellbeing", 6, stage="postpartum", unit="week"), "EV-PP-WEEK6"),
        ]
        for workspace, owner, req, evidence in cases:
            with self.subTest(evidence=evidence):
                packet = retrieve(gateway(), req, scope(workspace, owner, 99)).packet
                self.assertIn(evidence, packet.evidence_ids)

    def test_every_planned_domain_has_a_supported_case(self):
        mapping = {"journey": "EV-JOURNEY-24", "nutrition": "EV-NUT-24",
                   "movement": "EV-MOVE-24", "wellbeing": "EV-WELL-24",
                   "symptoms": "EV-SYM-24", "preparation": "EV-PREP-24",
                   "followup": "EV-FOLLOW-24"}
        for domain, evidence in mapping.items():
            with self.subTest(domain=domain):
                packet = retrieve(gateway(), request(
                    f"What {domain} guidance applies at week 24?", domain)).packet
                self.assertIn(evidence, packet.evidence_ids)


class Stage5GraphAndRankingTests(unittest.TestCase):
    def test_graph_adds_required_document_restriction_plan_path(self):
        req = request("Why is my movement plan stale after the restriction?", "movement")
        packet = retrieve(gateway(), req, purpose="causal_explanation").packet
        path = {item.path_id: item for item in packet.graph_paths}[
            "PATH-DOC-RESTRICTION-STALE-PLAN"]
        self.assertEqual([node.node_type for node in path.nodes],
                         ["document", "restriction", "plan_item", "plan"])
        self.assertEqual(path.depth, 3)
        self.assertFalse(packet.abstention.should_abstain)

    def test_graph_off_requires_abstention_but_sql_lookup_does_not(self):
        graph_req = request("Why is my movement plan stale after the restriction?", "movement", graph=False)
        graph_packet = retrieve(gateway(), graph_req, purpose="causal_explanation").packet
        self.assertEqual(graph_packet.abstention.reason, "no_eligible_evidence")
        sql_req = request("What allergy is in my confirmed record?", graph=False)
        sql_packet = retrieve(gateway(), sql_req, purpose="personal_record_lookup").packet
        self.assertFalse(sql_packet.abstention.should_abstain)

    def test_cycle_and_bounds_are_enforced(self):
        req = request("Why is my plan stale after restriction cycle?", "movement")
        packet = retrieve(gateway(), req, purpose="causal_explanation").packet
        self.assertNotIn("DECOY-CYCLE", {item.path_id for item in packet.graph_paths})
        self.assertLessEqual(len(packet.graph_paths), 8)
        self.assertTrue(all(item.depth <= 4 for item in packet.graph_paths))

    def test_duplicate_component_candidates_have_stable_order(self):
        first = retrieve(gateway(), request()).trace
        second = retrieve(gateway(), request()).trace
        self.assertEqual(first.deterministic_order_digest,
                         second.deterministic_order_digest)

    def test_wrong_week_candidate_is_retried_once_then_rejected(self):
        data = fixture()
        raw = next(item for item in data["public_records"]
                   if item["candidate"]["evidence_id"] == "EV-DECOY-WEEK-12")
        candidate = PublicEvidenceCandidate.model_validate_json(json.dumps(raw["candidate"]))
        class WrongWeekRepository(FixtureRetrievalRepository):
            def public_full_text(self, request, limit):
                self._called("public_full_text")
                return [CandidateHit(candidate, 1.0)]
        repo = WrongWeekRepository(data)
        service = RetrievalGateway(repo, embedding_provider=None,
                                   corpus_version="fixture",
                                   release_version="fixture")
        result = retrieve(service, request())
        component = next(item for item in result.trace.component_results
                         if item.component == "public_full_text")
        self.assertEqual(component.retries, 1)
        self.assertEqual(repo.call_counts["public_full_text"], 2)
        self.assertNotIn("EV-DECOY-WEEK-12", result.packet.evidence_ids)


class Stage5CacheAndFailureTests(unittest.TestCase):
    def test_personal_cache_uses_resolved_database_state_version(self):
        req = request()
        current = retrieve(gateway(), req, scope(version=3)).trace
        stale = retrieve(gateway(), req, scope(version=999)).trace
        self.assertEqual(current.personal_cache_key, stale.personal_cache_key)
        self.assertEqual(stale.resolved_state_version, 3)

    def test_personal_cache_keys_are_workspace_and_state_isolated(self):
        cache = Stage5RetrievalCache()
        req = request()
        query_a = trusted_query(req, scope())
        query_b = trusted_query(req, scope(WORKSPACE_B, OWNER_B, 2))
        self.assertNotEqual(cache.personal_key(scope(), query_a),
                            cache.personal_key(scope(WORKSPACE_B, OWNER_B, 2), query_b))
        changed = scope(version=4)
        self.assertNotEqual(cache.personal_key(scope(), query_a),
                            cache.personal_key(changed, query_a))

    def test_release_and_filter_versions_invalidate_public_key(self):
        cache, query = Stage5RetrievalCache(), trusted_query(request())
        keys = {
            cache.public_key(query, corpus_version="c1", release_version="r1"),
            cache.public_key(query, corpus_version="c1", release_version="r2"),
            cache.public_key(query, corpus_version="c1", release_version="r1", filter_version="stage5-filter-v2"),
        }
        self.assertEqual(len(keys), 3)

    def test_public_cache_rejects_personal_entry(self):
        cache = Stage5RetrievalCache()
        with self.assertRaises(TypeError):
            cache.put_public("public:x", PersonalCacheEntry(
                WORKSPACE_A, WORKSPACE_A, 1,
                FixtureRetrievalRepository(fixture()).exact_personal_context(scope(), request()),
                [], [], []))

    def test_invalidation_removes_personal_derived_result(self):
        cache, service, req = Stage5RetrievalCache(), None, request()
        service = gateway(cache=cache)
        result = retrieve(service, req)
        self.assertIsNotNone(cache.get_personal(result.trace.personal_cache_key, scope()))
        self.assertEqual(cache.invalidate_personal(WORKSPACE_A), 1)
        self.assertIsNone(cache.get_personal(result.trace.personal_cache_key, scope()))

    def test_shared_cache_is_order_invariant_across_policies(self):
        graph_question = request(
            "Why is my movement plan stale after the restriction?", "movement"
        )
        mixed_question = request(
            "How should my peanut allergy affect week 24 nutrition guidance?"
        )
        rows = [
            ("public_guidance", "causal_explanation", graph_question),
            ("causal_explanation", "public_guidance", graph_question),
            ("personal_record_lookup", "mixed_personalized_guidance",
             mixed_question),
            ("mixed_personalized_guidance", "personal_record_lookup",
             mixed_question),
        ]
        for first_purpose, second_purpose, req in rows:
            cache = Stage5RetrievalCache()
            shared = gateway(cache=cache)
            first = retrieve(shared, req, purpose=first_purpose)
            cached = retrieve(shared, req, purpose=second_purpose)
            fresh = retrieve(gateway(), req, purpose=second_purpose)
            with self.subTest(first=first_purpose, second=second_purpose):
                self.assertEqual(semantic_result(cached), semantic_result(fresh))
                self.assertNotEqual(first.trace.personal_cache_key,
                                    cached.trace.personal_cache_key)

    def test_max_candidate_cache_matrix_is_order_invariant(self):
        payload = expanded_candidate_fixture()
        request_pairs = [
            (request(max_candidates=1), request(max_candidates=5),
             "public_guidance"),
            (request(max_candidates=5), request(max_candidates=1),
             "public_guidance"),
            (request("What allergies are in my confirmed record?",
                     max_candidates=1),
             request("What allergies are in my confirmed record?",
                     max_candidates=5),
             "personal_record_lookup"),
            (request("What allergies are in my confirmed record?",
                     max_candidates=5),
             request("What allergies are in my confirmed record?",
                     max_candidates=1),
             "personal_record_lookup"),
        ]
        for first_req, second_req, purpose in request_pairs:
            cache = Stage5RetrievalCache()
            shared = gateway(payload, cache=cache)
            first = retrieve(shared, first_req, purpose=purpose)
            cached = retrieve(shared, second_req, purpose=purpose)
            fresh = retrieve(gateway(payload), second_req, purpose=purpose)
            with self.subTest(
                purpose=purpose, first=first_req.max_candidates,
                second=second_req.max_candidates,
            ):
                self.assertEqual(semantic_result(cached), semantic_result(fresh))
                self.assertNotEqual(first.trace.public_cache_key,
                                    cached.trace.public_cache_key)
                self.assertNotEqual(first.trace.personal_cache_key,
                                    cached.trace.personal_cache_key)

    def test_shared_cache_uses_server_version_and_invalidates_on_change(self):
        payload = fixture()
        repo = FixtureRetrievalRepository(payload)
        cache = Stage5RetrievalCache()
        service = RetrievalGateway(
            repo, embedding_provider=DeterministicTestEmbeddingProvider(),
            cache=cache, corpus_version="stage5-fixture-v2",
            release_version="fixture-release-v2",
        )
        req = request()
        current = retrieve(service, req, scope(version=3))
        stale_caller = retrieve(service, req, scope(version=999))
        self.assertEqual(current.trace.personal_cache_key,
                         stale_caller.trace.personal_cache_key)
        self.assertEqual(stale_caller.trace.resolved_state_version, 3)

        repo.payload["personal_state_versions"][str(WORKSPACE_A)] = 4
        changed = retrieve(service, req, scope(version=3))
        fresh = retrieve(
            RetrievalGateway(
                FixtureRetrievalRepository(repo.payload),
                embedding_provider=DeterministicTestEmbeddingProvider(),
                corpus_version="stage5-fixture-v2",
                release_version="fixture-release-v2",
            ), req, scope(version=4),
        )
        self.assertNotEqual(current.trace.personal_cache_key,
                            changed.trace.personal_cache_key)
        self.assertEqual(changed.trace.resolved_state_version, 4)
        self.assertEqual(semantic_result(changed), semantic_result(fresh))

    def test_vector_unavailable_is_labeled_and_sql_can_still_answer(self):
        req = request("What allergy is in my confirmed record?")
        packet = retrieve(gateway(provider=False), req, purpose="personal_record_lookup").packet
        self.assertFalse(packet.abstention.should_abstain)
        self.assertIn("vector_unavailable", {item.code for item in packet.failures})

    def test_database_failure_never_claims_personalization(self):
        class BrokenRepository(FixtureRetrievalRepository):
            def authenticated_scope(self, scope):
                raise RetrievalDatabaseUnavailable("fixture outage")
        packet = retrieve(RetrievalGateway(
            BrokenRepository(fixture()),
            embedding_provider=DeterministicTestEmbeddingProvider(),
            corpus_version="fixture", release_version="fixture"),
            request()).packet
        self.assertEqual(packet.confirmed_personal_facts, [])
        self.assertEqual(packet.abstention.reason, "database_unavailable")

    def test_timeout_forces_recoverable_abstention(self):
        class SlowRepository(FixtureRetrievalRepository):
            def exact_personal_context(self, scope, request):
                time.sleep(0.02)
                return super().exact_personal_context(scope, request)
        packet = retrieve(RetrievalGateway(
            SlowRepository(fixture()),
            embedding_provider=DeterministicTestEmbeddingProvider(),
            corpus_version="stage5-fixture-v2",
            release_version="fixture-release-v2"),
            request(timeout_ms=10)).packet
        self.assertEqual(packet.abstention.reason, "retrieval_timeout")
        self.assertIn("retrieval_timeout", packet.answerability.blocking_reasons)


class Stage5FinalSemanticClosureTests(unittest.TestCase):
    """Consolidated adversarial matrix for the final Stage 5 handoff."""

    @staticmethod
    def _json(payload):
        return json.dumps(payload, default=str)

    def _reject_packet(self, payload, label):
        with self.subTest(label=label), self.assertRaises(ValidationError):
            EvidencePacket.model_validate_json(self._json(payload))

    def _reject_result(self, payload, label):
        with self.subTest(label=label), self.assertRaises(ValidationError):
            RetrievalResult.model_validate_json(self._json(payload))

    def test_answerability_and_abstention_are_canonically_derived(self):
        supported = retrieve(gateway(), request()).packet
        partial = retrieve(
            gateway(),
            request("How should my peanut allergy change week 25 nutrition guidance?", week=25),
            purpose="mixed_personalized_guidance",
        ).packet
        unsupported = retrieve(
            gateway(), request("What hospital documents should I prepare at week 25?", "preparation", 25)
        ).packet
        conflicted = retrieve(
            gateway(),
            request("How should my conflicting prenatal yoga record affect week 25 movement guidance?", "movement", 25),
            scope(WORKSPACE_F, OWNER_F, 1),
            "mixed_personalized_guidance",
        ).packet
        self.assertEqual(
            [supported.answerability.support_state, partial.answerability.support_state,
             unsupported.answerability.support_state, conflicted.answerability.support_state],
            ["fully_supported", "partially_supported", "unsupported", "clarification_required"],
        )

        base = supported.model_dump(mode="python")
        mutations = []
        mutations.append(("full_with_missing_support", lambda p: p["answerability"].update({
            "satisfied_support": [], "missing_support": list(p["answerability"]["required_support"]),
        })))
        mutations.append(("satisfied_boolean_false", lambda p: p["answerability"].update({
            "public_guidance_supported": False,
        })))
        def conflict_while_generating(payload):
            identifier = UUID("c7777777-7777-4777-8777-777777777777")
            payload["unresolved_conflicts"] = [{
                "conflict_id": identifier, "fact_type": "allergy",
                "proposed_values": ["sesame"], "source_document_ids": [],
                "clarification_question_ids": [], "state": "requires_clarification",
            }]
            payload["answerability"]["relevant_conflict_ids"] = [str(identifier)]
            payload["allowed_claim_types"].append("clarification_required")
        mutations.append(("generation_with_conflict", conflict_while_generating))
        def clarification_without_issue(payload):
            payload["answerability"].update({
                "support_state": "clarification_required",
                "ordinary_generation_allowed": False,
            })
            payload["abstention"] = {
                "should_abstain": True, "reason": "partial_support", "detail": "invalid",
            }
        mutations.append(("clarification_without_issue", clarification_without_issue))
        for label, mutate in mutations:
            payload = deepcopy(base); mutate(payload); self._reject_packet(payload, label)

        payload = deepcopy(unsupported.model_dump(mode="python"))
        payload["abstention"]["reason"] = "unresolved_conflict"
        self._reject_packet(payload, "conflict_reason_without_conflict")

    def test_abstention_reasons_and_precedence_are_fixed(self):
        cases = [
            (retrieve(gateway(), request()).packet, "none"),
            (retrieve(gateway(), request("No matching preparation evidence at week 25", "preparation", 25)).packet,
             "no_approved_public_content"),
            (retrieve(gateway(), request("Why is my plan stale?", "movement", graph=False),
                      purpose="causal_explanation").packet, "no_eligible_evidence"),
            (retrieve(gateway(), request("How should my peanut allergy change week 25 nutrition guidance?", week=25),
                      purpose="mixed_personalized_guidance").packet, "partial_support"),
            (retrieve(gateway(), request("What should I prepare now?", "preparation"),
                      scope(WORKSPACE_B, OWNER_B, 999)).packet, "missing_information"),
            (retrieve(gateway(), request("How should my conflicting prenatal yoga record affect week 25 movement guidance?", "movement", 25),
                      scope(WORKSPACE_F, OWNER_F, 1), "mixed_personalized_guidance").packet,
             "unresolved_conflict"),
        ]
        for packet, reason in cases:
            with self.subTest(reason=reason):
                self.assertEqual(packet.abstention.reason, reason)
                payload = packet.model_dump(mode="python")
                payload["abstention"]["reason"] = (
                    "no_eligible_evidence" if reason != "no_eligible_evidence" else "partial_support"
                )
                payload["abstention"]["should_abstain"] = True
                self._reject_packet(payload, f"invalid_inverse_{reason}")

        payload = fixture()
        context = payload["personal_contexts"][str(WORKSPACE_A)]
        context["unresolved_conflicts"].append({
            "conflict_id": "c8111111-7777-4777-8777-777777777777",
            "fact_type": "allergy", "proposed_values": ["sesame", "none"],
            "source_document_ids": [], "clarification_question_ids": [],
            "state": "requires_clarification",
        })
        context["missing_information"].append({
            "field": "allergy_detail", "reason": "Missing allergy detail.",
            "required_for": ["personal_record"],
        })
        both = retrieve(
            gateway(payload), request("What allergies are in my record?"),
            purpose="personal_record_lookup",
        ).packet
        self.assertEqual(both.abstention.reason, "unresolved_conflict")

        class SlowBrokenRepository(FixtureRetrievalRepository):
            def authenticated_scope(self, requested_scope):
                time.sleep(0.02)
                raise RetrievalDatabaseUnavailable("synthetic outage")
        database_and_timeout = retrieve(
            RetrievalGateway(
                SlowBrokenRepository(fixture()),
                embedding_provider=DeterministicTestEmbeddingProvider(),
                corpus_version="stage5-fixture-v2", release_version="fixture-release-v2",
            ), request(timeout_ms=10),
        ).packet
        self.assertEqual(
            database_and_timeout.answerability.blocking_reasons,
            ["database_unavailable", "retrieval_timeout"],
        )
        self.assertEqual(database_and_timeout.abstention.reason, "database_unavailable")

    def test_all_trusted_journey_relations_enforce_the_truth_table(self):
        results = {
            "current": retrieve(gateway(), request()),
            "explicit_other": retrieve(
                gateway(), request("What should I prepare at week 30?", "preparation", 30)
            ),
            "overridden_to_current": retrieve(
                gateway(), request("What applies to me now?", week=12)
            ),
            "unconfirmed_current": retrieve(
                gateway(), request(), scope(WORKSPACE_B, OWNER_B, 2)
            ),
        }
        for relation, result in results.items():
            state = result.packet.trusted_state
            with self.subTest(valid=relation):
                self.assertEqual(state.journey_relation, relation)
                TrustedRetrievalState.model_validate_json(state.model_dump_json())

        current = results["current"].packet.trusted_state.model_dump(mode="python")
        explicit = results["explicit_other"].packet.trusted_state.model_dump(mode="python")
        overridden = results["overridden_to_current"].packet.trusted_state.model_dump(mode="python")
        unconfirmed = results["unconfirmed_current"].packet.trusted_state.model_dump(mode="python")
        invalid = [
            ("current_without_current", {**current, "current_journey": None}),
            ("current_mismatch", {**current, "effective_journey": JourneyPosition(stage="pregnancy", unit="week", exact=25)}),
            ("explicit_equal_current", {**current, "journey_relation": "explicit_other"}),
            ("explicit_effective_not_requested", {**explicit, "effective_journey": explicit["current_journey"]}),
            ("override_without_current", {**overridden, "current_journey": None}),
            ("override_effective_requested", {**overridden, "effective_journey": overridden["requested_journey"]}),
            ("unconfirmed_with_current", {**unconfirmed, "current_journey": current["current_journey"]}),
            ("unconfirmed_effective_mismatch", {**unconfirmed, "effective_journey": JourneyPosition(stage="pregnancy", unit="week", exact=25)}),
        ]
        for label, payload in invalid:
            with self.subTest(invalid=label), self.assertRaises(ValidationError):
                TrustedRetrievalState.model_validate_json(self._json(payload))

    def test_missing_information_is_category_specific_pairwise(self):
        categories = [
            ("allergy_detail", "What allergies are in my record?", "nutrition"),
            ("restriction_detail", "What restrictions are in my record?", "movement"),
            ("medication_list", "What medications are in my record?", "followup"),
            ("medical_condition", "What conditions are in my record?", "wellbeing"),
            ("appointment_date", "What appointments are in my record?", "preparation"),
            ("journey_week", "What week am I in?", "journey"),
        ]
        for missing_field, question, domain in categories:
            payload = fixture()
            context = payload["personal_contexts"][str(WORKSPACE_A)]
            context["missing_information"] = [{
                "field": missing_field, "reason": "Required fictional detail is missing.",
                "required_for": ["personal_record"],
            }]
            packet = retrieve(
                gateway(payload), request(question, domain),
                purpose="personal_record_lookup",
            ).packet
            with self.subTest(positive=missing_field):
                self.assertEqual([item.field for item in packet.missing_information], [missing_field])
                self.assertEqual(packet.abstention.reason, "missing_information")
            for other_field, other_question, other_domain in categories:
                if other_field == missing_field:
                    continue
                packet = retrieve(
                    gateway(payload), request(other_question, other_domain),
                    purpose="personal_record_lookup",
                ).packet
                with self.subTest(missing=missing_field, unrelated=other_field):
                    self.assertEqual(packet.missing_information, [])

    def test_conflicts_are_category_specific_pairwise(self):
        categories = [
            ("allergy", "allergy", ["sesame"], "What allergies are in my record?", "nutrition"),
            ("restriction", "dietary_restriction", ["avoid lifting"], "What restrictions are in my record?", "movement"),
            ("medication", "medication", ["fictional tablet"], "What medications are in my record?", "followup"),
            ("condition", "medical_history", ["fictional condition"], "What conditions are in my record?", "wellbeing"),
            ("appointment", "appointment", ["2026-10-01"], "What appointments are in my record?", "preparation"),
            ("journey", "journey_state", [23, 24], "What week am I in?", "journey"),
        ]
        for index, (category, fact_type, values, question, domain) in enumerate(categories, 1):
            payload = fixture()
            context = payload["personal_contexts"][str(WORKSPACE_A)]
            identifier = f"c900000{index}-7777-4777-8777-777777777777"
            context["unresolved_conflicts"] = [{
                "conflict_id": identifier, "fact_type": fact_type,
                "proposed_values": values, "source_document_ids": [],
                "clarification_question_ids": [], "state": "requires_clarification",
            }]
            packet = retrieve(
                gateway(payload), request(question, domain),
                purpose="personal_record_lookup",
            ).packet
            with self.subTest(positive=category):
                self.assertEqual(
                    [str(item.conflict_id) for item in packet.unresolved_conflicts],
                    [identifier],
                )
            for other_category, _, _, other_question, other_domain in categories:
                if other_category == category:
                    continue
                packet = retrieve(
                    gateway(payload), request(other_question, other_domain),
                    purpose="personal_record_lookup",
                ).packet
                with self.subTest(conflict=category, unrelated=other_category):
                    self.assertEqual(packet.unresolved_conflicts, [])

    def test_packet_inventory_applicability_and_span_mutations_are_rejected(self):
        base = retrieve(gateway(), request()).packet.model_dump(mode="python")
        mutations = [
            ("evidence_ids", lambda p: p.update({"evidence_ids": []})),
            ("source_ids", lambda p: p.update({"source_ids": []})),
            ("exact_spans", lambda p: p.update({"exact_spans": []})),
            ("required_citations", lambda p: p.update({"required_citations": []})),
            ("allowed_claim_types", lambda p: p.update({"allowed_claim_types": []})),
            ("selected_without_rank", lambda p: p.update({"ranked_candidates": []})),
            ("rank_without_selected", lambda p: p.update({"approved_guideline_passages": []})),
            ("wrong_corpus_mode", lambda p: p.update({"corpus_mode": "production_release"})),
            ("wrong_domain", lambda p: p["approved_guideline_passages"][0].update({"domain": "movement"})),
            ("wrong_week", lambda p: p["approved_guideline_passages"][0].update({"journey": {"stage": "pregnancy", "unit": "week", "exact": 25, "range_start": None, "range_end": None}})),
            ("wrong_jurisdiction", lambda p: p["approved_guideline_passages"][0].update({"jurisdictions": ["US"]})),
            ("wrong_condition", lambda p: p["approved_guideline_passages"][0].update({"conditions_required": ["home_birth"]})),
            ("wrong_lane", lambda p: (p.update({"evidence_lanes": ["guideline"]}), p["approved_guideline_passages"][0].update({"evidence_lane": "weekly_profile"}))),
            ("wrong_span_hash", lambda p: p["approved_guideline_passages"][0]["spans"][0].update({"text_sha256": "0" * 64})),
            ("wrong_span_source", lambda p: p["approved_guideline_passages"][0]["spans"][0].update({"source_id": "OTHER"})),
            ("wrong_span_evidence", lambda p: p["approved_guideline_passages"][0]["spans"][0].update({"evidence_id": "OTHER"})),
        ]
        for label, mutate in mutations:
            payload = deepcopy(base); mutate(payload); self._reject_packet(payload, label)

        expanded = retrieve(gateway(expanded_candidate_fixture()), request(max_candidates=5)).packet.model_dump(mode="python")
        self.assertGreater(len(expanded["ranked_candidates"]), 1)
        for label, mutate in (
            ("duplicate_rank", lambda p: p["ranked_candidates"][1].update({"rank": 1})),
            ("wrong_kind", lambda p: p["ranked_candidates"][0].update({"candidate_kind": "personal_passage"})),
            ("wrong_tie_breaker", lambda p: p["ranked_candidates"][0].update({"stable_tie_breaker": "OTHER"})),
        ):
            payload = deepcopy(expanded); mutate(payload); self._reject_packet(payload, label)

        personal = retrieve(
            gateway(), request("What allergy is in my confirmed record?"),
            purpose="personal_record_lookup",
        ).packet.model_dump(mode="python")
        self.assertTrue(personal["permitted_personal_passages"])
        personal["permitted_personal_passages"][0]["span"]["text_sha256"] = "0" * 64
        self._reject_packet(personal, "personal_span_hash")

        weekly = deepcopy(base)
        weekly["weekly_profile"] = {
            "profile_id": "P24-FIXTURE", "release_id": "55555555-5555-4555-8555-555555555555",
            "corpus_version": "stage5-fixture-v2",
            "journey": {"stage": "pregnancy", "unit": "week", "exact": 24,
                        "range_start": None, "range_end": None},
            "jurisdiction": ["IN"], "hero": {"title": "fixture"},
            "card_slots": {}, "evidence_ids": [], "status": "published", "fixture_only": True,
        }
        weekly["allowed_claim_types"].append("published_weekly_profile")
        EvidencePacket.model_validate_json(self._json(weekly))
        wrong_weekly = deepcopy(weekly)
        wrong_weekly["weekly_profile"]["jurisdiction"] = ["US"]
        self._reject_packet(wrong_weekly, "weekly_profile_jurisdiction")

    def test_graph_workspace_edges_and_trace_binding_are_strict(self):
        graph_result = retrieve(
            gateway(), request("Why is my movement plan stale after the restriction?", "movement"),
            purpose="causal_explanation",
        )
        graph = graph_result.packet.model_dump(mode="python")
        graph["graph_paths"][0]["workspace_id"] = WORKSPACE_B
        self._reject_packet(graph, "graph_workspace")
        graph = graph_result.packet.model_dump(mode="python")
        graph["graph_paths"][0]["edges"][0]["to_node_id"] = uuid4()
        self._reject_packet(graph, "graph_disconnected_edge")
        graph = graph_result.packet.model_dump(mode="python")
        graph["graph_paths"][0]["edges"][0]["from_node_id"] = graph["graph_paths"][0]["nodes"][1]["node_id"]
        self._reject_packet(graph, "graph_reversed_edge")

        base = retrieve(gateway(), request()).model_dump(mode="python")
        mutations = [
            ("question", lambda p: p["packet"].update({"question": "Different question"})),
            ("normalized_query", lambda p: p["trace"].update({"normalized_query": "different query"})),
            ("jurisdiction", lambda p: p["trace"].update({"jurisdiction": "US"})),
            ("timestamps", lambda p: p["trace"].update({"completed_at": p["trace"]["started_at"] - __import__("datetime").timedelta(seconds=1)})),
            ("ranking_digest", lambda p: p["trace"].update({"deterministic_order_digest": "0" * 64})),
            ("filter_version", lambda p: p["trace"].update({"filter_version": "wrong"})),
            ("ranking_version", lambda p: p["trace"].update({"ranking_version": "wrong"})),
            ("policy_version", lambda p: p["trace"].update({"policy_version": "wrong"})),
            ("corpus_version", lambda p: p["trace"].update({"corpus_version": "wrong"})),
            ("release_version", lambda p: p["trace"].update({"release_version": "wrong"})),
        ]
        for label, mutate in mutations:
            payload = deepcopy(base); mutate(payload); self._reject_result(payload, label)

    def test_component_failure_and_blocker_semantics_are_strict(self):
        base = retrieve(gateway(), request()).model_dump(mode="python")
        payload = deepcopy(base)
        payload["packet"]["component_results"][0].update({"status": "failed", "failure": None})
        payload["trace"]["component_results"] = deepcopy(payload["packet"]["component_results"])
        self._reject_result(payload, "failed_without_failure")

        payload = deepcopy(base)
        failure = {"code": "database_unavailable", "recoverable": True,
                   "component": "exact_sql", "detail": "synthetic"}
        payload["packet"]["component_results"][0]["failure"] = failure
        payload["packet"]["failures"].append(failure)
        payload["trace"]["component_results"] = deepcopy(payload["packet"]["component_results"])
        self._reject_result(payload, "ok_with_failure")

        degraded = retrieve(gateway(provider=False), request()).model_dump(mode="python")
        payload = deepcopy(degraded)
        personal = next(item for item in payload["packet"]["component_results"]
                        if item["component"] == "personal_vector")
        personal["failure"]["component"] = "public_vector"
        payload["trace"]["component_results"] = deepcopy(payload["packet"]["component_results"])
        self._reject_result(payload, "wrong_failure_owner")

        payload = deepcopy(degraded)
        payload["packet"]["failures"] = []
        self._reject_result(payload, "component_failure_missing_from_packet")

        payload = deepcopy(base)
        payload["packet"]["answerability"]["blocking_reasons"] = ["database_unavailable"]
        self._reject_result(payload, "database_blocker_without_exact_failure")

    def test_malformed_repository_candidate_raises_typed_failure(self):
        class MalformedRepository(FixtureRetrievalRepository):
            def public_full_text(self, request, limit):
                self._called("public_full_text")
                return [{"not": "a candidate hit"}]
        service = RetrievalGateway(
            MalformedRepository(fixture()),
            embedding_provider=DeterministicTestEmbeddingProvider(),
            corpus_version="stage5-fixture-v2", release_version="fixture-release-v2",
        )
        with self.assertRaises(RetrievalInvalidCandidate):
            retrieve(service, request())


if __name__ == "__main__":
    unittest.main()
