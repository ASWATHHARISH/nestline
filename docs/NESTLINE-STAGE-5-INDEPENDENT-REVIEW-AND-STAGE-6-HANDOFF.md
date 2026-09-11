# Nestline Stage 5 rectification: independent review and Stage 6 handoff

**Prepared:** 11 September 2026
**Repository:** `kajalchourasia-cmd/nestline`
**Branch:** `feat/stage-1-governed-ingestion`
**Reviewed/current HEAD:** `448eb6d2ab7b4e8cc7db9fc42ce5c523a7fe10a7`
**Rectification commit:** pending; local working tree only
**Engineering verdict:** ready for independent Stage 5 re-review
**Stage 6 verdict:** NO-GO until this review is accepted
**Public/clinical verdict:** NO-GO
**Remote actions:** none

## Review decision requested

Please decide whether the Stage 5 rectification correctly fixes answerability, trusted-state construction and personal-context minimisation while preserving the existing security, lifecycle, graph, cache, migration and Stage 1–4 guarantees.

Approval of this handoff permits Stage 6 engineering to begin. It does not approve clinical content, public release, production embeddings, agents or answer generation.

## Read in this order

1. `docs/STAGE-5-RECTIFICATION-RESPONSE.md`
2. `docs/STAGE-5-IMPLEMENTATION.md`
3. `docs/STAGE-5-PLAIN-LANGUAGE.md`
4. `docs/STAGE-5-SELF-VERIFICATION-AND-STAGE-6-READINESS.md`
5. `docs/STAGE-5-CHECK-RESULTS.json`
6. `docs/STAGE-5-RETRIEVAL-METRICS.json`
7. `docs/STAGE-5-RECTIFICATION-EVIDENCE-PACKETS.json`
8. `data/schemas/retrieval.schema.json`
9. `evals/stage5_retrieval_development.jsonl`

Architecture authorities remain:

- `docs/NESTLINE-EXECUTION-PLAN.md`
- `docs/Nestline updated architecture.md`
- `docs/STAGE-2-3-4-INDEPENDENT-REVIEW-RESPONSE-AND-STAGE-5-GATE.md`
- `docs/STAGE-4-REVIEW-HANDOFF.md`
- `docs/decisions/0003-owner-only-workspace-care-episode.md`
- `docs/decisions/0004-document-extraction-provider-selection.md`

## Review focus

| Area | Evidence | Reviewer question |
|---|---|---|
| Reproduced defects | rectification packets and tests | Do both old false-negative abstentions now fail closed for the correct reason? |
| Purpose-aware support | schemas, policy service, gateway | Can unrelated evidence ever satisfy a required support type? |
| Valid personal lookup | personal-record frozen cases | Can a confirmed allergy/medication/appointment be retrieved without public guidance? |
| Conflict/missing precedence | policy tests and packets | Does relevant conflict/missing information require clarification even when other evidence exists? |
| Relevance minimisation | policy service and conflict packet | Are unrelated records/passages absent from downstream context? |
| Trusted state | authenticated-scope RPC, gateway and tests | Are workspace, owner, journey, conditions and cache version database-derived? |
| Other-week questions | current mismatch/future-week cases | Is a clearly named other week preserved while silent client mismatch is overridden? |
| Hard filters | migration, pgTAP and evaluation | Are wrong-week/country/stage/lane/lifecycle/private decoys excluded before ranking? |
| Graph | RPC, tests and graph ablation | Is traversal bounded, deterministic, provenance-preserving and workspace-safe? |
| Cache | service/tests | Are public/personal entries isolated and invalidated by state/release/filter changes? |
| Regression | self-verification | Are all earlier gates and authenticated API checks still green? |
| Claims | all handoff documents | Are limitations and Stage 6/public gates stated without overclaiming? |

## Exact rectification results

### Defect 1

Unsupported week-25 hospital-preparation guidance with unrelated private data:

- before: public 0, facts 2, passages 1, `should_abstain=false`;
- after: public 0, relevant facts 0, relevant passages 0, support `unsupported`, `should_abstain=true`, reason `no_approved_public_content`.

