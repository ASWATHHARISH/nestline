"""Parse one registered public source and produce a reviewable dry-run/staging record."""

import argparse
from datetime import date
import json
import os
from pathlib import Path

from app.schemas.ingestion import IngestionRun, Stage1ReviewLedger
from app.services.embeddings import OpenAICompatibleEmbeddingProvider
from app.services.foundation import read_catalogues
from app.services.ingestion_store import (latest_staging_run, write_source_artifact,
                                          write_staging_run)
from app.services.public_ingestion import admission_for, run_ingestion
from app.services.public_parsers import TesseractCliOcrProvider
from app.services.source_capture import MAX_SOURCE_BYTES, fetch_registered_source
from scripts.validate_content import load_bundle

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-id", required=True)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--input", type=Path, help="previously captured local HTML/PDF")
    inputs.add_argument("--fetch", action="store_true", help="fetch the exact registered HTTPS URL")
    parser.add_argument("--retrieved-at", type=date.fromisoformat, required=True,
                        help="explicit YYYY-MM-DD for reproducible source metadata")
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today(),
                        help="date used for currency/review gates; defaults to today")
    parser.add_argument("--previous-run", type=Path)
    parser.add_argument("--review-decisions", type=Path,
                        help="schema-valid Stage 1 role-decision ledger")
    parser.add_argument("--commit-staging", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--embedding-provider")
    parser.add_argument("--embedding-url")
    parser.add_argument("--embedding-model")
    parser.add_argument("--embedding-api-key-env", default="NESTLINE_EMBEDDING_API_KEY")
    parser.add_argument("--tesseract-path",
                        help="explicit local Tesseract executable for scanned PDF pages")
    args = parser.parse_args(argv)

    bundle = load_bundle(ROOT / "data")
    source = next((item for item in bundle.sources if item.source_id == args.source_id), None)
    if source is None:
        parser.error("source ID is not registered")
    admission = admission_for(source, args.as_of)
    # A rejected source is never fetched or read. The placeholder only makes the
    # rejected audit run deterministic and is never stored as an artifact.
    try:
        if admission.decision == "rejected":
            raw = b"SOURCE_REJECTED_BEFORE_CAPTURE"
        elif args.fetch:
            raw = fetch_registered_source(source)
        else:
            if args.input.stat().st_size > MAX_SOURCE_BYTES:
                raise ValueError("local source exceeds the ingestion size limit")
            raw = args.input.read_bytes()
            if not raw:
                raise ValueError("local source is empty")
    except Exception as exc:
        print(json.dumps({"source_id": args.source_id, "outcome": "capture_failed",
                          "error": type(exc).__name__,
                          "message": "The registered source could not be captured; no artifact was stored."},
                         indent=2))
        return 1
    previous = (IngestionRun.model_validate_json(args.previous_run.read_text(encoding="utf-8"))
                if args.previous_run else latest_staging_run(
                    ROOT / "data/ingestion/staging", args.source_id))
    provider_values = [args.embedding_provider, args.embedding_url, args.embedding_model]
    provider = None
    if any(provider_values):
        if not all(provider_values):
            parser.error("embedding provider, URL and model must be supplied together")
        key = os.environ.get(args.embedding_api_key_env, "")
        if not key:
            parser.error(f"embedding API key is missing from {args.embedding_api_key_env}")
        provider = OpenAICompatibleEmbeddingProvider(name=args.embedding_provider, base_url=args.embedding_url,
                                                     api_key=key, model=args.embedding_model)
    ocr_provider = (TesseractCliOcrProvider(args.tesseract_path)
                    if args.tesseract_path else None)
    review_decisions = []
    if args.review_decisions:
        ledger = Stage1ReviewLedger.model_validate_json(
            args.review_decisions.read_text(encoding="utf-8"))
        review_decisions = [decision for decision in ledger.decisions
                            if decision.source_id == args.source_id]
    run = run_ingestion(bundle, args.source_id, raw, retrieved_at=args.retrieved_at,
                        dry_run=not args.commit_staging, previous=previous,
                        embedding_provider=provider, catalogue_items=read_catalogues(ROOT / "data"),
                        review_decisions=review_decisions,
                        ocr_provider=ocr_provider, as_of=args.as_of)
    if args.commit_staging:
        path, write_state = write_staging_run(run, ROOT / "data/ingestion/staging")
        artifact_path = None
        artifact_state = "not_stored"
        if run.admission.fixed_quote_only:
            artifact_state = "fixed_quote_snapshot_only"
        elif run.outcome != "rejected":
            artifact_path, artifact_state = write_source_artifact(
                run, raw, ROOT / "data/ingestion/artifacts")
    else:
        path, write_state = None, "dry_run_no_write"
        artifact_path, artifact_state = None, "dry_run_no_write"
    rendered = json.dumps(run.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({"run_id": run.run_id, "logical_version_id": run.logical_version_id,
                      "source_id": args.source_id, "outcome": run.outcome,
                      "blocks": run.parsed_block_count, "candidates": len(run.candidates),
                      "governed_blocks": len(run.governed_blocks),
                      "review_tasks": len(run.review_tasks), "embeddings": len(run.embeddings),
                      "issues": len(run.issues), "write_state": write_state,
                      "staging_path": str(path.relative_to(ROOT)) if path else None,
                      "artifact_state": artifact_state,
                      "artifact_path": str(artifact_path.relative_to(ROOT)) if artifact_path else None},
                     indent=2))
    return 1 if run.outcome == "rejected" else 0


if __name__ == "__main__":
    raise SystemExit(main())
