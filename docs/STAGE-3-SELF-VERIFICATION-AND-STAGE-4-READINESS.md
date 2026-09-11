# Stage 3 self-verification and Stage 4 readiness

**Audit date:** 11 September 2026  
**Auditor:** Codex engineering self-review  
**GitHub status:** local working tree only; no commit, push or pull request  
**Deployment status:** migrations 00900 and 01000 are deployed to the existing `nestline-dev` Supabase project

## Verdict

Stage 3 engineering is verified and ready for controlled Stage 4 development with
fictional data. The result is supported by a clean installation, an exact upgrade
from the previously deployed Stage 3 base, real local Auth/REST/Storage calls, a
Streamlit render, frozen deterministic cases and a read-only inspection of the
remote database catalogue.

Nestline is **not ready for live or public medical-document upload**. That boundary
is intentional. The upload-scanning policy, qualified clinical and
India-localisation reviews, and final product visual acceptance are release gates
that code cannot self-approve.

## What I checked against

The audit used these tracked sources rather than an improvised checklist:

- `docs/Nestline updated architecture.md`, especially Stage 3 onboarding and
  Stage 4 personal documents;
- `docs/NESTLINE-EXECUTION-PLAN.md`, S3 and S4 exit criteria;
- the deployed `nestline-dev` Supabase catalogue;
- all tracked application contracts, migrations, tests, evaluation fixtures and
  fictional document artifacts.

## Stage 3 requirement-by-requirement result

| Requirement | Result | Evidence |
|---|---|---|
| Personal Empty and isolated Fictional Demo workspaces | Pass | Streamlit flow, owner-only RLS, 13 Storage/API checks |
| Possible pregnancy without an invented week | Pass | resolver, unit test, persisted API matrix |
| Estimated due date | Pass | 280-day formula, unit tests, persisted API matrix, SQL arithmetic check |
| Dated manual week/day | Pass | deterministic roll-forward, unit/API/pgTAP evidence |
| Approximate month remains a range | Pass | resolver cases, schema, persisted API matrix |
| Delivery date and postpartum week/day | Pass | boundary tests, persisted API matrix, SQL arithmetic check |
| India product-date boundary | Pass | `Asia/Kolkata` clock and database validation |
| Optional allergies/history/restrictions/symptoms/appointment | Pass | atomic rich onboarding API case |
| Explicit confirmation and conflict choice | Pass | UI/service tests, atomic RPC and conflict history |
| Refresh/relogin persistence | Pass | real local Auth/PostgREST check |
| No model decides dates or conflicts | Pass | deterministic resolver has no model/network dependency |
| Draft safety rules cannot appear approved | Pass | application marker plus database constraint |
| Owner cannot bypass the confirmed committer | Pass | zero direct and zero legacy mutation grants remotely |

## What went well

- The original Stage 3 design already separated calculation from generation. The
  resolver is pure Python with an injected clock, which made all date boundaries
  replayable.
- The database already had one atomic, idempotent onboarding function. Facts,
  symptoms, appointments and journey state either commit together or all roll
  back.
- RLS and Storage tests exercise two real authenticated principals. They test the
  actual access boundary rather than relying only on SQL text inspection.
- The previous migration already included
  `user_reported_possible_pregnancy`. I initially suspected it was absent while
  reading the base table definition, then traced the full migration chain and
  corrected that finding before changing anything. No unnecessary source change
  was made.
- All eight canonical fictional Stage 4 reports are present as editable text,
  watermarked PDF and extraction truth. Their hashes and page/span provenance are
  internally consistent.

## What the exit audit found and how it was corrected

### 1. Persistence coverage did not exercise every timing path

The earlier API proof focused on the rich manual week/day submission. That left a
risk that a valid UI calculation could fail when persisted through Supabase.

**Correction:** `scripts/check_stage3_onboarding_api.py` now creates separate
fictional workspaces and persists possible-pregnancy, due-date, approximate-month,
delivery-date and postpartum-week paths, in addition to manual week/day. The API
suite increased from 12 to 17 checks and removes every temporary workspace/user.

### 2. A backward care-episode transition looked user-selectable

Postpartum to pregnancy, or confirmed pregnancy back to possible pregnancy, cannot
belong to the same one-episode workspace. The app previously represented this as a
normal timing disagreement even though accepting it could not produce a coherent
state.

**Correction:** the resolver marks this case `commit_blocked`; the service refuses
the write; and Streamlit tells the user to keep the current state or start a new
workspace for a new pregnancy. Unit, frozen and database tests cover the rule.

### 3. The database trusted client-computed conflict metadata

A correctly behaving app sent the right conflict flag and day difference, but a
crafted RPC request could omit a real conflict or submit fabricated conflict
provenance.

**Correction:** migration `20260911001000_stage3_exit_hardening.sql` recomputes
both stored timing positions at the proposed calculation date. A trigger requires
the exact previous state ID and computed difference when a conflict exists, rejects
fabricated conflicts, rejects noncontiguous versions and blocks backward episode
transitions.

### 4. Due-date and delivery arithmetic needed a second boundary check

The Python resolver calculated these values correctly, but the RPC accepted the
calculated week/day as client data.

**Correction:** database constraints independently verify the 280-day due-date
formula and elapsed delivery-day formula. Tampered examples fail with a constraint
error and leave no partial state.

### 5. Draft symptom safety could be mislabeled by a crafted payload

