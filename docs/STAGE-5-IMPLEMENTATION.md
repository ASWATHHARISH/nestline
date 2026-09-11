# Stage 5 implementation: hybrid retrieval and causal graph

**Updated:** 12 September 2026
**Branch:** `feat/stage-1-governed-ingestion`
**Final consolidated review baseline:** `2a067945986d68f85fba6234b9cb59be90a90eab`
**Current authoritative evidence:** `STAGE-5-FINAL-CONSOLIDATED-CORRECTION-AND-STAGE-6-GATE.md`
**Stage 6 status:** not started

## Scope

Stage 5 supplies one read-only Retrieval Gateway for future specialists. It combines exact SQL, PostgreSQL full-text search, pgvector discovery and bounded PostgreSQL graph traversal. It filters candidates before ranking, merges eligible candidates deterministically, isolates public and personal caches, and returns a typed Evidence Packet with explicit support and failure states.

The final consolidated correction adds one canonical semantic-validation boundary across answerability, journey state, category relevance, graph structure, packet inventories, trace identity and failure behavior. The final evidence set contains 56 focused Stage 5 tests, 232 total Python tests and 212 generated adversarial matrix cases. See the authoritative evidence file above for exact results and the Stage 6 gate.

It does not generate health answers, implement safety routing, confirm personal facts, write graph state, select a production embedding provider, publish draft health content or deploy a public application.

## Answerability and policy contract

The gateway identifies the evidence required by the trusted request purpose before retrieval:

| Purpose | Required evidence |
|---|---|
| `public_guidance` | eligible approved public guidance |
| `personal_record_lookup` | relevant confirmed personal record |
| `causal_explanation` | permitted bounded graph path |
| `mixed_personalized_guidance` | eligible public guidance plus a relevant confirmed constraint |

`RetrievalGateway.retrieve()` accepts a purpose enum and constructs the policy internally. The `EvidenceRequirementPolicy` schema independently enforces the exact canonical ID, version, purpose, domain, required-support sequence and personal-context sequence. A caller cannot fabricate or weaken a policy.

`AnswerabilityAssessment` separates public support, personal-record support, constraints and graph support. It reports fully supported, partially supported, unsupported or clarification-required. Relevant conflicts, required missing information, database failure and timeout prevent ordinary generation even when unrelated evidence exists.

The second review found five remaining defects on remote HEAD `3991896`: policy-dependent personal-cache reuse, max-candidate cache truncation, caller-constructible policies, contradictory packets/results, and generic category questions that could hide conflicts. Each was reproduced before correction.

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

Cross-field validation requires the packet and result to agree on request ID, authenticated workspace/care episode, state version, effective journey, policy, domain, answerability, abstention, ordinary-generation permission and component traces. Unsupported, partial or clarification-required packets must abstain. Schema mutation tests reject contradictory combinations.

## Trusted-state construction

`RetrievalRequest` does not accept workspace ID, care-episode ID, owner ID, state version or active conditions.

For every request, the gateway:

1. resolves owner-only scope with `stage5_authenticated_scope` and the authenticated session subject;
2. reads confirmed exact personal state;
3. accepts current journey only from confirmed Journey Resolver output;
4. derives active conditions and restrictions only from confirmed facts;
5. distinguishes the current journey, an explicit other-week question, a mismatch overridden to current state and an unconfirmed current state;
6. uses the database-derived state version in the personal cache key;
7. applies the same trusted journey and conditions to public applicability filters.

A legitimate explicit future-week question retains that requested week. A silent or ambiguous mismatch cannot change current personalised applicability.

## Retrieval components

### Exact SQL

Exact SQL retrieves confirmed allergies, conditions, restrictions, journey state, document-derived facts, medication records, appointments, saved/stale plans and open clarification questions. Vector similarity is never used to guess an exact date, medication, week, allergy or restriction.

### Public full-text and vector search

Public components filter before ranking by publication/release state, approved lane, current corpus/source/release version, stage, exact week or valid range, pregnancy/postpartum unit, jurisdiction, domain, condition applicability and retirement state.

Development uses isolated fixture releases because the repository still contains zero published weekly profiles.

### Personal full-text and vector search

Private candidates must belong to the authenticated workspace and care episode and to confirmed, conflict-free documents. Only relevant confirmed records enter ordinary context. Generic terms such as `record` and `document` cannot expose unrelated private text.

