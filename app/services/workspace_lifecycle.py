"""Authenticated Storage-first lifecycle operations for fictional workspaces."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from uuid import UUID


MEDICAL_DOCUMENT_BUCKET = "medical-documents"


class WorkspaceLifecycleError(RuntimeError):
    """A remote Storage or database lifecycle operation failed safely."""


class WorkspaceLifecycleGateway(Protocol):
    """Small boundary implemented by Supabase and deterministic test doubles."""

    def list_workspace_objects(self, workspace_id: UUID) -> list[str]: ...

    def delete_workspace_objects(self, object_paths: list[str]) -> None: ...

    def reseed_demo_workspace(
        self,
        workspace_id: UUID,
        expected_updated_at: datetime,
        seed_version: str,
    ) -> datetime: ...


@dataclass(frozen=True)
class WorkspaceResetResult:
    workspace_id: UUID
    deleted_object_paths: tuple[str, ...]
    updated_at: datetime
    seed_version: str


@dataclass
class SupabaseWorkspaceLifecycleGateway:
    """Minimal user-token Supabase REST adapter; no service-role key is used."""

    project_url: str
    publishable_key: str
    user_access_token: str
    timeout_seconds: float = 20.0

    def _request(self, method: str, path: str, payload: dict[str, Any]) -> Any:
        body = json.dumps(payload).encode("utf-8")
        request = Request(
            f"{self.project_url.rstrip('/')}{path}",
            data=body,
            method=method,
            headers={
                "apikey": self.publishable_key,
                "Authorization": f"Bearer {self.user_access_token}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read()
        except HTTPError as exc:
            # Keep credentials and medical content out of exceptions and logs.
            raise WorkspaceLifecycleError(
                f"Supabase lifecycle request failed with HTTP {exc.code}."
            ) from exc
        except URLError as exc:
            raise WorkspaceLifecycleError("Supabase lifecycle request could not connect.") from exc
        return json.loads(raw) if raw else None

    def _list_folder(self, folder: str) -> list[str]:
        files: list[str] = []
        offset = 0
        while True:
            items = self._request(
                "POST",
                f"/storage/v1/object/list/{quote(MEDICAL_DOCUMENT_BUCKET, safe='')}",
                {
                    "prefix": folder,
                    "limit": 100,
                    "offset": offset,
                    "sortBy": {"column": "name", "order": "asc"},
                },
            )
            if not isinstance(items, list):
                raise WorkspaceLifecycleError("Supabase returned an invalid Storage listing.")
            for item in items:
                name = item.get("name") if isinstance(item, dict) else None
                if not isinstance(name, str) or not name:
                    raise WorkspaceLifecycleError("Supabase returned an unnamed Storage object.")
                path = name if name.startswith(f"{folder}/") else f"{folder}/{name}"
                if item.get("id") is None:
                    files.extend(self._list_folder(path))
                else:
                    files.append(path)
            if len(items) < 100:
                break
            offset += len(items)
        return files

    def list_workspace_objects(self, workspace_id: UUID) -> list[str]:
        prefix = str(workspace_id)
        paths = sorted(set(self._list_folder(prefix)))
        if any(not path.startswith(f"{prefix}/") for path in paths):
            raise WorkspaceLifecycleError("Storage listing escaped the workspace prefix.")
        return paths

    def delete_workspace_objects(self, object_paths: list[str]) -> None:
        for start in range(0, len(object_paths), 100):
            batch = object_paths[start:start + 100]
            if batch:
                self._request(
                    "DELETE",
                    f"/storage/v1/object/{quote(MEDICAL_DOCUMENT_BUCKET, safe='')}",
                    {"prefixes": batch},
                )

    def reseed_demo_workspace(
        self,
        workspace_id: UUID,
        expected_updated_at: datetime,
        seed_version: str,
    ) -> datetime:
        value = self._request(
            "POST",
            "/rest/v1/rpc/reseed_demo_workspace_state",
            {
                "requested_workspace_id": str(workspace_id),
                "expected_workspace_updated_at": expected_updated_at.isoformat(),
                "requested_seed_version": seed_version,
            },
        )
        if not isinstance(value, str):
            raise WorkspaceLifecycleError("Supabase returned an invalid reset timestamp.")
        return datetime.fromisoformat(value.replace("Z", "+00:00"))


def reset_seeded_demo_workspace(
    gateway: WorkspaceLifecycleGateway,
    workspace_id: UUID,
    expected_updated_at: datetime,
    seed_version: str = "maya-v1",
) -> WorkspaceResetResult:
    """Delete exact-prefix files first, then reset and reapply the demo seed."""

    object_paths = gateway.list_workspace_objects(workspace_id)
    gateway.delete_workspace_objects(object_paths)
    updated_at = gateway.reseed_demo_workspace(
        workspace_id, expected_updated_at, seed_version
    )
    return WorkspaceResetResult(
        workspace_id=workspace_id,
        deleted_object_paths=tuple(object_paths),
        updated_at=updated_at,
        seed_version=seed_version,
    )
