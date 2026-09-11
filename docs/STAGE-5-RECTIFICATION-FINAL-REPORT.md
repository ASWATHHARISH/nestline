# Nestline Stage 5 rectification final report

**Prepared:** 11 September 2026
**Repository:** `kajalchourasia-cmd/nestline`
**Branch:** `feat/stage-1-governed-ingestion`
**Reviewed baseline:** `448eb6d2ab7b4e8cc7db9fc42ce5c523a7fe10a7`
**Rectification implementation commit:** dcec1f9e847a64185330ba4406a886bcced688b2
**Recommendation:** Stage 5 ready for independent re-review; Stage 6 remains blocked pending acceptance

## Plain-language root cause

The reviewed gateway treated any retrieved information as enough evidence. An unrelated allergy, medication, appointment, plan or private passage could therefore make an unsupported question look answerable. Relevant conflicts and missing information were also checked only after the broad evidence collection was empty.

The correction first identifies what support the question requires:

- public guidance requires eligible approved public evidence;
- a personal-record lookup requires a relevant confirmed record;
- mixed personalised guidance requires both public guidance and a relevant confirmed constraint;
- a causal explanation requires a permitted graph path.

Relevant conflicts, required missing information, database failure and retrieval timeout block ordinary generation even when some unrelated evidence exists.

## Reproduced defects: before and after

| Defect | Reviewed behavior | Corrected behavior |
|---|---|---|
| Week-25 hospital preparation question with no matching public evidence but unrelated private data | Public 0, personal facts 2, private passages 1, `should_abstain=false`, reason `none` | Public 0, relevant facts/passages 0/0, support `unsupported`, `should_abstain=true`, reason `no_approved_public_content` |
| Conflicting prenatal-yoga record plus unrelated confirmed information | Public 0, personal facts 2, private passages 1, conflict 1, `should_abstain=false`, reason `none` | Public 0, relevant constraint 1, unrelated passages 0, relevant conflict 1, support `clarification_required`, `should_abstain=true`, reason `unresolved_conflict` |

Full machine-readable packets are in `docs/STAGE-5-RECTIFICATION-EVIDENCE-PACKETS.json`.

## Implementation changes

| File | Purpose |
|---|---|
| `app/schemas/retrieval.py` | Twenty versioned contracts for requests, trusted state, evidence policy, candidates, answerability, failures, Evidence Packets and traces |
| `app/services/retrieval_policy.py` | Fixed server-side policies, database-derived journey/condition/state construction, relevance minimisation and support assessment |
| `app/services/retrieval.py` | Trusted scope before filters/cache, purpose-aware retrieval and explicit partial/conflict/missing/unsupported behavior |
| `scripts/build_stage5_fixtures.py` | Controlled multi-journey corpus and frozen 26-case truth |
| `scripts/run_stage5_retrieval_evals.py` | Vector, hybrid, ranking and graph experiments plus corrected packet generation |
| `scripts/export_retrieval_schema.py` | Regenerates all Stage 5 schemas |
| `scripts/check_stage5.py` | Deterministic rectification and independent-review gate |
| `scripts/check_stage5_retrieval_api.py` | Twenty-five authenticated Stage 5 API checks |
| `tests/test_retrieval.py` | Thirty-six Stage 5 contract, security, answerability, graph, cache and failure tests |
| Generated schema, fixture, truth and reports | Regenerated from repository scripts rather than edited to force a pass |
| Stage 5 and project-status documents | Updated to remove the obsolete five-case metrics and premature Stage 6 GO |

## Trusted-state and minimisation guarantees

- Workspace, care episode, owner and state version come from authenticated database scope.
- Current journey comes from confirmed Journey Resolver state.
- Active conditions/restrictions come from confirmed facts.
- Client text cannot override authenticated scope or cache state version.
- A clearly named other week is distinguished from a silent mismatch with current state.
- Generic terms such as `record` or `document` cannot expose an unrelated private passage.
- Medication remains record-only.
- Symptoms remain safety-evaluation-only and never imply that a situation is safe.
- Proposed, rejected, superseded and conflicted facts cannot personalise.
- Broader future safety context is represented separately; Stage 5 does not implement Stage 6.

