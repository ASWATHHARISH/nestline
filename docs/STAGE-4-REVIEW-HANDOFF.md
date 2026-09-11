# Stage 4 final verification, review and Stage 5 handoff

**Prepared:** 11 September 2026  
**Scope:** Stage 4 fictional document-to-confirmed-state behavior  
**Branch:** feat/stage-1-governed-ingestion  
**Reviewed baseline Git commit:** 68722f8039dcb5202ec105033f8b242f6dff64cb
**GitHub status:** baseline is pushed; current independent-review corrections are local and uncommitted
**Engineering verdict:** complete for Stage 5 engineering  
**Real/public medical upload:** blocked by the open release gates in Section 12

## 1. Purpose and review boundary

This is the single reviewer-facing guide for Stage 4. It joins the agreed
architecture, implementation, fictional scenarios, verification evidence,
failure/recovery record, human review steps and Stage 5 entry rules.

An engineering pass means the fictional flow and database boundaries passed the
recorded automated checks. It is not clinical approval, India-localisation
approval, product acceptance or permission to accept real medical records.

Stage 1 public-content governance is a separate workstream. Kajal's recorded
product/content decisions for the PC00/P10/PP01 slice are not relabelled here as
clinical, India-localisation or licence approvals.

## 2. Exact bundle under review

Every decision must identify this bundle. If a listed migration, fixture, schema,
UI behavior or review phrase changes, re-review the affected scope.

| Item | Identity |
|---|---|
| Project | nestline-dev |
| Supabase reference and region | jtmiduftpbvmahbmryki; ap-northeast-2 |
| Remote verification | 2026-09-11T12:16:44.0100105+05:30 |
| Document migration | 20260911001100_stage4_document_confirmation.sql |
| Document migration SHA-256 | ae8d9cb2ddf629e4ca359b6a34816db95476e74b48c79b9470b3bc081568f528 |
| API hardening migration | 20260911001200_stage4_api_role_hardening.sql |
| API hardening SHA-256 | c0720cdd99f324a63d4b9c6db1a8f271ca92c1b22fe567b7f64e32253ffb5349 |
| Fictional fixture set | DOC-001 to DOC-008 and DOC-003-noisy.png |
| Machine verdict | docs/STAGE-4-CHECK-RESULTS.json: valid true |
| Remote proof | data/supabase/stage4-remote-verification.json: contains_secrets false |

The worktree has no final Git commit for this bundle. Add it before a review is
used as release evidence.

## 3. Architecture alignment

| Planned requirement or exit test | Implemented result | Evidence | Status |
|---|---|---|---|
| Eight editable fictional records, watermarked PDFs, extraction truth, graph truth and one noisy case | DOC-001 to DOC-008 contain all four artifacts; DOC-003-noisy has frozen OCR truth | document_inventory.csv; Stage 4 readiness check | Pass |
| Reject locked, corrupt, unsupported, oversized and wrong-person files | Type, MIME, signature, size, lock and corruption checks run; identity requires an exact subject or verified fixture binding | Edge-case manifest; missing/blank/multiple/near/wrong identity tests | Pass |
| Keep the original private and owner scoped | Private Storage path, RLS and orphan cleanup are implemented | Migration, pgTAP and authenticated API tests | Pass |
| Typed proposals with page/span provenance | The review UI displays document, page, exact words, offsets, available coordinates, confidence, completeness, disposition and state | Extraction truth, schema and rendered UI tests | Pass |
| Medication remains recorded text | Candidate and confirmed state keep record_only; UI states that this is not treatment advice | DOC-003, schema and UI | Pass; human wording review open |
| Explicit edit, confirm, reject and keep-conflict | Every radio starts empty; every row needs a decision and the final checkbox before save enables | Rendered UI and commit-function tests | Pass; product review open |
| Proposal is never an active fact | Extraction has no confirmed-fact or graph side effect; direct candidate/graph mutation is revoked | pgTAP and API tests | Pass |
| Commit once; reject stale versions | Owner, complete review, version and idempotency are checked atomically | Database tests | Pass |
| Conflict preserves both sources | DOC-005/DOC-006 create unresolved state and clarification; disputed data cannot personalize; restriction invalidates movement output | Graph truth and database/API scenario | Pass |
| Prompt injection stays inert | DOC-006 attack text remains audit data and cannot become a candidate, tool call or policy | Deterministic and mocked-provider tests | Pass |
| Bad dose is visible | Mismatch is forced to manual review; only the corrected value can commit | Python and pgTAP tests | Pass |
| Duplicate upload/confirmation makes one logical update | File, extraction and commit paths are idempotent | Service and database tests | Pass |
| Data API follows least privilege | Anonymous access is six public read tables and one public retrieval function; personal access remains closed | Migration 01200 and remote checks | Pass |

