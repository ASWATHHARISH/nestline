# Nestline human-review handout for Kajal

**Prepared:** 10 September 2026

**Purpose:** Give Kajal and the specialist reviewers one safe, repeatable process for reviewing Nestline's draft knowledge before any of it enters embeddings, live RAG or the public demonstration.
**Current state:** The review material exists, but there are **zero recorded human approvals**. Every item must stay a draft until the correct reviewer makes a traceable decision.

## The one rule to remember

Each reviewer signs only for the job they actually performed.

For example, Kajal may decide that a card is clear and useful for the dashboard. That is a **product decision**. It does not mean that the medical statement is clinically correct, suitable for India, or legally reusable.

```text
Source passage
      |
      v
Licence review -------- Can we store, quote, display and embed it?
      |
      v
Content review -------- Does our wording faithfully match the source?
      |
      v
Clinical review ------- Is it medically responsible within its stated scope?
      |
      v
India-localisation ---- Is the country, service and timing context suitable?
      |
      v
Product review -------- Is it clear, useful and placed correctly in Nestline?
      |
      v
All required decisions accepted for the same unchanged version
      |
      v
Eligible for publication and embeddings
```

If one required role is still pending, the item remains pending. If the wording, source, week range, condition, country or licence information changes after review, the affected decisions must be made again for the changed version.

## What Kajal should do

Kajal owns the **product, user experience and evaluation review**. She may also perform an editorial content pass if the team explicitly records her capacity as `content reviewer`, but she must not be listed as a clinician or licence reviewer unless she truly has the relevant qualification or authority.

Kajal should:

1. Review the representative journey profiles and their card order.
2. Review the 55 Stage 1 evidence candidates for clarity, usefulness and correct placement.
3. Review the practical nutrition, movement, wellbeing and follow-up catalogue items.
4. Mark uncertainty honestly and route it to the correct specialist.
5. Decide whether the optional fetal-size comparison feature remains hidden.
6. Coordinate the qualified clinical, India-localisation and source/licence reviews.
7. Return complete decision records using the template in this handout.

Kajal should not write code, edit generated IDs, create embeddings, or manually change publication status.

## What to open in VS Code

Review these files in this order:

1. `docs/STAGE-0-REVIEW-PACKET.md`
   This is the main human-readable packet. It contains the representative weekly profiles, draft wording, evidence links, conditions and catalogue proposals. The fingerprint printed near the top identifies the exact version being reviewed.

2. `docs/STAGE-1-REVIEW-QUEUE.md`
   This contains 55 extracted evidence candidates. Each candidate shows the source text, locator, week or stage, intended dashboard slot, profile links and reason it is still blocked.

3. `data/catalogues/food_components.csv`
   Twelve nutrition proposals.

4. `data/catalogues/movement_components.csv`
   Six movement proposals.

5. `data/catalogues/wellbeing_exercises.csv`
   Six mental-wellbeing proposals.

6. `data/catalogues/followup_milestones.csv`
   Ten follow-up proposals.

7. `data/safety/rule_spec.yaml`
   Draft safety rules. Kajal may review the user experience and wording, but a suitably qualified maternal-health reviewer must assess the medical routing before release.

8. `data/guidelines/source_registry.csv`
   The source/licence reviewer uses this to check ownership, dates, jurisdiction, permitted use, attribution and any restrictions.

Do not treat the text labelled **“Codex assessment”** as a human decision. It is only an engineering explanation of why the draft was created.

## Review scope

The data model can represent the full journey, but the capstone does not pretend that all 54 weekly pregnancy/postpartum profiles have already received deep human review.

### Representative journey slice

Review these 17 populated records:

- `PC00`: possible pregnancy;
- `P01`, `P09`, `P10`, `P24`, `P36`: representative pregnancy weeks;
- `PP01`, `PP06`, `PP12`: representative postpartum weeks;
- `PPD0` through `PPD7`: early postpartum day overlays.

The remaining 46 journey records are intentional hidden shells. Kajal should not fill them with invented or copied guidance merely to make every week look complete.

### Stage 1 evidence queue

The 55 candidates are grouped by source as follows:

| Source ID | Candidates | Main review theme |
|---|---:|---|
| `BHC-WEEKS` | 2 | Week 9/10 development wording, measurement and old-source currency |
| `NHM-CHO` | 11 | India programme and maternal-care information |
| `NHM-MOTHERHOOD` | 13 | India pregnancy/postpartum guidance and warnings |
| `NHS-PP-ACTIVE` | 6 | Postpartum movement and conditions |
| `NHS-PP-BODY` | 1 | Postpartum body/fertility context |
| `NHS-PP-DIET` | 1 | Postpartum diet context |
| `NHS-PP-SUPPORT` | 1 | Postpartum professional support context |
| `NHS-PREG-MIND` | 2 | Pregnancy mental-wellbeing actions |
| `OWH-HEALTH` | 8 | Pregnancy health and food-safety guidance |
| `OWH-RECOVERY` | 2 | Early postpartum recovery |
| `OWH-STAGES` | 4 | General journey-stage content |
| `OWH-TEST` | 1 | Pregnancy-test instructions |
| `OWH-WELLBEING` | 2 | Postpartum mental-wellbeing actions |
| `PIB-PMSMA` | 1 | India programme information |
| **Total** | **55** | All remain pending human review |

For the strongest time-bound workflow, Kajal can product-review all 55 candidates, while the specialists fully review the smaller set that will appear in the first demo. The rest stays visibly pending and cannot enter embeddings or live RAG.

## The five review roles

### 1. Product review — Kajal

The product reviewer checks whether the information works correctly inside Nestline.

For every profile or evidence candidate, ask:

- Is the title understandable to a pregnant or postpartum user?
- Is this useful at this stage or week?
- Is the proposed dashboard area correct: nutrition, movement, mental wellbeing, preparation, follow-up, development, consider/avoid, or ask-a-professional?
- Is the card order sensible?
- Does the text explain when it applies?
- Does the interface need more user information before showing it?
- Would the wording sound like a diagnosis, prescription or personal clearance?
- Are country and source labels visible where needed?
- If this information is unavailable, does the planned empty state explain that honestly?
- Does the content support one of the agreed demonstration stories?

The product reviewer may accept the placement while requesting simpler wording. If there is any doubt about medical meaning, choose `needs_specialist_review`.

### 2. Content review — named editor

The content reviewer checks whether Nestline's proposed wording faithfully represents the exact source passage.

For every item, ask:

- Does the proposed wording say only what the cited passage supports?
- Has an important qualifier, exception or warning been removed?
- Does a general statement wrongly sound week-specific?
- Are measurements, units and terminology copied accurately?
- Does the week/day range match the source?
- Are the conditions explicit, such as confirmed pregnancy, breastfeeding, birth setting, movement suitability or professional instruction?
- Is the source link and locator sufficient for another reviewer to verify it?
- Is the paraphrase clear without becoming stronger than the source?

Never repair uncertainty by writing a plausible medical statement from memory. Request a better source or specialist decision.

### 3. Clinical review — qualified maternal-health reviewer

This role must be performed by a person with suitable maternal-health expertise for the reviewed subject and release context. Record the person's name and capacity truthfully.

The clinical reviewer checks:

- medical meaning and important omitted context;
- appropriate pregnancy/postpartum stage and timing;
- contraindications, eligibility and stop conditions;
- movement and postpartum recovery boundaries;
- food-safety and medicine-related boundaries;
- safety wording and escalation behavior;
- whether measurements are presented as general education rather than a personal result;
- whether a statement could cause unsafe reassurance or delay professional care;
- whether a concern requires a narrower claim or specialist review.

This review is not a certification that Nestline is safe for real clinical use. It is a traceable review of the specific, unchanged demonstration content.

### 4. India-localisation review — named local-context reviewer

The India-localisation reviewer checks:

- whether programme names and descriptions are current;
- whether care timing and service references apply in the intended Indian context;
- whether a foreign source is clearly labelled as foreign guidance;
- whether emergency or contact instructions avoid foreign phone numbers and assumptions;
- whether availability may vary by state, district, facility or birth setting;
- whether the wording promises a service that may not be locally available;
- whether local food examples and terms are understandable without becoming a personal diet prescription;
- whether unresolved regional differences are shown as unresolved.

The reviewer must not convert one programme document into a universal personal appointment schedule.

### 5. Source and licence review — authorised reviewer

The source/licence reviewer makes a separate decision for each intended use. “The page is public” is not sufficient.

Record whether Nestline may:

- store the selected text;
- quote the selected text;
- paraphrase it;
- display it in the application;
- include it in a downloadable or public repository;
- convert it into embeddings;
- use it in a public demonstration;
- use it commercially, if that ever becomes relevant;
- retain the required attribution and source link.

Check the exact source, publisher, version/date, third-party credits and selected section. Resolve the outstanding BHC currency/reuse decision and the NHM use conditions explicitly. When permission is uncertain, choose `needs_specialist_review` or reject the intended use; do not guess.

## Step-by-step process for Kajal

### Step 1 — Write down the release slice

