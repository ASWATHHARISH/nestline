"""Run and record reproducible Stage 1 engineering and saved-source checks."""

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys

from app.schemas.ingestion import IngestionRun
from app.services.foundation import read_catalogues, validate_foundation
from scripts.validate_content import load_bundle

ROOT = Path(__file__).resolve().parents[1]


def command(arguments: list[str]) -> dict:
    result = subprocess.run([sys.executable, *arguments], cwd=ROOT, capture_output=True, text=True)
    return {"arguments": arguments, "exit_code": result.returncode,
            "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}


def inspect_saved_runs(bundle) -> dict:
    by_source = {}
    malformed = []
    for path in sorted((ROOT / "reports/local").glob("stage1-*.json")):
        try:
            run = IngestionRun.model_validate_json(path.read_text(encoding="utf-8"))
        except Exception as exc:
            malformed.append({"file": path.name, "error": type(exc).__name__})
            continue
        by_source[run.admission.source_id] = run
    fixed_quote_sources = {source.source_id for source in bundle.sources
                           if source.delivery_mode == "fixed_quote"}
    processed = {candidate.evidence_id for run in by_source.values() for candidate in run.candidates}
    expected = {evidence.evidence_id for evidence in bundle.evidence}
    missing = expected - processed
    unexpected_missing = sorted(evidence_id for evidence_id in missing
                                if next(e.source_id for e in bundle.evidence
                                        if e.evidence_id == evidence_id) not in fixed_quote_sources)
    return {
        "saved_run_count": len(by_source),
        "source_ids": sorted(by_source),
        "candidate_count": sum(len(run.candidates) for run in by_source.values()),
        "verified_anchor_count": sum(candidate.source_anchor_verified for run in by_source.values()
                                     for candidate in run.candidates),
        "review_task_count": sum(len(run.review_tasks) for run in by_source.values()),
        "embedding_count": sum(len(run.embeddings) for run in by_source.values()),
        "error_count": sum(issue.severity == "error" for run in by_source.values() for issue in run.issues),
        "outcomes": {source_id: run.outcome for source_id, run in sorted(by_source.items())},
        "missing_evidence_ids": sorted(missing),
        "expected_fixed_quote_missing_ids": sorted(missing - set(unexpected_missing)),
        "unexpected_missing_ids": unexpected_missing,
        "malformed_run_files": malformed,
    }


def main() -> int:
    tests = command(["-m", "unittest", "discover", "-s", "tests", "-q"])
    dependencies = command(["-m", "pip", "check"])
    bundle = load_bundle(ROOT / "data")
    foundation_errors = validate_foundation(bundle, ROOT / "data")
    schema_file = json.loads((ROOT / "data/schemas/ingestion.schema.json").read_text(encoding="utf-8"))
    schema_ok = set(schema_file.get("records", {})) == {
        "evidence_candidate", "evidence_review_task", "ingestion_run", "corpus_manifest"
    }
    saved = inspect_saved_runs(bundle)
    match = re.search(r"Ran (\d+) tests?", tests["stderr"])
    report = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "execution": "Local engineering checks and previously captured exact-source dry runs",
        "tests_run": int(match.group(1)) if match else None,
        "checks": {"software_tests": tests, "dependencies": dependencies,
                   "foundation_errors": foundation_errors,
                   "ingestion_schema_present": schema_ok,
                   "saved_source_dry_runs": saved},
        "release_state": {
            "public_corpus_published": False,
            "reason": "All current public evidence still requires actual source/content/local/clinical/product review.",
            "production_embedding_provider_selected": False,
        },
        "limitations": [
            "Engineering tests are not clinical review or an AI answer evaluation.",
            "The two Better Health Channel fixed quotations are display-only under the registry and are forbidden from embeddings.",
            "Private medical reports belong to Stage 4 and were not placed in this public corpus.",
            "Supabase publication belongs to Stage 2; Stage 1 publishes only an immutable local corpus after approvals.",
        ],
    }
    (ROOT / "docs/STAGE-1-CHECK-RESULTS.json").write_bytes(
        (json.dumps(report, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({"tests_run": report["tests_run"],
                      "tests_exit": tests["exit_code"],
                      "dependency_exit": dependencies["exit_code"],
                      "foundation_errors": len(foundation_errors),
                      "source_runs": saved["saved_run_count"],
                      "candidates": saved["candidate_count"],
                      "anchors": saved["verified_anchor_count"],
                      "unexpected_missing": saved["unexpected_missing_ids"],
                      "source_errors": saved["error_count"]}, indent=2))
    return int(any((tests["exit_code"], dependencies["exit_code"], foundation_errors,
                    not schema_ok, saved["malformed_run_files"],
                    saved["unexpected_missing_ids"], saved["error_count"],
                    saved["candidate_count"] != saved["verified_anchor_count"])))


if __name__ == "__main__":
    raise SystemExit(main())
