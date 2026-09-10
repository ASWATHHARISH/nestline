"""Stage 1 ingestion, provenance, OCR, idempotency and publication checks."""

from copy import deepcopy
from datetime import date
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest
from unittest.mock import patch

import fitz

from app.schemas.content import ContentBundle
from app.schemas.foundation import CatalogueItem
from app.schemas.ingestion import (CorpusManifest, DevelopmentMeasurement,
                                   EvidenceCandidate, EvidenceReviewDecision,
                                   EvidenceReviewTask, IngestionRun, ParsedBlock,
                                   Stage1Audit, Stage1ReviewLedger)
from app.services.embeddings import DeterministicTestEmbeddingProvider
from app.services.ingestion_store import (latest_staging_run, publish_corpus,
                                          write_source_artifact, write_staging_run)
from app.services.public_ingestion import (admission_for, development_measurements_for,
                                           apply_review_decisions, run_ingestion)
from app.services.public_parsers import normalize_text, parse_html, parse_pdf
from app.services.source_capture import fetch_registered_source


TEXT = "Synthetic test passage for checking source linkage."
ROOT = Path(__file__).resolve().parents[1]
HTML = f"""<html><body><nav>Ignore this menu</nav><main><h1>Pregnancy week 10</h1>
<p>{TEXT}</p><ul><li>Keep this list structure.</li></ul>
<table><tr><th>Week</th><th>Topic</th></tr><tr><td>10</td><td>Test</td></tr></table>
<script>ignore()</script></main></body></html>""".encode()


class FixtureEmbeddingProvider:
    name = "fixture-provider"
    model = "fixture-model-v1"

    def embed(self, texts):
        return [[0.1, 0.2, 0.3] for _ in texts]


class FixtureOcrProvider:
    name = "fixture-ocr"
    version = "1.0"

    def extract_page(self, png, page_number):
        assert png.startswith(b"\x89PNG")
        return "Synthetic OCR passage long enough to satisfy the controlled extraction threshold.", 0.8


class BrokenOcrProvider:
    name = "broken-ocr"
    version = "1.0"

    def extract_page(self, png, page_number):
        raise TimeoutError("synthetic OCR timeout")


class BrokenEmbeddingProvider:
    name = "broken-provider"
    model = "broken-model"

    def embed(self, texts):
        raise TimeoutError("synthetic provider timeout")


def approved_bundle() -> ContentBundle:
    checksum = sha256(TEXT.encode()).hexdigest()
    review = {"reviewer": "TEST-REVIEWER", "reviewed_at": "2026-09-09",
              "kind": "content_reviewed", "notes": "TEST ONLY: ingestion fixture"}
    scope = {"stage": "pregnancy", "unit": "week", "start": 10, "end": 10}
    payload = {"sources": [{
        "source_id": "TEST-SOURCE", "title": "TEST ONLY", "publisher": "Test publisher",
        "canonical_url": "https://example.org/test", "jurisdiction": ["IN"],
        "document_type": "html", "topics": ["journey"], "evidence_lane": "weekly_profile",
        "status": "approved_for_capstone", "version_or_last_update": "test-v1",
        "last_checked_at": "2026-09-09", "reuse_status": "permitted",
        "allowed_use": ["store", "embed", "display"],
        "license_or_reuse_note": "Self-authored test text only",
        "prohibited_inferences": "Not medical evidence", "review": review,
        "content_checksum": checksum, "journey_stages": ["pregnancy"],
        "selected_sections": ["#test"], "snapshot_path": "guidelines/snapshots/test.json",
        "retrieved_at": "2026-09-10",
        "publisher_updated_at": "2026-09-01",
        "next_review_at": "2026-12-09",
        "revalidation_status": "current_capture",
        "paraphrase_permission": "permitted",
        "commercial_permission": "permitted",
    }], "evidence": [{
        "evidence_id": "TEST-EVIDENCE", "source_id": "TEST-SOURCE",
        "source_version": "test-v1", "source_checksum": checksum,
        "locator": "#test", "text": TEXT, "text_checksum": checksum,
        "applies_to": scope, "jurisdiction": ["IN"], "status": "published", "review": review,
    }], "fragments": [{
        "fragment_id": "TEST-FRAGMENT", "domain": "journey", "text": TEXT,
        "applies_to": scope, "jurisdiction": ["IN"],
        "evidence_span_ids": ["TEST-EVIDENCE"], "status": "published", "review": review,
    }], "profiles": [{
        "profile_id": "P10", "applies_to": scope, "status": "published",
        "hero": {"title": "Test profile", "development_evidence_ids": ["TEST-EVIDENCE"]},
        "guidance_fragment_ids": ["TEST-FRAGMENT"],
        "source_evidence_ids": ["TEST-EVIDENCE"], "jurisdiction": ["IN"],
        "review": review, "content_priority": "representative",
    }]}
    return ContentBundle.model_validate_json(json.dumps(payload))