This covers all five Stage 4 build items and all four exit conditions in
docs/NESTLINE-EXECUTION-PLAN.md. No Stage 4 engineering item is parked.

## 4. Implemented change inventory

1. Typed document, proposal, provenance, identity, review and commit contracts.
2. Default-off document feature with nine exact-hash repository fixture choices,
   native parsing and controlled OCR; no arbitrary uploader.
3. Optional OpenAI Structured Outputs adapter: no tools, store=false, exact-quote
   reconciliation and injected-line filtering.
4. Owner-scoped private Storage and PostgREST integration.
5. Field-by-field Streamlit review with full visible provenance, no preselection,
   and blocked save until every row is deliberately resolved.
6. Atomic extraction recorder and reviewed-state committer.
7. Confirmed facts, record-only medication state, typed graph links, clarification
   questions and movement-plan invalidation.
8. Stage 3 legacy-row backfill before stricter Stage 4 constraints.
9. Direct derived-state mutation closure.
10. API-role hardening after remote verification exposed unintended anonymous
    privileges from automatic Data API exposure.
11. Upgrade, clean-install, RLS, Storage, Auth/API, render, lint, migration-parity
    and drift verification.

## 5. Fictional scenario checklist

Do not use real-person records in this review.

| Record | Purpose | Expected behavior |
|---|---|---|
| DOC-001 | Pregnancy intake | Six proposals show exact evidence; nothing activates before review |
| DOC-002 | Laboratory report | Haemoglobin/specimen transcribe; missing range/interpretation abstain; no diagnosis |
| DOC-003 | Medication record | Name/dose/frequency/prescriber remain record-only; missing route abstains; no treatment change |
| DOC-004 | Routine visit | Week/due date/follow-up are proposed; missing new allergy data does not erase history |
| DOC-005 | Earlier walking instruction | Narrow walking scope is preserved and becomes a dependency only after confirmation |
| DOC-006 | Conflicting restriction | Attack text is inert; both sources survive; conflict creates clarification and remains non-personalizing; confirmed restriction stales movement output |
| DOC-007 | Follow-up | Explicit save is required; replay creates one logical task |
| DOC-008 | Postpartum summary | Transition is proposed; delivery type/feeding abstain; pregnancy episode remains history |

The controlled OCR image is
data/synthetic/noisy_variants/DOC-003-noisy.png. Its truth file requires five exact
fields. It proves one controlled case, not general OCR quality.

## 6. Product and rendered-UI review

### Setup

Use the fictional demo workspace and repository fixtures only. Enable the feature
only in the supervised local process.

    $env:NESTLINE_ENABLE_STAGE4_FIXTURE_DEMO="true"
    .venv\Scripts\python.exe -m scripts.check_stage4_ui
    .venv\Scripts\streamlit.exe run streamlit_app.py

The first command proves that the enabled supervised flow renders one exact-fixture
selector, no arbitrary uploader, full provenance, no preselected decisions and a
disabled save while one decision is missing. It separately proves the default
public state is closed, with zero network calls. It does not
replace visual acceptance.

For every proposal check:

- field, value, exact source words and page/span;
- confidence/completeness where shown;
- proposed, abstain, confirmed, rejected, conflict or superseded state;
- the available action and its consequence;
- visible fictional and private-data boundaries;
- absence of diagnosis, prescription, treatment change and invented missing data.

Saving must be blocked until every field has a deliberate decision and the reviewer
checks **I reviewed every field and want to apply these decisions**.

### Required rendered flows

| Flow | Action | Expected visible result |
|---|---|---|
| Baseline | Select DOC-001 and inspect before save | Extraction says nothing was applied; every proposal has evidence |
| Abstention | Select DOC-002 | Missing fields abstain and no diagnosis appears |
| Medication/OCR | Review DOC-003.pdf and controlled noisy image separately | Record-only wording appears; missing route abstains; no treatment advice |
| History | Review DOC-004.pdf | Missing new allergy information does not imply deletion |
| Conflict/dependency | Confirm relevant DOC-005 value, then review DOC-006 | Keep-conflict or reject is offered; keep-conflict gives unresolved/clarification feedback; confirmed restriction reports stale movement output |
| Duplicate | Select and process the same fixture twice | Existing logical document is reused |
| Follow-up | Review DOC-007.pdf | Work appears only after explicit save; automated proof confirms idempotent replay |
| Transition | Review DOC-008.pdf | Postpartum is proposed; delivery/feeding gaps abstain; no unsupported claim |

