"""Prevent draft localisation and quote permissions from becoming silent approval."""

import unittest
from pathlib import Path

from pydantic import ValidationError

from app.services.content_selection import select_content
from app.services.content_validation import review_readiness_errors
from scripts.validate_content import load_bundle
from tests.test_content import check, fixture
from tests.test_selection_and_snapshots import bundle

ROOT = Path(__file__).resolve().parents[1]


def quote_fixture():
    data = fixture()
    data["sources"][0].update(delivery_mode="fixed_quote", allowed_use=["store", "display"],
                              attribution_text="Synthetic test publisher", max_quote_sections=1)
    data["fragments"][0]["presentation"] = "quotation"
    return data


class ReviewAndLicensingTests(unittest.TestCase):
    def test_draft_localisation_cannot_be_published_without_its_own_review(self):
        data = fixture()
        data["sources"][0]["jurisdiction"] = ["US"]
        data["evidence"][0]["localisation"] = {
            "source_jurisdiction": ["US"], "target_jurisdiction": ["IN"],
            "category": "general_education", "rationale": "Synthetic adoption test", "review": None}
        for records in ("evidence", "fragments", "profiles"):
            data[records][0]["status"] = "draft"
        self.assertTrue(check(data).valid)
        data["evidence"][0]["status"] = "published"
        self.assertFalse(check(data).valid)
        data["evidence"][0]["localisation"]["review"] = data["evidence"][0]["review"]
        self.assertTrue(check(data).valid)
        data["evidence"][0]["localisation"]["source_jurisdiction"] = ["UK"]
        self.assertFalse(check(data).valid)

    def test_quote_only_content_is_excluded_from_model_retrieval(self):
        content = bundle(quote_fixture())
        result = select_content(content, content.profiles[0].applies_to, "IN")
        self.assertEqual(result["retrievable_fragment_ids"], [])
        self.assertEqual(result["fixed_quote_fragment_ids"], ["TEST-FRAGMENT"])
        self.assertEqual(result["quotation_cards"][0]["attribution"], "Synthetic test publisher")
        self.assertEqual(result["quotation_cards"][0]["text"], content.evidence[0].text)

    def test_quote_permission_cannot_expand_to_embeddings_or_extra_sections(self):
        for attack in ("embed", "extra_section", "missing_attribution"):
            with self.subTest(attack=attack):
                data = quote_fixture()
                source = data["sources"][0]
                if attack == "embed":
                    source["allowed_use"].append("embed")
                elif attack == "extra_section":
                    source["selected_sections"].append("unauthorised quote")
                else:
                    source["attribution_text"] = ""
                with self.assertRaises(ValidationError):
                    bundle(data)

    def test_quote_only_fragment_cannot_be_rewritten(self):
        data = quote_fixture()
        data["fragments"][0]["text"] = "A generated interpretation of the source."
        self.assertFalse(check(data).valid)

    def test_review_ready_requires_domain_cards_and_empty_slot_explanations(self):
        content = load_bundle(ROOT / "data")
        self.assertEqual(review_readiness_errors(content), [])
        profile = next(p for p in content.profiles if p.profile_id == "P10")
        profile.card_slots.nutrition_focus = []
        self.assertTrue(review_readiness_errors(content))

    def test_typo_in_empty_slot_decision_is_rejected(self):
        content = load_bundle(ROOT / "data")
        content.profiles[0].slot_notes["nutriton_focus"] = "Misspelled slot"
        self.assertTrue(any("unknown slot note" in e for e in review_readiness_errors(content)))


if __name__ == "__main__":
    unittest.main()
