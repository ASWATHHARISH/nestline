"""Stage 2 storage, privacy and lifecycle contract tests."""

from datetime import date, datetime, timezone
import json
from pathlib import Path
import unittest
from uuid import uuid4

from pydantic import ValidationError

from app.schemas.storage import (HumanReviewCase, JourneyState, STAGE2_TABLES,
                                 USER_OWNED_TABLES)
from app.services.storage_validation import (
    validate_journey_state_invariants,
    validate_owner_only_episode_boundary,
    validate_personal_dependency_invalidation,
    validate_release_provenance_migration,
    validate_stage2_migration,
    validate_storage_first_documents,
    validate_versioned_demo_workspaces,
    validate_workspace_lifecycle_migration,
    validate_workspace_membership_hardening,
    validate_workspace_owner_visibility,
)

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

    def test_workspace_boundary_is_owner_only_and_one_episode(self):
        self.assertEqual(validate_owner_only_episode_boundary(OWNER_ONLY_MIGRATION), [])

    def test_journey_state_combinations_are_strict(self):
        self.assertEqual(validate_journey_state_invariants(JOURNEY_INVARIANTS_MIGRATION), [])

    def test_personal_dependencies_are_normalized_and_invalidated(self):
        self.assertEqual(validate_personal_dependency_invalidation(DEPENDENCY_MIGRATION), [])

    def test_demo_workspaces_are_versioned_and_session_scoped(self):
        self.assertEqual(validate_versioned_demo_workspaces(DEMO_WORKSPACES_MIGRATION), [])

    def test_document_metadata_deletion_cannot_bypass_storage(self):
        self.assertEqual(validate_storage_first_documents(STORAGE_FIRST_MIGRATION), [])

    def test_exported_schema_matches_table_contract(self):
        exported = json.loads((ROOT / "data/schemas/storage.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(set(exported["database_tables"]), STAGE2_TABLES)
        self.assertEqual(set(exported["workspace_owned_tables"]), USER_OWNED_TABLES)

    def test_every_personal_table_has_an_exported_record_contract(self):
        exported = json.loads((ROOT / "data/schemas/storage.schema.json").read_text(encoding="utf-8"))
        expected_records = {
            "workspace", "workspace_member", "journey_state", "private_document",
            "document_chunk", "document_fact", "health_fact", "medication_mention",
            "symptom_event", "appointment", "appointment_question", "saved_plan",
            "plan_item", "graph_node", "graph_edge", "human_review_case",
            "notification", "feedback",
        }
        self.assertEqual(set(exported["records"]), expected_records)
        self.assertEqual(len(exported["records"]), len(USER_OWNED_TABLES) + 2)

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
    def setUp(self):
        self.now = datetime.now(timezone.utc)

    def journey(self, **overrides):
        values = {
            "id": uuid4(), "workspace_id": uuid4(), "stage": "pregnancy",
            "timing_source": "manual_week_day", "gestational_week": 24,
            "gestational_day": 2, "user_confirmed": True,
            "has_dating_conflict": False, "is_current": True, "version": 1,
            "created_at": self.now, "updated_at": self.now,
        }
        values.update(overrides)
        return values

    def test_journey_state_rejects_stage_confusion(self):
        values = self.journey(postpartum_week=1)
        with self.assertRaises(ValidationError):
            JourneyState.model_validate(values)

    def test_possible_pregnancy_does_not_invent_a_week(self):
        values = self.journey(
            stage="possible_pregnancy", timing_source="user_reported_possible_pregnancy",
            gestational_week=4, gestational_day=None, user_confirmed=False,
        )
        with self.assertRaises(ValidationError):
            JourneyState.model_validate(values)

    def test_all_supported_journey_inputs_validate(self):
        cases = [
            self.journey(
                stage="possible_pregnancy",
                timing_source="user_reported_possible_pregnancy",
                gestational_week=None, gestational_day=None, user_confirmed=False,
            ),
            self.journey(),
            self.journey(
                timing_source="user_estimated_due_date",
                estimated_due_date=date(2026, 12, 29),
            ),
            self.journey(
                timing_source="document_estimated_due_date",
                estimated_due_date=date(2026, 12, 29),
            ),
            self.journey(
                timing_source="approximate_month_range", gestational_week=None,
                gestational_day=None, approximate_month_min=5,
                approximate_month_max=6, user_confirmed=False,
            ),
            self.journey(
                stage="postpartum", timing_source="delivery_date",
                gestational_week=None, gestational_day=None, postpartum_week=2,
                postpartum_day=3, delivery_date=date(2026, 8, 24),
            ),
            self.journey(
                stage="postpartum", timing_source="postpartum_week",
                gestational_week=None, gestational_day=None, postpartum_week=2,
                postpartum_day=3,
            ),
        ]
        self.assertTrue(all(JourneyState.model_validate(case) for case in cases))

    def test_journey_inputs_reject_partial_or_contradictory_values(self):
        invalid_cases = [
            self.journey(gestational_day=None),
            self.journey(timing_source="user_estimated_due_date"),
            self.journey(
                timing_source="approximate_month_range", gestational_week=None,
                gestational_day=None, approximate_month_min=7,
                approximate_month_max=4,
            ),
            self.journey(
                stage="postpartum", timing_source="delivery_date",
                gestational_week=None, gestational_day=None, postpartum_week=2,
                postpartum_day=3,
            ),
            self.journey(
                stage="postpartum", timing_source="postpartum_week",
                gestational_week=None, gestational_day=None, postpartum_week=2,
                postpartum_day=3, delivery_date=date(2026, 8, 24),
            ),
        ]
        for values in invalid_cases:
            with self.subTest(values=values):
                with self.assertRaises(ValidationError):
                    JourneyState.model_validate(values)

    def test_reviewed_handoff_requires_consent_and_review_timestamps(self):
        base = {"id": uuid4(), "workspace_id": uuid4(), "state": "reviewed",
                "reason": "Synthetic review fixture.", "simulated": True,
                "created_at": self.now, "updated_at": self.now}
        with self.assertRaises(ValidationError):
            HumanReviewCase.model_validate(base)
        record = HumanReviewCase.model_validate({
            **base, "consented_at": self.now, "reviewed_at": self.now,
        })
        self.assertEqual(record.state, "reviewed")


if __name__ == "__main__":
    unittest.main()
