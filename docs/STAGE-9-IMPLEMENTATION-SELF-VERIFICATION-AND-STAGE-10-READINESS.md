# Stage 9 implementation, self-verification and Stage 10 readiness

Date: 2026-09-12
Branch: `feat/stage-9-streamlit-product-experience`
Exact accepted Stage 8 starting commit: `2444f1c15b9b8a37b38a76b0257b76d2180f4b17`
Accepted Stage 7 ancestor: `9525acb332b90f258bf9a7b08ad19415286fe9fc`
Final Stage 9 commit: intentionally recorded in the final task response after this report is committed
Final working-tree expectation: clean after the normal Stage 9 commit and push; the final response records the verified remote head

## Verdict

`STAGE 9 ACCEPTED FOR CONTROLLED ENGINEERING — STAGE 10 ENGINEERING MAY BEGIN`

This verdict permits controlled Stage 10 engineering only. It is not clinical validation, public-release approval, production readiness, external usability research or WCAG conformance. The safety specification remains draft, the public weekly-profile release count remains zero, live provider and LangSmith UI benchmarks were not run, and the Stage 9 experience uses clearly labeled fictional fixtures where live accepted services are unavailable.

## Plain-language result

Stage 9 turns the accepted Stage 3–8 service contracts into one locally runnable Streamlit product experience. A user can see a calm weekly overview, ask Compass a supported question, inspect a fictional record, review a proposed day or week plan, open an exact evidence span, inspect a clearly simulated review state, and view generated evaluation evidence. Urgent symptom text goes through the deterministic Stage 6 gate first and produces the fixed safety route before any ordinary agent or answer composition call.

Personal Mode begins empty and does not inherit Demo Mode state. Demo Mode is visibly fictional, resets deterministically and uses no real medical data. Confirmation, saving, reviewer submission, automation and deployment remain disabled because they belong to Stage 10 or later authorized work.

## Entry evidence

- The accepted Stage 8 report verdict was exactly `STAGE 8 ACCEPTED FOR CONTROLLED ENGINEERING — STAGE 9 ENGINEERING MAY BEGIN`.
- The accepted Stage 8 remote head was `2444f1c15b9b8a37b38a76b0257b76d2180f4b17`.
- Stage 8 GitHub run `34663428145` passed `validate` job `103470459969` and `supabase-integration` job `103470460057` on that exact SHA.
- `git merge-base --is-ancestor 9525acb332b90f258bf9a7b08ad19415286fe9fc 2444f1c15b9b8a37b38a76b0257b76d2180f4b17` passed, proving Stage 7 ancestry.
- The pre-implementation Stage 3–8 critical gate rerun passed 257/257 checks.
- Production safety remained fail-closed because `data/safety/rule_spec.yaml` remained `draft`.
- This branch was created from the accepted Stage 8 remote SHA, not from `main`.

## Requirement-to-implementation mapping

| Requirement | Implementation and evidence |
|---|---|
| Canonical entry and separated UI | `streamlit_app.py`; `app/pages_and_components/stage9.py`; services and contracts remain outside callbacks |
| Strict UI contracts | `app/schemas/product_experience.py`; exported `data/schemas/product_experience.schema.json` |
| Personal/Demo separation | `build_personal_empty_home`, deterministic fixture workspace, isolated `stage9_demo_*` reset keys, mutation tests |
| Weekly Home without agent fan-out | `build_demo_weekly_home`; prevalidated joins; generated metric `home_agent_fanout=0` |
| Compass with accepted Stage 6–8 interfaces | `run_compass`; Stage 7 orchestrator first applies Stage 6 safety, then Stage 8 validation/composition |
| Urgent fixed route | Safety route rendered separately; 9/9 repeated urgent stories and focused tests record zero routine generation calls |
| Records and confirmation intent | Seven fictional document states, exact page/span/confidence/provenance, disabled confirmation write |
| Plan display | Four accepted plan variants, day/week rendering, constraints/evidence, session inspection, disabled durable save |
| Evidence drawer | Exact source/evidence/span and support display; public/private scope enforced by strict schema |
| Simulated review | Seven truthful simulated states, minimum proposed context, disabled submission, no urgent delay |
| Evaluator view | Reads generated Stage 5–8 reports and exposes authentic Stage 8 first-pass 55/62 failure rather than hard-coded success |
| Shared view states | Eight typed states: loading, empty, success, validation error, recoverable error, safety blocked, stale/conflict and unavailable/disabled |
| Accessibility and responsive checks | Focus CSS, semantic labels, alt text, non-color-only status, keyboard-only evidence and 11 phone/desktop screenshots |
| Safe rendering and privacy | Streamlit text primitives for data; exact evidence scope invariant; fictional/redacted artifacts; secret and real-data scan |
| Local-only delivery | `docs/STAGE-9-LOCAL-RUNBOOK.md`; no hosting project, domain, cloud secret, deployment or remote environment change |
| Deterministic CI | Stage 9 evaluation, UI and completion checkers added to `.github/workflows/data-contracts.yml`; no paid credential required |

