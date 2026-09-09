"""Adversarial data-integrity checks, not a clinical evaluation dataset."""

from copy import deepcopy
from contextlib import redirect_stdout
from hashlib import sha256
from io import StringIO
import json
from pathlib import Path
import unittest

from pydantic import ValidationError

from app.schemas.content import Applicability, ContentBundle
from app.services.content_validation import expected_profile_ids, validate_bundle
from scripts.validate_content import load_bundle, main

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    """Invented non-medical text; review identities are test doubles only."""
    review = {"reviewer": "TEST-REVIEWER", "reviewed_at": "2026-09-09",
              "kind": "content_reviewed", "notes": "TEST ONLY: structural validator fixture"}
    scope = {"stage": "pregnancy", "unit": "week", "start": 10, "end": 10}
    text = "Synthetic test passage for checking source linkage."
    checksum = sha256(text.encode()).hexdigest()
    return {"sources": [{"source_id": "TEST-SOURCE", "title": "TEST ONLY",
                         "publisher": "Test publisher", "canonical_url": "https://example.org/test",
                         "jurisdiction": ["IN"], "document_type": "html", "topics": ["journey"],
                         "evidence_lane": "weekly_profile", "status": "approved_for_capstone",
                         "version_or_last_update": "test-v1", "last_checked_at": "2026-09-09",
                         "reuse_status": "permitted", "allowed_use": ["store", "embed", "display"],
                         "license_or_reuse_note": "Self-authored test text only",
                         "prohibited_inferences": "Not medical evidence", "review": review,
                         "content_checksum": checksum}],
            "evidence": [{"evidence_id": "TEST-EVIDENCE", "source_id": "TEST-SOURCE",
                          "source_version": "test-v1", "source_checksum": checksum,
                          "locator": "#test", "text": text, "text_checksum": checksum,
                          "applies_to": scope, "jurisdiction": ["IN"], "status": "published",
                          "review": review}],
            "fragments": [{"fragment_id": "TEST-FRAGMENT", "domain": "journey", "text": text,
                           "applies_to": scope, "jurisdiction": ["IN"], "status": "published",
                           "evidence_span_ids": ["TEST-EVIDENCE"], "review": review}],
            "profiles": [{"profile_id": "P10", "applies_to": scope, "status": "published",
                          "hero": {"title": "Test profile", "development_evidence_ids": ["TEST-EVIDENCE"]},
                          "guidance_fragment_ids": ["TEST-FRAGMENT"],
                          "source_evidence_ids": ["TEST-EVIDENCE"], "jurisdiction": ["IN"],
                          "review": review, "content_priority": "representative"}]}


def check(payload):
    return validate_bundle(ContentBundle.model_validate_json(json.dumps(payload)), require_coverage=False)


