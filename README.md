# Nestline

Nestline is a safety-focused maternal continuity AI capstone covering pregnancy through 12 weeks postpartum. Its assistant, Compass, organizes user-provided records, retrieves governed public guidance, coordinates bounded specialist agents, and stops or escalates when evidence is missing, conflicting, or urgent.

> Nestline is a capstone prototype, not a medical device, doctor, diagnostic service, treatment system, or emergency service. Do not upload real personal or medical information to the public prototype.

## Start here

The canonical product, architecture, data, safety, delivery, and evaluation specification is:

- [Nestline Updated Architecture](<docs/Nestline updated architecture.md>)
- [Execution plan, stage estimates, and release gates](docs/NESTLINE-EXECUTION-PLAN.md)

It covers the Streamlit application, one explicit profile for every pregnancy and postpartum week, reusable sourced guidance fragments, onboarding, home and chat UX, governed sources, Supabase data architecture, RAG and GraphRAG, specialist-agent contracts, plans, safety, human review, error handling, n8n workflows, evaluation, implementation sequence, pre-mortem, and old-versus-current decision reconciliation. The earlier source-of-truth document is retained as decision history only.

## Development status

Current engineering work is on `feat/stage-1-governed-ingestion` in
`kajalchourasia-cmd/nestline`. No pull request or merge to `main` is created
without Aswath's explicit request.

The Stage 0 correction pass has 63 journey records: nine populated representative
profiles, eight populated early-postpartum overlays and 46 hidden shells. There
are 31 registered sources, 14 active selected-excerpt snapshots, 55 unique evidence spans
and 56 draft fragments. The additional catalogues, eight fictional PDF/text/truth
fixtures and visible software-test cases are present.

Local checks pass: 175 unit tests, 64 public-content contract cases and 26 journey
resolver cases. These are not live AI-model or clinical evaluations. **Stage 0 is
not a completed content release:**
source currency, current Indian clinical interpretation, exact wording and actual
human review/publication remain open. Fruit measurements and object dimensions
are unverified; those proposals remain hidden. No health content is published.

Stage 1's governed ingestion system is implemented. Dry runs against all 14
evidence-bearing sources resolve all 55 unique source passages and create 55 human
review tasks. They correctly create zero embeddings while the content is unapproved.
Kajal has accepted the product wording, placement and conditional behaviour for
the 27 evidence tasks used by `PC00`, `P10` and `PP01`. Those 54 role decisions
(content plus product) are checksum-bound in the governed ledger. Clinical,
India-localisation and licence review remain open, so the slice is still unpublished.

The attached rounder/repeatable baby-size sequence has been applied. All 42
comparisons remain draft and hidden because measurement values and object
dimensions are still unverified.

Stage 2's Supabase storage foundation is deployed to `nestline-dev`: 28 tables,
RLS on all 28, a private medical-document bucket, pgvector support, release-bound
public provenance and authenticated workspace/journey lifecycle functions. Ten
migrations now enforce owner-only workspaces, strict timing combinations,
dependency invalidation, Storage-first document deletion and versioned per-session
demo reset. The current Stage 2 two-user suite pins 122 assertions, passes on both
an upgrade and a clean installation, and rolls back all fixtures. The earlier
remote record reported 141, but its exact SQL source was not preserved; the
reconciliation is documented without inventing a one-to-one mapping. A separate
13-check local API
test proves the same owner boundary through Auth, REST and private Storage and
removes every temporary fixture.

Stage 3 onboarding and journey resolution are implemented and deployed as base
migration 00900 plus exit-hardening migration 01000. Streamlit now provides
sign-in/account creation, Personal Empty/Fictional Demo workspace selection, all
six timing paths and optional allergies, history, restrictions, symptoms and
appointments. Pure Python calculates exact week/day or an approximate range with
a test clock; conflicts are shown for explicit user choice, while backward care-
episode transitions require a new workspace. The database independently rechecks
timing arithmetic, conflict provenance and the draft-safety marker. Direct and
legacy journey mutation grants are both zero. The 26-case date corpus, 160 current database
assertions, 17 real onboarding API checks and Streamlit smoke render pass. Draft
symptom routing remains evaluation-only until specialist review.

Stage 4 personal-document engineering is complete for a supervised fictional demo.
The document feature defaults off and exposes no arbitrary uploader. When enabled
for development, it accepts only nine exact-hash repository fixtures, verifies
identity, uses native text or controlled OCR, shows complete proposal provenance,
starts every review decision empty, and commits confirmed state only after every
row is deliberately resolved. The governed document migration and API-
role hardening are deployed to `nestline-dev`; all 14 migrations are in parity, all
206 local and remote database assertions pass, 45 authenticated API checks pass,
and remote lint reports zero findings. Anonymous access is limited to six read-only
published-content tables. Real medical uploads remain closed until a deployable
scanner and human release gates are complete.

- [Correction findings, evidence and remaining work](docs/STAGE-0-CORRECTION-STATUS.md)
- [Current source states](docs/STAGE-0-SOURCE-STATE.json)
- [Plain-language project progress](docs/PROJECT-PROGRESS.md)
- [Demo work log: failures and recovery](docs/DEMO-WORK-LOG.md)
- [Actual content review packet](docs/STAGE-0-REVIEW-PACKET.md)
- [Stage 0 setup and handoff](docs/STAGE-0-HANDOFF.md)
- [Stage 1 implementation and operator guide](docs/STAGE-1-IMPLEMENTATION.md)
- [Stage 1 in plain language](docs/STAGE-1-PLAIN-LANGUAGE.md)
- [Stage 1 reviewer queue](docs/STAGE-1-REVIEW-QUEUE.md)
- [Stage 1 independent-review correction status](docs/STAGE-1-CORRECTION-STATUS.md)
- [Kajal human-review handout](docs/KAJAL-HUMAN-REVIEW-HANDOUT.md)
- [PC00/P10/PP01 specialist and final visual review handoff](docs/STAGE-1-PC00-P10-PP01-REVIEW-HANDOFF.md)
- [Kajal updated approval import record](docs/STAGE-1-KAJAL-APPROVAL-IMPORT-RECORD.md)
- [Stage 2 implementation and verification](docs/STAGE-2-IMPLEMENTATION.md)
- [Stage 2 in plain language](docs/STAGE-2-PLAIN-LANGUAGE.md)
- [Stage 2 independent-review response](docs/STAGE-2-INDEPENDENT-REVIEW-RESPONSE.md)
- [Stage 3 implementation and verification](docs/STAGE-3-IMPLEMENTATION.md)
- [Stage 3 in plain language](docs/STAGE-3-PLAIN-LANGUAGE.md)
- [Stage 3 product and independent-review handoff](docs/STAGE-3-REVIEW-HANDOFF.md)
- [Stage 3 self-verification and Stage 4 readiness](docs/STAGE-3-SELF-VERIFICATION-AND-STAGE-4-READINESS.md)
- [Stage 4 implementation and verification](docs/STAGE-4-IMPLEMENTATION.md)
- [Stage 4 in plain language](docs/STAGE-4-PLAIN-LANGUAGE.md)
- [Stage 4 final verification, review, and Stage 5 handoff](docs/STAGE-4-REVIEW-HANDOFF.md)
- [Stage 4 self-verification and Stage 5 readiness](docs/STAGE-4-SELF-VERIFICATION-AND-STAGE-5-READINESS.md)

Run the current Streamlit application with:

```powershell
.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```
