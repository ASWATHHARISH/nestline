# Stage 0: data foundation and review handoff

Scope: first implementation of the full canonical architecture. No medical content
is published yet. No backend, UI, database permissions, model, clinical safety gate,
or deployment is claimed to be implemented by this change.

## What exists

- Pydantic contracts for source records, reviews, applicability, evidence spans,
  fragments, heroes/cards and weekly profiles, plus exported JSON Schema.
- All 63 journey shells with a checked coverage matrix; nine canonical representative
  profiles are prioritized without reducing the overall record coverage.
- Source candidates transcribed from the canonical architecture. URLs, source dates,
  reuse permissions and actual passages still require individual verification.
- A command-line authoring check for schemas, identifiers, citations, source versions,
  checksums, review metadata, applicability and jurisdiction.
- A stricter release mode that fails while representative profiles remain unpublished.
- A fictional journey specification and eight-document inventory for the next stage.

## Run locally

From the repository root with Python 3.12:

VS Code is configured to use the project's `.venv` interpreter. Use **Terminal >
Run Task** for `Nestline: test data contracts` or `Nestline: validate draft dataset`.
The Python extension, if installed, can discover the unittest suite in the Test view.

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -m unittest discover -s tests -v
.venv/Scripts/python -m scripts.validate_content
.venv/Scripts/python -m scripts.validate_content --require-release
```

The last command deliberately exits 1 until reviewed content is populated. An
authoring pass means the draft dataset is structurally consistent, not ready to serve
health answers. Regenerate the schema with `python -m scripts.export_content_schema`
when Python contracts change; tests detect a stale schema export.

Validation evidence for this initial change: a fresh Windows Python 3.12 virtual
environment installed all pinned dependencies and ran the local checks. The GitHub
Actions workflow is provided but its hosted run is not yet verified.

CSV array/object columns use JSON values, not ad hoc comma-splitting. Empty evidence
and fragment JSONL files are deliberate: no retrieved medical passages have been
approved or copied yet. The coverage matrix is an audit view of the weekly manifest.

## Next working sequence

1. Codex verifies candidate sources and exact reuse terms and selects passages for the
   nine canonical representative profiles. Begin with PC00/P10/PP01 to validate the
   pipeline, then complete the rest; this is build order, not a reduced final target.
2. Kajal reviews the card structure, product wording and intended applicability with
   the team. Record actual reviewer identities; never pre-fill fictitious approval.
3. Codex implements versioned public ingestion and document fixtures, preserving
   source snapshots/locators. Supabase isolation can proceed alongside this once
   account access exists.
4. Kajal defines expected evaluation behavior. The engineering contract tests here
   are additional to the 45 development and 15 sealed holdout product scenarios.

## Limits of the checker

It verifies explicit metadata and relationships. It cannot prove a reuse declaration
is legally correct, authenticate a reviewer, assess the medical meaning of a passage,
or prove that a citation supports a paraphrase. Those require source review and later
claim-support evaluation. The current command never publishes or writes to a service.

Postpartum day overlays have their own applicability unit. The canonical PPD0–PPD7
inventory is retained without silently defining how day 7 maps to a postpartum week;
that boundary must be specified and tested in the journey resolver implementation.
