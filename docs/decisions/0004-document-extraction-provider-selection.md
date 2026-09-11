# ADR 0004: benchmark document extraction providers behind one packet contract

- Status: Accepted
- Date: 11 September 2026
- Scope: Stage 4 document extraction and Stage 5 readiness

## Context

The architecture calls for provider-neutral document extraction and comparison of
candidate models. The repository currently has a deterministic fictional-fixture
parser and one optional OpenAI Structured Outputs adapter. No exact Grok model,
endpoint, credentials, quality result or cost ceiling has been approved. Naming a
winner now would invent evidence.

## Decision

The versioned DocumentExtractionPacket schema is the provider-neutral boundary.
Every adapter must return that same proposal-only contract with exact source
spans, confidence, completeness, disposition, provider trace and no direct state
mutation.

The deterministic parser remains the reproducible baseline for all Stage 4 and
Stage 5 engineering tests. The OpenAI adapter remains an unselected benchmark
candidate. Grok or another provider may be added only after an exact model and
endpoint are available.

Provider selection will use the frozen fictional corpus and measure exact-source
field recall, abstention behavior, injection resistance, identity handling,
latency and cost under an approved ceiling. Results must be stored without report
contents or secrets. No provider output becomes a confirmed fact without the
same explicit review commit.

Stage 5 deterministic retrieval engineering may proceed because it consumes
confirmed facts and approved public evidence, independent of which extractor
eventually wins.

## Consequences

- There is no unsupported claim that OpenAI is the production provider.
- Provider benchmarking and cost approval remain an operational gate.
- Public or real medical-document upload remains closed until a deployable
  server-side scanner, provider decision and required human approvals exist.
- Adding another adapter does not change the database confirmation boundary.
