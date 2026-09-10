# Nestline: what exists, in plain language

Updated 11 September 2026 after the Stage 1 correction pass and Stage 2 deployment. This is the current
status; earlier entries in the demo log are history.

## What the project is

Nestline is meant to help a woman keep track of pregnancy and recovery after birth.
Compass is the assistant we will build inside it. The finished product should
organise her reports, answer supported questions, help prepare suitable plans and
questions for her care team, and direct concerning symptoms to medical help.
We are building by stages. Today the working code includes the information
foundation, governed ingestion, the isolated Supabase storage foundation and a
draft-only Streamlit reviewer preview. There is no working chat, agent team or
patient-facing safety system yet. Private-report extraction remains Stage 4.

## Stage 0, explained as a library

Before opening a library, we need shelves, books we may legally use, page references
and someone qualified to check the material. Stage 0 builds that foundation.

### 1. The shelves: 63 journey records

| Record | Meaning | Actual content |
|---|---|---|
| PC00 | Pregnancy might be possible | Test instructions and asking about local testing support. |
| P01 | Pregnancy week 1 | Pregnancy timing only. Weeks count from the last normal period; this does not establish conception. |
| P09, P10 | Pregnancy weeks 9 and 10 | Separate development quotations and sourced general cards. Older source currency needs review. |
| P24, P36 | Pregnancy weeks 24 and 36 | Exact-week development, general food/movement/wellbeing and care-preparation cards. |
| PP01, PP06, PP12 | Weeks after birth | Recovery/support cards, conditional activity and feeding content, and relevant follow-up questions. |
| PPD0-PPD7 | Extra information for birth day through day 7 | All eight have sourced rest/help cards; days 0, 1, 3 and 7 also have applicable contact information. |
| Remaining 46 records | Other pregnancy/postpartum weeks | Hidden shells with explicit reasons; no fabricated weekly advice. |

Nine representative profiles and eight day overlays are populated drafts. All 63
are unpublished. P42 stays hidden until exact local wording has been reviewed.
The same rest advice can appear on several days: we do not pretend that every day
has a unique medical event.

Birth is day 0. Our explicit display convention puts days 0-7 in PP01, days 8-14
in PP02 and days 36-42 in PP06. This is a product timing convention, not a clinical
appointment schedule. Stage 3 still needs the full date resolver.

### 2. The books: a source register

There are 31 registered sources. Fourteen have documented reuse research and
active excerpt snapshots; twelve are used in assembled draft profiles/catalogues.
Zero sources have actual human approval, and zero evidence records are published.
A registered link is not the same thing as a usable or approved book.

We retain each publisher's original country. Proposed Indian use has a separate
localisation record. Foreign clinic schedules and emergency numbers cannot silently
become Indian instructions. Five excluded sources remain excluded. CDC's warning
list is a link-only clinical reference because third-party reuse needs clarification.

### 3. The page references: 55 unique evidence records

Each record saves a selected supporting passage, its source and location, and the
time range it supports. A file fingerprint detects local changes. It cannot prove
that a doctor approved the passage or that an interpretation is medically correct.

The follow-up correction illustrates why this matters. The old evidence said only
“42nd Day”, while our wording said more. It now contains the complete programme
schedule for both home and facility births. We also restored the full conditional
exercise paragraph and removed the unsupported extra clause in the feeding card.

### 4. The small cards: 56 draft fragments

A fragment is a small reusable piece of guidance with evidence attached. Every
fragment now has my recorded source-to-wording assessment. These are explicitly
labelled Codex assessments; they are not clinical or human approvals. Changing the
wording, conditions or evidence makes the assessment stale and fails the checks.

We also expanded older clipped anchors, including pregnancy timing, the professional-
care context for support, and the breastfeeding/fertility sentence.

### 5. Showing the right card

The software checks each card separately. Suppose feeding advice needs confirmed
breastfeeding, but we do not know whether she is breastfeeding. That card says
“needs information”; other eligible cards and the week page remain available.
If she confirms the condition does not apply, that card becomes “not applicable”.
Unpublished content stays unavailable regardless of the conditions.

The shared condition dictionary prevents spelling mistakes from creating new rules.
Unknown does not mean no restriction. Conflicting delivery details need clarification.
A month-only description remains a range: “three months” means weeks 9-13 for this
filtering contract, never an invented exact week.

### 6. The option lists for later plans

| Catalogue | Rows | What exists and what it does not prove |
|---|---:|---|
| Food | 12 | Ingredient examples, qualitative nutrient roles, allergen/restriction fields and food-handling notes. No calorie plan, portions or therapeutic diet. |
| Movement | 6 | Pregnancy and postpartum options/questions, suitability conditions, progression notes and stop-rule references. No automatic week-six clearance. |
| Wellbeing | 6 | Optional actions such as naming a feeling, choosing something enjoyable, resting or asking for help. Consent and professional-help routes are explicit. These are not therapy. |
| Follow-up | 10 | Indian programme registration/check/contact drafts, including PMSMA information. Local current clinical scheduling still needs reconciliation. |
| Comparisons | 42 | Kajal's editorial proposals and stable image keys. Measurements and object dimensions are unverified; all remain hidden. Artwork is deferred by her review. |

“Self-love” in the review referred to gentle wellbeing support like these optional
actions. It did not mean relationship dating. “Pregnancy dating” means pregnancy
timing, so the team guide uses that clearer phrase.

### 7. Fictional documents for the future document reader

