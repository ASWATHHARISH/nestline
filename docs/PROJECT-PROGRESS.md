# Nestline progress: a plain-language guide for Kajal

Updated 10 September 2026. Read this first, then DEMO-WORK-LOG.md for the problems
we encountered and STAGE-0-REVIEW-PACKET.md for the actual draft content.

## What we are building

Nestline is intended to help someone through pregnancy and after birth. Compass
is its assistant. The planned product will organise confirmed reports, show
relevant weekly information, help answer questions with sources, and help prepare
plans and questions for care professionals. Urgent situations follow a separate
safety route. It is not intended to independently diagnose or prescribe.

Today we are building the information foundation. The chat, screens, database,
document reading and safety route are not implemented yet.

## Stages, pipeline steps and phases are different views

- **11 stages, numbered 0-10:** the work packages we use to track implementation.
- **14 pipeline steps, numbered 0-13:** how information moves through the system.
- **8 phases, numbered 0-7:** broader delivery milestones in Section 18 of the
  architecture; a phase can contain work from several stages.

We build and report progress by stage. We check the pipeline when connecting the
pieces. We have not completed all of Phase 0 or Phase 1 just because we worked on
Stage 0: their safety, scenario, fixture and evaluation requirements are broader.

## Stage 0: what each part does, and what exists now

Imagine a library. We need labelled shelves, trustworthy books, page references,
rules about who checks the books, and a way to stop unchecked material reaching
readers. Stage 0 prepares those things.

### 1. Label every place where weekly content will live

We created 63 separate records:

| Records | Count | Meaning |
|---|---:|---|
| PC00 | 1 | Pregnancy is possible; do not assume it is confirmed. |
| P01-P42 | 42 | One addressable record for each pregnancy week. |
| PP01-PP12 | 12 | One for each postpartum week. |
| PPD0-PPD7 | 8 | Extra records for early days after delivery. |

These are labelled containers, not 63 completed medical guides. Nine have populated
source-linked content ready for review; 54 remain empty shells. All 63 remain unpublished.
P42 is deliberately not a generic wellness page.

Files: data/weekly/weekly_content_manifest.jsonl and coverage_matrix.csv.
The checker confirms that both files agree and no record is missing.

### 2. Keep a register of information sources

The register has 29 entries, including selected OWH, NHM, standard NHS and Better
Health Channel sources.
For each we record who published it, the URL, country, reuse status, check date,
version, and what we may not conclude from it. A check date can mean a failed
access attempt; it does not mean the source was approved.

The original A.D.A.M., NHS Best Start and Pregnancy Birth and Baby candidates are
excluded. NIN is now excluded too because its product-reuse permission was not
established. Official hosting is not permission to ingest everything on a site.

NHM supplies Indian material. The other selected pages retain their original US,
UK or Australian source labels. An explicit proposed India adoption record states
what is being reused and requires a real review before publication. We do not
import foreign emergency numbers, clinic schedules or service entitlements.

The two Better Health Channel passages may only appear as unchanged, attributed
short quotations. The code excludes them from the AI-retrieval subset. Their
source was reviewed in 2012, which is clearly flagged for the content reviewer.
NHM CHO material is for free distribution; this is not a commercial launch licence.

Files: data/guidelines/source_registry.csv and source_audit.jsonl.

### 3. Save the exact small pieces we intend to use

There are 13 local excerpt snapshots and 28 evidence records. Each evidence
record identifies a source, a heading or paragraph location, the exact selected
words, the time range they support, and the country label.

A **checksum** is like a fingerprint of a file. If the saved excerpt changes,
the checker notices. It also checks the actual words and location, not just the
fingerprint. This helps prevent accidental edits from quietly changing evidence.
It does not prove that a publisher or doctor approved our interpretation.

Files: data/guidelines/snapshots/ and section_manifest.jsonl.
These snapshots contain selected excerpts, not entire downloaded websites.

### 4. Write small reusable pieces of guidance

We created 28 draft fragments. A fragment contains one small claim or action
and points back to its evidence. Stable guidance can be used in several weeks;
we do not rewrite it to pretend something medically new happens every week.

For example, a general pregnancy food-hygiene fragment can be linked from P09,
P10, P24 and P36. An exact P24 developmental fragment cannot be used for P10.

Some fragments have conditions. Postpartum support taken from a page about
professional care for depression is not presented as universal advice for every
new mother. Those conditions must remain attached throughout the future system.

