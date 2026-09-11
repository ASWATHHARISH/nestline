"""Static Stage 2 migration checks that run without database credentials."""

import re
from pathlib import Path

from app.schemas.storage import (ADMIN_ONLY_TABLES, PUBLIC_KNOWLEDGE_TABLES,
                                 STAGE2_TABLES, USER_OWNED_TABLES)


def _created_tables(sql: str) -> set[str]:
    return set(re.findall(r"create\s+table\s+public\.([a-z_]+)", sql, re.IGNORECASE))


def _rls_tables(sql: str) -> set[str]:
    return set(re.findall(
        r"alter\s+table\s+public\.([a-z_]+)\s+enable\s+row\s+level\s+security",
        sql, re.IGNORECASE))


def validate_stage2_migration(path: Path) -> list[str]:
    """Check security and architecture invariants before a remote migration runs."""
    sql = path.read_text(encoding="utf-8")
    lowered = sql.casefold()
    errors = []
    created = _created_tables(sql)
    missing = STAGE2_TABLES - created
    extra = created - STAGE2_TABLES
    if missing:
        errors.append("missing Stage 2 tables: " + ", ".join(sorted(missing)))
    if extra:
        errors.append("unexpected Stage 2 tables: " + ", ".join(sorted(extra)))
    without_rls = created - _rls_tables(sql)
    if without_rls:
        errors.append("tables without Row Level Security: " + ", ".join(sorted(without_rls)))

    if "private.is_workspace_member(workspace_id)" not in lowered:
        errors.append("workspace-owned policies do not call the membership boundary")
    policy_section = lowered.split("-- all user-owned records", 1)[-1]
    for table in USER_OWNED_TABLES:
        if f"'{table}'" not in policy_section:
            errors.append(f"{table}: missing workspace-member policy registration")
    if "to anon, authenticated" not in lowered:
        errors.append("published public knowledge has no explicit read grant/policy")
    for table in ADMIN_ONLY_TABLES:
        if re.search(rf"grant\s+[^;]*\b{table}\b[^;]*\bto\s+(anon|authenticated)",
                     lowered, re.DOTALL):
            errors.append(f"{table}: administrative table granted to an API user role")
    for table in PUBLIC_KNOWLEDGE_TABLES - {"source_artifacts"}:
        if table not in lowered:
            errors.append(f"{table}: public knowledge contract absent")

    required_fragments = {
        "pgvector extension": "create extension if not exists vector",
        "private document bucket": "values ('medical-documents', 'medical-documents', false",
        "workspace-filtered private retrieval": "private.is_workspace_member(requested_workspace_id)",
        "published-only public retrieval": "release.status = 'published'",
        "bounded public retrieval": "least(match_count, 20)",
        "document deletion cascade": "references public.private_documents(workspace_id, id) on delete cascade",
        "single current journey state": "journey_states_one_current_per_workspace",
        "plan confirmation gate": "status not in ('saved', 'active') or user_confirmed_at is not null",
        "private storage policy": "bucket_id = 'medical-documents'",
    }
    for label, fragment in required_fragments.items():
        if fragment not in lowered:
            errors.append(f"missing {label}")
    if "using (true)" in lowered or "with check (true)" in lowered:
        errors.append("unrestricted RLS policy found")
    if "service_role" in lowered:
        errors.append("service-role material must not be placed in the migration")
    return errors


def validate_workspace_membership_hardening(path: Path) -> list[str]:
    """Ensure API users cannot create, rewrite, or remove the owner membership."""
    lowered = path.read_text(encoding="utf-8").casefold()
    errors = []
    if 'drop policy if exists "owners manage membership"' not in lowered:
        errors.append("broad workspace membership policy is not removed")
    for operation in ("insert", "update", "delete"):
        if f"for {operation} to authenticated" not in lowered:
            errors.append(f"missing scoped workspace membership {operation} policy")
    if lowered.count("role <> 'owner'") < 4:
        errors.append("owner membership is not protected in every mutation policy")
    if "using (true)" in lowered or "with check (true)" in lowered:
        errors.append("unrestricted workspace membership policy found")
    return errors


def validate_release_provenance_migration(path: Path) -> list[str]:
    """Check that stable ingestion identifiers are scoped to one content release."""
    lowered = path.read_text(encoding="utf-8").casefold()
    errors = []
    required = {
        "source identity is release-scoped":
            "primary key (release_id, source_id)",
        "source blocks are release-scoped":
            "primary key (release_id, block_id)",
        "ingestion runs are release-scoped":
            "primary key (release_id, run_id)",
        "review tasks are release-scoped":
            "primary key (release_id, task_id)",
        "artifact provenance is composite":
            "foreign key (release_id, source_id, source_artifact_id)",
        "review-run provenance is composite":
            "foreign key (release_id, source_id, run_id)",
        "review-decision provenance is composite":
            "foreign key (release_id, task_id)",
    }
    for label, fragment in required.items():
        if fragment not in lowered:
            errors.append(f"missing {label}")
    return errors


