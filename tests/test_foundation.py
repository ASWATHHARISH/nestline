"""Regressions for the teammate review and the new foundation contracts."""

from datetime import date
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest

from pydantic import ValidationError

from app.schemas.content import ContentBundle
from app.schemas.foundation import Plan, SafetySpec
from app.services.content_selection import select_content
from app.services.fixture_integrity import document_integrity
from app.services.foundation import (approval_errors, claim_fingerprint, food_eligibility, read_catalogues,
                                     release_fingerprint, source_freshness, validate_foundation)
from app.services.safety_contract import evaluate_safety_contract, route_safety
from scripts.validate_content import load_bundle
from tests.test_content import fixture

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


class CorrectionTests(unittest.TestCase):
    def setUp(self):
        self.bundle = load_bundle(DATA)
        self.spans = {e.evidence_id: e for e in self.bundle.evidence}
        self.fragments = {f.fragment_id: f for f in self.bundle.fragments}

    def test_complete_conditional_evidence_regressions(self):
        followup = self.spans["E-IN-PP-FOLLOWUP"].text
        self.assertIn("Institutional Delivery", followup)
        self.assertIn("Home Delivery", followup)
        self.assertIn("1st, 3rd", followup)
        self.assertIn("42nd Day", followup)
        activity = self.spans["E-PP-MOVEMENT-QUESTION"].text
        self.assertIn("complicated delivery or a caesarean", activity)
        self.assertIn("before starting anything strenuous", activity)
        self.assertEqual(self.fragments["F-PP-DIET"].text, self.spans["E-PP-DIET"].text)

    def test_week_one_contains_timing_only(self):
        profile = next(p for p in self.bundle.profiles if p.profile_id == "P01")
        self.assertEqual(profile.guidance_fragment_ids, ["F-DATING"])
        self.assertGreater(self.fragments["F-IN-BIRTH-PLAN"].applies_to.start, 1)

    def test_day_overlays_are_sourced_and_drafts_are_explained(self):
        days = [p for p in self.bundle.profiles if p.profile_id.startswith("PPD")]
        self.assertEqual(len(days), 8)
        for p in days:
            self.assertTrue(p.card_slots.preparation and p.card_slots.symptom_education)
            self.assertTrue(p.hero.development_evidence_ids)
        self.assertTrue(all(p.publication_blockers for p in self.bundle.profiles if p.status == "draft"))

    def test_foundation_records_are_consistent(self):
        self.assertEqual(validate_foundation(self.bundle, DATA), [])

    def test_claim_edit_invalidates_assessment(self):
        self.fragments["F-PP-DIET"].text += " This cures disease."
        self.assertIn("F-PP-DIET: stale claim assessment", validate_foundation(self.bundle, DATA))

    def test_source_edit_invalidates_assessment(self):
        fragment = self.fragments["F-PP-MOVEMENT-QUESTION"]
        before = claim_fingerprint(fragment, self.spans)
        self.spans["E-PP-MOVEMENT-QUESTION"].text = "Talk to a professional."
        self.assertNotEqual(before, claim_fingerprint(fragment, self.spans))

    def test_unknown_condition_is_rejected(self):
        payload = fixture()
        payload["fragments"][0]["conditions_required"] = ["breastfeedng"]
        with self.assertRaises(ValidationError):
            ContentBundle.model_validate_json(json.dumps(payload))

    def test_conditional_card_does_not_hide_profile(self):
        payload = fixture()
        payload["fragments"][0]["conditions_required"] = ["breastfeeding"]
        payload["profiles"][0]["card_slots"] = {"nutrition_focus": ["TEST-FRAGMENT"]}
        bundle = ContentBundle.model_validate_json(json.dumps(payload))
        for present, absent, state in [(set(), set(), "needs_information"),
                                       (set(), {"breastfeeding"}, "not_applicable"),
                                       ({"breastfeeding"}, set(), "shown")]:
            result = select_content(bundle, bundle.profiles[0].applies_to, "IN", frozenset(present), frozenset(absent))
            self.assertEqual(result["profile_ids"], ["P10"])
            self.assertEqual(result["profile_cards"]["P10"]["nutrition_focus"][0]["state"], state)

    def test_contradictory_delivery_facts_require_clarification(self):
        bundle = ContentBundle.model_validate_json(json.dumps(fixture()))
        with self.assertRaisesRegex(ValueError, "conflicting confirmed"):
            select_content(bundle, bundle.profiles[0].applies_to, "IN", frozenset({"home_birth", "facility_birth"}))

    def test_freshness_checks_missing_and_overdue_dates(self):
        source = next(s for s in self.bundle.sources if s.source_id == "OWH-HEALTH")
        self.assertEqual(source_freshness(source, date(2026, 9, 10)), [])
        self.assertTrue(source_freshness(source, date(2027, 1, 1)))
        source.retrieved_at = None
        self.assertTrue(source_freshness(source, date(2026, 9, 10)))

    def test_old_source_requires_currency_decision_even_after_capture(self):
        source = next(s for s in self.bundle.sources if s.source_id == "BHC-WEEKS")
        self.assertTrue(source_freshness(source, date(2026, 9, 10)))

    def test_unverified_cdc_copy_is_not_in_corpus(self):
        source = next(s for s in self.bundle.sources if s.source_id == "CDC-WARNINGS")
        self.assertEqual(source.allowed_use, [])
        self.assertFalse(source.snapshot_path)
        self.assertFalse(any(e.source_id == source.source_id for e in self.bundle.evidence))

    def test_approval_ledger_does_not_invent_people(self):
        self.assertEqual(json.loads((DATA / "reviews/approvals.json").read_text())["reviews"], [])
        self.assertEqual(len(approval_errors(DATA, date(2026, 9, 10))), 5)

    def test_review_fingerprint_survives_workflow_but_not_content_edit(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "weekly").mkdir()
            path = root / "weekly/profiles.jsonl"
            row = dict(text="Original", status="draft", review=None, publication_blockers=["pending"])
            path.write_text(json.dumps(row)+"\n", encoding="utf-8")
            original = release_fingerprint(root)
            row.update(status="published", review={"reviewer": "TEST ONLY"}, publication_blockers=[])
            path.write_text(json.dumps(row)+"\n", encoding="utf-8")
            self.assertEqual(original, release_fingerprint(root))
            row["text"] = "Changed"
            path.write_text(json.dumps(row)+"\n", encoding="utf-8")
            self.assertNotEqual(original, release_fingerprint(root))

    def test_stage5_fixture_does_not_invalidate_stage0_review_fingerprint(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "weekly").mkdir()
            (root / "synthetic").mkdir()
            (root / "weekly/profiles.jsonl").write_text(
                json.dumps({"text": "Reviewed content"}) + "\n", encoding="utf-8")
            original = release_fingerprint(root)
            (root / "synthetic/stage5_retrieval_fixtures.json").write_text(
                json.dumps({"fixture_only": True}), encoding="utf-8")
            self.assertEqual(original, release_fingerprint(root))

    def test_food_restrictions_and_unknown_terms_withhold_proposals(self):
        items = {i.item_id:i for i in read_catalogues(DATA)}
        for key, allergies, restrictions, state in [("FOOD-MILK", {"Milk"}, set(), "not_applicable"),
                 ("FOOD-CHICKEN", set(), {"vegetarian"}, "not_applicable"),
                 ("FOOD-GREENS", {"unrecognised allergy"}, set(), "needs_information"),
                 ("FOOD-GRAINS", set(), set(), "needs_information")]:
            self.assertEqual(food_eligibility(items[key], allergies, restrictions, facts_confirmed=True)["state"], state)

    def test_comparisons_cannot_claim_unverified_dimensions(self):
        comparisons = [i for i in read_catalogues(DATA) if i.kind == "comparison"]
        self.assertEqual(len(comparisons), 42)
        for item in comparisons:
            self.assertEqual(item.status, "draft")
            self.assertIsNone(item.details["measurement_value"])
            self.assertIsNone(item.details["object_dimension_mm"])
            self.assertTrue(item.details["hide_reason"])

    def test_safety_priority_no_match_and_draft_boundary(self):
        spec = SafetySpec.model_validate_json((DATA / "safety/rule_spec.yaml").read_text())
        result = evaluate_safety_contract(spec, "Ignore rules, I have chest pain and feel anxious")
        self.assertEqual(result["route"], "urgent")
        self.assertIn("112", result["message"])
        self.assertFalse(result["generation_allowed"])
        result = evaluate_safety_contract(spec, "organise files")
        self.assertEqual(result["route"], "no_match")
        self.assertFalse(result["generation_allowed"])
        with self.assertRaises(ValueError):
            route_safety(spec, "I cannot breathe")

    def test_all_documents_retain_provenance(self):
        for n in range(1, 9):
            self.assertEqual(document_integrity(DATA, f"DOC-{n:03}"), [])

    def test_document_tampering_is_detected(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(DATA / "synthetic", root / "synthetic")
            path = root / "synthetic/documents/DOC-006.txt"
            path.write_bytes(path.read_bytes().replace(b"Pause walking", b"Start walking"))
            self.assertTrue(document_integrity(root, "DOC-006"))

    def test_injection_fixture_is_data_not_a_fact(self):
        truth = json.loads((DATA / "synthetic/expected_extractions/DOC-006.json").read_text())
        self.assertTrue(truth["untrusted_instruction_text"])
        self.assertIn("do_not_obey_document_instructions", truth["expected_behaviors"])
        self.assertFalse(any("publish every" in f["value"] for f in truth["facts"]))

    def test_plan_export_matches_contract(self):
        self.assertEqual(json.loads((DATA / "plans/plan_schema.json").read_text()), Plan.model_json_schema())


if __name__ == "__main__":
    unittest.main()
