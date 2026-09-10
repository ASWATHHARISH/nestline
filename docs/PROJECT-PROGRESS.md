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

These are labelled containers, not 63 completed medical guides. Nine have initial
source-linked draft content; 54 remain empty shells. All 63 remain unpublished.
P42 is deliberately not a generic wellness page.

Files: data/weekly/weekly_content_manifest.jsonl and coverage_matrix.csv.
The checker confirms that both files agree and no record is missing.

### 2. Keep a register of information sources

The register has 21 entries: the original 16 candidates and five new OWH sources.
For each we record who published it, the URL, country, reuse status, check date,
version, and what we may not conclude from it. A check date can mean a failed
access attempt; it does not mean the source was approved.

Four sources are excluded from ingestion: the A.D.A.M. article, the two NHS Best
Start entries, and the Pregnancy Birth and Baby index. WHO/NIN/NHM/CDC entries
remain candidates with explicit pending work. Five OWH sources permit the
selected text reuse, but have not received our content review.

Files: data/guidelines/source_registry.csv and source_audit.jsonl.

### 3. Save the exact small pieces we intend to use

There are five local excerpt snapshots and eleven evidence records. Each evidence
record identifies a source, a heading or paragraph location, the exact selected
words, the time range they support, and the country label.

A **checksum** is like a fingerprint of a file. If the saved excerpt changes,
the checker notices. It also checks the actual words and location, not just the
fingerprint. This helps prevent accidental edits from quietly changing evidence.
It does not prove that a publisher or doctor approved our interpretation.

Files: data/guidelines/snapshots/ and section_manifest.jsonl.
These snapshots contain selected excerpts, not entire downloaded websites.

### 4. Write small reusable pieces of guidance

We created eleven draft fragments. A fragment contains one small claim or action
and points back to its evidence. Stable guidance can be used in several weeks;
we do not rewrite it to pretend something medically new happens every week.

For example, a general pregnancy food-hygiene fragment can be linked from P09,
P10, P24 and P36. An exact P24 developmental fragment cannot be used for P10.

Some fragments have conditions. Postpartum support taken from a page about
professional care for depression is not presented as universal advice for every
new mother. Those conditions must remain attached throughout the future system.

File: data/guidelines/guidance_fragments.jsonl.

### 5. Assemble the nine representative review drafts

| Profile | Present draft material | Important remaining work |
|---|---|---|
| PC00 | Following home-test instructions | Fuller verification/next-step content and review. |
| P01 | How gestational dating is counted | Review early-week wording without implying conception or confirmed pregnancy. |
| P09 | Trimester-wide changes, dating, food hygiene, exercise consultation | Permitted exact-week development evidence and review. |
| P10 | The same applicable general fragments, in its own record | Same exact-week gap; never relabel P09 evidence as P10 evidence. |
| P24 | Selected 24-week development, food hygiene, exercise consultation | Broader cards and review. |
| P36 | Selected 36-week development, food hygiene, exercise consultation | Broader preparation and review. |
| PP01 | Conditional early-home rest and support alongside professional care | Broader first-week recovery and day-overlay review. |
| PP06 | A question about resuming activity and conditional support | Local follow-up context and broader recovery content. |
| PP12 | Conditional ongoing support alongside professional care | Broader recovery content; no invented week-12 milestone. |

Every row is still a **draft**. US reference jurisdiction is deliberately retained
on these nine drafts; the product's intended Indian context still needs suitable
content and review. The other shells retain the intended IN context.

An empty nutrition or symptom card means we have no reviewed content in that
slot. It does not mean there is nothing the user needs to know. We must not ask
a language model to fill those gaps from memory.

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

There are now 41 software tests. Examples include a made-up citation, the wrong
week, a changed source file, a foreign source requested for India, an unreviewed
profile marked published, and missing information treated as clearance.

These tests pass locally. They are not 41 conversations with an AI model. The
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
| 1 | Prepare evidence, fictional data and evaluation contracts | Source/data foundation underway; content review, document fixtures and eval contract incomplete. |
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
but the requirement to deeply source, review and publish the representative
profiles is still open. Product acceptance is a separate real action, not a flag
we should toggle just to make a test green.
