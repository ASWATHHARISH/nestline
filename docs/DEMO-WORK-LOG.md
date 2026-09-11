# Demo work log: corrections, failures and recovery

## Current correction pass - 10 September 2026

Earlier claims of completion were too broad. Kajal found real problems: a day-42
statement with only a tiny supporting anchor, a missing activity condition in the
saved paragraph, an unsupported diet clause, poorly timed P01 preparation and empty
early-day overlays. Software consistency did not establish clinical correctness.

### What we changed

- Restored complete source passages and corrected wording. Also expanded timing,
  professional-care and fertility evidence where old fragments were too clipped.
- Limited P01 to pregnancy timing. Populated all eight early-postpartum overlays
  with sourced, reusable rest/help content and appropriate contact information.
- Changed selection to card-level states: missing details withhold the affected
  card rather than the whole week. Added a typed condition dictionary and conflict
  checks. Confirmed absence is required where a restriction must be absent.
- Added draft food, movement, wellbeing, follow-up and comparison catalogues.
  Food constraints reject known conflicts and ask about unfamiliar constraints.
  No fruit measurements or clinical approvals were invented to fill a table.
- Built eight fictional reports with matching extraction truth and provenance.
- Added per-fragment Codex assessments, stale-assessment checks and actual review
  roles bound to a content fingerprint. No human reviewer has approved the data.

### Failures encountered and how we recovered

1. **Old tests used loose condition names.** The new registry rejected fake keys
   such as clearance/restriction, and the exported schema was stale. Updated the
   fixtures to the real typed keys and regenerated the schema; did not loosen it.
2. **The old release test expected only nine errors.** The complete gate now checks
   eight day overlays, catalogues, role approvals and currency too. Updated the
   regression to assert specific missing obligations rather than hide new failures.
3. **A government-hosted page included a third-party warning list.** CDC credits
   AIM/ACOG, and the general federal reuse policy does not clear every third-party
   passage. Removed copied warning passages before committing; retain link-only
   references for clinical review. Licensed NHM excerpts support general escalation.
   No claim that NHM proves every CDC-specific threshold is made.
4. **Download/extraction tools were uneven.** Some official page downloads returned
   403/404. Recorded those failures; used readable official pages where available.
   The local pdftotext command was unavailable, so pypdf extracted NHM source text.
   We did not label a failed download as a verified full-file capture.
   The PIB web screenshot also missed its cache; downloading the official PDF
   and rendering pages 2 and 3 locally completed that visual source check.
5. **PDF rendering warned about the Symbol font.** Fixtures use ordinary Latin text;
   all eight rendered pages were inspected and showed no clipping/overlap or missing
   fixture text. The warning was logged, not taken as proof that rendering failed.
6. **Approval hashes could have invalidated themselves.** Hashing raw workflow
   statuses would change the fingerprint when a reviewer recorded approval. The
   fingerprint now binds content/source/conditions and ignores review/status fields;
   separate release checks still enforce those fields. A regression proves wording
   changes invalidate the fingerprint while recording a review does not.
7. **Current Indian programme descriptions differ from global contact guidance.**
   Documented NHM, June 2026 PMSMA and WHO contexts separately. A local clinical
   decision is still needed; we did not silently merge them into one schedule.

### What can be demonstrated now

In VS Code run the unit tests, authoring/review-readiness checks and the release
check. Open P01, a day overlay, a full source passage, the review packet and DOC-006.
Show the difference between evidence, a draft card, a recorded assessment and actual
publication. The draft release refusal is an honest control demonstration.

The current run passes 68 unit tests and 64 visible deterministic software cases.
These are not model or medical evaluations. OCR and real state-change behaviour
are not implemented. The machine-readable local report is STAGE-0-CHECK-RESULTS.json.

### Remaining work to disclose in a demo

Source currency, current Indian clinical interpretation, exact wording, actual
human approvals and publication are still open. Size-comparison measurements and
object dimensions are unverified; those cards remain hidden. Safety patterns need
clinical review and much broader validation before live use. Read
STAGE-0-CORRECTION-STATUS.md rather than describing the whole Stage 0 as released.

## Historical entries below

The following entries describe earlier passes. Their counts, missing-artifact
lists and whole-profile filtering behaviour are superseded by the correction pass
above; they are preserved to explain what changed and why.

# Nestline: what happened, what failed, and how we recovered

## Latest pass: preparing all nine profiles for review (10 September 2026)

