"""Verify Stage 1 from tracked, text-free evidence rather than ignored local files."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys

from app.schemas.ingestion import Stage1Audit, Stage1ReviewLedger
from app.services.foundation import read_catalogues, validate_foundation
from app.services.ingestion_audit import validate_stage1_audit
from scripts.validate_content import load_bundle

ROOT = Path(__file__).resolve().parents[1]


def command(arguments: list[str]) -> dict:
    result = subprocess.run([sys.executable, *arguments], cwd=ROOT, capture_output=True, text=True)
    return {"arguments": arguments, "exit_code": result.returncode,
            "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}


def inspect_canonical_audit(bundle) -> tuple[dict, list[str]]:
    path = ROOT / "data/ingestion/audit/stage1-source-audit.json"
    if not path.exists():
        return {"present": False}, ["tracked canonical Stage 1 source audit is missing"]
    try:
        audit = Stage1Audit.model_validate_json(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"present": True, "malformed": type(exc).__name__}, [
            f"tracked canonical Stage 1 source audit is malformed: {type(exc).__name__}"]
    errors = validate_stage1_audit(audit, bundle, ROOT / "data")
    return {
        "present": True,
        "source_count": len(audit.sources),
        "source_ids": [source.source_id for source in audit.sources],
        "candidate_count": sum(len(source.candidate_ids) for source in audit.sources),
        "verified_anchor_count": sum(source.verified_anchor_count for source in audit.sources),
        "governed_block_count": sum(len(source.governed_block_ids) for source in audit.sources),
        "review_task_count": sum(source.review_task_count for source in audit.sources),
        "embedding_count": sum(source.embedding_count for source in audit.sources),
        "error_count": sum(source.error_count for source in audit.sources),
        "outcomes": {source.source_id: source.outcome for source in audit.sources},
        "foundation_release_fingerprint": audit.foundation_release_fingerprint,
    }, errors


def inspect_review_ledger() -> tuple[dict, list[str]]:
    """Prove that every recorded role decision still names a current task."""
    ledger_path = ROOT / "data/reviews/ingestion_decisions.json"
    audit_path = ROOT / "data/ingestion/audit/stage1-source-audit.json"
    if not ledger_path.exists():
        return {"present": False}, ["Stage 1 review ledger is missing"]
    try:
        ledger = Stage1ReviewLedger.model_validate_json(
            ledger_path.read_text(encoding="utf-8"))
        audit = Stage1Audit.model_validate_json(audit_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"present": True, "malformed": type(exc).__name__}, [
            f"Stage 1 review ledger or audit is malformed: {type(exc).__name__}"]

    sources = {source.source_id: source for source in audit.sources}
    errors = []
    for decision in ledger.decisions:
        source = sources.get(decision.source_id)
        if source is None:
            errors.append(f"{decision.task_id}: decision source is absent from the canonical audit")
            continue
        if decision.task_id not in source.review_task_ids:
            errors.append(f"{decision.task_id}: review task is absent or stale")
        if decision.candidate_id not in source.candidate_ids:
            errors.append(f"{decision.task_id}: candidate is absent or stale")
        if decision.evidence_id not in source.evidence_ids:
            errors.append(f"{decision.task_id}: evidence is absent or stale")
        if decision.candidate_checksum not in source.candidate_checksums:
            errors.append(f"{decision.task_id}: candidate checksum is absent or stale")
        if decision.task_id != f"REV-{decision.candidate_checksum[:20]}":
            errors.append(f"{decision.task_id}: task ID does not match its candidate checksum")
        if decision.candidate_id != f"C-{decision.evidence_id}":
            errors.append(f"{decision.task_id}: candidate ID does not match its evidence ID")
    role_counts = {role: sum(decision.role == role for decision in ledger.decisions)
                   for role in ("licence", "content", "clinical", "india_localisation", "product")}
    return {
        "present": True,
        "decision_count": len(ledger.decisions),
        "task_count": len({decision.task_id for decision in ledger.decisions}),
        "reviewer_names": sorted({decision.reviewer_name for decision in ledger.decisions}),
        "role_counts": role_counts,
    }, errors


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true",
                        help="refresh docs/STAGE-1-CHECK-RESULTS.json after verification")
    parser.add_argument("--report-path", type=Path,
                        default=ROOT / "docs/STAGE-1-CHECK-RESULTS.json")
    args = parser.parse_args(argv)
    tests = command(["-m", "unittest", "discover", "-s", "tests", "-q"])
    dependencies = command(["-m", "pip", "check"])
    bundle = load_bundle(ROOT / "data")
    foundation_errors = validate_foundation(bundle, ROOT / "data")
    schema_file = json.loads((ROOT / "data/schemas/ingestion.schema.json").read_text(encoding="utf-8"))
    schema_ok = set(schema_file.get("records", {})) == {
        "parsed_block", "evidence_candidate", "evidence_review_decision",
        "evidence_review_task", "stage1_review_ledger", "ingestion_run",
        "corpus_manifest", "stage1_audit"
    }
    saved, audit_errors = inspect_canonical_audit(bundle)
    review_ledger, review_ledger_errors = inspect_review_ledger()
    match = re.search(r"Ran (\d+) tests?", tests["stderr"])
    report = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "execution": "Clean-checkout engineering checks and tracked exact-source audit",
        "tests_run": int(match.group(1)) if match else None,
        "checks": {"software_tests": tests, "dependencies": dependencies,
                   "foundation_errors": foundation_errors,
                   "ingestion_schema_present": schema_ok,
                   "canonical_source_audit": saved,
                   "canonical_source_audit_errors": audit_errors,
                   "governed_review_ledger": review_ledger,
                   "governed_review_ledger_errors": review_ledger_errors},
        "release_state": {
            "public_corpus_published": False,
            "reason": "The PC00/P10/PP01 slice has product/content decisions; licence, clinical and India-localisation reviews remain open, as do reviews outside that slice.",
            "production_embedding_provider_selected": False,
        },
        "limitations": [
            "Engineering tests are not clinical review or an AI answer evaluation.",
            "The two Better Health Channel fixed quotations are display-only under the registry and are forbidden from embeddings.",
            "Private medical reports belong to Stage 4 and were not placed in this public corpus.",
            "Supabase publication belongs to Stage 2; Stage 1 publishes only an immutable local corpus after approvals.",
        ],
    }
    if args.write_report:
        args.report_path.parent.mkdir(parents=True, exist_ok=True)
        args.report_path.write_bytes(
            (json.dumps(report, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({"tests_run": report["tests_run"],
                      "tests_exit": tests["exit_code"],
                      "dependency_exit": dependencies["exit_code"],
                      "foundation_errors": len(foundation_errors),
                      "source_runs": saved.get("source_count", 0),
                      "candidates": saved.get("candidate_count", 0),
                      "anchors": saved.get("verified_anchor_count", 0),
                      "governed_blocks": saved.get("governed_block_count", 0),
                      "audit_errors": audit_errors,
                      "review_decisions": review_ledger.get("decision_count", 0),
                      "review_ledger_errors": review_ledger_errors,
                      "source_errors": saved.get("error_count", 0)}, indent=2))
    return int(any((tests["exit_code"], dependencies["exit_code"], foundation_errors,
                    not schema_ok, audit_errors, review_ledger_errors,
                    saved.get("error_count", 0),
                    saved.get("candidate_count") != saved.get("verified_anchor_count"))))


if __name__ == "__main__":
    raise SystemExit(main())
