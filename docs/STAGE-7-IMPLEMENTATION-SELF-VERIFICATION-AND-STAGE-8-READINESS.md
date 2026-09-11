# Nestline Stage 7 implementation, self-verification, and Stage 8 readiness

**Report date:** 2026-09-12
**Stage:** 7 only — bounded orchestration, eight planned workers, Plan Composer, and deterministic Schedule Builder
**Branch:** `feat/stage-7-agent-orchestration`
**Exact accepted Stage 6 base:** `f815ab3ffc125ec595ab0ea55fe17a1fe83f3d75`
**Stage 7 implementation commit before this handoff:** `83225ac`
**Final Stage 7 remote head and GitHub check URLs:** intentionally recorded in the final task response after this report is committed and pushed; this report does not fabricate a self-referential SHA.

## Final verdict

`STAGE 7 ACCEPTED FOR CONTROLLED ENGINEERING — STAGE 8 ENGINEERING MAY BEGIN`

This verdict applies only to deterministic, controlled engineering with synthetic fixtures. It is not public-release, clinical-validation, provider-selection, or production-model approval. The Stage 6 safety specification and public health corpus remain draft, so public/live health generation remains fail-closed. Stage 8 must validate worker outputs before they become user-visible.

## Plain-language explanation

Stage 7 now acts like a careful dispatcher. Every request first carries the exact Stage 6 Safety Gate result. Urgent or unresolved safety requests stop before any ordinary worker or model call. A routine request goes to one relevant worker. A day or week plan calls only the requested domain workers and then the Plan Composer. Workers cannot write to the database, cannot use service-role credentials, and cannot call one another.

The Plan Composer uses a deterministic Schedule Builder. It places validated Nutrition, Movement, Well-being, and Follow-up contributions into explicit weekday/weekend availability, avoids fixed appointments, keeps medication or supplement timing as a separate exact read-only record reminder, and returns only an editable proposal. The same ordered input produces the same schedule. Saving, activation, durable staleness, reminders, and human-review persistence remain Stage 10 work.

## Entry-gate evidence

| Entry requirement | Evidence | Result |
|---|---|---|
| Stage 6 handoff exists | `docs/STAGE-6-IMPLEMENTATION-SELF-VERIFICATION-AND-STAGE-7-READINESS.md` | PASS |
| Exact Stage 6 verdict | `STAGE 6 ACCEPTED FOR CONTROLLED ENGINEERING — STAGE 7 ENGINEERING MAY BEGIN` | PASS |
| Accepted Stage 6 remote head | `f815ab3ffc125ec595ab0ea55fe17a1fe83f3d75` | PASS |
| Stage 6 GitHub `validate` | workflow 34652032439, job 103436163217 | PASS |
| Stage 6 GitHub `supabase-integration` | workflow 34652032439, job 103436163070 | PASS |
| Stage 5 retrieval and Stage 6 safety regression | 79/79 focused tests; Stage 5 and Stage 6 checkers valid | PASS |
| Draft safety behavior | `data/safety/rule_spec.yaml` remains `draft`; controlled fixture mode only | PASS |
| Stage 7 branch provenance | Created from the exact accepted Stage 6 SHA, not from `main` | PASS |

Starting worktree at `f815ab3ffc125ec595ab0ea55fe17a1fe83f3d75` was clean. At this report's authoring point, implementation commit `83225ac` contained the Stage 7 code, tests, generated evidence and CI wiring; this handoff plus whitespace cleanup were the only packaging changes. The final clean working-tree status is reported after the report commit in the task response.

## Implemented scope and requirement-to-file mapping