File: data/guidelines/guidance_fragments.jsonl.

### 5. Assemble the nine representative review drafts

| Profile | What the draft now contains | Review focus |
|---|---|---|
| PC00 | Test instructions and asking a local health worker about testing | Do not assume pregnancy is confirmed. |
| P01 | Dating explanation plus stable food, rest, wellbeing and preparation cards | Week 1 must not imply conception has happened. |
| P09 | Its own exact-week quotation, first-trimester changes and general domain cards | Check older source currency and preserve quotation-only use. |
| P10 | Its own exact-week quotation and applicable general cards | Never substitute the P09 passage or treat approximate size as a scan result. |
| P24 | Week-24 development and stable food, rest, wellbeing and preparation | General education, not an individual fetal assessment. |
| P36 | Week-36 development and birth preparation | No prediction of delivery timing or permission to exercise. |
| PP01 | Rest, practical help, general wellbeing and conditional nutrition/activity cards | Feeding and delivery conditions must be confirmed. |
| PP06 | Local day-42 follow-up, ongoing support and fertility education | No claim of full recovery at six weeks; do not wait with symptoms. |
| PP12 | Ongoing support, practical help, fertility education and conditional cards | No invented week-12 milestone or assumption of depression. |

All nine are **proposed Indian drafts**, not approved Indian health content. Every
cross-country adoption has its own review requirement. Older US-only conditional
fragments are retained as draft source work but are not assembled into these profiles.

Empty slots now have an explicit explanation in `slot_notes`, visible in the
review packet. For example, PC00 focuses on testing rather than inventing a
pregnancy routine. We do not add symptom reassurance simply to fill a box.
Conditional breastfeeding or delivery-specific cards remain unavailable when the
condition is unknown. The current selector conservatively withholds a complete
profile if any of its required fragments is filtered out; later UI work must show
eligible cards and unavailable states without inventing content.

There are three different checks:

1. **Authoring:** are the records and citations internally consistent?
2. **Review ready:** do the nine profiles have concrete domain cards, sourced
   heroes and reasons for empty slots? This now passes.
3. **Release:** have actual named reviews happened and the nine profiles been
   published? This still fails deliberately because those reviews are pending.

### 6. Stop unfinished content from being shown

Records move through these states:

```text
draft -> reviewed -> published -> superseded
```

Draft means work in progress. Reviewed means an actual named review happened.
Published means it passed the required checks and may be selected. Superseded
means an older version remains in history but is no longer selected.

Sources use candidate/approved_for_capstone/excluded/superseded states. Evidence
must be published before dependent fragments; fragments must be published before
their complete profile can be published. The validator checks these dependencies.
The current files are edited locally; there is no authenticated reviewer UI or
database state-transition service yet.

Changing reviewed content requires a new version and renewed review. Do not edit
approved text while retaining the old reviewer record. In a later storage stage,
versioned review history must be enforced by the write service.

The current checker also rejects profiles that still list publication blockers.
Nobody's name is pre-filled as a reviewer. Software checks cannot authenticate a
person's review or replace clinical expertise.

### 7. Keep uncertain timing uncertain

If someone says "three months", our small selection contract represents weeks
9-13. It does not secretly choose week 10. Only information supported across the
whole range is eligible; no exact-week hero is selected.

Month nine is treated conservatively as weeks 36-42 within our representable
scope, because the architecture says 36-40+. This is a filtering convention,
not a calculation of someone's due date. The full journey resolver is Stage 3.

Day overlays and week records stay separate. Stage 3 must decide the delivery-day
boundary explicitly; Stage 0 does not silently convert a day into a week.

File: app/services/content_selection.py.

### 8. Check the system deliberately with bad examples

There are now 47 software tests. Examples include a made-up citation, the wrong
week, a changed source file, a foreign source requested for India, an unreviewed
profile marked published, and missing information treated as clearance.

These tests pass locally. They are not 47 conversations with an AI model. The
planned 45 development and 15 held-out product scenarios have not been run.

### 9. What the code files mean