The bad-dose mismatch is a synthetic service/database scenario, not a changed
canonical PDF. Inspect its expected warning copy and use automated evidence to
confirm that the mismatch cannot silently commit.

Product reviewer questions:

- Is it obvious that extraction is only a draft?
- Can a user compare every proposal with its exact source?
- Are edit, reject, confirm and keep-conflict understandable before save?
- Is medication record-only language clear?
- Are abstention, conflict, clarification and stale-plan messages useful?
- Are the default-off and fictional boundaries visible before selection, during review and after save?
- Do errors help without exposing private text or secrets?

## 7. Specialist and operational review

### Clinical

A qualified reviewer checks all eight scenarios, especially no lab diagnosis,
medication as documentation only, retained allergy history, conflict/restriction
wording, follow-up wording, postpartum abstentions and the absence of unsafe
reassurance or implied clinical monitoring. The decision covers only this exact
fictional scope; it is not certification for real use.

### India localisation

A qualified India-context reviewer checks terms, dates, care-team/follow-up
language, escalation wording and service assumptions. Record state/language/service
limits. Do not infer nationwide availability from generic copy.

### Malware scanner decision

| Required field | Decision |
|---|---|
| Vendor and exact service | Pending |
| Supported PDF/PNG/JPEG behavior | Pending |
| Maximum size | Pending |
| Processing region | Pending |
| Timeout/retry limit | Pending |
| Failure behavior | Must fail closed |
| Retention, quarantine and deletion | Pending |
| Log redaction/forbidden fields | Pending |
| Test evidence and approver | Pending |

Until this is implemented and tested, non-fictional upload stays closed.

### Extraction provider benchmark

Aswath records the exact candidate model IDs and maximum cost per fictional document.
Codex then runs the frozen eight PDFs plus noisy image. Report counts and
denominators for field recall, critical misses, abstentions, exact source
reconciliation, dose errors, injection filtering, conflict preservation, schema
failures/retries, latency, tokens and cost. Valid JSON alone is not a pass. The
deterministic extractor remains the reproducible demo baseline.

## 8. Verified evidence

| Check | Result |
|---|---:|
| Python regression | 175/175 |
| Public-content contracts | 64/64 |
| Journey cases | 26/26 |
| Documents / candidates / abstentions | 8 / 33 / 6 |
| Graph truth | 8 files, 36 nodes, 29 edges |
| Controlled OCR | 1 image, 5 fields |
| Upload failures | 5/5 categories |
| Streamlit render | passed, 0 network calls |
| Upgrade-path and clean-install pgTAP | 206/206 on each |
| Authenticated API checks | 45/45 on each local history |
| Remote pgTAP | 206/206 |
| Local and remote lint | 0 findings |
| Pending remote migrations | 0 |
| Application-role drift | 0 |
| Nestline function semantic mismatch | 0/9 |
| Remote fixture/personal rows | 0 |
| Anonymous API boundary | public 200; personal 401 |

The clean local migration comparison returned No schema changes found.

Remote proof records 14 migrations, both Stage 4 functions, both authenticated
execute grants, zero direct derived-state mutation grants, six anonymous public
read grants and zero anonymous personal grants.

The raw hosted diff contains 112 Supabase-managed service_role statements, nine
CR/LF-only function serializations and public.rls_auto_enable(). Application-role
drift and Nestline function semantic drift are both zero, so this raw diff must not
be applied as a Nestline migration.

## 9. Failure and recovery record

