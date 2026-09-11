"""Build deterministic Stage 4 OCR, graph-truth, and upload-failure fixtures."""

from __future__ import annotations

import csv
from hashlib import sha256
import json
from pathlib import Path
import random

import fitz
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/synthetic"
DOCUMENTS = BASE / "documents"
TRUTH = BASE / "expected_extractions"
GRAPH = BASE / "expected_graph_changes"
NOISY = BASE / "noisy_variants"
EDGES = BASE / "upload_edge_cases"


FIELD_NODE_TYPES = {
    "reported_allergy": "Allergy",
    "new_allergy_information": "Allergy",
    "medicine_name": "MedicationMention",
    "recorded_dose": "MedicationMention",
    "recorded_frequency": "MedicationMention",
    "route": "MedicationMention",
    "pregnancy_week": "JourneyState",
    "estimated_due_date": "JourneyState",
    "delivery_date": "JourneyState",
    "current_journey": "JourneyState",
    "followup_date": "Appointment",
    "followup_reason": "Question",
    "recorded_instruction": "DocumentFact",
    "instruction_scope": "DocumentFact",
    "new_restriction": "Condition",
}


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")


def _graph_truth(document_id: str, extraction: dict) -> dict:
    nodes = [
        {
            "key": f"document:{document_id}",
            "type": "Document",
            "created_when": "extraction_recorded",
        }
    ]
    edges = []
    for fact in extraction["facts"]:
        if fact["extraction_disposition"] == "abstain":
            continue
        field = fact["field"]
        node_type = FIELD_NODE_TYPES.get(field, "DocumentFact")
        fact_key = f"fact:{document_id}:{field}"
        nodes.append({
            "key": fact_key,
            "type": node_type,
            "created_when": "user_confirms_candidate",
            "source_field": field,
        })
        edges.append({
            "from": fact_key,
            "to": f"document:{document_id}",
            "type": "EXTRACTED_FROM",
            "created_when": "user_confirms_candidate",
        })
    if document_id == "DOC-006":
        edges.extend([
            {
                "from": "fact:DOC-006:recorded_instruction",
                "to": "fact:DOC-005:recorded_instruction",
                "type": "CONFLICTS_WITH",
                "created_when": "user_keeps_conflict",
            },
            {
                "from": "question:DOC-006:movement-clarification",
                "to": "fact:DOC-006:recorded_instruction",
                "type": "NEEDS_CLARIFICATION",
                "created_when": "user_keeps_conflict",
            },
        ])
        nodes.append({
            "key": "question:DOC-006:movement-clarification",
            "type": "Question",
            "created_when": "user_keeps_conflict",
        })
    return {
        "schema_version": "stage4-graph-truth-v1",
        "document_id": document_id,
        "workspace_key": "DEMO-MAYA",
        "nodes": nodes,
        "edges": edges,
        "expected_side_effects": extraction["expected_behaviors"],
        "proposal_side_effects": [],
    }


def build_graph_truth() -> None:
    GRAPH.mkdir(parents=True, exist_ok=True)
    for path in sorted(TRUTH.glob("DOC-*.json")):
        extraction = json.loads(path.read_text(encoding="utf-8"))
        _write_json(GRAPH / path.name, _graph_truth(extraction["document_id"], extraction))

    inventory_path = BASE / "document_inventory.csv"
    with inventory_path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        row["typed_graph_truth"] = f"expected_graph_changes/{row['document_id']}.json"
    with inventory_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_noisy_variant() -> None:
    NOISY.mkdir(parents=True, exist_ok=True)
    source_pdf = DOCUMENTS / "DOC-003.pdf"
    with fitz.open(source_pdf) as document:
        pixmap = document[0].get_pixmap(matrix=fitz.Matrix(1.45, 1.45), alpha=False)
        image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
    image = image.convert("L")
    image = ImageEnhance.Contrast(image).enhance(0.82)
    image = image.filter(ImageFilter.GaussianBlur(0.55))
    image = image.rotate(0.65, resample=Image.Resampling.BICUBIC, expand=False, fillcolor=248)
    draw = ImageDraw.Draw(image)
    rng = random.Random(4003)
    for _ in range(90):
        x = rng.randrange(0, image.width)
        y = rng.randrange(0, image.height)
        draw.point((x, y), fill=rng.randrange(130, 225))
    output = NOISY / "DOC-003-noisy.png"
    image.save(output, format="PNG", optimize=True)
    source_truth = json.loads((TRUTH / "DOC-003.json").read_text(encoding="utf-8"))
    _write_json(NOISY / "DOC-003-noisy.expected.json", {
        "schema_version": "stage4-ocr-truth-v1",
        "source_document_id": "DOC-003",
        "fictional": True,
        "image_sha256": sha256(output.read_bytes()).hexdigest(),
        "expected_ocr_text": (DOCUMENTS / "DOC-003.txt").read_text(encoding="utf-8"),
        "expected_fields": [fact["field"] for fact in source_truth["facts"]],
        "minimum_exact_field_recall": 1.0,
        "purpose": "controlled low-contrast, blur, rotation and sparse-noise OCR path",
    })


