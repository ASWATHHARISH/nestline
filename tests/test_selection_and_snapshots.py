"""Regression cases for uncertainty, permissions and saved-source integrity."""

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from app.schemas.content import Applicability, ContentBundle
from app.services.content_selection import pregnancy_month_scope, select_content
from app.services.source_snapshots import validate_snapshots
from scripts.validate_content import load_bundle, read_jsonl
from tests.test_content import check, fixture

ROOT = Path(__file__).resolve().parents[1]


def bundle(payload):
    return ContentBundle.model_validate_json(json.dumps(payload))


class SelectionTests(unittest.TestCase):
    def test_month_three_never_selects_week_ten_profile(self):
        result = select_content(bundle(fixture()), pregnancy_month_scope(3), "IN")
        self.assertEqual(result["profile_ids"], [])
        self.assertEqual(result["fragment_ids"], [])

    def test_full_range_fragment_is_available_without_exact_week_hero(self):
        data = fixture()
        for collection in ("evidence", "fragments"):
            data[collection][0]["applies_to"].update(start=9, end=13)
        result = select_content(bundle(data), pregnancy_month_scope(3), "IN")
        self.assertEqual(result["profile_ids"], [])
        self.assertEqual(result["fragment_ids"], ["TEST-FRAGMENT"])

    def test_wrong_week_is_not_returned(self):
        scope = Applicability(stage="pregnancy", unit="week", start=9, end=9)
        self.assertEqual(select_content(bundle(fixture()), scope, "IN")["status"], "content_unavailable")

    def test_foreign_guidance_is_not_returned_for_india(self):
        data = fixture()
        for records in (data["sources"], data["evidence"], data["fragments"], data["profiles"]):
            records[0]["jurisdiction"] = ["US"]
        scope = Applicability(stage="pregnancy", unit="week", start=10, end=10)
        self.assertEqual(select_content(bundle(data), scope, "IN")["status"], "content_unavailable")

    def test_missing_condition_is_not_inferred_clearance(self):
        data = fixture()
        data["fragments"][0]["conditions_required"] = ["clearance"]
        data["fragments"][0]["conditions_excluded"] = ["restriction"]
        scope = Applicability(stage="pregnancy", unit="week", start=10, end=10)
        self.assertEqual(select_content(bundle(data), scope, "IN")["fragment_ids"], [])
        self.assertEqual(select_content(bundle(data), scope, "IN", frozenset({"clearance"}))["fragment_ids"], [])
        result = select_content(bundle(data), scope, "IN", frozenset({"clearance"}), frozenset({"restriction"}))
        self.assertEqual(result["fragment_ids"], ["TEST-FRAGMENT"])

    def test_conflicting_condition_reports_are_rejected(self):
        scope = pregnancy_month_scope(3)
        with self.assertRaises(ValueError):
            select_content(bundle(fixture()), scope, "IN", frozenset({"x"}), frozenset({"x"}))

    def test_month_nine_keeps_beyond_term_uncertainty(self):
        self.assertEqual(pregnancy_month_scope(9).end, 42)

    def test_invalid_months_fail(self):
        for month in (0, 10, True, "3", 3.5):
            with self.subTest(month=month), self.assertRaises(ValueError):
                pregnancy_month_scope(month)

    def test_draft_corpus_returns_no_runtime_content(self):
        for jurisdiction in ("IN", "US"):
            result = select_content(load_bundle(ROOT / "data"), pregnancy_month_scope(3), jurisdiction)
            self.assertEqual(result["status"], "content_unavailable")

    def test_invalid_bundle_cannot_be_selected(self):
        data = fixture()
        data["sources"] = []
        with self.assertRaises(ValueError):
            select_content(bundle(data), pregnancy_month_scope(3), "IN")


class ProvenanceTests(unittest.TestCase):
    def test_restricted_source_cannot_hide_in_draft_evidence(self):
        for status, reuse in (("excluded", "restricted"), ("candidate", "unverified")):
            data = fixture()
            for collection in ("evidence", "fragments", "profiles"):
                data[collection][0]["status"] = "draft"
            data["sources"][0].update(status=status, reuse_status=reuse)
            self.assertFalse(check(data).valid)

    def test_draft_source_version_mismatch_is_rejected(self):
        data = fixture()
        for collection in ("evidence", "fragments", "profiles"):
            data[collection][0]["status"] = "draft"
        data["evidence"][0]["source_version"] = "older-copy"
        self.assertFalse(check(data).valid)

    def test_publication_blockers_prevent_publication(self):
        data = fixture()
        data["profiles"][0]["publication_blockers"] = ["India review pending"]
        self.assertFalse(check(data).valid)

    def test_conditions_cannot_contradict_each_other(self):
        data = fixture()
        data["fragments"][0].update(conditions_required=["x"], conditions_excluded=["x"])
        self.assertFalse(check(data).valid)

    def test_real_saved_excerpts_match_the_manifest(self):
        data = load_bundle(ROOT / "data")
        self.assertEqual(validate_snapshots(data, ROOT / "data"), [])
        self.assertGreater(len(data.evidence), 0)

    def test_snapshot_integrity_and_locator_attacks(self):
        data = load_bundle(ROOT / "data")
        used = next(s for s in data.sources if s.snapshot_path)
        original = (ROOT / "data" / used.snapshot_path).read_bytes()
        for attack in ("changed_bytes", "forged_locator", "wrong_url", "escape_path"):
            with self.subTest(attack=attack), TemporaryDirectory() as tmp:
                altered = data.model_copy(deep=True)
                # Reduce to one source so this test isolates the intended error.
                altered.sources = [deepcopy(used)]
                altered.evidence = [e for e in altered.evidence if e.source_id == used.source_id]
                path = Path(tmp) / used.snapshot_path
                path.parent.mkdir(parents=True)
                path.write_bytes(original)
                if attack == "changed_bytes":
                    path.write_bytes(original + b" ")
                elif attack == "forged_locator":
                    altered.evidence[0].locator = "invented location"
                elif attack == "wrong_url":
                    snapshot = json.loads(original)
                    snapshot["canonical_url"] = "https://example.org/unrelated"
                    path.write_bytes(json.dumps(snapshot).encode())
                    altered.sources[0].content_checksum = sha256(path.read_bytes()).hexdigest()
                else:
                    altered.sources[0].snapshot_path = "../outside.json"
                self.assertTrue(validate_snapshots(altered, Path(tmp)))

    def test_json_error_identifies_the_file_and_line(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "broken.jsonl"
            path.write_text('{}\nnot json\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "broken.jsonl:2"):
                read_jsonl(path)