## Product surface inventory and Stage 3–8 integration

| Page | User-visible behavior | Accepted service boundary |
|---|---|---|
| Weekly Home | Journey header, focus areas, constraints, symptoms, appointment, plan and record/review state | Stage 3 journey state and prevalidated Stage 4–8 fixture joins; zero page-load agents |
| Compass | Supported record, medication, symptom, nutrition, movement, well-being, follow-up and plan interactions | Stage 6 Safety Gate → Stage 7 orchestrator/workers → Stage 8 validation/composition |
| Records | Fictional extraction status, exact page/span, confidence, conflicts and recovery | Stage 4 document contracts; proposal intent only |
| Plan | Nutrition, movement, well-being and holistic day/week drafts | Stage 7 Plan Composer/Schedule Builder → Stage 8 plan validation; no save |
| Evidence | Exact supporting span and applicability/status | Stage 5 candidate and Stage 8 citation identities |
| Simulated review | Offered through timed-out status vocabulary with truthful simulation label | Display-only fixture; no reviewer or persistence claim |
| Evaluator view | Generated counts, gate state, latency/call evidence and failed trace | Repository-owned Stage 5–9 JSON reports |

The persistent Compass/emergency route remains available through navigation. The product shell shows the educational and organizational prototype boundary and tells demo users not to upload real information.

## Typed contracts and view-state coverage

Schema version is `9.0.0`. The exported bundle includes `RuntimeConfig`, `JourneyHeader`, `HomeSection`, `WeeklyHomeView`, `EvidenceDrawerItem`, `ChatDisplayResult`, `RecordFieldView`, `DocumentView`, `SimulatedReviewView` and `EvaluatorMetric`, plus all relevant enums. Extra fields and contradictory combinations are rejected.

`EvidenceDrawerItem` rejects personal evidence without a workspace scope and rejects public evidence carrying a private workspace scope. Urgent `ChatDisplayResult` objects cannot carry ordinary composition, and ordinary validated answers cannot masquerade as safety output. Coverage is machine-readable in `docs/STAGE-9-COVERAGE-MANIFEST.json`.

## Weekly Home

Weekly Home renders journey context first, then what may be changing, confirmed information, nutrition/movement/well-being/preparation focus, `consider`/`avoid`/`ask first`, symptoms/emergency access, appointment/follow-up, plan state, extraction/conflict/review status and quick actions. It uses an original abstract 24-dot SVG with meaningful alternative text; it does not invent a fetal measurement or expose the hidden comparison catalogue. Exact and approximate journey headers have separate tests, and wrong-week fixture content is suppressed before display.

The page is assembled by deterministic joins from already validated structures. The generated evaluation and UI checker both observed `home_agent_fanout=0`.

## Compass and citations

Compass preserves messages in isolated Streamlit session state, disables duplicate sends while processing and shows a non-reassuring safety/evidence status. A request uses a stable fictional authenticated snapshot. The real Stage 7 orchestrator runs the accepted Stage 6 safety boundary; eligible drafts then use the real Stage 8 validation pipeline. Validated output renders the five accepted provenance labels, applied constraints, uncertainty, citations and proposed actions.

