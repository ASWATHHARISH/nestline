# Stage 1 — governed public ingestion

Updated 11 September 2026. This is the technical source of truth for Stage 1.

## Outcome

The Stage 1 ingestion system is implemented and tested. It can admit an exact
registered public source, capture a version, parse HTML or PDF, use explicitly
configured OCR for an image-only PDF, resolve each selected citation back to
source blocks, attach downstream metadata, create a human review queue, create
embeddings only for approved retrievable units, detect updates/duplicates and
publish an immutable local corpus version.

An independent handoff review identified seven engineering corrections and one
environment-specific TLS check. All seven corrections are implemented. Verified
TLS capture succeeded for all five OWH pages, so no certificate verification was
disabled and no fallback was needed.

The current health content is **not published**. Kajal accepted content and
product behaviour for the 27 evidence tasks behind `PC00`, `P10` and `PP01`.
The governed ledger contains 54 current checksum-bound decisions. Clinical,
India-localisation and licence decisions remain pending for that slice, while
the other evidence still needs its applicable reviews. The 14-source run therefore
keeps all 55 tasks in review and creates zero embeddings.

## What goes in and what comes out

Input is one exact HTML page or PDF already present in the source registry. The
job also reads Stage 0 evidence, fragments, weekly profiles and recommendation
catalogues. It never invents medical text from the rest of a page.

Output is a typed ingestion run containing:

- source URL, version, retrieval date, byte count, parser version and SHA-256;
- structured source blocks with page/heading/table anchors;
- one candidate per selected unique evidence unit;
- original citation text plus normalized search text;
- stage, week/day range, jurisdiction, domain and conditions;
- links to weekly profiles, fragments and catalogue items;
- future dashboard slots and required personal fact types;
- a human checklist and explicit blocking reasons;
- a diff showing new, changed, removed and invalidated records;
- one embedding per approved retrievable unit, or none when approval forbids it.

Public-source ingestion and personal-document ingestion remain separate. Allergies,
medical history, medication/supplement mentions, symptoms, movement restrictions,
the confirmed week and next appointment will come from onboarding or confirmed
private-document facts in Stages 3–4. Stage 1 records only which fact types a future
recommendation needs. It never puts a person's report into the public corpus.

## Complete Stage 1 work breakdown

| Part | Deliverable | Estimate | State |
|---:|---|---:|---|
| 1 | Typed ingestion contract | 20 min | Done |
| 2 | Dashboard/content labels for hero, KPIs, nutrition, movement, wellbeing, symptoms, preparation, consider/avoid and follow-up | 20 min | Done |
| 3 | Future personal-fact dependencies for week, allergies, restrictions, history, medicines, symptoms and appointment | 25 min | Done |
| 4 | Source admission from status, reuse permission, storage permission, currency and review | 30 min | Done |
| 5 | Exact source version, retrieval date, parser version, byte count and checksum | 20 min | Done |
| 6 | HTML parsing by headings, paragraphs, lists and tables; page chrome removed | 45 min | Done |
| 7 | PDF parsing by selected pages with page and heading anchors; tables preserved | 50 min | Done |
| 8 | Controlled OCR adapter with visible `NEEDS_OCR`, `OCR_FAILED` and `OCR_APPLIED` states | 35 min | Done; real selected PDFs had text layers |
| 9 | Conservative Unicode, whitespace, quote, dash and PDF split-word normalization | 25 min | Done |
| 10 | Meaningful evidence units limited to already selected Stage 0 passages | 30 min | Done |
| 11 | Stage/week/day/jurisdiction/applicability metadata | 20 min | Done |
| 12 | General development-measurement contract kept separate from a user's scan values | 20 min | Done; exact P10 2.5 cm candidate captured, while fruit/object comparisons remain unverified |
| 13 | Recommendation metadata and profile/fragment/catalogue links | 30 min | Done |
| 14 | Pydantic validation and citation-to-block verification | 35 min | Done |
| 15 | Five-role human review queue, reloadable structured decisions and no automatic approval | 30 min | Done |
| 16 | Profile and recommendation catalogue linkage | 25 min | Done |
| 17 | Original citation text, normalized search text and provider-neutral embedding adapter | 35 min | Done |
| 18 | Duplicate detection, deterministic run IDs and idempotent writes | 35 min | Done |
| 19 | Source-change diff, affected profile/catalogue IDs and cache invalidation scopes | 35 min | Done |
| 20 | Dry run for all 14 evidence-bearing sources | 60 min | Done: 55/55 anchors, no parser errors |
| 21 | Adversarial parser, admission, OCR, citation, embedding, update and storage tests | 60 min | Done |
| 22 | Immutable local corpus publisher with hashes and test-vector prohibition | 35 min | Done; no health corpus released before review |
| 23 | VS Code handoff, check report, demo log and reviewer packet | 45 min | Done |

The estimate is about 12–15 focused hours for a first implementation. Parts were
completed together where one test exercised several contracts.

## Current dry-run evidence

`docs/STAGE-1-CHECK-RESULTS.json` records the clean-checkout result from the
tracked, text-free `data/ingestion/audit/stage1-source-audit.json`:

- 14 source runs;
- 55 unique candidate evidence units;
- 55 verified source anchors;
- 55 pending review tasks;
- 54 recorded role decisions across 27 of those tasks (content and product);
- 0 parser/validation errors;
- 0 embeddings and 0 published health records.

