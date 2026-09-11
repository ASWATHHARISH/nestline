# Stage 3 implementation: onboarding and journey resolution

**Implementation date:** 11 September 2026  
**Engineering status:** complete and deployed to the existing **nestline-dev** Supabase project  
**Content/safety release status:** still blocked by the separate Stage 0 specialist reviews

## What Stage 3 was required to do

The canonical architecture requires a privacy warning, Personal Empty and Fictional
Demo choices, possible-pregnancy/pregnancy/postpartum timing, deterministic date
calculation, a visible confirmation step, optional user-reported details, conflict
handling and timestamped symptoms. The execution plan additionally requires
rollover, boundary, future-date, disagreement, postpartum-transition and relogin
evidence, with no language model deciding dates or conflicts.

Stage 3 implements those requirements. Document upload, extracted-fact review and
the weekly dashboard remain in their planned Stage 4 and Stage 9 packages.

## Runtime flow

1. Streamlit shows the development/privacy boundary and authenticates through
   Supabase with the public project key.
2. The authenticated user selects or creates an owner-only Personal Empty or
   session-scoped Fictional Demo workspace.
3. A strict Pydantic input records one timing source and its effective date.
4. Pure Python resolves the current exact week/day or approximate range using an
   injected clock.
5. Existing and proposed timing are compared. A disagreement is displayed; code
   never chooses a side.
6. Allergies, history, dietary restrictions, movement restrictions, symptoms and
   a next appointment are optional.
7. Each symptom is handed to the existing Stage 6 draft rule contract. Urgent
   draft matches remain urgent; a draft non-match fails closed to clarification.
   Every result is labeled evaluation-only because specialist review is pending.
8. The user must confirm the displayed data and separately choose a new value when
   there is a conflict.
9. One owner-checked Supabase function commits journey state, facts, symptoms and
   appointments atomically. An idempotency key plus payload SHA-256 prevents a
   repeated click from creating duplicates.
10. Refresh or a new login reads the confirmed state and deterministically rolls
    it forward from the stored effective date.

## Deterministic date contract

The due-date calculation uses the conventional 280-day pregnancy position:
**position_day = 280 - (estimated_due_date - calculation_date)**. The implementation
is aligned with ACOG's 40-week/280-day convention and gestational-age definition:

- https://www.acog.org/womens-health/faqs/when-pregnancy-goes-past-your-due-date
- https://www.acog.org/practice-management/health-it-and-clinical-informatics/revitalize-obstetrics-data-definitions

The production clock explicitly uses the Asia/Kolkata date boundary, matching the
Streamlit prompts and database future-date validation even when the app host runs
in UTC.

Supported pregnancy display positions are week 1 day 0 through week 42 day 6.
Supported postpartum positions are delivery day 0 through postpartum week 12 day
6. Future effective/delivery dates and rollovers outside these ranges are rejected.

An approximate month stays an interval. It is never converted to one exact week.
Possible pregnancy never claims a confirmed pregnancy or week.

The state clock and the Stage 0 postpartum content grouping are deliberately
separate. Elapsed day 7 is chronological postpartum week 2 day 0, while product
decision 0002 keeps the **PPD7** overlay grouped with **PP01**. A regression test
locks that explicit content decision.

## Conflict and episode contract

- Two different exact pregnancy positions create a dating conflict with the
  absolute difference in days.
- An exact position inside an approximate range is compatible.
- Non-overlapping ranges require an explicit choice.
- Pregnancy to postpartum is a valid forward transition.
- Postpartum to pregnancy, or confirmed pregnancy back to possible pregnancy, is
  blocked in the same workspace. One workspace represents one pregnancy-through-
  postpartum episode; a new pregnancy starts in a new workspace.
- Both old and accepted new versions remain auditable.
- Direct client insert/update/delete on **journey_states** is denied.
- The older Stage 2 journey-mutation function is no longer executable by an
  authenticated client. Confirmed changes use **complete_onboarding**.

