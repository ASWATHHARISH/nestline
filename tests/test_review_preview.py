"""Checks for the governed three-profile reviewer preview."""

from pathlib import Path
import unittest

from app.schemas.ingestion import Stage1ReviewLedger
from app.services.foundation import read_catalogues
from app.services.review_preview import build_review_preview, comparison_gate
from scripts.export_stage1_slice_review import render as render_slice_review
from scripts.validate_content import load_bundle

ROOT = Path(__file__).resolve().parents[1]


class ReviewPreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = load_bundle(ROOT / "data")
        cls.ledger = Stage1ReviewLedger.model_validate_json(
            (ROOT / "data/reviews/ingestion_decisions.json").read_text(encoding="utf-8"))

    def test_kajal_decisions_cover_every_card_in_the_three_profile_slice(self):
        evidence_ids = set()
        for profile_id in ("PC00", "P10", "PP01"):
            preview = build_review_preview(self.bundle, self.ledger, profile_id)
            for cards in preview["cards_by_slot"].values():
                for card in cards:
                    evidence_ids.update(card["evidence_ids"])
                    self.assertEqual(card["accepted_roles"], ["content", "product"])
                    self.assertEqual(card["pending_roles"],
                                     ["licence", "clinical", "india_localisation"])
        self.assertEqual(len(evidence_ids), 27)
        self.assertEqual(len(self.ledger.decisions), 54)

    def test_unknown_conditions_are_visible_as_questions_not_clearance(self):
        preview = build_review_preview(
            self.bundle, self.ledger, "P10", confirmed=frozenset({"pregnancy_confirmed"}))
        movement = preview["cards_by_slot"]["movement_focus"]
        self.assertTrue(movement)
        self.assertTrue(all(card["state"] == "needs_information" for card in movement))

        cleared = build_review_preview(
            self.bundle, self.ledger, "P10",
            confirmed=frozenset({"pregnancy_confirmed", "exercise_clearance"}),
            absent=frozenset({"movement_restriction", "current_warning_symptom"}))
        self.assertTrue(all(card["state"] == "shown"
                            for card in cleared["cards_by_slot"]["movement_focus"]))

    def test_postpartum_scenarios_do_not_infer_delivery_or_feeding_facts(self):
        missing = build_review_preview(self.bundle, self.ledger, "PP01")
        self.assertEqual(missing["cards_by_slot"]["nutrition_focus"][0]["state"],
                         "needs_information")
        caesarean = build_review_preview(
            self.bundle, self.ledger, "PP01",
            confirmed=frozenset({"breastfeeding", "complicated_delivery_or_caesarean"}),
            absent=frozenset({"uncomplicated_delivery", "current_warning_symptom"}))
        movement = caesarean["cards_by_slot"]["movement_focus"]
        self.assertEqual([card["state"] for card in movement],
                         ["not_applicable", "shown"])

    def test_all_size_comparisons_are_unverified_and_hidden(self):
        gate = comparison_gate(read_catalogues(ROOT / "data"))
        self.assertEqual(gate, {"total": 42, "verified_count": 0,
                                "published_count": 0, "hidden_count": 42,
                                "partially_verified_count": 0,
                                "safe": True})

    def test_specialist_handoff_is_reproducible_from_tracked_records(self):
        rendered = render_slice_review(
            ROOT / "data/reviews/ingestion_decisions.json",
            ROOT / "data/ingestion/audit/stage1-source-audit.json",
        )
        checked_in = (ROOT / "docs/STAGE-1-PC00-P10-PP01-REVIEW-HANDOFF.md").read_text(
            encoding="utf-8")
        self.assertEqual(rendered.rstrip(), checked_in.rstrip())


if __name__ == "__main__":
    unittest.main()
