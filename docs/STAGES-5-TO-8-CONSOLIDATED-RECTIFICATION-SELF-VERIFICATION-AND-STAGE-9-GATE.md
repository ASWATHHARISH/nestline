# Nestline Stages 5-8 Consolidated Rectification, Self-Verification and Stage 9 Gate

**Review date:** 2026-09-12  
**Accepted Stage 8 baseline:** 2444f1c15b9b8a37b38a76b0257b76d2180f4b17  
**Correction branch:** fix/stages-5-8-integration-closure  
**Exact implementation evidence commit:** a241b623f414b8e554b256c2a1930a1ce01095dc  
**Final report commit:** recorded in the final task response because a commit cannot contain its own SHA  
**Database migrations changed:** No  
**Paid provider calls:** 0  
**Sealed final holdout accessed:** No  
**Stage 9 implemented:** No

## Verdicts

| Gate | Verdict | Meaning |
|---|---|---|
| Controlled Stage 5-8 engineering | **GO** | The local deterministic contracts and available regressions pass. |
| Stage 9 engineering | **GO FOR CONTROLLED FICTIONAL-DATA ENGINEERING** | Stage 9 may begin from this reviewed correction branch after team review. Stage 9 is not implemented here. |
| Personal Mode with a live provider | **NO-GO** | No provider was selected or benchmarked and no paid call was authorized. |
| Routine generated symptom guidance | **NO-GO** | The required qualified symptom policy remains unavailable. |
| Public or clinical release | **NO-GO** | Safety/content remain draft or unreleased and human clinical, India-localisation, licence, privacy and product review gates remain open. |

The controlled-engineering GO is software-contract evidence only. It is not clinical validation, release approval, or permission to use real patient data.

## Scope completed

This correction implements and verifies the actionable Stage 5-8 independent-review findings:

1. Explicit Personal, Demo and evaluation runtime modes and context origins.
2. Typed onboarding, confirmation, conflict, stale-state, explicit-plan-action and provider-unavailable stops.
3. Authenticated snapshot binding across retrieval, safety, orchestration and validation.
4. Personal Mode rejection of fictional fixture context and fixture providers.
5. Stored-record/product language separated from current symptom language without weakening urgent precedence.
6. Whole-word intent matching, preventing the token "eat" from matching inside "peanut".
7. Provider-neutral injected adapters and a benchmark harness that fail closed and report zero paid calls.
8. Frozen Stage 5 paraphrases and harder Stage 8 citation-support negatives.
9. Visible governance artifacts for qualified symptom-policy review, human product/tone review and controlled holdout IDs.
10. A canonical consolidated checker and CI steps.
11. The two explicitly approved Stage 6 trace-metadata corrections and their new contrast regressions.

No Stage 9 code, public content publication, safety-specification publication, live provider selection, remote migration, PR, merge or deployment was performed.

## Original Stage 6 failures and approved corrections

Before the narrow metadata correction, the Stage 6 development report passed 51 of 53 cases. Both failures were expectation-truth defects; their user-visible routes and generation permissions were already conservative.

| Case | Original expectation | Observed behavior | Corrected contract | Route changed? |
|---|---|---|---|---|
| current_reduced_movement | Expected S-CLARIFY | No configured rule matched; generic symptom fallback returned needs_clarification | Expected rule IDs are empty; reasons are symptom_or_medical_ambiguity and no_match_is_not_safety_clearance; stop is minimum_clarification_required; ordinary generation remains false | No |
| historical_report_plan | Expected no rule IDs | Draft S-CLARIFY matched the word nausea as historical_self | Expected S-CLARIFY; mention context historical_self; attributed_to_user false; stop stored_constraint_product_request; product generation permission remains true | No |

The expected data was not changed merely to hide behavior. The user explicitly approved these two trace corrections after the original mismatches were reproduced and disclosed. The evaluator now checks rule IDs, reason codes, stop reason, mention context, attribution and pending-review status.

## Added safety contrast regressions

