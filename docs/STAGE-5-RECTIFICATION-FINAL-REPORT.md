# Nestline Stage 5 second-rectification final report

> **Historical record:** This report describes the second rectification. Current final semantic-closure evidence is in STAGE-5-FINAL-CONSOLIDATED-CORRECTION-AND-STAGE-6-GATE.md.

**Prepared:** 12 September 2026
**Repository:** `kajalchourasia-cmd/nestline`
**Branch:** `feat/stage-1-governed-ingestion`
**Independently reviewed remote HEAD:** `3991896135eca094bc0ab0462f3e87c615469978`
**Corrected implementation commit:** `467422a62a3db31740a2d631538a73c2f34cc526`
**Verdict:** `READY FOR INDEPENDENT RE-REVIEW`

## 1. Root cause of each finding

1. **Policy cache collision:** the personal cache key described user/state/query identity but omitted retrieval policy identity. Graph eligibility and personal-passage eligibility depend on policy, so whichever purpose populated the cache first changed the later result.
2. **Candidate-limit collision:** both cache keys omitted `max_candidates`, while the cached component result had already been truncated. A small request could therefore starve a later larger request.
3. **Mutable evidence policy:** a `trusted_server_created` Boolean was treated as authority even though callers could construct the model and choose inconsistent fields.
4. **Contradictory contracts:** field-level types were valid, but no model-level invariant required EvidencePacket support, abstention and ordinary-generation fields to agree or required RetrievalResult packet/trace fields to match.
5. **Generic conflict relevance:** conflict matching relied too heavily on literal question tokens. A user had to know the word “conflict” or the proposed value; a generic category question could miss the unresolved state.
6. **Generic missing-information relevance:** the same token-only approach was fragile for category wording and singular/plural variants.

## 2. File-by-file change summary

| File | Change |
|---|---|
| `app/schemas/retrieval.py` | Adds canonical policy mapping/version and cross-field validators for policy, trusted query, EvidencePacket and RetrievalResult |
| `app/services/retrieval.py` | Gateway accepts purpose only; public/personal cache keys bind policy identity and effective candidate limit |
| `app/services/retrieval_policy.py` | Builds canonical policies and applies typed, policy-bounded category relevance for conflicts and missing information |
| `tests/test_retrieval.py` | Expands Stage 5 tests to 47, including shared-cache order, limit, policy, mutation and generic-category matrices |
| `scripts/build_stage5_fixtures.py` | Adds an isolated fictional conflict workspace and two frozen development cases |
| `scripts/run_stage5_retrieval_evals.py` | Uses the purpose-only gateway and reports the 28-case truth |
| `scripts/run_stage5_rectification_matrix.py` | New canonical generator for second-review before/after evidence and all requested matrices |
| `scripts/check_stage5.py` | Enforces regenerated artifacts, 28 cases, 47 tests and the rectification matrix |
| `scripts/check_stage5_retrieval_api.py` | Uses the purpose-only gateway boundary |
| `data/schemas/retrieval.schema.json` | Regenerated typed schema |
| `data/synthetic/stage5_retrieval_fixtures.json` | Regenerated fictional fixture |
| `evals/stage5_retrieval_development.jsonl` | Regenerated 28-case development truth |
| `docs/STAGE-5-RETRIEVAL-METRICS.json` | Regenerated metrics |
| `docs/STAGE-5-CHECK-RESULTS.json` | Regenerated gate result |
| `docs/STAGE-5-RECTIFICATION-EVIDENCE-PACKETS.json` | Regenerated corrected original-defect packets |
| `docs/STAGE-5-RECTIFICATION-REGRESSION-MATRIX.json` | New machine-readable second-rectification report |
| `docs/STAGE-5-IMPLEMENTATION.md` | Current implementation contract |
| `docs/STAGE-5-SELF-VERIFICATION-AND-STAGE-6-READINESS.md` | Complete verification, recovery and open-gate record |
| `docs/NESTLINE-STAGE-5-INDEPENDENT-REVIEW-AND-STAGE-6-HANDOFF.md` | Current independent-review checklist |
| `docs/STAGE-5-SECOND-RECTIFICATION-AND-RE-REVIEW-HANDOFF.md` | Dedicated second-review handoff |
| `docs/STAGE-5-RECTIFICATION-FINAL-REPORT.md` | This consolidated report |
| `docs/STAGE-5-PLAIN-LANGUAGE.md` | Updated nontechnical explanation |
| `docs/NESTLINE-EXECUTION-PLAN.md` | Current Stage 5 gate and counts |
| `docs/PROJECT-PROGRESS.md` | Current project status |
| `docs/DEMO-WORK-LOG.md` | Failure, recovery and final-evidence record |
| `docs/STAGE-5-RECTIFICATION-RESPONSE.md` | Marks the first rectification as historical/superseded |

Additional CI repair file: supabase/tests/stage3_onboarding.test.sql aligns its future-date assertion with the application India-date contract.

No migration or environment/configuration file changed.

## 3. Before-and-after reproductions