Eight clearly marked fictional PDFs now exist, with matching text and expected
extraction files. They follow Maya from pregnancy to postpartum. Examples include
a recorded allergy, a lab report without interpretation, an explicitly invented
non-medicine instruction, a movement restriction, a follow-up and delivery details.
Each expected fact points to its page, text line and rectangle on the page.

One document contains a deliberately malicious instruction. Its expected behaviour
is to treat that sentence as document text, never an instruction to the application.
Another conflicts with an older movement instruction. Later code must retain both
sources, ask for confirmation and mark affected plans stale. Those future state
changes are specified, not implemented or proven by having the fixtures.

All eight PDFs were rendered and visually checked. This tests the demo artifacts;
it does not mean OCR or AI extraction works.

### 8. Checks, not an AI evaluation result

There are 119 passing unit tests covering the foundation, corrected Stage 1
ingestion tests. They try valid and invalid data: broken citations, wrong weeks,
missing conditions, altered source files, parser/OCR failures, duplicate units and
false publication states.
There are also 64 visible software cases in the future evaluation-contract file.
The local runner checks existing deterministic functions and fixture integrity.
**Neither count means conversations tested with Grok, GPT or any other AI model.**

Kajal's review explicitly requested the future evaluation contract. It is prepared
now so later implementations have agreed examples to test against. These 64 cases
are not a sealed holdout and do not replace the planned independent AI benchmark.

The safety contract contains draft English matching examples. Urgent matches take
priority. A missing match never proves a symptom is safe or authorises generation.
The live entry point refuses the draft rules. This is not a clinically validated
triage system or the finished Stage 6 safety gate.

### 9. The release lock

Authoring checks that data and source links agree. Review-readiness additionally
checks populated cards, explained gaps, catalogues and assessment freshness. Both
pass. Release checks require actual reviews and published dependencies, and still
fail. Five review roles are required: licence, content, clinical, India localisation
and product. Kajal's 27 content decisions and 27 product decisions for
`PC00`/`P10`/`PP01` are now recorded in the checksum-bound Stage 1 ledger. The
release-level approval file remains empty because the other required roles and
the rest of the release have not been reviewed.

This is not just paperwork left over. An appropriate reviewer must resolve older
source currency, current Indian care interpretation, exact medical wording and
safety behaviour. Comparisons still lack verified measurements/object dimensions.
Their safe fallback is sourced development text without a size comparison.

## Where every remaining stage stands

| Stage | What we will build | Status today |
|---|---|---|
| 0: Content foundation | Sources, cards, rules and review controls | Corrected draft foundation; rounder comparison proposals applied and hidden; product/content accepted for the three-profile slice. Specialist and full-release reviews remain blocked. |
| 1: Ingestion | Repeatedly read approved documents with versions and provenance | Seven independent-review corrections complete; tracked 14-source audit found all 55 anchors and verified TLS for every source. The governed ledger binds 54 Kajal decisions to 27 current tasks. No embeddings/corpus are published. |
| 2: Storage | Keep each user's information secure and separate | Supabase foundation deployed: 28 RLS-enabled tables, private file bucket, pgvector, release provenance, atomic journey versions and workspace lifecycle. Two-user isolation and lifecycle transactions passed and rolled back. |
| 3: Onboarding | Confirm details and work out journey timing | Month/day selection contracts exist; onboarding and date resolution are not built. |
| 4: Personal documents | Propose extracted facts and request confirmation | Eight input/truth fixtures exist; the extraction and confirmation pipeline is not built. |
| 5: Retrieval | Find the right evidence and personal facts | Draft/published/time/country/condition filters exist; SQL/vector/graph retrieval is not built. |
| 6: Safety | Handle urgent and uncertain requests before normal answers | Draft rule specification and offline cases exist; reviewed live gate is not built. |
| 7: Agents | Coordinate specialist helpers | Architecture only. |
| 8: Answer validation | Reject unsupported or conflicting generated answers | Data-integrity checks exist; generated-answer verification is not built. |
| 9: Experience | Build the home page, chat, plans and review screens | Draft-only PC00/P10/PP01 reviewer preview exists; patient dashboard, onboarding, chat and plans are not built. |
| 10: State updates | Save confirmed changes and refresh affected plans | Expected behaviours and plan schema exist; persistence/dependency updates are not built. |

## Stages, pipeline and phases

We track implementation through 11 stages, numbered 0-10. The 14 pipeline steps
(numbered 0-13) describe how a request flows through the eventual system:
content -> extraction -> storage -> timing -> personal documents -> access/context
-> safety -> routing -> retrieval -> drafting -> validation -> display -> consent
-> confirmed updates. We have pieces of the first steps and offline contracts,
not a connected working pipeline.

The architecture also has eight broader phases. Phase 0 scope/scenario/safety
acceptance remains open. Phase 1 has draft evidence, fixtures and software contracts,
with clinical/content release still open. Phase 2 has limited deterministic helpers.
Stage 2 now supplies the persistent isolation foundation. Phases 3-5 integration/retrieval/agents/state work are not implemented. Phase 6 AI
measurement has not run. Phase 7 submission packaging is not complete.

## What Kajal can review now

Kajal's first product/content pass is recorded. Read
STAGE-1-PC00-P10-PP01-REVIEW-HANDOFF.md for the exact 27-task specialist queue and
the final visual gate. Clinical approval must come from an appropriately qualified
reviewer; India-localisation and licence decisions also need real named reviewers.
Codex handles implementation. Aswath coordinates access and reviewer availability.
We must not mark Stage 0 fully released until those real decisions and the release
checks are satisfied.
