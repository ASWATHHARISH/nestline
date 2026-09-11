# Stage 5 self-verification and Stage 6 readiness

**Verification date:** 12 September 2026
**Branch:** `feat/stage-1-governed-ingestion`
**Final consolidated review baseline:** `2a067945986d68f85fba6234b9cb59be90a90eab`
**Authoritative final evidence:** `STAGE-5-FINAL-CONSOLIDATED-CORRECTION-AND-STAGE-6-GATE.md`
**Final recommendation:** `STAGE 5 ACCEPTED FOR CONTROLLED ENGINEERING — STAGE 6 ENGINEERING MAY BEGIN`
**Stage 6 recommendation:** GO for a separate controlled engineering task; no Stage 6 code is included here
**Public/clinical recommendation:** NO-GO

## What was verified

The attached independent review was checked against the code and reproduced on the exact reviewed remote HEAD before correction. The final local state was then checked against the Stage 5 architecture, all Stage 1–4 gates, database RLS/RPC behavior, both-principal authenticated API behavior and frozen Stage 5 development truth.

No Stage 6 code, agent, answer generation, Streamlit UI, production embedding selection or public deployment was added.

The final consolidated correction is verified by 56/56 focused Stage 5 tests, 232/232 total Python tests, a generated 212/212 adversarial matrix, 254/254 pgTAP assertions and 70/70 authenticated API checks. The linked authoritative report records the new semantic invariants, exact breakdown and remote gate.

## Root causes and before/after evidence

| Finding | Before on `3991896` | Corrected local behavior |
|---|---|---|
| Policy cache ordering | public→causal hid the required graph path; causal→public leaked that path into public guidance | cached and fresh results are equivalent in both directions |
| Candidate-limit ordering | public and personal max-1→max-5 reused truncated component candidates | both directions equal fresh retrieval for public and personal results |
| Caller-fabricated policy | a `public_guidance` policy requiring only a personal constraint was accepted | gateway builds policies internally; schema rejects every noncanonical field combination |
| Contradictory packet/result | unsupported evidence with `should_abstain=false` could validate | packet/result cross-field validators reject contradictory support, abstention, scope, policy and trace fields |
| Generic allergy conflict | “What allergies are in my record?” returned confirmed facts and hid an unresolved allergy conflict | the conflict surfaces, support is `clarification_required`, and ordinary generation abstains |
| Generic missing information | category wording and singular/plural variants could miss required fields | six personal categories map deterministically to matching missing-information fields |

The two defects from the first Stage 5 review also remain corrected:

- unsupported week-25 hospital preparation guidance with unrelated personal data abstains with `no_approved_public_content`;
- a relevant prenatal-yoga conflict abstains with `unresolved_conflict` and excludes unrelated personal passages.

Full original-defect packets are in `docs/STAGE-5-RECTIFICATION-EVIDENCE-PACKETS.json`. The second-review before/after matrix is in `docs/STAGE-5-RECTIFICATION-REGRESSION-MATRIX.json`.

## Second-rectification matrices

| Matrix | Result |
|---|---:|
| Cached-versus-fresh equivalence | 10/10 |
| Fabricated/inconsistent policy rejection | 10/10 |
| EvidencePacket/RetrievalResult mutation rejection | 17/17 |
| Generic conflict relevance | 6/6 |
| Generic missing-information relevance | 6/6 |

The cache matrix covers public→causal, causal→public, personal→mixed, mixed→personal, both max-candidate directions for public and personal results, a stale caller state version and server state N→N+1.

## Retrieval evaluation

The frozen development set has 28 deterministic synthetic cases covering all planned domains, both original abstention defects, personal-record lookup, relevant/irrelevant conflicts, missing information, graph on/off behavior, condition applicability, current/future week handling, stale caller version, possible pregnancy, postpartum and record-only medication/symptom behavior.

| Metric | Result |
|---|---:|
| Recall@5 | 18/18 = 1.000 |
| Citation/evidence precision | 18/18 = 1.000 |
| Confirmed-personal-fact precision | 12/12 = 1.000 |
| Expected behavior accuracy | 28/28 = 1.000 |
| Support-state accuracy | 28/28 = 1.000 |
| Journey-relation accuracy | 28/28 = 1.000 |
| Graph-path correctness | 1/1 = 1.000 |
| Wrong-week retrieval | 0 |
| Wrong-jurisdiction retrieval | 0 |
| Unapproved-source retrieval | 0 |
| Cross-workspace leakage | 0 |
| Conflict/proposal personalization violations | 0 |
| Forbidden evidence IDs observed | 0 |

The vector-only baseline found 18/18 expected public IDs but returned 27 public candidates, so precision was 18/27. The adopted hybrid found 18/18 with 18/18 precision and 12/12 confirmed-personal-fact precision. One deterministic ranking trial matched the hybrid and was not adopted because it showed no gain.

Graph-off fails the one relationship-required case and graph-on passes 1/1. An exact-SQL record lookup is unchanged with graph on/off, so no graph benefit is claimed there. Component latency measurements are local development measurements in `docs/STAGE-5-RETRIEVAL-METRICS.json`.

## Application, content and regression verification

