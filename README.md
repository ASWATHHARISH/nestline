# Nestline

Nestline is a safety-focused maternal continuity AI capstone covering pregnancy through 12 weeks postpartum. Its assistant, Compass, organizes user-provided records, retrieves governed public guidance, coordinates bounded specialist agents, and stops or escalates when evidence is missing, conflicting, or urgent.

> Nestline is a capstone prototype, not a medical device, doctor, diagnostic service, treatment system, or emergency service. Do not upload real personal or medical information to the public prototype.

## Start here

The canonical product, architecture, data, safety, delivery, and evaluation specification is:

- [Nestline Updated Architecture](<docs/Nestline updated architecture.md>)
- [Execution plan, stage estimates, and release gates](docs/NESTLINE-EXECUTION-PLAN.md)

It covers the Streamlit application, one explicit profile for every pregnancy and postpartum week, reusable sourced guidance fragments, onboarding, home and chat UX, governed sources, Supabase data architecture, RAG and GraphRAG, specialist-agent contracts, plans, safety, human review, error handling, n8n workflows, evaluation, implementation sequence, pre-mortem, and old-versus-current decision reconciliation. The earlier source-of-truth document is retained as decision history only.

## Development status

Stage 0 work is shared on `feat/stage-0-data-foundation` in
`kajalchourasia-cmd/nestline`. Pull requests and changes to `main` require an
explicit request from Aswath.

The Stage 0 correction pass has 63 journey records: nine populated representative
profiles, eight populated early-postpartum overlays and 46 hidden shells. There
are 31 registered sources, 14 active selected-excerpt snapshots, 55 unique evidence spans
and 56 draft fragments. The additional catalogues, eight fictional PDF/text/truth
fixtures and visible software-test cases are present.

Local checks pass: 95 unit tests and 64 deterministic software cases. These are
not AI-model or clinical evaluations. **Stage 0 is not a completed content release:**
source currency, current Indian clinical interpretation, exact wording and actual
human review/publication remain open. Fruit measurements and object dimensions
are unverified; those proposals remain hidden. No health content is published.

Stage 1's governed ingestion system is implemented. Dry runs against all 14
evidence-bearing sources resolve all 55 unique source passages and create 55 human
review tasks. They correctly create zero embeddings while the content is unapproved.

- [Correction findings, evidence and remaining work](docs/STAGE-0-CORRECTION-STATUS.md)
- [Current source states](docs/STAGE-0-SOURCE-STATE.json)
- [Plain-language project progress](docs/PROJECT-PROGRESS.md)
- [Demo work log: failures and recovery](docs/DEMO-WORK-LOG.md)
- [Actual content review packet](docs/STAGE-0-REVIEW-PACKET.md)
- [Stage 0 setup and handoff](docs/STAGE-0-HANDOFF.md)
- [Stage 1 implementation and operator guide](docs/STAGE-1-IMPLEMENTATION.md)
- [Stage 1 in plain language](docs/STAGE-1-PLAIN-LANGUAGE.md)
- [Stage 1 reviewer queue](docs/STAGE-1-REVIEW-QUEUE.md)
