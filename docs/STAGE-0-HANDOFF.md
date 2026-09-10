# Stage 0 setup and handoff

Read PROJECT-PROGRESS.md for the simple explanation and
STAGE-0-CORRECTION-STATUS.md for implemented fixes and open decisions. No patient-
facing content or safety system is released by this change.

## Run in VS Code

Open this repository folder in VS Code. Its tasks use the local .venv interpreter.
With Python 3.12 installed, run these from the repository root:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m unittest discover -s tests -v
.venv/Scripts/python.exe -m scripts.validate_content
.venv/Scripts/python.exe -m scripts.validate_content --require-review-ready
.venv/Scripts/python.exe -m scripts.run_contract_evals
.venv/Scripts/python.exe -m scripts.export_source_state
.venv/Scripts/python.exe -m scripts.export_review_packet
.venv/Scripts/python.exe -m scripts.validate_content --require-release
```

Release currently exits 1 for actual unresolved review/publication work. Do not
change statuses just to make it pass. The other commands pass locally. The script
scripts.check_stage0 records all checks in docs/STAGE-0-CHECK-RESULTS.json and
returns the release result; its nonzero exit is not hidden as a successful release.
The GitHub workflow runs software and review-readiness checks, not clinical approval.

## Maintained files

- app/schemas/content.py and data/schemas/content_bundle.schema.json define content.
- app/services/content_validation.py checks references, scope and publication.
- app/services/source_snapshots.py checks saved excerpt bytes, locators and paths.
- app/services/content_selection.py selects published cards and preserves unknowns.
- app/schemas/foundation.py defines catalogue, review, plan and safety records.
- app/services/foundation.py checks catalogue evidence, recorded claim assessments,
  review fingerprints, source currency and release requirements.
- app/services/safety_contract.py exercises draft English routing examples offline;
  it does not permit normal generation or establish clinical safety.
- data/catalogues/ contains editable draft options; conditions come from the shared
  condition_registry.yaml. JSON is used inside structured CSV columns.
- data/safety/rule_spec.yaml uses the JSON subset of YAML 1.2; no extra YAML parser.
- data/reviews/claim_audit.jsonl records Codex assessments, distinct from the empty
  actual human approvals.json ledger.
- data/synthetic/ contains eight fictional PDFs/texts and expected extraction truth.
- evals/phase_1_contract.jsonl is a versioned visible software contract, not an AI
  baseline, hidden test set or proof of extraction accuracy.

## Reproduction and editing

Regenerate the content schema with scripts.export_content_schema after schema edits.
The curation scripts contain the explicit 10 September authored changes; they do
not fetch or freshly verify websites. They refuse to overwrite actual reviews.
Re-running curation cannot approve revised clinical claims: existing claim hashes
must be reassessed by their named assessor if their supporting content changes.

The eight PDFs are already committed. To recreate them, use a separate optional
Python environment with requirements-fixtures.txt and run
python -m scripts.build_synthetic_documents. Rendering uses pdftoppm when installed.
This authoring dependency is separate from the application runtime. Generated
PDF bytes can vary with library versions; verify the PDFs and matching truth
together before replacing them. No real medical document is used.

## What is not established by the checks

The checks do not authenticate a reviewer, prove clinical meaning, grant licences,
measure object dimensions or assess AI quality. See the correction status for the
specific remaining work. Later stages still need ingestion/OCR, isolated storage,
confirmed state updates, retrieval, reviewed safety, agents, answer validation and UI.

All work stays on feat/stage-0-data-foundation in kajalchourasia-cmd/nestline.
Aswath authorised pushing there. No PR or change to main is authorised.
