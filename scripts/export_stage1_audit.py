"""Create the tracked, text-free Stage 1 audit from exact-source ingestion runs."""

import argparse
import json
from pathlib import Path

from app.schemas.ingestion import IngestionRun
from app.services.ingestion_audit import build_stage1_audit
from scripts.validate_content import load_bundle

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-directory", required=True, type=Path)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "data/ingestion/audit/stage1-source-audit.json")
    args = parser.parse_args(argv)
    paths = sorted(args.run_directory.glob("stage1-*.json"))
    if not paths:
        parser.error("run directory contains no stage1-*.json files")
    runs = [IngestionRun.model_validate_json(path.read_text(encoding="utf-8")) for path in paths]
    audit = build_stage1_audit(runs, load_bundle(ROOT / "data"), ROOT / "data")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(audit.model_dump(mode="json"), indent=2) + "\n",
                           encoding="utf-8", newline="\n")
    print(json.dumps({"output": str(args.output), "sources": len(audit.sources),
                      "candidates": sum(len(source.candidate_ids) for source in audit.sources)},
                     indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
