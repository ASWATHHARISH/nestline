"""Validate authored records, or require actual published representative coverage."""

import argparse
import csv
import json
from pathlib import Path

from pydantic import ValidationError

from app.schemas.content import ContentBundle
from app.services.content_validation import validate_bundle

REPRESENTATIVE = {"PC00", "P01", "P09", "P10", "P24", "P36", "PP01", "PP06", "PP12"}
ROOT = Path(__file__).resolve().parents[1]


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_bundle(data: Path) -> ContentBundle:
    with (data / "guidelines/source_registry.csv").open(encoding="utf-8", newline="") as stream:
        sources = list(csv.DictReader(stream))
    structured = {"jurisdiction", "topics", "allowed_use", "review"}
    optional = {"publication_date", "last_checked_at", "content_checksum", "supersedes_source_id"}
    for source in sources:
        for key in structured:
            source[key] = json.loads(source[key])
        for key in optional:
            source[key] = source[key] or None
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
    args = parser.parse_args(argv)
    try:
        bundle = load_bundle(args.data_dir)
        report = validate_bundle(bundle)
        # Coverage is a checked-in audit view, never an independent source of truth.
        with (args.data_dir / "weekly/coverage_matrix.csv").open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        actual = {p.profile_id: (p.status, p.content_priority) for p in bundle.profiles}
        declared = {r["profile_id"]: (r["status"], r["content_priority"]) for r in rows}
        if actual != declared or len(rows) != len(actual):
            report.errors.append("coverage matrix differs from weekly manifest")
        if args.require_release:
            published = {p.profile_id for p in bundle.profiles if p.status == "published"}
            for missing in sorted(REPRESENTATIVE - published):
                report.errors.append(f"release requires reviewed, published profile: {missing}")
        print(json.dumps({"valid": report.valid, "mode": "release" if args.require_release else "authoring",
                          "profiles": len(bundle.profiles), "published_profiles": report.published_profiles,
                          "sources": len(bundle.sources), "errors": report.errors}, indent=2))
        return 0 if report.valid else 1
    except (OSError, ValueError, KeyError, TypeError, ValidationError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