| Finding | Recovery | Post-fix proof |
|---|---|---|
| PNG fingerprint path assumed UTF-8 | Hash binary fixtures as bytes | Full suite passes |
| Stage 4 fixtures changed broad Stage 1 checksum | Guarded rebind allows only top-level fingerprint change | 14 sources, 55 anchors and 54 Kajal decisions validate |
| Legacy confirmed rows lacked new decision fields | Backfill before constraints | Exact Stage 3-to-4 upgrade passes |
| Owner could mutate derived graph directly | Revoke direct writes; protected function writes | pgTAP/API pass |
| Conflict entered confirmed dependency input | Keep clarification but exclude disputed input | Conflict scenario passes |
| Model could echo injected line as proposal | Keep it only as untrusted audit text | Mock provider regression passes |
| Parallel SQL tests deadlocked transiently | Run independent pgTAP files sequentially | Both histories pass |
| Global Python lacked PyMuPDF | Use pinned project virtual environment | App suite passes |
| First Supabase token lacked project access | Replace with project-scoped token; no invalid-token write attempted | Link/deploy/verify pass |
| Data API defaults added 72 anonymous grant changes | Migration 01200 revokes broad access and restores six reads | 11 hardening tests and 200/401 boundary pass |
| Clean reset tried to alter platform-owner defaults | Scope default ACL to application migration owner | Clean and remote checks pass |

No known local Stage 4 engineering defect remains after the independent-review
corrections. GitHub CI must rerun after the local changes are pushed.

## 10. Reproduction

    .venv\Scripts\python.exe -m unittest discover -s tests
    .venv\Scripts\python.exe -m scripts.validate_content --require-review-ready
    .venv\Scripts\python.exe -m scripts.run_contract_evals
    .venv\Scripts\python.exe -m scripts.run_journey_evals
    .venv\Scripts\python.exe -m scripts.check_stage1
    .venv\Scripts\python.exe -m scripts.check_stage2
    .venv\Scripts\python.exe -m scripts.check_stage3
    .venv\Scripts\python.exe -m scripts.check_stage4_readiness
    .venv\Scripts\python.exe -m scripts.check_stage4_ui
    .venv\Scripts\python.exe -m scripts.check_stage4