## Persisted provenance

A confirmed journey stores the timing source, original observation, effective
date, calculation date, confirmation time, confirming authenticated user, prior
conflicting state, day difference, submission key and payload checksum. Symptoms
store the report time, input source, route, matched draft rule IDs, rule-spec
version and evaluation-only marker. Optional facts and appointments retain the
same onboarding submission key.

The RPC takes an expected current version and locks the workspace/current state.
A stale client, reused key with changed data, cross-user request, future
calculation date or malformed optional item aborts the whole transaction.

Exit-hardening migration 01000 recomputes stored timing bounds inside Postgres. It
requires exact conflict provenance, validates due-date and delivery arithmetic,
rejects backward episode transitions and ensures onboarding symptom routing stays
evaluation-only while the SafetySpec is a draft. These checks protect the same
boundary even if a client sends a crafted RPC payload.

## Main files

| Purpose | File |
|---|---|
| Strict onboarding input/output models | app/schemas/onboarding.py |
| Deterministic resolver and conflict comparison | app/services/journey.py |
| Auth, preparation, confirmation and user-token gateway | app/services/onboarding.py |
| Streamlit onboarding experience | app/pages_and_components/onboarding.py |
| Application entry point | streamlit_app.py |
| Atomic database migration and authorization boundary | supabase/migrations/20260911000900_stage3_onboarding_commit.sql |
| Database-side arithmetic, conflict and safety hardening | supabase/migrations/20260911001000_stage3_exit_hardening.sql |
| Deterministic evaluation cases | evals/journey_resolver_set.jsonl |
| Database contract suites | supabase/tests/stage3_onboarding.test.sql and stage3_exit_hardening.test.sql |
| Real local API check | scripts/check_stage3_onboarding_api.py |
| Streamlit render check | scripts/check_stage3_ui.py |
| Machine-readable acceptance check | scripts/check_stage3.py |
| Deployment evidence | data/supabase/stage3-remote-verification.json |

## Verification evidence

| Check | Result |
|---|---:|
| Full Python regression | 154/154 passed |
| Existing deterministic contracts | 64/64 passed |
| Journey resolver frozen cases | 26/26 passed |
| Stage 2 + Stage 3 pgTAP on exact 00900 upgrade | 160/160 passed |
| Stage 2 + Stage 3 pgTAP on clean replay | 160/160 passed |
| Real local Auth/REST/Storage checks | 13/13 passed |
| Real local onboarding/relogin/isolation checks | 17/17 passed |
| Streamlit no-network initial render | passed |
| Supabase database lint | zero findings |
| Temporary users/workspaces/objects after checks | 0 |
| Remote migration history | 12 rows, ending at 20260911001000 |
| Remote direct/legacy journey mutation grants | 0 / 0 |

The API checks used temporary fictional identities and removed them. No real
medical record was used. The remote evidence file contains counts and hashes only,
with no key, password or token.

## What this does not claim

Stage 3 does not make the draft symptom rules clinically approved. It proves the
onboarding handoff, conservative behavior and provenance. Specialist clinical and
India-localisation review must finish before public release.

Stage 3 does not parse medical reports, activate extracted facts, generate a weekly
dashboard, retrieve RAG evidence or run an LLM. Those remain in their written later
stages. No model provider or LangSmith call was required to calculate or persist
journey timing.

## Reproduce locally

From the repository root:

~~~powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe -m scripts.run_contract_evals
.venv\Scripts\python.exe -m scripts.run_journey_evals
.venv\Scripts\python.exe -m scripts.check_stage3_ui
pnpm exec supabase db reset --local
pnpm exec supabase test db --local
pnpm exec supabase db lint --local
.venv\Scripts\python.exe -m scripts.check_stage3
.venv\Scripts\python.exe -m streamlit run streamlit_app.py
~~~

The real local API checks require the environment returned by
**pnpm exec supabase status -o env**; CI supplies that automatically.