| Check | Result |
|---|---:|
| Python compile check | passed |
| Complete Python unit suite | 232/232 passed |
| Focused Stage 5 unit suite | 56/56 passed |
| Content authoring validation | passed: 63 profiles, 0 published, 31 sources, 55 evidence spans, 56 fragments |
| Content review-ready validation | passed with the same inventory |
| Content contract evaluation | 64/64 passed |
| Journey evaluation | 26/26 passed |
| Stage 1 check | passed: 232 tests, 55 candidates/anchors, 72 governed blocks, 54 review decisions |
| Stage 2 check | passed |
| Stage 3 UI smoke | passed; unauthenticated onboarding; 0 network calls |
| Stage 3 check | passed |
| Stage 4 readiness | passed |
| Stage 4 UI smoke | passed; explicit review; 0 preselected items; public feature closed; 0 network calls |
| Stage 4 full check | passed |
| Expanded Stage 5 evaluation | 28/28 behaviors/support/journey classifications passed |
| Second-rectification matrix | 212/212 cases passed across 12 generated groups |
| Stage 5 deterministic check | passed; `ready_for_independent_re_review=true`; `ready_for_stage6_engineering=false` |
| `git diff --check` | passed |

## Database verification

No migration was added or modified during this rectification.

### Exact Stage 4 → Stage 5 upgrade

The local database was reset to migration `20260911001200`, the controlled Stage 4 upgrade fixture was inserted, migration `20260911001300_stage5_hybrid_retrieval.sql` was applied, and `stage5_stage4_upgrade_check.sql` passed. Its cleanup removed every temporary fixture row.

### Clean replay

A clean local reset applied all 15 migrations and recorded the Stage 5 migration. The final public schema contains 29 application tables.

### pgTAP

| File | Result |
|---|---:|
| `stage2_security_and_lifecycle.test.sql` | 122/122 |
| `stage3_exit_hardening.test.sql` | 12/12 |
| `stage3_onboarding.test.sql` | 26/26 |
| `stage4_api_role_hardening.test.sql` | 11/11 |
| `stage4_document_confirmation.test.sql` | 35/35 |
| `stage5_hybrid_retrieval.test.sql` | 48/48 |
| **Total** | **254/254** |

### Authenticated API checks

| Checker | Result |
|---|---:|
| Stage 2 Storage | 13/13 |
| Stage 3 onboarding | 17/17 |
| Stage 4 documents | 15/15 |
| Stage 5 retrieval | 25/25 |
| **Total** | **70/70** |

The Stage 5 API checker uses two authenticated principals and verifies authenticated scope, server-derived state version and policy, cross-workspace denial and expected retrieval behavior.

Application-schema lint was run only over Nestline `public` and `private` schemas and returned 0 findings.

## Failures encountered and recovery

1. The two cache-order defects, candidate-limit truncation, fabricated policy, contradictory packet and hidden generic conflict were reproduced before correction. The implementation fixes the underlying key, construction and validation boundaries rather than special-casing the examples.
2. During the exact migration test, Supabase CLI 2.117 on Windows returned from `db reset` while local schema initialization was still settling. The first fixture attempt inserted its Auth row and then met a table that was not ready. The database was reset again, readiness was verified from PostgreSQL, and the exact upgrade passed cleanly.
3. The first Stage 4 authenticated checker invocation used system Python and stopped at import time because PyMuPDF was absent. It made no API assertion. Rerunning with the project virtual environment passed 15/15; Stage 5 then passed 25/25.
4. A PowerShell loop exited after three individually successful pgTAP files. The remaining three were run explicitly, and all six total 254/254.
5. The first pushed GitHub run passed validate but exposed a UTC/India-midnight defect in the Stage 3 future-date test. The test now derives tomorrow from Asia/Kolkata, matching the database guard. Exact Stage 3 upgrade and clean-install paths both pass the complete database/API/lint sequence locally.

## Exact commands used

~~~powershell
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
.venv\Scripts\python.exe -m scripts.build_stage5_fixtures
.venv\Scripts\python.exe -m scripts.export_retrieval_schema
.venv\Scripts\python.exe -m scripts.run_stage5_retrieval_evals --write-report
.venv\Scripts\python.exe -m scripts.run_stage5_rectification_matrix --write-report
.venv\Scripts\python.exe -m scripts.check_stage5 --write-report
pnpm exec supabase db reset --local --version 20260911001200 --no-seed
pnpm exec supabase migration up --local
pnpm exec supabase db reset --local --no-seed
pnpm exec supabase test db --local supabase/tests/<each .test.sql>
.venv\Scripts\python.exe -m scripts.check_stage2_storage_api
.venv\Scripts\python.exe -m scripts.check_stage3_onboarding_api
.venv\Scripts\python.exe -m scripts.check_stage4_document_api
.venv\Scripts\python.exe -m scripts.check_stage5_retrieval_api
pnpm exec supabase db lint --local --schema public --schema private
git diff --check
~~~

## Remote CI status

GitHub `validate` and `supabase-integration` must pass on the latest pushed branch head before merge. The live GitHub run is the authority for remote status.

## Honest limitations and open gates

- SHA-256 fixture embeddings and 28 synthetic questions test determinism, isolation, filtering and contracts; they do not prove production retrieval or clinical quality.
- All 63 real weekly profiles remain drafts. Controlled fixture evidence is isolated test data.
- Clinical, India-localisation, licence, product/publication and production-provider work remains open.
- Independent review of this exact local rectification remains open.
- Stage 6 Safety Gate behavior is absent.

## Final decision

`READY FOR INDEPENDENT RE-REVIEW` locally.

Stage 6 remains NO-GO until implementation commit `467422a62a3db31740a2d631538a73c2f34cc526` and its documentation follow-up are independently accepted. Nothing was merged or deployed.
