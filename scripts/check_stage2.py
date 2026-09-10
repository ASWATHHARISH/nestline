"""Verify Stage 2 contracts, migrations and tracked remote evidence without secrets."""

import argparse
from hashlib import sha256
import json
from pathlib import Path

from app.schemas.storage import STAGE2_TABLES, USER_OWNED_TABLES
from app.services.storage_validation import (validate_stage2_migration,
                                             validate_release_provenance_migration,
                                             validate_workspace_lifecycle_migration,
                                             validate_workspace_owner_visibility,
                                             validate_workspace_membership_hardening)

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "supabase/migrations/20260910000100_stage2_storage.sql"
HARDENING_MIGRATION = ROOT / "supabase/migrations/20260910000200_protect_workspace_owner.sql"
PROVENANCE_MIGRATION = ROOT / "supabase/migrations/20260911000100_bind_public_release_provenance.sql"
LIFECYCLE_MIGRATION = ROOT / "supabase/migrations/20260911000200_workspace_lifecycle.sql"
OWNER_VISIBILITY_MIGRATION = ROOT / "supabase/migrations/20260911000300_workspace_owner_visibility.sql"
REMOTE_EVIDENCE = ROOT / "data/supabase/remote-verification.json"


def _remote_evidence_errors(payload: dict) -> list[str]:
    errors = []
    expected_checks = {
        "stage2_tables": len(STAGE2_TABLES),
        "rls_enabled_tables": len(STAGE2_TABLES),
        "private_medical_document_buckets": 1,
        "vector_extension_enabled": 1,
        "workspace_membership_policies": 4,
        "release_bound_foreign_keys": 8,
        "migration_history_rows": 5,
        "workspace_lifecycle_functions": 3,
        "document_dedup_constraints": 1,
        "workspace_owner_visibility_policies": 1,
        "transactional_isolation_assertions": 9,
        "transactional_lifecycle_assertions": 5,
        "temporary_fixture_rows_remaining": 0,
    }
    if payload.get("checks") != expected_checks:
        errors.append("tracked remote verification counts are missing or stale")
    if payload.get("contains_secrets") is not False:
        errors.append("remote verification record must explicitly be secret-free")
    tracked = {item.get("version"): item for item in payload.get("migrations", [])}
    for path in (MIGRATION, HARDENING_MIGRATION, PROVENANCE_MIGRATION,
                 LIFECYCLE_MIGRATION, OWNER_VISIBILITY_MIGRATION):
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
    remote = json.loads(REMOTE_EVIDENCE.read_text(encoding="utf-8"))
    errors.extend(_remote_evidence_errors(remote))
    schema = json.loads((ROOT / "data/schemas/storage.schema.json").read_text(encoding="utf-8"))
    if set(schema.get("database_tables", [])) != STAGE2_TABLES:
        errors.append("exported storage schema table list is stale")
    if set(schema.get("workspace_owned_tables", [])) != USER_OWNED_TABLES:
        errors.append("exported workspace-owned table list is stale")
    result = {
        "valid": not errors,
        "migrations": [str(MIGRATION.relative_to(ROOT)),
                       str(HARDENING_MIGRATION.relative_to(ROOT)),
                       str(PROVENANCE_MIGRATION.relative_to(ROOT)),
                       str(LIFECYCLE_MIGRATION.relative_to(ROOT)),
                       str(OWNER_VISIBILITY_MIGRATION.relative_to(ROOT))],
        "tables": len(STAGE2_TABLES),
        "workspace_owned_tables": len(USER_OWNED_TABLES),
        "remote_project": remote["project_name"],
        "remote_verified_at": remote["verified_at"],
        "remote_checks": remote["checks"],
        "errors": errors,
    }
    if args.write_report:
        report = ROOT / "docs/STAGE-2-CHECK-RESULTS.json"
        report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
