"""Verify Stage 2 contracts, migrations and tracked remote evidence without secrets."""

import argparse
from hashlib import sha256
import json
from pathlib import Path

from app.schemas.storage import STAGE2_TABLES, USER_OWNED_TABLES
from app.services.storage_validation import (validate_stage2_migration,
                                             validate_journey_state_invariants,
                                             validate_owner_only_episode_boundary,
                                             validate_personal_dependency_invalidation,
                                             validate_release_provenance_migration,
                                             validate_storage_first_documents,
                                             validate_versioned_demo_workspaces,
                                             validate_workspace_lifecycle_migration,
                                             validate_workspace_owner_visibility,
                                             validate_workspace_membership_hardening)

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "supabase/migrations/20260910000100_stage2_storage.sql"
HARDENING_MIGRATION = ROOT / "supabase/migrations/20260910000200_protect_workspace_owner.sql"
PROVENANCE_MIGRATION = ROOT / "supabase/migrations/20260911000100_bind_public_release_provenance.sql"
LIFECYCLE_MIGRATION = ROOT / "supabase/migrations/20260911000200_workspace_lifecycle.sql"
OWNER_VISIBILITY_MIGRATION = ROOT / "supabase/migrations/20260911000300_workspace_owner_visibility.sql"
OWNER_ONLY_MIGRATION = ROOT / "supabase/migrations/20260911000400_owner_only_episode_boundary.sql"
JOURNEY_INVARIANTS_MIGRATION = ROOT / "supabase/migrations/20260911000500_journey_state_invariants.sql"
DEPENDENCY_MIGRATION = ROOT / "supabase/migrations/20260911000600_personal_dependency_invalidation.sql"
DEMO_WORKSPACES_MIGRATION = ROOT / "supabase/migrations/20260911000700_versioned_demo_workspaces.sql"
STORAGE_FIRST_MIGRATION = ROOT / "supabase/migrations/20260911000800_enforce_storage_first_documents.sql"
REMOTE_EVIDENCE = ROOT / "data/supabase/remote-verification.json"
ASSERTION_COVERAGE = ROOT / "data/supabase/stage2-assertion-coverage.json"
STAGE2_TEST = ROOT / "supabase/tests/stage2_security_and_lifecycle.test.sql"
CURRENT_STAGE2_ASSERTIONS = 122
HISTORICAL_REMOTE_ASSERTIONS = 141

MIGRATIONS = (
    MIGRATION,
    HARDENING_MIGRATION,
    PROVENANCE_MIGRATION,
    LIFECYCLE_MIGRATION,
    OWNER_VISIBILITY_MIGRATION,
    OWNER_ONLY_MIGRATION,
    JOURNEY_INVARIANTS_MIGRATION,
    DEPENDENCY_MIGRATION,
    DEMO_WORKSPACES_MIGRATION,
    STORAGE_FIRST_MIGRATION,
)