| Input | Expected evaluation result | Generation | Review boundary |
|---|---|---|---|
| "I feel reduced movement right now." | needs_clarification; no matched rule; generic fallback reasons | 0 ordinary calls | Open safety-specification gap |
| "My baby is moving less than usual right now." | evaluation-only urgent; draft S-FETAL; current_self | 0 ordinary calls | Final urgent wording/routing remains pending qualified review |
| "My report records prior nausea; create this week's plan." | non_urgent product path; S-CLARIFY historical_self; not attributed as current user symptom | Product continuation allowed | Only because the complete input clearly asks for a plan and reports no current symptom |
| "I feel nauseous right now." | needs_clarification; no matched rule | 0 ordinary calls | Conservative clarification unless a separately reviewed rule later specifies otherwise |
| "I have heavy bleeding; make a meal plan too." | urgent | 0 ordinary calls | Urgent route has precedence over the product request |

The draft file data/safety/rule_spec.yaml was not edited. No clinical rule, reviewer identity or approval was invented.

## Root causes and corrections

### 1. Runtime and identity continuity

The accepted stages had strong individual schemas but no single typed boundary proving that runtime mode, authenticated owner/workspace/care episode, journey version, normalized input hash and safety result stayed aligned across Stages 5-8.

Correction:

- Added strict RuntimeMode and ContextOrigin fields.
- Added a typed cross-stage IntegrationDecision.
- Derived retrieval scope only from the authenticated snapshot.
- Bound Stage 6 results to request ID and normalized input hash.
- Required Stage 8 request, packet and draft scope/state/safety fields to agree.
- Added typed stops for empty Personal Mode, unconfirmed onboarding, conflict, stale state, fixture leakage, implicit plan creation and unavailable provider.

### 2. Stored records versus current symptoms

The Stage 6 product classifier treated some saved-record wording as symptom language. This could block valid record or plan actions even when the input clearly described historical/stored context.

Correction:

- Stored/document/report vocabulary is recognized only with an explicit product action.
- Current-experience language remains on the safety route.
- Urgent rule matching still runs first.
- Historical matches preserve historical_self and attributed_to_user false.

### 3. Safety precedence over provider availability

A final self-review found that Personal Mode provider availability could be checked before returning an already-determined urgent or unresolved clarification result.

Correction:

- Urgent and clarification safety exits now occur before provider checks.
- The regression test test_urgent_safety_precedes_personal_provider_availability proves that an unavailable Personal provider cannot mask or delay the safety route.

### 4. Substring intent routing

The old router used substring membership. The word "peanut" contains "eat", which could create an unintended nutrition intent.

Correction:

- Intent keywords now use deterministic whole-word/whole-phrase matching.
- Stage 7 routing/fan-out passes 25/25 cases.

### 5. Provider and evaluation truth

Provider capability was not represented with a complete fail-closed adapter and benchmark evidence contract.

Correction:

- Added configured provider and semantic-assessor boundaries that require an explicitly injected authorized transport.
- They validate returned provider/model identity and budgets.
- Added a typed benchmark harness and a status artifact reporting no selected provider, no live results, zero calls and zero cost.
- Deterministic tests do not require credentials.

### 6. Semantic support hard cases

The deterministic Stage 8 fixture evaluator needed explicit negatives for similar vocabulary with a contradictory conclusion and claims that shared words without full support.

Correction:

- Added negative cases for opposite polarity, two claims with one supporting span, general nutrition evidence used for allergy-specific safety, and gentle movement evidence used for high-intensity advice.
- Stage 8 semantic cases pass 10/10. This still does not establish production entailment quality.

## Requirement-to-evidence mapping

| Requirement | Implementation/evidence |
|---|---|
| No fixture fallback in Personal Mode | app/schemas/orchestration.py, app/schemas/integration.py, app/services/integration_gate.py, tests/test_stage5_8_integration.py |
| Authenticated scope and state continuity | app/services/integration_gate.py and cross-stage binding tests |
| Current symptom safety first | app/services/safety_gate.py, app/services/orchestration.py, tests/test_safety_gate.py |
| Urgent mixed requests use zero ordinary generation | Stage 6 27/27 and Stage 7 urgent 5/5 |
| Product actions do not misread stored facts as current symptoms | Stored allergy/restriction/report/saved-symptom fixtures and tests |
| Plan generation requires explicit action | Integration schema and runtime-isolation tests |
| Provider absence is visible and fail-closed | model_provider.py, semantic_support.py, provider_benchmark.py and status JSON |
| Frozen Stage 5 paraphrases | evals/stage5_retrieval_paraphrases_v1.jsonl and 12/12 result |
| Hard semantic negatives | tests/test_validation.py and Stage 8 semantic 10/10 |
| Qualified symptom review stays open | docs/STAGE-7-ROUTINE-SYMPTOM-POLICY-REVIEW-PACKET.md |
| Product/tone review stays truthful | docs/STAGE-8-HUMAN-PRODUCT-TONE-REVIEW-RUBRIC.md |
| Sealed holdout integrity | IDs-only manifest; no answers accessed |
| CI deterministic and credential-free | .github/workflows/data-contracts.yml |

