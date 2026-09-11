# Stage 3 product and independent-review handoff

**Prepared for:** Kajal and an independent engineering reviewer  
**Prepared on:** 11 September 2026  
**Review target:** Stage 3 onboarding and journey resolution  
**Current state:** engineering complete; human review not pre-filled

This handoff is for product, visual and independent engineering review. It is not
a clinical approval form. The Stage 0 clinical, India-localisation and licence
queues remain separate.

## What to review

Stage 3 should let a user identify their journey position and optional onboarding
details, see the calculated result, resolve any disagreement themselves and save
one confirmed version. It must not read medical reports yet, invent a week from a
month, choose between conflicting dates, diagnose a symptom or call draft safety
wording clinically approved.

## Start the application

In the VS Code terminal at the repository root:

~~~powershell
.venv\Scripts\python.exe -m streamlit run streamlit_app.py
~~~

Use a fictional email and fictional health details only. The local **.env** must
contain the existing **NESTLINE_SUPABASE_URL** and
**NESTLINE_SUPABASE_PUBLISHABLE_KEY**. Do not copy keys into this review file.

## Product and visual walkthrough

Record pass, change requested or blocked for each item.

| ID | Fictional walkthrough | Expected result | Decision | Notes |
|---|---|---|---|---|
| S3-UI-01 | Open the app while signed out | Development/privacy warning, Sign in and Create account are clear |  |  |
| S3-UI-02 | Create/open Personal Empty | It starts without a journey state |  |  |
| S3-UI-03 | Choose “I may be pregnant” | No pregnancy week is claimed |  |  |
| S3-UI-04 | Enter an estimated due date | Exact week/day appears with calculation limitation |  |  |
| S3-UI-05 | Enter a dated week/day | Result rolls forward by elapsed days |  |  |
| S3-UI-06 | Enter approximate month 5 | A week range appears; no exact week is selected |  |  |
| S3-UI-07 | Enter delivery date today | Postpartum week 1 day 0 appears |  |  |
| S3-UI-08 | Enter a dated postpartum week/day | Result rolls forward and keeps postpartum language |  |  |
| S3-UI-09 | Add fictional allergy/history/diet/movement items | Items are visible for review and save together |  |  |
| S3-UI-10 | Add fictional breathing difficulty | Urgent draft route is visible and labeled awaiting specialist review |  |  |
| S3-UI-11 | Save without confirmation | Nothing is saved; explicit confirmation is requested |  |  |
| S3-UI-12 | Propose a different exact week after saving | Both values appear; a separate choice is required |  |  |
| S3-UI-13 | Refresh/sign in again | The same confirmed version is restored |  |  |
| S3-UI-14 | Open Fictional Demo | It is visibly fictional and separate from Personal Empty |  |  |
| S3-UI-15 | Read the bottom notice | Report upload is clearly described as Stage 4 |  |  |
| S3-UI-16 | Try to change postpartum back to pregnancy in the same workspace | Save is blocked and a new workspace is requested for the new pregnancy |  |  |

## Wording decisions Kajal should check

1. Does “Pregnancy timing not confirmed” communicate possible pregnancy without
   sounding like a diagnosis?
2. Are “effective date” prompts understandable in the week/day and month paths?
3. Is the approximate week range clear enough that a user will not assume it is
   an exact clinical estimate?
4. Does the conflict screen make it clear that the user chooses and the older
   value remains in history?
5. Is “movement restrictions” a clearer label than fitness restrictions?
6. Are the symptom messages prominent without implying the draft rules are
   clinically validated?
7. Is the separation between Personal Empty and Fictional Demo obvious?

Do not approve clinical accuracy, emergency wording or India localisation in this
product review unless the reviewer is explicitly serving in the qualified role.

## Independent engineering checks

| ID | Check | Evidence to inspect | Decision | Notes |
|---|---|---|---|---|
| S3-ENG-01 | All timing calculations are pure/deterministic | app/services/journey.py; tests/test_journey.py |  |  |
| S3-ENG-02 | Test clock controls date-sensitive cases | FixedClock; 26-case resolver set |  |  |
| S3-ENG-03 | Month remains a range | month unit tests and JSONL cases |  |  |
| S3-ENG-04 | Conflict is visible and user-chosen | onboarding service/unit tests |  |  |
| S3-ENG-05 | Save is atomic, idempotent and independently revalidated in SQL | migrations 00900/01000; pgTAP/API scripts |  |  |
| S3-ENG-06 | Direct/legacy journey writes are closed | migration grants; remote evidence counts 0/0 |  |  |
| S3-ENG-07 | User A cannot read/write user B | pgTAP and 17-check API run |  |  |
| S3-ENG-08 | Relogin restores the confirmed state | API check |  |  |
| S3-ENG-09 | Symptoms are timestamped with rule provenance | schema, RPC and API check |  |  |
| S3-ENG-10 | No temporary fixtures or secrets remain | deployment evidence; repository secret check |  |  |
| S3-ENG-11 | Exact 00900 upgrade and clean replay both work | 160 current assertions on both paths |  |  |
| S3-ENG-12 | CI reproduces Python, UI and Supabase checks | .github/workflows/data-contracts.yml |  |  |

## Explicit boundaries for this review

- Day 7 after delivery is stored chronologically as postpartum week 2 day 0.
  Product decision 0002 separately keeps the **PPD7** content overlay on **PP01**.
  Review both labels in context; do not merge state calculation with content
  grouping without a new recorded product decision.
- The symptom path uses a draft SafetySpec. Its route/provenance is tested, while
  public clinical release remains blocked.
- The application stores optional user-reported facts. It does not yet extract
  facts from an uploaded report.
- There is no RAG, chatbot answer generation or weekly recommendation dashboard
  in Stage 3.

## Reviewer record

Please fill this section manually.

- Reviewer name:
- Review capacity:
- Review date:
- Build or commit reviewed:
- Product/visual result:
- Engineering result:
- Requested changes:
- Evidence or screenshots attached:
- Signature/typed acknowledgement:

A reviewer must not mark a row passed without running or inspecting the stated
evidence. Any requested change should cite its row ID.