def validate_workspace_lifecycle_migration(path: Path) -> list[str]:
    """Check authenticated creation, atomic state replacement and safe demo reset."""
    lowered = path.read_text(encoding="utf-8").casefold()
    errors = []
    required = {
        "duplicate document protection":
            "unique (workspace_id, sha256)",
        "authenticated workspace ownership":
            "values (auth.uid(), requested_mode, requested_display_name)",
        "journey compare-and-set":
            "current_version <> expected_current_version",
        "atomic journey lock":
            "where id = requested_workspace_id\n  for update",
        "demo owner gate":
            "not private.is_workspace_owner(requested_workspace_id)",
        "storage deletion gate":
            "remove workspace files through the storage api before database reset",
        "authenticated-only function grant":
            "to authenticated",
    }
    for label, fragment in required.items():
        if fragment not in lowered:
            errors.append(f"missing {label}")
    if "service_role" in lowered:
        errors.append("workspace lifecycle must not depend on a service-role client")
    return errors


def validate_workspace_owner_visibility(path: Path) -> list[str]:
    """Keep INSERT ... RETURNING usable before the membership trigger completes."""
    lowered = path.read_text(encoding="utf-8").casefold()
    errors = []
    if 'drop policy if exists "members read workspaces"' not in lowered:
        errors.append("old workspace read policy is not replaced")
    if "owner_user_id = auth.uid()" not in lowered:
        errors.append("workspace owner is not visible during authenticated creation")
    if "or private.is_workspace_member(id)" not in lowered:
        errors.append("workspace member read access was not preserved")
    return errors


def validate_owner_only_episode_boundary(path: Path) -> list[str]:
    """Check the explicit owner-only and one-workspace-one-episode decision."""
    lowered = path.read_text(encoding="utf-8").casefold()
    errors = []
    required = {
        "non-owner upgrade guard": "where role <> 'owner'",
        "owner-only role constraint": "workspace_members_owner_only check (role = 'owner')",
        "membership mutation grants removed":
            "revoke insert, update, delete on public.workspace_members from authenticated",
        "owner identity in access boundary": "workspace.owner_user_id = auth.uid()",
        "owner role in access boundary": "member.role = 'owner'",
        "care episode decision": "one private care episode per workspace",
    }
    for label, fragment in required.items():
        if fragment not in lowered:
            errors.append(f"missing {label}")
    return errors


def validate_journey_state_invariants(path: Path) -> list[str]:
    """Check strict stage/source combinations at the database boundary."""
    lowered = path.read_text(encoding="utf-8").casefold()
    errors = []
    required = {
        "possible pregnancy source": "user_reported_possible_pregnancy",
        "strict timing constraint": "journey_states_stage_timing_check",
        "pregnancy due date source":
            "timing_source in ('document_estimated_due_date', 'user_estimated_due_date')",
        "approximate range source": "timing_source = 'approximate_month_range'",
        "postpartum delivery source":
            "timing_source = 'delivery_date' and delivery_date is not null",
        "postpartum day range": "check (postpartum_day between 0 and 6)",
    }
    for label, fragment in required.items():
        if fragment not in lowered:
            errors.append(f"missing {label}")
    return errors


def validate_personal_dependency_invalidation(path: Path) -> list[str]:
    """Check normalized links, graph validation and stale-state transitions."""
    lowered = path.read_text(encoding="utf-8").casefold()
    errors = []
    required = {
        "journey fact map": "private.journey_state_fact_dependencies",
        "question fact map": "private.appointment_question_fact_dependencies",
        "plan fact map": "private.plan_item_fact_dependencies",
        "plan guidance map": "private.plan_item_guidance_dependencies",
        "plan evidence map": "private.plan_item_evidence_dependencies",
        "workspace-scoped fact key":
            "references public.health_facts(workspace_id, id) on delete restrict",
        "plan stale transition": "set status = 'stale'",
        "question stale transition": "set status = 'stale'",
        "journey conflict transition": "set has_dating_conflict = true",
        "graph entity validation": "graph_nodes_validate_entity",
        "storage-first document deletion":
            "remove the document through the storage api before deleting its database record",
    }
    for label, fragment in required.items():
        if fragment not in lowered:
            errors.append(f"missing {label}")
    return errors


def validate_versioned_demo_workspaces(path: Path) -> list[str]:
    """Check per-session, versioned and repeatable fictional workspace seeding."""
    lowered = path.read_text(encoding="utf-8").casefold()
    errors = []
    required = {
        "session identity": "demo_session_key text",
        "seed identity": "demo_seed_version text",
        "owner/session uniqueness": "workspaces_owner_demo_session_key",
        "versioned seed": "requested_seed_version <> 'maya-v1'",
        "per-session clone": "public.create_demo_workspace",
        "reset and reseed": "public.reseed_demo_workspace_state",
        "existing reset reuse": "public.reset_demo_workspace_state",
    }
    for label, fragment in required.items():
        if fragment not in lowered:
            errors.append(f"missing {label}")
    return errors


def validate_storage_first_documents(path: Path) -> list[str]:
    """Check that clients cannot bypass Storage-first document deletion."""
    lowered = path.read_text(encoding="utf-8").casefold()
    errors = []
    required = {
        "broad document policy removed":
            'drop policy if exists "workspace members manage private_documents"',
        "direct document delete revoked":
            "revoke delete on public.private_documents from authenticated",
        "owner-checked delete function":
            "not private.is_workspace_owner(requested_workspace_id)",
        "storage existence gate":
            "remove the document through the storage api before deleting its database record",
        "protected reset rights":
            "alter function public.reset_demo_workspace_state(uuid, timestamptz) security definer",
    }
    for label, fragment in required.items():
        if fragment not in lowered:
            errors.append(f"missing {label}")
    if "create policy" in lowered and "for delete to authenticated" in lowered:
        errors.append("direct authenticated document delete policy found")
    return errors
