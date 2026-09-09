# Fictional journey contract

Status: authored scenario outline; not clinical guidance or reviewed medical data.
All future fixture PDFs must display FICTIONAL DEMO DATA. No real person's records,
contacts, identifiers, clinician identity or institution branding may be used.

Use one fictional persona, Maya, in an isolated demo workspace. The story starts at
P10, advances through P24, and later reaches PP01. Fixed fixture dates and a testable
clock must be selected together in the document-fixture implementation; never use
the wall clock to silently change a recorded demonstration.

## Expected events

1. DOC-001 proposes baseline timing and a fictional food allergy. Until explicit
   confirmation, extracted values are visible proposals and cannot personalize.
2. A reviewed baseline plan records the confirmed state version, evidence IDs and
   dependencies. Missing information remains unknown, never interpreted as absent.
3. DOC-003 introduces a documented instruction. Medication wording is recorded
   verbatim with provenance; Compass does not recommend a dose or a treatment change.
4. DOC-006 adds a movement restriction and conflicts with an older instruction.
   Confirmation creates new state, retains the historical source, marks dependent
   plans stale and prepares a clarification question. It does not resolve the conflict.
5. DOC-007 proposes an appointment/follow-up. Explicit save is required; repeated
   processing creates one logical task.
6. DOC-008 proposes the transition to postpartum; user confirmation is required and
   the old episode remains historical rather than being overwritten.
7. A separate curated urgent input bypasses routine generation and never waits for
   simulated human review. Actual input/wording awaits the reviewed safety specification.

## Invariants for later expected-extraction fixtures

- A second workspace never retrieves any persona artifact.
- Every proposed fact retains document/page/span and status.
- A duplicate document, replayed confirmation or stale save cannot corrupt state.
- Irrelevant new information does not mark every plan stale.
- A changed dependency explains which plan item became stale and why.
- Delete removes or invalidates derived facts, chunks, graph links and summaries.
- Simulated review is labeled in every state and requires consent for the packet.

The inventory is in document_inventory.csv. Actual text/PDFs and expected JSON are
not yet generated. This outline is not counted as eight completed documents.