Urgent output is rendered in a separate action-first block using the fixed Stage 6 message and never exposes a partial draft. Symptom ambiguity clarifies. Unsupported intent and evidence abstention are visibly distinct from success. Selecting `Open supporting evidence` was exercised by the Stage 9 UI checker and reaches the correct evidence ID/span. Medication output remains `recorded/documented as`; medication-change presentation is refused upstream and cannot render as a recommendation.

## Records, plans, evidence and simulated review

Records cover ready, low-confidence, conflict, locked, corrupt, unsupported and wrong-person fictional files. Document content is displayed as text, never interpreted as application instructions or unsafe HTML. Confirmation and correction intents are inspectable but persistence is disabled.

Plans render weekdays/weekends, domain, time window, duration/range, optional/flexible status, rest/recovery, exact citations, personal constraints, conflicts and assumptions. Allergies, restrictions, journey state and clinician-recorded medication/supplement reminders remain visible and read-only. None, draft, saved, stale, conflict, invalid and unavailable states are represented; saved is only a display-state fixture and the UI explicitly says Stage 10 persistence is unavailable. Nutrition-only, movement-only, well-being-only and combined holistic drafts use the accepted Stage 7/8 path.

The evidence drawer distinguishes public fixture evidence from workspace-scoped fictional personal-document evidence, shows current/review state and exact page/span, and has honest unavailable/superseded/insufficient recovery states. Simulated review never claims a doctor reviewed content, exposes the exact simulated state and proposed shared context, and disables submission.

## Evaluator view

The evaluator page is clearly separated from the user product. It reads generated repository artifacts instead of embedding success claims. It reports exact denominators, schema/dataset identifiers, fixture-only boundaries and local latency/call evidence. It includes the authentic Stage 8 first-pass failure: 55/62 before correction, followed by 62/62 after the documented rectification. No live LangSmith or provider run is claimed.

## Development evaluation and walkthrough results

The visible deterministic set is `evals/stage9_product_experience.jsonl`. It contains 38 cases; 25 are critical. The sealed final holdout was not opened or used.

| Scenario group | Result |
|---|---:|
| Compass | 7/7 |
| Evaluator | 2/2 |
| Persistence boundary | 1/1 |
| Plan | 4/4 |
| Privacy | 4/4 |
| Records | 6/6 |
| Simulated review | 7/7 |
| Safety | 2/2 |
| Shared states | 1/1 |
| Weekly Home | 4/4 |
| **Total** | **38/38** |
| **Critical** | **25/25** |

Local deterministic evaluation latency covered 38 samples: mean 1.7341 ms and maximum 8.0463 ms. These figures do not represent network, provider or production latency.

Each architecture story ran three consecutive times after a deterministic Demo Mode reset:

| Story | Runs | Result | Honest Stage 10 boundary |
|---|---:|---:|---|
| Week-aware holistic plan with fictional peanut allergy and movement restriction | 3 | 3/3 | Draft displayed; durable save unavailable |
| Fictional record-to-action continuity | 3 | 3/3 | Evidence and proposed downstream action displayed; confirmation write unavailable |
| Urgent safety bypass and simulated handoff state | 3 | 3/3 | Fixed urgent route, zero ordinary generation; review queue remains simulated/unavailable |

Overall: 9/9 story runs and 9/9 urgent zero-generation assertions. These were internal deterministic walkthroughs, not external user research.

## Visual, accessibility and interaction evidence

`docs/stage9-ui-evidence/visual-inspection.json` records 11 fictional/redacted screenshots and no clipped active-content controls at inspected widths. Desktop width was 1440 px and phone width was 390 px. Evidence includes:

- `desktop-home.png`, `phone-home.png`;
- `desktop-compass-validated.png`, `phone-urgent.png`;
- `desktop-records.png`, `phone-records.png`;
- `desktop-plan.png`, `phone-plan.png`;
- `desktop-evidence.png`;
- `desktop-simulated-review.png`;
- `desktop-evaluator.png`.