| Requirement | Implementation/evidence |
|---|---|
| Versioned strict Stage 7 contracts | `app/schemas/orchestration.py`, generated `data/schemas/orchestration.schema.json` |
| Eight-worker catalogue, tools, evidence lanes, budgets, prohibitions and context minimisation | `app/services/orchestration_catalogue.py`, `docs/STAGE-7-COVERAGE-MANIFEST.json` |
| Provider-neutral, bounded structured-output interface | `app/services/model_provider.py` |
| Record, Medication Record, Symptom Navigation, Nutrition, Movement, Well-being and Follow-up workers | `app/services/agents.py` |
| Journey Orchestrator and deterministic route plans | `app/services/orchestration.py` |
| Plan Composer boundary | `app/services/orchestration.py` |
| Deterministic day/week Schedule Builder | `app/services/schedule_builder.py` |
| Offline fixtures and 76 visible expected-truth cases | `scripts/stage7_fixture_support.py`, `scripts/build_stage7_evals.py`, `evals/stage7_orchestration_development.jsonl` |
| Evaluator with per-case, per-agent and scenario denominators | `scripts/run_stage7_evals.py`, `docs/STAGE-7-EVAL-RESULTS.json` |
| Deterministic Stage 7 gate | `scripts/check_stage7.py`, `docs/STAGE-7-CHECK-RESULTS.json` |
| Schema/coverage regeneration | `scripts/export_orchestration_schema.py` |
| Executable security, mutation, worker, routing, budget and scheduling tests | `tests/test_orchestration.py` |
| CI | `.github/workflows/data-contracts.yml` |
| Evaluation documentation | `evals/README.md` |
| Final handoff | this file |

## Typed contract inventory

The exported Stage 7 schema bundle contains strict, extra-field-rejecting contracts for:

- `AgentBudget`, `AgentDefinition`, and stable agent/catalogue versions;
- `EvidenceReference`, `WorkerEvidence`, `ContextItem`, `AuthenticatedContextSnapshot`, and `MinimalWorkerContext`;
- `WorkerRequest`, `OrchestrationRequest`, `EvidencePlanItem`, and `RoutePlan`;
- `RecordFinding`, `MedicationTimelineEntry`, `SymptomNavigation`, `PlanContribution`, `FollowupTask`, `ProposedAction`, and `WorkerResult`;
- `AvailabilityWindow`, `FixedAppointment`, `RecordedReminder`, `ScheduleRequest`, `ScheduledItem`, and `ProposedSchedule`;
- `AgentTrace`, `OrchestrationTrace`, and `OrchestrationResult`.

Cross-field validation binds the request ID and normalized input hash to the exact Stage 6 decision, ensures the authenticated owner owns the owner-only workspace/care episode, rejects wrong-journey evidence, restricts context fields per worker, makes medication data record-only, enforces proposal-only/no-write output, and makes generation flags agree with actual provider-call counts.

## Orchestrator and worker coverage

| Component | Trigger and typed output | Allowed tools/evidence | Budget | Main stop/prohibition rules | Measured cases |
|---|---|---|---|---|---:|
| Journey Orchestrator | Safe request → typed route plan/result | deterministic classifier, catalogue, authenticated snapshot | 0 baseline routing calls; ≤5 total worker/composer calls; ≤32 steps; 30 s total deadline | Safety first; one specialist by default; no worker-to-worker calls; stop unsupported, stale/invalid, failed worker or budget | routing/fan-out 25/25 |
| Record Agent | Record/extraction question → findings and proposed actions | personal SQL/documents and exact spans | 1 provider call, ≤6 steps, 1 repair, 8 s | no diagnosis/treatment; show unconfirmed state; stop missing, poor OCR or conflict | 6/6 |
| Medication Record Agent | Medication/supplement record question → chronological record-only timeline | personal SQL/documents | 1 call, ≤6 steps, 1 repair, 8 s | no start/stop/substitute/combine/reschedule/missed-dose advice; reaction re-enters safety; conflicts clarify | 8/8 |
| Symptom Navigation Agent | Non-urgent Stage 6 result → bounded action route | Stage 6 result and approved symptom evidence | 1 answer call after a separately completed clarification cycle, ≤7 steps, 8 s | no diagnosis/reassurance; urgent/clarification bypass; no approved routine policy means abstention | 3/3 worker cases; symptom safety 16/16 |
| Nutrition Agent | Nutrition request/plan → cited option/contribution | public nutrition/weekly/catalogue evidence | 1 call, ≤6 steps, 1 repair, 8 s | hard-exclude allergen/restriction tags before and after generation; no clinical diet; missing/conflicting evidence stops | 14/14 |
| Movement Agent | Movement request/plan → conservative cited contribution | safety result and movement/weekly/catalogue evidence | 1 call, ≤6 steps, 1 repair, 8 s | no inferred clearance; current symptom re-enters safety; conflict/missing sourced intensity stops; explicit stop warning | 13/13 |
| Well-being Agent | Well-being request/check-in → optional support contribution | safety result and approved well-being evidence | 1 call, ≤6 steps, 1 repair, 8 s | crisis handled by Stage 6; no diagnosis; persistent/worsening concern stops for professional follow-up | 8/8 |
| Follow-up Agent | Appointment/question/brief request → grouped provenance-linked tasks | personal SQL/documents | 1 call, ≤6 steps, 1 repair, 8 s | no false monitoring; reminder/tracking remains consented proposal; new symptom re-enters safety; instruction conflicts clarify | 8/8 |
| Plan Composer | Validated contributions → typed worker result plus proposed schedule | deterministic Schedule Builder and constraint checker | 1 composition call, ≤8 steps, 1 repair, 10 s | no direct save; contributor failure, state mismatch, contradiction, missing availability, timeout/provider/schema failure stops | 6/6 |