def build_upload_edge_cases() -> None:
    EDGES.mkdir(parents=True, exist_ok=True)
    source = fitz.open(DOCUMENTS / "DOC-001.pdf")
    source.save(
        EDGES / "locked-fictional.pdf",
        encryption=fitz.PDF_ENCRYPT_AES_256,
        owner_pw="fictional-owner",
        user_pw="fictional-only",
    )
    source.close()
    (EDGES / "corrupt-fictional.pdf").write_bytes(
        b"%PDF-1.7\nFICTIONAL DEMO DATA\ntruncated object"
    )
    (EDGES / "unsupported-fictional.rtf").write_text(
        r"{\rtf1 FICTIONAL DEMO DATA - unsupported fixture}", encoding="utf-8"
    )

    wrong = fitz.open()
    page = wrong.new_page()
    page.insert_text((50, 60), "FICTIONAL DEMO DATA - NOT A REAL MEDICAL RECORD")
    page.insert_text((50, 90), "persona: Other Fictional Person")
    page.insert_text((50, 120), "This intentionally does not belong to Maya.")
    wrong.save(EDGES / "wrong-person-fictional.pdf")
    wrong.close()

    files = []
    for path in sorted(EDGES.iterdir()):
        if path.name == "manifest.json":
            continue
        files.append({"filename": path.name, "sha256": sha256(path.read_bytes()).hexdigest()})
    _write_json(EDGES / "manifest.json", {
        "schema_version": "stage4-upload-edge-cases-v1",
        "fictional": True,
        "cases": [
            {"id": "locked", "filename": "locked-fictional.pdf", "expected_code": "locked"},
            {"id": "corrupt", "filename": "corrupt-fictional.pdf", "expected_code": "corrupt"},
            {"id": "unsupported", "filename": "unsupported-fictional.rtf", "expected_code": "unsupported_format"},
            {
                "id": "oversize",
                "generated_byte_count": 10 * 1024 * 1024 + 1,
                "expected_code": "oversize",
                "reason_not_committed": "Avoid adding a 10 MiB test blob to Git history.",
            },
            {
                "id": "wrong_person",
                "filename": "wrong-person-fictional.pdf",
                "expected_subject": "Maya - fictional demo persona",
                "subject_as_written": "Other Fictional Person",
                "expected_code": "wrong_person",
            },
        ],
        "files": files,
    })


def build_fixture_registry() -> None:
    """Pin every file exposed by the fictional demo selector to an exact digest."""

    with (BASE / "document_inventory.csv").open(encoding="utf-8", newline="") as stream:
        inventory = list(csv.DictReader(stream))
    expected_subject = "Maya - fictional demo persona"
    fixtures = []
    for item in inventory:
        path = BASE / item["watermarked_pdf"]
        fixtures.append({
            "id": item["document_id"],
            "label": f"{item['document_id']} - {item['title']}",
            "relative_path": path.relative_to(ROOT).as_posix(),
            "media_type": "application/pdf",
            "sha256": sha256(path.read_bytes()).hexdigest(),
            "expected_subject": expected_subject,
        })
    noisy_path = NOISY / "DOC-003-noisy.png"
    fixtures.append({
        "id": "DOC-003-NOISY",
        "label": "DOC-003-NOISY - controlled OCR image",
        "relative_path": noisy_path.relative_to(ROOT).as_posix(),
        "media_type": "image/png",
        "sha256": sha256(noisy_path.read_bytes()).hexdigest(),
        "expected_subject": expected_subject,
        "ocr_truth_path": (
            NOISY / "DOC-003-noisy.expected.json"
        ).relative_to(ROOT).as_posix(),
    })
    _write_json(BASE / "stage4_fixture_registry.json", {
        "schema_version": "stage4-fictional-fixture-registry-v1",
        "workspace_key": "DEMO-MAYA",
        "public_demo_upload": False,
        "fixtures": fixtures,
    })


def main() -> None:
    build_graph_truth()
    build_noisy_variant()
    build_upload_edge_cases()
    build_fixture_registry()
    print(
        "Built 8 graph truths, 1 controlled OCR variant, 5 upload edge cases, "
        "and the 9-file exact-hash demo registry."
    )


if __name__ == "__main__":
    main()