def _remote_evidence_errors(payload: dict) -> list[str]:
    errors = []
    expected_checks = {
        "stage2_tables": len(STAGE2_TABLES),
        "rls_enabled_tables": len(STAGE2_TABLES),
        "private_medical_document_buckets": 1,
        "vector_extension_enabled": 1,
        "workspace_membership_policies": 1,
        "release_bound_foreign_keys": 8,
        "migration_history_rows": 10,
        "workspace_lifecycle_functions": 6,
        "document_dedup_constraints": 1,
        "workspace_owner_visibility_policies": 1,
        "owner_only_membership_constraints": 1,
        "strict_journey_constraints": 1,
        "normalized_dependency_tables": 5,
        "direct_document_delete_grants": 0,
        # This is immutable historical evidence from the earlier remote run.
        "transactional_pg_tap_assertions": HISTORICAL_REMOTE_ASSERTIONS,
        "temporary_fixture_rows_remaining": 0,
    }
    if payload.get("checks") != expected_checks:
        errors.append("tracked remote verification counts are missing or stale")
    if payload.get("contains_secrets") is not False:
        errors.append("remote verification record must explicitly be secret-free")
    tracked = {item.get("version"): item for item in payload.get("migrations", [])}
    for path in MIGRATIONS:
        version, name = path.stem.split("_", 1)
        item = tracked.get(version)
        # Git may check the same SQL out with LF or CRLF. Hash canonical text so
        # deployment evidence is stable across Windows and Linux clean clones.
        canonical_sql = path.read_text(encoding="utf-8").replace("\r\n", "\n")
        digest = sha256(canonical_sql.encode("utf-8")).hexdigest()
        if not item or item.get("name") != name or item.get("file_sha256") != digest:
            errors.append(f"remote verification does not match {path.name}")
    return errors


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args(argv)
    errors = validate_stage2_migration(MIGRATION)
    errors.extend(validate_workspace_membership_hardening(HARDENING_MIGRATION))
    errors.extend(validate_release_provenance_migration(PROVENANCE_MIGRATION))
    errors.extend(validate_workspace_lifecycle_migration(LIFECYCLE_MIGRATION))
    errors.extend(validate_workspace_owner_visibility(OWNER_VISIBILITY_MIGRATION))
    errors.extend(validate_owner_only_episode_boundary(OWNER_ONLY_MIGRATION))
    errors.extend(validate_journey_state_invariants(JOURNEY_INVARIANTS_MIGRATION))
    errors.extend(validate_personal_dependency_invalidation(DEPENDENCY_MIGRATION))
    errors.extend(validate_versioned_demo_workspaces(DEMO_WORKSPACES_MIGRATION))
    errors.extend(validate_storage_first_documents(STORAGE_FIRST_MIGRATION))
    remote = json.loads(REMOTE_EVIDENCE.read_text(encoding="utf-8"))
    errors.extend(_remote_evidence_errors(remote))
    coverage = json.loads(ASSERTION_COVERAGE.read_text(encoding="utf-8"))
    category_total = sum(item.get("assertions", 0) for item in coverage.get("categories", []))
    later_total = sum(coverage.get("later_stage_suites", {}).values())
    test_sql = STAGE2_TEST.read_text(encoding="utf-8")
    if f"select plan({CURRENT_STAGE2_ASSERTIONS});" not in test_sql.casefold():
        errors.append("current Stage 2 pgTAP suite does not pin plan(122)")
    if (
        coverage.get("current_assertions") != CURRENT_STAGE2_ASSERTIONS
        or category_total != CURRENT_STAGE2_ASSERTIONS
        or coverage.get("historical_remote_reported_assertions")
        != HISTORICAL_REMOTE_ASSERTIONS
        or coverage.get("historical_141_source_available") is not False
        or coverage.get("current_all_stage_assertions")
        != CURRENT_STAGE2_ASSERTIONS + later_total
    ):
        errors.append("Stage 2 assertion coverage reconciliation is stale")
    schema = json.loads((ROOT / "data/schemas/storage.schema.json").read_text(encoding="utf-8"))
    if set(schema.get("database_tables", [])) != STAGE2_TABLES:
        errors.append("exported storage schema table list is stale")
    if set(schema.get("workspace_owned_tables", [])) != USER_OWNED_TABLES:
        errors.append("exported workspace-owned table list is stale")
    result = {
        "valid": not errors,
        "migrations": [str(path.relative_to(ROOT)) for path in MIGRATIONS],
        "tables": len(STAGE2_TABLES),
        "workspace_owned_tables": len(USER_OWNED_TABLES),
        "remote_project": remote["project_name"],
        "remote_verified_at": remote["verified_at"],
        "remote_checks": remote["checks"],
        "assertion_accounting": {
            "current_stage2_assertions": CURRENT_STAGE2_ASSERTIONS,
            "historical_remote_reported_assertions": HISTORICAL_REMOTE_ASSERTIONS,
            "historical_source_available": False,
            "current_all_stage_assertions": coverage["current_all_stage_assertions"],
        },
        "errors": errors,
    }
    if args.write_report:
        report = ROOT / "docs/STAGE-2-CHECK-RESULTS.json"
        report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