**Current result:** 63 records; nine populated representative profiles; 29 source
entries; 13 saved selected-excerpt snapshots; 28 spans and 28 fragments. All 47
engineering tests pass. Authoring and review-readiness pass. Publication remains
blocked because no actual named content/localisation review has been recorded.
The earlier sections below describe the previous pass and its then-open gaps.

### What changed

We added distinct week-9 and week-10 development quotations; Indian food/rest,
birth-preparation and day-42 follow-up material; pregnancy wellbeing; and broader
postpartum support, fertility education and conditional nutrition/activity content.
The same stable guidance can appear in several weeks. We do not invent a new fact
for every week or describe week 12 as automatic recovery.

The readable review packet now shows actual card wording, required conditions,
original source country, proposed India use, permissions and reasons for empty
slots. Its dataset fingerprint identifies the exact content being reviewed.

### What failed and how we recovered

| Problem found | Recovery | What remains explicit |
|---|---|---|
| Original weekly sources did not establish dataset reuse permission | Found Better Health Channel's short-quotation route for weeks 9 and 10 | Two unchanged quotes only, attribution required, no embeddings; 2012 source currency needs review. |
| A foreign source could not honestly become Indian guidance by changing a label | Added explicit localisation proposals and a separate review requirement | Source country remains unchanged; no foreign schedules or entitlements imported. |
| PP12 had only conditional depression-related material | Added general months-after-birth support and practical-help evidence | No depression assumption or invented week-12 milestone. |
| General Indian nutrition candidate had restrictive reuse terms | Kept NIN excluded and selected small original NHM text passages | Older NHM doses, schedules and third-party pictures were not adopted. |
| PDF rendering attempt could not import PyMuPDF | Used the already available Poppler renderer and inspected the relevant pages | Full PDFs and rendered pages stay in ignored local raw storage. |
| Network sandbox blocked the official PDF download | Retried the same public downloads with authorized network access | Only selected attributed excerpts and original-document hashes enter Git. |
| The handoff described the wrong command as the expected failure | Named `--require-release` explicitly | Review-ready and release are separate checks. |

### Engineering changes worth demonstrating

- A foreign draft can carry a proposed India adaptation, but publishing it without
  that adaptation's named review fails.
- Quote-only material cannot be assigned embedding permission, rewritten, copied
  beyond its configured excerpt limit or selected without attribution metadata.
- Review readiness checks domain cards and explanations for empty slots; passing
  it never sets a published flag.
- The selection contract returns a separate model-retrievable subset and attributed
  quotation cards. The future ingestion and UI must preserve that boundary.
- `scripts/check_stage0.py` reruns checks and writes the actual outputs to
  `STAGE-0-CHECK-RESULTS.json`; its exit status still follows the release gate.

### Reproduce the current result

```powershell
.venv/Scripts/python.exe -m scripts.check_stage0
```

Expect engineering and review-ready checks to pass and the publication gate to
exit 1 until real reviews are recorded. This is an honest demonstration of the
publication safeguard, not a completed health assistant or clinical validation.

### Remaining Stage 0 sign-off

The team must review this exact packet's wording, claim support, permissions,
source currency, India applicability and empty/conditional cards. Record the
actual reviewer and corrections. Publish approved source/evidence/fragment/profile
dependencies in order, then rerun the release check. Do not relabel this work as
Stage 1 or fabricate a reviewer to turn the check green. No authenticated review
portal or clinical evaluation is claimed by these local-file tools.

## Earlier pass: historical findings and results

Last updated: 10 September 2026. Work was built and tested locally in VS Code.
Aswath subsequently authorized sharing it directly on a feature branch in Kajal's
repository. This upload does not publish health content or mark Stage 0 complete.

## Honest demo status

Stage 0 has a working data foundation and a first sourced review dataset. It is
**not fully signed off**: no profile is published, actual team review is pending,
and some content/licensing/localisation gaps remain. A passing software test is
not evidence that the assistant gives safe health answers. There is no live
assistant, database, clinical safety engine or application UI in this change.

## The starting point

The earlier Stage 0 commit contained 63 empty journey records, a list of 16 source
candidates, strict data contracts and 24 software tests. Evidence and guidance
files were empty. The source-verification pass on 9 September excluded the
MedlinePlus A.D.A.M. article from ingestion after checking its restrictive terms.

## What we did on 10 September