All workers use one provider-neutral interface. The included deterministic provider echoes a pre-bounded structured fixture and is used only for offline software-contract tests. No OpenAI, Grok, Fireworks, LangChain, or paid-model import exists in the Stage 7 execution path. No provider/model superiority claim is made.

## Shared context and safety controls

- Workspace, owner, care episode and state version come only from `AuthenticatedContextSnapshot`; client text has no scope field.
- Every worker receives a `MinimalWorkerContext` filtered by its catalogue policy.
- Confirmed, user-reported, document-derived-unconfirmed, conflicting and stale facts remain separate.
- The exact Stage 6 normalized-input hash must match the Stage 7 request and every worker request. Post-gate text replacement is rejected.
- An urgent or `needs_clarification` Stage 6 result cannot carry workers, a schedule, or ordinary generation.
- Provider output is schema-validated and then independently checked for confirmed-fact use, constraint preservation, evidence provenance, forbidden reassurance and domain-specific hard boundaries.
- No Stage 7 service imports Supabase/PostgREST/psycopg, and traces enforce `direct_write_count=0` and `service_role_used=false`.
- All state changes and follow-up actions are proposals requiring confirmation.

## Plan Composer and deterministic Schedule Builder

The Schedule Builder supports one-day and one-week horizons. Monday through Sunday are explicit, including weekends. Inputs contain user availability, fixed appointments, evidence-backed duration/cadence, optional preferred days/windows, exact record-only reminders, state version, constraints and uncertainties.

Stable ordering uses contributor order, contribution ID, weekday order, time and a SHA-256-derived schedule item ID. Placement uses 30-minute deterministic increments. Fixed appointments and exact medication/supplement record reminders are placed first. Repeated contributions occur only from explicit fixture evidence and a compatible confirmed user cadence; the schedule records whether cadence came from evidence, user preference, or a single organizational proposal. It carries flexible alternatives and rest/recovery notes supplied by evidence.

A schedule with overlaps, contradictory duplicate IDs, unplaceable items, unresolved uncertainty or stale state is not save-eligible. `mark_stale` only returns an in-memory stale proposal. Durable save, active status, dependency invalidation, reminder dispatch and human-review persistence were not implemented.

Measured schedule and plan results:

- day/week plan variants and scheduling: 18/18;
- deterministic identical-input repeatability: 1/1;
- explicit weekday/weekend coverage: 1/1;
- appointment collision avoidance: 1/1;
- unplaceable conflict detection: 1/1;
- exact read-only record reminder fidelity: 1/1;
- state-version mismatch rejection and material-change stale marking: 2/2;
- user cadence, flexible alternative and rest/recovery propagation: 1/1;
- condition/clinician-instruction summary propagation: 1/1.

## Development evaluation inventory and actual metrics

Dataset: 76 visible, synthetic Stage 7 development cases. The sealed final holdout was not read or generated. Expected outcomes were stored before the final run.

| Metric | Result |
|---|---:|
| All development cases | 76/76 |
| High-criticality cases | 64/64 |
| Orchestration cases | 25/25 |
| Worker-boundary cases | 39/39 |
| Schedule cases | 12/12 |
| Urgent cases with zero ordinary workers/generation | 5/5 |
| Single-domain minimal routing | 6/6 |
| Structured communication-contract checks | 66/66 |
| Zero unauthorized worker writes/service-role use | 66/66 |
| Routing and fan-out group | 25/25 |
| Symptom-safety group | 16/16 |
| Medication-boundary group | 7/7 |
| Constraint-propagation group | 9/9 |
| Movement-stage group | 8/8 |
| Well-being-escalation group | 4/4 |
| Follow-up consent/provenance group | 5/5 |
| Plan variants/scheduling group | 18/18 |
| Provider/schema/budget group | 7/7 |

