"""Exercise Stage 5 through local Auth, PostgREST, pgvector, and graph RPCs.

All records are conspicuously fictional and are deleted before success. Product
retrieval uses two real user JWTs and the publishable key; the service key is
used only for isolated fixture setup and cleanup.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import PurePosixPath
from urllib.parse import quote
from uuid import UUID, uuid4

from app.schemas.documents import DocumentReviewRequest
from app.schemas.retrieval import (
    AuthenticatedRetrievalScope, JourneyPosition, RetrievalRequest,
)
from app.services.embeddings import DeterministicTestEmbeddingProvider
from app.services.onboarding import SupabaseAuthClient, SupabaseOnboardingGateway
from app.services.personal_documents import SupabaseDocumentGateway
from app.services.retrieval import PostgrestRetrievalRepository, RetrievalGateway
from scripts.check_stage2_storage_api import LocalSupabase, _expect_success
from scripts.check_stage4_document_api import _decisions, _process_fixture


def _vector(value: list[float]) -> str:
    return "[" + ",".join(f"{item:.12f}" for item in value) + "]"


def _write(local: LocalSupabase, table: str, body, *, method="POST", query=""):
    status, raw = local.request(
        method, f"/rest/v1/{table}{query}", key=local.service_key,
        json_body=body, extra_headers={"Prefer": "return=representation"})
    _expect_success(status, f"Stage 5 fixture {method} {table}")
    return local.json(raw)


def main() -> int:
    local = LocalSupabase()
    marker = uuid4().hex
    password = f"Nestline-{uuid4().hex}-A1!"
    emails = [f"stage5-owner-{marker}@example.invalid",
              f"stage5-other-{marker}@example.invalid"]
    user_ids, workspace_ids, object_paths = [], [], []
    release_id = str(uuid4())
    source_id = f"S5-API-{marker}"
    checks = 0
    try:
        for email in emails:
            status, raw = local.request(
                "POST", "/auth/v1/admin/users", key=local.service_key,
                json_body={"email": email, "password": password,
                           "email_confirm": True})
            _expect_success(status, "temporary Stage 5 user creation")
            user_ids.append(local.json(raw)["id"])
        auth = SupabaseAuthClient(local.url, local.anon_key)
        sessions = [auth.sign_in(email, password) for email in emails]
        checks += 2
        for index, session in enumerate(sessions):
            onboarding = SupabaseOnboardingGateway(
                local.url, local.anon_key, session.access_token)
            workspace_ids.append(str(onboarding.create_demo_workspace(
                f"stage5-{marker}-{index}",
                f"Stage 5 fictional workspace {index + 1}")))
        owner_workspace, other_workspace = workspace_ids
        checks += 2

        _write(local, "content_releases", {
            "id": release_id, "corpus_version": f"stage5-fixture-{marker}",
            "release_fingerprint": sha256(marker.encode()).hexdigest(),
            "status": "published", "published_at": "2026-09-11T00:00:00Z"})
        _write(local, "public_sources", {
            "source_id": source_id, "release_id": release_id,
            "title": "Stage 5 API synthetic source", "publisher": "Nestline tests",
            "canonical_url": f"https://example.invalid/{source_id}",
            "jurisdiction": ["IN"], "source_version": "fixture-1",
            "reuse_status": "permitted",
            "allowed_use": ["store", "embed", "display"],
            "status": "published", "content_checksum": "a" * 64})
        provider = DeterministicTestEmbeddingProvider()
        evidence_text = "week 24 gentle movement respects a confirmed restriction"
        embedding = _vector(provider.embed([evidence_text])[0])
        base_chunk = {
            "release_id": release_id, "source_id": source_id,
            "candidate_checksum": "b" * 64,
            "source_block_ids": ["S5-API-BLOCK"], "stage": "pregnancy",
            "unit": "week", "jurisdiction": ["IN"],
            "domains": ["movement"], "display_slots": ["plan"],
            "embedding_provider": provider.name, "embedding_model": provider.model,
            "embedding_dimensions": 32, "embedding": embedding,
            "status": "published"}
        _write(local, "guideline_chunks", base_chunk | {
            "chunk_id": f"S5-API-GOOD-{marker}",
            "evidence_id": f"S5-API-EV-GOOD-{marker}", "text": evidence_text,
            "range_start": 24, "range_end": 24})
        _write(local, "guideline_chunks", base_chunk | {
            "chunk_id": f"S5-API-WRONG-{marker}",
            "evidence_id": f"S5-API-EV-WRONG-WEEK-{marker}",
            "candidate_checksum": "c" * 64,
            "text": "week 12 gentle movement wrong week decoy",
            "range_start": 12, "range_end": 12})
        checks += 3

        document_gateway = SupabaseDocumentGateway(
            local.url, local.anon_key, sessions[0].access_token)
        _, validation, document_id, _, version, candidates = _process_fixture(
            document_gateway, owner_workspace, "DOC-005")
        object_paths.append(
            f"{owner_workspace}/{validation.sha256}/{validation.safe_filename}")
        result = document_gateway.commit_review(DocumentReviewRequest(
            workspace_id=UUID(owner_workspace), document_id=document_id,
            expected_review_version=version,
            submission_key=f"stage5-api-{marker}",
            decisions=_decisions(candidates)))
        if not result.confirmed_fact_ids:
            raise AssertionError("Stage 5 setup did not create confirmed facts")
        _write(local, "document_chunks", {"embedding_provider": provider.name,
            "embedding_model": provider.model, "embedding_dimensions": 32,
            "embedding": embedding}, method="PATCH",
            query=f"?workspace_id=eq.{owner_workspace}&document_id=eq.{document_id}")
        checks += 2

        plan_id, item_id, restriction_id = map(lambda _: str(uuid4()), range(3))
        status, raw = local.request(
            "GET", f"/rest/v1/journey_states?workspace_id=eq.{owner_workspace}"
                   "&is_current=eq.true&select=id",
            key=local.anon_key, token=sessions[0].access_token)
        _expect_success(status, "Stage 5 seeded journey lookup")
        journey_id = local.json(raw)[0]["id"]
        status, raw = local.request(
            "GET", f"/rest/v1/plans?workspace_id=eq.{owner_workspace}"
                   "&select=version&order=version.desc&limit=1",
            key=local.anon_key, token=sessions[0].access_token)
        _expect_success(status, "Stage 5 seeded plan version lookup")
        plan_version = (local.json(raw)[0]["version"] + 1) if local.json(raw) else 1
        _write(local, "health_facts", {
            "id": restriction_id, "workspace_id": owner_workspace,
            "fact_type": "dietary_restriction",
            "value": {"fictional": "avoid high-impact movement"},
            "source_kind": "human_reviewed",
            "confirmation_status": "confirmed"})
        _write(local, "plans", {"id": plan_id, "workspace_id": owner_workspace,
            "version": plan_version, "journey_state_id": journey_id,
            "source_release_id": release_id, "status": "stale",
            "stale_reasons": ["confirmed_restriction_changed"]})
        _write(local, "plan_items", {"id": item_id,
            "workspace_id": owner_workspace, "plan_id": plan_id,
            "evidence_ids": [f"S5-API-EV-GOOD-{marker}"],
            "category": "movement", "title": "Fictional movement item",
            "body": "Fictional plan body", "state": "stale", "position": 0})
        status, raw = local.request(
            "GET", f"/rest/v1/graph_nodes?workspace_id=eq.{owner_workspace}"
                   f"&node_type=eq.document&entity_id=eq.{document_id}&select=id",
            key=local.anon_key, token=sessions[0].access_token)
        _expect_success(status, "Stage 5 document graph lookup")
        document_node_id = local.json(raw)[0]["id"]
        graph_node_ids = [str(uuid4()) for _ in range(3)]
        _write(local, "graph_nodes", [
            {"id": graph_node_ids[0], "workspace_id": owner_workspace,
             "node_type": "restriction", "entity_id": restriction_id,
             "label": "Confirmed fictional movement restriction"},
            {"id": graph_node_ids[1], "workspace_id": owner_workspace,
             "node_type": "plan_item", "entity_id": item_id,
             "label": "Stale fictional movement plan item"},
            {"id": graph_node_ids[2], "workspace_id": owner_workspace,
             "node_type": "plan", "entity_id": plan_id,
             "label": "Stale fictional movement plan"}])
        _write(local, "graph_edges", [
            {"workspace_id": owner_workspace, "from_node_id": document_node_id,
             "to_node_id": graph_node_ids[0], "relation": "EXTRACTED_FROM"},
            {"workspace_id": owner_workspace, "from_node_id": graph_node_ids[0],
             "to_node_id": graph_node_ids[1], "relation": "CONSTRAINS"},
            {"workspace_id": owner_workspace, "from_node_id": graph_node_ids[1],
             "to_node_id": graph_node_ids[2], "relation": "TRIGGERED"}])
        checks += 5

        status, raw = local.request(
            "POST", "/rest/v1/rpc/stage5_authenticated_scope",
            key=local.anon_key, token=sessions[0].access_token,
            json_body={"requested_workspace_id": owner_workspace})
        _expect_success(status, "Stage 5 authenticated scope")
        retrieval_scope = AuthenticatedRetrievalScope.model_validate_json(
            raw.decode())
        checks += 1
        status, raw = local.request(
            "POST", "/rest/v1/rpc/stage5_authenticated_scope",
            key=local.anon_key, token=sessions[0].access_token,
            json_body={"requested_workspace_id": other_workspace})
        _expect_success(status, "cross-workspace scope check")
        if local.json(raw) is not None:
            raise AssertionError("owner derived scope for another workspace")
        checks += 1

        repository = PostgrestRetrievalRepository(
            supabase_url=local.url, publishable_key=local.anon_key,
            access_token=sessions[0].access_token,
            corpus_version=f"stage5-fixture-{marker}",
            release_id=UUID(release_id))
        service = RetrievalGateway(
            repository, embedding_provider=provider,
            corpus_version=f"stage5-fixture-{marker}",
            release_version=release_id)
        answer = service.retrieve(RetrievalRequest(
            question="Why is my week 24 movement plan stale after the restriction?",
            domain="movement",
            journey=JourneyPosition(stage="pregnancy", unit="week", exact=24),
            jurisdiction="IN"), retrieval_scope,
            purpose="mixed_personalized_guidance")
        evidence = set(answer.packet.evidence_ids)
        if f"S5-API-EV-GOOD-{marker}" not in evidence:
            raise AssertionError("expected public evidence was not retrieved")
        if f"S5-API-EV-WRONG-WEEK-{marker}" in evidence:
            raise AssertionError("wrong-week evidence survived hard filters")
        if not answer.packet.confirmed_personal_facts:
            raise AssertionError("confirmed exact facts were not retrieved")
        if not answer.packet.graph_paths:
            raise AssertionError("bounded causal graph path was not retrieved")
        if any(path.depth > 4 for path in answer.packet.graph_paths):
            raise AssertionError("graph traversal exceeded its depth bound")
        if answer.packet.answerability.support_state != "fully_supported":
            raise AssertionError("authenticated answerability policy was not satisfied")
        if answer.trace.resolved_state_version != answer.packet.trusted_state.cache_state_version:
            raise AssertionError("cache did not use resolved database state version")
        if answer.packet.retrieval_policy.purpose != "mixed_personalized_guidance":
            raise AssertionError("trusted retrieval purpose was not preserved")
        checks += 3
        checks += 5

        status, raw = local.request(
            "POST", "/rest/v1/rpc/stage5_personal_vector",
            key=local.anon_key, token=sessions[0].access_token,
            json_body={"requested_workspace_id": other_workspace,
                       "query_embedding": embedding, "match_count": 20})
        _expect_success(status, "cross-workspace personal vector check")
        if local.json(raw) != []:
            raise AssertionError("personal vector RPC crossed workspaces")
        checks += 1
    finally:
        for object_path in object_paths:
            status, _ = local.request(
                "DELETE", "/storage/v1/object/medical-documents",
                key=local.service_key, json_body={"prefixes": [object_path]})
            _expect_success(status, "Stage 5 Storage cleanup")
        # Deleting temporary Auth users cascades their owner-only workspaces and
        # all personal rows; this uses the same cleanup boundary as production.
        for user_id in user_ids:
            status, _ = local.request(
                "DELETE", f"/auth/v1/admin/users/{quote(user_id)}",
                key=local.service_key)
            _expect_success(status, "Stage 5 user cleanup")
        if source_id:
            _write(local, "guideline_chunks", None, method="DELETE",
                   query=f"?release_id=eq.{quote(release_id)}")
            _write(local, "public_sources", None, method="DELETE",
                   query=f"?source_id=eq.{quote(source_id)}")
            _write(local, "content_releases", None, method="DELETE",
                   query=f"?id=eq.{quote(release_id)}")

    print(json.dumps({"valid": True, "checks": checks,
                      "mode": "fictional_local_authenticated_api"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
