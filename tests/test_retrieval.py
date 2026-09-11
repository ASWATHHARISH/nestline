"""Stage 5 contracts, answerability, security, graph, cache, and regression tests."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import time
import unittest
from uuid import UUID

from pydantic import ValidationError

from app.schemas.retrieval import (
    AuthenticatedRetrievalScope, JourneyPosition, PublicEvidenceCandidate,
    RetrievalRequest, RerankerInput,
)
from app.services.embeddings import DeterministicTestEmbeddingProvider
from app.services.retrieval import (
    CandidateHit, FixtureRetrievalRepository, PersonalCacheEntry,
    RetrievalDatabaseUnavailable, RetrievalGateway, Stage5RetrievalCache,
)
from app.services.retrieval_policy import build_evidence_policy, build_trusted_query

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "data/synthetic/stage5_retrieval_fixtures.json"
OWNER_A = UUID("11111111-1111-4111-8111-111111111111")
OWNER_B = UUID("22222222-2222-4222-8222-222222222222")
WORKSPACE_A = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
WORKSPACE_B = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
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
            week=24, graph=True, timeout_ms=2000, *, stage="pregnancy", unit="week"):
    journey = (JourneyPosition(stage="possible_pregnancy", unit="none")
               if stage == "possible_pregnancy"
               else JourneyPosition(stage=stage, unit=unit, exact=week))
    return RetrievalRequest(
        question=question, domain=domain, journey=journey,
        jurisdiction="IN", include_graph=graph, timeout_ms=timeout_ms)


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
        req, auth_scope or scope(),
        policy=build_evidence_policy(purpose, req.domain))


def trusted_query(req, auth_scope=None):
    auth_scope = auth_scope or scope()
    repo = FixtureRetrievalRepository(fixture())
    resolved = repo.authenticated_scope(auth_scope)
    exact = repo.exact_personal_context(resolved, req)
    return build_trusted_query(
        req, auth_scope, resolved, exact,
        build_evidence_policy("public_guidance", req.domain))[1]


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
        packet = retrieve(gateway(), req, purpose="mixed_personalized_guidance").packet
        self.assertEqual(packet.answerability.support_state, "clarification_required")
        self.assertEqual(packet.abstention.reason, "unresolved_conflict")
        self.assertTrue(packet.unresolved_conflicts)
        self.assertEqual(packet.permitted_personal_passages, [])

    def test_irrelevant_conflict_does_not_block_supported_nutrition(self):
        packet = retrieve(gateway(), request()).packet
        self.assertFalse(packet.abstention.should_abstain)
        self.assertEqual(packet.unresolved_conflicts, [])

    def test_required_missing_information_requires_clarification(self):
        req = request("What should I prepare now?", "preparation")
        packet = retrieve(gateway(), req, scope(WORKSPACE_B, OWNER_B, 999)).packet
        self.assertEqual(packet.abstention.reason, "missing_information")
        self.assertEqual(packet.approved_guideline_passages, [])

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
            corpus_version="fixture", release_version="fixture"),
            request(timeout_ms=10)).packet
        self.assertEqual(packet.abstention.reason, "retrieval_timeout")
        self.assertIn("retrieval_timeout", packet.answerability.blocking_reasons)


if __name__ == "__main__":
    unittest.main()
