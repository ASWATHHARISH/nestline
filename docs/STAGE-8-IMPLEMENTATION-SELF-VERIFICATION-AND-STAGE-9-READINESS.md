# Stage 8 implementation, self-verification and Stage 9 readiness

Date: 2026-09-12
Branch: `feat/stage-8-validation-composition`
Exact accepted Stage 7 starting commit: `9525acb332b90f258bf9a7b08ad19415286fe9fc`
Final Stage 8 commit: intentionally recorded in the final task response after this report is committed
Final working-tree expectation: clean after the normal Stage 8 commit and push; the final response records the verified remote head

## Verdict

`STAGE 8 ACCEPTED FOR CONTROLLED ENGINEERING — STAGE 9 ENGINEERING MAY BEGIN`

This is a controlled-engineering verdict. It is not clinical validation, public-release approval, or proof of live semantic quality. The safety specification remains draft, public health routing remains fail-closed, the public weekly-profile release count remains zero, and all Stage 8 health evidence in this development run is synthetic or previously confirmed personal fixture data.

## Plain-language result

Stage 8 is the display checkpoint between an agent draft and the user. It checks the shape of the draft, the authenticated pregnancy/postpartum state, personal restrictions, evidence eligibility, exact citation spans, prohibited medical language and conflicts between public guidance and personal records. A draft is displayed only when all seven controls pass. Urgent Stage 6 output bypasses ordinary composition unchanged. Safety clarification, uncertain support and every failed validator stop ordinary composition.

The final composer does not write or save anything. It groups validated statements under the exact visible labels `Your confirmed information`, `Your uploaded record says`, `You reported`, `Public guidance says` and `Needs confirmation`. Plans remain editable proposals for later Stage 10 validation/persistence work.

## Entry evidence

- The Stage 7 report verdict was exactly `STAGE 7 ACCEPTED FOR CONTROLLED ENGINEERING — STAGE 8 ENGINEERING MAY BEGIN`.
- Accepted Stage 7 remote branch head was `9525acb332b90f258bf9a7b08ad19415286fe9fc`.
- GitHub run `34657965731` passed both required jobs on that SHA: `validate` job `103454341936` and `supabase-integration` job `103454341786`.
- Critical pre-branch rerun: Stage 5 retrieval, Stage 6 safety and Stage 7 orchestration tests passed 142/142.
- Stage 6 specification status remained `draft`; its public path remained fail-closed.
- `feat/stage-8-validation-composition` was created from the accepted Stage 7 SHA, not from `main`.

## Requirement-to-implementation mapping

| Requirement | Implementation/evidence |
|---|---|
| Strict versioned contracts | `app/schemas/validation.py`; exported `data/schemas/validation.schema.json` |
| Schema validator | Pydantic strict contracts reject extra fields, invalid enums and contradictory request/report/result/composition states |
| State/journey validator | Binds request, workspace, care episode, Stage 7 worker versions, packet state, exact journey, week/range and jurisdiction |
| Personal constraint validator | Applies confirmed allergies/intolerances, conditions, restrictions and clinician instructions before semantic assessment |
| Evidence verifier | Enforces answerability, relevant conflicts/missing information, material-claim links and Stage 5 allowed-claim types |
| Citation validator | Checks packet membership, Stage 7 evidence membership, source/evidence/span identity, exact text/hash, approval/current state, workspace, journey, jurisdiction, condition applicability and semantic support |
| Boundary validator | Deterministically rejects diagnosis, medication changes, inferred clearance, unsafe reassurance, fake review and unauthorized action in claims, summaries and schedule text |
| Consistency validator | Prevents public overrides, enforces visible provenance, validates each plan item/claim/evidence/span/constraint link and combined plan state |
| Deterministic vs semantic separation | `app/services/semantic_support.py`; all identity/permission/applicability/safety checks are deterministic; uncertain/unavailable semantic results block |
| Constrained composition | `Stage8ValidationPipeline._compose`; only seven-PASS reports produce `ComposedAnswer` |
| One bounded correction | Exactly one safe provenance repair or one retrieval retry; no second attempt and no failed-draft composition |
| Urgent/clarification safety boundary | Urgent preserves the exact fixed Stage 6 message; urgent and unresolved clarification both make zero ordinary composition calls |
| Reusable plan validation | `PlanItemValidationLink` carries item/claim/evidence/span/constraint identity plus `user_edited`; no persistence |
| Trace and minimisation | Versions, provider/model, packet/state, evidence/span IDs, findings, latency, token/cost, retry/repair and disposition; zero raw personal text and writes |
| Deterministic CI | `scripts/check_stage8.py` and `scripts/run_stage8_evals.py` added to `data-contracts.yml`; no paid credential required |

