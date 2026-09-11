# Stage 5 rectification response before Stage 6

> **Historical first-rectification record:** This file records the earlier correction at `dcec1f9e`. It is superseded for current status by `STAGE-5-SECOND-RECTIFICATION-AND-RE-REVIEW-HANDOFF.md`, which covers the independent return for changes against `3991896`.

**Prepared:** 11 September 2026
**Branch:** `feat/stage-1-governed-ingestion`
**Reviewed baseline:** 448eb6d2ab7b4e8cc7db9fc42ce5c523a7fe10a7
**Rectification implementation commit:** dcec1f9e847a64185330ba4406a886bcced688b2
**Recommendation:** ready for independent Stage 5 re-review; Stage 6 remains blocked pending that review
**Remote publication:** implementation commit pushed to upstream/feat/stage-1-governed-ingestion; no merge or deployment

## Review conclusion

The two central findings in `NESTLINE-STAGE-5-RECTIFICATION-BEFORE-STAGE-6.md` were technically correct and were reproduced on the reviewed commit before code changes.

The old gateway made one broad decision: if any public passage, personal fact, private passage, medication, symptom, appointment, plan state, question or graph path existed, the request was treated as having evidence. That allowed unrelated private data to make an unsupported question appear answerable. It also checked conflicts and missing information only when the broad evidence collection was empty.

The correction replaces that rule with a trusted, purpose-aware evidence policy. It distinguishes public guidance, personal-record lookup, personal constraints and graph relationships, then decides whether each required kind of support is satisfied by relevant evidence. Relevant conflicts and required missing information block ordinary generation even when other evidence exists.

## Independent assessment of the review

| Review finding | Assessment | Action |
|---|---|---|
| Unsupported public guidance could be unblocked by unrelated personal data | Confirmed on reviewed commit | Reproduced, fixed and frozen as `S5-DEFECT-PUBLIC-001` |
| Relevant conflict could be hidden by unrelated confirmed data | Confirmed on reviewed commit | Reproduced, fixed and frozen as `S5-DEFECT-CONFLICT-001` |
| Answerability needed purpose/evidence requirements | Confirmed | Added four fixed server-side policies and typed support states |
| Trusted journey/conditions/state boundary was incomplete | Confirmed | Rebuilt applicability and cache state from authenticated database results |
| Personal context was too broad | Confirmed | Added query/domain/purpose minimisation and a separate safety snapshot contract |
| More targeted cases were required | Confirmed | Expanded the frozen set from 5 to 26 cases across every planned domain |
| Always abstain without a public release | Rejected as a universal rule | Public-guidance policies require public support; personal-record policies can be fully supported by relevant confirmed records |

There is no material architecture disagreement with the attached review. The one design qualification above follows the review requirement that valid personal-record questions must work without public guidance.

## Before and after: reproduced defects

| Case | Reviewed commit `448eb6d2` | Corrected result |
|---|---|---|
| Public preparation question at week 25, no public evidence, unrelated private data present | public 0; personal facts 2; personal passages 1; `should_abstain=false`; reason `none` | public 0; relevant facts 0; relevant passages 0; support `unsupported`; `should_abstain=true`; reason `no_approved_public_content` |
| Conflicting prenatal-yoga record plus unrelated confirmed data | public 0; personal facts 2; personal passages 1; conflicts 1; `should_abstain=false`; reason `none` | public 0; relevant constraint facts 1; relevant passages 0; relevant conflicts 1; support `clarification_required`; `should_abstain=true`; reason `unresolved_conflict` |

Full machine-readable before summaries and corrected Evidence Packets are in `docs/STAGE-5-RECTIFICATION-EVIDENCE-PACKETS.json`.

## Corrected design

### Trusted state boundary

The client request contains the question, domain, requested journey target, jurisdiction and retrieval controls. It cannot supply workspace, care episode, owner, state version, active conditions or retrieval purpose.

The gateway:

1. derives owner identity from the authenticated session;
2. resolves the owner-only workspace and care episode through `stage5_authenticated_scope`;
3. reads confirmed Journey Resolver state and confirmed facts;
4. creates a trusted state using the database state version;
5. distinguishes current journey, an explicitly requested other week, an untrusted mismatch overridden to current state and a missing/unconfirmed current state;
6. derives active conditions only from confirmed state;
7. constructs both applicability filters and personal cache keys from that trusted state.

A stale caller state version is recorded for traceability but never used as the cache version.

### Purpose-aware support

The fixed policies are:

| Purpose | Required support |
|---|---|
| `public_guidance` | approved public guidance |
| `personal_record_lookup` | relevant confirmed personal record |
| `causal_explanation` | permitted bounded graph relationship |
| `mixed_personalized_guidance` | approved public guidance and relevant confirmed personal constraint |

The answerability assessment reports `fully_supported`, `partially_supported`, `unsupported` or `clarification_required`. Ordinary generation is allowed only for fully supported packets with no database/timeout blocker.

