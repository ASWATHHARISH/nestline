"""Export Stage 1 record schemas for editor and storage integration."""

import json
from pathlib import Path

from app.schemas.ingestion import (CorpusManifest, EvidenceCandidate, EvidenceReviewDecision,
                                   EvidenceReviewTask, IngestionRun, ParsedBlock, Stage1Audit,
                                   Stage1ReviewLedger)

ROOT = Path(__file__).resolve().parents[1]


def main():
    target = ROOT / "data/schemas/ingestion.schema.json"
    payload = {"$schema": "https://json-schema.org/draft/2020-12/schema",
               "records": {"parsed_block": ParsedBlock.model_json_schema(),
                           "evidence_candidate": EvidenceCandidate.model_json_schema(),
                           "evidence_review_decision": EvidenceReviewDecision.model_json_schema(),
                           "evidence_review_task": EvidenceReviewTask.model_json_schema(),
                           "stage1_review_ledger": Stage1ReviewLedger.model_json_schema(),
                           "ingestion_run": IngestionRun.model_json_schema(),
                           "corpus_manifest": CorpusManifest.model_json_schema(),
                           "stage1_audit": Stage1Audit.model_json_schema()}}
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(target)


if __name__ == "__main__":
    main()
