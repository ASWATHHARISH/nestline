"""Publish reviewed committed ingestion runs as one immutable local corpus version."""

import argparse
import json
from pathlib import Path

from app.schemas.ingestion import IngestionRun
from app.services.ingestion_store import publish_corpus

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-version", required=True)
    parser.add_argument("runs", nargs="+", type=Path)
    args = parser.parse_args(argv)
    runs = [IngestionRun.model_validate_json(path.read_text(encoding="utf-8")) for path in args.runs]
    manifest = publish_corpus(runs, ROOT / "data/ingestion/corpora", args.corpus_version,
                              governance_data=ROOT / "data")
    print(json.dumps(manifest.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    main()