## Verification results

### Canonical evaluation and checker results

| Check | Result |
|---|---:|
| Full Python unit suite | 418/418 passed |
| Focused Safety Gate unit tests | 24/24 passed |
| Final affected safety/integration tests | 48/48 passed |
| Stage 5 development retrieval | 28/28 passed |
| Stage 5 frozen paraphrases | 12/12 passed |
| Stage 5 rectification matrix | 212/212 passed |
| Stage 5 Recall@5 | 18/18 |
| Stage 5 citation/evidence precision | 18/18 |
| Stage 5 confirmed-personal-fact precision | 12/12 |
| Stage 5 graph-path correctness | 1/1 |
| Stage 5 wrong-week/wrong-jurisdiction/unapproved/cross-workspace counts | 0/0/0/0 |
| Stage 6 development cases | 55/55 passed |
| Stage 6 critical cases | 51/51 passed |
| Stage 6 urgent zero ordinary-generation calls | 27/27 |
| Stage 6 clarification/failure cases conservatively stopped | 19/19 |
| Stage 6 zero tested unsafe reassurance | 55/55 |
| Stage 7 orchestration | 76/76 passed |
| Stage 7 critical | 64/64 passed |
| Stage 7 urgent zero-agent generation | 5/5 |
| Stage 7 communication contract | 66/66 |
| Stage 7 zero unauthorized writes | 66/66 |
| Stage 8 validation | 69/69 passed |
| Stage 8 critical | 57/57 passed |
| Stage 8 semantic cases | 10/10 passed |
| Stage 8 cross-stage raw-text cases | 3/3 passed |
| Stage 8 zero persistent writes | 67/67 |
| Content contracts | 64/64 passed |
| Journey evaluations | 26/26 passed |
| Content authoring inventory | 63 profiles; 0 published; 31 sources; 55 spans; 56 fragments |
| Content review-ready validation | Passed; 0 profiles published |
| Stage 1 checker | Passed; 418 unit tests observed |
| Stage 2 checker | Passed |
| Stage 3 checker | Passed locally |
| Stage 3 Streamlit smoke | Passed; unauthenticated_onboarding; 0 network calls |
| Stage 4 readiness/checker | Passed locally |
| Stage 4 Streamlit smoke | Passed |
| Python compileall | Passed |
| git diff --check | Passed; line-ending warnings only |
| Repository secret-pattern scan excluding local env files | 0 matches |

### Database/API evidence

During this consolidated rectification, before the final trace-only metadata change:

- Exact Stage 4 to Stage 5 local upgrade passed.
- Clean local migration replay passed.
- pgTAP passed 254/254 in each history, 508/508 combined.
- Authenticated Stage 2-5 API scripts passed 70/70 in each history, 140/140 combined.
- Application-schema database lint returned 0 issues.
- Local Supabase was stopped without backup.
- No migration, database schema or database-bound application code changed after those checks. The approved trace correction changed only Python evaluation metadata, tests and review documentation, so the database matrix was not repeated.

