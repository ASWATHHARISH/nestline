"""Executable Stage 5 contract, retrieval, security, graph, and cache tests."""

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
    PublicCacheEntry, RetrievalDatabaseUnavailable, RetrievalGateway,
    Stage5RetrievalCache,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "data/synthetic/stage5_retrieval_fixtures.json"
OWNER_A = UUID("11111111-1111-4111-8111-111111111111")
OWNER_B = UUID("22222222-2222-4222-8222-222222222222")
WORKSPACE_A = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
WORKSPACE_B = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")


def fixture():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def scope(workspace=WORKSPACE_A, owner=OWNER_A, version=3):
    return AuthenticatedRetrievalScope(
        workspace_id=workspace, care_episode_id=workspace,
        owner_user_id=owner, session_subject=owner, state_version=version,
        authenticated_at=datetime.now(timezone.utc))


def request(question="What protein foods matter at week 24?", domain="nutrition",
            week=24, graph=True, timeout_ms=2000):
    return RetrievalRequest(
        question=question, domain=domain,
        journey=JourneyPosition(stage="pregnancy", unit="week", exact=week),
        jurisdiction="IN", include_graph=graph, timeout_ms=timeout_ms)


def gateway(payload=None, *, provider=True, cache=None, improvement=False):
    return RetrievalGateway(
        FixtureRetrievalRepository(payload or fixture()),
        embedding_provider=(DeterministicTestEmbeddingProvider()
                            if provider else None),
        cache=cache, corpus_version="stage5-fixture-v1",
        release_version="fixture-release-v1",
        apply_ranking_improvement=improvement)


class Stage5ContractTests(unittest.TestCase):
    def test_request_cannot_accept_user_workspace(self):
        payload = request().model_dump(mode="json")
        payload["workspace_id"] = str(WORKSPACE_B)
        with self.assertRaises(ValidationError):
            RetrievalRequest.model_validate_json(json.dumps(payload))

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


class Stage5FilterAndSafetyTests(unittest.TestCase):
    def test_expected_public_evidence_survives_all_hard_filters(self):
        packet = gateway().retrieve(request(), scope()).packet
        self.assertIn("EV-NUT-24", packet.evidence_ids)

    def test_wrong_week_jurisdiction_lifecycle_and_stage_decoys_are_excluded(self):
        packet = gateway().retrieve(request(), scope()).packet
        forbidden = {"EV-DECOY-WEEK-12", "EV-DECOY-US-24",
                     "EV-DECOY-POSTPARTUM", "EV-DECOY-DRAFT",
                     "EV-DECOY-REJECTED", "EV-DECOY-RETIRED"}
        self.assertTrue(forbidden.isdisjoint(packet.evidence_ids))

    def test_proposed_conflicted_and_superseded_facts_do_not_personalize(self):
        packet = gateway().retrieve(request(), scope()).packet
        values = {str(item.fact_id) for item in packet.confirmed_personal_facts}
        forbidden = {"a3333333-3333-4333-8333-333333333333",
                     "a4444444-4444-4444-8444-444444444444",
                     "a5555555-5555-4555-8555-555555555555"}
        self.assertTrue(values.isdisjoint(forbidden))
        self.assertEqual(len(values), 2)

    def test_medication_remains_record_only(self):
        packet = gateway().retrieve(request(), scope()).packet
        self.assertTrue(packet.medication_records)
        self.assertTrue(all(item.record_only for item in packet.medication_records))
        self.assertIn("record_only_medication", packet.allowed_claim_types)

    def test_no_match_symptom_is_evaluation_only_not_safe(self):
        packet = gateway().retrieve(request(), scope()).packet
        symptom = packet.symptom_records[0]
        self.assertEqual(symptom.safety_route, "no_match")
        self.assertTrue(symptom.safety_evaluation_only)
        self.assertNotIn("safe", packet.allowed_claim_types)

    def test_other_workspace_private_passage_never_crosses_scope(self):
        packet = gateway().retrieve(
            request("What is in my fictional document?"), scope()).packet
        ids = {item.candidate_id for item in packet.permitted_personal_passages}
        self.assertNotIn("personal-b2222222-2222-4222-8222-222222222222", ids)

    def test_user_b_cannot_retrieve_user_a_exact_facts(self):
        packet = gateway().retrieve(
            request("What allergy is confirmed?"),
            scope(WORKSPACE_B, OWNER_B)).packet
        self.assertEqual(packet.confirmed_personal_facts, [])

    def test_unresolved_conflict_returns_clarification_not_chosen_fact(self):
        packet = gateway().retrieve(
            request("Give week 42 preparation evidence", "preparation", 42),
            scope(WORKSPACE_B, OWNER_B)).packet
        self.assertTrue(packet.abstention.should_abstain)
        self.assertEqual(packet.abstention.reason, "unresolved_conflict")
        self.assertTrue(packet.unresolved_conflicts)
        self.assertEqual(packet.confirmed_personal_facts, [])

    def test_no_public_release_is_explicit(self):
        data = fixture()
        data["public_records"] = []
        packet = gateway(data).retrieve(
            request("Unknown preparation", "preparation", 42),
            scope(WORKSPACE_B, OWNER_B)).packet
        self.assertEqual(packet.corpus_mode, "no_public_release")
        self.assertIn("no_approved_public_content",
                      {item.code for item in packet.failures})