Before reviewing individual items, record which profiles and cards the first demonstration will actually show. The recommended first release slice is `PC00`, `P10` and `PP01`, expanded only after those paths work end to end.

This does not delete the other representative profiles. It establishes which items must receive all required decisions first.

### Step 2 — Review the journey experience

Open each selected profile in `docs/STAGE-0-REVIEW-PACKET.md` and inspect:

1. hero/title;
2. general development information;
3. nutrition cards;
4. movement cards;
5. mental-wellbeing cards;
6. preparation and follow-up;
7. consider/avoid content;
8. questions for the care team;
9. conditions controlling whether each card appears;
10. source and country labels;
11. missing-information, conflict and unpublished states.

For `PC00`, never imply pregnancy is confirmed. For `P10`, keep the general weekly measurement separate from any future uploaded scan result. For `PP01`, preserve birth-setting, recovery and professional-instruction conditions.

Record one decision for every reviewed profile and any separate decision required for a disputed card.

### Step 3 — Review the matching Stage 1 evidence

For each selected profile, search `docs/STAGE-1-REVIEW-QUEUE.md` for its profile ID, then review the linked evidence tasks.

For every task:

1. note the `REV-...` review-task ID and `E-...` evidence ID;
2. open the cited source and find the stated locator;
3. compare the exact passage with the proposed Nestline use;
4. verify stage, week/day range, jurisdiction and conditions;
5. verify profile and catalogue links;
6. check the proposed dashboard slot;
7. record the decision for the reviewer's actual role;
8. supply exact replacement wording when requesting a wording change.

Checking a box inside the generated queue does not change the governed data. A completed decision record must be returned to Aswath/Codex for application and revalidation.

### Step 4 — Review the practical catalogues

Review all 34 practical items:

- **Nutrition (12):** check names, dietary labels, allergen fields, handling notes and qualitative purpose. Do not create calories, doses, therapeutic diets or invented portions.
- **Movement (6):** check eligibility, progression, professional-instruction conditions and linked stop rules. Do not imply medical clearance.
- **Mental wellbeing (6):** use optional, respectful language and a route to professional support where appropriate. Do not present an exercise as therapy or a guaranteed treatment.
- **Follow-up (10):** check timing, programme/local context and suggested questions. Do not turn general programme information into the user's confirmed appointment.

An allergy or restriction should exclude conflicting food suggestions. Missing information should produce a request for clarification, not assumed suitability.

### Step 5 — Keep size comparisons hidden or fully verify them

There are 42 fetal-size comparison proposals. Their measurements and comparison-object dimensions have not been verified.

Recommended decision for the capstone:

```text
Keep all 42 comparison objects hidden.
Show only a reviewed general measurement or development statement where available.
Never replace a user's scan measurement with a general weekly measurement.
```

If Kajal wants to enable the feature, every enabled week needs a named measurement source, measurement convention, object dimensions, wording review, clinical review, licence review and product review. Selecting a familiar fruit or object without those checks is not approval.

### Step 6 — Send specialist batches

Give each specialist only the items relevant to their role, together with:

- this handout;
- the exact release fingerprint from `docs/STAGE-0-REVIEW-PACKET.md`;
- the applicable review-task and evidence IDs;
- source URLs and locators;
- proposed Nestline wording and conditions;
- intended use: storage, display, embedding and/or public demo;
- the decision template below.

Do not ask one reviewer to sign a single vague “approved” statement covering every role.

### Step 7 — Return the decision log

The engineering schema now accepts and reloads role-specific decisions. Kajal may
return a Markdown document or spreadsheet using the block below. Aswath/Codex
will copy the validated fields into `data/reviews/ingestion_decisions.json` and
rerun ingestion with `--review-decisions`. Do not manually change
`data/reviews/approvals.json`; that file is the separate final release gate.

Use one block per **item and reviewer role**:

```text
Review-task ID: REV-...
Candidate ID: C-...
Evidence ID: E-...
Source ID: ...
Profile/catalogue/rule ID when applicable: ...
Reviewed fingerprint or checksum: ...
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name: ...
Reviewer role: licence | content | clinical | india_localisation | product
Reviewer capacity/qualification: ...
Review date: YYYY-MM-DD
Reason: ...
Exact replacement wording: ... | not applicable
Source/supporting reference: ...
Week/day/stage change: ... | none
Condition change: ... | none
Country/jurisdiction change: ... | none
Permission granted for storage: yes | no | unresolved
Permission granted for display: yes | no | unresolved
Permission granted for embeddings: yes | no | unresolved
Follow-up owner: ... | none
```

Use these four decisions consistently:

| Decision | Meaning | What happens next |
|---|---|---|
| `accepted` | This reviewer accepts this unchanged item within their role and stated scope | Wait for the other required roles |
| `changes_requested` | The item can continue after a specific correction | Codex applies the change; affected roles review the new version again |
| `rejected` | The item must not be used in the proposed way | It remains blocked, is removed, or receives a different source/design |
| `needs_specialist_review` | This reviewer cannot safely decide it | Assign the named question to the correct specialist; keep it blocked |

Do not use a bare `approved` label because it hides which role and scope were actually accepted.
The loader rejects unknown task IDs, duplicate task/role entries, a decision tied
to another source/evidence/candidate, and any changed candidate checksum. A
`changes_requested` record is invalid unless it names an exact wording, timing,
condition or jurisdiction change.

### Step 8 — Codex applies and verifies the decisions

After Kajal returns the decision log, Codex will:

1. validate reviewer names, roles, dates and scopes;
2. apply accepted corrections to the governed source records;
3. update changed checksums/fingerprints;
4. invalidate decisions affected by a change;
5. regenerate the Stage 0 packet and Stage 1 queue;
6. rerun software and data-contract checks;
7. show which items are accepted, blocked or awaiting another role;
8. publish and embed only items that satisfy every required gate.

No review decision silently changes the user's medical facts. User-reported details and uploaded-document extractions have their own confirmation workflow in later stages.

## When to stop and ask instead of deciding

Choose `needs_specialist_review` and write the precise question when:

- the source and proposed wording appear to disagree;
- the source is old and the information may have changed;
- two official sources conflict;
- an India-specific programme or schedule may have changed;
- the week, trimester or postpartum-day range is unclear;
- a medical measurement uses an unclear convention;
- an allergy, condition, medicine or clinician instruction changes suitability;
- content could be interpreted as diagnosis, prescribing or medical clearance;
- urgent and non-urgent routing is unclear;
- source ownership or embedding permission is uncertain;
- the reviewer is being asked to decide outside their actual capacity.

The question should identify the item and uncertainty. Example:

```text
E-IN-ANC-VISITS: Does this dated programme description remain current for the
intended Indian demonstration, and how should regional variation be stated?
```

## Suggested review order and time

| Order | Work | Primary owner | Focused time |
|---:|---|---|---:|
| 1 | Confirm demo release slice and keep/defer comparison feature | Kajal + Aswath | 15–30 min |
| 2 | Product review of `PC00`, `P10`, `PP01` and matching evidence | Kajal | 45–75 min |
| 3 | Product review of remaining representative profiles and all 55 candidates | Kajal | 2–3 h |
| 4 | Review 34 practical catalogue items | Kajal | 45–75 min |
| 5 | Clinical review of the first release slice and relevant safety rules | Qualified reviewer | 2–4 h |
| 6 | India-localisation review of the first release slice | Named local-context reviewer | 1–2 h |
| 7 | Source/licence review of every source used by the first release slice | Authorised reviewer | 1–2 h |
| 8 | Apply changes, regenerate packets and re-check affected decisions | Codex + reviewers | Depends on changes |

The specialist-review work may run while Stage 2 database engineering is built. It must finish before the reviewed content is embedded, placed in live RAG or described as release-ready.

## Kajal's return checklist

Kajal should return:

- [ ] the exact demo release slice;
- [ ] a decision on keeping all 42 size comparisons hidden or verifying selected ones;
- [ ] product decisions for the representative profiles;
- [ ] product decisions for the 55 Stage 1 evidence candidates, or an explicit list of candidates deferred from the demo;
- [ ] decisions for the 34 practical catalogue items;
- [ ] the name and real capacity of every specialist reviewer;
- [ ] separate clinical, India-localisation and source/licence decision records for the release slice;
- [ ] exact replacement wording for every `changes_requested` item;
- [ ] a precise question and owner for every `needs_specialist_review` item;
- [ ] confirmation that no real patient data was used.

## Review is complete only when

- every released item has role-specific decisions tied to the current fingerprint/checksum;
- all required roles have accepted the unchanged released version;
- requested changes were applied and re-reviewed where necessary;
- source storage, display and embedding permissions are explicit;
- country, week/day and conditions are explicit;
- rejected and unresolved items remain blocked;
- the size-comparison feature remains hidden unless its enabled entries are fully verified;
- no product or team decision is mislabeled as clinical or licence approval;
- the regenerated gates confirm that only eligible material can be published.

Stage 2 table and security work can proceed while this review is happening. **Embeddings, live RAG and public release must use only the subset that completes this process.**