| Reproduction | Before on `3991896` | After |
|---|---|---|
| Public→causal, shared cache | causal paths 0; fresh paths 1; cached result unsupported | cached/fresh equivalent; required path present; fully supported |
| Causal→public, shared cache | public result inherited one graph path; fresh had none | cached/fresh equivalent; public result has no graph path |
| Public max 1→5 | cached large returned 2 IDs; fresh returned 5 | cached/fresh both return 5 |
| Personal max 1→5 | cached large returned 2 passages; fresh returned 5 | cached/fresh both return 5 |
| Fabricated public policy requiring only personal evidence | accepted and allowed ordinary generation for unsupported guidance | rejected before repository access |
| Unsupported packet with no abstention | accepted by schema | rejected by schema |
| Generic allergy question with unresolved allergy conflict | conflict hidden; fully supported; no abstention | conflict surfaced; clarification required; abstains |

## 4. Cache-order and max-candidate matrices

| Case | Result |
|---|---:|
| Public→causal | pass |
| Causal→public | pass |
| Personal→mixed | pass |
| Mixed→personal | pass |
| Public max-1→5 | pass |
| Public max-5→1 | pass |
| Personal max-1→5 | pass |
| Personal max-5→1 | pass |
| Caller stale version→server version | pass |
| Server state N→N+1 | pass |
| **Total** | **10/10** |

## 5. Policy rejection results

Ten of ten inconsistent/fabricated policies were rejected. The matrix mutates policy ID, policy version, purpose/domain combinations, required support and personal-context combinations. It also verifies that the gateway rejects a caller-supplied policy object before repository access.

## 6. Contract-mutation rejection results

Seventeen of seventeen contradictory mutations were rejected:

- 12 EvidencePacket mutations covering support/abstention, ordinary-generation permission, policy, scope, journey, conflict and missing-information alignment;
- 5 RetrievalResult mutations covering request ID, policy, state version, journey relation and component trace agreement.

## 7. Generic conflict and missing-information results

| Category | Conflict | Missing information |
|---|---:|---:|
| Allergies | pass | pass |
| Restrictions | pass | pass |
| Medications | pass | pass |
| Conditions | pass | pass |
| Appointments | pass | pass |
| Journey timing | pass | pass |
| **Total** | **6/6** | **6/6** |

A relevant unresolved category requires clarification/abstention. An unrelated appointment conflict or missing appointment does not block a supported movement request.

## 8. Verification results

### Python, content and stage gates

| Check | Result |
|---|---:|
| Compile | pass |
| Complete Python suite | 223/223 |
| Focused Stage 5 suite | 47/47 |
| Content authoring | pass: 63 profiles, 0 published, 31 sources, 55 evidence spans, 56 fragments |
| Content review-ready | pass with same inventory |
| Content contracts | 64/64 |
| Journey evaluations | 26/26 |
| Stage 1 | pass; includes 223 tests |
| Stage 2 | pass |
| Stage 3 UI | pass; 0 network calls |
| Stage 3 | pass |
| Stage 4 readiness | pass |
| Stage 4 UI | pass; 0 network calls |
| Stage 4 full | pass |
| Stage 5 behavior/support/journey | 28/28 each |
| Stage 5 rectification matrix | 49/49 |
| Stage 5 checker | pass |
| `git diff --check` | pass |

### Retrieval metrics

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

### Database

| Check | Result |
|---|---:|
| Exact Stage 4 → Stage 5 upgrade | pass; synthetic fixture survived/backfilled and was removed |
| Clean replay | pass; 15/15 migrations including Stage 5 |
| pgTAP | 254/254 across six files |
| Authenticated API | 70/70 across Stages 2–5 |
| Stage 5 authenticated API | 25/25 with two principals |
| Public/private schema lint | 0 findings |

## 9. Working-tree and commit status

- Branch remains `feat/stage-1-governed-ingestion`.
- Baseline commit remains `3991896135eca094bc0ab0462f3e87c615469978`.
- The Stage 5 implementation is committed at `467422a62a3db31740a2d631538a73c2f34cc526`; a documentation-only status commit follows it on the review branch.
- Publication to the review branch is authorized. Nothing was merged or deployed.
- No migration was added or modified.

## GitHub check repair

The first pushed run, 34636253179, passed validate but failed supabase-integration in the combined Stage 3 upgrade step. Local reproduction isolated the failure to the Stage 3 future-calculation-date pgTAP assertion. The test used PostgreSQL UTC current_date plus one, while the application validates against Asia/Kolkata. After midnight in India but before midnight UTC, the test value was India’s current date and was correctly accepted, causing the next assertion to see journey version 2.

The test now constructs tomorrow from the Asia/Kolkata date. After correction, both the Stage 3 to current upgrade path and clean replay pass 254/254 pgTAP assertions, 70/70 authenticated API checks and unscoped workflow lint with zero errors.
## 10. Remaining limitations and disagreements

No material review finding was rejected. The findings were reproducible and required correction.

Remaining limitations:

- deterministic SHA-256 fixture embeddings do not prove production semantic retrieval quality;
- 28 synthetic development questions are not a sealed clinical holdout;
- all 63 weekly profiles remain drafts and no production embeddings were created;
- clinical, India-localisation, licence, product/publication and production-provider reviews remain open;
- Stage 6 safety routing is absent;
- GitHub `validate` and `supabase-integration` must pass on the latest pushed branch head before merge.

## 11. Final verdict

`READY FOR INDEPENDENT RE-REVIEW`

This verdict applies to local Stage 5 engineering. Stage 6 remains blocked until this exact change set is independently accepted.
