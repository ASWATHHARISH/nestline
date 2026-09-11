"""Exercise local Supabase Storage with two temporary authenticated users.

This check is intentionally local-only. It uses the local service-role key for
fixture creation and cleanup, while every product operation uses a real user JWT.
No key, token, email, object body or medical-looking content is printed.
"""

from __future__ import annotations

import json
import os
from pathlib import PurePosixPath
from typing import Any
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen
from uuid import uuid4


def _required_environment(*names: str) -> str:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    raise RuntimeError(f"Missing local Supabase setting: {' or '.join(names)}")


class LocalSupabase:
    def __init__(self) -> None:
        self.url = _required_environment("API_URL", "SUPABASE_URL").rstrip("/")
        self.anon_key = _required_environment("ANON_KEY", "SUPABASE_ANON_KEY")
        self.service_key = _required_environment("SERVICE_ROLE_KEY", "SUPABASE_SERVICE_ROLE_KEY")

    def request(
        self,
        method: str,
        path: str,
        *,
        key: str,
        token: str | None = None,
        json_body: Any | None = None,
        raw_body: bytes | None = None,
        content_type: str = "application/json",
        extra_headers: dict[str, str] | None = None,
    ) -> tuple[int, bytes]:
        if json_body is not None and raw_body is not None:
            raise ValueError("request accepts JSON or raw bytes, not both")
        body = json.dumps(json_body).encode() if json_body is not None else raw_body
        headers = {
            "apikey": key,
            "Authorization": f"Bearer {token or key}",
            "Content-Type": content_type,
        }
        headers.update(extra_headers or {})
        request = Request(f"{self.url}{path}", data=body, method=method, headers=headers)
        try:
            with urlopen(request, timeout=20) as response:
                return response.status, response.read()
        except HTTPError as exc:
            return exc.code, exc.read()

    @staticmethod
    def json(raw: bytes) -> Any:
        return json.loads(raw) if raw else None


def _expect_success(status: int, operation: str) -> None:
    if not 200 <= status < 300:
        raise AssertionError(f"{operation} failed with HTTP {status}")


def _expect_denied(status: int, operation: str) -> None:
    if 200 <= status < 300:
        raise AssertionError(f"{operation} unexpectedly succeeded")