def review_bundle() -> ContentBundle:
    """Return the same synthetic content with every publishable layer held in draft."""
    payload = approved_bundle().model_dump(mode="json")
    for collection in ("evidence", "fragments", "profiles"):
        payload[collection][0]["status"] = "draft"
        payload[collection][0]["review"] = None
    return ContentBundle.model_validate_json(json.dumps(payload))


def food_catalogue(status="published", blockers=None):
    return CatalogueItem(item_id="TEST-FOOD", kind="food", title="Test food",
                         description="Synthetic catalogue link.",
                         applies_to={"stage": "pregnancy", "unit": "week", "start": 10, "end": 10},
                         jurisdiction=["IN"], evidence_span_ids=["TEST-EVIDENCE"],
                         status=status, blockers=blockers or [])


class ParserTests(unittest.TestCase):
    def test_html_preserves_structure_and_removes_page_chrome(self):
        blocks, issues = parse_html("TEST-SOURCE", HTML)
        self.assertFalse(issues)
        self.assertEqual([block.block_kind for block in blocks],
                         ["heading", "paragraph", "list_item", "table"])
        self.assertNotIn("ignore this menu", " ".join(block.normalized_text for block in blocks))
        self.assertIn("Pregnancy week 10", blocks[1].heading_path)
        self.assertIn("Week | Topic", blocks[-1].text)

    def test_normalizer_handles_spacing_quotes_and_dash_variants(self):
        self.assertEqual(normalize_text("  A\u2014B  \u201cC\u201d "), 'a-b "c"')

    def test_pdf_preserves_page_anchor(self):
        document = fitz.open()
        page = document.new_page()
        page.insert_text((72, 72), "Synthetic PDF passage with enough text for deterministic parsing and anchoring.")
        raw = document.tobytes()
        document.close()
        blocks, issues = parse_pdf("TEST-PDF", raw)
        self.assertFalse([issue for issue in issues if issue.severity == "error"])
        self.assertTrue(blocks)
        self.assertTrue(all(block.page == 1 for block in blocks))
        self.assertTrue(all(block.extraction_method == "pdf_text" for block in blocks))

    def test_image_only_pdf_stops_for_ocr(self):
        document = fitz.open()
        document.new_page()
        raw = document.tobytes()
        document.close()
        blocks, issues = parse_pdf("TEST-PDF", raw)
        self.assertFalse(blocks)
        self.assertEqual([issue.code for issue in issues], ["NEEDS_OCR"])

    def test_configured_ocr_adapter_is_used_and_labelled(self):
        document = fitz.open()
        document.new_page()
        raw = document.tobytes()
        document.close()
        blocks, issues = parse_pdf("TEST-PDF", raw, ocr_provider=FixtureOcrProvider())
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].extraction_method, "ocr")
        self.assertEqual([issue.code for issue in issues], ["OCR_APPLIED"])

    def test_ocr_failure_is_reported_without_text(self):
        document = fitz.open()
        document.new_page()
        raw = document.tobytes()
        document.close()
        blocks, issues = parse_pdf("TEST-PDF", raw, ocr_provider=BrokenOcrProvider())
        self.assertFalse(blocks)
        self.assertEqual([issue.code for issue in issues], ["OCR_FAILED"])

    def test_corrupt_and_locked_pdfs_fail_safely(self):
        _blocks, issues = parse_pdf("TEST-PDF", b"not a pdf")
        self.assertEqual(issues[0].code, "PDF_OPEN_FAILED")
        document = fitz.open()
        document.new_page().insert_text((72, 72), "Password protected synthetic document")
        raw = document.tobytes(encryption=fitz.PDF_ENCRYPT_AES_256,
                               owner_pw="owner", user_pw="reader")
        document.close()
        _blocks, issues = parse_pdf("TEST-PDF", raw)
        self.assertEqual(issues[0].code, "PDF_LOCKED")