| File | Plain-language job |
|---|---|
| app/schemas/content.py | Defines the form each kind of record must follow. |
| app/services/content_validation.py | Checks that records and their links agree. |
| app/services/source_snapshots.py | Checks the actual saved source excerpt files. |
| app/services/content_selection.py | Demonstrates published-only selection with time/country/condition filters. |
| scripts/validate_content.py | Runs the checks from a terminal and reports errors. |
| scripts/export_content_schema.py | Generates the editor-friendly form definition from the Python definition. |
| scripts/export_review_packet.py | Turns the current dataset into a readable review worksheet. |
| tests/ | Deliberately tries valid and invalid examples. |

Comments explain the non-obvious decisions: uncertain weeks, country boundaries,
source permission, conditional advice and publication gates. We avoid comments
that merely repeat obvious Python operations. There are no AI-provider calls in
these files and no new runtime dependency was needed for this pass.

## What is done under each remaining stage

| Stage | Planned result in simple words | Actual status today |
|---|---|---|
| 1: Ingestion | Read approved documents repeatedly without duplicates; preserve their versions and passages. | Manual selected-excerpt preparation exists. Automated ingestion, OCR and embeddings are not built. |
| 2: Storage | Save information securely and isolate each user. | Local files only. Supabase, tables, authentication and RLS are not built. |
| 3: Onboarding | Collect details and resolve the correct journey time. | Month-range selection contract exists; onboarding and full date resolver are not built. |
| 4: Personal documents | Read reports, propose facts and ask for confirmation. | Fictional story and eight-document inventory exist. Actual document fixtures and extraction are not built. |
| 5: Retrieval | Find exact personal facts and relevant public evidence. | Stage 0 filters have tests. SQL/vector/graph retrieval is not built. |
| 6: Safety | Recognise concerning requests before ordinary answering. | Source candidate identified; no reviewed rule set or runtime safety gate yet. |
| 7: Agents | Coordinate the relevant specialist helpers. | Architecture only; no orchestrator or working agents yet. |
| 8: Validation | Check an assistant's draft for support, conflicts and safety. | Dataset integrity checks exist. Generated-answer verification is not built. |
| 9: Experience | Provide the usable screens, chat and weekly view. | VS Code tooling exists, but product screens are not built. |
| 10: Saved plans | Save confirmed changes and mark affected plans stale. | Expected behaviour documented; persistence and updates are not built. |

## Pipeline steps: how these connect later

0. Define content and sources: Stage 0 work described above.
1. Extract and review public knowledge: selected draft excerpts only so far.
2. Store the published corpus: not built.
3. Resolve the user's journey: only a small range-selection contract exists.
4. Read optional personal documents: not built.
5. Check workspace access and assemble context: not built.
6. Run the urgent-situation gate: not built.
7. Choose the helper/workflow: not built.
8. Retrieve evidence with SQL/text/vector/graph: not built.
9. Generate a structured draft: not built.
10. Validate the answer: dataset checks are not this runtime step.
11. Show the result: not built.
12. Ask what the user wants to save: not built.
13. Persist confirmed changes and update dependencies: not built.

## Broader phases: what we can honestly claim

| Phase | Meaning | Current position |
|---|---|---|
| 0 | Freeze scope, scenarios and safety boundaries | Architecture and owner decisions exist; full scenario/safety lock not signed off. |
| 1 | Prepare evidence, fictional data and evaluation contracts | Representative content prepared; named review, document fixtures and eval contract incomplete. |
| 2 | Build app scaffold and deterministic core | Only data tooling and limited selection contracts exist. |
| 3 | Connect retrieval and document updates | Not implemented. |
| 4 | Connect safety and agents | Not implemented. |
| 5 | Connect graph dependencies and human responsibility | Not implemented. |
| 6 | Measure and improve with evaluations | Engineering tests exist; AI baseline/holdout comparison not implemented. |
| 7 | Package the submission | Technical notes exist; finished UI/video/reset demonstration not implemented. |

## What Kajal can do with this now

Read STAGE-0-REVIEW-PACKET.md and mark which cards need different wording or more
content. Review what an empty/unavailable card should look like. Decide which
claims belong in the initial demo, coordinate content review and India applicability,
and prepare expected behaviours for the later AI evaluations. Codex handles the
technical implementation; Kajal is not being assigned backend coding.

Do not mark the whole Stage 0 complete yet. Its engineering foundation is tested,
but actual named content/localisation review and publication of the representative
profiles are still open. The content packet is prepared; the team must review it.
This remaining sign-off belongs to Stage 0, not an upcoming stage. Product acceptance is a separate real action, not a flag
we should toggle just to make a test green.
