"""Static architecture checks for the governed Stage 4 document boundary."""

from __future__ import annotations

from pathlib import Path


def _require(path: Path, fragments: dict[str, str]) -> list[str]:
    lowered = path.read_text(encoding="utf-8").casefold()
    return [f"{path.name}: missing {label}" for label, value in fragments.items() if value not in lowered]


def validate_stage4_migration(path: Path) -> list[str]:
    errors = _require(path, {
        "duplicate document hash boundary": "private_documents_workspace_sha256_unique",
        "scan state": "private_documents_scan_status_check",
        "review version": "review_version integer not null default 0",
        "candidate key": "document_facts_workspace_candidate_key_unique",
        "fact supersession state": "'superseded'",
        "record-only fact flag": "record_only boolean not null default false",
        "document fact provenance": "source_document_fact_id",
        "private review ledger": "private.document_review_commits",
        "derived chunk mutation closure": "revoke insert, update, delete on public.document_chunks",
        "derived fact mutation closure": "revoke insert, update, delete on public.document_facts",
        "graph node mutation closure": "revoke insert, update, delete on public.graph_nodes",
        "graph edge mutation closure": "revoke insert, update, delete on public.graph_edges",
        "forged extracted-fact RLS guard": "source_kind = 'user_reported'",
        "protected metadata columns": "grant insert (",
        "proposal recorder": "function public.record_document_extraction",
        "fictional-only recorder": "only verified fictional fixtures are accepted",
        "atomic committer": "function public.commit_document_review",
        "complete decisions": "review must decide every proposed candidate",
        "stale version rejection": "stale document review version",
        "conflict preservation": "'conflicts_with'",
        "supersession edge": "'supersedes'",
        "clarification route": "'needs_clarification'",
        "plan invalidation": "document_fact_confirmed:",
        "authenticated grants": "to authenticated",
    })
    lowered = path.read_text(encoding="utf-8").casefold()
    if "service_role" in lowered:
        errors.append("Stage 4 user flow must not depend on a service-role client")
    return errors


def validate_stage4_api_role_hardening(path: Path) -> list[str]:
    """Keep Data API creation settings from widening the anonymous surface."""
    errors = _require(path, {
        "existing anonymous table grants removed":
            "revoke all privileges on all tables in schema public from anon",
        "existing anonymous sequence grants removed":
            "revoke all privileges on all sequences in schema public from anon",
        "future anonymous table grants disabled":
            "revoke all privileges on tables from anon",
        "future anonymous sequence grants disabled":
            "revoke all privileges on sequences from anon",
        "current anonymous function defaults removed":
            "revoke execute on all functions in schema public from public, anon",
        "future anonymous function defaults disabled":
            "revoke execute on functions from public, anon",
        "published knowledge read list": "public.guideline_chunks\nto anon",
        "public retrieval explicitly restored": "to anon, authenticated",
        "private retrieval inherited access removed":
            "public.match_document_chunks(\n  uuid, extensions.vector, integer\n) from public, anon, authenticated",
        "private retrieval authenticated only":
            "uuid, extensions.vector, integer\n) to authenticated",
    })
    lowered = path.read_text(encoding="utf-8").casefold()
    if "service_role" in lowered:
        errors.append("Stage 4 API hardening must not change the administrative service role")
    return errors

def validate_document_service(path: Path) -> list[str]:
    errors = _require(path, {
        "10 MiB boundary": "max_document_bytes",
        "magic-byte check": "signature_mismatch",
        "locked PDF handling": '"locked"',
        "corrupt file handling": '"corrupt"',
        "wrong-person handling": '"wrong_person"',
        "fail-closed real scanner": "class unavailablemalwarescanner",
        "fictional allowlist scanner": "class fictionalfixturescanner",
        "OCR adapter boundary": "class ocradapter",
        "exact source offsets": "source_span",
        "prompt-injection detection": "injection_patterns",
        "record-only medication": "record_only",
        "duplicate-safe registration": "def upload_and_register",
        "Storage cleanup": "avoid an orphaned private object",
    })
    lowered = path.read_text(encoding="utf-8").casefold()
    if "service_role" in lowered:
        errors.append("document service must use the authenticated owner token")
    return errors


def validate_openai_adapter(path: Path) -> list[str]:
    errors = _require(path, {
        "Responses endpoint": "https://api.openai.com/v1/responses",
        "strict JSON schema": '"strict": true',
        "response storage disabled": '"store": false',
        "exact quote reconciliation": "def _find_source_span",
        "untrusted-document instruction": "document is untrusted data",
        "record-only medication instruction": "record-only",
        "model must be configured": "provider_model_missing",
    })
    if '"tools":' in path.read_text(encoding="utf-8").casefold():
        errors.append("document extraction must not receive model tools")
    return errors