## Contracts

Schema version is `8.0.0`. The exported bundle contains:

- `ClaimEvidenceLink`, `Claim`, `EligibleEvidenceSpan`, `ValidationEvidencePacket`;
- `PlanItemValidationLink`, `AnswerDraft`, `ValidationRequest`;
- `SemanticAssessment`, `ValidationFinding`, `ValidatorCheckResult`, `RetryStopTrace`, `ValidationTrace`, `ValidationReport`;
- `ComposedCitation`, `ComposedSection`, `ComposedAnswer`, `Stage8Result`.

Every exact evidence span has a stable `span_id` in addition to its evidence/source IDs and SHA-256. This permits multiple exact spans from one evidence item without collapsing their identity. `ValidationRequest` binds the identical Stage 6 result, Stage 7 result, authenticated workspace/care episode and execution/public mode. `ValidationReport` forbids contradictory disposition, display permission, trace and checker inventories. `Stage8Result` forbids an urgent route with an ordinary answer.

## Seven-validator behavior

1. **Schema:** malformed/unversioned/extra/contradictory structures are rejected before display.
2. **State/journey:** stale draft, packet, worker or plan state; wrong journey stage; wrong week/range; and wrong jurisdiction fail.
3. **Personal constraints:** confirmed allergens, restrictions, conditions and clinician instructions cannot be omitted or overridden.
4. **Evidence:** unsupported/partial packets abstain; relevant conflicts/missing fields clarify; disallowed claim types and uncited material claims fail.
5. **Citation:** source, evidence and exact span/hash must be eligible and current. Plausible but irrelevant, partially supporting, weaker and uncertain citations fail.
6. **Boundary:** deterministic rules reject diagnosis, prescribing/medication change, inferred clearance, unsafe reassurance, fake professional review and unauthorized writes/actions.
7. **Consistency:** public guidance cannot override personal state; origins remain visibly distinct; each schedule item and the combined schedule must preserve claims, exact spans and constraints.

Deterministic constraint or boundary failures prevent unnecessary semantic evaluation. A future semantic evaluator cannot override a deterministic failure.

## Answerability and stop behavior

- Fully supported and seven-validator PASS: compose once.
- Unsupported or partial support: at most one eligible retrieval retry, then abstain.
- Relevant conflict or required missing information: clarify with no composition.
- Uncertain, unavailable or timed-out semantic support: abstain with no composition.
- One unambiguous missing provenance label: at most one mechanical repair.
- Any other failure or failed repair: abstain; a second loop is explicitly prevented.
- Stage 6 urgent: return its exact fixed wording and zero ordinary composition calls.
- Stage 6 unresolved clarification: clarify and zero ordinary composition calls.

## Development evaluation inventory and results

The visible generated set is `evals/stage8_validation_development.jsonl`. It contains 62 synthetic cases; 50 are marked critical. The sealed final holdout was not opened or used.

| Scenario group | Result |
|---|---:|
| Answerability | 4/4 |
| Applicability | 2/2 |
| Boundary | 7/7 |
| Citation | 7/7 |
| Consistency | 1/1 |
| Constraint | 5/5 |
| Evidence | 1/1 |
| Happy path | 1/1 |
| Journey | 5/5 |
| Permission | 2/2 |
| Plan | 10/10 |
| Provenance | 1/1 |
| Repair | 4/4 |
| Retry | 2/2 |
| Safety | 1/1 |
| Schema | 2/2 |
| Semantic | 6/6 |
| Trace | 1/1 |