Generic category questions map singular/plural terms and typed fields to allergies, restrictions, medications, conditions, appointments and journey timing. Matching unresolved conflicts or required missing information surface even when the user does not type “conflict” or a proposed value. Policy boundaries keep unrelated conflicts from blocking an otherwise supported request.

Broader symptom, allergy and medication context belongs to the explicit future safety-context contract. Stage 5 does not implement the Stage 6 Safety Gate.

### Bounded graph

The graph remains in PostgreSQL. Traversal starts only from permitted nodes, remains in the authenticated workspace, stops at depth four and eight paths, protects against cycles and orders results deterministically. It preserves node/edge types and provenance for:

`document -> confirmed restriction or unresolved conflict -> affected plan item -> stale plan or clarification question`

Stage 5 reads graph state and never writes or confirms it.

## Deterministic ranking

Eligible full-text and vector candidates are merged with stable reciprocal-rank fusion using `RRF_K = 60`. Tie-breaking includes component ranks/scores, authority, applicability, week fit, source version and candidate identity. Maximum candidate counts are deterministic and bounded.

A typed learned-reranker input exists for later measured work. The one Stage 5 ranking trial produced no improvement and was not adopted.

## Cache separation and invalidation

Public cache keys include normalized query/domain, stage and week/range, jurisdiction, evidence lane, corpus/release/filter version, canonical policy ID/version/purpose/required support and effective `max_candidates`.

Personal cache keys include workspace, care episode, database-derived state version, normalized query/filter version, canonical policy identity and required support, allowed personal-context kinds and effective `max_candidates`.

Public cache entries reject personal payloads. State, release or filter changes alter the appropriate key. The 10-case shared-cache matrix proves:

- public and causal policies do not exchange graph paths;
- personal and mixed policies do not exchange private passages;
- max-1 then max-5 and max-5 then max-1 equal fresh retrieval for public and personal results;
- caller-supplied stale state versions cannot control cache identity;
- confirmed server state N and N+1 do not share personal results.

## Failure behavior

The gateway returns typed failures and abstention for no eligible evidence, no approved public content, partial support, relevant unresolved conflict, required missing information, invalid candidates after one retry, vector degradation, database unavailability, malformed requests and retrieval timeout.

A vector failure may fall back only to supported SQL/full-text behavior and is labelled degraded. A database failure never claims personalized success. Medication stays record-only. Symptom retrieval stays safety-evaluation-only and never treats “no match” as safe.

## Files and generated artifacts

- `app/schemas/retrieval.py`
- `app/services/retrieval.py`
- `app/services/retrieval_policy.py`
- `tests/test_retrieval.py`
- `scripts/build_stage5_fixtures.py`
- `scripts/export_retrieval_schema.py`
- `scripts/run_stage5_retrieval_evals.py`
- `scripts/run_stage5_rectification_matrix.py`
- `scripts/check_stage5.py`
- `scripts/check_stage5_retrieval_api.py`
- `data/schemas/retrieval.schema.json`
- `data/synthetic/stage5_retrieval_fixtures.json`
- `evals/stage5_retrieval_development.jsonl`
- `docs/STAGE-5-RETRIEVAL-METRICS.json`
- `docs/STAGE-5-CHECK-RESULTS.json`
- `docs/STAGE-5-RECTIFICATION-EVIDENCE-PACKETS.json`
- `docs/STAGE-5-RECTIFICATION-REGRESSION-MATRIX.json`
- `docs/STAGE-5-SECOND-RECTIFICATION-AND-RE-REVIEW-HANDOFF.md`

## Database and configuration impact

No database migration changed in this rectification. The existing additive `20260911001300_stage5_hybrid_retrieval.sql` remains the Stage 5 database contract. It passed exact Stage 4 → Stage 5 upgrade and clean replay locally, along with 254/254 pgTAP assertions and 70/70 authenticated API checks.

No environment variable, provider key, paid model or service-role credential was added. No migration was deployed.

## Limitations and status

Deterministic SHA-256 fixture embeddings verify contracts, filtering, cache behavior and repeatability. They do not establish production semantic quality. The 28-case synthetic set is development truth, not a sealed clinical holdout. All 63 weekly profiles remain drafts. Clinical, India-localisation, licence, product/publication and production-provider reviews remain open.

The local implementation is `READY FOR INDEPENDENT RE-REVIEW`. Stage 6 remains blocked until this exact rectification is independently accepted. GitHub checks must pass on the latest pushed branch head before merge.