## Verification results

| Verification | Result |
|---|---:|
| Complete Python suite | 212/212 passed |
| Focused Stage 5 Python suite | 36/36 passed |
| Content contracts | 64/64 passed |
| Journey evaluations | 26/26 passed |
| Frozen Stage 5 behavior | 26/26 passed |
| Recall@5 | 18/18 |
| Citation/evidence precision | 18/18 |
| Confirmed-personal-fact precision | 11/11 |
| Support-state accuracy | 26/26 |
| Journey-relation accuracy | 26/26 |
| Graph-path correctness | 1/1 |
| Wrong-week retrieval | 0 |
| Wrong-jurisdiction retrieval | 0 |
| Unapproved-source retrieval | 0 |
| Cross-workspace leakage | 0 |
| Conflict/proposal personalization violations | 0 |
| pgTAP | 254/254 passed |
| Authenticated API checks | 70/70 passed |
| Stage 1-4 regression gates | all passed |
| Nestline public/private schema lint | 0 findings |
| Git whitespace check | passed |
| Credential-shaped strings in changed files | 0 |

### pgTAP accounting

- Stage 2 security/lifecycle: 122/122
- Stage 3 exit hardening: 12/12
- Stage 3 onboarding: 26/26
- Stage 4 API role: 11/11
- Stage 4 document confirmation: 35/35
- Stage 5 retrieval: 48/48

### Authenticated API accounting

- Stage 2 Storage: 13/13
- Stage 3 onboarding: 17/17
- Stage 4 documents: 15/15
- Stage 5 retrieval: 25/25

### Database histories

- Exact Stage 4 to Stage 5 migration: passed.
- Clean migration replay through Stage 5: passed.
- No migration was added or modified during rectification.
- No remote migration was deployed.

## Experiments

The vector-only baseline retrieved 18/18 expected public evidence IDs but returned 27 public candidates, giving 18/27 precision. The adopted hybrid returned 18/18 expected IDs with 18/18 precision and 11/11 confirmed-personal-fact precision.

One ranking adjustment matched the hybrid result but produced no measurable improvement, so it was not adopted.

The graph-required case fails without graph support and succeeds 1/1 with graph support. The exact-SQL personal-record case is unchanged with graph enabled or disabled, so no false graph benefit is claimed.

## Failures and recovery

1. Both reported false-negative abstention defects were reproduced before the fix.
2. Final packet inspection found an unrelated peanut-allergy passage in the prenatal-yoga conflict packet because both contained the generic word `record`. Generic container terms can no longer establish private-passage relevance, and a regression assertion was added.
3. Unscoped database lint after pgTAP included third-party `extensions` functions and reported extension-internal findings. The final application lint explicitly checks Nestline's `public` and `private` schemas and returns zero findings.
4. A Windows document-editing pass introduced mojibake into three existing status files. They were restored from the reviewed commit and the intended status lines were reapplied using explicit UTF-8 I/O. The final scan found no mojibake.

## Remaining limitations and gates

- Deterministic SHA-256 fixture embeddings verify control flow, isolation and filters; they do not establish production semantic quality.
- Twenty-six synthetic development questions do not prove clinical retrieval quality and are not a sealed final holdout.
- All 63 weekly profiles remain drafts.
- Clinical, India-localisation, licence, product/publication and production-embedding reviews remain open.
- Stage 6 Safety Gate behavior is not implemented.
- Independent Stage 5 acceptance is required before Stage 6 begins.

## Review recommendation

Stage 5 is ready for independent re-review. It is not approved for Stage 6 engineering until the review is accepted, and it is not ready for public, clinical or production use.

No migration was deployed and no Stage 6 code was added.

