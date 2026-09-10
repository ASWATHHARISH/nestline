"""Stage 2 storage, privacy and lifecycle contract tests."""

from datetime import datetime, timezone
import json
from pathlib import Path
import unittest
from uuid import uuid4

from pydantic import ValidationError

from app.schemas.storage import (HumanReviewCase, JourneyState, STAGE2_TABLES,
                                 USER_OWNED_TABLES)
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


class StorageMigrationTests(unittest.TestCase):
    def test_migration_satisfies_stage2_contract(self):
        self.assertEqual(validate_stage2_migration(MIGRATION), [])

    def test_owner_membership_cannot_be_changed_through_client_policies(self):
        self.assertEqual(validate_workspace_membership_hardening(HARDENING_MIGRATION), [])

    def test_public_ingestion_provenance_is_bound_to_one_release(self):
        self.assertEqual(validate_release_provenance_migration(PROVENANCE_MIGRATION), [])

    def test_workspace_lifecycle_has_atomic_and_idempotent_boundaries(self):
        self.assertEqual(validate_workspace_lifecycle_migration(LIFECYCLE_MIGRATION), [])

    def test_workspace_owner_is_visible_during_authenticated_creation(self):
        self.assertEqual(validate_workspace_owner_visibility(OWNER_VISIBILITY_MIGRATION), [])

    def test_exported_schema_matches_table_contract(self):
        exported = json.loads((ROOT / "data/schemas/storage.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(set(exported["database_tables"]), STAGE2_TABLES)
        self.assertEqual(set(exported["workspace_owned_tables"]), USER_OWNED_TABLES)

    def test_private_retrieval_checks_authenticated_workspace(self):
        sql = MIGRATION.read_text(encoding="utf-8").casefold()
        private_function = sql.split("create or replace function public.match_document_chunks", 1)[1]
        private_function = private_function.split("$$;", 1)[0]
        self.assertIn("chunk.workspace_id = requested_workspace_id", private_function)
        self.assertIn("private.is_workspace_member(requested_workspace_id)", private_function)

    def test_document_delete_cascades_to_derived_rows(self):
        sql = MIGRATION.read_text(encoding="utf-8").casefold()
        cascade = "references public.private_documents(workspace_id, id) on delete cascade"
        self.assertGreaterEqual(sql.count(cascade), 4)

    def test_public_vectors_are_not_indexed_before_provider_dimension_is_selected(self):
        sql = MIGRATION.read_text(encoding="utf-8").casefold()
        self.assertIn("embedding extensions.vector", sql)
        self.assertNotIn("using hnsw", sql)
        self.assertNotIn("using ivfflat", sql)


class StorageRecordTests(unittest.TestCase):
    def test_journey_state_rejects_stage_confusion(self):
        values = {
            "id": uuid4(), "workspace_id": uuid4(), "stage": "pregnancy",
            "timing_source": "manual_week_day", "gestational_week": 24,
            "gestational_day": 2, "postpartum_week": 1, "user_confirmed": True,
            "has_dating_conflict": False, "is_current": True, "version": 1,
        }
        with self.assertRaises(ValidationError):
            JourneyState.model_validate(values)

    def test_possible_pregnancy_does_not_invent_a_week(self):
        values = {
            "id": uuid4(), "workspace_id": uuid4(), "stage": "possible_pregnancy",
            "timing_source": "manual_week_day", "gestational_week": 4,
            "user_confirmed": False, "has_dating_conflict": False,
            "is_current": True, "version": 1,
        }
        with self.assertRaises(ValidationError):
            JourneyState.model_validate(values)

    def test_reviewed_handoff_requires_consent_and_review_timestamps(self):
        now = datetime.now(timezone.utc)
        base = {"id": uuid4(), "workspace_id": uuid4(), "state": "reviewed",
                "reason": "Synthetic review fixture.", "simulated": True}
        with self.assertRaises(ValidationError):
            HumanReviewCase.model_validate(base)
        record = HumanReviewCase.model_validate({**base, "consented_at": now, "reviewed_at": now})
        self.assertEqual(record.state, "reviewed")


if __name__ == "__main__":
    unittest.main()
