# Stage 6 Implementation, Self-Verification, and Stage 7 Readiness

## Verdict

`STAGE 6 ACCEPTED FOR CONTROLLED ENGINEERING — STAGE 7 ENGINEERING MAY BEGIN`

This is a controlled-engineering verdict only. The safety specification remains
`draft`; qualified clinical and India-localisation reviews have not been recorded.
Public/live health routing therefore fails closed, and the draft rules run only
through the visibly labelled evaluation-only path. Nothing in this report claims
clinical validation, medical clearance, population sensitivity or public-release
readiness.

## Plain-language explanation

Stage 6 is a small rule engine that reads text before any ordinary model could run.
If a configured urgent phrase applies to the current user, it immediately returns
the fixed India emergency wording and prevents ordinary generation. If the text is
symptom-like, unclear, negated, historical, hypothetical, quoted or about another
person, it asks the minimum safety clarification and still prevents generation. A
clearly non-symptom product request, such as opening the dashboard or showing a
saved plan, may continue, but the result explicitly does not say the user is
medically safe.

The engine does not call OpenAI, Grok, Fireworks, LangChain or another provider.
Instructions inside chat or extracted documents are data and cannot change the
rules. The trace stores identifiers, versions, timings, a one-way input hash and
character count; it does not store the raw personal text.

## Entry gate and exact starting state

- Repository starting branch: `feat/stage-1-governed-ingestion`.
- Accepted Stage 5 commit and Stage 6 branch point:
  `7977b80032184c221a6e475a68b31839e081b01a`.
- Starting working tree: clean.
- Accepted Stage 5 verdict:
  `STAGE 5 ACCEPTED FOR CONTROLLED ENGINEERING — STAGE 6 ENGINEERING MAY BEGIN`.
- Exact accepted-commit GitHub workflow: `34648184162`.
- Accepted-commit jobs: `validate` passed (`103423888655`) and
  `supabase-integration` passed (`103423888433`).
- Stage 6 branch: `feat/stage-6-safety-gate`, created from that exact commit.
- The older Stage 5 checker still describes the pre-acceptance independent-review
  gate. The later consolidated acceptance evidence is the authority for this
  entry decision; the older field was not rewritten as historical evidence.

## Scope and changed files

### Runtime and typed contracts

- `app/schemas/safety.py`: strict version `6.0.0` input, match,
  clarification, fixed-message, trace, result and generation-guard contracts with
  cross-field invariants and `extra=forbid` inherited from the common contract.
- `app/services/safety_gate.py`: one deterministic gate, normalization,
  context handling, urgent precedence, explicit draft/missing/malformed/version
  failures, five channel adapters and the pre-generation guard.
- `app/schemas/foundation.py`: safety regexes now compile during schema
  validation, rule IDs must be unique, and India help-route provenance is typed.
- `app/schemas/onboarding.py` and `app/services/onboarding.py`: onboarding uses
  the canonical Stage 6 result. One explicit persistence boundary maps
  `urgent / needs_clarification / non_urgent` to the legacy database values
  `urgent / clarify / no_match`.

### Generated evidence, evaluations and CI

- `data/schemas/safety.schema.json`: generated Stage 6 JSON Schema bundle.
- `data/schemas/onboarding.schema.json`: regenerated after the canonical route and
  trace ID were added.
- `evals/stage6_safety_development.jsonl`: visible 45-case development set.
- `evals/README.md`: Stage 6 dataset scope and limitations.
- `scripts/build_stage6_safety_evals.py`: canonical development-set builder.
- `scripts/export_safety_schema.py`: canonical schema exporter.
- `scripts/run_stage6_safety_evals.py`: deterministic evaluation and metrics.
- `scripts/check_stage6.py`: repository consistency and Stage 6 exit gate.
- `docs/STAGE-6-SAFETY-EVAL-RESULTS.json`: generated evaluation result.
- `docs/STAGE-6-CHECK-RESULTS.json`: generated checker result.
- `.github/workflows/data-contracts.yml`: adds the evaluation and Stage 6 checker
  to `validate`; no secret or paid provider is required.
- `tests/test_safety_gate.py`: focused contract, route, context, failure and guard
  tests.
- `tests/test_onboarding.py`: canonical route and legacy storage-boundary
  regression.

No Stage 6 database migration was added. No safety rule content, source status,
human review, licence decision or public content release was invented.

## Contract inventory