class IngestionTests(unittest.TestCase):
    def test_exported_schema_matches_stage1_contracts(self):
        exported = json.loads((ROOT / "data/schemas/ingestion.schema.json").read_text(encoding="utf-8"))
        expected = {"$schema": "https://json-schema.org/draft/2020-12/schema",
                    "records": {"parsed_block": ParsedBlock.model_json_schema(),
                                "evidence_candidate": EvidenceCandidate.model_json_schema(),
                                "evidence_review_decision": EvidenceReviewDecision.model_json_schema(),
                                "evidence_review_task": EvidenceReviewTask.model_json_schema(),
                                "stage1_review_ledger": Stage1ReviewLedger.model_json_schema(),
                                "ingestion_run": IngestionRun.model_json_schema(),
                                "corpus_manifest": CorpusManifest.model_json_schema(),
                                "stage1_audit": Stage1Audit.model_json_schema()}}
        self.assertEqual(exported, expected)

    def test_approved_source_creates_one_cited_embedding_and_future_metadata(self):
        run = run_ingestion(approved_bundle(), "TEST-SOURCE", HTML,
                            retrieved_at=date(2026, 9, 10),
                            embedding_provider=FixtureEmbeddingProvider(),
                            catalogue_items=[food_catalogue()])
        self.assertEqual(run.outcome, "publishable")
        self.assertEqual(len(run.candidates), 1)
        self.assertEqual(len(run.embeddings), 1)
        candidate = run.candidates[0]
        self.assertTrue(candidate.source_anchor_verified)
        self.assertEqual(candidate.linked_profile_ids, ["P10"])
        self.assertEqual(candidate.linked_catalogue_item_ids, ["TEST-FOOD"])
        self.assertIn("nutrition_focus", candidate.display_slots)
        self.assertTrue({"allergies", "dietary_restrictions", "medical_history"}
                        <= set(candidate.personal_fact_dependencies))
        self.assertEqual(candidate.original_text, TEXT)
        self.assertEqual({block.block_id for block in run.governed_blocks},
                         set(candidate.source_block_ids))

    def test_draft_records_enter_review_queue_and_never_embeddings(self):
        run = run_ingestion(review_bundle(), "TEST-SOURCE", HTML,
                            retrieved_at=date(2026, 9, 10),
                            embedding_provider=FixtureEmbeddingProvider())
        self.assertEqual(run.outcome, "review_required")
        self.assertEqual(run.candidates[0].state, "review_required")
        self.assertEqual(len(run.review_tasks), 1)
        self.assertFalse(run.embeddings)

    def test_invalid_cross_record_bundle_is_rejected_before_parsing(self):
        payload = approved_bundle().model_dump(mode="json")
        payload["evidence"][0]["source_version"] = "different-version"
        run = run_ingestion(ContentBundle.model_validate_json(json.dumps(payload)),
                            "TEST-SOURCE", HTML, retrieved_at=date(2026, 9, 10),
                            embedding_provider=FixtureEmbeddingProvider())
        self.assertEqual(run.outcome, "rejected")
        self.assertIsNone(run.artifact)
        self.assertIn("CONTENT_BUNDLE_INVALID", {issue.code for issue in run.issues})

    def test_old_retrieval_date_cannot_bypass_current_currency_gate(self):
        payload = approved_bundle().model_dump(mode="json")
        payload["sources"][0]["next_review_at"] = "2026-09-09"
        bundle = ContentBundle.model_validate_json(json.dumps(payload))
        run = run_ingestion(bundle, "TEST-SOURCE", HTML,
                            retrieved_at=date(2025, 1, 1), as_of=date(2026, 9, 10),
                            embedding_provider=FixtureEmbeddingProvider())
        self.assertEqual(run.admission.decision, "parse_for_review")
        self.assertEqual(run.outcome, "review_required")
        self.assertFalse(run.embeddings)

    def test_missing_anchor_rejects_candidate(self):
        run = run_ingestion(approved_bundle(), "TEST-SOURCE", b"<main><p>Different text entirely.</p></main>",
                            retrieved_at=date(2026, 9, 10),
                            embedding_provider=FixtureEmbeddingProvider())
        self.assertEqual(run.outcome, "rejected")
        self.assertEqual(run.candidates[0].state, "rejected")
        self.assertIn("ANCHOR_NOT_FOUND", {issue.code for issue in run.issues})
        self.assertFalse(run.embeddings)

    def test_rejected_source_is_not_parsed_or_embedded(self):
        payload = approved_bundle().model_dump(mode="json")
        payload["sources"][0]["status"] = "excluded"
        bundle = ContentBundle.model_validate_json(json.dumps(payload))
        self.assertEqual(admission_for(bundle.sources[0], date(2026, 9, 10)).decision, "rejected")
        run = run_ingestion(bundle, "TEST-SOURCE", HTML, retrieved_at=date(2026, 9, 10),
                            embedding_provider=FixtureEmbeddingProvider())
        self.assertEqual(run.outcome, "rejected")
        self.assertIsNone(run.artifact)
        self.assertFalse(run.candidates)
        self.assertFalse(run.embeddings)

    def test_approved_retrievable_evidence_requires_provider(self):
        run = run_ingestion(approved_bundle(), "TEST-SOURCE", HTML,
                            retrieved_at=date(2026, 9, 10))
        self.assertEqual(run.outcome, "rejected")
        self.assertIn("EMBEDDING_PROVIDER_REQUIRED", {issue.code for issue in run.issues})

    def test_embedding_provider_failure_is_a_safe_rejection(self):
        run = run_ingestion(approved_bundle(), "TEST-SOURCE", HTML,
                            retrieved_at=date(2026, 9, 10),
                            embedding_provider=BrokenEmbeddingProvider())
        self.assertEqual(run.outcome, "rejected")
        self.assertFalse(run.embeddings)
        self.assertIn("EMBEDDING_FAILED", {issue.code for issue in run.issues})

    def test_duplicate_units_are_reported_and_block_publication(self):
        payload = approved_bundle().model_dump(mode="json")
        duplicate = deepcopy(payload["evidence"][0])
        duplicate["evidence_id"] = "TEST-EVIDENCE-2"
        payload["evidence"].append(duplicate)
        run = run_ingestion(ContentBundle.model_validate_json(json.dumps(payload)), "TEST-SOURCE", HTML,
                            retrieved_at=date(2026, 9, 10),
                            embedding_provider=FixtureEmbeddingProvider())
        self.assertEqual(run.outcome, "rejected")
        self.assertIn("DUPLICATE_CANDIDATE", {issue.code for issue in run.issues})

    def test_source_change_invalidates_profile_catalogue_and_cache(self):
        bundle = approved_bundle()
        catalogue = [food_catalogue()]
        first = run_ingestion(bundle, "TEST-SOURCE", HTML, retrieved_at=date(2026, 9, 10),
                              embedding_provider=FixtureEmbeddingProvider(), catalogue_items=catalogue)
        changed_html = HTML.replace(b"</main>", b"<!-- publisher update --></main>")
        second = run_ingestion(bundle, "TEST-SOURCE", changed_html, retrieved_at=date(2026, 9, 10),
                               previous=first, embedding_provider=FixtureEmbeddingProvider(),
                               catalogue_items=catalogue)
        self.assertEqual(second.diff.changed_evidence_ids, ["TEST-EVIDENCE"])
        self.assertEqual(second.diff.invalidated_profile_ids, ["P10"])
        self.assertEqual(second.diff.invalidated_catalogue_item_ids, ["TEST-FOOD"])
        self.assertIn("public-source:TEST-SOURCE", second.diff.invalidate_cache_scopes)
        self.assertEqual(second.candidates[0].state, "review_required")
        self.assertEqual(second.outcome, "review_required")
        self.assertFalse(second.embeddings)

    def test_governance_change_without_new_bytes_forces_review(self):
        first = run_ingestion(approved_bundle(), "TEST-SOURCE", HTML,
                              retrieved_at=date(2026, 9, 10),
                              embedding_provider=FixtureEmbeddingProvider())
        payload = approved_bundle().model_dump(mode="json")
        payload["sources"][0]["attribution_text"] = "Updated attribution requirement"
        governed_update = ContentBundle.model_validate_json(json.dumps(payload))
        second = run_ingestion(governed_update, "TEST-SOURCE", HTML,
                               retrieved_at=date(2026, 9, 11), previous=first,
                               embedding_provider=FixtureEmbeddingProvider())
        self.assertNotEqual(first.candidates[0].source_governance_checksum,
                            second.candidates[0].source_governance_checksum)
        self.assertEqual(second.candidates[0].state, "review_required")
        self.assertEqual(second.outcome, "review_required")
        self.assertFalse(second.embeddings)

    def test_cross_date_capture_keeps_one_logical_version(self):
        first = run_ingestion(approved_bundle(), "TEST-SOURCE", HTML,
                              retrieved_at=date(2026, 9, 10), as_of=date(2026, 9, 10),
                              embedding_provider=FixtureEmbeddingProvider())
        second = run_ingestion(approved_bundle(), "TEST-SOURCE", HTML,
                               retrieved_at=date(2026, 9, 11), as_of=date(2026, 9, 11),
                               previous=first, embedding_provider=FixtureEmbeddingProvider())
        self.assertEqual(first.logical_version_id, second.logical_version_id)
        self.assertNotEqual(first.run_id, second.run_id)
        self.assertEqual(second.diff.unchanged_candidate_ids, ["C-TEST-EVIDENCE"])

    def test_review_decisions_are_role_scoped_and_version_bound(self):
        checksum = "a" * 64
        accepted = EvidenceReviewDecision(
            task_id="REV-TEST", candidate_id="C-TEST", evidence_id="E-TEST", source_id="S-TEST",
            role="product", decision="accepted", reviewer_name="Test reviewer",
            reviewer_capacity="TEST ONLY product fixture", reviewed_at=date(2026, 9, 10),
            reason="Synthetic acceptance.", candidate_checksum=checksum)
        task = EvidenceReviewTask(
            task_id="REV-TEST", candidate_id="C-TEST", evidence_id="E-TEST",
            source_id="S-TEST", candidate_checksum=checksum,
            required_checks=["wording"], required_roles=["product", "clinical"],
            blocking_reasons=["Synthetic pending role."], decisions=[accepted], status="pending")
        self.assertEqual(task.decisions[0].role, "product")
        with self.assertRaises(ValueError):
            EvidenceReviewDecision(
                task_id="REV-TEST", candidate_id="C-TEST", evidence_id="E-TEST", source_id="S-TEST",
                role="clinical", decision="changes_requested", reviewer_name="Test reviewer",
                reviewer_capacity="TEST ONLY clinical fixture", reviewed_at=date(2026, 9, 10),
                reason="Change needed.", candidate_checksum=checksum)

    def test_ingestion_attaches_only_current_task_decisions(self):
        first = run_ingestion(review_bundle(), "TEST-SOURCE", HTML,
                              retrieved_at=date(2026, 9, 10))
        task = first.review_tasks[0]
        decision = EvidenceReviewDecision(
            task_id=task.task_id, candidate_id=task.candidate_id,
            evidence_id=task.evidence_id, source_id=task.source_id,
            role="product", decision="accepted", reviewer_name="Test reviewer",
            reviewer_capacity="TEST ONLY product fixture", reviewed_at=date(2026, 9, 10),
            reason="Placement is suitable for this synthetic test.",
            candidate_checksum=task.candidate_checksum)
        ledger = Stage1ReviewLedger(decisions=[decision])
        second = run_ingestion(review_bundle(), "TEST-SOURCE", HTML,
                               retrieved_at=date(2026, 9, 10),
                               review_decisions=ledger.decisions)
        self.assertEqual(second.review_tasks[0].decisions, [decision])
        self.assertEqual(second.review_tasks[0].status, "pending")

        stale = decision.model_copy(update={"task_id": "REV-STALE"})
        with self.assertRaisesRegex(ValueError, "absent or stale"):
            run_ingestion(review_bundle(), "TEST-SOURCE", HTML,
                          retrieved_at=date(2026, 9, 10),
                          review_decisions=[stale])

    def test_post_parse_review_attachment_keeps_checksum_gate(self):
        run = run_ingestion(review_bundle(), "TEST-SOURCE", HTML,
                            retrieved_at=date(2026, 9, 10))
        task = run.review_tasks[0]
        decision = EvidenceReviewDecision(
            task_id=task.task_id, candidate_id=task.candidate_id,
            evidence_id=task.evidence_id, source_id=task.source_id,
            role="product", decision="accepted", reviewer_name="Test reviewer",
            reviewer_capacity="TEST ONLY product fixture", reviewed_at=date(2026, 9, 10),
            reason="Placement is suitable for this synthetic test.",
            candidate_checksum=task.candidate_checksum)
        decided = apply_review_decisions(run, [decision])
        self.assertEqual(decided.review_tasks[0].decisions, [decision])
        with self.assertRaisesRegex(ValueError, "absent or stale"):
            apply_review_decisions(run, [decision.model_copy(update={"task_id": "REV-STALE"})])

    def test_general_measurements_reject_incomplete_or_inverted_ranges(self):
        with self.assertRaises(ValueError):
            DevelopmentMeasurement(kind="length", unit="cm", basis="general_source_range",
                                   variability_notice="Synthetic test.")
        with self.assertRaises(ValueError):
            DevelopmentMeasurement(kind="length", minimum=3, maximum=2, unit="cm",
                                   basis="general_source_range", variability_notice="Synthetic test.")

    def test_curated_measurement_is_bound_to_exact_evidence_checksum(self):
        payload = approved_bundle().evidence[0].model_dump(mode="json")
        text = "The embryo is now known as a fetus and is about 2.5 cm in length."
        payload.update({"evidence_id": "E-P10-DEVELOPMENT", "text": text,
                        "text_checksum": sha256(text.encode()).hexdigest()})
        evidence = approved_bundle().evidence[0].__class__.model_validate_json(json.dumps(payload))
        measurements, current = development_measurements_for(evidence)
        self.assertTrue(current)
        self.assertEqual((measurements[0].value, measurements[0].unit), (2.5, "cm"))
        bundle_payload = approved_bundle().model_dump(mode="json")
        bundle_payload["evidence"][0].update(payload)
        bundle_payload["fragments"][0]["evidence_span_ids"] = ["E-P10-DEVELOPMENT"]
        bundle_payload["profiles"][0]["hero"]["development_evidence_ids"] = ["E-P10-DEVELOPMENT"]
        bundle_payload["profiles"][0]["source_evidence_ids"] = ["E-P10-DEVELOPMENT"]
        bundle = ContentBundle.model_validate_json(json.dumps(bundle_payload))
        source_html = f"<main><p>{text}</p></main>".encode()
        run = run_ingestion(bundle, "TEST-SOURCE", source_html,
                            retrieved_at=date(2026, 9, 10),
                            embedding_provider=FixtureEmbeddingProvider())
        self.assertEqual(run.candidates[0].development_measurements, measurements)
        stale = evidence.model_copy(update={"text_checksum": "0" * 64})
        self.assertEqual(development_measurements_for(stale), ([], False))