1. Read the actual Stage 0 requirements in Kajal's architecture and the execution
   plan. The requirement is 63 addressable records, with nine representative
   profiles deeply curated; it does not permit invented weekly variation.
2. Checked the source plan against publisher pages and reuse policies. Recorded
   the outcome for each original candidate, distinguishing a reachable landing
   page from a verified downloadable document.
3. Added five Office on Women's Health source entries whose page footers explicitly
   permit reproduction. Saved selected text only, with URLs, headings, versions,
   dates and checksums. These are not full-page archives or medical approval.
4. Authored eleven evidence records and eleven small draft guidance fragments.
   Linked draft content to all nine representative profiles. Kept US source
   jurisdiction visible. The IN production target has not been silently changed.
5. Added offline snapshot integrity checks, stronger draft-source checks, explicit
   publication blockers, and a small selection contract for exact weeks versus
   approximate months and confirmed conditions.
6. Added explanatory docstrings/comments at the important boundaries, improved
   malformed-JSON error messages, centralised representative IDs and removed a
   redundant exception entry. No model SDK, new runtime dependency, database or
   general-purpose scraping framework was added.
7. Created a reproducible review packet, this work log and the plain-language
   stage guide. Evidence counts can be regenerated by the validator.

## Real failures and recoveries

### A trusted website did not mean reusable content

The MedlinePlus fetal-development article is supplied by A.D.A.M./Ebix, whose
footer restricts AI/dataset reuse. We excluded it instead of copying it.
Source: https://medlineplus.gov/ency/article/002398.htm

The next check found a second, less obvious issue: NHS's normal Open Government
Licence does not cover Best Start in Life. That excluded subsite hosts the
week-by-week pages proposed in the architecture. Its separate terms did not
establish permission for our intended reuse. NHS-01 and NHS-02 are now excluded
from ingestion. No content from those pages was added to our dataset.

Policy evidence:
- https://www.nhs.uk/our-policies/terms-and-conditions/content-not-licensed-for-re-use/
- https://www.nhs.uk/best-start-in-life/terms-and-conditions/

Recovery: used permitted OWH text for a review draft. This recovered useful
content, **not every exact-week gap**. P09/P10 currently have trimester-wide
material; their exact-week developmental hero remains blocked.

### A source URL failed

The original NIN PDF returned 404. Official search identified a replacement
filename, DGI_2024.pdf, but the direct fetch also failed. WHO IRIS PDF requests
returned 403; official publication landing pages were reachable. We recorded
these outcomes and recovery URLs rather than claiming the PDFs were ingested.
A search result is not a verified corpus document.

WHO's general open licence also has noncommercial conditions. A capstone reuse
route cannot automatically be carried into a commercial startup deployment.
Each exact document still needs its own licence and section verification.
Policy: https://www.who.int/about/policies/publishing/copyright

### Draft status could conceal prohibited source material

Code review found that the old validator checked source approval/version mainly
when content became reviewed or published. Draft evidence could therefore be
stored without equally strong source-use checks.

Recovery: every stored evidence record now needs documented storage permission,
a current matching source version/checksum, and a non-excluded source. Discovery
indexes cannot act as evidence. Regression tests exercise these cases.

### Matching two checksum strings did not check the saved file

The original checks compared metadata but did not inspect source snapshot bytes.
Recovery: the file validator now hashes the actual local excerpt snapshot and
checks source identity, URL, version, locator and exact text. Paths must remain
inside the snapshot directory. Tests deliberately change bytes, URLs and locators
and attempt a path escape; each is rejected.

Limit: a checksum detects changes in our saved file. It cannot authenticate a
publisher or prove a medical claim is correct. Human source review is still needed.

### One new test initially failed for the wrong reason

The first expanded run had 41 tests with one error. The test fixture reused the
same mutable timing dictionary for evidence, fragments and a profile. Extending
an evidence range also changed the profile's supposedly exact week.

Recovery: gave each fixture record an independent copy. The rerun passed all 41
tests. This was a test-fixture defect; we did not weaken the exact-week validator.

### A missing condition must not become permission

A person not reporting a restriction does not prove that restriction is absent.
The selection contract requires explicit confirmed conditions and, where needed,
confirmed absences. It withholds a whole profile if its linked conditional items
are ineligible. This is a foundation contract, not a completed clinical resolver.

## Demo walkthrough we can show today