def main() -> int:
    client = LocalSupabase()
    marker = uuid4().hex
    password = f"Nestline-{uuid4().hex}-A1!"
    emails = [f"stage2-owner-{marker}@example.invalid", f"stage2-other-{marker}@example.invalid"]
    user_ids: list[str] = []
    workspace_ids: list[str] = []
    object_path: str | None = None
    checks = 0

    try:
        tokens = []
        for email in emails:
            status, raw = client.request(
                "POST", "/auth/v1/admin/users", key=client.service_key,
                json_body={"email": email, "password": password, "email_confirm": True},
            )
            _expect_success(status, "temporary user creation")
            user_ids.append(client.json(raw)["id"])
            status, raw = client.request(
                "POST", "/auth/v1/token?grant_type=password", key=client.anon_key,
                json_body={"email": email, "password": password},
            )
            _expect_success(status, "temporary user sign-in")
            tokens.append(client.json(raw)["access_token"])

        for index, token in enumerate(tokens):
            status, raw = client.request(
                "POST", "/rest/v1/rpc/create_workspace", key=client.anon_key, token=token,
                json_body={
                    "requested_mode": "personal_empty",
                    "requested_display_name": f"Stage 2 API fixture {index + 1}",
                },
            )
            _expect_success(status, "workspace creation")
            workspace_ids.append(client.json(raw))

        owner_workspace, other_workspace = workspace_ids
        object_path = str(PurePosixPath(owner_workspace) / "synthetic.pdf")
        encoded_path = "/".join(quote(part, safe="") for part in object_path.split("/"))
        first_body = b"fictional-stage2-object-v1"
        second_body = b"fictional-stage2-object-v2"

        status, raw = client.request(
            "POST", f"/storage/v1/object/medical-documents/{encoded_path}",
            key=client.anon_key, token=tokens[0], raw_body=first_body,
            content_type="application/pdf", extra_headers={"x-upsert": "false"},
        )
        _expect_success(status, "owner upload")
        checks += 1

        status, raw = client.request(
            "POST", "/rest/v1/private_documents", key=client.anon_key, token=tokens[0],
            json_body={
                "workspace_id": owner_workspace,
                "storage_object_path": object_path,
                "original_filename": "synthetic.pdf",
                "media_type": "application/pdf",
                "byte_size": len(first_body),
                "sha256": "a" * 64,
                "contains_real_medical_data": False,
            },
            extra_headers={"Prefer": "return=representation"},
        )
        _expect_success(status, "owner document metadata creation")
        document_id = client.json(raw)[0]["id"]
        checks += 1

        status, raw = client.request(
            "POST", "/storage/v1/object/list/medical-documents", key=client.anon_key,
            token=tokens[0], json_body={"prefix": owner_workspace, "limit": 100, "offset": 0},
        )
        _expect_success(status, "owner list")
        if [item["name"] for item in client.json(raw)] != ["synthetic.pdf"]:
            raise AssertionError("owner list did not return the exact workspace object")
        checks += 1

        status, raw = client.request(
            "GET", f"/storage/v1/object/authenticated/medical-documents/{encoded_path}",
            key=client.anon_key, token=tokens[0],
        )
        _expect_success(status, "owner download")
        if raw != first_body:
            raise AssertionError("owner download bytes changed")
        checks += 1

        status, raw = client.request(
            "PUT", f"/storage/v1/object/medical-documents/{encoded_path}",
            key=client.anon_key, token=tokens[0], raw_body=second_body,
            content_type="application/pdf", extra_headers={"x-upsert": "true"},
        )
        _expect_success(status, "owner update")
        checks += 1

        status, raw = client.request(
            "POST", "/storage/v1/object/list/medical-documents", key=client.anon_key,
            token=tokens[1], json_body={"prefix": owner_workspace, "limit": 100, "offset": 0},
        )
        _expect_success(status, "other-user list request")
        if client.json(raw) != []:
            raise AssertionError("other user discovered owner Storage metadata")
        checks += 1

        status, _ = client.request(
            "GET", f"/storage/v1/object/authenticated/medical-documents/{encoded_path}",
            key=client.anon_key, token=tokens[1],
        )
        _expect_denied(status, "other-user download")
        checks += 1

        denied_path = str(PurePosixPath(owner_workspace) / "other-user.pdf")
        encoded_denied_path = "/".join(quote(part, safe="") for part in denied_path.split("/"))
        status, _ = client.request(
            "POST", f"/storage/v1/object/medical-documents/{encoded_denied_path}",
            key=client.anon_key, token=tokens[1], raw_body=b"denied",
            content_type="application/pdf", extra_headers={"x-upsert": "false"},
        )
        _expect_denied(status, "other-user upload")
        checks += 1

        status, _ = client.request(
            "PUT", f"/storage/v1/object/medical-documents/{encoded_path}",
            key=client.anon_key, token=tokens[1], raw_body=b"denied-update",
            content_type="application/pdf", extra_headers={"x-upsert": "true"},
        )
        _expect_denied(status, "other-user update")
        checks += 1

        status, _ = client.request(
            "DELETE", "/storage/v1/object/medical-documents", key=client.anon_key,
            token=tokens[1], json_body={"prefixes": [object_path]},
        )
        if 200 <= status < 300:
            status, raw = client.request(
                "GET", f"/storage/v1/object/authenticated/medical-documents/{encoded_path}",
                key=client.anon_key, token=tokens[0],
            )
            _expect_success(status, "owner verification after other-user delete")
            if raw != second_body:
                raise AssertionError("other user changed or deleted the owner object")
        checks += 1

        status, _ = client.request(
            "POST", "/rest/v1/rpc/delete_private_document", key=client.anon_key,
            token=tokens[0], json_body={
                "requested_workspace_id": owner_workspace,
                "requested_document_id": document_id,
            },
        )
        _expect_denied(status, "metadata deletion while Storage object exists")
        checks += 1

        status, _ = client.request(
            "DELETE", "/storage/v1/object/medical-documents", key=client.anon_key,
            token=tokens[0], json_body={"prefixes": [object_path]},
        )
        _expect_success(status, "owner Storage delete")
        object_path = None
        checks += 1

        status, raw = client.request(
            "POST", "/rest/v1/rpc/delete_private_document", key=client.anon_key,
            token=tokens[0], json_body={
                "requested_workspace_id": owner_workspace,
                "requested_document_id": document_id,
            },
        )
        _expect_success(status, "metadata deletion after Storage cleanup")
        if client.json(raw) != f"{owner_workspace}/synthetic.pdf":
            raise AssertionError("document deletion returned an unexpected path")
        checks += 1

    finally:
        if object_path:
            status, _ = client.request(
                "DELETE", "/storage/v1/object/medical-documents", key=client.service_key,
                json_body={"prefixes": [object_path]},
            )
            _expect_success(status, "Storage fixture cleanup")
        for workspace_id in workspace_ids:
            status, _ = client.request(
                "DELETE", f"/rest/v1/workspaces?id=eq.{quote(workspace_id)}",
                key=client.service_key,
            )
            _expect_success(status, "workspace fixture cleanup")
        for user_id in user_ids:
            status, _ = client.request(
                "DELETE", f"/auth/v1/admin/users/{quote(user_id)}", key=client.service_key,
            )
            _expect_success(status, "user fixture cleanup")

    print(json.dumps({"valid": True, "checks": checks, "fixtures_removed": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
