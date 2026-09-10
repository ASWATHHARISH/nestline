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

Local checks pass: 113 unit tests and 64 deterministic software cases. These are
not AI-model or clinical evaluations. **Stage 0 is not a completed content release:**
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
public provenance and authenticated workspace/journey lifecycle functions. A
transactional two-user test passed across SQL, private vector search, graph,
Storage policy and cross-workspace mutation, then rolled back all fixtures.

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

Run the draft-only reviewer preview with:

```powershell
.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```