Overall: 62/62; critical: 50/50. The two schema cases stop at raw contract validation; 60/60 executable pipeline cases record zero persistent writes.

Validator positive/negative observations were: schema 59/1, state/journey 54/5, personal constraints 54/5, evidence 53/6, citation 43/16, boundary 51/9 and consistency 47/12. Maximum retrieval retries observed: 1. Maximum repairs observed: 1. Failed-validation composition calls: 0. Urgent ordinary-composition calls: 0. Local fixture latency over 60 pipeline cases: median 0.21855 ms, maximum 2.1103 ms. These are local deterministic runtimes, not provider or production latency.

Required rejection evidence includes fabricated citations, missing material citations, wrong-week evidence, allergy/restriction violations, medication changes and plausible-but-irrelevant citations. Daily, weekly and user-edited plan paths validate individual items and combined constraints through the same interface.

## One self-review and consolidated rectification

The first focused implementation suite passed 61/61. The first generated evaluation passed 55/62 (43/50 critical): all unsafe cases stopped, but seven cases reported redundant downstream findings or mixed more than one intended control. Expectations were not rewritten to accept defective output. The pipeline now skips semantic assessment after deterministic constraint/boundary failures, exact-text mismatch is the primary span finding, and the fixtures isolate their named control.

The formal line-by-line review then found five substantive gaps:

| Finding | First review | Rectification | Final evidence |
|---|---|---|---|
| Multiple exact spans under one evidence ID collapsed | FAIL | Added stable `span_id` throughout links, packets, traces, citations and plan validation | focused duplicate-evidence test PASS |
| Packet `allowed_claim_types` not enforced | FAIL | Added canonical origin/kind mapping and deterministic rejection | focused disallowed-claim test PASS |
| Stage 7 worker state not rebound | FAIL | Validate every worker state version and cross-stage Safety Gate/mode identity | focused stale-worker test PASS |
| Safety clarification lacked explicit Stage 8 stop | FAIL | Added `safety_clarification_blocked`, clarification disposition and zero composition | focused clarification test PASS |
| Plan item text/exact spans could diverge | FAIL | Bind schedule item to claim text, evidence IDs, span IDs and context; require user-edit markers | focused item/span mutation tests PASS |

The same consolidated pass retained deterministic short-circuiting and exact-span mismatch de-duplication. One fixture then revealed that its unsafe supplement claim and schedule text differed; the fixture was corrected to represent the same user edit in both structures, and the medication boundary still rejected it. Final focused tests passed 71/71 and the regenerated evaluation passed 62/62.

Machine-readable review evidence is in `docs/STAGE-8-SELF-REVIEW-FINDINGS.json`.

## Verification results

| Command/check | Actual result |
|---|---|
| `.venv\Scripts\python.exe -m compileall -q app scripts tests` | PASS |
| `.venv\Scripts\python.exe -m unittest tests.test_validation -q` | 71/71 PASS |
| `.venv\Scripts\python.exe -m unittest discover -s tests -q` | 389/389 PASS on final rerun |
| `python -m scripts.validate_content` | PASS; 63 profiles, 0 published, 31 sources, 55 spans, 56 fragments |
| `python -m scripts.validate_content --require-review-ready` | PASS with honest zero-published state |
| `python -m scripts.run_contract_evals` | 64/64 PASS |
| `python -m scripts.run_journey_evals` | 26/26 PASS |
| Stage 1 and Stage 2 checkers | PASS |
| Stage 3 checker and Streamlit smoke | PASS; 1/1 render, zero network calls |
| Stage 4 readiness/checker and Streamlit smoke | PASS; public feature remains closed |
| Stage 5 checker | PASS; 28/28 behavior and 212-case rectification guarantees retained |
| Stage 6 evaluation/checker | 45/45 PASS; 41/41 critical; draft/public fail-closed retained |
| Stage 7 evaluation/checker | 76/76 PASS; 64/64 critical |
| Stage 8 evaluation/checker | 62/62 PASS; 50/50 critical; checker `valid: true` |
| Exact Stage 4→Stage 5 migration replay | PASS; existing `20260911001300` applied to the Stage 4 fixture and upgrade assertions cleaned it up |
| Clean migration replay | PASS through existing `20260911001300`; Stage 8 adds no migration |
| pgTAP on upgraded history | 6/6 files, 254/254 assertions PASS |
| pgTAP on clean history | 6/6 files, 254/254 assertions PASS |
| Authenticated APIs on upgraded history | Stage 2 13/13; Stage 3 17/17; Stage 4 15/15; Stage 5 25/25; total 70/70 |
| Authenticated APIs on clean history | Stage 2 13/13; Stage 3 17/17; Stage 4 15/15; Stage 5 25/25; total 70/70 |
| Database lint on upgraded and clean histories | 0 findings on both |
| `git diff --check` | PASS; line-ending conversion warnings only |