class ContentTests(unittest.TestCase):
    def test_linked_reviewed_fixture_passes(self):
        self.assertTrue(check(fixture()).valid)

    def test_candidates_and_draft_shells_pass_authoring_only(self):
        bundle = load_bundle(ROOT / "data")
        report = validate_bundle(bundle)
        self.assertTrue(report.valid, report.errors)
        self.assertEqual(len(bundle.profiles), 63)
        self.assertEqual(report.published_profiles, 0)
        self.assertEqual({p.profile_id for p in bundle.profiles}, expected_profile_ids())

    def test_empty_corpus_cannot_pass_release(self):
        with redirect_stdout(StringIO()) as output:
            result = main(["--require-release"])
        self.assertEqual(result, 1)
        self.assertEqual(len(json.loads(output.getvalue())["errors"]), 9)

    def test_fake_publication_of_shell_is_blocked(self):
        bundle = load_bundle(ROOT / "data")
        payload = bundle.model_dump(mode="json")
        payload["profiles"][0]["status"] = "published"
        self.assertFalse(check(payload).valid)

    def test_missing_source_rejected(self):
        data = fixture()
        data["sources"] = []
        self.assertFalse(check(data).valid)

    def test_retired_source_rejected(self):
        for status in ("candidate", "excluded", "superseded"):
            with self.subTest(status=status):
                data = fixture()
                data["sources"][0]["status"] = status
                self.assertFalse(check(data).valid)

    def test_approval_requires_every_governance_field(self):
        cases = {"reuse_status": "unverified", "allowed_use": ["display"],
                 "version_or_last_update": "", "last_checked_at": None,
                 "license_or_reuse_note": "", "review": None, "content_checksum": None,
                 "document_type": "index"}
        for key, value in cases.items():
            with self.subTest(field=key):
                data = fixture()
                data["sources"][0][key] = value
                with self.assertRaises(ValidationError):
                    check(data)

    def test_duplicate_identifiers_rejected(self):
        for collection in ("sources", "evidence", "fragments", "profiles"):
            with self.subTest(collection=collection):
                data = fixture()
                data[collection].append(deepcopy(data[collection][0]))
                self.assertFalse(check(data).valid)

    def test_review_required_at_every_publishable_layer(self):
        for collection in ("evidence", "fragments", "profiles"):
            with self.subTest(collection=collection):
                data = fixture()
                data[collection][0]["review"] = None
                self.assertFalse(check(data).valid)

    def test_source_update_invalidates_old_evidence(self):
        data = fixture()
        data["sources"][0]["version_or_last_update"] = "test-v2"
        self.assertFalse(check(data).valid)

    def test_changed_text_requires_new_checksum(self):
        data = fixture()
        data["evidence"][0]["text"] = "Altered passage"
        self.assertFalse(check(data).valid)

    def test_fabricated_citation_is_blocked(self):
        data = fixture()
        data["fragments"][0]["evidence_span_ids"] = ["DOES-NOT-EXIST"]
        self.assertFalse(check(data).valid)

    def test_hero_cannot_bypass_citation_checks(self):
        data = fixture()
        data["profiles"][0]["hero"]["development_evidence_ids"] = ["DOES-NOT-EXIST"]
        self.assertFalse(check(data).valid)

    def test_card_cannot_bypass_declared_fragment_list(self):
        data = fixture()
        data["profiles"][0]["card_slots"] = {"movement_focus": ["HIDDEN-FRAGMENT"]}
        self.assertFalse(check(data).valid)

    def test_unpublished_dependencies_are_rejected(self):
        for collection in ("evidence", "fragments"):
            with self.subTest(collection=collection):
                data = fixture()
                data[collection][0]["status"] = "draft"
                self.assertFalse(check(data).valid)

    def test_wrong_week_and_partially_supported_range_are_rejected(self):
        data = fixture()
        data["fragments"][0]["applies_to"] = {"stage": "pregnancy", "unit": "week", "start": 9, "end": 10}
        self.assertFalse(check(data).valid)

    def test_wrong_jurisdiction_is_rejected(self):
        data = fixture()
        data["profiles"][0]["jurisdiction"] = ["UK"]
        self.assertFalse(check(data).valid)

    def test_local_source_cannot_be_relabelled_global(self):
        data = fixture()
        data["evidence"][0]["jurisdiction"] = ["GLOBAL"]
        self.assertFalse(check(data).valid)

    def test_profile_identity_cannot_lie_about_week(self):
        data = fixture()
        data["profiles"][0]["profile_id"] = "P09"
        with self.assertRaises(ValidationError):
            check(data)

    def test_invalid_ranges_fail(self):
        for stage, unit, start, end in [("pregnancy", "week", 10, 9), ("pregnancy", "week", 0, 1),
                                       ("pregnancy", "week", 1, 43), ("pregnancy", "day", 1, 2),
                                       ("postpartum", "week", 1, 13), ("postpartum", "day", 0, 8),
                                       ("possible_pregnancy", "week", 1, 1)]:
            with self.subTest(stage=stage, unit=unit, start=start, end=end):
                with self.assertRaises(ValidationError):
                    Applicability(stage=stage, unit=unit, start=start, end=end)

    def test_day_overlay_never_silently_becomes_week(self):
        day = Applicability(stage="postpartum", unit="day", start=0, end=7)
        week = Applicability(stage="postpartum", unit="week", start=1, end=1)
        self.assertFalse(day.covers(week))

    def test_unknown_fields_and_boolean_week_rejected(self):
        data = fixture()
        data["profiles"][0]["approved_by_ai"] = True
        with self.assertRaises(ValidationError):
            check(data)
        with self.assertRaises(ValidationError):
            Applicability(stage="pregnancy", unit="week", start=True, end=1)

    def test_missing_profile_is_detected(self):
        bundle = load_bundle(ROOT / "data")
        bundle.profiles.pop()
        self.assertFalse(validate_bundle(bundle).valid)

    def test_json_schema_export_matches_python_contract(self):
        exported = json.loads((ROOT / "data/schemas/content_bundle.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(exported, ContentBundle.model_json_schema())


if __name__ == "__main__":
    unittest.main()
