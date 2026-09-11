# Stage 5 implementation: hybrid retrieval and causal graph

**Updated:** 11 September 2026
**Branch:** `feat/stage-1-governed-ingestion`
**Reviewed baseline:** 448eb6d2ab7b4e8cc7db9fc42ce5c523a7fe10a7
**Rectification implementation commit:** dcec1f9e847a64185330ba4406a886bcced688b2
**Stage 6 status:** not started

## Scope

Stage 5 supplies one read-only Retrieval Gateway for future specialists. It combines exact SQL, PostgreSQL full-text search, pgvector discovery and bounded PostgreSQL graph traversal. It filters candidates before ranking, merges eligible candidates deterministically, isolates public and personal caches, and returns a typed Evidence Packet with explicit support and failure states.

It does not generate health answers, implement safety routing, confirm personal facts, write graph state, select a production embedding provider, publish draft health content or deploy a public application.

## Answerability correction

The reviewed implementation treated any retrieved item as proof that a question was answerable. Unrelated private records could therefore prevent abstention, and relevant conflicts could be masked by unrelated evidence.

Stage 5 now uses a trusted `EvidenceRequirementPolicy` selected by server code:

| Purpose | Required evidence |
|---|---|
| `public_guidance` | eligible approved public guidance |
| `personal_record_lookup` | relevant confirmed personal record |
| `causal_explanation` | permitted bounded graph path |
| `mixed_personalized_guidance` | eligible public guidance plus a relevant confirmed constraint |

`AnswerabilityAssessment` separates public support, personal-record support, constraints and graph support. It reports full, partial, unsupported or clarification-required support. Relevant conflicts, required missing information, database failure and timeout prevent ordinary generation even when other evidence exists.

## Typed contract inventory

The exported schema contains 20 versioned contracts:

1. retrieval request;
2. authenticated scope;
3. evidence requirement policy;
4. trusted retrieval state;
5. trusted retrieval query;
6. answerability assessment;
7. safety context snapshot;
8. public evidence candidate;
9. personal fact candidate;
10. personal passage candidate;
11. graph path;
12. ranked candidate;
13. reranker input;
14. missing information;
15. unresolved conflict;
16. abstention;
17. retrieval failure;
18. Evidence Packet;
19. retrieval trace;
20. retrieval result.

The Evidence Packet records the request and authenticated scope, requested/effective journey, jurisdiction, purpose, support assessment, relevant confirmed context, weekly/public evidence, graph paths, exact spans, citations, provenance versions, conflicts, missing information, allowed claim types, component results, degradations and abstention.

## Trusted-state construction

`RetrievalRequest` does not accept workspace ID, care-episode ID, owner ID, state version, active conditions or purpose.

For every request, the gateway:

1. resolves scope with `stage5_authenticated_scope` and the authenticated session subject;
2. reads confirmed exact personal state;
3. accepts the current journey only from confirmed Journey Resolver output;
4. derives active conditions and restrictions only from confirmed facts;
5. distinguishes current journey, an explicit other-week question, a mismatch overridden to current state and an unconfirmed current state;
6. uses the database-derived state version in the personal cache key;
7. applies the same trusted journey and conditions to public applicability filters.

A legitimate explicit future-week question retains that requested week. A silent or ambiguous mismatch cannot change the user’s current personalized applicability.

## Retrieval components

### Exact SQL

Exact SQL retrieves confirmed allergies, conditions, restrictions, journey state, document-derived facts, medication records, appointments, saved/stale plans and open clarification questions. Vector similarity is never used to guess an exact date, medication, week, allergy or restriction.

### Public full-text and vector search

Both public components use the same hard filters before ranking:

- published source, chunk and release;
- approved evidence lane;
- current source/corpus/release version;
- stage and exact week or valid range;
- pregnancy/postpartum/possible-pregnancy unit;
- country/jurisdiction;
- domain;
- required and excluded conditions;
- retirement/lifecycle state.