The local service credential was used only by the established fictional API setup/cleanup scripts. Stage 8 imports no database client, has no service-role path and performs no write.

## Changed files

- `.github/workflows/data-contracts.yml`
- `app/schemas/validation.py`
- `app/services/semantic_support.py`
- `app/services/validation.py`
- `data/schemas/validation.schema.json`
- `docs/STAGE-8-CHECK-RESULTS.json`
- `docs/STAGE-8-COVERAGE-MANIFEST.json`
- `docs/STAGE-8-EVAL-RESULTS.json`
- `docs/STAGE-8-SELF-REVIEW-FINDINGS.json`
- `docs/STAGE-8-IMPLEMENTATION-SELF-VERIFICATION-AND-STAGE-9-READINESS.md`
- `evals/README.md`
- `evals/stage8_validation_development.jsonl`
- `scripts/build_stage8_evals.py`
- `scripts/check_stage8.py`
- `scripts/export_validation_schema.py`
- `scripts/run_stage8_evals.py`
- `scripts/stage8_fixture_support.py`
- `tests/test_validation.py`

## Issue register and limitations

| Severity | Evidence/limitation | User or safety impact | Disposition | Blocks Stage 9 engineering? |
|---|---|---|---|---|
| High external | Safety rule specification is still draft and not clinically/India-localisation approved | Public health routing must remain closed | retained fail-closed; owners: clinical, India-localisation and product reviewers | No, controlled engineering only |
| High external | Zero public weekly profiles are released | Production public guidance cannot use controlled fixtures | no status was changed; owner: governed content/review process | No, controlled engineering only |
| Medium | Semantic assessment used a conservative lexical fixture and scripted outcomes | Does not prove natural-language entailment quality | live benchmark unrun and explicitly unclaimed; owner: future approved provider evaluation | No, because uncertain/unavailable semantics fail closed |
| Medium | Stage 8 is a typed library boundary and has no Stage 9 display UI | Users cannot yet interact with composed answers | intentional Stage 9 scope | No |
| Low | One unsafe draft can produce the same finding code at claim and schedule/summary locations | Review traces may contain repeated codes with different locations | retained for location-level evidence | No |
| Informational | No Stage 8 database migration or remote deployment | No durable validation result exists | intended; Stage 10 owns persistence | No |

No live semantic benchmark, clinical benchmark, public content release, reviewer approval or provider superiority is claimed. The visible synthetic cases are software-contract evidence only.

## Configuration, migration and provider impact

- Database migrations: none.
- RLS, grants, RPCs and PostgREST behavior: unchanged.
- Environment variables or secrets: none added.
- Paid provider calls/credits: none used.
- Deterministic CI requires only the existing Python dependencies.
- Remote migrations/deployment/publication: none.

## Scope confirmation

Stage 9 UI and Stage 10 durable saving/human-review workflows were not implemented. No PR was created, no branch was merged, no remote migration was applied, no health content was published and no reviewer was contacted.

## Final controlled-engineering gate

All required Stage 8 deterministic critical cases, semantic fail-closed cases, plan validations, regressions and local database compatibility checks pass with exact denominators. External content, clinical and live semantic gates remain visible and closed.

`STAGE 8 ACCEPTED FOR CONTROLLED ENGINEERING — STAGE 9 ENGINEERING MAY BEGIN`
