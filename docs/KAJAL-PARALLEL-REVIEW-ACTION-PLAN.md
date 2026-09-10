# Kajal's parallel content, product and evaluation action plan

**Prepared:** 10 September 2026

**Purpose:** Complete the non-engineering work that can run while Stage 2 is being built.

**Boundary:** This document contains no account, API-key, database or deployment-access work.

## 1. Current position

Nestline's Stage 0 authoring foundation and Stage 1 ingestion machinery are built.
The content is still a governed draft:

- 63 journey records exist: possible pregnancy, pregnancy weeks 1–42,
  postpartum weeks 1–12 and eight day 0–7 overlays;
- nine representative journey profiles and all eight day overlays contain the
  current demonstration content;
- 55 unique public-source passages have been located and matched to their exact
  source anchors;
- 34 practical catalogue items exist: 12 nutrition, 6 movement, 6 wellbeing
  and 10 follow-up items;
- 42 size-comparison proposals exist but remain hidden and unverified;
- 55 Stage 1 review tasks are waiting;
- no passage has been embedded or published.

Engineering can continue. Only approved content may later enter embeddings or
live RAG, and every required review for the released slice must finish before a
public demonstration is called release-ready.

## 2. Kajal's immediate product/content review

**Estimated focused time: 2–3 hours**

Review the actual material in `docs/STAGE-0-REVIEW-PACKET.md` and
`docs/STAGE-1-REVIEW-QUEUE.md`. For every decision, use the template in Section 8.

### 2.1 Review the representative weekly slice

- [ ] `PC00`: possible pregnancy — never imply that pregnancy is confirmed.
- [ ] `P01`: timing education only — no incorrect birth-planning content.
- [ ] `P09` and `P10`: neighbouring weeks must remain visibly distinct.
- [ ] `P24`: check the mid-pregnancy dashboard story and card priorities.
- [ ] `P36`: check the later-pregnancy dashboard story and preparation wording.
- [ ] `PP01`: check the first postpartum week and its day overlays.
- [ ] `PP06`: check later postpartum follow-up behavior.
- [ ] `PP12`: check the end-of-scope transition.
- [ ] `PPD0–PPD7`: check all eight day overlays, including empty and conditional states.

For each profile, review:

- the hero/title and plain-language meaning;
- which cards appear and their order;
- whether a card is exact-week content or broader guidance;
- what happens when a condition is unknown, false or conflicting;
- source and country labels shown to the user;
- wording that asks the user to contact or prepare questions for a professional;
- the empty state when a profile or card remains unpublished.

Do not fill the other 46 hidden records with invented weekly advice. Their expansion
is a later content workstream. For the award demonstration, depth and traceability
in the representative slice matter more than superficial text on every week.

### 2.2 Review dashboard content requirements

- [ ] Confirm the top KPI order: journey week/stage, reviewed general development
  measurement when available, next appointment and other genuinely useful status.
- [ ] Confirm the main content areas: nutrition, movement and mental wellbeing.
- [ ] Confirm separate preparation, symptoms, consider/avoid and questions-for-care-team areas.
- [ ] Confirm that a user's scan measurement is never replaced by a general weekly measurement.
- [ ] Confirm that missing allergies, restrictions, symptoms or movement instructions
  produce “we need more information,” rather than implied permission.
- [ ] Confirm that citations and country/applicability information can be opened from the UI.
- [ ] Confirm language for unpublished weeks and temporarily unavailable cards.

This work defines later UI behavior. It does not require building the dashboard now.

### 2.3 Review practical catalogue items

- [ ] 12 nutrition items: names, dietary labels, allergen fields, handling notes
  and qualitative roles. Do not add calorie targets, therapeutic diets or invented portions.
- [ ] 6 movement items: eligibility conditions, progression wording, stop-rule links
  and no inferred medical clearance.
- [ ] 6 wellbeing items: optional and respectful language, consent, and an appropriate
  route to professional help. These items are not therapy.
