# Stage 4 self-verification and Stage 5 readiness

**Audit date:** 11 September 2026  
**Auditor:** Codex engineering self-review  
**Verdict:** Stage 4 fictional-demo engineering passes and Stage 5 engineering may begin locally

The current finding-by-finding correction record is
STAGE-2-3-4-INDEPENDENT-REVIEW-RESPONSE-AND-STAGE-5-GATE.md. GitHub CI remains
pending until these local changes are approved and pushed.

## Scope of the verdict

This verdict covers the planned Stage 4 document-to-confirmed-state slice with
fictional records. It does not claim medical correctness, India-local clinical
approval, production malware protection or live-model quality. Those need the
named external work listed below.

## Requirement-by-requirement result

| Required result | Evidence | Result |
|---|---|---|
| Eight coherent fictional documents | Text, watermarked PDFs, extraction truth and typed graph truth for `DOC-001`–`DOC-008` | Pass |
| Controlled OCR case | Frozen noisy image and five-field truth; injected OCR adapter test | Pass |
| Upload failures are explicit | Locked, corrupt, unsupported, oversize and wrong-person fixtures | Pass |
| Public upload boundary | Feature defaults off; supervised mode selects nine exact-hash fixtures and exposes no arbitrary uploader | Pass |
| Identity cannot be skipped | Extracted exact match or verified fixture binding; missing, blank, multiple, near-match and wrong tests | Pass |
| Proposals are not active facts | SQL grants/RLS and pre-confirmation API lookup | Pass |
| Exact provenance | Page, source quote, offsets, coordinates, checksum and extraction method | Pass |
| User controls the change | No radio is preselected; save is disabled until every row has a decision | Pass |
| Reviewer sees provenance | Document, page/span, coordinates, confidence, completeness, disposition and state render | Pass |
| Atomic and repeatable commit | Expected-version and idempotency ledger checks | Pass |
| Conflicts preserve history | `DOC-005`/`DOC-006` database and API scenario | Pass |
| Plan dependency is visible | Restriction confirmation marks movement plan stale | Pass |
| Prompt injection is inert | Document text test plus tool-free provider contract | Pass |
| Cross-user privacy | pgTAP owner/outsider checks and authenticated API test | Pass |
| Upgrade safety | Existing Stage 3 confirmed rows receive decision provenance | Pass |
| Clean setup and shared deployment | All 14 migrations replay locally and match `nestline-dev` migration history | Pass |

## Evidence totals

- 175 Python tests passed.
- 64 public-content contract cases passed.
- 26 journey cases passed.
- The exact Stage 3→4 document upgrade retains its 195 passing assertions; the
  API-role hardening adds 11, for 206 passing assertions on the clean local and
  deployed remote schemas.
- 45 authenticated Storage/PostgREST/RPC checks passed on both local database paths.
- Stage 3 and Stage 4 Streamlit render checks passed without network calls.
- Local and remote database lint returned zero findings; remote migration parity,
  application-role drift and temporary-fixture counts are all zero.

## What failed during implementation and how it was corrected

### Binary fixture fingerprinting

Adding the noisy PNG exposed a text-only assumption in the release fingerprint.
The reader attempted to decode the image as UTF-8. PNG/JPEG files now use byte
hashes, and the full regression suite passes.

### Stage 1 audit invalidation

The governed Stage 4 fixtures legitimately changed the broad foundation checksum,
but retained Stage 1 ingestion run artifacts use an older internal schema. Blindly
rebuilding would have failed or implied a new source audit. A guarded rebind script
now permits only the top-level fingerprint mismatch and refuses to write if source
coverage, evidence, candidate checksums, parser provenance or review tasks differ.
The current 14-source audit and all 54 imported decisions validate afterward.

### Upgrade compatibility

The initial migration needed explicit backfill for older confirmed document,
document-fact and medication rows before adding stricter provenance constraints.
A pre-Stage-4 fixture now makes CI prove this exact upgrade instead of testing an
empty migration history.

### Derived graph mutation

Owner isolation alone still allowed a client to write graph nodes and edges
directly. Stage 4 closes direct graph mutation and leaves the protected confirmation
function as the only writer. Owners retain read access.

### Conflict dependency semantics

A conflicted proposal originally appeared in a confirmed dependency list. The
commit path now creates a clarification question without treating the disputed
fact as confirmed input.

### SQL and test-runner issues

Postgres required explicit array casts and parenthesized JSON label expressions.
The combined pgTAP runner also encountered a transient deadlock when files ran in
parallel. The SQL was corrected, and CI runs the independent transactional files
sequentially. All suites pass twice.

### Local Python interpreter

The global Python installation lacked PyMuPDF. The repository virtual environment
contains the pinned dependencies, so all official commands and CI use the project
interpreter/environment.

### Remote Supabase authorization and Data API exposure

The first scoped token could not link to `nestline-dev`, so no remote write was
attempted with it. After Aswath supplied a replacement project-scoped token, link,
dry run and deployment succeeded.

The first post-deployment schema comparison then caught 72 unintended anonymous
grant changes from the project's automatic Data API exposure setting. RLS still
blocked cross-workspace data, but the extra API surface did not meet the architecture's
least-privilege rule. Migration `01200` revokes current anonymous table, sequence
and inherited function access, restores only six published-content reads, and
closes future `postgres` application-object defaults. Its 11 regression assertions
pass locally and remotely. No application-role or Nestline-function semantic drift
remains; the raw CLI diff contains only Supabase-managed administrative metadata,
CR/LF serialization and one platform helper.

## Work parked outside the engineering verdict

| Item | Why it is parked | Required before |
|---|---|---|
| Production malware scanner | No scanner service was selected | Any real medical upload |
| Exact candidate model IDs and cost ceiling | Product/cost choice is unset | Live fictional provider benchmark |
| Clinical and India-localisation decisions | Code cannot self-approve care wording | Live health guidance/public release |
| Final rendered product acceptance | Named product review is still open | Public release |

## Stage 5 handoff

Stage 5 may use the confirmed health facts, medication record-only rows,
appointments, typed graph nodes/edges, clarification questions and stale-plan
markers created here on both the local and `nestline-dev` schemas. It must preserve
the same workspace boundary and may retrieve only confirmed facts. It must apply hard lane, approval, stage/week, jurisdiction
and workspace filters before semantic ranking. Stage 5 must also prove that graph
expansion changes a relationship-dependent case and must not claim a graph benefit
when exact SQL already answers it.

This independent-review correction remains local. GitHub still points to reviewed
commit 68722f8 until Aswath explicitly approves a push.
