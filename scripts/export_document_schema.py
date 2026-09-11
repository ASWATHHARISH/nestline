"""Export the Stage 4 upload, extraction, and confirmation contracts."""

from __future__ import annotations

import json
from pathlib import Path

from app.schemas.documents import (
    ConfirmationDecision,
    DocumentCandidate,
    DocumentExtractionPacket,
    DocumentReviewRequest,
    DocumentReviewResult,
    ParsedPage,
    SourceSpan,
    UploadValidationResult,
)


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "data/schemas/document.schema.json"


def build_payload() -> dict:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "source_span": SourceSpan.model_json_schema(),
        "parsed_page": ParsedPage.model_json_schema(),
        "upload_validation": UploadValidationResult.model_json_schema(),
        "candidate": DocumentCandidate.model_json_schema(),
        "extraction_packet": DocumentExtractionPacket.model_json_schema(),
        "confirmation_decision": ConfirmationDecision.model_json_schema(),
        "review_request": DocumentReviewRequest.model_json_schema(),
        "review_result": DocumentReviewResult.model_json_schema(),
    }


def main() -> int:
    TARGET.write_text(
        json.dumps(build_payload(), indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(TARGET)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