For each source, the audit keeps the artifact hash, source version, parser name
and version, stable logical version, evidence/candidate/checksum lists, separate
selected-text and source-governance checksums, governed block IDs, exact review
task IDs and outcome. It does not commit full copyrighted source documents.

`data/reviews/ingestion_decisions.json` holds the actual role decisions. The
Stage 1 checker proves that each task ID, candidate, evidence record, source and
checksum still exists in the canonical audit. The reviewer queue joins those
decisions and shows only the three pending roles for the first slice.

## Independent correction pass

1. The feature branch was merged with the current upstream `main` without
   removing the Stage 0 gates.
2. The 14-source/55-passage audit moved from ignored local reports to a tracked,
   text-free record; the Stage 1 checker now runs in CI.
3. Governed parsed blocks are stored in every run and a published corpus writes
   `blocks.jsonl`; every candidate block ID must resolve exactly.
4. Changed bytes, source version or governed source permissions force renewed
   review, clear embeddings and invalidate linked profiles, catalogues and caches.
5. Review decisions preserve task/candidate/evidence/source IDs, checksum,
   reviewer role/capacity, disposition, reason, references and exact requested
   changes. The CLI rejects stale or mismatched decision ledgers.
6. Corpus publication rechecks the current Stage 0 fingerprint and all five
   separate release roles instead of trusting an ingestion flag.
7. Logical source versions are stable across capture dates, and the CLI
   automatically loads the latest same-source staged run for comparison.
8. All five OWH sources were captured using normal verified TLS in the full
   14-source rerun. No insecure TLS option exists in the capture workflow.

During the dry run, Stage 1 caught a duplicated NHS evidence passage. The two
different fragments now share one canonical evidence unit. No text or meaning was
discarded. It also handled punctuation-only HTML differences, section-separated
bullets and the PDF text-layer split `registratio n` without changing stored source
quotes.

## Future dashboard and RAG contract

Stage 3 will calculate or confirm the current journey timing. Stage 4 will propose
facts from the user's uploaded fictional/demo reports and ask for confirmation.
Stage 5 will combine that confirmed private context with this public corpus using
hard filters before search. A future week page can then assemble:

- confirmed week/stage and timing KPI;
- a reviewed general development KPI, if one exists for that week;
- next-appointment information from the user's confirmed state;
- reviewed nutrition, movement and wellbeing cards compatible with known facts;
- symptoms, preparation, consider/avoid and professional-question cards;
- a chatbot evidence packet with resolvable citations.

Unknown allergy, restriction, clearance or symptom facts remain unknown. The
system must ask or withhold the affected recommendation; it cannot treat missing
information as permission.

## Operator commands

```powershell
# Run every engineering test
.venv/Scripts/python.exe -m unittest discover -s tests -v

# Parse a saved exact source without writing staging data
.venv/Scripts/python.exe -m scripts.ingest_public_source `
  --source-id NHM-MOTHERHOOD `
  --input data/raw/nhm-motherhood.pdf `
  --retrieved-at 2026-09-10 `
  --as-of 2026-09-10 `
  --output reports/local/stage1-nhm-motherhood.json

# Render all current review tasks
.venv/Scripts/python.exe -m scripts.export_ingestion_review `
  --run-directory reports/local `
  --output docs/STAGE-1-REVIEW-QUEUE.md

# Rebuild the PC00/P10/PP01 specialist packet from tracked governed records
.venv/Scripts/python.exe -m scripts.export_stage1_slice_review

# Reload role-specific reviewer decisions for one source
.venv/Scripts/python.exe -m scripts.ingest_public_source `
  --source-id NHM-MOTHERHOOD `
  --input data/raw/nhm-motherhood.pdf `
  --retrieved-at 2026-09-10 `
  --review-decisions data/reviews/ingestion_decisions.json

# Recreate the Stage 1 evidence report
.venv/Scripts/python.exe -m scripts.check_stage1
```

`--retrieved-at` records when the bytes were captured. `--as-of` is the separate
date used to decide whether the source is still current; an old capture date cannot
bypass an overdue review. `--commit-staging` stores an admitted, non-rejected
retrievable artifact and run locally under ignored `data/ingestion` folders.
Fixed-quotation sources keep only their governed excerpts, never a full page
artifact. A scanned PDF also needs `--tesseract-path` and
an installed Tesseract executable. Embeddings need an explicit provider name,
full OpenAI-compatible embeddings endpoint, model and API key environment
variable. No provider has been chosen because there are no approved units yet.

The `publish_ingestion_corpus` command accepts only committed `publishable` runs.
It rejects drafts, missing embeddings, duplicate evidence IDs and the deterministic
test vectors. Stage 2 will move the released records to Supabase with access rules.

## Files to open in VS Code

- `app/schemas/ingestion.py` — data contracts and review records.
- `app/services/public_parsers.py` — HTML, PDF and controlled OCR.
- `app/services/public_ingestion.py` — admission, anchors, metadata, review and embeddings.
- `app/services/ingestion_store.py` — idempotent staging and immutable corpus publication.
- `scripts/ingest_public_source.py` — one-source operator command.
- `scripts/export_ingestion_review.py` — reviewer packet generator.
- `tests/test_ingestion.py` — adversarial Stage 1 tests.
- `docs/STAGE-1-REVIEW-QUEUE.md` — all pending human decisions.
- `docs/DEMO-WORK-LOG.md` — failures, fixes and honest limitations.