| Contract | Purpose |
|---|---|
| `SafetyGateInput` | Strict channel, trusted origin pairing, request ID, India jurisdiction and optional required spec version |
| `SafetyRuleMatch` | Rule ID, configured route, hashed match, span, mention context and user attribution |
| `SafetyClarificationState` | Required minimum question and reason, or a provably empty non-clarification state |
| `FixedSafetyMessage` | Route-bound ID, message/spec version, India jurisdiction, checksum and visible help-route IDs |
| `SafetyTrace` | Request/trace IDs, route, channel, rules, versions, latency, zero gate-generation calls and data-minimised input metadata |
| `SafetyGateResult` | Canonical result with cross-field consistency and explicit configuration failure |
| `SafetyGenerationGuardResult` | Proof that urgent/clarification blocks and permitted product flow calls at most one supplied continuation |

Contradictory route/permission, trace/result, message/result, request/trace,
configuration/public eligibility and urgent-attribution combinations are rejected
by schema validation.

## Five entry-channel wiring

| Entry channel | Adapter | Boundary status |
|---|---|---|
| Onboarding symptom text | `evaluate_onboarding_symptom` | Integrated into existing onboarding preparation |
| Every future chat message | `evaluate_chat_message` | Typed pre-orchestrator boundary; Stage 7/9 not implemented |
| Symptom check-in | `evaluate_symptom_check_in` | Typed boundary; check-in UI not implemented |
| Extracted document fact | `evaluate_extracted_document_fact` | Always marked `untrusted_document`; document instructions cannot change policy |
| Plan-generation input | `evaluate_plan_generation_input` | Typed pre-generation boundary; plan generation not implemented |

All adapters return the same `SafetyGateResult`. Only onboarding has an existing
runtime surface in the current repository; the other adapters are tested interfaces
for later stages, without implementing those later stages.

## Architecture and requirement mapping

| Requirement | Result | Evidence |
|---|---:|---|
| Deterministic gate, not an agent | PASS | `SafetyGate`; source-dependency checker rejects model/provider imports |
| Runs before ordinary generation | PASS | `continue_after_safety_gate` and spy tests |
| Urgent can never be downgraded | PASS | direct urgent is evaluated first; prompt-injection and mixed-rule tests |
| Urgent fixed output never waits for review | PASS | synchronous fixed-message construction; reviewer-unavailable development case |
| No-match is not proof of safety | PASS | unknown symptom clarifies; `no_medical_safety_claim=true` |
| Draft specification rejected in public runtime | PASS | `draft_specification` fail-closed result; public eligibility false |
| Explicit evaluation-only route | PASS | `execution_mode=evaluation_only`; every development result is non-public |
| Canonical three-route vocabulary | PASS | canonical schema plus one documented DB compatibility map |
| Exact permission for `non_urgent` | PASS | limited to clearly non-symptom product/record-management requests without current-experience language |
| Uncertain language | PASS | current uncertain urgent phrases remain urgent |
| Negated language | PASS | scoped negation clarifies; unrelated “not” cannot downgrade a current urgent phrase |
| Historical/hypothetical/quoted/third-person | PASS | preserved as non-attributed clarification contexts |
| Unicode/case/space/spelling normalization | PASS | NFKC, apostrophe/case/whitespace and two explicit English spelling variants |
| Prompt injection cannot alter policy | PASS | text is matched only as data; urgent injection cases stay urgent |
| Urgent-over-clarification precedence | PASS | multiple-rule development and unit cases |
| Required IDs/versions/reasons/trace | PASS | strict result and trace contracts |
| Five entry channels | PASS | five typed adapters and five-channel evaluation coverage |
| Extracted text is untrusted | PASS | channel/origin invariant plus document-injection case |
| Generation guard | PASS | urgent and clarification spies remain at zero calls |
| Fixed wording separate from prose | PASS | route-bound message identity/version/checksum from the spec |
| India provenance preserved | PASS | typed existing `112`/`14416` routes; source URLs and verification dates unchanged |
| Missing/malformed/unsupported/draft failures | PASS | five configuration cases all fail closed |
| Data-minimised trace | PASS | hash/count only; fixture secret absent and raw-input flag is false |
| Model-call budget: urgent path zero | PASS | 25/25 urgent cases and guard spies |
| No Stage 7/8/9 work | PASS | no agents, answer validator, answer generation or UI added |

## Development evaluation inventory and results

