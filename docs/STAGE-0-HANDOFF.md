# Stage 0: data foundation and review handoff

Scope: first implementation of the full canonical architecture. No medical content
is published yet. No backend, UI, database permissions, model, clinical safety gate,
or deployment is claimed to be implemented by this change.

## What exists

- Pydantic contracts for source records, reviews, applicability, evidence spans,
  fragments, heroes/cards and weekly profiles, plus exported JSON Schema.
- All 63 journey shells with a checked coverage matrix; nine canonical representative
  profiles are prioritized without reducing the overall record coverage.
- 29 source entries, 13 selected-excerpt snapshots, 28 evidence spans and 28
  fragments. Nine representative profiles have concrete domain cards and reasons
  for intentionally empty slots. Named review remains pending.
- Proposed India adoption records preserve original foreign jurisdictions and
  require their own named review. NHM passages supply local guidance.
- Quote-only permissions preserve wording and attribution and exclude those
  fragments from the model-retrieval subset.
- A command-line authoring check for schemas, identifiers, citations, source versions,
  checksums, review metadata, applicability and jurisdiction.
- A stricter release mode that fails while representative profiles remain unpublished.
- A fictional journey specification and eight-document inventory for the next stage.
- Published-only selection contract covering uncertain months, jurisdictions and
  confirmed conditions; this is not the complete Stage 3 journey resolver.
- A review worksheet and plain-language/demo work logs for the team.

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
.venv/Scripts/python -m scripts.validate_content --require-review-ready
.venv/Scripts/python -m scripts.validate_content --require-release
.venv/Scripts/python -m scripts.export_review_packet
```

The `--require-release` command deliberately exits 1 until the representative
content has actually been reviewed and published. An
authoring pass means the draft dataset is structurally consistent, not ready to serve
health answers. Regenerate the schema with `python -m scripts.export_content_schema`
when Python contracts change; tests detect a stale schema export.

Validation evidence for this initial change: a fresh Windows Python 3.12 virtual
environment installed all pinned dependencies and ran the local checks. The GitHub
Actions workflow is provided but its hosted run is not yet verified.

CSV array/object columns use JSON values, not ad hoc comma-splitting. Evidence and
fragment JSONL files now contain drafts; none is approved or published. The coverage
matrix is an audit view of the weekly manifest. Snapshot checksums refer to actual
selected-excerpt JSON bytes, not full publisher webpages. Git attributes preserve
LF newlines for these files across Windows and Linux.

The latest local run passed 47 engineering tests. Read PROJECT-PROGRESS.md
for precise stage/phase status and DEMO-WORK-LOG.md for failures and recovery.
Run `python -m scripts.check_stage0` to refresh the machine-readable check report.
It returns the release gate's nonzero status while review/publication is pending.

## Next working sequence

1. Review the concrete cards in STAGE-0-REVIEW-PACKET.md against their full source
   context. Exact P09/P10 evidence, broader PP12 material and local NHM guidance
   have been added. Explicitly assess the older BHC source and its quote-only use.
2. Record actual source, evidence, localisation, fragment and profile reviews for
   the packet's dataset fingerprint. Correct rejected items, regenerate the packet
   and review again. Publish dependencies in order and rerun the release gate.
   This is still Stage 0; it is not being silently deferred to Stage 1.
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