`docs/stage9-ui-evidence/keyboard-walkthrough.json` records an internal Chrome DevTools keyboard-only run: Weekly Home to Compass was reached after four focus steps, the destination was activated without pointer input, and visible focus was observed. Controls use descriptive labels, the original visual has alternative text, status is conveyed with text as well as color, and focus styles are visible. Long content and narrow layouts were inspected in the captured phone/desktop states.

This evidence is a bounded implementation check. It does not prove WCAG conformance, clinical usability or independent usability quality. Browser refresh/rerun and deep-link state were exercised locally; relogin cannot be a live authenticated-user study in fixture Demo Mode, so the truthful boundary is deterministic state reset and Personal/Demo isolation.

## One self-review and consolidated rectification

The first focused test set passed 24/24, the deterministic development set passed 38/38 and the three stories passed 9/9. A browser interaction walkthrough then found defects that the render-only checker had not exposed. Expectations were not weakened.

| Finding | Severity | Rectification | Final evidence |
|---|---|---|---|
| Repeated week-plan items reused one span ID, so Stage 8 rejected a real week draft | High | Use a stable day/start-derived span ID per repeated item | Real week plan validates; focused test PASS |
| Citation and quick-action navigation mutated an instantiated sidebar radio and crashed | High | Replace widget-backed navigation mutation with accessible state-driven buttons; activate citation in checker | Evidence drawer opens exact span; UI checker PASS |
| Fresh deep links could lose plan/evidence identifiers after the first rerun | Medium | Preserve recognized identifiers in isolated Demo session state and add evidence recovery | Deep-link and recovery walkthrough PASS |
| Hero HTML interpolation and evidence scope invariant were weaker than required | Medium | Use Streamlit primitives; remove unnecessary HTML; add public/private workspace cross-field rejection | Focused mutation test PASS |

Machine-readable findings are in `docs/STAGE-9-SELF-REVIEW-FINDINGS.json`. All four findings are `PASS` after one consolidated rectification round. No critical browser defect remained in the final review.

## Verification results

| Command/check | Actual result |
|---|---|
| `.venv\Scripts\python.exe -m compileall -q app scripts tests` | PASS |
| `.venv\Scripts\python.exe -m unittest tests.test_product_experience -q` | 25/25 PASS |
| `.venv\Scripts\python.exe -m scripts.run_stage9_evals` | 38/38; critical 25/25; stories 9/9 |
| `.venv\Scripts\python.exe -m scripts.check_stage9_ui` | PASS; 7 pages, validated chat, 7 record recovery states, citation navigation, home fan-out 0, urgent generation 0, Stage 10 writes 0 |
| `.venv\Scripts\python.exe -m unittest discover -s tests -q` | 414/414 PASS |
| `.venv\Scripts\python.exe -m scripts.validate_content` | PASS; 63 profiles, 0 published, 31 sources, 55 evidence spans, 56 fragments |
| `.venv\Scripts\python.exe -m scripts.validate_content --require-review-ready` | PASS with the honest zero-published state |
| `.venv\Scripts\python.exe -m scripts.run_contract_evals` | 64/64 PASS |
| `.venv\Scripts\python.exe -m scripts.run_journey_evals` | 26/26 PASS |
| Stage 1 checker | PASS; 414 Python tests in its regression run |
| Stage 2 checker | PASS |
| Stage 3 checker and Streamlit smoke | PASS; 1/1 render, zero network calls |
| Stage 4 readiness, UI and full checkers | PASS; public feature remains closed |
| Stage 5 checker | PASS; retrieval/security/rectification guarantees retained |
| Stage 6 evaluation and checker | 45/45; critical 41/41; urgent zero-generation 25/25; unsafe-reassurance checks 45/45; PASS |
| Stage 7 evaluation and checker | 76/76; critical 64/64; PASS |
| Stage 8 evaluation and checker | 62/62; critical 50/50; PASS |
| Exact Stage 4→Stage 5 migration verification | PASS; existing Stage 5 migration applied to Stage 4 fixture and upgrade assertions cleaned fixtures |
| Exact Stage 3→current migration verification | PASS through existing Stage 5 migration; no Stage 9 migration |
| Clean migration replay | PASS through all 13 existing migrations; no Stage 9 migration |
| pgTAP on upgraded history | 6/6 files; 254/254 assertions PASS |
| pgTAP on clean history | 6/6 files; 254/254 assertions PASS |
| Authenticated APIs on upgraded history | Stage 2 13/13; Stage 3 17/17; Stage 4 15/15; Stage 5 25/25; total 70/70 |
| Authenticated APIs on clean history | Stage 2 13/13; Stage 3 17/17; Stage 4 15/15; Stage 5 25/25; total 70/70 |
| Database lint on upgraded and clean histories | 0 findings on both |
| Local documented Streamlit start and navigation | PASS using the exact runbook command; 11 screenshot states and keyboard walkthrough captured |
| `git diff --check` | PASS; line-ending conversion warnings only |
| GitHub `validate` and `supabase-integration` | PASS on implementation commit `c57fd135426647f559d9d19e783b0b907ec6309e`; run `34670830170`; jobs `103491743614` and `103491743721` |