The visible set has 45 synthetic English cases. It contains all ten configured
urgent categories; urgent text mixed with a plan question; physical and self-harm
examples; ambiguous, incomplete, worsening and unknown wording; scoped negation,
history, hypothesis, quotation, third-person and uncertain-current contexts;
case, punctuation, whitespace, Unicode, missing-apostrophe and explicit spelling
variations; prompt-injection/downgrade attempts; ordinary product requests; all five
entry channels; simultaneous matches; draft, missing, malformed and unsupported
specification paths; reviewer unavailable; and trace minimisation.

| Metric | Result |
|---|---:|
| All visible development cases | 45/45 |
| Curated critical cases | 41/41 |
| Urgent cases with zero ordinary-generation calls | 25/25 |
| Ambiguous/configuration cases that clarified or stopped | 16/16 |
| Cases with no tested unsafe reassurance | 45/45 |
| Configured urgent categories covered | 10/10 |
| Entry channels covered | 5/5 |
| Route distribution | 25 urgent, 16 needs clarification, 4 non-urgent product flow |
| Recorded evaluation latency | 45 samples; latest generated report contains median and maximum |

The sealed final holdout was not read or generated. These denominators measure only
the visible deterministic development set.

## First self-review and one rectification pass

| Finding from first implementation/review | First status | Rectification and final evidence |
|---|---:|---|
| “List symptoms in my record” was classified as a symptom report | FAIL | Product/record intent now runs after urgent/context checks but before broad clarify-only terms; positive unit and eval case passes |
| Initial expected-rule lists omitted simultaneous broad clarification matches | FAIL | Canonical visible truth now lists the complete deterministic match inventory; regenerated, not hand-edited report |
| Onboarding schema was stale after route/trace changes | FAIL | Ran `scripts.export_onboarding_schema`; Stage 3 checker is green |
| Broad `not` within 45 characters could de-escalate an unrelated current urgent phrase | FAIL | Negation must now syntactically scope `have/feel/experience`; both contraction and non-contraction regressions stay urgent |
| Apostrophes in surrounding contractions could resemble quote delimiters | FAIL | Only explicit double-quoted spans and quote markers are treated as quotation; contraction regression stays urgent |
| Fixed text could be mutated without an integrity failure | FAIL | Added text SHA-256 plus route/message/trace identity invariants and mutation test |
| Invalid regex, duplicate rule ID or invalid execution mode was not rejected early enough | FAIL | Typed spec validation and execution-mode guard added; all three negative tests pass |
| Draft spec might be published or assigned fake reviewers | PASS | File remains draft; no reviewer or approval record changed |
| A model/provider could enter the urgent path | PASS | No provider dependency; checker enforces absence |
| Raw personal text might be logged | PASS | Trace records hash and length only; explicit minimisation test passes |

One consolidated rectification pass addressed every FAIL above. The full verification
below was then run once after rectification.

## Exact verification commands and actual results

### Python and generated artifacts

```text
.venv/Scripts/python.exe -m unittest tests.test_safety_gate tests.test_foundation tests.test_onboarding -v
.venv/Scripts/python.exe -m unittest discover -s tests -v
.venv/Scripts/python.exe -m scripts.export_onboarding_schema
.venv/Scripts/python.exe -m scripts.build_stage6_safety_evals
.venv/Scripts/python.exe -m scripts.export_safety_schema
.venv/Scripts/python.exe -m scripts.run_stage6_safety_evals --write-report
.venv/Scripts/python.exe -m scripts.check_stage6 --write-report
.venv/Scripts/python.exe -m compileall -q app scripts tests
```

- Focused safety/foundation/onboarding suite: 54/54 passed.
- Full Python suite after rectification: 255/255 passed.
- Schema/devset/evaluation/check reports regenerated from canonical scripts.
- Python compilation: passed.

### Stage 1–6 and UI regressions

```text
.venv/Scripts/python.exe -m scripts.validate_content
.venv/Scripts/python.exe -m scripts.validate_content --require-review-ready
.venv/Scripts/python.exe -m scripts.run_contract_evals
.venv/Scripts/python.exe -m scripts.run_journey_evals
.venv/Scripts/python.exe -m scripts.check_stage1
.venv/Scripts/python.exe -m scripts.check_stage2
.venv/Scripts/python.exe -m scripts.check_stage3_ui
.venv/Scripts/python.exe -m scripts.check_stage3
.venv/Scripts/python.exe -m scripts.check_stage4_readiness
.venv/Scripts/python.exe -m scripts.check_stage4_ui
.venv/Scripts/python.exe -m scripts.check_stage4
.venv/Scripts/python.exe -m scripts.check_stage5
.venv/Scripts/python.exe -m scripts.run_stage6_safety_evals
.venv/Scripts/python.exe -m scripts.check_stage6
```

