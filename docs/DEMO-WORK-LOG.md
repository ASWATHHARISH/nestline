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