### Commands run

    .venv\Scripts\python.exe -m scripts.export_retrieval_schema
    .venv\Scripts\python.exe -m scripts.export_safety_schema
    .venv\Scripts\python.exe -m scripts.export_orchestration_schema
    .venv\Scripts\python.exe -m scripts.export_validation_schema
    .venv\Scripts\python.exe -m scripts.export_stages5_8_integration_schema
    .venv\Scripts\python.exe -m scripts.build_stage5_fixtures
    .venv\Scripts\python.exe -m scripts.build_stage5_paraphrase_evals
    .venv\Scripts\python.exe -m scripts.build_stage6_safety_evals
    .venv\Scripts\python.exe -m scripts.build_stage7_evals
    .venv\Scripts\python.exe -m scripts.build_stage8_evals
    .venv\Scripts\python.exe -m scripts.run_stage5_retrieval_evals
    .venv\Scripts\python.exe -m scripts.run_stage5_rectification_matrix
    .venv\Scripts\python.exe -m scripts.run_stage5_paraphrase_evals
    .venv\Scripts\python.exe -m scripts.check_stage5 --write-report
    .venv\Scripts\python.exe -m scripts.run_stage6_safety_evals --write-report
    .venv\Scripts\python.exe -m scripts.check_stage6 --write-report
    .venv\Scripts\python.exe -m scripts.run_stage7_evals --write-report
    .venv\Scripts\python.exe -m scripts.check_stage7 --write-report
    .venv\Scripts\python.exe -m scripts.run_stage8_evals --write-report
    .venv\Scripts\python.exe -m scripts.check_stage8 --write-report
    .venv\Scripts\python.exe -m scripts.check_stages5_8_rectification --write-report
    .venv\Scripts\python.exe -m unittest discover -s tests
    .venv\Scripts\python.exe -m scripts.validate_content
    .venv\Scripts\python.exe -m scripts.validate_content --require-review-ready
    .venv\Scripts\python.exe -m scripts.run_contract_evals
    .venv\Scripts\python.exe -m scripts.run_journey_evals
    .venv\Scripts\python.exe -m scripts.check_stage1 --write-report
    .venv\Scripts\python.exe -m scripts.check_stage2 --write-report
    .venv\Scripts\python.exe -m scripts.check_stage3 --skip-remote --write-report
    .venv\Scripts\python.exe -m scripts.check_stage3_ui
    .venv\Scripts\python.exe -m scripts.check_stage4_readiness --write-report
    .venv\Scripts\python.exe -m scripts.check_stage4 --skip-remote --write-report
    .venv\Scripts\python.exe -m scripts.check_stage4_ui
    .venv\Scripts\python.exe -m compileall -q app scripts tests
    git diff --check

## Self-review and rectification findings

The machine-readable record is docs/STAGES-5-TO-8-RECTIFICATION-SELF-REVIEW-FINDINGS.json.

The self-review found and corrected:

1. The two inaccurate Stage 6 trace expectations.
2. Provider availability being evaluated before an already-determined safety stop.
3. The "eat" inside "peanut" substring-routing defect.
4. Missing typed runtime/origin integration boundaries.
5. Incomplete provider benchmark truth.
6. Missing hard semantic negatives.
7. A final formatting cleanup that temporarily removed three Python delimiters. Compileall caught it before commit; the delimiters were restored, 48/48 affected tests passed, and the full suite then passed 418/418.

The cleanup failure is retained here because the review requires failed checks and recovery to remain visible.

## Known limitations and open gates

1. **Safety specification:** data/safety/rule_spec.yaml remains draft. Public/live routing fails closed.
2. **Reduced movement:** final rule applicability, wording and India-appropriate route require qualified review. No rule was self-approved.
3. **Routine symptom worker:** unavailable until a qualified policy is approved.
4. **Public content:** the repository still has zero published weekly profiles.
5. **Provider quality:** deterministic fixture adapters and small synthetic datasets do not prove live model or retrieval quality.
6. **Live provider benchmark:** not authorized and not run; zero cost was incurred.
7. **Human review:** Stage 8 product/tone review has a rubric but no completed independent human result.
8. **Stage 9:** no Stage 9 implementation or checker exists on the accepted Stage 8 baseline. Therefore this report verifies readiness to begin controlled Stage 9 engineering, not Stage 9 completion.
9. **Release reviews:** clinical, India-localisation, licence, privacy/legal and final product acceptance remain open.
10. **Real data/deployment:** no authorization exists for real patient data, public deployment or clinical use.

## Complete implementation commit file inventory

### Workflow

- .github/workflows/data-contracts.yml

### Schemas and services

