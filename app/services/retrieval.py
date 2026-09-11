"""Stage 5 permission-safe hybrid retrieval gateway.

All future specialists call this one read-only gateway. The gateway accepts a
trusted authenticated scope separately from user-controlled input.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
import re
from time import perf_counter
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import UUID

from app.schemas.retrieval import (
    AbstentionState, AuthenticatedRetrievalScope, EvidencePacket,
    ExactPersonalContext, GraphPath, PersonalPassageCandidate,
    PublicEvidenceCandidate, RankedRetrievalCandidate, RetrievalComponentResult,
    RetrievalFailure, RetrievalPurpose, RetrievalRequest,
    RetrievalResult, RetrievalTrace, RuntimeBlocker, TrustedRetrievalQuery,
    WeeklyProfileCandidate, derive_abstention_reason, derive_packet_inventory,
    normalize_retrieval_query, ranked_candidate_digest,
)
from app.services.embeddings import EmbeddingProvider
from app.services.retrieval_policy import (
    assess_answerability,
    build_evidence_policy,
    build_trusted_query,
    meaningful_tokens,
    minimise_personal_context,
    personal_passage_relevant,
)

FILTER_VERSION = "stage5-filter-v1"
BASE_RANKING_VERSION = "rrf-v1-authority-applicability-tiebreak-v1"
TRIAL_RANKING_VERSION = "rrf-v1-authority-applicability-score-trial-v1"
RRF_K = 60
MAX_GRAPH_DEPTH = 4
MAX_GRAPH_PATHS = 8


class RetrievalDatabaseUnavailable(RuntimeError):
    """The repository could not complete a read."""


class RetrievalVectorUnavailable(RuntimeError):
    """The vector component is unavailable; text and SQL may still be used."""


class RetrievalInvalidCandidate(RuntimeError):
    """A repository returned a malformed or wrong-lane candidate; fail closed."""


@dataclass(frozen=True)
class CandidateHit:
    candidate: PublicEvidenceCandidate | PersonalPassageCandidate
    score: float


class RetrievalRepository(Protocol):
    """Read-only persistence boundary used by the single Retrieval Gateway."""

    def authenticated_scope(
        self, requested_scope: AuthenticatedRetrievalScope,
    ) -> AuthenticatedRetrievalScope: ...
    def exact_personal_context(self, scope: AuthenticatedRetrievalScope,
                               request: RetrievalRequest) -> ExactPersonalContext: ...
    def public_full_text(self, request: TrustedRetrievalQuery, limit: int) -> list[CandidateHit]: ...
    def public_vector(self, request: TrustedRetrievalQuery, embedding: list[float],
                      limit: int) -> list[CandidateHit]: ...
    def personal_full_text(self, scope: AuthenticatedRetrievalScope,
                           request: TrustedRetrievalQuery, limit: int) -> list[CandidateHit]: ...
    def personal_vector(self, scope: AuthenticatedRetrievalScope,
                        request: TrustedRetrievalQuery, embedding: list[float],
                        limit: int) -> list[CandidateHit]: ...
    def weekly_profile(self, request: TrustedRetrievalQuery) -> WeeklyProfileCandidate | None: ...
    def graph_paths(self, scope: AuthenticatedRetrievalScope,
                    request: TrustedRetrievalQuery, max_depth: int,
                    max_paths: int) -> list[GraphPath]: ...


@dataclass
class PublicCacheEntry:
    full_text: list[CandidateHit]
    vector: list[CandidateHit]
    weekly_profile: WeeklyProfileCandidate | None


@dataclass
class PersonalCacheEntry:
    workspace_id: UUID
    care_episode_id: UUID
    state_version: int
    exact: ExactPersonalContext
    full_text: list[CandidateHit]
    vector: list[CandidateHit]
    graph_paths: list[GraphPath]


class Stage5RetrievalCache:
    """Process-local cache with structurally separate public and personal stores."""

    def __init__(self) -> None:
        self._public: dict[str, PublicCacheEntry] = {}
        self._personal: dict[str, PersonalCacheEntry] = {}

    @staticmethod
    def _digest(payload: dict[str, Any]) -> str:
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        return sha256(raw.encode("utf-8")).hexdigest()

    def public_key(self, request: TrustedRetrievalQuery, *, corpus_version: str,
                   release_version: str, filter_version: str = FILTER_VERSION) -> str:
        return "public:" + self._digest({
            "query": normalize_query(request.question), "domain": request.domain,
            "stage": request.journey.stage, "unit": request.journey.unit,
            "start": request.journey.start, "end": request.journey.end,
            "jurisdiction": request.jurisdiction.upper(),
            "lanes": sorted(request.evidence_lanes),
            "conditions": sorted(request.active_conditions),
            "policy_id": request.policy.policy_id,
            "policy_version": request.policy.policy_version,
            "purpose": request.policy.purpose,
            "required_support": request.policy.required_support,
            "max_candidates": request.max_candidates,
            "corpus_version": corpus_version, "release_version": release_version,
            "filter_version": filter_version,
        })

    def personal_key(self, scope: AuthenticatedRetrievalScope,
                     request: TrustedRetrievalQuery,
                     *, filter_version: str = FILTER_VERSION) -> str:
        return "personal:" + self._digest({
            "workspace": str(scope.workspace_id),
            "care_episode": str(scope.care_episode_id),
            "state_version": scope.state_version,
            "query": normalize_query(request.question), "domain": request.domain,
            "stage": request.journey.stage, "unit": request.journey.unit,
            "start": request.journey.start, "end": request.journey.end,
            "include_graph": request.include_graph,
            "policy_id": request.policy.policy_id,
            "policy_version": request.policy.policy_version,
            "purpose": request.policy.purpose,
            "required_support": request.policy.required_support,
            "personal_context_kinds": request.policy.personal_context_kinds,
            "max_candidates": request.max_candidates,
            "filter_version": filter_version,
        })

    def get_public(self, key: str) -> PublicCacheEntry | None:
        value = self._public.get(key)
        return deepcopy(value) if value is not None else None

    def put_public(self, key: str, value: PublicCacheEntry) -> None:
        if not isinstance(value, PublicCacheEntry):
            raise TypeError("public cache accepts only PublicCacheEntry")
        self._public[key] = deepcopy(value)

    def get_personal(self, key: str,
                     scope: AuthenticatedRetrievalScope) -> PersonalCacheEntry | None:
        value = self._personal.get(key)
        if value is None:
            return None
        if value.workspace_id != scope.workspace_id or value.care_episode_id != scope.care_episode_id:
            return None
        return deepcopy(value)

    def put_personal(self, key: str, value: PersonalCacheEntry) -> None:
        if not isinstance(value, PersonalCacheEntry):
            raise TypeError("personal cache accepts only PersonalCacheEntry")
        self._personal[key] = deepcopy(value)

    def invalidate_personal(self, workspace_id: UUID,
                            care_episode_id: UUID | None = None) -> int:
        keys = [key for key, entry in self._personal.items()
                if entry.workspace_id == workspace_id and
                (care_episode_id is None or entry.care_episode_id == care_episode_id)]
        for key in keys:
            del self._personal[key]
        return len(keys)

    def clear_public(self) -> int:
        count = len(self._public)
        self._public.clear()
        return count


class PostgrestRetrievalRepository:
    """Authenticated PostgREST adapter. It never accepts a service-role key."""

    def __init__(self, *, supabase_url: str, publishable_key: str,
                 access_token: str, corpus_version: str, release_id: UUID,
                 timeout_seconds: int = 5) -> None:
        if not all(value.strip() for value in (supabase_url, publishable_key, access_token)):
            raise ValueError("Supabase URL, publishable key, and user access token are required")
        self._url = supabase_url.rstrip("/")
        self._key = publishable_key
        self._token = access_token
        self._corpus_version = corpus_version
        self._release_id = release_id
        self._timeout = timeout_seconds

    def _rpc(self, function: str, payload: dict[str, Any]) -> Any:
        body = json.dumps(payload, default=str).encode("utf-8")
        req = Request(f"{self._url}/rest/v1/rpc/{function}", data=body, method="POST",
                      headers={"apikey": self._key,
                               "Authorization": f"Bearer {self._token}",
                               "Content-Type": "application/json"})
        try:
            with urlopen(req, timeout=self._timeout) as response:
                raw = response.read(10 * 1024 * 1024 + 1)
        except (HTTPError, URLError, TimeoutError) as exc:
            raise RetrievalDatabaseUnavailable(f"{function} failed") from exc
        if len(raw) > 10 * 1024 * 1024:
            raise RetrievalDatabaseUnavailable(f"{function} response exceeded limit")
        try:
            return json.loads(raw) if raw else None
        except json.JSONDecodeError as exc:
            raise RetrievalDatabaseUnavailable(f"{function} returned malformed JSON") from exc

    def _position_payload(self, request: TrustedRetrievalQuery) -> dict[str, Any]:
        return {"requested_stage": request.journey.stage,
                "requested_unit": request.journey.unit,
                "requested_range_start": request.journey.start,
                "requested_range_end": request.journey.end,
                "requested_jurisdiction": request.jurisdiction.upper(),
                "requested_domain": request.domain,
                "requested_conditions": request.active_conditions,
                "requested_evidence_lanes": request.evidence_lanes,
                "requested_corpus_version": self._corpus_version,
                "requested_release_id": str(self._release_id)}

    @staticmethod
    def _hits(rows: Any, model) -> list[CandidateHit]:
        if not isinstance(rows, list):
            raise RetrievalDatabaseUnavailable("retrieval RPC did not return a list")
        result = []
        for row in rows:
            if not isinstance(row, dict) or "candidate" not in row or "component_score" not in row:
                raise RetrievalDatabaseUnavailable("retrieval RPC returned a malformed candidate")
            result.append(CandidateHit(model.model_validate_json(json.dumps(row["candidate"])),
                                       float(row["component_score"])))
        return result

    def authenticated_scope(self, requested_scope):
        value = self._rpc("stage5_authenticated_scope", {
            "requested_workspace_id": str(requested_scope.workspace_id),
        })
        if not isinstance(value, dict):
            raise RetrievalDatabaseUnavailable(
                "authenticated scope could not be resolved"
            )
        resolved = AuthenticatedRetrievalScope.model_validate_json(json.dumps(value))
        if resolved.session_subject != requested_scope.session_subject:
            raise RetrievalDatabaseUnavailable(
                "authenticated session subject changed during scope resolution"
            )
        return resolved

    def exact_personal_context(self, scope, request):
        value = self._rpc("stage5_exact_personal_context",
                          {"requested_workspace_id": str(scope.workspace_id)})
        return ExactPersonalContext.model_validate_json(json.dumps(value))

    def public_full_text(self, request, limit):
        payload = self._position_payload(request) | {
            "search_query": request.question, "match_count": limit}
        return self._hits(self._rpc("stage5_public_full_text", payload),
                          PublicEvidenceCandidate)

    def public_vector(self, request, embedding, limit):
        payload = self._position_payload(request) | {
            "query_embedding": embedding, "match_count": limit}
        return self._hits(self._rpc("stage5_public_vector", payload),
                          PublicEvidenceCandidate)

    def personal_full_text(self, scope, request, limit):
        rows = self._rpc("stage5_personal_full_text", {
            "requested_workspace_id": str(scope.workspace_id),
            "search_query": request.question, "match_count": limit})
        return self._hits(rows, PersonalPassageCandidate)

    def personal_vector(self, scope, request, embedding, limit):
        rows = self._rpc("stage5_personal_vector", {
            "requested_workspace_id": str(scope.workspace_id),
            "query_embedding": embedding, "match_count": limit})
        return self._hits(rows, PersonalPassageCandidate)

    def weekly_profile(self, request):
        value = self._rpc("stage5_weekly_profile", self._position_payload(request))
        return None if value is None else WeeklyProfileCandidate.model_validate_json(json.dumps(value))

    def graph_paths(self, scope, request, max_depth, max_paths):
        rows = self._rpc("stage5_graph_paths", {
            "requested_workspace_id": str(scope.workspace_id),
            "search_query": request.question,
            "requested_max_depth": max_depth, "requested_max_paths": max_paths})
        if not isinstance(rows, list):
            raise RetrievalDatabaseUnavailable("graph RPC did not return a list")
        return [GraphPath.model_validate_json(json.dumps(row)) for row in rows]


def normalize_query(value: str) -> str:
    """Backward-compatible alias for the canonical contract normalizer."""

    return normalize_retrieval_query(value)


def _tokens(value: str) -> set[str]:
    return meaningful_tokens(value)


def _cosine(left: list[float], right: list[float]) -> float:
    if not left or len(left) != len(right):
        raise RetrievalVectorUnavailable("fixture vector dimensions do not match")
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    return 0.0 if not left_norm or not right_norm else dot / (left_norm * right_norm)


class FixtureRetrievalRepository:
    """Deterministic, isolated Stage 5 repository used only by tests and evals."""

    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = deepcopy(payload)
        self.call_counts: dict[str, int] = {}

    def _called(self, name: str) -> None:
        self.call_counts[name] = self.call_counts.get(name, 0) + 1

    def _owns(self, scope: AuthenticatedRetrievalScope) -> bool:
        owners = self.payload.get("workspace_owners", {})
        return owners.get(str(scope.workspace_id)) == str(scope.owner_user_id)

    @staticmethod
    def _range_fits(candidate: PublicEvidenceCandidate,
                    request: TrustedRetrievalQuery) -> bool:
        if (candidate.journey.stage != request.journey.stage or
                candidate.journey.unit != request.journey.unit):
            return False
        if request.journey.unit == "none":
            return True
        return (candidate.journey.start is not None and
                request.journey.start is not None and
                candidate.journey.start <= request.journey.start and
                candidate.journey.end >= request.journey.end)

    def _public_candidates(self, request: TrustedRetrievalQuery, *, vector: bool):
        result = []
        conditions = set(request.active_conditions)
        for record in self.payload.get("public_records", []):
            # Lifecycle checks happen before a candidate enters ranking.
            if (record.get("release_status") != "published" or
                    record.get("source_status") != "published" or
                    record.get("candidate_status") != "published" or
                    record.get("retired", False)):
                continue
            candidate = PublicEvidenceCandidate.model_validate_json(json.dumps(record["candidate"]))
            if (candidate.provenance.corpus_version != self.payload.get("active_corpus_version") or
                    str(candidate.provenance.release_id) != self.payload.get("active_release_id")):
                continue
            if (candidate.evidence_lane not in request.evidence_lanes or
                    candidate.domain != request.domain or
                    not self._range_fits(candidate, request)):
                continue
            if (request.jurisdiction.upper() not in candidate.jurisdictions and
                    "GLOBAL" not in candidate.jurisdictions):
                continue
            if not set(candidate.conditions_required).issubset(conditions):
                continue
            if set(candidate.conditions_excluded) & conditions:
                continue
            if ("display" not in candidate.allowed_use or
                    (vector and "embed" not in candidate.allowed_use)):
                continue
            result.append((record, candidate))
        return result

    def authenticated_scope(self, requested_scope):
        self._called("authenticated_scope")
        workspace_id = str(requested_scope.workspace_id)
        owner = self.payload.get("workspace_owners", {}).get(workspace_id)
        if owner is None or owner != str(requested_scope.session_subject):
            raise RetrievalDatabaseUnavailable(
                "authenticated session does not own requested workspace"
            )
        version = int(
            self.payload.get("personal_state_versions", {}).get(workspace_id, 1)
        )
        return AuthenticatedRetrievalScope(
            workspace_id=requested_scope.workspace_id,
            care_episode_id=requested_scope.workspace_id,
            owner_user_id=UUID(owner),
            session_subject=UUID(owner),
            state_version=version,
            authenticated_at=datetime.now(timezone.utc),
        )

    def exact_personal_context(self, scope, request):
        self._called("exact_sql")
        if not self._owns(scope):
            raise RetrievalDatabaseUnavailable(
                "authenticated owner does not own requested workspace")
        value = deepcopy(self.payload.get("personal_contexts", {}).get(
            str(scope.workspace_id), {}))
        confirmed = []
        for record in self.payload.get("personal_fact_records", []):
            if (record.get("workspace_id") == str(scope.workspace_id) and
                    record.get("confirmation_status") == "confirmed" and
                    not record.get("superseded", False) and
                    record.get("valid_to") is None):
                confirmed.append(record["candidate"])
        if confirmed:
            value["confirmed_facts"] = confirmed
        return ExactPersonalContext.model_validate_json(json.dumps(value))

    def public_full_text(self, request, limit):
        self._called("public_full_text")
        query_terms = _tokens(request.question)
        hits = []
        for _, candidate in self._public_candidates(request, vector=False):
            score = len(query_terms & _tokens(candidate.text)) / max(1, len(query_terms))
            if score > 0:
                hits.append(CandidateHit(candidate, score))
        return sorted(hits,
                      key=lambda hit: (-hit.score, hit.candidate.candidate_id))[:limit]

    def public_vector(self, request, embedding, limit):
        self._called("public_vector")
        hits = [CandidateHit(candidate, _cosine(embedding, record["embedding"]))
                for record, candidate in self._public_candidates(request, vector=True)
                if record.get("embedding") is not None]
        return sorted(hits,
                      key=lambda hit: (-hit.score, hit.candidate.candidate_id))[:limit]

    def _personal_candidates(self, scope):
        if not self._owns(scope):
            raise RetrievalDatabaseUnavailable(
                "authenticated owner does not own requested workspace")
        rows = []
        for record in self.payload.get("personal_passages", []):
            if (record.get("workspace_id") != str(scope.workspace_id) or
                    record.get("care_episode_id") != str(scope.care_episode_id) or
                    record.get("document_status") != "confirmed" or
                    record.get("confirmation_status") != "confirmed"):
                continue
            rows.append((record, PersonalPassageCandidate.model_validate_json(json.dumps(record["candidate"]))))
        return rows

    def personal_full_text(self, scope, request, limit):
        self._called("personal_full_text")
        query_terms = _tokens(request.question)
        hits = []
        for _, candidate in self._personal_candidates(scope):
            score = len(query_terms & _tokens(candidate.text)) / max(1, len(query_terms))
            if score > 0:
                hits.append(CandidateHit(candidate, score))
        return sorted(hits,
                      key=lambda hit: (-hit.score, hit.candidate.candidate_id))[:limit]

    def personal_vector(self, scope, request, embedding, limit):
        self._called("personal_vector")
        hits = [CandidateHit(candidate, _cosine(embedding, record["embedding"]))
                for record, candidate in self._personal_candidates(scope)
                if record.get("embedding") is not None]
        return sorted(hits,
                      key=lambda hit: (-hit.score, hit.candidate.candidate_id))[:limit]

    def weekly_profile(self, request):
        self._called("weekly_profile")
        for record in self.payload.get("weekly_profiles", []):
            if (record.get("release_status") != "published" or
                    record.get("status") != "published"):
                continue
            candidate = WeeklyProfileCandidate.model_validate_json(json.dumps(record["candidate"]))
            if (candidate.corpus_version != self.payload.get("active_corpus_version") or
                    str(candidate.release_id) != self.payload.get("active_release_id")):
                continue
            if (candidate.journey.stage != request.journey.stage or
                    candidate.journey.unit != request.journey.unit or
                    candidate.journey.start != request.journey.start or
                    candidate.journey.end != request.journey.end):
                continue
            if (request.jurisdiction.upper() in candidate.jurisdiction or
                    "GLOBAL" in candidate.jurisdiction):
                return candidate
        return None

    def graph_paths(self, scope, request, max_depth, max_paths):
        self._called("graph")
        if not self._owns(scope):
            raise RetrievalDatabaseUnavailable(
                "authenticated owner does not own requested workspace")
        allowed_start = {"document", "fact", "restriction", "question",
                         "plan_item", "plan"}
        paths = []
        query_terms = _tokens(request.question)
        for record in self.payload.get("graph_paths", []):
            raw = record.get("path", record)
            keywords = set(record.get("keywords", []))
            if keywords and not (keywords & query_terms):
                continue
            if raw.get("workspace_id") != str(scope.workspace_id):
                continue
            raw_node_ids = [node.get("node_id") for node in raw.get("nodes", [])]
            if len(raw_node_ids) != len(set(raw_node_ids)):
                continue
            path = GraphPath.model_validate_json(json.dumps(raw))
            if (path.depth > min(max_depth, MAX_GRAPH_DEPTH) or
                    path.nodes[0].node_type not in allowed_start):
                continue
            paths.append(path)
        return sorted(paths, key=lambda path: (path.depth, path.path_id))[
            :min(max_paths, MAX_GRAPH_PATHS)]


class RetrievalGateway:
    """One deterministic, provider-neutral retrieval entry point."""

    def __init__(self, repository: RetrievalRepository, *,
                 embedding_provider: EmbeddingProvider | None,
                 cache: Stage5RetrievalCache | None = None,
                 corpus_version: str = "unreleased",
                 release_version: str = "none",
                 apply_ranking_improvement: bool = False) -> None:
        self.repository = repository
        self.embedding_provider = embedding_provider
        self.cache = cache or Stage5RetrievalCache()
        self.corpus_version = corpus_version
        self.release_version = release_version
        self.apply_ranking_improvement = apply_ranking_improvement
        self.ranking_version = (
            TRIAL_RANKING_VERSION if apply_ranking_improvement
            else BASE_RANKING_VERSION)

    @staticmethod
    def _component(name, status, started, attempted, returned, rejected=0,
                   retries=0, failure=None):
        return RetrievalComponentResult(
            component=name, status=status, attempted=attempted, returned=returned,
            rejected_by_filters=rejected,
            latency_ms=(perf_counter() - started) * 1000,
            retries=retries, failure=failure)

    @staticmethod
    def _public_eligible(candidate, request, *, vector):
        if (candidate.release_status != "published" or
                candidate.source_status != "published" or
                candidate.candidate_status != "published" or
                "display" not in candidate.allowed_use or
                (vector and "embed" not in candidate.allowed_use)):
            return False
        if (candidate.evidence_lane not in request.evidence_lanes or
                candidate.domain != request.domain or
                candidate.journey.stage != request.journey.stage or
                candidate.journey.unit != request.journey.unit):
            return False
        if request.journey.unit != "none" and not (
                candidate.journey.start <= request.journey.start and
                candidate.journey.end >= request.journey.end):
            return False
        if (request.jurisdiction.upper() not in candidate.jurisdictions and
                "GLOBAL" not in candidate.jurisdictions):
            return False
        active = set(request.active_conditions)
        return (set(candidate.conditions_required).issubset(active) and
                not (set(candidate.conditions_excluded) & active))

    @staticmethod
    def _personal_eligible(candidate):
        return candidate.document_status == "confirmed"

    def _filter_hits(self, hits, request, *, public, vector):
        allowed, rejected, seen = [], [], set()
        expected_type = (PublicEvidenceCandidate if public
                         else PersonalPassageCandidate)
        for hit in hits:
            if not isinstance(hit, CandidateHit) or not isinstance(
                    getattr(hit, "candidate", None), expected_type):
                raise RetrievalInvalidCandidate(
                    "repository returned a malformed or wrong-lane candidate"
                )
            candidate_id = hit.candidate.candidate_id
            valid = (self._public_eligible(hit.candidate, request, vector=vector)
                     if public else self._personal_eligible(hit.candidate))
            if not valid:
                rejected.append(candidate_id)
            elif candidate_id not in seen:
                allowed.append(hit)
                seen.add(candidate_id)
        return allowed, rejected

    def _rank(self, components, limit):
        candidates, ranks, scores = {}, {}, {}
        for component in sorted(components):
            ordered = sorted(components[component],
                             key=lambda hit: (-hit.score,
                                              hit.candidate.candidate_id))
            for rank, hit in enumerate(ordered, start=1):
                candidate_id = hit.candidate.candidate_id
                candidates[candidate_id] = hit.candidate
                ranks.setdefault(candidate_id, {})[component] = rank
                scores.setdefault(candidate_id, {})[component] = hit.score
        rows = []
        for candidate_id, candidate in candidates.items():
            rrf = sum(1.0 / (RRF_K + rank)
                      for rank in ranks[candidate_id].values())
            if isinstance(candidate, PublicEvidenceCandidate):
                authority, applicability = (candidate.authority_score,
                                             candidate.applicability_score)
                exact_fit = candidate.journey.start == candidate.journey.end
                source_version = candidate.provenance.source_version
            else:
                authority = applicability = 1.0
                exact_fit, source_version = True, candidate.provenance.source_version
            # The sole tuned improvement is a small bounded authority/applicability
            # adjustment after reciprocal-rank fusion.
            final_score = (rrf + 0.0025 * authority + 0.0025 * applicability
                           if self.apply_ranking_improvement else rrf)
            rows.append((candidate_id, candidate, final_score, authority,
                         applicability, exact_fit, source_version))
        # Stable passes make every documented tie-break input observable:
        # candidate ID, source version, exact position fit, applicability, authority, score.
        rows.sort(key=lambda row: row[0])
        rows.sort(key=lambda row: row[6] or "", reverse=True)
        rows.sort(key=lambda row: row[5], reverse=True)
        rows.sort(key=lambda row: row[4], reverse=True)
        rows.sort(key=lambda row: row[3], reverse=True)
        rows.sort(key=lambda row: row[2], reverse=True)
        output = [RankedRetrievalCandidate(
            candidate_id=candidate_id,
            candidate_kind=("public_evidence"
                            if isinstance(candidate, PublicEvidenceCandidate)
                            else "personal_passage"),
            rank=index, final_score=score,
            component_ranks=ranks[candidate_id],
            component_scores=scores[candidate_id],
            authority_score=authority, applicability_score=applicability,
            exact_position_fit=exact_fit, source_version=source_version,
            stable_tie_breaker=candidate_id)
            for index, (candidate_id, candidate, score, authority, applicability,
                        exact_fit, source_version) in enumerate(rows[:limit], start=1)]
        return output, candidates

    def retrieve(
        self,
        request: RetrievalRequest,
        scope: AuthenticatedRetrievalScope,
        *,
        purpose: RetrievalPurpose = "public_guidance",
    ) -> RetrievalResult:
        """Retrieve under a trusted purpose; construct its fixed policy internally."""

        policy = build_evidence_policy(purpose, request.domain)
        started_at, clock = datetime.now(timezone.utc), perf_counter()
        normalized = normalize_query(request.question)
        components: list[RetrievalComponentResult] = []
        failures: list[RetrievalFailure] = []
        rejected_ids: list[str] = []

        # Resolve the owner/workspace/state boundary from the authenticated database
        # before deriving applicability or constructing either cache key.
        tick = perf_counter()
        personal_database_ok = True
        try:
            resolved_scope = self.repository.authenticated_scope(scope)
            full_exact = self.repository.exact_personal_context(resolved_scope, request)
            exact_count = sum((
                len(full_exact.confirmed_facts), len(full_exact.medications),
                len(full_exact.symptoms), len(full_exact.appointments),
                len(full_exact.plan_states), len(full_exact.open_questions),
                len(full_exact.unresolved_conflicts),
                len(full_exact.missing_information),
            ))
            components.append(self._component(
                "exact_sql", "ok", tick, 2, exact_count))
        except RetrievalDatabaseUnavailable:
            resolved_scope = scope
            full_exact = ExactPersonalContext()
            personal_database_ok = False
            failure = RetrievalFailure(
                code="database_unavailable", recoverable=True,
                component="exact_sql",
                detail=("Authenticated scope or personal state could not be "
                        "resolved; personalization is unavailable."))
            failures.append(failure)
            components.append(self._component(
                "exact_sql", "failed", tick, 2, 0, failure=failure))

        trusted_state, query = build_trusted_query(
            request, scope, resolved_scope, full_exact, policy)
        public_key = self.cache.public_key(
            query, corpus_version=self.corpus_version,
            release_version=self.release_version)
        personal_key = self.cache.personal_key(resolved_scope, query)

        vector: list[float] | None = None
        vector_unavailable_detail: str | None = None
        if self.embedding_provider is not None:
            try:
                vector = self.embedding_provider.embed([query.question])[0]
            except Exception:
                vector_unavailable_detail = (
                    "Embedding component unavailable; exact SQL and full text "
                    "remain active."
                )
        else:
            vector_unavailable_detail = (
                "No embedding provider configured; exact SQL and full text "
                "remain active."
            )

        public_needed = (
            "public_guidance" in policy.required_support
            and trusted_state.journey_relation != "unconfirmed_current"
        )
        public_entry = (
            self.cache.get_public(public_key)
            if public_needed else PublicCacheEntry([], [], None)
        )
        if public_entry is None:
            public_text: list[CandidateHit] = []
            public_vector: list[CandidateHit] = []
            tick = perf_counter()
            try:
                raw = self.repository.public_full_text(
                    query, query.max_candidates * 2)
                public_text, rejected = self._filter_hits(
                    raw, query, public=True, vector=False)
                rejected_ids.extend(rejected)
                retries = 0
                if rejected and not public_text:
                    retries = 1
                    raw = self.repository.public_full_text(
                        query, min(20, query.max_candidates * 4))
                    public_text, second = self._filter_hits(
                        raw, query, public=True, vector=False)
                    rejected_ids.extend(second)
                components.append(self._component(
                    "public_full_text", "degraded" if rejected else "ok",
                    tick, len(raw), len(public_text), len(rejected), retries))
            except RetrievalDatabaseUnavailable:
                failure = RetrievalFailure(
                    code="database_unavailable", recoverable=True,
                    component="public_full_text",
                    detail="Public full-text retrieval did not complete.")
                failures.append(failure)
                components.append(self._component(
                    "public_full_text", "failed", tick, 0, 0,
                    failure=failure))

            tick = perf_counter()
            if vector is None:
                failure = RetrievalFailure(
                    code="vector_unavailable", recoverable=True,
                    component="public_vector",
                    detail=vector_unavailable_detail or "Public vector retrieval unavailable.",
                )
                failures.append(failure)
                components.append(self._component(
                    "public_vector", "degraded", tick, 0, 0,
                    failure=failure))
            else:
                try:
                    raw = self.repository.public_vector(
                        query, vector, query.max_candidates * 2)
                    public_vector, rejected = self._filter_hits(
                        raw, query, public=True, vector=True)
                    rejected_ids.extend(rejected)
                    components.append(self._component(
                        "public_vector", "degraded" if rejected else "ok",
                        tick, len(raw), len(public_vector), len(rejected)))
                except (RetrievalDatabaseUnavailable,
                        RetrievalVectorUnavailable):
                    failure = RetrievalFailure(
                        code="vector_unavailable", recoverable=True,
                        component="public_vector",
                        detail=("Public vector retrieval failed; filtered full "
                                "text remains active."))
                    failures.append(failure)
                    components.append(self._component(
                        "public_vector", "degraded", tick, 0, 0,
                        failure=failure))

            tick = perf_counter()
            try:
                profile = self.repository.weekly_profile(query)
                components.append(self._component(
                    "weekly_profile", "ok", tick, 1,
                    1 if profile else 0))
            except RetrievalDatabaseUnavailable:
                profile = None
                failure = RetrievalFailure(
                    code="database_unavailable", recoverable=True,
                    component="weekly_profile",
                    detail="Weekly profile retrieval did not complete.")
                failures.append(failure)
                components.append(self._component(
                    "weekly_profile", "failed", tick, 1, 0,
                    failure=failure))
            public_entry = PublicCacheEntry(public_text, public_vector, profile)
            self.cache.put_public(public_key, public_entry)
        else:
            for name, count in (
                ("public_full_text", len(public_entry.full_text)),
                ("public_vector", len(public_entry.vector)),
                ("weekly_profile", int(public_entry.weekly_profile is not None)),
            ):
                components.append(RetrievalComponentResult(
                    component=name, status="skipped", attempted=0,
                    returned=count, rejected_by_filters=0, latency_ms=0.0))

        personal_entry = (
            self.cache.get_personal(personal_key, resolved_scope)
            if personal_database_ok else None
        )
        if personal_entry is None:
            personal_text: list[CandidateHit] = []
            personal_vector: list[CandidateHit] = []
            graph_paths: list[GraphPath] = []

            tick = perf_counter()
            if personal_database_ok:
                try:
                    raw = self.repository.personal_full_text(
                        resolved_scope, query, query.max_candidates * 2)
                    eligible, rejected = self._filter_hits(
                        raw, query, public=False, vector=False)
                    personal_text = [hit for hit in eligible
                                     if personal_passage_relevant(
                                         hit.candidate, policy, query.question,
                                         component="personal_full_text")]
                    relevance_rejected = [
                        hit.candidate.candidate_id for hit in eligible
                        if hit not in personal_text]
                    rejected.extend(relevance_rejected)
                    rejected_ids.extend(rejected)
                    components.append(self._component(
                        "personal_full_text",
                        "degraded" if rejected else "ok", tick,
                        len(raw), len(personal_text), len(rejected)))
                except RetrievalDatabaseUnavailable:
                    failure = RetrievalFailure(
                        code="database_unavailable", recoverable=True,
                        component="personal_full_text",
                        detail=("Personal full-text retrieval failed; no passage "
                                "personalization was used."))
                    failures.append(failure)
                    components.append(self._component(
                        "personal_full_text", "failed", tick, 0, 0,
                        failure=failure))
            else:
                components.append(self._component(
                    "personal_full_text", "skipped", tick, 0, 0))

            tick = perf_counter()
            if personal_database_ok and vector is not None:
                try:
                    raw = self.repository.personal_vector(
                        resolved_scope, query, vector,
                        query.max_candidates * 2)
                    eligible, rejected = self._filter_hits(
                        raw, query, public=False, vector=True)
                    personal_vector = [hit for hit in eligible
                                       if personal_passage_relevant(
                                           hit.candidate, policy, query.question,
                                           component="personal_vector")]
                    relevance_rejected = [
                        hit.candidate.candidate_id for hit in eligible
                        if hit not in personal_vector]
                    rejected.extend(relevance_rejected)
                    rejected_ids.extend(rejected)
                    components.append(self._component(
                        "personal_vector", "degraded" if rejected else "ok",
                        tick, len(raw), len(personal_vector), len(rejected)))
                except (RetrievalDatabaseUnavailable,
                        RetrievalVectorUnavailable):
                    failure = RetrievalFailure(
                        code="vector_unavailable", recoverable=True,
                        component="personal_vector",
                        detail=("Personal vector retrieval failed; exact SQL and "
                                "full text remain active."))
                    failures.append(failure)
                    components.append(self._component(
                        "personal_vector", "degraded", tick, 0, 0,
                        failure=failure))
            else:
                personal_failure = None
                if personal_database_ok:
                    personal_failure = RetrievalFailure(
                        code="vector_unavailable", recoverable=True,
                        component="personal_vector",
                        detail=(vector_unavailable_detail
                                or "Personal vector retrieval unavailable."),
                    )
                    failures.append(personal_failure)
                components.append(self._component(
                    "personal_vector",
                    "degraded" if personal_database_ok else "skipped",
                    tick, 0, 0, failure=personal_failure))

            tick = perf_counter()
            graph_requested = (
                personal_database_ok and query.include_graph
                and policy.purpose in {
                    "causal_explanation", "mixed_personalized_guidance"
                }
            )
            if graph_requested:
                try:
                    graph_paths = self.repository.graph_paths(
                        resolved_scope, query,
                        MAX_GRAPH_DEPTH, MAX_GRAPH_PATHS)
                    components.append(self._component(
                        "graph", "ok", tick, len(graph_paths),
                        len(graph_paths)))
                except RetrievalDatabaseUnavailable:
                    failure = RetrievalFailure(
                        code="database_unavailable", recoverable=True,
                        component="graph",
                        detail=("Graph traversal failed; no causal path was "
                                "returned."))
                    failures.append(failure)
                    components.append(self._component(
                        "graph", "failed", tick, 0, 0,
                        failure=failure))
            else:
                components.append(self._component(
                    "graph", "skipped", tick, 0, 0))

            personal_entry = PersonalCacheEntry(
                resolved_scope.workspace_id, resolved_scope.care_episode_id,
                resolved_scope.state_version, full_exact,
                personal_text, personal_vector, graph_paths)
            if personal_database_ok:
                self.cache.put_personal(personal_key, personal_entry)
        else:
            full_exact = personal_entry.exact
            for name, count in (
                ("personal_full_text", len(personal_entry.full_text)),
                ("personal_vector", len(personal_entry.vector)),
                ("graph", len(personal_entry.graph_paths)),
            ):
                components.append(RetrievalComponentResult(
                    component=name, status="skipped", attempted=0,
                    returned=count, rejected_by_filters=0, latency_ms=0.0))

        exact = minimise_personal_context(
            full_exact, trusted_state, policy, query.question)
        ranked, candidate_map = self._rank({
            "personal_full_text": personal_entry.full_text,
            "personal_vector": personal_entry.vector,
            "public_full_text": public_entry.full_text,
            "public_vector": public_entry.vector,
        }, query.max_candidates)
        chosen_ids = {item.candidate_id for item in ranked}
        public = [
            candidate for candidate_id, candidate in candidate_map.items()
            if candidate_id in chosen_ids
            and isinstance(candidate, PublicEvidenceCandidate)
        ]
        public.sort(key=lambda item: next(
            rank.rank for rank in ranked
            if rank.candidate_id == item.candidate_id))
        personal_passages = [
            candidate for candidate_id, candidate in candidate_map.items()
            if candidate_id in chosen_ids
            and isinstance(candidate, PersonalPassageCandidate)
        ]
        personal_passages.sort(key=lambda item: next(
            rank.rank for rank in ranked
            if rank.candidate_id == item.candidate_id))

        corpus_mode = (
            "controlled_fixture"
            if any(item.provenance.fixture_only for item in public)
            or (public_entry.weekly_profile is not None
                and public_entry.weekly_profile.fixture_only)
            else "production_release"
            if public or public_entry.weekly_profile is not None
            else "no_public_release"
        )
        requires_public = "public_guidance" in policy.required_support
        if requires_public and corpus_mode == "no_public_release":
            failures.append(RetrievalFailure(
                code="no_approved_public_content", recoverable=False,
                detail=("No approved public release matched; no public evidence "
                        "was fabricated.")))

        elapsed_ms = (perf_counter() - clock) * 1000
        timed_out = elapsed_ms > query.timeout_ms
        blocking_reasons: list[RuntimeBlocker] = []
        if not personal_database_ok:
            blocking_reasons.append("database_unavailable")
        if timed_out:
            blocking_reasons.append("retrieval_timeout")
            failures.append(RetrievalFailure(
                code="timeout", recoverable=True,
                detail=("Retrieval exceeded its bounded time budget; downstream "
                        "use must abstain.")))
        answerability = assess_answerability(
            policy, exact, len(public),
            public_entry.weekly_profile is not None,
            len(personal_passages), len(personal_entry.graph_paths),
            blocking_reasons=blocking_reasons)

        abstention_reason = derive_abstention_reason(answerability, corpus_mode)
        abstention_details = {
            "none": "",
            "database_unavailable": "Trusted personal state could not be established.",
            "retrieval_timeout": "Retrieval exceeded its bounded time budget.",
            "unresolved_conflict": "Relevant conflicting information requires clarification.",
            "missing_information": "Information required by this question is missing.",
            "partial_support": ("Some relevant evidence exists, but required support "
                                "for a complete answer is missing."),
            "no_approved_public_content": ("No eligible approved public evidence "
                                           "supports this question."),
            "no_eligible_evidence": ("No eligible evidence satisfies this question's "
                                     "policy."),
        }
        abstention = AbstentionState(
            should_abstain=abstention_reason != "none",
            reason=abstention_reason, detail=abstention_details[abstention_reason],
        )
        inventory = derive_packet_inventory(
            confirmed_facts=exact.confirmed_facts,
            personal_passages=personal_passages, medications=exact.medications,
            symptoms=exact.symptoms, appointments=exact.appointments,
            plan_states=exact.plan_states, open_questions=exact.open_questions,
            public_passages=public, weekly_profile=public_entry.weekly_profile,
            unresolved_conflicts=exact.unresolved_conflicts,
            missing_information=exact.missing_information,
        )
        packet = EvidencePacket(
            request_id=query.request_id,
            workspace_id=resolved_scope.workspace_id,
            care_episode_id=resolved_scope.care_episode_id,
            question=query.question, domain=query.domain,
            journey=query.journey,
            jurisdiction=query.jurisdiction.upper(),
            evidence_lanes=query.evidence_lanes,
            retrieval_policy=policy,
            trusted_state=trusted_state,
            answerability=answerability,
            confirmed_personal_facts=exact.confirmed_facts,
            permitted_personal_passages=personal_passages,
            medication_records=exact.medications,
            symptom_records=exact.symptoms,
            appointments=exact.appointments,
            plan_states=exact.plan_states,
            open_questions=exact.open_questions,
            weekly_profile=public_entry.weekly_profile,
            approved_guideline_passages=public,
            graph_paths=personal_entry.graph_paths,
            ranked_candidates=ranked,
            source_ids=inventory["source_ids"],
            evidence_ids=inventory["evidence_ids"],
            exact_spans=inventory["exact_spans"],
            provenance_versions={
                "schema": "5.0.0", "filter": FILTER_VERSION,
                "ranking": self.ranking_version,
                "policy": policy.policy_version,
                "corpus": self.corpus_version,
                "release": self.release_version},
            missing_information=exact.missing_information,
            unresolved_conflicts=exact.unresolved_conflicts,
            allowed_claim_types=inventory["allowed_claim_types"],
            required_citations=inventory["required_citations"],
            component_results=components, failures=failures,
            corpus_mode=inventory["corpus_mode"], abstention=abstention)

        completed_at = datetime.now(timezone.utc)
        digest = ranked_candidate_digest(ranked)
        trace = RetrievalTrace(
            request_id=query.request_id,
            started_at=started_at, completed_at=completed_at,
            total_latency_ms=(perf_counter() - clock) * 1000,
            normalized_query=normalized,
            jurisdiction=query.jurisdiction.upper(),
            public_cache_key=public_key,
            personal_cache_key=personal_key,
            filter_version=FILTER_VERSION,
            ranking_version=self.ranking_version,
            policy_id=policy.policy_id,
            policy_version=policy.policy_version,
            corpus_version=self.corpus_version,
            release_version=self.release_version,
            resolved_state_version=resolved_scope.state_version,
            journey_relation=trusted_state.journey_relation,
            component_results=components,
            rejected_candidate_ids=sorted(set(rejected_ids)),
            deterministic_order_digest=digest)
        return RetrievalResult(packet=packet, trace=trace)