The successful GitHub implementation run is [Data contracts run 34670830170](https://github.com/ASWATHHARISH/nestline/actions/runs/34670830170): [validate job 103491743614](https://github.com/ASWATHHARISH/nestline/actions/runs/34670830170/job/103491743614) and [supabase-integration job 103491743721](https://github.com/ASWATHHARISH/nestline/actions/runs/34670830170/job/103491743721). Both ran against `c57fd135426647f559d9d19e783b0b907ec6309e` and concluded `success`.

A PowerShell wrapper used during the first regression pass accidentally launched interactive Python because it reused PowerShell's automatic `$args` variable. Its output was discarded. Every intended command was then rerun explicitly and the table above reports only the corrected runs.

## Local startup, configuration and troubleshooting

The exact clean-start command is:

```powershell
.venv\Scripts\python.exe -m streamlit run streamlit_app.py --server.headless true --server.port 8501 --browser.gatherUsageStats false
```

Demo Mode requires no secret. Personal Mode validates the existing placeholder configuration names documented in `.env.example`; missing configuration produces a clear error instead of a fixture-looking success. Setup, reset and troubleshooting instructions are in `docs/STAGE-9-LOCAL-RUNBOOK.md`.

## Changed files

- `.env.example`
- `.github/workflows/data-contracts.yml`
- `streamlit_app.py`
- `app/pages_and_components/stage9.py`
- `app/schemas/product_experience.py`
- `app/services/product_experience.py`
- `assets/stage9/week-24-journey.svg`
- `data/schemas/product_experience.schema.json`
- `evals/README.md`
- `evals/stage9_product_experience.jsonl`
- `tests/test_product_experience.py`
- `scripts/export_product_experience_schema.py`
- `scripts/run_stage9_evals.py`
- `scripts/check_stage9_ui.py`
- `scripts/check_stage9.py`
- `docs/STAGE-9-LOCAL-RUNBOOK.md`
- `docs/STAGE-9-COVERAGE-MANIFEST.json`
- `docs/STAGE-9-EVAL-RESULTS.json`
- `docs/STAGE-9-DEMO-WALKTHROUGH-RESULTS.json`
- `docs/STAGE-9-SELF-REVIEW-FINDINGS.json`
- `docs/STAGE-9-CHECK-RESULTS.json`
- `docs/STAGE-9-IMPLEMENTATION-SELF-VERIFICATION-AND-STAGE-10-READINESS.md`
- `docs/stage9-ui-evidence/visual-inspection.json`
- `docs/stage9-ui-evidence/keyboard-walkthrough.json`
- the 11 fictional/redacted PNG files listed in the visual evidence section

## Migration, configuration and provider impact

Stage 9 adds no database migration, RPC, RLS policy, storage bucket or remote data. `.env.example` contains placeholder names only. Demo Mode requires no Supabase, OpenAI, Grok, Fireworks or LangSmith credential. Personal Mode reuses the existing accepted local configuration boundary. No paid provider was called, no cloud secret was changed and no remote migration was applied.

## Privacy and safety proof

- Personal Mode is empty in the focused contract test and AppTest startup check.
- Demo Mode uses the synthetic `ws-stage9-demo` fixture, resets only `stage9_demo_*` keys and cannot populate Personal Mode.
- Stage 6 urgent routes produced zero routine agent/generation calls in focused tests and all 9 repeated story runs.
- Weekly Home observed zero specialist-agent calls on load.
- The evaluator reads generated redacted reports and the screenshots contain only fictional fixture data.
- Source scans found no committed `.env`, API keys, service-role values, real person names or real medical documents.
- Public and personal evidence scope mixing is rejected by the typed contract.
- User/document text is rendered as text; it cannot become application code or alter the Safety Gate.

## Honest issue and limitation register

| Severity | Evidence and reproduction | User/safety impact | Disposition | Stage 10 blocker? |
|---|---|---|---|---|
| High, corrected | Week-plan Stage 8 packet rejected repeated span IDs | Week plan could not display | Corrected and regression-tested | No |
| High, corrected | Activating a citation caused `StreamlitWidgetAlreadyInstantiatedError` | Evidence was not inspectable | Corrected; checker now activates the route | No |
| Medium, corrected | Fresh deep link could resolve to empty review state | Reviewer confusion | Corrected and walked through | No |
| Medium, corrected | HTML/data and evidence-scope boundary weaker than required | Future data-rendering/privacy risk | Corrected and mutation-tested | No |
| External high | Safety specification remains draft and public weekly profiles remain unreleased | Live/public health use remains blocked | Preserve fail-closed/public-disabled status; clinical/content owners | No for controlled engineering; yes for public release |
| External medium | No live provider or LangSmith UI benchmark was authorized | No production latency/semantic-quality claim | Deterministic fixture mode is visibly labeled | No |
| External medium | No independent participant was available | Comprehension/usability is not externally validated | Recorded as internal walkthrough only | No |
| Technical low | The bundled browser-control Node REPL could not start under the Windows sandbox ACL | Preferred browser harness unavailable | Used local Chrome DevTools and committed redacted evidence; no test hidden | No |
| Scope boundary | Durable save, fact confirmation, review submission, automation and deployment unavailable | User cannot finish Stage 10 persistence tasks | Controls disabled and labeled | Expected Stage 10 work |
| Scope boundary | No production upload or real authentication/relogin session was exercised in Stage 9 UI | Live lifecycle remains unproven | Existing database/API boundaries tested with fictional principals; UI remains local fixture experience | No for controlled engineering; yes for release |
| Tooling low | Initial PowerShell regression wrapper launched a Python REPL | No product effect; first run unusable | Discarded and reran every command correctly | No |

No required safety, privacy, journey, evidence or Stage 9 task-completion failure remains in the controlled local fixture scope. Public and clinical release remains a separate NO-GO.

## Explicitly unfinished Stage 10 and external work

Stage 9 does not implement or enable durable plan saving, State Committer changes, durable fact confirmation/correction, stale-plan dependency persistence, real review submission/response, asynchronous automation, deployment, domain/hosting configuration or production document upload. It does not create a PR, merge, publish content or contact a reviewer/tester.

## Final recommendation

The implementation commit passed both required GitHub jobs and is ready for controlled Stage 10 engineering. This report-only follow-up commit must also pass those jobs; its exact final SHA and check URLs are recorded in the final task response to avoid a self-referential commit. Public/live use remains blocked by the draft safety specification, unreleased public content, absent clinical/licence/localisation approvals and unrun external usability/provider validation.

`STAGE 9 ACCEPTED FOR CONTROLLED ENGINEERING — STAGE 10 ENGINEERING MAY BEGIN`