class Stage5GraphAndRankingTests(unittest.TestCase):
    def test_graph_adds_required_document_restriction_plan_path(self):
        packet = gateway().retrieve(
            request("Why is my movement plan stale after the restriction?",
                    "movement"), scope()).packet
        paths = {item.path_id: item for item in packet.graph_paths}
        path = paths["PATH-DOC-RESTRICTION-STALE-PLAN"]
        self.assertEqual([node.node_type for node in path.nodes],
                         ["document", "restriction", "plan_item", "plan"])
        self.assertEqual(path.depth, 3)

    def test_graph_disabled_preserves_exact_sql_without_false_benefit(self):
        packet = gateway().retrieve(
            request("What allergy is in my confirmed record?", graph=False),
            scope()).packet
        self.assertTrue(packet.confirmed_personal_facts)
        self.assertEqual(packet.graph_paths, [])

    def test_cycle_fixture_is_excluded(self):
        packet = gateway().retrieve(
            request("cycle restriction graph", "movement"), scope()).packet
        self.assertNotIn("DECOY-CYCLE", {item.path_id for item in packet.graph_paths})

    def test_graph_depth_and_path_counts_are_bounded(self):
        packet = gateway().retrieve(
            request("Why is my plan stale after restriction?", "movement"),
            scope()).packet
        self.assertLessEqual(len(packet.graph_paths), 8)
        self.assertTrue(all(item.depth <= 4 for item in packet.graph_paths))

    def test_duplicate_component_candidates_have_stable_order(self):
        first = gateway().retrieve(request(), scope()).trace
        second = gateway().retrieve(request(), scope()).trace
        self.assertEqual(first.deterministic_order_digest,
                         second.deterministic_order_digest)

    def test_wrong_week_candidate_is_retried_once_then_rejected(self):
        data = fixture()
        raw = next(item for item in data["public_records"]
                   if item["candidate"]["evidence_id"] == "EV-DECOY-WEEK-12")
        candidate = PublicEvidenceCandidate.model_validate_json(
            json.dumps(raw["candidate"]))

        class WrongWeekRepository(FixtureRetrievalRepository):
            def public_full_text(self, request, limit):
                self._called("public_full_text")
                return [CandidateHit(candidate, 1.0)]

        repo = WrongWeekRepository(data)
        result = RetrievalGateway(repo, embedding_provider=None,
                                  corpus_version="fixture",
                                  release_version="fixture").retrieve(
                                      request(), scope())
        component = next(item for item in result.trace.component_results
                         if item.component == "public_full_text")
        self.assertEqual(component.retries, 1)
        self.assertNotIn("EV-DECOY-WEEK-12", result.packet.evidence_ids)
        self.assertEqual(repo.call_counts["public_full_text"], 2)


class Stage5CacheAndFailureTests(unittest.TestCase):
    def test_personal_cache_keys_are_workspace_and_state_isolated(self):
        cache = Stage5RetrievalCache()
        req = request()
        self.assertNotEqual(cache.personal_key(scope(), req),
                            cache.personal_key(scope(WORKSPACE_B, OWNER_B), req))
        self.assertNotEqual(cache.personal_key(scope(version=3), req),
                            cache.personal_key(scope(version=4), req))

    def test_release_and_filter_versions_invalidate_public_key(self):
        cache = Stage5RetrievalCache()
        req = request()
        first = cache.public_key(req, corpus_version="c1", release_version="r1")
        second = cache.public_key(req, corpus_version="c1", release_version="r2")
        third = cache.public_key(req, corpus_version="c1", release_version="r1",
                                 filter_version="stage5-filter-v2")
        self.assertEqual(len({first, second, third}), 3)

    def test_public_cache_rejects_personal_entry(self):
        cache = Stage5RetrievalCache()
        with self.assertRaises(TypeError):
            cache.put_public("public:x", PersonalCacheEntry(
                WORKSPACE_A, WORKSPACE_A, 1,
                gateway().repository.exact_personal_context(scope(), request()),
                [], [], []))

    def test_personal_invalidation_removes_derived_result(self):
        cache = Stage5RetrievalCache()
        service = gateway(cache=cache)
        service.retrieve(request(), scope())
        key = cache.personal_key(scope(), request())
        self.assertIsNotNone(cache.get_personal(key, scope()))
        self.assertEqual(cache.invalidate_personal(WORKSPACE_A), 1)
        self.assertIsNone(cache.get_personal(key, scope()))

    def test_vector_unavailable_degrades_without_hiding_sql(self):
        packet = gateway(provider=False).retrieve(request(), scope()).packet
        self.assertTrue(packet.confirmed_personal_facts)
        self.assertIn("vector_unavailable", {item.code for item in packet.failures})

    def test_database_failure_never_claims_personalization(self):
        class BrokenRepository(FixtureRetrievalRepository):
            def exact_personal_context(self, scope, request):
                raise RetrievalDatabaseUnavailable("fixture outage")
        service = RetrievalGateway(
            BrokenRepository(fixture()),
            embedding_provider=DeterministicTestEmbeddingProvider(),
            corpus_version="fixture", release_version="fixture")
        packet = service.retrieve(
            request("Unknown preparation", "preparation", 42),
            scope(WORKSPACE_B, OWNER_B)).packet
        self.assertEqual(packet.confirmed_personal_facts, [])
        self.assertIn("database_unavailable", {item.code for item in packet.failures})

    def test_timeout_forces_recoverable_abstention(self):
        class SlowRepository(FixtureRetrievalRepository):
            def exact_personal_context(self, scope, request):
                time.sleep(0.02)
                return super().exact_personal_context(scope, request)
        service = RetrievalGateway(
            SlowRepository(fixture()),
            embedding_provider=DeterministicTestEmbeddingProvider(),
            corpus_version="fixture", release_version="fixture")
        packet = service.retrieve(request(timeout_ms=10), scope()).packet
        self.assertTrue(packet.abstention.should_abstain)
        self.assertEqual(packet.abstention.reason, "retrieval_timeout")


if __name__ == "__main__":
    unittest.main()