class StorageTests(unittest.TestCase):
    def _committed_run(self, provider=None):
        return run_ingestion(approved_bundle(), "TEST-SOURCE", HTML,
                             retrieved_at=date(2026, 9, 10), dry_run=False,
                             embedding_provider=provider or FixtureEmbeddingProvider())

    @staticmethod
    def _publish(runs, root, version):
        with patch("app.services.ingestion_store.approval_errors", return_value=[]), \
                patch("app.services.ingestion_store.release_fingerprint", return_value="a" * 64):
            return publish_corpus(runs, root, version, governance_data=root)

    def test_staging_and_artifact_writes_are_idempotent(self):
        run = self._committed_run()
        with TemporaryDirectory() as folder:
            root = Path(folder)
            path, state = write_staging_run(run, root / "staging")
            self.assertEqual(state, "created")
            self.assertTrue(path.exists())
            self.assertEqual(write_staging_run(run, root / "staging")[1], "unchanged")
            artifact, state = write_source_artifact(run, HTML, root / "artifacts")
            self.assertEqual(state, "created")
            self.assertEqual(write_source_artifact(run, HTML, root / "artifacts")[1], "unchanged")
            self.assertEqual(artifact.read_bytes(), HTML)

    def test_latest_staging_run_is_automatic_and_source_scoped(self):
        first = self._committed_run()
        second = run_ingestion(approved_bundle(), "TEST-SOURCE", HTML,
                               retrieved_at=date(2026, 9, 11), as_of=date(2026, 9, 11),
                               dry_run=False, previous=first,
                               embedding_provider=FixtureEmbeddingProvider())
        with TemporaryDirectory() as folder:
            root = Path(folder)
            write_staging_run(first, root)
            write_staging_run(second, root)
            latest = latest_staging_run(root, "TEST-SOURCE")
            self.assertEqual(latest.run_id, second.run_id)
            self.assertIsNone(latest_staging_run(root, "OTHER-SOURCE"))

    def test_corpus_is_hashed_and_immutable(self):
        run = self._committed_run()
        with TemporaryDirectory() as folder:
            root = Path(folder)
            manifest = self._publish([run], root, "corpus-test-v1")
            self.assertEqual(manifest.embedding_provider, "fixture-provider")
            self.assertEqual(manifest.release_fingerprint, "a" * 64)
            self.assertTrue((root / "corpus-test-v1/blocks.jsonl").exists())
            self.assertTrue((root / "corpus-test-v1/manifest.json").exists())
            with self.assertRaises(FileExistsError):
                self._publish([run], root, "corpus-test-v1")

    def test_corpus_publication_requires_current_five_role_release_gate(self):
        run = self._committed_run()
        with TemporaryDirectory() as folder, \
                patch("app.services.ingestion_store.approval_errors",
                      return_value=["release needs actual clinical approval"]):
            with self.assertRaisesRegex(ValueError, "clinical approval"):
                publish_corpus([run], Path(folder), "corpus-test-v1",
                               governance_data=Path(folder))

    def test_test_vectors_can_never_be_published(self):
        run = self._committed_run(DeterministicTestEmbeddingProvider())
        with TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "test embeddings"):
                self._publish([run], Path(folder), "corpus-test-v1")

    def test_fixed_quote_corpus_has_no_embeddings(self):
        payload = approved_bundle().model_dump(mode="json")
        source = payload["sources"][0]
        source.update({"delivery_mode": "fixed_quote", "allowed_use": ["store", "display"],
                       "attribution_text": "Synthetic attribution.", "max_quote_sections": 1,
                       "paraphrase_permission": "restricted"})
        payload["fragments"][0]["presentation"] = "quotation"
        payload["fragments"][0]["text"] = TEXT
        bundle = ContentBundle.model_validate_json(json.dumps(payload))
        run = run_ingestion(bundle, "TEST-SOURCE", HTML, retrieved_at=date(2026, 9, 10),
                            dry_run=False)
        self.assertEqual(run.outcome, "publishable")
        self.assertFalse(run.embeddings)
        with TemporaryDirectory() as folder:
            manifest = self._publish([run], Path(folder), "fixed-quote-v1")
            self.assertEqual(manifest.embedding_provider, "none-fixed-quote-only")
            with self.assertRaisesRegex(ValueError, "governed excerpts"):
                write_source_artifact(run, HTML, Path(folder) / "artifacts")

    def test_dry_run_cannot_be_written_or_published(self):
        run = run_ingestion(approved_bundle(), "TEST-SOURCE", HTML,
                            retrieved_at=date(2026, 9, 10),
                            embedding_provider=FixtureEmbeddingProvider())
        with TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "dry-run"):
                write_staging_run(run, Path(folder))
            with self.assertRaisesRegex(ValueError, "committed"):
                self._publish([run], Path(folder), "corpus-test-v1")