### Defect 2

Relevant prenatal-yoga conflict with unrelated confirmed data:

- before: public 0, facts 2, passages 1, conflict 1, `should_abstain=false`;
- after: public 0, relevant constraint 1, unrelated passages 0, relevant conflict 1, support `clarification_required`, `should_abstain=true`, reason `unresolved_conflict`.

## Evidence inventory

| Item | Value |
|---|---:|
| Exported typed contracts | 20 |
| Frozen development cases | 26 |
| Planned domains covered | 7/7 |
| Focused Stage 5 Python tests | 36/36 |
| Complete Python suite | 212/212 |
| Content contracts | 64/64 |
| Journey cases | 26/26 |
| pgTAP assertions | 254/254 |
| Authenticated API checks | 70/70 |
| Stage 5 authenticated API checks | 25/25 |
| Published weekly profiles | 0/63 |
| Database lint findings | 0 |

## Retrieval metrics

| Metric | Result |
|---|---:|
| Recall@5 | 18/18 |
| Citation/evidence precision | 18/18 |
| Confirmed-personal-fact precision | 11/11 |
| Expected behavior | 26/26 |
| Support classification | 26/26 |
| Journey relation | 26/26 |
| Graph path | 1/1 |
| Wrong-week | 0 |
| Wrong-jurisdiction | 0 |
| Unapproved-source | 0 |
| Cross-workspace leakage | 0 |
| Conflict/proposal personalization violations | 0 |

The vector-only baseline achieved 18/18 recall but only 18/27 evidence precision. The adopted hybrid achieved 18/18 for both. The single ranking trial did not improve the hybrid and was not adopted. Graph-off fails the one relationship-required case; graph-on passes 1/1. The exact-SQL case is unchanged, so no graph benefit is claimed there.

## Required reviewer checks

1. Verify that `RetrievalRequest` rejects workspace, care episode, owner, state version, active conditions and purpose.
2. Verify that fixed policies are selected by trusted application code.
3. Verify that authenticated database state is resolved before public applicability and personal-cache lookup.
4. Verify that public guidance cannot be supported by an unrelated fact, medication, symptom, appointment, plan or private passage.
5. Verify that relevant conflict/missing information blocks ordinary generation.
6. Verify that irrelevant conflict/missing information does not block a fully supported question.
7. Verify that generic terms such as “record” cannot expose an unrelated private passage.
8. Verify that proposed, rejected, superseded and conflicted facts do not personalise.
9. Verify medication record-only and symptom safety-evaluation-only outputs.
10. Verify graph depth, cycle, start-node and workspace constraints.
11. Verify exact Stage 4 upgrade, clean replay, all pgTAP files and both-principal API tests.
12. Verify that no Stage 6 implementation or public-release claim is included.

## Migration and deployment status

The rectification adds no migration and changes no existing migration. It relies on `20260911001300_stage5_hybrid_retrieval.sql`, which passed exact Stage 4 upgrade and clean replay locally.

No migration was deployed. No code was pushed or merged. No commit was created for this rectification.

## Limitations the reviewer must preserve

- SHA-256 fixture embeddings are deterministic test vectors, not evidence of production semantic quality.
- Twenty-six synthetic questions do not establish clinical retrieval quality or replace a sealed holdout.
- The public corpus used by tests is isolated controlled fixture data.
- All 63 real weekly profiles remain draft.
- Clinical, India-localisation, licence, rendered-product/publication and production-provider gates remain open.
- Stage 6 safety routing is absent.

## Reviewer response template

```text
Stage 5 rectification verdict: ACCEPT / RETURN FOR CHANGES

Defect 1 answerability:
Defect 2 conflict handling:
Trusted-state boundary:
Personal-context minimisation:
Security/filter/cache/graph regression:
Migration and authenticated API evidence:
Documentation accuracy:
Required corrections:
Permission to begin Stage 6 engineering: YES / NO
```

## Current recommendation

Stage 5 is ready for independent re-review. Begin Stage 6 only after an independent reviewer accepts this exact rectification set. Keep public, clinical and production use blocked.
