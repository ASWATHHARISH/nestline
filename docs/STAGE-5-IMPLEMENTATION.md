# Stage 5 implementation: hybrid retrieval and causal graph

**Implemented and locally verified:** 11 September 2026
**Scope:** typed, read-only retrieval over controlled public and personal fixtures
**Engineering verdict:** locally complete for Stage 6 engineering
**Public or clinical release:** blocked by the open gates below
**Implementation commit:** a1f0489cd7b16cf2391cab58b8e558432c4f4bba

## What Stage 5 now does

Stage 5 provides one Retrieval Gateway for future specialists. It reads exact personal
state with SQL, finds terminology with PostgreSQL full-text search, discovers similar
passages with pgvector, and follows bounded causal links in the existing PostgreSQL
graph. It merges passage candidates with deterministic reciprocal-rank fusion.

The gateway produces a typed EvidencePacket. It does not generate a health answer,
interpret symptoms, confirm facts, change medication, save state, or write a plan.

Request -> server-derived owner scope -> hard filters -> SQL + full text + vector +
bounded graph -> deterministic rank -> EvidencePacket and trace.

## Implemented architecture requirements

| Requirement | Implemented result |
|---|---|
| One gateway | app/services/retrieval.py exposes one RetrievalGateway and one repository protocol for future specialists. |
| Typed contracts | Version 5.0.0 Pydantic contracts and generated JSON Schema cover requests, authenticated scope, public and personal candidates, graph paths, ranked candidates, reranker input, missing/conflict/abstention states, EvidencePacket and trace/result. |
| Server scope | RetrievalRequest has no workspace or care-episode field. public.stage5_authenticated_scope derives the owner-only workspace/care episode and state version from auth.uid(). |
| Exact personal state | public.stage5_exact_personal_context reads journey state, confirmed facts, record-only medication, evaluation-only symptoms, appointments, plans and open questions. Conflicts are separate. |
| Public full text | A generated tsvector and GIN index support PostgreSQL full-text search. Release, source, chunk, lane, stage, unit, range, country, domain, condition, corpus and release filters run in SQL first. |
| Public vector | pgvector searches only the exact allowed release and corpus, requires published lifecycle states and both embed/display permission, and applies all applicability filters first. |
| Personal passages | Full-text and vector RPCs require the authenticated owner and retrieve only confirmed, scanned, conflict-free documents in that workspace. |
| Weekly profile | The RPC returns only an exact published profile from the requested release. The repository still has 63 drafts and zero published profiles, so production retrieval returns none. |
| Deterministic rank | Reciprocal-rank fusion uses stable component ranks/scores and deterministic tie breaks for score, authority, applicability, exact position, source version and candidate ID. |
| Reranker boundary | A typed RerankerInput exists and learned_reranker_enabled is fixed to false. One score trial was measured and rejected because it did not improve Recall@5 or precision. |
| Causal graph | PostgreSQL recursive traversal starts only at document nodes, stays in one owner workspace, clamps depth to four and paths to eight, prevents cycles and orders results deterministically. |
| Required path | Controlled database and in-memory fixtures prove document -> restriction -> affected plan item -> stale plan. Conflict/question output remains a permitted future branch. |
| Cache separation | Public and personal cache entries use different types and stores. Public keys bind query/applicability/corpus/release/filter versions. Personal keys bind workspace/care episode/state/query/filter versions. |
| Failure behavior | Typed failures cover vector degradation, database failure, timeout, invalid candidates and no approved content. Missing information and unresolved conflicts cause explicit abstention/clarification. |
| Provider neutrality | Tests use deterministic SHA-256 fixture embeddings. No paid model or private model credential is required. |
| Read-only boundary | Stage 5 RPCs are stable security-invoker reads. Authenticated product retrieval uses a publishable key and user JWT, never a service-role key. |

## Contract inventory

The exported data/schemas/retrieval.schema.json contains 15 top-level contracts:

1. RetrievalRequest
2. AuthenticatedRetrievalScope
3. PublicEvidenceCandidate
4. PersonalFactCandidate
5. PersonalPassageCandidate
6. GraphPath
7. RankedRetrievalCandidate
8. RerankerInput
9. MissingInformation
10. UnresolvedConflict
11. AbstentionState
12. RetrievalFailure
13. EvidencePacket
14. RetrievalTrace
15. RetrievalResult

EvidencePacket includes request and server scope, question/domain, exact or approximate
journey position, country, confirmed facts, permitted private passages, weekly profile,
approved guideline passages, graph paths, exact spans, IDs, provenance versions,
missing information, unresolved conflicts, allowed claim types, required citations,
component results and failure states.

## Database migration

supabase/migrations/20260911001300_stage5_hybrid_retrieval.sql is additive after
migration 01200. It:

- extends the graph vocabulary while preserving existing UUID graph identities;
- supports release-bound text identities for public weekly/evidence graph nodes;
- adds generated full-text columns and GIN indexes;
- adds owner-readable personal retrieval versions and state-change triggers;
- creates authenticated scope, exact SQL, public/private full-text, public/private
  vector, weekly-profile and bounded-graph RPCs;
- retains hardened legacy Stage 1-4 retrieval RPCs for regression compatibility;
- applies RLS and least-privilege grants.

It was tested from the exact Stage 4 boundary, from the deployed Stage 3 boundary,
and from an empty database. No migration was deployed remotely.

## Files added

- app/schemas/retrieval.py
- app/services/retrieval.py
- data/schemas/retrieval.schema.json
- data/synthetic/stage5_retrieval_fixtures.json
- evals/stage5_retrieval_development.jsonl
- scripts/build_stage5_fixtures.py
- scripts/export_retrieval_schema.py
- scripts/run_stage5_retrieval_evals.py
- scripts/check_stage5.py
- scripts/check_stage5_retrieval_api.py
- supabase/migrations/20260911001300_stage5_hybrid_retrieval.sql
- supabase/tests/stage5_hybrid_retrieval.test.sql
- supabase/fixtures/stage5_stage4_upgrade.sql
- supabase/fixtures/stage5_stage4_upgrade_check.sql
- tests/test_retrieval.py
- docs/STAGE-5-CHECK-RESULTS.json
- docs/STAGE-5-RETRIEVAL-METRICS.json
- docs/STAGE-5-IMPLEMENTATION.md
- docs/STAGE-5-PLAIN-LANGUAGE.md
- docs/STAGE-5-SELF-VERIFICATION-AND-STAGE-6-READINESS.md
- docs/NESTLINE-STAGE-5-INDEPENDENT-REVIEW-AND-STAGE-6-HANDOFF.md

## Files changed

- .github/workflows/data-contracts.yml: adds the Stage 5 deterministic gate, exact
  Stage 4 upgrade proof and authenticated Stage 5 API checks.
- app/schemas/storage.py: aligns graph contracts with the approved architecture node
  vocabulary and release-bound public graph identities.
- app/services/foundation.py: excludes the downstream Stage 5 retrieval fixture from
  the Stage 0 human-review fingerprint.
- tests/test_foundation.py: locks that review-fingerprint boundary.
- supabase/tests/stage2_security_and_lifecycle.test.sql: updates the old expectation
  so unconfirmed private chunks remain excluded after Stage 5 hardening.
- docs/NESTLINE-EXECUTION-PLAN.md, docs/PROJECT-PROGRESS.md and
  docs/DEMO-WORK-LOG.md: record the local Stage 5 result without claiming release.

## Configuration impact

No new secret or paid account is required. Deterministic CI uses the existing Python,
Node, Docker and local Supabase setup. Production use will later require an approved
embedding provider/model and a published content release, but neither is selected here.

## Boundaries retained

Stage 5 does not implement the Stage 6 Safety Gate, agents, answer generation,
answer validation, dashboard/chat, production uploads or State Committer writes.
Medication stays record-only. Symptoms stay safety-evaluation-only. No-match never
means safe. No live web search is used for runtime health answers.