Database review must run the exact migration-01000 upgrade with its legacy fixture
and a blank replay through 01200. Run each supabase/tests/*.test.sql sequentially,
then all three authenticated API scripts and lint. The exact sequence is in
.github/workflows/data-contracts.yml.

Never copy .env, tokens, passwords or service-role keys into reviews, screenshots,
terminal logs or Git.

## 11. Governed finding and decision loop

Record one row per finding.

| ID | Date | Reviewer/role | Document/screen | Severity | Exact finding | Required correction | Owner | Status | Rerun evidence |
|---|---|---|---|---|---|---|---|---|---|
| S4-R-___ | YYYY-MM-DD | Name/role | DOC/UI/artifact | blocker/high/medium/low | Pending | Pending | Pending | open/fixed/rejected | Pending |

Rerun rules:

| Change | Minimum rerun |
|---|---|
| Copy/layout | UI checker, affected rendered flows, product review |
| Fixture/truth | Readiness, Stage 4 checker, Python suite, affected specialist reviews |
| Parser/extractor/schema | Python, readiness, UI, Stage 4 and provider benchmark if relevant |
| Database/RLS/migration | Both histories, 206 pgTAP, 45 API, lint and remote drift/boundary checks |
| Clinical/local wording | Product plus each affected specialist role |
| Model/prompt | Frozen benchmark and injection/abstention/source regressions |

A rejected finding needs a recorded reason and decision-maker. Silence is not
acceptance.

Copy one block per reviewer role:

    Stage: 4
    Migration hashes: <both hashes from Section 2>
    Final Git commit: <required for release evidence>
    Reviewer name:
    Role: product | clinical | india_localisation | security_platform | provider_benchmark
    Capacity or qualification:
    Date and timezone:
    Documents/screens reviewed:
    Evidence inspected:
    Disposition: accepted | changes_requested | rejected | needs_specialist_review
    Finding IDs:
    Exact reason:
    Conditions or limitations:
    Typed acknowledgement:

One person may sign multiple roles only if their real responsibility or
qualification covers each. Automated tests do not sign a human role.

## 12. Open gates and ownership

| Gate | Safe current behavior | Owner/action | Blocks Stage 5 engineering | Blocks real/public use |
|---|---|---|---:|---:|
| Rendered product review | Automated render only | Kajal/named product reviewer | No | Yes |
| Clinical review | Unreviewed guidance unpublished | Qualified clinician | No | Yes |
| India-local review | Unreviewed local claim unreleased | Qualified local reviewer | No | Yes |
| Production scanner | Real upload fails closed | Product/security decision, then Codex implementation | No | Yes |
| Exact model/cost/benchmark | Deterministic extractor | Aswath decides; Codex benchmarks | No | Yes |
| Final Git identity | Local worktree only | Aswath authorizes future commit/push | No locally | Team/release gate |

## 13. Completed deployment and next executable actions

### Completed remote deployment

The replacement project-scoped Supabase token was used only from the local
environment. Migrations 01100 and 01200 were each dry-run, deployed and verified.
The final remote dry run has no pending migration; all 14 versions are present,
all 206 remote pgTAP assertions pass, lint has zero findings, the 200/401 API
boundary is correct and no temporary or personal fixture rows remain. No token
value was written to a tracked artifact.

### Provider decision still required

Choose the exact candidate extraction model IDs and maximum permitted cost per
fictional document. Save them locally as:

    NESTLINE_DOCUMENT_MODEL=<exact chosen model ID>
    NESTLINE_DOCUMENT_MAX_COST_USD=<chosen ceiling>

Do not select values by assumption or place them in Git. The frozen benchmark in
Section 7 must pass before live provider extraction is accepted. This decision can
run alongside deterministic Stage 5 work.

### Start Stage 5 in this order

1. Freeze typed retrieval-request, evidence-packet and trace schemas.
2. Add exact SQL retrieval for confirmed personal facts and published public
   metadata.
3. Enforce workspace, evidence-lane, publication, stage/week/range, jurisdiction
   and condition filters before ranking.
4. Add Postgres full-text retrieval.
5. Add pgvector retrieval only for approved public chunks and allowed confirmed
   personal chunks.
6. Merge candidates with deterministic reciprocal-rank fusion and stable tie
   rules.
7. Add bounded graph expansion from the typed Stage 4 nodes and edges.
8. Prove the document to restriction/conflict to stale-plan/clarification journey.
9. Key public cache entries by corpus/filter version and personal entries by
   workspace/state version; prove there is no cross-workspace reuse.
10. Run wrong-week, private-decoy, unpublished-source, conflict and graph-ablation
    evaluations before declaring Stage 5 complete.

## 14. Stage 5 entry contract

Stage 5 engineering may begin. It must retrieve only confirmed personal facts,
exclude proposals and conflicts from personalization, keep medication record-only,
carry provenance, and filter workspace, approval, evidence lane, stage/week/range
and jurisdiction before ranking. It must preserve clarification/stale markers,
bound graph expansion, prove graph value with an ablation and prevent cache reuse
between workspaces.

Only approved public content may enter production embeddings or live RAG. All
required reviews remain mandatory before public release.

## 15. Final checklist

### Engineering

- [x] Five planned Stage 4 build items implemented.
- [x] Four Stage 4 exit behaviors have executable proof.
- [x] Upgrade and clean database histories pass.
- [x] Migrations 01100 and 01200 deployed and verified remotely.
- [x] Migration parity, lint, role drift, function semantics and cleanup pass.
- [x] Anonymous public/private API returns intended 200/401.
- [x] Remote proof contains no secret.

### Human and operational release

- [ ] Product behavior and final rendered layout accepted for this bundle.
- [ ] Qualified clinical decision recorded.
- [ ] Qualified India-localisation decision recorded.
- [ ] Scanner policy implemented and tested.
- [ ] Exact extraction model and cost ceiling recorded.
- [ ] Frozen fictional provider benchmark passed.
- [ ] No real-person fixture or secret appears in evidence.
- [ ] Final reviewed Git commit recorded.

### Stage 5 boundary

- [ ] Confirmed-only personal retrieval.
- [ ] Conflicts/proposals remain non-personalizing.
- [ ] Medication remains record-only.
- [ ] Filter-first negative-decoy tests pass.
- [ ] Bounded graph ablation is recorded.

## 16. Evidence index

- docs/NESTLINE-EXECUTION-PLAN.md
- docs/STAGE-4-IMPLEMENTATION.md
- docs/STAGE-4-SELF-VERIFICATION-AND-STAGE-5-READINESS.md
- docs/STAGE-4-PLAIN-LANGUAGE.md
- docs/STAGE-4-CHECK-RESULTS.json
- data/supabase/stage4-remote-verification.json
- data/synthetic/document_inventory.csv
- .github/workflows/data-contracts.yml
- supabase/migrations/20260911001100_stage4_document_confirmation.sql
- supabase/migrations/20260911001200_stage4_api_role_hardening.sql

## 17. Current decision

- **Stage 4 fictional-demo engineering:** pass.
- **Stage 5 local and nestline-dev engineering may begin:** yes.
- **Real/public medical-document upload:** no.
- **Known unfixed Stage 4 code defect:** none found.
- **GitHub updated:** no, following Aswath's instruction.