- [ ] 10 follow-up items: scheduling/programme wording, local relevance and questions
  the user may prepare. Do not convert general programme information into a personal appointment.

For every item, choose `accept`, `change`, `reject` or `needs_specialist_review`.

### 2.4 Decide the comparison feature

- [ ] Choose one product decision:
  - keep all 42 comparisons hidden for the capstone; or
  - verify every enabled measurement, comparison-object dimension and wording with
    an identified source and the required reviewers.

**Recommended for the time-bound build:** keep comparisons hidden and use reviewed
development text or measurements without an object comparison. Do not enable a
comparison merely because an image or editorial label exists.

## 3. Stage 1 passage review

**Estimated focused time for Kajal's product/content pass: 1.5–2.5 hours**

Use `docs/STAGE-1-REVIEW-QUEUE.md`. There are 55 candidate passages. Kajal's pass should check:

- [ ] the source passage and proposed wording mean the same thing;
- [ ] the dashboard/content slot is sensible;
- [ ] the stage and week/day range match the intended product experience;
- [ ] conditional content asks for the correct missing information;
- [ ] the proposed profile and catalogue links are useful;
- [ ] the wording is understandable and does not sound diagnostic or prescriptive;
- [ ] passages with country-specific schedules are visibly country-specific;
- [ ] duplicate wording is reused rather than pretending to be a new medical fact;
- [ ] uncertain decisions are labelled `needs_specialist_review`.

Kajal's review is a product/content review. It must not be recorded as clinical,
India-localisation or licence approval unless she genuinely holds that role and is
qualified to make that exact decision.

## 4. Reviews Kajal and Aswath must coordinate

These reviews require the appropriate people. They may happen at the same time as
Stage 2 engineering.

### 4.1 Qualified maternal-health review

**Estimated reviewer time: 2–4 hours for the released demonstration slice**

- [ ] Check exact wording, omitted context and applicability conditions.
- [ ] Review movement, postpartum and safety-related content.
- [ ] Decide whether the older BHC week 9/week 10 material remains suitable.
- [ ] Review NHM programme interpretation and current Indian maternal-health context.
- [ ] Review ambiguous and urgent symptom examples before Stage 6 goes live.
- [ ] Approve, request changes or reject each passage intended for the released slice.

### 4.2 India-localisation review

**Estimated reviewer time: 1–2 hours**

- [ ] Check India-specific programme names, timing and current availability.
- [ ] Check that foreign appointment schedules and emergency contacts are not presented
  as Indian instructions.
- [ ] Approve locally appropriate help/escalation wording for the demonstration.
- [ ] Record unresolved state or regional variation instead of guessing one universal answer.

### 4.3 Source and licence review

**Estimated reviewer time: 1–2 hours**

- [ ] Decide which passages may be quoted and displayed.
- [ ] Decide which passages may be stored in the project/database.
- [ ] Decide which passages may be converted into embeddings.
- [ ] Check required attribution and links.
- [ ] Resolve the BHC and NHM reuse/storage questions.
- [ ] Keep link-only or fixed-quotation sources within their stated limits.

## 5. Evaluation work Kajal can prepare now

**Estimated focused time: 1.5–2 hours**

Preparing expected outcomes now prevents later prompt tuning from changing what
“correct” means.

- [ ] Review the existing deterministic cases and remove trivial duplicates.
- [ ] Mark each case as critical, high, medium or exploratory.
- [ ] Write the expected user-visible result, without writing an ideal model answer
  that encourages word matching.
- [ ] Ensure the cases cover wrong-week retrieval, allergy/restriction exclusion,
  unknown conditions, conflicting records, missing evidence, citations, urgent routing
  and refusal to prescribe or diagnose.
- [ ] Define at least 45 development scenarios and 15 separately controlled holdout scenarios.
- [ ] Keep holdout answers away from prompt-development work.
- [ ] Define the three demonstration stories and their visible success criteria.
- [ ] Record one anticipated failure example for each story so the demo can show honest improvement.

