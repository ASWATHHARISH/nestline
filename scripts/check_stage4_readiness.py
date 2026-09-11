"""Verify that the Stage 4 fictional-document foundation is complete and honest.

This check deliberately separates readiness to begin controlled Stage 4 work from
readiness to accept live medical documents. The latter remains blocked by human
review and an upload-scanning policy decision.
"""

from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/synthetic"
INVENTORY = BASE / "document_inventory.csv"
EXPECTED_IDS = {f"DOC-{number:03d}" for number in range(1, 9)}
REPORT = ROOT / "docs/STAGE-4-READINESS-CHECK-RESULTS.json"


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _relative_file(value: str) -> Path:
    candidate = (BASE / value).resolve()
    if BASE.resolve() not in candidate.parents:
        raise ValueError(f"inventory path leaves the synthetic fixture folder: {value}")
    return candidate


def run() -> dict:
    errors: list[str] = []
    verified_facts = 0
    verified_abstentions = 0
    verified_injection_cases = 0
    rows: list[dict[str, str]] = []

    if not INVENTORY.exists():
        errors.append("document inventory is missing")
    else:
        with INVENTORY.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))

    ids = {row.get("document_id", "") for row in rows}
    if ids != EXPECTED_IDS or len(rows) != len(EXPECTED_IDS):
        errors.append("inventory must contain exactly DOC-001 through DOC-008 once each")

    for row in rows:
        document_id = row.get("document_id", "")
        if row.get("status") != "generated_fictional":
            errors.append(f"{document_id}: fixture status is not generated_fictional")
        try:
            text_path = _relative_file(row["source_text"])
            pdf_path = _relative_file(row["watermarked_pdf"])
            truth_path = _relative_file(row["expected_extraction_json"])
        except (KeyError, ValueError) as exc:
            errors.append(f"{document_id}: {exc}")
            continue

        for label, path in (("text", text_path), ("PDF", pdf_path), ("truth", truth_path)):
            if not path.is_file():
                errors.append(f"{document_id}: {label} artifact is missing")
        if not all(path.is_file() for path in (text_path, pdf_path, truth_path)):
            continue

        text = text_path.read_text(encoding="utf-8")
        if "FICTIONAL DEMO DATA - NOT A REAL MEDICAL RECORD" not in text:
            errors.append(f"{document_id}: editable text lacks the fictional-data watermark")

        try:
            with fitz.open(pdf_path) as document:
                pdf_text = "\n".join(page.get_text() for page in document)
                page_count = document.page_count
        except Exception as exc:  # pragma: no cover - result is reported to the caller
            errors.append(f"{document_id}: PDF cannot be opened: {exc}")
            continue
        if page_count != 1:
            errors.append(f"{document_id}: canonical PDF must have one page")
        if "FICTIONAL DEMO DATA" not in pdf_text or "NOT A REAL MEDICAL RECORD" not in pdf_text:
            errors.append(f"{document_id}: PDF lacks the fictional-data watermark")

        try:
            truth = json.loads(truth_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            errors.append(f"{document_id}: extraction truth is invalid JSON: {exc}")
            continue

        if truth.get("document_id") != document_id or truth.get("fictional") is not True:
            errors.append(f"{document_id}: extraction truth identity or fictional flag is wrong")
        if truth.get("pdf_sha256") != _digest(pdf_path):
            errors.append(f"{document_id}: PDF checksum does not match extraction truth")
        if truth.get("source_text_sha256") != _digest(text_path):
            errors.append(f"{document_id}: text checksum does not match extraction truth")
        if truth.get("date_semantics") != "fixed fixture clock; never substitute today's date":
            errors.append(f"{document_id}: fixture date semantics are missing")

        try:
            inventory_graph = json.loads(row["expected_graph_changes"])
        except (KeyError, json.JSONDecodeError):
            inventory_graph = None
        if (
            not isinstance(inventory_graph, list)
            or inventory_graph != truth.get("expected_graph_changes")
            or inventory_graph != truth.get("expected_behaviors")
        ):
            errors.append(f"{document_id}: expected behavior/graph labels are inconsistent")

        facts = truth.get("facts")
        if not isinstance(facts, list) or not facts:
            errors.append(f"{document_id}: extraction truth has no fact candidates")
            continue
        for index, fact in enumerate(facts, start=1):
            required = {
                "field", "value", "source_text", "page", "source_line",
                "coordinates", "coordinate_system", "status",
                "extraction_disposition",
            }
            missing = required - set(fact) if isinstance(fact, dict) else required
            if missing:
                errors.append(f"{document_id}: fact {index} lacks {sorted(missing)}")
                continue
            if fact["status"] != "proposed":
                errors.append(f"{document_id}: fact {index} is active before confirmation")
            if fact["page"] != 1 or not fact["coordinates"]:
                errors.append(f"{document_id}: fact {index} lacks page/span provenance")
            if fact["source_text"] not in text:
                errors.append(f"{document_id}: fact {index} source text is not in the editable fixture")
            missing_value = str(fact["value"]).casefold() in {"not supplied", "not recorded"}
            if missing_value and fact["extraction_disposition"] != "abstain":
                errors.append(f"{document_id}: missing fact {index} does not abstain")
            verified_facts += 1
            verified_abstentions += int(missing_value)

        attacks = truth.get("untrusted_instruction_text")
        if not isinstance(attacks, list):
            errors.append(f"{document_id}: untrusted instruction list is missing")
        else:
            for attack in attacks:
                if attack not in text:
                    errors.append(f"{document_id}: declared injected text is absent from the source")
                verified_injection_cases += 1

    doc6_path = BASE / "expected_extractions/DOC-006.json"
    if doc6_path.exists():
        doc6 = json.loads(doc6_path.read_text(encoding="utf-8"))
        conflict_values = {
            fact.get("value") for fact in doc6.get("facts", [])
            if fact.get("field") == "conflicts_with"
        }
        if conflict_values != {"DOC-005"} or not doc6.get("untrusted_instruction_text"):
            errors.append("DOC-006 must preserve both the DOC-005 conflict and injected instruction")

    doc8_path = BASE / "expected_extractions/DOC-008.json"
    if doc8_path.exists():
        doc8 = json.loads(doc8_path.read_text(encoding="utf-8"))
        dispositions = {
            fact.get("field"): fact.get("extraction_disposition")
            for fact in doc8.get("facts", [])
        }
        if dispositions.get("delivery_type") != "abstain" or dispositions.get("feeding_method") != "abstain":
            errors.append("DOC-008 must abstain on missing delivery type and feeding method")

    noisy_variants = list((BASE / "noisy_variants").glob("**/*")) if (BASE / "noisy_variants").exists() else []
    typed_graph_truth = list((BASE / "expected_graph_changes").glob("*.json")) if (BASE / "expected_graph_changes").exists() else []
    upload_edge_cases = list((BASE / "upload_edge_cases").glob("**/*")) if (BASE / "upload_edge_cases").exists() else []

    fixture_additions = [
        {
            "item": "one controlled noisy/OCR variant with expected extraction truth",
            "present": bool([path for path in noisy_variants if path.is_file()]),
        },
        {
            "item": "typed node/edge graph-change truth derived from confirmed state transitions",
            "present": len([path for path in typed_graph_truth if path.is_file()]) == 8,
        },
        {
            "item": "locked, corrupt, unsupported, oversize and wrong-person upload fixtures",
            "present": bool([path for path in upload_edge_cases if path.is_file()]),
        },
    ]
    result = {
        "valid": not errors,
        "ready_to_start_stage4": not errors,
        "ready_for_live_or_public_upload": False,
        "verified": {
            "inventory_documents": len(rows),
            "editable_text_documents": sum((BASE / f"documents/{item}.txt").is_file() for item in EXPECTED_IDS),
            "watermarked_pdfs": sum((BASE / f"documents/{item}.pdf").is_file() for item in EXPECTED_IDS),
            "extraction_truth_files": sum((BASE / f"expected_extractions/{item}.json").is_file() for item in EXPECTED_IDS),
            "fact_candidates_with_provenance": verified_facts,
            "explicit_abstentions": verified_abstentions,
            "prompt_injection_cases": verified_injection_cases,
        },
        "stage4_fixture_additions": fixture_additions,
        "stage4_build_items_remaining": [
            item["item"] for item in fixture_additions if not item["present"]
        ],
        "parked_release_gates": [
            {
                "owner": "product/security/platform decision",
                "gate": "choose and document upload malware-scanning policy before broader deployment",
            },
            {
                "owner": "qualified clinical and India-localisation reviewers",
                "gate": "finish required content and safety reviews before live health guidance",
            },
            {
                "owner": "product reviewer",
                "gate": "complete final rendered UI acceptance before public release",
            },
        ],
        "errors": errors,
    }
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args(argv)
    result = run()
    if args.write_report:
        REPORT.write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n"
        )
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())