Final local deterministic evaluation latency was measured over 76 calls: median approximately 1.28 ms and maximum approximately 4.70 ms on this machine. These are local fixture runtimes, not network/provider or production latency claims. The generated JSON contains every redacted case result and exact measured value without raw personal text.

## Verification commands and actual results

| Command/check | Actual result |
|---|---|
| `.venv\Scripts\python.exe -m compileall -q app scripts tests` | PASS |
| `.venv\Scripts\python.exe -m unittest tests.test_orchestration -q` | 63/63 PASS |
| `.venv\Scripts\python.exe -m unittest discover -s tests -q` | 318/318 PASS |
| `python -m scripts.validate_content` | valid; 63 profiles, 0 published, 31 sources, 55 spans, 56 fragments |
| `python -m scripts.validate_content --require-review-ready` | valid with same honest 0-published status |
| `python -m scripts.run_contract_evals` | 64/64 PASS |
| `python -m scripts.run_journey_evals` | 26/26 PASS |
| `python -m scripts.check_stage1` | PASS; 318 tests, 55 candidates/anchors, 72 governed blocks, 0 errors |
| `python -m scripts.check_stage2` | PASS; existing database/storage/RLS report valid |
| `python -m scripts.check_stage3_ui` and `check_stage3` | both PASS; onboarding smoke made 0 network calls |
| `python -m scripts.check_stage4_readiness`, `check_stage4_ui`, `check_stage4` | all PASS; fixture UI smoke made 0 network calls |
| `python -m scripts.check_stage5` | PASS for the frozen Stage 5 implementation; 28/28 behavior cases and 212-case rectification matrix retained |
| `python -m scripts.run_stage6_safety_evals` | 45/45 PASS; 41/41 critical; 25/25 urgent zero-generation; 45/45 no tested unsafe reassurance |
| `python -m scripts.check_stage6` | PASS; draft specification/public fail-closed status preserved |
| `python -m scripts.build_stage7_evals` | generated 76 cases |
| `python -m scripts.export_orchestration_schema` | schemas and coverage regenerated |
| `python -m scripts.run_stage7_evals --write-report` | 76/76 PASS; 64/64 critical |
| `python -m scripts.check_stage7 --write-report` | valid; controlled Stage 8 engineering ready |
| Exact Stage 4 → Stage 5 local migration replay | PASS; synthetic upgrade fixture loaded, migration `20260911001300` applied, upgrade checker passed and cleaned up |
| Exact Stage 3 → current local migration replay | PASS; migrations `20260911001100`–`01300` applied, legacy checker passed and cleaned up |
| Clean local migration replay | PASS through `20260911001300`; Stage 7 adds no migration |
| All pgTAP files on upgraded history | 6/6 files, 254/254 assertions PASS |
| All pgTAP files on clean history | 6/6 files, 254/254 assertions PASS |
| Authenticated API checks on upgraded history | Stage 2 13/13; Stage 3 17/17; Stage 4 15/15; Stage 5 25/25; temporary fixtures removed |
| Authenticated API checks on clean history | Stage 2 13/13; Stage 3 17/17; Stage 4 15/15; Stage 5 25/25; temporary fixtures removed |
| `pnpm exec supabase db lint --local` on upgraded and clean histories | 0 findings on both |
| Secret/direct-database-client scan of Stage 7 path | no secret match; no Supabase/PostgREST/psycopg import |
| `git diff --check` after final whitespace rectification | PASS; line-ending conversion warnings only |

The database/API scripts used two temporary authenticated principals where applicable. The local service credential was used only inside existing fixture setup/cleanup scripts; ordinary Stage 7 workers have no database client or service-role access. No migration was added, deployed or remotely applied.

## First implementation failures and one consolidated self-review/rectification round

Initial implementation tests were not all green. The first focused run passed 45/49 and exposed ambiguous medication routing plus schedule enum/conversion defects. The first visible evaluator passed 57/61 and exposed missed daily-plan routing plus availability fallback defects. These were corrected before the formal review and retained as regression tests.

