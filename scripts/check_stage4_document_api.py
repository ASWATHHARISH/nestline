"""Exercise Stage 4 through real local Auth, Storage, PostgREST, and RPC calls.

Only conspicuously fictional fixtures are used. Temporary users, workspaces, and
objects are removed before success is reported. No credential or document body
is printed.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

from app.schemas.documents import ConfirmationDecision, DocumentReviewRequest
from app.services.onboarding import SupabaseAuthClient, SupabaseOnboardingGateway
from app.services.personal_documents import (
    FictionalFixtureScanner,
    SupabaseDocumentGateway,
    extract_fixture_candidates,
    load_fictional_fixture_registry,
    parse_document,
    validate_upload,
)
from scripts.check_stage2_storage_api import LocalSupabase, _expect_denied, _expect_success


ROOT = Path(__file__).resolve().parents[1]


def _decisions(candidates: list[dict]) -> list[ConfirmationDecision]:
    result = []
    for item in candidates:
        if item["disposition"] == "abstain":
            action = "reject"
        elif item.get("conflict_document_keys"):
            action = "keep_conflict"
        else:
            action = "confirm"
        result.append(ConfirmationDecision(
            candidate_key=item["candidate_key"], action=action
        ))
    return result


def _process_fixture(
    gateway: SupabaseDocumentGateway,
    workspace_id,
    document_key: str,
):
    fixture = next(
        item
        for item in load_fictional_fixture_registry()
        if item.fixture_id == document_key
    )
    path = fixture.path
    data = path.read_bytes()
    scanner = FictionalFixtureScanner(frozenset({fixture.sha256}))
    validation = validate_upload(
        data,
        filename=path.name,
        claimed_media_type=fixture.media_type,
        scanner=scanner,
    )
    pages, fitz_pages = parse_document(data, media_type=validation.media_type)
    packet = extract_fixture_candidates(
        pages, document_sha256=validation.sha256, fitz_pages=fitz_pages
    )
    validation = validate_upload(
        data,
        filename=path.name,
        claimed_media_type=fixture.media_type,
        scanner=scanner,
        expected_subject=fixture.expected_subject,
        subject_as_written=packet.subject_as_written,
        fixture_bound_subject=fixture.expected_subject,
    )
    document_id, created = gateway.upload_and_register(workspace_id, validation, data)
    review_version = gateway.record_extraction(
        workspace_id, document_id, validation, packet
    )
    candidates = gateway.list_candidates(workspace_id, document_id)
    return path, validation, document_id, created, review_version, candidates


def main() -> int:
    local = LocalSupabase()
    marker = uuid4().hex
    password = f"Nestline-{uuid4().hex}-A1!"
    emails = [
        f"stage4-owner-{marker}@example.invalid",
        f"stage4-other-{marker}@example.invalid",
    ]
    user_ids: list[str] = []
    object_paths: list[str] = []
    workspace_id = None
    checks = 0
    try:
        for email in emails:
            status, raw = local.request(
                "POST", "/auth/v1/admin/users", key=local.service_key,
                json_body={"email": email, "password": password, "email_confirm": True},
            )
            _expect_success(status, "temporary Stage 4 user creation")
            user_ids.append(local.json(raw)["id"])
        auth = SupabaseAuthClient(local.url, local.anon_key)
        owner_session = auth.sign_in(emails[0], password)
        other_session = auth.sign_in(emails[1], password)
        checks += 1

        onboarding = SupabaseOnboardingGateway(
            local.url, local.anon_key, owner_session.access_token
        )
        workspace_id = onboarding.create_demo_workspace(
            f"stage4-{marker}", "Maya Stage 4 API fixture"
        )
        checks += 1
        owner = SupabaseDocumentGateway(
            local.url, local.anon_key, owner_session.access_token
        )
        other = SupabaseDocumentGateway(
            local.url, local.anon_key, other_session.access_token
        )

        _, first_validation, first_id, created, version, candidates = _process_fixture(
            owner, workspace_id, "DOC-005"
        )
        object_paths.append(
            f"{workspace_id}/{first_validation.sha256}/{first_validation.safe_filename}"
        )
        if not created or version != 1 or len(candidates) != 2:
            raise AssertionError("DOC-005 did not reach one complete proposal set")
        checks += 1

        status, raw = local.request(
            "GET",
            f"/rest/v1/health_facts?workspace_id=eq.{workspace_id}&source_document_id=eq.{first_id}&select=id",
            key=local.anon_key,
            token=owner_session.access_token,
        )
        _expect_success(status, "pre-confirmation fact lookup")
        if local.json(raw) != []:
            raise AssertionError("proposal affected confirmed personal state")
        checks += 1

        first_request = DocumentReviewRequest(
            workspace_id=workspace_id,
            document_id=first_id,
            expected_review_version=version,
            submission_key=f"stage4-api-doc5-{marker}",
            decisions=_decisions(candidates),
        )
        first_result = owner.commit_review(first_request)
        if len(first_result.confirmed_fact_ids) != 2 or first_result.idempotent_replay:
            raise AssertionError("DOC-005 review did not create two confirmed facts")
        checks += 1
        if not owner.commit_review(first_request).idempotent_replay:
            raise AssertionError("review replay was not idempotent")
        checks += 1
        duplicate_id, duplicate_created = owner.upload_and_register(
            workspace_id, first_validation,
            (ROOT / "data/synthetic/documents/DOC-005.pdf").read_bytes(),
        )
        if duplicate_id != first_id or duplicate_created:
            raise AssertionError("duplicate upload created a second logical document")
        checks += 1

        status, _ = local.request(
            "PATCH", f"/rest/v1/document_facts?document_id=eq.{first_id}",
            key=local.anon_key, token=owner_session.access_token,
            json_body={"status": "confirmed"},
        )
        _expect_denied(status, "direct proposal mutation")
        checks += 1
        if other.list_candidates(workspace_id, first_id):
            raise AssertionError("other user discovered document candidates")
        checks += 1

        _, second_validation, second_id, created, version, candidates = _process_fixture(
            owner, workspace_id, "DOC-006"
        )
        object_paths.append(
            f"{workspace_id}/{second_validation.sha256}/{second_validation.safe_filename}"
        )
        if not created or version != 1 or len(candidates) != 3:
            raise AssertionError("DOC-006 did not reach its expected proposal set")
        checks += 1
        second_result = owner.commit_review(DocumentReviewRequest(
            workspace_id=workspace_id,
            document_id=second_id,
            expected_review_version=version,
            submission_key=f"stage4-api-doc6-{marker}",
            decisions=_decisions(candidates),
        ))
        if len(second_result.conflict_fact_ids) != 1:
            raise AssertionError("declared DOC-006 conflict was not preserved")
        checks += 1

        for table, expected_minimum in (
            ("health_facts", 1),
            ("graph_edges", 1),
            ("appointment_questions", 1),
        ):
            status, raw = local.request(
                "GET",
                f"/rest/v1/{table}?workspace_id=eq.{workspace_id}&select=id",
                key=local.anon_key,
                token=owner_session.access_token,
            )
            _expect_success(status, f"{table} owner lookup")
            if len(local.json(raw)) < expected_minimum:
                raise AssertionError(f"{table} did not contain the confirmed graph state")
            checks += 1

        status, raw = local.request(
            "GET",
            f"/rest/v1/document_chunks?document_id=eq.{second_id}&source_text=not.is.null&select=id",
            key=local.anon_key,
            token=owner_session.access_token,
        )
        # `source_text` is intentionally invalid for chunks; a successful broad
        # query below proves the injected line is private without logging it.
        if 200 <= status < 300:
            raise AssertionError("unexpected document_chunks source_text column exists")
        status, raw = local.request(
            "GET", f"/rest/v1/document_chunks?document_id=eq.{second_id}&select=id,text",
            key=local.anon_key, token=owner_session.access_token,
        )
        _expect_success(status, "owner private chunk lookup")
        if len(local.json(raw)) != 1:
            raise AssertionError("DOC-006 text did not remain one private chunk")
        checks += 1

    finally:
        for object_path in object_paths:
            status, _ = local.request(
                "DELETE", "/storage/v1/object/medical-documents",
                key=local.service_key, json_body={"prefixes": [object_path]},
            )
            _expect_success(status, "Stage 4 Storage cleanup")
        if workspace_id:
            status, _ = local.request(
                "DELETE", f"/rest/v1/workspaces?id=eq.{quote(str(workspace_id))}",
                key=local.service_key,
            )
            _expect_success(status, "Stage 4 workspace cleanup")
        for user_id in user_ids:
            status, _ = local.request(
                "DELETE", f"/auth/v1/admin/users/{quote(user_id)}",
                key=local.service_key,
            )
            _expect_success(status, "Stage 4 user cleanup")

    print(f'{{"valid": true, "checks": {checks}, "mode": "fictional_local_api"}}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