Development uses isolated fixture releases because the repository still contains zero published weekly profiles.

### Personal full-text and vector search

Private candidates must belong to the resolved workspace and care episode and to confirmed, conflict-free documents. Full-text candidates must match a meaningful query subject. Generic words such as “record” and “document” cannot expose unrelated private text. Deterministic fixture-vector hits are discovery candidates only and do not count as answer support without meaningful relevance.

Only relevant confirmed records enter the ordinary Evidence Packet. Broader symptom/allergy/medication context is represented by a separate future safety-context contract.

### Bounded graph

The graph stays in PostgreSQL. Traversal starts only from permitted nodes, remains inside the authenticated workspace, stops at depth four and eight paths, prevents repeated nodes and orders results deterministically. It preserves node/edge types and provenance for:

`document -> confirmed restriction or unresolved conflict -> affected plan item -> stale plan or clarification question`

Stage 5 reads graph state and never writes or confirms it.

## Deterministic ranking

Eligible full-text and vector candidates are merged with stable reciprocal-rank fusion using `RRF_K = 60`. Stable tie-breaking includes component ranks/scores, authority, applicability, week fit, source version and candidate identity. Maximum candidate counts are bounded.

A typed learned-reranker input exists for later measured work. The one Stage 5 ranking trial produced no improvement and was not adopted.

## Cache separation and invalidation

Public cache keys include normalized query/domain, journey stage and week/range, jurisdiction, evidence lane, corpus/release/filter version.

Personal cache keys include workspace, care episode, database-derived state version, normalized query and filter version.

Public cache entries reject personal payloads. Confirmed state changes invalidate personal retrieval versions. Release or filter changes change public keys. Tests prove that one workspace cannot reuse another workspace’s result.

## Failure behavior

The gateway returns typed failures and abstention for:

- no eligible evidence;
- no approved public content;
- partial support;
- relevant unresolved conflict;
- required missing information;
- invalid/wrong-week candidates after at most one retry;
- vector degradation;
- database unavailability;
- malformed typed request;
- retrieval timeout.

A vector failure may fall back to explicitly supported SQL/full-text behavior and is labelled degraded. A database failure never claims personalized success. Symptom retrieval never treats “no match” as safe.

## Files and generated artifacts

- `app/schemas/retrieval.py`
- `app/services/retrieval.py`
- `app/services/retrieval_policy.py`
- `data/schemas/retrieval.schema.json`
- `data/synthetic/stage5_retrieval_fixtures.json`
- `evals/stage5_retrieval_development.jsonl`
- `scripts/build_stage5_fixtures.py`
- `scripts/export_retrieval_schema.py`
- `scripts/run_stage5_retrieval_evals.py`
- `scripts/check_stage5.py`
- `scripts/check_stage5_retrieval_api.py`
- `tests/test_retrieval.py`
- `docs/STAGE-5-RETRIEVAL-METRICS.json`
- `docs/STAGE-5-CHECK-RESULTS.json`
- `docs/STAGE-5-RECTIFICATION-EVIDENCE-PACKETS.json`

## Database impact

No database migration changed during rectification. The existing additive migration `20260911001300_stage5_hybrid_retrieval.sql` remains the Stage 5 database contract, with RLS and least-privilege authenticated RPCs. It has been exercised locally from the exact Stage 4 migration and from a clean database history.

No migration was deployed and no service-role credential is used by ordinary retrieval.

## Limitations

Deterministic SHA-256 fixture embeddings verify contracts, filters, cache behavior and repeatability. They do not establish production semantic quality. The 26-case synthetic set is development truth, not a sealed clinical holdout. Human clinical, India-localisation, licence, product and publication reviews remain open. Stage 6 Safety Gate behavior is still absent.

See `docs/STAGE-5-RECTIFICATION-RESPONSE.md` and `docs/STAGE-5-SELF-VERIFICATION-AND-STAGE-6-READINESS.md` for reproduced defects, exact results and the re-review gate.