The formal line-by-line self-review then used this matrix. `FAIL` means the first reviewed implementation was incomplete; every listed failure was included in the single consolidated rectification pass and rerun.

| Requirement/control | First review | Evidence/finding | Consolidated disposition |
|---|---|---|---|
| Exact Stage 6 base/checks | PASS | exact accepted SHA and both jobs verified | retained |
| Safety Gate before orchestration | PASS | typed Stage 6 result required | retained |
| Urgent/clarification zero workers | PASS | schema plus tests/evals | retained |
| Eight-worker catalogue | PASS | exactly eight definitions | retained |
| One-domain minimal route | PASS | deterministic router | retained |
| Full plan max four contributors + composer | PASS | typed route constraint | retained |
| Worker-to-worker calls prohibited | PASS | catalogue literal false | retained |
| Authenticated owner/workspace context | PASS | strict owner-only snapshot | retained |
| Minimum context per worker | PASS | context policy filtering | retained |
| Exact post-Safety-Gate text binding | FAIL | post-gate text substitution was not initially bound | added normalized-input SHA checks at orchestrator and worker boundaries |
| Wrong-journey evidence rejection | FAIL | evidence journey was not initially rechecked by worker input | added exact stage/unit/range validation |
| Post-generation hard-constraint validation | FAIL | a schema-valid provider response could drop a constraint | added base and domain-specific semantic validators plus tampering tests |
| Allergen cannot be reintroduced | FAIL | pre-generation filter alone was insufficient | rechecked returned citation tags/evidence after provider output |
| Medication lifecycle | FAIL | timeline lacked explicit current/historical/stopped/unconfirmed categories | added typed lifecycle and mixed-timestamp deterministic ordering |
| Medication/instruction conflict | FAIL | related conflicting instruction could be omitted | added instruction/report conflict stop |
| Medication remains record-only | PASS | schema rejects plan contributions; change requests stop | retained and expanded |
| Routine symptom policy absence | PASS | worker abstains; public routing closed | retained as limitation |
| Movement sourced intensity | FAIL | first draft used fixed fixture wording without a typed evidence field | duration, cadence, intensity, alternatives and recovery now come from evidence metadata |
| Movement report conflict | FAIL | conflicting document fact did not stop | added conservative clarification stop |
| Persistent/worsening well-being concern | FAIL | supportive worker could continue | added professional-follow-up clarification stop |
| Follow-up conflicting instruction | FAIL | conflict was surfaced as a task but did not stop | added unresolved-instruction clarification stop |
| Follow-up reminder consent | PASS with weak evidence | proposal-only existed, but no named eval | added explicit consent case/assertion |
| Total orchestration deadline | FAIL | only worker-local timeout existed | passes remaining deadline to each provider and stops fan-out |
| Plan Composer provider/schema failure | FAIL | provider exception/invalid output could escape | added timeout/failure/budget/one-repair handling and semantic validation |
| Evidence-backed schedule duration/cadence | FAIL | fixed worker values could appear invented | moved values to typed evidence and explicit cadence source |
| Availability and appointment collision | PASS | deterministic placement/checks | retained |
| Weekday/weekend representation | PASS | seven-day enum/order | retained |
| Flexible alternative/rest-recovery propagation | FAIL | fields were implicit in notes | added explicit typed fields through contribution and schedule |
| Contradictory duplicate contribution | FAIL | identical IDs could overwrite silently | detect and make proposal ineligible |
| State mismatch/staleness | PASS | typed version and in-memory stale function | retained |
| Condition/clinician instruction plan visibility | FAIL | not directly measured | added context summary/constraint propagation tests and eval |
| Provider/token/latency/repair budgets | FAIL | provider-reported latency/tokens were not independently rechecked | added declared and measured budget checks; one repair maximum |
| Proposal-only/no writes/service role | PASS | literals, traces and import scan | retained |
| Generated artifacts canonical | PASS | scripts compare tracked truth/schema/coverage | regenerated after rectification |
| Stage 1–6 regressions | PASS | full deterministic and database matrix | retained |
| `git diff --check` packaging | FAIL | first packaging attempt revealed blank final lines in eight new source/test files | trimmed in final handoff commit and reran check |

No threshold was lowered and no expected outcome was changed to accept defective behavior. The evaluation grew from 61 initial cases to 76 final cases to cover the demonstrated gaps.