In VS Code, open the stage guide and review packet, then run:

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -v
.venv/Scripts/python.exe -m scripts.validate_content
.venv/Scripts/python.exe -m scripts.validate_content --require-release
```

The tests pass. Authoring validation reports 63 profiles, 21 source entries,
11 spans, 11 fragments and zero published profiles. The release command must
exit 1 because nine required profiles are unpublished. Show that refusal as an
honest governance demonstration, not as a successful product release.

The tests include wrong-week requests, month-only uncertainty, foreign-source
filtering, missing conditions, fake citations, source changes and tampered files.
These are engineering tests. The planned 45 development and 15 held-out AI
evaluation scenarios are separate and have not been executed.

## What still prevents full Stage 0 completion

- Actual named content review and product acceptance of the nine profiles.
- India-appropriate source/applicability decisions and wording; US labels cannot
  simply be replaced with IN or GLOBAL.
- A permitted exact-week development source for P09/P10.
- Broader PP12 recovery content; current support text has a specific professional-
  care condition and must not become universal advice.
- More complete domain/card content where the review packet shows empty slots.
- Publication and content-quality evaluation after these gaps are resolved.

No current health claim is published. P42 and all other uncurated shells remain
draft. The source audit records which permission/access work is still unresolved.

## A short sentence for judges

"We first built a traceable content foundation. Our checks reject wrong-week,
unreviewed and altered evidence. Source auditing caught licence restrictions in
our original plan, so we changed the dataset rather than pretending those sources
were usable. The current milestone is a reviewable foundation, not a clinically
validated assistant."

## Stage 1 implementation: public-source ingestion

### What we built

Stage 1 now admits only exact registered sources, records their version and hash,
parses structured HTML and selected PDF pages, exposes a controlled OCR boundary,
resolves selected evidence back to source blocks, adds week/domain/country/
condition/dashboard metadata, creates a human review queue, and supports
idempotent staging, source-update invalidation and immutable corpus versions.

All 14 evidence-bearing sources were dry-run. The result was 55 verified source
anchors, 55 pending review tasks, zero parser errors and zero embeddings. Zero is
intentional because none of the health records has actual publication approval.

### The first real-source run rejected passages

The first dry run did not silently accept near matches. It exposed three parser
representation problems: HTML punctuation around links, evidence deliberately
assembled from labelled bullets in more than one source block, and a PDF text
layer that returned `registratio n` with a false space.

Recovery: citation verification now normalizes punctuation only for matching,
checks each selected sentence or labelled bullet, repairs a narrowly defined
single-letter PDF split for both sides of the comparison, and stores every matched
source block ID. Original citation text is never rewritten by this normalization.
The rerun resolved every selected passage.

### A dashboard slot was absent from the Stage 1 type

The OWH stages dry run initially failed because the existing weekly profile uses
`what_may_change`, while the new display-slot type omitted it.

Recovery: added the existing slot to the typed Stage 1 contract and schema. We did
not rename the Stage 0 UI contract to make the test pass.

### Duplicate detection found duplicated Stage 0 evidence

The NHS postpartum-body page had the same complete fertility sentence stored as
`E-PP-FERTILITY` and `E-PP-FERTILITY-FEEDING` with identical scope. Two distinct
fragments used the sentence to support two different pieces of wording.

Recovery: retained one canonical evidence span, linked both fragments to it,
regenerated the governed snapshot/profile references, and refreshed the two
explicit Codex claim assessments. The evidence count changed from 56 to 55; the
56 distinct fragments remain. Stage 0 and Stage 1 checks both pass after the fix.

### OCR was not installed on the workstation

PyMuPDF was available after adding the pinned Stage 1 dependencies, but no local
Tesseract executable was installed. Pretending scanned pages were parsed would
have made the demo unsafe.

Recovery: implemented and tested an explicit Tesseract CLI adapter. An image-only
page without that configured adapter returns `NEEDS_OCR`; a failed adapter returns
`OCR_FAILED`; successful OCR is labelled `OCR_APPLIED` with provider/version and
confidence. The selected real PDFs have usable text layers, so no real source
needed OCR in this run.

### Dry-run files initially failed their own schema

The CLI first mixed operator fields such as `write_state` into the serialized
`IngestionRun`. Strict Pydantic validation correctly rejected those files.

Recovery: the output file now contains only the typed run. Operator write/artifact
states remain in the console summary. All 14 saved dry-run reports now validate.

### Capture date and currency date were initially the same input

The first implementation used the artifact's retrieval date to decide whether a
source review was overdue. Replaying an old capture could therefore judge currency
in the past instead of today.

Recovery: each run now records a separate `evaluated_at` date. The run ID binds
both dates, and a regression test proves an old retrieval date cannot bypass an
overdue current review.

### The first P10 measurement candidate failed checksum serialization

The exact P10 passage contains a 2.5 cm length. When that typed candidate was first
added, the real-source run stopped because the checksum builder received a Pydantic
object instead of canonical JSON.

Recovery: measurement candidates are converted to validated JSON before hashing.
The annotation is bound to the exact evidence checksum; an evidence edit makes it
stale. The full candidate-path test and the BHC source rerun now pass. No fruit or
object comparison was promoted.

### Network capture was blocked inside the sandbox

The first exact-URL fetch failed with a Windows socket-permission error. This was
an execution boundary, not a source or parsing result.

Recovery: reran the administrative capture with the allowed network permission.
The capture code still restricts requests to registered public HTTPS URLs, checks
public DNS, host-preserving redirects, content type, empty bodies and a 20 MB limit.

### Embeddings and publication remain deliberately empty

The repository has a provider-neutral OpenAI-compatible embedding adapter, but no
provider/model is selected and no content is approved. Test vectors are marked
`TEST_ONLY` and the corpus publisher rejects them.

Recovery is a real review process, not a code bypass: named reviewers must update
the governed records, then ingestion reruns with an explicitly selected provider.
Only committed publishable runs can create a hashed immutable corpus version.

## Independent Stage 1 correction pass

Kajal's handoff identified seven engineering corrections and one Windows TLS
reproduction concern. We merged current upstream `main`, moved the audit proof
out of ignored local reports, stored governed blocks, forced changed sources back
to review, added five-role decisions, bound corpus publication to the Stage 0
fingerprint, and separated logical content versions from capture dates. The CLI
now finds the latest same-source run automatically.

The tracked audit initially recorded counts but omitted parser identity and exact
review-task IDs requested by the handoff. Recovery: expanded the text-free audit
contract and regenerated all 14 sources. It now contains parser/version,
artifact/source/governance/selected-text hashes, block IDs and review-task IDs.

The five OWH URLs downloaded successfully through the existing verified HTTPS
path. The earlier TLS error did not reproduce. No `verify=False`, alternate
unverified context or certificate bypass was added.

The review packet previously asked reviewers to return a document because the
machine-readable decision schema was incomplete. Recovery: each decision now
binds task, candidate, evidence, source, role and candidate checksum; preserves
reviewer identity/capacity/reason and exact proposed changes; and can be reloaded
with `--review-decisions`. Unknown or stale task decisions fail validation.

## Stage 2 Supabase storage and isolation

Five versioned migrations were applied to the new `nestline-dev` project. The
first creates 28 tables, RLS on every table, a private 10 MB PDF/PNG/JPEG medical
document bucket, dimension-neutral pgvector fields, published-only public search
and workspace-filtered private search. Later migrations protect owner membership,
bind ingestion provenance to one content release, add workspace/journey lifecycle
functions and fix owner visibility during workspace creation.

### The SQL editor rejected the first automation method

The dashboard uses a Monaco editor. The first direct fill action failed because
the page target changed while the editor was active. Recovery: focused the editor,
selected its complete contents and typed the migration through the browser. Before
execution, the editor content was copied back and compared after normalising line
endings. Supabase returned `Success. No rows returned`, followed by live counts of
28 Stage 2 tables, 28 RLS-enabled tables, one private bucket and the vector extension.

### Dashboard SQL did not create migration history

The schema was present, but `supabase_migrations.schema_migrations` initially did
not exist because the first migration was run in the dashboard. A future CLI push
could otherwise try to run it again. The CLI login command could not open an
interactive token prompt in this execution channel. Recovery: used Supabase's
documented migration-table structure, stored each exact migration body with its
canonical timestamp/name, and verified all five version rows. Repository hashes
and secret-free live counts are committed for drift detection.

### The first lifecycle test found an RLS timing bug

`create_workspace` inserted the correct `owner_user_id`, but `INSERT ... RETURNING`
also evaluated the read policy before the AFTER INSERT membership trigger had
created the owner row. Supabase rejected the insert. Recovery: the workspace read
policy now permits the authenticated owner immediately and preserves membership
access for collaborators. The repeated lifecycle transaction passed.

### Live isolation and lifecycle evidence

One rolled-back transaction created fictional users A and B. A saw one SQL row,
one private vector result, one graph node and one private Storage record. B saw
zero of all four and a cross-workspace update changed zero rows: nine assertions
passed. A second transaction proved workspace creation, journey versions 1 and 2,
stale-version rejection, same-document-hash rejection and demo reset. Follow-up
queries showed zero temporary users, workspaces and Storage objects remaining.

No public corpus, health embedding or real personal record was added. Stage 2
provides storage and isolation; Stage 0 human approvals still control which public
health content may enter the later RAG system.

### The first clean-clone Stage 2 check failed on line endings

The SQL and all Stage 1 checks passed in the clean clone, but every recorded SQL
hash differed because Git checked the files out with Windows CRLF line endings
while the original files used LF. Recovery: Stage 2 now hashes canonical UTF-8
text after normalising CRLF to LF, matching the platform-independent Stage 0
fingerprint approach. The repeated clean clone passed both Stage 1 and Stage 2
checkers. No SQL or deployed schema was changed for this fix.

## Kajal product/content review and three-profile preview

Kajal returned an explicit product/content decision for `PC00`, `P10` and `PP01`,
plus a corrected 42-row comparison catalogue. We applied the 13 changed week rows
and regenerated the Stage 0 fingerprint and reviewer artifacts. All comparison
rows remain draft; measurement values and object dimensions remain blank, so the
comparison gate keeps all 42 hidden.

The initial review ledger was empty even though the ingestion schema supported
role decisions. Recovery: recorded two real roles for each of the 27 exact tasks,
producing 54 decisions bound to task, candidate, evidence, source and checksum.
The Stage 1 checker now validates this ledger against the tracked source audit,
and the main review queue displays recorded and pending roles separately.

We added a deterministic specialist handoff for the clinical, India-localisation
and licence reviewers. It contains the exact source text, proposed wording,
conditions, source/reuse state and copyable decision form for each task. No
specialist identity or approval was invented.

The Streamlit reviewer app reads the same draft records and ledger. It renders
the three profiles with fictional condition scenarios, makes unknown facts visible
as “needs information”, and labels the entire app as unavailable to public users,
embeddings and live RAG. It is a visual-review artifact, not the Stage 9 patient
application or a content release.

## Updated Kajal approval bundle import

The updated handoff and worksheet restate the accepted product/content scope,
Kajal's review capacity/date and the specialist boundaries. The user supplied the
explicit typed instruction to import these decisions. We preserved both attached
files byte-for-byte with SHA-256 identifiers and updated all 54 governed role
decisions to cite them.

The replacement comparison CSV exactly matched the catalogue already applied, so
no duplicate data edit or new fingerprint was created. Two PC00 task IDs printed
in the worksheet belonged to an older candidate version. We retained the approved
stable evidence IDs and resolved them to the current canonical tasks/checksums;
the governed checker rejects the obsolete task IDs. Specialist and final rendered
UI approvals remain pending.

## Independent Stage 2 correction pass

The independent review found eight real gaps behind the earlier passing static
checker. The main gaps were unused member roles with equal powers, no repeatable
clean/upgrade database suite, unvalidated dependency arrays, an unfinished
Storage-first reset path, ambiguous episode ownership, incomplete journey
constraints and only ten typed personal records.

Recovery: adopted an owner-only V1 and documented one workspace as one care
episode; added five normalized dependency tables with transactional stale-state
updates; made journey stage/timing combinations exact in SQL and Pydantic; added
all missing typed records; added exact-prefix Storage cleanup plus session-scoped
`maya-v1` demo reseeding; and added Docker CI for clean and upgrade paths.

While constructing the live suite, we found a further bypass: the broad original
policy still permitted direct deletion of private document metadata. Recovery:
removed that policy, revoked direct delete permission and made the owner-checked
lifecycle functions the only database deletion route after Storage cleanup.

The first pgTAP run exposed a test-harness column-name error; the next reached
128 successful assertions before a leftover direct Storage cleanup statement hit
Supabase's own deletion-protection trigger. We corrected the harness instead of
weakening Storage. The remote verification at that point reported 141 assertions,
but its exact SQL source was not preserved in Git. The current Stage 2 suite pins
122 assertions; the evidence gap and current coverage inventory are recorded in
STAGE-2-ASSERTION-COVERAGE-MAPPING.md. Both the exact five-migration upgrade and
a clean ten-migration replay pass with zero database lint errors. All five additive corrections were then deployed to `nestline-dev`,
and read-only remote verification found ten migration rows, all 28 tables under
RLS, five dependency tables, zero direct document-delete grants and zero fixtures.
A separate 13-check local Auth/REST/Storage run also proved the actual owner and
outsider file boundary plus complete temporary-fixture cleanup.

## Stage 3 onboarding and journey resolution

Stage 3 added strict timing inputs, a pure resolver with an injected clock,
optional onboarding details, a functional Streamlit flow and one atomic confirmed
Supabase commit. The remote nestline-dev project now ends at migration 00900.

### Day 7 exposed two different meanings of “week”

The chronological resolver correctly maps seven elapsed days to postpartum week 2
day 0. The existing content selector maps overlay PPD7 to profile PP01. Before
changing either value, we checked decision 0002: the team had explicitly accepted
PPD0-PPD7 as an overlay group on PP01. Recovery: kept chronological journey state
and content grouping as separate concepts, documented both and added a regression
test for the accepted PPD7/PP01 mapping.

### A passing owner policy still allowed confirmation bypass

The Stage 2 all-actions policy allowed an authenticated owner to update a journey
row directly. RLS protected users from one another, but this route could bypass
Stage 3's confirmation provenance. Recovery: migration 00900 changes journey RLS
to owner read-only access, revokes direct insert/update/delete, revokes the older
mutation RPC and keeps the security-definer complete_onboarding function as the
authenticated confirmed-write route. Local and remote checks report zero direct
and zero legacy mutation grants.

### Database lint found implicit-array cast warnings

The first exact Stage 2-to-Stage 3 upgrade behaved correctly, but database lint
reported five warnings around empty UUID/text arrays. Recovery: added explicit
UUID-array and text-array casts. The repeated exact upgrade, clean replay and lint
then passed with 167 assertions and zero findings.

### The first Streamlit smoke assertion used the wrong accessor

The app rendered, but the test script tried to inspect an AppTest form collection
that this Streamlit version does not expose. Recovery: assert the rendered title,
privacy warning, tabs, submit buttons and inputs through supported accessors. The
repeated smoke check passed without a network request.

### Initial Stage 3 evidence before the exit audit

The 153-test Python regression, 64 existing contract cases, 26 journey cases,
exact upgrade, clean replay, 13 Storage API checks, 12 onboarding API checks and
Streamlit render all passed. Relogin restored the confirmed state; another user
could neither read nor write it; repeated submission created no duplicate; and
independent fixture queries returned zero. A dry run listed only migration 00900
before it was deployed. No GitHub commit, push or pull request was performed.
## Stage 3 independent exit audit and Stage 4 readiness

The initial Stage 3 build passed its stated tests, but the later plan-by-plan audit
looked for ways a correct UI could still be bypassed. It found that the real API
persistence check did not store every timing route, backward care-episode
transitions appeared selectable, and the database trusted client-computed timing
conflicts and the draft-safety Boolean.

Recovery: expanded the real onboarding matrix from 12 to 17 checks so all six
input routes persist; marked pregnancy/postpartum regressions noncommittable in
the resolver, service and UI; and added migration 01000. The migration independently
recomputes timing bounds, verifies due/delivery arithmetic and conflict provenance,
requires contiguous versions, blocks episode regression and requires every
onboarding symptom to remain evaluation-only while the safety file is a draft.
It also updates demo seeding to preserve confirmation identity and time.

The first full database rerun caught an over-strict confirmation constraint. Fact
deletion intentionally invalidates a journey while keeping its old confirmation
audit trail. Recovery: changed the rule to require paired confirmation fields and
require them for a currently confirmed state, while allowing invalidated history
to remain attributed. The older deletion test and every new negative test then
passed. A lint run performed concurrently with pgTAP saw temporary pgTAP functions;
lint was rerun after the transaction and returned zero findings. CI keeps these
steps sequential.

Final evidence is 154/154 Python tests, 64/64 contract cases, 26/26 journey cases,
24/24 focused journey/onboarding tests, and 160/160 database assertions on both an
exact 00900-to-01000 upgrade and a clean twelve-migration replay. The 13 Storage
API checks, 17 onboarding API checks and Streamlit smoke render pass. Read-only
remote inspection confirms 12 migrations, all hardening constraints and trigger,
zero direct/legacy mutation grants, zero private-helper grants and zero temporary
fixtures.

The Stage 4 readiness checker validates eight editable texts, eight watermarked
PDFs, eight extraction-truth files, 33 proposed candidates with provenance, six
explicit abstentions and one prompt-injection fixture. The noisy/OCR variant,
typed graph-change truth and upload edge-case fixtures are the first Stage 4 build
items. Live/public upload remains parked behind a scanning-policy decision and the
outstanding human review gates.

No GitHub commit, push or pull request was performed during this exit audit.

## Stage 4 personal documents and confirmed state

Stage 4 now implements the full fictional document-to-state slice. Eight
watermarked records have typed extraction and graph truth, one noisy OCR image has
frozen expected text, and locked, corrupt, unsupported, oversize and wrong-person
files exercise the upload boundary. Proposals retain exact page/span provenance;
medication text remains record-only; missing information abstains. Authenticated
owners may edit, confirm, reject or preserve a conflict. One versioned idempotent
transaction creates confirmed facts and graph links, asks clarification questions
and marks affected movement plans stale. Direct client mutation of proposals,
derived facts and graph state is closed.

The exact migration upgrade was tested from `01000` with pre-existing confirmed
document, fact and medication rows. It backfilled the required decision provenance.
A clean replay through `01100` was tested separately. Each path passed 195 pgTAP
assertions, 45 authenticated Auth/Storage/PostgREST/RPC checks and database lint
with zero findings. The complete application suite passed 175 Python tests, 64
content-contract cases, 26 journey cases and the Stage 3/4 Streamlit renders.

Adding the noisy PNG first broke the release fingerprint because binary images
were decoded as text. Binary hashing fixed it. The new governed fixtures then
changed the foundation checksum; a guarded fingerprint-only audit rebind was added
that refuses any source, evidence, candidate, parser or review-task change. An
attempt to rebuild from local Stage 1 run artifacts correctly failed because those
transient files use the earlier ingestion schema. We did not rewrite or invent
source review. The guarded rebind validated all 14 sources and 54 recorded Kajal
decisions.

The combined pgTAP runner had previously deadlocked when independent SQL files ran
in parallel, so CI now runs them sequentially. CI also loads a real legacy fixture
before migration `01100` and verifies the backfill after it. The global Python
interpreter lacked PyMuPDF; official local commands use the pinned repository
virtual environment.

Remote deployment did not occur. Supabase refused the saved scoped access token for
project `jtmiduftpbvmahbmryki` because the token/account pair lacks the required
privilege. No remote schema was changed and no GitHub commit, push or pull request
was performed. A corrected project-scoped database/migration token is required to
deploy `01100`. Real uploads additionally remain closed until a malware scanner,
exact model/cost benchmark and the named human reviews are complete.

## Stage 4 remote deployment and API-role recovery

The original remote deployment attempt was correctly stopped when the first scoped
Supabase token lacked project access. Aswath replaced it with a project-scoped
token stored only in `.env`. Link and dry-run then succeeded, migration `01100` was
deployed, and all 195 existing remote pgTAP assertions passed.

The first linked schema comparison exposed a separate issue that the behavior tests
had not measured: automatic Data API exposure had added 72 anonymous grant changes.
RLS still prevented a cross-workspace read, but the privilege surface was broader
than the architecture permits. Migration `01200` now revokes anonymous access to
all current public tables, sequences and inherited functions, then restores only
six read-only published-content tables plus published guideline retrieval. It also
closes anonymous defaults for future `postgres`-owned application objects.

The first clean reset of `01200` failed because it attempted to alter the managed
`supabase_admin` role's default privileges. That operation is not available to an
application migration. Recovery: removed the platform-owner operation, kept the
current-object revocation and scoped future defaults to Nestline's migration owner.
The next clean install succeeded and the new 11-assertion role test passed.

Final remote evidence: all 14 migrations are present, none are pending, all 206
pgTAP assertions pass, lint has zero findings, anonymous access is exactly six
read-only public-content grants, private retrieval is unavailable to anonymous
users, and zero test fixtures or personal workspaces remain. The publishable-key
API returned HTTP 200 for public content and HTTP 401 for personal workspaces. The raw CLI diff still
contains Supabase-managed `service_role` metadata and `public.rls_auto_enable`, plus
CR/LF-only serialization of nine Nestline functions; application-role drift and
Nestline-function semantic mismatches are both zero. The secret-free evidence is
`data/supabase/stage4-remote-verification.json`.

No GitHub commit, push or pull request was performed.
