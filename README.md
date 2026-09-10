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

Stage 0 has 63 journey records, 21 source entries, five saved excerpt snapshots,
11 evidence spans, 11 fragments and nine populated review drafts. All profiles
remain unpublished. Local engineering checks pass; content completion, India
applicability and actual review remain open.

- [Plain-language project progress](docs/PROJECT-PROGRESS.md)
- [Demo work log: failures and recovery](docs/DEMO-WORK-LOG.md)
- [Actual content review packet](docs/STAGE-0-REVIEW-PACKET.md)
- [Stage 0 setup and handoff](docs/STAGE-0-HANDOFF.md)