### Context minimisation

Exact records and personal passages are filtered by trusted purpose, domain and meaningful query subject. Generic container words such as “record,” “document” and “week” cannot by themselves expose an unrelated private passage. The conflict example therefore carries the relevant movement restriction and conflict, while excluding the unrelated peanut-allergy passage.

Medication remains record-only. Symptoms remain safety-evaluation-only and never imply safety. The broader `SafetyContextSnapshot` is a separate typed contract for a future reviewed Safety Gate; Stage 5 does not perform Stage 6 routing.

## Changed implementation and evidence

| File | Change |
|---|---|
| `app/schemas/retrieval.py` | Added versioned policy, trusted state/query, support assessment and safety-context contracts; removed trusted fields from the client request |
| `app/services/retrieval_policy.py` | Added trusted-state construction, four fixed evidence policies, relevance minimisation and answerability assessment |
| `app/services/retrieval.py` | Resolves authenticated state before filters/cache, applies purpose-aware retrieval and returns explicit partial/conflict/missing/unsupported states |
| `scripts/build_stage5_fixtures.py` | Builds the expanded controlled corpus and 26-case frozen truth |
| `data/synthetic/stage5_retrieval_fixtures.json` | Regenerated controlled fixture corpus |
| `evals/stage5_retrieval_development.jsonl` | Regenerated frozen 26-case development set |
| `scripts/run_stage5_retrieval_evals.py` | Evaluates ordered vector, hybrid, ranking and graph experiments and writes corrected packets |
| `scripts/export_retrieval_schema.py` | Exports all 20 Stage 5 contract schemas |
| `data/schemas/retrieval.schema.json` | Regenerated schema bundle |
| `scripts/check_stage5.py` | Enforces rectification artifacts, contract/truth coverage and Stage 6 re-review gate |
| `scripts/check_stage5_retrieval_api.py` | Verifies the trusted database state/policy boundary through authenticated APIs |
| `tests/test_retrieval.py` | Expanded to 36 Stage 5 contract, answerability, security, cache, graph and failure tests |
| `docs/STAGE-5-RETRIEVAL-METRICS.json` | Regenerated from the frozen development set |
| `docs/STAGE-5-RECTIFICATION-EVIDENCE-PACKETS.json` | Added reviewed-commit reproduction and corrected full packets |
| Stage 5 review documents | Rewritten to reflect the rectified implementation and actual verification totals |

## Database and configuration impact

No migration was added or changed by this rectification. The implementation continues to use `supabase/migrations/20260911001300_stage5_hybrid_retrieval.sql`.

The existing migration was tested both as an exact Stage 4 to Stage 5 upgrade and in a clean replay. All database runs were local. No remote migration was deployed. No paid embedding or model credential is required.

## Verification record

| Verification | Result |
|---|---:|
| Complete Python suite | 212/212 passed |
| Focused Stage 5 Python tests | 36/36 passed |
| Content contract evaluations | 64/64 passed |
| Journey evaluations | 26/26 passed |
| Frozen Stage 5 behaviors | 26/26 passed |
| Recall@5 | 18/18 = 1.00 |
| Citation/evidence precision | 18/18 = 1.00 |
| Confirmed-personal-fact precision | 11/11 = 1.00 |
| Graph-path correctness | 1/1 = 1.00 |
| Support-state accuracy | 26/26 = 1.00 |
| Journey-relation accuracy | 26/26 = 1.00 |
| Wrong-week results | 0 |
| Wrong-jurisdiction results | 0 |
| Unapproved-source results | 0 |
| Cross-workspace leakage | 0 |
| Conflict/proposal personalization violations | 0 |
| Database pgTAP | 254/254 passed |
| Authenticated API checks | 70/70 passed |
| Database lint | 0 findings in Nestline public/private schemas |
| Stage 1–4 gates | all passed |
| git diff --check | passed after artifact generation |

## Remaining limitations and gates

- Fixture embeddings are deterministic SHA-256 test vectors. They verify interfaces, filters and repeatability; they do not establish production semantic-retrieval quality.
- The 26 cases are a small synthetic development set, separate from a future sealed holdout. They do not prove clinical quality.
- Weekly profiles remain 63 drafts and 0 published. Controlled fixture releases do not authorize production embeddings or public answers.
- Clinical, India-localisation, licence, product/publication and production-provider reviews remain open with their human owners.
- Stage 6 safety behavior is not implemented and must not be inferred from Stage 5.
- Independent Stage 5 re-review remains the gate before Stage 6 engineering begins.

## Local decision

Stage 5 is locally ready for independent re-review. The regenerated Stage 5 checker is green; the final Git check was rerun after documentation cleanup.

The rectification implementation commit was pushed to the review branch. Nothing was merged or deployed, and no Stage 6 code was created.