class CaptureTests(unittest.TestCase):
    class Headers:
        def __init__(self, content_type="text/html", length=None):
            self.content_type = content_type
            self.length = length

        def get(self, key):
            return self.length if key == "Content-Length" else None

        def get_content_type(self):
            return self.content_type

    class Response:
        def __init__(self, body=HTML, url="https://example.org/test", **headers):
            self.body = body
            self.url = url
            self.headers = CaptureTests.Headers(**headers)

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def geturl(self):
            return self.url

        def read(self, amount):
            return self.body[:amount]

    @patch("app.services.source_capture._public_host")
    @patch("app.services.source_capture.urlopen")
    def test_exact_registered_capture(self, urlopen, _public_host):
        urlopen.return_value = self.Response()
        self.assertEqual(fetch_registered_source(approved_bundle().sources[0]), HTML)

    @patch("app.services.source_capture._public_host")
    @patch("app.services.source_capture.urlopen")
    def test_cross_host_redirect_and_size_limit_are_blocked(self, urlopen, _public_host):
        source = approved_bundle().sources[0]
        urlopen.return_value = self.Response(url="https://evil.example/test")
        with self.assertRaisesRegex(ValueError, "redirected"):
            fetch_registered_source(source)
        urlopen.return_value = self.Response(length="999")
        with self.assertRaisesRegex(ValueError, "size limit"):
            fetch_registered_source(source, maximum_bytes=10)


if __name__ == "__main__":
    unittest.main()
