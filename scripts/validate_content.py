"""Validate authored records, or require actual published representative coverage."""

import argparse
import csv
import json
from datetime import date
from pathlib import Path

from app.schemas.content import ContentBundle
from app.services.content_validation import review_readiness_errors, validate_bundle
from app.services.foundation import release_errors, validate_foundation
from app.services.source_snapshots import validate_snapshots

ROOT = Path(__file__).resolve().parents[1]


def read_jsonl(path: Path) -> list[dict]:
    """Show the filename and line so an author can fix a malformed record."""
    records = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                records.append(json.loads(line))
            except ValueError as exc:
                raise ValueError(f"{path.name}:{number}: {exc}") from exc
    return records


def load_bundle(data: Path) -> ContentBundle:
    with (data / "guidelines/source_registry.csv").open(encoding="utf-8", newline="") as stream:
        sources = list(csv.DictReader(stream))
    structured = {"jurisdiction", "topics", "allowed_use", "review", "journey_stages", "selected_sections"}
    optional = {"publication_date", "last_checked_at", "content_checksum", "supersedes_source_id",
                "retrieved_at", "publisher_updated_at", "next_review_at"}
    for source in sources:
        for key in structured:
            if key in source:
                source[key] = json.loads(source[key])
        for key in optional:
            if key in source:
                source[key] = source[key] or None
        if "max_quote_sections" in source:
            source["max_quote_sections"] = int(source["max_quote_sections"]) if source["max_quote_sections"] else None
    payload = dict(sources=sources,
                   evidence=read_jsonl(data / "guidelines/section_manifest.jsonl"),
                   fragments=read_jsonl(data / "guidelines/guidance_fragments.jsonl"),
                   profiles=read_jsonl(data / "weekly/weekly_content_manifest.jsonl"))
    return ContentBundle.model_validate_json(json.dumps(payload))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--require-release", action="store_true",
                        help="fail unless all canonical representative profiles are published")
    parser.add_argument("--require-review-ready", action="store_true",
                        help="require representative cards and explicit empty-slot decisions; does not approve them")
    args = parser.parse_args(argv)
    try:
        bundle = load_bundle(args.data_dir)
        report = validate_bundle(bundle)
        report.errors.extend(validate_snapshots(bundle, args.data_dir))
        # Coverage is a checked-in audit view, never an independent source of truth.
        with (args.data_dir / "weekly/coverage_matrix.csv").open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        actual = {p.profile_id: (p.status, p.content_priority) for p in bundle.profiles}
        declared = {r["profile_id"]: (r["status"], r["content_priority"]) for r in rows}
        if actual != declared or len(rows) != len(actual):
            report.errors.append("coverage matrix differs from weekly manifest")
        if args.require_release or args.require_review_ready:
            report.errors.extend(review_readiness_errors(bundle))
            report.errors.extend(validate_foundation(bundle, args.data_dir))
        if args.require_release:
            report.errors.extend(release_errors(bundle, args.data_dir, date.today()))
        mode = "release" if args.require_release else "review_ready" if args.require_review_ready else "authoring"
        print(json.dumps({"valid": report.valid, "mode": mode,
                          "profiles": len(bundle.profiles), "published_profiles": report.published_profiles,
                          "sources": len(bundle.sources), "evidence_spans": len(bundle.evidence),
                          "fragments": len(bundle.fragments), "errors": report.errors}, indent=2))
        return 0 if report.valid else 1
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