## Honest issue and limitation register

| Severity | Issue/evidence | User or safety impact | Disposition | Blocks controlled Stage 8? |
|---|---|---|---|---|
| High for public use | Safety specification remains draft; 0 weekly profiles are public | live health routing cannot be treated as reviewed | public/live generation remains fail-closed; controlled fixtures clearly labeled | No; blocks public release |
| High for public use | Routine non-urgent symptom-navigation policy has no approved release | generated symptom advice could be unsupported | routine worker is disabled/abstains without explicit controlled evidence | No; blocks that public capability |
| High for public use | No clinical or India-localisation approval is claimed | wording/applicability is not clinically certified | remains an external review gate | No; blocks public/clinical release |
| Medium | Only deterministic fixture provider was executed | no evidence of live model schema/tone/latency quality | provider-neutral interface retained; live benchmark requires separate authorization | No; provider capability remains disabled |
| Medium | Communication metric is deterministic lexical/contract evidence | cannot prove real human-perceived warmth | report states this limitation; product/manual review remains required | No |
| Medium | Synthetic 76-case set is small and visible | passing it does not prove population coverage or final holdout quality | sealed holdout remains untouched | No |
| Medium | Full-plan workers run sequentially in this implementation | fixture latency is tiny, but live full-plan p95 may be slower than a parallel implementation | total deadline and call caps enforced; calibrate after provider selection | No for controlled Stage 8; performance follow-up required |
| Medium | Broad report conflicts conservatively stop Nutrition/Movement because Stage 7 lacks a reviewed semantic relevance policy | may over-clarify an unrelated report conflict | conservative stop chosen; Stage 8/retrieval relevance can narrow only with evidence | No; safe limitation |
| Low | Deterministic classifier uses explicit supported English keywords | unseen phrasing may route to clarification/out-of-scope | safe stop; future frozen evaluation may justify one bounded classifier call | No |
| Low | Schedule uses deterministic 30-minute placement increments | may be less convenient than free-form timing | editable proposal and flexible alternatives provided | No |
| Low | Stage 7 has no UI | users cannot interact with workers yet | correctly deferred to Stage 9 | No |
| Informational | No Stage 7 database migration | no durable plan or worker state exists | intended boundary; Stage 10 owns persistence | No |
| Informational | GitHub checks were pending when this report was authored | remote commit had not yet been evaluated | required jobs are inspected on the exact pushed head and reported in final response; any failure changes verdict to NO-GO | Pending external gate |

## Proof of safety and write boundaries

- Stage 6: 25/25 urgent development cases made zero generation calls; 45/45 tested outputs contained no unsafe reassurance.
- Stage 7: 5/5 mixed urgent/product requests invoked zero workers and zero ordinary generation.
- Stage 7 worker traces: 66/66 reported zero direct writes and no service-role use.
- Static scan: no Supabase, PostgREST or psycopg client exists in the Stage 7 services.
- Every `ProposedAction` requires confirmation and is proposal-only; every `ProposedSchedule` is proposal-only and reports no persistent write.
- A provider cannot change request identity, Stage 6 text binding, evidence provenance, confirmed-fact set, personal constraints, medication record-only status, movement stop/clearance boundary, or urgent bypass without validation failure.

## Migration, configuration and provider impact

- **Database migration:** none.
- **Remote migration/deployment:** none.
- **Configuration/environment variables:** none added.
- **Dependencies/lockfiles:** none changed.
- **Paid model/API call:** none.
- **Provider selected:** none; deterministic fixture adapter only.
- **Public content status:** unchanged; 0 published profiles.
- **Safety specification status:** unchanged; draft.

## Deferred scope confirmation

Stage 8 answer composition/final validation, Stage 9 Streamlit experience, Stage 10 durable plan saving/staleness/reminders/human-review persistence, production model selection, production embedding/provider work, public deployment, clinical review and content publication were not implemented in this branch.

## Stage 8 recommendation

Proceed with Stage 8 controlled engineering only after the exact pushed Stage 7 commit passes both required GitHub jobs. Stage 8 must add independent journey, personal-constraint, evidence, citation, boundary and consistency validation before any Stage 7 draft is shown as an answer. It must preserve the same draft/public-release gates and must not reinterpret these synthetic software-contract results as clinical validation.
