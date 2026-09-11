# Stage 5 final consolidated correction and Stage 6 gate

**Prepared:** 12 September 2026
**Repository:** `kajalchourasia-cmd/nestline`
**Branch:** `feat/stage-1-governed-ingestion`
**Reviewed starting commit:** `2a067945986d68f85fba6234b9cb59be90a90eab`
**Verified implementation commit:** `aeae51c42017edc6010f89ba4ff20d1e2f8a13ef`
**Verified implementation workflow:** [34647636253](https://github.com/kajalchourasia-cmd/nestline/actions/runs/34647636253)
**Stage 6 engineering gate:** `STAGE 5 ACCEPTED FOR CONTROLLED ENGINEERING — STAGE 6 ENGINEERING MAY BEGIN`
**Public or clinical release:** `NO-GO`

## Plain-language result

The review was correct about one shared weakness: an Evidence Packet could contain fields that each looked valid while disagreeing about what evidence was present, whether the request was answerable, which journey state applied, or why retrieval failed. The fix creates shared derivation functions and makes both packet construction and validation use them. A changed or incomplete packet now fails validation instead of reaching a future answer generator.

All seven Stage 5 findings have been implemented locally. The complete Python suite, Stage 1–5 checks, database migrations, 254 pgTAP assertions, 70 authenticated API checks and database lint pass. No Stage 6 implementation, migration change, production provider, UI, agent, deployment or real medical data was added.

The generated Stage 5 checker intentionally continues to report `ready_for_stage6_engineering=false` because it is a deterministic pre-acceptance artifact. That gate was not bypassed in code. The final independent checklist in the supplied review is now complete, and both required GitHub jobs passed on the exact implementation commit.

## Independent verification of the review

The repository and remote review branch both started at `2a067945986d68f85fba6234b9cb59be90a90eab`, with a clean working tree. The execution plan and updated architecture were reread. They introduced no newer conflicting Stage 5 requirement, and no Stage 6 runtime was present.

Before the fix, the consolidated mutation probe accepted 10 invalid states:

- fully supported while required support was missing;
- satisfied support whose source Boolean was false;
- clarification without a conflict or missing item;
- unresolved-conflict reason without a conflict;
- contradictory current-journey relation;
- graph path from another workspace;
- removed evidence inventory;
- packet/trace question mismatch;
- reversed trace chronology;
- failed component without a failure object.

The ordinary-generation-with-conflict probe initially appeared rejected only because that ad-hoc Python probe supplied a string where strict validation required a UUID object. The equivalent JSON/deserialization mutation was accepted before the fix. It is now covered in the canonical matrix and rejected for the intended semantic reason. This probe issue did not change the implementation scope.

## Corrections implemented

| Finding | Result | Evidence |
|---|---|---|
| S5-FINAL-01 — canonical answerability and abstention | PASS | `derive_answerability_values()` derives ordered satisfied/missing support and the only valid state; `derive_abstention_reason()` enforces blocker precedence; runtime blockers and abstention reasons are typed. Covered by `test_answerability_and_abstention_are_canonically_derived` and `test_abstention_reasons_and_precedence_are_fixed`. |
| S5-FINAL-02 — trusted journey relationship | PASS | All four journey relations enforce the review truth table and preserve the server state-version boundary. Covered by `test_all_trusted_journey_relations_enforce_the_truth_table`. |
| S5-FINAL-03 — category-specific missing information | PASS | A broad support label can no longer make allergies block an appointment lookup or another unrelated category. Positive and all ordered pairwise category cases cover allergy, restriction, medication, condition, appointment and journey. Covered by `test_missing_information_is_category_specific_pairwise`. |
| S5-FINAL-04 — graph meaning and workspace binding | PASS | Every path must match the packet workspace; every edge must connect its adjacent declared nodes; existing cycle/depth/path limits remain. Covered by `test_graph_workspace_edges_and_trace_binding_are_strict`. |
| S5-FINAL-05 — packet inventory and applicability | PASS | Shared helpers derive IDs, sources, spans, citations, claims and ranking digest. Validators enforce rank/kind/tie-breaker consistency, corpus mode, lane, domain, journey, week, jurisdiction, conditions, source versions, rights, span hashes and profile applicability. Covered by `test_packet_inventory_applicability_and_span_mutations_are_rejected`. |
| S5-FINAL-06 — packet and trace binding | PASS | Result validation binds normalized question, jurisdiction, request/scope/state identity, policy and provenance versions, ranking digest, journey relation and chronological timestamps. Covered by `test_graph_workspace_edges_and_trace_binding_are_strict`. |
| S5-FINAL-07 — failure and blocker consistency | PASS | Component status/failure ownership is strict, vector failures are component-correct, packet and trace failures agree, database/timeout blockers imply the matching abstention reason, and malformed repository candidates raise a typed fail-closed exception. Covered by `test_component_failure_and_blocker_semantics_are_strict` and `test_malformed_repository_candidate_raises_typed_failure`. |

## File-by-file change inventory

| File | Why it changed |
|---|---|
| `app/schemas/retrieval.py` | Adds typed blocker/reason/corpus/claim fields and the shared semantic derivations; enforces answerability, journey, graph, inventory, applicability, provenance, trace, ranking and failure invariants. |
| `app/services/retrieval_policy.py` | Uses the canonical answerability derivation and limits conflict/missing relevance to the requested category or an explicit global requirement. |
| `app/services/retrieval.py` | Builds packets and traces with the shared derivations, correct component failures, typed blockers and fail-closed candidate handling. |
| `tests/test_retrieval.py` | Adds nine focused semantic-closure tests and repairs two synthetic fixtures so their span parent IDs and corpus versions are internally consistent. |
| `scripts/run_stage5_rectification_matrix.py` | Expands the generated adversarial matrix from 49 to 212 cases across all consolidated review groups. |
| `scripts/check_stage5.py` | Enforces the new test and generated-matrix totals. |
| `data/schemas/retrieval.schema.json` | Regenerated from the final typed contracts. |
| `docs/STAGE-5-RECTIFICATION-REGRESSION-MATRIX.json` | Regenerated 212-case matrix report. |
| `docs/STAGE-5-RECTIFICATION-EVIDENCE-PACKETS.json` | Regenerated valid packet examples. |
| `docs/STAGE-5-RETRIEVAL-METRICS.json` | Regenerated frozen-development retrieval experiment results. |
| `docs/STAGE-5-CHECK-RESULTS.json` | Regenerated deterministic Stage 5 gate evidence. |
| `docs/STAGE-5-FINAL-CONSOLIDATED-CORRECTION-AND-STAGE-6-GATE.md` | This final human-readable evidence and handoff. |
| Current Stage 5 status documents | Point reviewers to this report and distinguish earlier rectification evidence from the current final closure. |

No file under `supabase/migrations` changed.

## Consolidated adversarial matrix

The matrix is generated by `scripts.run_stage5_rectification_matrix`; its total is not manually guessed.

| Group | Passed |
|---|---:|
| Cache equivalence and invalidation | 10/10 |
| Canonical policy rejection | 10/10 |
| Earlier cross-contract mutations | 17/17 |
| Generic conflict relevance | 6/6 |
| Generic missing-information relevance | 6/6 |
| Final answerability and abstention | 23/23 |
| Trusted journey truth table | 12/12 |
| Pairwise conflict relevance | 36/36 |
| Pairwise missing-information relevance | 36/36 |
| Packet inventory and applicability | 26/26 |
| Graph, trace, failure and blocker consistency | 26/26 |
| Representative valid policy packets | 4/4 |
| **Total** | **212/212** |

Machine-readable report: `docs/STAGE-5-RECTIFICATION-REGRESSION-MATRIX.json`.

## Retrieval evaluation

The same frozen 28-case synthetic development truth was used. No sealed holdout answer was used for tuning.

| Metric | Result |
|---|---:|
| Expected behavior | 28/28 |
| Support-state classification | 28/28 |
| Journey-relation classification | 28/28 |
| Recall@5 | 18/18 |
| Citation/evidence precision | 18/18 |
| Confirmed-personal-fact precision | 12/12 |
| Expected graph paths | 1/1 |
| Wrong-week retrievals | 0 |
| Wrong-jurisdiction retrievals | 0 |
| Unapproved-source retrievals | 0 |
| Cross-workspace leakage | 0 |
| Conflict/proposal personalization violations | 0 |

The vector-only baseline retained 18/18 Recall@5 but achieved 18/30 citation precision and could not provide exact-personal, graph, answerability or journey behavior. Hybrid retrieval achieved the results above. Graph-on adds the one expected document → restriction → stale-plan path; graph-off correctly omits it. The allergy-record case is solved by SQL with graph on or off, so no false graph benefit is claimed.

## Verification evidence

| Evidence | Actual result |
|---|---|
| Starting branch commit | `2a067945986d68f85fba6234b9cb59be90a90eab` |
| Verified implementation commit | `aeae51c42017edc6010f89ba4ff20d1e2f8a13ef`; the final response records the later documentation-only branch head because a Git commit cannot contain its own hash |
| Files changed | Listed above; final `git diff --name-only` is recorded before commit |
| S5-FINAL-01 | PASS — two focused tests plus matrix cases |
| S5-FINAL-02 | PASS — journey truth-table test and 12/12 matrix cases |
| S5-FINAL-03 | PASS — missing and conflict pairwise tests; 72/72 pairwise cases |
| S5-FINAL-04 | PASS — graph workspace/adjacency test plus existing bound/cycle tests |
| S5-FINAL-05 | PASS — packet inventory/applicability/span mutation test; 26/26 matrix cases |
| S5-FINAL-06 | PASS — graph/trace binding test and matrix mutations |
| S5-FINAL-07 | PASS — failure/blocker and malformed-candidate tests |
| Consolidated adversarial matrix | 212/212; `docs/STAGE-5-RECTIFICATION-REGRESSION-MATRIX.json` |
| Stage 5 development evaluation | behavior 28/28; support 28/28; journey 28/28 |
| Retrieval metrics | Recall@5 18/18; citation precision 18/18; prohibited counts all 0 |
| Compilation | PASS |
| Focused Stage 5 tests | 56/56 |
| Complete Python suite | 232/232 |
| Content validation | PASS; 63 profiles, 0 published, 31 sources, 55 evidence candidates, 56 fragments |
| Review-ready content validation | PASS with the same governed draft inventory |
| Content contract evaluations | 64/64 |
| Journey evaluations | 26/26 |
| Stage 1–5 checkers | PASS/5; Stage 5 remains explicitly gated for independent acceptance |
| Streamlit smoke checks | PASS/2 — Stage 3 and Stage 4 |
| Exact Stage 4 → Stage 5 migration | PASS from `20260911001200` through existing `20260911001300`, with synthetic upgrade fixtures removed |
| Clean migration replay | PASS |
| pgTAP | 254/254 across 6 files: 122 + 12 + 26 + 11 + 35 + 48 |
| Authenticated API checks | 70/70: Stage 2 13/13, Stage 3 17/17, Stage 4 15/15, Stage 5 25/25 |
| Database lint | PASS; 0 findings in `public` and `private` |
| Migration/configuration impact | None; no migration, deployed database, environment variable or provider configuration changed |
| Git whitespace check | PASS; `git diff --check` returned no errors |
| GitHub `validate` | PASS on `aeae51c`; [job 103422107877](https://github.com/kajalchourasia-cmd/nestline/actions/runs/34647636253/job/103422107877) |
| GitHub `supabase-integration` | PASS on `aeae51c`; [job 103422107642](https://github.com/kajalchourasia-cmd/nestline/actions/runs/34647636253/job/103422107642) |
| Stage 6 code included | NO |

## Commands executed

~~~powershell
.venv\Scripts\python.exe -m scripts.build_stage5_fixtures
.venv\Scripts\python.exe -m scripts.export_retrieval_schema
.venv\Scripts\python.exe -m scripts.run_stage5_retrieval_evals --write-report
.venv\Scripts\python.exe -m scripts.run_stage5_rectification_matrix --write-report
.venv\Scripts\python.exe -m scripts.check_stage5 --write-report
.venv\Scripts\python.exe -m compileall -q app scripts tests
.venv\Scripts\python.exe -m unittest tests.test_retrieval -v
.venv\Scripts\python.exe -m unittest discover -s tests -q
.venv\Scripts\python.exe -m scripts.validate_content
.venv\Scripts\python.exe -m scripts.validate_content --require-review-ready
.venv\Scripts\python.exe -m scripts.run_contract_evals
.venv\Scripts\python.exe -m scripts.run_journey_evals
.venv\Scripts\python.exe -m scripts.check_stage1
.venv\Scripts\python.exe -m scripts.check_stage2
.venv\Scripts\python.exe -m scripts.check_stage3_ui
.venv\Scripts\python.exe -m scripts.check_stage3
.venv\Scripts\python.exe -m scripts.check_stage4_readiness
.venv\Scripts\python.exe -m scripts.check_stage4_ui
.venv\Scripts\python.exe -m scripts.check_stage4
.venv\Scripts\python.exe -m scripts.check_stage5
pnpm exec supabase db reset --local --version 20260911001200 --no-seed
pnpm exec supabase migration up --local
pnpm exec supabase db reset --local --no-seed
pnpm exec supabase test db --local <each supabase/tests/*.test.sql>
.venv\Scripts\python.exe -m scripts.check_stage2_storage_api
.venv\Scripts\python.exe -m scripts.check_stage3_onboarding_api
.venv\Scripts\python.exe -m scripts.check_stage4_document_api
.venv\Scripts\python.exe -m scripts.check_stage5_retrieval_api
pnpm exec supabase db lint --local --schema public --schema private
git diff --check
~~~

## What went well, what failed, and how it was recovered

- The review correctly grouped the remaining issues under one semantic-validation boundary. Shared helpers removed constructor/validator drift instead of patching individual mutations.
- Initial strict validation exposed two inconsistent synthetic test fixtures: cloned public candidates changed candidate IDs without changing span parent IDs, and a timeout gateway used an old corpus label. The fixtures were corrected; validation was not weakened.
- The first ad-hoc UUID mutation probe used a Python string against a strict UUID field. The canonical JSON/deserialization case was added to the generated matrix so it tests the real boundary.
- No retrieval, security, lifecycle, cache, database or earlier-stage regression had to be waived.

## Remaining limitations and open owners

- Deterministic fixture embeddings and 28 synthetic questions prove control flow, isolation and filters; they do not establish production retrieval quality.
- All 63 weekly profiles remain drafts and hidden. There is no production RAG corpus or public release.
- Clinical and India-localisation reviewers still own health-content and safety-material approval.
- The licence reviewer still owns reuse and embedding-rights approval.
- Product reviewers still own rendered UI and publication decisions.
- Stage 6 engineering and reviewers still need to implement and independently validate the Safety Gate.
- Platform/product still need to benchmark a production embedding provider later; no provider was selected here.

## Stage 6 decision

Every applicable item in the final consolidated checklist passes locally and both required GitHub jobs passed on the exact implementation commit. The verdict is:

`STAGE 5 ACCEPTED FOR CONTROLLED ENGINEERING — STAGE 6 ENGINEERING MAY BEGIN`

That verdict authorizes only a separate Stage 6 engineering task. It does not approve merge, deployment, public release, real medical-data use, a production provider, clinical content, India localisation or licence status.
