"""Verify Stage 3 resolver, onboarding contracts, UI, migrations, and deployment."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

from app.services.stage3_validation import (
    validate_deterministic_resolver,
    validate_stage3_hardening_migration,
    validate_stage3_migration,
)
from scripts.export_onboarding_schema import build_payload
from scripts.run_journey_evals import run as run_journey_evals


ROOT = Path(__file__).resolve().parents[1]
BASE_MIGRATION = ROOT / "supabase/migrations/20260911000900_stage3_onboarding_commit.sql"
HARDENING_MIGRATION = ROOT / "supabase/migrations/20260911001000_stage3_exit_hardening.sql"
RESOLVER = ROOT / "app/services/journey.py"
SCHEMA = ROOT / "data/schemas/onboarding.schema.json"
REMOTE_EVIDENCE = ROOT / "data/supabase/stage3-remote-verification.json"


def _canonical_digest(path: Path) -> str:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    return sha256(text.encode("utf-8")).hexdigest()


def _remote_errors(payload: dict) -> list[str]:
    errors = []
    expected_checks = {
        "migration_history_rows": 12,
        "journey_provenance_columns": 8,
        "symptom_provenance_columns": 4,
        "onboarding_submission_indexes": 4,
        "complete_onboarding_functions": 1,
        "complete_onboarding_authenticated_grants": 1,
        "journey_direct_mutation_grants": 0,
        "legacy_journey_mutation_grants": 0,
        "journey_hardening_constraints": 3,
        "symptom_hardening_constraints": 1,
        "journey_transition_triggers": 1,
        "private_bounds_authenticated_grants": 0,
        "stage3_pg_tap_assertions": 26,
        "stage3_exit_hardening_pg_tap_assertions": 12,
        "stage3_api_checks": 17,
        "stage3_streamlit_render_checks": 1,
        "temporary_fixture_rows_remaining": 0,
    }
    if payload.get("checks") != expected_checks:
        errors.append("tracked Stage 3 remote verification counts are missing or stale")
    if payload.get("contains_secrets") is not False:
        errors.append("Stage 3 remote verification must explicitly be secret-free")

    base = payload.get("migration", {})
    if (
        base.get("version") != "20260911000900"
        or base.get("name") != "stage3_onboarding_commit"
        or base.get("file_sha256") != _canonical_digest(BASE_MIGRATION)
    ):
        errors.append("Stage 3 remote verification does not match the base migration")

    hardening = payload.get("hardening_migration", {})
    if (
        hardening.get("version") != "20260911001000"
        or hardening.get("name") != "stage3_exit_hardening"
        or hardening.get("file_sha256") != _canonical_digest(HARDENING_MIGRATION)
    ):
        errors.append("Stage 3 remote verification does not match the hardening migration")
    return errors


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-remote", action="store_true")
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args(argv)

    errors = []
    errors.extend(validate_stage3_migration(BASE_MIGRATION))
    errors.extend(validate_stage3_hardening_migration(HARDENING_MIGRATION))
    errors.extend(validate_deterministic_resolver(RESOLVER))

    generated_schema = build_payload()
    tracked_schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    if tracked_schema != generated_schema:
        errors.append("tracked onboarding JSON Schema is stale")

    evaluation = run_journey_evals()
    if not evaluation["valid"] or evaluation["total"] != 26:
        errors.extend(evaluation["errors"] or ["journey resolver evaluation set is incomplete"])

    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    for dependency in ("streamlit==1.63.0", "python-dotenv==1.2.3"):
        if dependency not in requirements:
            errors.append(f"missing pinned Stage 3 dependency: {dependency}")

    ui = (ROOT / "app/pages_and_components/onboarding.py").read_text(encoding="utf-8")
    for fragment in (
        "Personal empty workspace", "Fictional demo mode",
        "Calculate and review", "Save confirmed information",
        "render_document_panel",
        "start a new workspace for a new pregnancy",
    ):
        if fragment not in ui:
            errors.append(f"onboarding UI is missing: {fragment}")

    remote = None
    if not args.skip_remote:
        if not REMOTE_EVIDENCE.exists():
            errors.append("Stage 3 remote verification evidence is missing")
        else:
            remote = json.loads(REMOTE_EVIDENCE.read_text(encoding="utf-8"))
            errors.extend(_remote_errors(remote))

    result = {
        "valid": not errors,
        "migrations": [
            {
                "path": str(BASE_MIGRATION.relative_to(ROOT)),
                "sha256": _canonical_digest(BASE_MIGRATION),
            },
            {
                "path": str(HARDENING_MIGRATION.relative_to(ROOT)),
                "sha256": _canonical_digest(HARDENING_MIGRATION),
            },
        ],
        "journey_evaluations": {
            "total": evaluation["total"],
            "passed": evaluation["passed"],
            "dataset_sha256": evaluation["dataset_sha256"],
        },
        "remote_project": remote.get("project_name") if remote else None,
        "remote_verified_at": remote.get("verified_at") if remote else None,
        "remote_checks": remote.get("checks") if remote else None,
        "errors": errors,
    }
    if args.write_report:
        (ROOT / "docs/STAGE-3-CHECK-RESULTS.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n"
        )
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())