# Nestline Stage 5 final consolidated correction: review handoff

**Prepared:** 12 September 2026
**Repository:** `kajalchourasia-cmd/nestline`
**Branch:** `feat/stage-1-governed-ingestion`
**Final consolidated review baseline:** `2a067945986d68f85fba6234b9cb59be90a90eab`
**Authoritative evidence:** `STAGE-5-FINAL-CONSOLIDATED-CORRECTION-AND-STAGE-6-GATE.md`
**Engineering verdict:** `STAGE 5 ACCEPTED FOR CONTROLLED ENGINEERING`
**Stage 6 verdict:** `STAGE 6 ENGINEERING MAY BEGIN` as a separate controlled task
**Verified implementation:** `aeae51c42017edc6010f89ba4ff20d1e2f8a13ef`; workflow [34647636253](https://github.com/kajalchourasia-cmd/nestline/actions/runs/34647636253); nothing merged or deployed

## Review decision requested

Please review the final consolidated evidence file first. It verifies the earlier cache/policy changes and closes the remaining cross-field semantics across answerability, trusted journey state, category relevance, graph paths, evidence inventories, packet/trace identity and component failures. The current local evidence is 56/56 focused Stage 5 tests, 232/232 total Python tests and 212/212 generated adversarial cases.

Acceptance permits a separate Stage 6 implementation to begin. It does not approve clinical content, public release, production embeddings, agents, answer generation or deployment.

## Read in this order

1. `docs/STAGE-5-FINAL-CONSOLIDATED-CORRECTION-AND-STAGE-6-GATE.md`
2. `docs/STAGE-5-SELF-VERIFICATION-AND-STAGE-6-READINESS.md`
3. `docs/STAGE-5-IMPLEMENTATION.md`
4. `docs/STAGE-5-PLAIN-LANGUAGE.md`
5. `docs/STAGE-5-CHECK-RESULTS.json`
6. `docs/STAGE-5-RETRIEVAL-METRICS.json`
7. `docs/STAGE-5-RECTIFICATION-EVIDENCE-PACKETS.json`
8. `docs/STAGE-5-RECTIFICATION-REGRESSION-MATRIX.json`
9. `data/schemas/retrieval.schema.json`
10. `evals/stage5_retrieval_development.jsonl`

Architecture authorities remain the execution plan, updated architecture, Stage 2–4 response/gate, Stage 4 handoff and decisions 0003/0004.

## Independently reproduced findings

| Finding | Reviewed behavior on `3991896` | Corrected behavior |
|---|---|---|
| Public→causal shared cache | causal request reused graph-free public cache and abstained | cached and fresh causal results match and contain the required path |
| Causal→public shared cache | public guidance inherited a graph path | cached and fresh public results match and contain no graph path |
| Max 1→5 | public and personal larger requests reused truncated candidates | cached and fresh max-5 results match |
| Fabricated policy | public guidance could be configured to require only personal evidence | gateway builds a canonical policy; inconsistent models fail validation |
| Contradictory contracts | unsupported packet with no abstention validated | packet/result cross-field contradictions fail validation |
| Generic conflict | generic allergy wording hid an unresolved allergy conflict | conflict is returned, clarification is required and the packet abstains |

The two answerability defects from the first review remain fixed.

## Evidence inventory

| Item | Result |
|---|---:|
| Exported typed contracts | 20 |
| Frozen development cases | 28 |
| Planned domains covered | 7/7 |
| Focused Stage 5 Python tests | 56/56 |
| Complete Python suite | 232/232 |
| Cache equivalence matrix | 10/10 |
| Policy rejection matrix | 10/10 |
| Contract mutation matrix | 17/17 |
| Generic conflict matrix | 6/6 |
| Generic missing-information matrix | 6/6 |
| Content contracts | 64/64 |
| Journey cases | 26/26 |
| pgTAP assertions | 254/254 |
| Authenticated API checks | 70/70 |
| Published weekly profiles | 0/63 |
| Application-schema lint findings | 0 |

## Retrieval metrics

| Metric | Result |
|---|---:|
| Recall@5 | 18/18 |
| Citation/evidence precision | 18/18 |
| Confirmed-personal-fact precision | 12/12 |
| Expected behavior | 28/28 |
| Support classification | 28/28 |
| Journey relation | 28/28 |
| Graph path | 1/1 |
| Wrong-week | 0 |
| Wrong-jurisdiction | 0 |
| Unapproved-source | 0 |
| Cross-workspace leakage | 0 |
| Conflict/proposal personalization violations | 0 |
| Forbidden evidence IDs | 0 |

The vector-only baseline achieved 18/18 recall and 18/27 precision. The adopted hybrid achieved 18/18 for recall and precision. The single ranking trial did not improve the hybrid and was not adopted. Graph-off fails the one graph-required relationship case; graph-on passes 1/1. Exact SQL already solves the control lookup, so no graph benefit is claimed for it.

## Required reviewer checks

1. Verify that the gateway accepts a trusted purpose enum and constructs the policy internally.
2. Mutate policy ID/version/purpose/domain/support/context fields and confirm all noncanonical combinations fail before repository access.
3. Reuse one cache in both public↔causal and personal↔mixed orders; compare every result with a fresh request.
4. Run max-1↔max-5 in both directions for public and personal candidates.
5. Mutate packet/result support, abstention, scope, journey, policy, request ID, state version and trace fields.
6. Ask generic category questions for allergies, restrictions, medications, conditions, appointments and journey timing; verify matching conflicts/missing fields surface.
7. Verify unrelated conflicts/missing fields do not block unrelated supported requests.
8. Recheck workspace isolation, server-derived state version/journey/conditions, pre-ranking lifecycle/week/jurisdiction filters, medication record-only behavior and symptom safety-evaluation-only behavior.
9. Recheck bounded, cycle-safe and workspace-safe graph traversal.
10. Reproduce exact Stage 4 → Stage 5 upgrade, clean replay, all pgTAP and both-principal authenticated API checks.
11. Preserve the fixture-only and zero-public-release limitations.
12. Confirm Stage 6 remains absent.

## Migration, deployment and CI status

This rectification adds or changes no migration. Existing migration `20260911001300_stage5_hybrid_retrieval.sql` passed exact Stage 4 upgrade and clean local replay.

Implementation commit `467422a62a3db31740a2d631538a73c2f34cc526` is authorized for publication on this review branch. Nothing was merged or deployed. GitHub `validate` and `supabase-integration` must pass on the latest pushed branch head before merge.

## Limitations

- SHA-256 fixture embeddings are deterministic test vectors, not evidence of production semantic quality.
- Twenty-eight synthetic questions do not establish clinical retrieval quality or replace a sealed holdout.
- The public corpus used in tests is isolated controlled fixture data.
- All 63 real weekly profiles remain draft.
- Clinical, India-localisation, licence, rendered-product/publication and production-provider gates remain open.
- Stage 6 safety routing is absent.

## Reviewer response template

~~~text
Stage 5 second-rectification verdict: ACCEPT / RETURN FOR CHANGES

Policy-bound cache identity:
Candidate-limit cache identity:
Canonical policy boundary:
EvidencePacket/RetrievalResult invariants:
Generic conflict/missing relevance:
Prior security/filter/graph regression:
Migration and authenticated API evidence:
Documentation accuracy:
Required corrections:
Permission to begin Stage 6 engineering: YES / NO
~~~

## Current recommendation

`READY FOR INDEPENDENT RE-REVIEW` locally. Begin Stage 6 only after an independent reviewer accepts this exact change set.
