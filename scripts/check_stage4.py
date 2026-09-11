"""Verify Stage 4 contracts, fixtures, migration, UI, and release boundaries."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

from app.services.stage4_validation import (
    validate_document_service,
    validate_openai_adapter,
    validate_stage4_api_role_hardening,
    validate_stage4_migration,
)
from scripts.export_document_schema import build_payload


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/synthetic"
MIGRATION = ROOT / "supabase/migrations/20260911001100_stage4_document_confirmation.sql"
API_ROLE_HARDENING = ROOT / "supabase/migrations/20260911001200_stage4_api_role_hardening.sql"
SERVICE = ROOT / "app/services/personal_documents.py"
OPENAI = ROOT / "app/services/openai_document_extractor.py"
SCHEMA = ROOT / "data/schemas/document.schema.json"
REPORT = ROOT / "docs/STAGE-4-CHECK-RESULTS.json"
REMOTE_EVIDENCE = ROOT / "data/supabase/stage4-remote-verification.json"
FIXTURE_REGISTRY = BASE / "stage4_fixture_registry.json"


def _digest(path: Path) -> str:
    data = path.read_bytes()
    if path.suffix.casefold() == ".sql":
        # Git may materialise SQL with CRLF on Windows. Migration identity is
        # based on canonical LF bytes so the same commit verifies everywhere.
        data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return sha256(data).hexdigest()


def _remote_errors(payload: dict) -> list[str]:
    """Bind tracked remote proof to this exact migration pair and release gate."""
    errors: list[str] = []
    expected_checks = {
        "migration_history_rows": 14,
        "pending_migrations": 0,
        "stage4_document_migration_rows": 1,
        "stage4_api_hardening_migration_rows": 1,
        "document_review_commit_tables": 1,
        "record_extraction_functions": 1,
        "commit_review_functions": 1,
        "authenticated_stage4_execute_grants": 2,
        "direct_candidate_mutation_grants": 0,
        "anon_table_grants": 6,
        "anon_non_select_table_grants": 0,
        "anon_non_public_knowledge_grants": 0,
        "anon_executable_public_functions": 1,
        "anon_private_retrieval_execute": 0,
        "postgres_anonymous_default_acls": 0,
        "stage2_pg_tap_assertions": 122,
        "stage3_exit_hardening_pg_tap_assertions": 12,
        "stage3_onboarding_pg_tap_assertions": 26,
        "stage4_document_pg_tap_assertions": 35,
        "stage4_api_role_pg_tap_assertions": 11,
        "transactional_pg_tap_assertions": 206,
        "database_lint_findings": 0,
        "application_role_drift_statements": 0,
        "application_functions_compared": 9,
        "application_function_semantic_mismatches": 0,
        "temporary_fixture_rows_remaining": 0,
        "remote_personal_workspace_rows": 0,
        "anonymous_public_content_http_status": 200,
        "anonymous_personal_workspace_http_status": 401,
        "anonymous_api_boundary_checks": 2,
    }
    if payload.get("checks") != expected_checks:
        errors.append("tracked Stage 4 remote verification counts are missing or stale")
    if payload.get("project_ref") != "jtmiduftpbvmahbmryki":
        errors.append("Stage 4 remote verification targets the wrong project")
    if payload.get("application_schema_semantically_aligned") is not True:
        errors.append("Stage 4 application schema is not semantically aligned remotely")
    if payload.get("contains_secrets") is not False:
        errors.append("Stage 4 remote verification must explicitly be secret-free")

    expected_migrations = {
        "20260911001100": ("stage4_document_confirmation", _digest(MIGRATION)),
        "20260911001200": ("stage4_api_role_hardening", _digest(API_ROLE_HARDENING)),
    }
    observed = {
        item.get("version"): (item.get("name"), item.get("file_sha256"))
        for item in payload.get("migrations", [])
        if isinstance(item, dict)
    }
    if observed != expected_migrations:
        errors.append("Stage 4 remote verification does not match the migration files")
    return errors

def run(skip_remote: bool = False) -> dict:
    errors: list[str] = []
    errors.extend(validate_stage4_migration(MIGRATION))
    errors.extend(validate_stage4_api_role_hardening(API_ROLE_HARDENING))
    errors.extend(validate_document_service(SERVICE))
    errors.extend(validate_openai_adapter(OPENAI))

    expected_pg_tap_plans = {
        "stage2_security_and_lifecycle.test.sql": 122,
        "stage3_exit_hardening.test.sql": 12,
        "stage3_onboarding.test.sql": 26,
        "stage4_api_role_hardening.test.sql": 11,
        "stage4_document_confirmation.test.sql": 35,
    }
    for filename, expected in expected_pg_tap_plans.items():
        sql = (ROOT / "supabase/tests" / filename).read_text(encoding="utf-8")
        if f"select plan({expected});" not in sql.casefold():
            errors.append(f"{filename}: expected pgTAP plan({expected}) is not pinned")
    if sum(expected_pg_tap_plans.values()) != 206:
        errors.append("pinned pgTAP plans do not total 206")
    tracked_schema = json.loads(SCHEMA.read_text(encoding="utf-8")) if SCHEMA.exists() else None
    if tracked_schema != build_payload():
        errors.append("tracked Stage 4 document JSON Schema is stale")

    graph_types = {
        "Person", "JourneyState", "WeeklyProfile", "Document", "DocumentFact",
        "MedicationMention", "Allergy", "Condition", "SymptomEvent", "Appointment",
        "Plan", "PlanItem", "GuidelineEvidence", "Question", "HumanReviewCase",
    }
    edge_types = {
        "IN_WEEK", "EXTRACTED_FROM", "CONFLICTS_WITH", "SUPERSEDES", "CONSTRAINS",
        "SUPPORTED_BY", "TRIGGERED", "SCHEDULED_FOR", "NEEDS_CLARIFICATION", "REVIEWED_BY",
    }
    graph_files = sorted((BASE / "expected_graph_changes").glob("DOC-*.json"))
    if len(graph_files) != 8:
        errors.append("typed graph truth must contain exactly eight document files")
    graph_nodes = graph_edges = 0
    for path in graph_files:
        value = json.loads(path.read_text(encoding="utf-8"))
        if value.get("schema_version") != "stage4-graph-truth-v1":
            errors.append(f"{path.name}: graph schema version is wrong")
        if value.get("proposal_side_effects") != []:
            errors.append(f"{path.name}: an extraction proposal has graph side effects")
        for node in value.get("nodes", []):
            if node.get("type") not in graph_types:
                errors.append(f"{path.name}: unknown graph node type {node.get('type')}")
            graph_nodes += 1
        for edge in value.get("edges", []):
            if edge.get("type") not in edge_types:
                errors.append(f"{path.name}: unknown graph edge type {edge.get('type')}")
            graph_edges += 1

    noisy_image = BASE / "noisy_variants/DOC-003-noisy.png"
    noisy_truth_path = BASE / "noisy_variants/DOC-003-noisy.expected.json"
    if not noisy_image.exists() or not noisy_truth_path.exists():
        errors.append("controlled noisy/OCR fixture is missing")
        noisy_fields = 0
    else:
        noisy_truth = json.loads(noisy_truth_path.read_text(encoding="utf-8"))
        if noisy_truth.get("image_sha256") != _digest(noisy_image):
            errors.append("controlled noisy/OCR fixture checksum is stale")
        if noisy_truth.get("minimum_exact_field_recall") != 1.0:
            errors.append("controlled OCR truth does not require exact canonical field recall")
        noisy_fields = len(noisy_truth.get("expected_fields", []))

    fixture_registry = json.loads(FIXTURE_REGISTRY.read_text(encoding="utf-8"))
    registered_fixtures = fixture_registry.get("fixtures", [])
    if fixture_registry.get("public_demo_upload") is not False:
        errors.append("arbitrary public demo upload must remain disabled")
    if len(registered_fixtures) != 9:
        errors.append("fictional fixture registry must contain exactly nine entries")
    for item in registered_fixtures:
        fixture_path = ROOT / item.get("relative_path", "")
        if (
            not fixture_path.is_file()
            or _digest(fixture_path) != item.get("sha256")
            or item.get("expected_subject") != "Maya - fictional demo persona"
        ):
            errors.append(f"fictional fixture registry entry is invalid: {item.get('id')}")
    edge_manifest_path = BASE / "upload_edge_cases/manifest.json"
    edge_case_ids: set[str] = set()
    if not edge_manifest_path.exists():
        errors.append("upload edge-case manifest is missing")
    else:
        edge_manifest = json.loads(edge_manifest_path.read_text(encoding="utf-8"))
        edge_case_ids = {item.get("id") for item in edge_manifest.get("cases", [])}
        expected = {"locked", "corrupt", "unsupported", "oversize", "wrong_person"}
        if edge_case_ids != expected:
            errors.append("upload edge-case pack is incomplete")
        for item in edge_manifest.get("files", []):
            path = BASE / "upload_edge_cases" / item["filename"]
            if not path.exists() or _digest(path) != item["sha256"]:
                errors.append(f"upload edge fixture checksum is stale: {item['filename']}")

    ui = (ROOT / "app/pages_and_components/documents.py").read_text(encoding="utf-8")
    for fragment in (
        "NESTLINE_ENABLE_STAGE4_FIXTURE_DEMO", "Arbitrary uploads are disabled",
        "Review every extracted field",
        "No review choice is preselected", "character span", "confidence",
        "completeness", "extraction disposition", "I reviewed every field",
        "unresolved conflict",
    ):
        if fragment.casefold() not in ui.casefold():
            errors.append(f"Stage 4 UI is missing: {fragment}")
    if "st.file_uploader" in ui:
        errors.append("Stage 4 public demo still exposes an arbitrary file uploader")
    if ui.count("index=None") < 2:
        errors.append("Stage 4 selector and review decisions must have no default")
    if "render_document_panel" not in (
        ROOT / "app/pages_and_components/onboarding.py"
    ).read_text(encoding="utf-8"):
        errors.append("Stage 4 UI is not integrated into the authenticated workspace")

    env_example = (ROOT / ".env.example").read_text(encoding="utf-8")
    if "NESTLINE_ENABLE_STAGE4_FIXTURE_DEMO=false" not in env_example:
        errors.append("Stage 4 fixture feature must default off in .env.example")
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    if "Pillow==12.3.0" not in requirements:
        errors.append("controlled OCR image dependency is not pinned")

    remote = None
    if not skip_remote:
        if not REMOTE_EVIDENCE.exists():
            errors.append("Stage 4 remote verification evidence is missing")
        else:
            remote = json.loads(REMOTE_EVIDENCE.read_text(encoding="utf-8"))
            errors.extend(_remote_errors(remote))

    result = {
        "valid": not errors,
        "stage": 4,
        "fictional_demo_engineering_complete": not errors,
        "ready_for_stage5_engineering": not errors,
        "ready_for_live_or_public_medical_upload": False,
        "remote_project": remote.get("project_name") if remote else None,
        "remote_verified_at": remote.get("verified_at") if remote else None,
        "remote_checks": remote.get("checks") if remote else None,
        "verified": {
            "canonical_documents": 8,
            "typed_graph_truth_files": len(graph_files),
            "typed_graph_nodes": graph_nodes,
            "typed_graph_edges": graph_edges,
            "controlled_ocr_expected_fields": noisy_fields,
            "registered_exact_hash_fixtures": len(registered_fixtures),
            "pinned_pg_tap_assertions": sum(expected_pg_tap_plans.values()),
            "upload_edge_cases": sorted(edge_case_ids),
            "migration_sha256": _digest(MIGRATION),
            "api_role_hardening_sha256": _digest(API_ROLE_HARDENING),
        },
        "implemented_boundaries": [
            "format, size, signature, lock, corruption, exact-fixture, and fail-closed identity validation",
            "document feature defaults off; supervised demos can select only nine repository-owned fixture hashes",
            "visible page/span/coordinate/confidence/completeness/disposition provenance",
            "proposal-only extraction with unselected explicit edit, confirm, reject, conflict and supersede actions",
            "atomic idempotent versioned commit with graph updates and movement-plan invalidation",
            "owner-only derived-state mutation and duplicate upload deduplication",
            "optional tool-free, store-disabled OpenAI Structured Outputs adapter",
        ],
        "parked_release_gates": [
            "deployable malware scanner for real medical documents",
            "exact candidate extraction models and cost ceiling followed by live fictional benchmark",
            "qualified clinical and India-localisation approval",
            "final rendered product acceptance",
        ],
        "errors": errors,
    }
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--skip-remote", action="store_true")
    args = parser.parse_args(argv)
    result = run(skip_remote=args.skip_remote)
    if args.write_report:
        REPORT.write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n"
        )
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
