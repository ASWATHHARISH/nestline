"""Check fictional document truth/provenance without pretending to run OCR."""

from hashlib import sha256
import json
from pathlib import Path
import re


def document_integrity(data: Path, document_id: str) -> list[str]:
    if not re.fullmatch(r"DOC-00[1-8]", document_id):
        raise ValueError("unknown fictional document ID")
    base = data / "synthetic"
    expected = json.loads((base / "expected_extractions" / f"{document_id}.json").read_text(encoding="utf-8"))
    pdf = (base / "documents" / f"{document_id}.pdf").read_bytes()
    raw = (base / "documents" / f"{document_id}.txt").read_bytes()
    text = raw.decode("utf-8")
    lines = text.splitlines()
    errors = []
    if sha256(pdf).hexdigest() != expected["pdf_sha256"] or sha256(raw).hexdigest() != expected["source_text_sha256"]:
        errors.append("document bytes differ from expected provenance")
    if not expected["fictional"] or "FICTIONAL DEMO DATA" not in text or not pdf.startswith(b"%PDF"):
        errors.append("fictional document marker missing")
    if expected["document_id"] != document_id or expected["workspace_id"] != "DEMO-MAYA":
        errors.append("wrong document/workspace identity")
    for fact in expected["facts"]:
        number = fact["source_line"]
        if not 1 <= number <= len(lines) or lines[number-1] != fact["source_text"]:
            errors.append("fact source line differs")
        if fact["status"] != "proposed" or fact["page"] != 1:
            errors.append("extraction must remain a proposed page-one fact")
        if fact["value"] in {"not supplied", "not recorded"} and fact["extraction_disposition"] != "abstain":
            errors.append("missing information must require abstention")
        if not fact["coordinates"] or any(not (0 <= x0 < x1 <= 595.3 and 0 <= y0 < y1 <= 841.9)
                                           for x0, y0, x1, y1 in fact["coordinates"]):
            errors.append("fact coordinates are outside the one-page fixture")
    return errors