The Stage 6 SafetySpec is still a draft. The app correctly sends
`safety_evaluation_only=true`, but the database previously trusted that Boolean.

**Correction:** every symptom written by an onboarding submission is now required
to remain evaluation-only. The negative pgTAP case proves a false value rolls back
the entire onboarding transaction.

### 6. Demo seeding needed the newer confirmation fields

The demo seed function was defined before migration 009 added confirmation identity
and time. The new invariant exposed that a future demo session could create a
confirmed row without those fields.

**Correction:** the seed now records confirmation time, authenticated confirmer,
India calculation/effective dates and a future-relative fictional appointment.

### 7. Current documentation contained stale test counts

An earlier audit changed a claimed Stage 2 count from 143 to the remote record of
141 without preserving the corresponding SQL source. The current tracked Stage 2
file actually contains and now pins 122 assertions. With 26 Stage 3 base and 12
Stage 3 hardening assertions, the Stage 2–3 subtotal is 160. The current Stage
2–4 full gate is 206. STAGE-2-ASSERTION-COVERAGE-MAPPING.md records the evidence
gap and current coverage without inventing a one-to-one mapping.

## Failures during this verification and recovery

The first hardened database run failed an older deletion test. The initial
confirmation constraint required an unconfirmed journey to erase its historic
confirmation identity. That conflicts with intentional dependency invalidation:
when a confirmed source fact is removed, the journey becomes unconfirmed while
its audit history must remain visible. The rule was corrected to require paired
confirmation fields and require them for a currently confirmed row, while allowing
an invalidated row to retain history. The full older suite then passed.

One lint invocation ran at the same time as pgTAP and inspected pgTAP's temporary
functions, producing extension-only false findings. Lint was rerun after the test
transaction ended and returned zero schema findings. CI keeps database tests and
lint sequential.

## Final engineering evidence

| Verification | Observed result |
|---|---:|
| Full Python regression | 154/154 passed |
| Existing deterministic contract cases | 64/64 passed |
| Frozen journey/date/conflict cases | 26/26 passed |
| Focused journey + onboarding unit tests | 24/24 passed |
| Database assertions, exact 00900 to 01000 upgrade | 160/160 passed |
| Database assertions, clean twelve-migration install | 160/160 passed |
| Real local Auth/REST/Storage checks | 13/13 passed |
| Real local onboarding/relogin/isolation checks | 17/17 passed |
| Streamlit initial render | passed, zero network calls |
| Supabase database lint | zero findings |
| Remote migration history | 12 rows, ending at 20260911001000 |
| Remote direct / legacy journey mutation grants | 0 / 0 |
| Remote private-bounds grants to authenticated | 0 |
| Temporary verification fixtures remaining | 0 |

Machine-readable evidence:

- `docs/STAGE-3-CHECK-RESULTS.json`
- `data/supabase/stage3-remote-verification.json`
- `docs/STAGE-4-READINESS-CHECK-RESULTS.json`

## Stage 4 fixture readiness

The repeatable readiness checker verified:

- 8 inventory records, exactly `DOC-001` through `DOC-008`;
- 8 editable source-text files;
- 8 one-page watermarked fictional PDFs;
- 8 expected-extraction JSON files;
- 33 proposed fact candidates with page/span provenance;
- 6 explicit abstentions for values that are not supplied or not recorded;
- 1 prompt-injection fixture preserved as untrusted document text;
- matching PDF/text checksums and expected behavior labels.

This is enough to begin Stage 4 engineering. Three items are deliberately part of
the Stage 4 build and are still absent:

1. one controlled noisy/OCR variant with matching truth;
2. typed expected node/edge changes, replacing the current high-level graph
   behavior labels;
3. locked, corrupt, unsupported, oversize and wrong-person upload fixtures.

The checker reports these items every run so they cannot be forgotten.

## Parked release gates

| Gate | Why it is parked | Required owner/time |
|---|---|---|
| Upload malware-scanning policy | A product/security/platform decision is needed before broader deployment | Decide during the Stage 4 upload-boundary task |
| Qualified clinical and India-localisation review | Engineering cannot self-certify health wording or local clinical interpretation | Must finish before live health guidance/public release |
| Final rendered product review | The product reviewer is unavailable for this audit | Complete before public release |
| Live provider benchmark and tracing | Belongs to controlled Stage 4 extraction evaluation; only fictional/redacted traces may be sent | Run after deterministic upload/parser baseline exists |
| Weekly home, chatbot and recommendations | Planned later integration work, mainly Stages 5, 7, 8 and 9 | Do not pull into document ingestion |

## Stage 4 execution order

1. Add the noisy/OCR and upload-edge-case fixture pack, then freeze expected truth.
2. Build the authenticated private upload boundary with format/size/lock/corrupt
   handling and the documented scanning decision.
3. Parse native PDF text first and use OCR only for image-based input.
4. Produce typed candidate facts with document, page and exact-span provenance;
   keep medication text record-only.
5. Build edit/confirm/reject/conflict/superseded states. Unconfirmed extraction
   must never personalize output.
6. Commit confirmed changes atomically and idempotently with stale-version checks.
7. Create typed graph changes and dependency invalidation only after confirmation.
8. Run clean, noisy, conflicting, duplicate, dose-error and prompt-injection
   evaluations with synthetic/redacted LangSmith traces.

Run the readiness gate at any time with:

```powershell
.venv\Scripts\python.exe -m scripts.check_stage4_readiness --write-report
```