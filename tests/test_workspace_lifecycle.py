"""Tests for the Storage-first fictional workspace reset boundary."""

from datetime import datetime, timedelta, timezone
import unittest
from uuid import uuid4

from app.services.workspace_lifecycle import (
    WorkspaceLifecycleError,
    reset_seeded_demo_workspace,
)


class FakeLifecycleGateway:
    def __init__(self, *, object_paths=None, fail_delete=False):
        self.object_paths = object_paths or []
        self.fail_delete = fail_delete
        self.calls = []
        self.new_timestamp = datetime.now(timezone.utc) + timedelta(seconds=1)

    def list_workspace_objects(self, workspace_id):
        self.calls.append(("list", workspace_id))
        return list(self.object_paths)

    def delete_workspace_objects(self, object_paths):
        self.calls.append(("delete", tuple(object_paths)))
        if self.fail_delete:
            raise WorkspaceLifecycleError("Synthetic Storage failure.")

    def reseed_demo_workspace(self, workspace_id, expected_updated_at, seed_version):
        self.calls.append(("reseed", workspace_id, expected_updated_at, seed_version))
        return self.new_timestamp


class WorkspaceLifecycleTests(unittest.TestCase):
    def test_reset_deletes_storage_before_database_reseed(self):
        workspace_id = uuid4()
        expected = datetime.now(timezone.utc)
        paths = [f"{workspace_id}/report-a.pdf", f"{workspace_id}/nested/report-b.pdf"]
        gateway = FakeLifecycleGateway(object_paths=paths)

        result = reset_seeded_demo_workspace(gateway, workspace_id, expected)

        self.assertEqual([call[0] for call in gateway.calls], ["list", "delete", "reseed"])
        self.assertEqual(result.deleted_object_paths, tuple(paths))
        self.assertEqual(result.updated_at, gateway.new_timestamp)
        self.assertEqual(result.seed_version, "maya-v1")

    def test_storage_failure_prevents_database_reset(self):
        workspace_id = uuid4()
        gateway = FakeLifecycleGateway(
            object_paths=[f"{workspace_id}/report.pdf"], fail_delete=True,
        )

        with self.assertRaises(WorkspaceLifecycleError):
            reset_seeded_demo_workspace(gateway, workspace_id, datetime.now(timezone.utc))

        self.assertEqual([call[0] for call in gateway.calls], ["list", "delete"])

    def test_empty_storage_prefix_still_reseeds_deterministically(self):
        workspace_id = uuid4()
        gateway = FakeLifecycleGateway()

        result = reset_seeded_demo_workspace(
            gateway, workspace_id, datetime.now(timezone.utc), "maya-v1",
        )

        self.assertEqual([call[0] for call in gateway.calls], ["list", "delete", "reseed"])
        self.assertEqual(result.deleted_object_paths, ())


if __name__ == "__main__":
    unittest.main()