The three demonstration stories are:

1. **Week-aware plan:** resolve `P10`, confirm a fictional allergy and restriction,
   generate a sourced plan, edit it and save it.
2. **Record-to-action continuity:** upload a fictional document, confirm extracted
   facts, create an appointment question and show the affected plan becoming stale.
3. **Safety and human handoff:** enter a curated urgent scenario, bypass normal
   generation, obtain consent for a simulated review packet and show evaluation evidence.

These are evaluation specifications. They are not claims that an AI model or the
finished application has already passed them.

## 6. UI preparation Kajal can do without code

**Estimated focused time: 1–2 hours**

- [ ] Draw the dashboard hierarchy and card order for desktop and a narrow screen.
- [ ] Define visible states: loading, no data, needs information, unavailable,
  conflicting, stale, error and ready.
- [ ] Define the citation/evidence drawer fields.
- [ ] Define how general public guidance, user-reported facts and document-confirmed
  facts look different.
- [ ] Define how users correct their week, allergy, history and next appointment.
- [ ] Define the chatbot entry point without hiding the dashboard plan.
- [ ] Define edit, save and discard behavior for plans.
- [ ] Define the simulated-review wording so it never impersonates a real clinician.
- [ ] Keep the public demo clearly fictional and prohibit real medical uploads.

Figma or sketches are acceptable. Each screen decision should reference the relevant
profile, catalogue item or evaluation scenario rather than decorative content.

## 7. Priority and suggested parallel schedule

| Priority | Work | Owner | Estimate | Blocks |
|---:|---|---|---:|---|
| P0 | Representative-profile product review | Kajal | 1–1.5 h | Released weekly slice |
| P0 | Stage 1 passage product/content pass | Kajal | 1.5–2.5 h | Final wording and linkage |
| P0 | Clinical review of released slice and safety material | Qualified reviewer | 2–4 h | Embeddings, live RAG, safety release |
| P0 | India-localisation review | Qualified/local reviewer | 1–2 h | Local release wording |
| P0 | Source/licence review | Appropriate reviewer | 1–2 h | Storage, embeddings and display |
| P1 | Practical catalogue review | Kajal | 45–75 min | Plan recommendations |
| P1 | Evaluation scenario preparation | Kajal | 1.5–2 h | Later RAG/agent measurement |
| P1 | Dashboard state and hierarchy sketches | Kajal | 1–2 h | Stage 9 implementation |
| P2 | Comparison decision | Kajal + reviewers if enabled | 15 min to defer; substantially longer to verify | Optional comparison feature |

The reviewer estimates describe focused review time and exclude the time needed to
find and schedule qualified reviewers.

## 8. Decision format

Kajal and each reviewer can return decisions in a document, spreadsheet or structured
message using this exact shape:

```text
Item ID:
Decision: accept | change | reject | needs_specialist_review
Reviewer name:
Reviewer role/capacity:
Review date:
Reason:
Exact replacement wording (only when changing):
Source or supporting reference (when relevant):
Conditions/week/country changes:
```

Do not write `approved` when the person reviewed only product layout or readability.
Use their real review capacity. Content edits made after approval require the changed
fingerprint to be reviewed again.

## 9. Definition of finished parallel work

This parallel work is complete when:

- [ ] Kajal has returned explicit decisions for the representative profiles,
  practical catalogues and the Stage 1 passages needed by the demo;
- [ ] the comparison feature is explicitly deferred or fully supported;
- [ ] the qualified reviewers have returned traceable decisions for the released slice;
- [ ] every requested wording change includes exact replacement wording;
- [ ] the three demo stories and their success criteria are agreed;
- [ ] dashboard states and provenance labels are defined;
- [ ] no team review is mislabeled as clinical or licence approval;
- [ ] unresolved items remain visibly blocked instead of being silently accepted.

After these decisions return, Codex can apply accepted corrections, regenerate the
review packets, run all gates, create embeddings only for approved passages and
publish a versioned corpus when the release requirements are satisfied.