- Content authoring and review-ready validation: 63 profiles, 0 published,
  31 sources, 55 evidence spans and 56 fragments; zero errors in both modes.
- Phase 1 visible contract evaluations: 64/64.
- Journey evaluations: 26/26.
- Stage 1: green; it independently reran 255 tests.
- Stage 2: green.
- Stage 3 UI smoke: 1/1 rendered, zero network calls; Stage 3 checker green.
- Stage 4 readiness, UI and full checker: green; UI used only registered fixtures,
  public feature remained closed and made zero network calls.
- Stage 5 checker and 212-case rectification matrix: green.
- Stage 6 evaluation: 45/45; Stage 6 checker: green.

### Local database and authenticated API regression

```text
pnpm exec supabase start
.venv/Scripts/python.exe -m scripts.check_stage2_storage_api
.venv/Scripts/python.exe -m scripts.check_stage3_onboarding_api
.venv/Scripts/python.exe -m scripts.check_stage4_document_api
.venv/Scripts/python.exe -m scripts.check_stage5_retrieval_api
pnpm exec supabase test db --local <each supabase/tests/*.test.sql>
pnpm exec supabase db lint --local
```

- Authenticated API checks: Stage 2 13/13, Stage 3 17/17, Stage 4 15/15,
  Stage 5 25/25; total 70/70. Temporary fixtures were removed.
- pgTAP: 122 + 12 + 26 + 11 + 35 + 48 = 254/254 assertions.
- Database lint: zero findings.
- Stage 6 adds no migration and does not change an RPC, RLS policy, grant or table.
  The onboarding API remained compatible through the one legacy route map.

### Repository integrity

```text
git diff --check
```

Passed with no whitespace errors. Git printed only line-ending conversion notices.

## Safety specification and review status

- `data/safety/rule_spec.yaml` remains version `1.0.0`, status `draft`, jurisdiction
  `IN`, language `en`.
- No clinical, India-localisation, licence or product approval was added.
- Existing India emergency (`112`) and Tele-MANAS support (`14416`) provenance,
  source URLs, verification dates and limitations are retained.
- Public runtime returns a typed fail-closed clarification for the draft spec.
- Evaluation mode is explicitly labelled `evaluation_only=true` and
  `public_routing_eligible=false`.

## Migration, configuration and provider impact

- Database migrations: none.
- Remote migrations/deployment: none.
- Environment variables or secrets: none added.
- Paid provider calls/credits: none.
- Model selection: none.
- CI: deterministic Stage 6 evaluation/checker added to `validate`.

## Remaining limitations and owners

| Limitation or gate | Owner/action |
|---|---|
| Rules and fixed wording are draft and not clinically validated | Qualified clinical reviewer must review exact version/checksum |
| India routing/localisation is not approved for public use | Qualified India-localisation reviewer must approve exact material |
| Visible 45-case English set is small | Stage 6 independent review should add adversarial cases without using the sealed holdout |
| English normalization covers only explicitly tested variants | Product/clinical review must set supported-language and robustness scope |
| Existing fixed copy says “Compass,” an inherited draft product-name issue | Product/content reviewer must decide wording before publication; engineering did not silently edit safety copy |
| Live/public health routing is blocked | Keep fail-closed until published spec and required approvals exist |
| Stage 7 orchestrator does not exist | Stage 7 may consume the typed guard only after this controlled-engineering handoff is reviewed |

## Explicit non-scope confirmation

Stage 7 agents/orchestration, Stage 8 answer generation/validation, Stage 9 UI,
production embeddings, public deployment and production document upload were not
implemented. No PR was created, no branch was merged, no migration was deployed,
no safety specification was published, no reviewer was contacted and no paid
provider credit was used.

## Git completion record

This handoff is committed with the implementation on
`feat/stage-6-safety-gate`. The exact final remote commit cannot be embedded inside
the commit that creates it without fabricating a self-reference. The clean
post-commit working-tree status, exact remote head, and GitHub `validate` and
`supabase-integration` run/job URLs are recorded in the final task response after
the push and checks complete.