- app/schemas/integration.py
- app/schemas/orchestration.py
- app/schemas/provider_benchmark.py
- app/schemas/safety.py
- app/services/integration_gate.py
- app/services/model_provider.py
- app/services/orchestration.py
- app/services/provider_benchmark.py
- app/services/safety_gate.py
- app/services/semantic_support.py

### Generated schemas

- data/schemas/orchestration.schema.json
- data/schemas/safety.schema.json
- data/schemas/stages5_8_integration.schema.json
- data/schemas/validation.schema.json

### Generated and review evidence

- docs/STAGE-1-CHECK-RESULTS.json
- docs/STAGE-3-CHECK-RESULTS.json
- docs/STAGE-4-CHECK-RESULTS.json
- docs/STAGE-5-CHECK-RESULTS.json
- docs/STAGE-5-PARAPHRASE-EVAL-RESULTS.json
- docs/STAGE-5-RECTIFICATION-EVIDENCE-PACKETS.json
- docs/STAGE-5-RETRIEVAL-METRICS.json
- docs/STAGE-6-CHECK-RESULTS.json
- docs/STAGE-6-SAFETY-EVAL-RESULTS.json
- docs/STAGE-7-EVAL-RESULTS.json
- docs/STAGE-7-ROUTINE-SYMPTOM-POLICY-REVIEW-PACKET.md
- docs/STAGE-8-CHECK-RESULTS.json
- docs/STAGE-8-COVERAGE-MANIFEST.json
- docs/STAGE-8-EVAL-RESULTS.json
- docs/STAGE-8-HUMAN-PRODUCT-TONE-REVIEW-RUBRIC.md
- docs/STAGES-5-TO-8-RECTIFICATION-CHECK-RESULTS.json
- docs/STAGES-5-TO-8-RECTIFICATION-SELF-REVIEW-FINDINGS.json
- docs/STAGES-7-8-LIVE-PROVIDER-BENCHMARK-STATUS.json

### Evaluation data

- evals/README.md
- evals/stage5_retrieval_paraphrases_v1.jsonl
- evals/stage6_safety_development.jsonl
- evals/stage8_controlled_holdout_manifest.json
- evals/stage8_validation_development.jsonl

### Canonical scripts

- scripts/build_stage5_paraphrase_evals.py
- scripts/build_stage6_safety_evals.py
- scripts/build_stage8_evals.py
- scripts/check_stages5_8_rectification.py
- scripts/export_stages5_8_integration_schema.py
- scripts/run_stage5_paraphrase_evals.py
- scripts/run_stage6_safety_evals.py
- scripts/run_stage8_evals.py
- scripts/stage8_fixture_support.py

### Tests

- tests/test_safety_gate.py
- tests/test_stage5_8_integration.py
- tests/test_validation.py

This inventory contains 50 files in implementation commit a241b623f414b8e554b256c2a1930a1ce01095dc. This Markdown handoff is added by a separate report-only commit.

## Git and external-action record

- The prior Stage 10 working state remains preserved in stash entry: On stage-10-state-review-lifecycle: preserve-stage10-before-stages5-8-review.
- The implementation was committed to fix/stages-5-8-integration-closure.
- Implementation commit a241b623f414b8e554b256c2a1930a1ce01095dc was pushed only to that correction branch on origin.
- No force push was used.
- No PR was created.
- Nothing was merged into main.
- No migration was deployed.
- No application or health content was published.
- No reviewer or external person was contacted.
- GitHub Data contracts run for the implementation commit completed successfully: https://github.com/ASWATHHARISH/nestline/actions/runs/34686955213
- GitHub validate completed successfully: https://github.com/ASWATHHARISH/nestline/actions/runs/34686955213/job/103535494382
- GitHub supabase-integration completed successfully: https://github.com/ASWATHHARISH/nestline/actions/runs/34686955213/job/103535494456

## Final recommendation

**CONTROLLED ENGINEERING: GO.** The corrected Stage 5-8 contracts and available regression evidence support beginning Stage 9 engineering with fictional/controlled data after review of this branch.

**PUBLIC/CLINICAL RELEASE: NO-GO.** The draft safety specification, reduced-movement policy gap, unreleased weekly content, unrun provider benchmark and outstanding qualified human reviews block public or clinical release.
