"""Export strict cross-stage and provider benchmark schemas from Python source."""

from __future__ import annotations

import json
from pathlib import Path

from app.schemas.integration import CrossStageBinding, RuntimeGateInput, RuntimeGateResult
from app.schemas.provider_benchmark import ProviderBenchmarkObservation, ProviderBenchmarkReport

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data/schemas/stages5_8_integration.schema.json"
MODELS = (
    RuntimeGateInput,
    RuntimeGateResult,
    CrossStageBinding,
    ProviderBenchmarkObservation,
    ProviderBenchmarkReport,
)


def build_payload() -> dict:
    return {
        "schema_version": "5-8.1.0",
        "generated_from": [
            "app.schemas.integration",
            "app.schemas.provider_benchmark",
        ],
        "schemas": {model.__name__: model.model_json_schema() for model in MODELS},
    }


def main() -> int:
    OUTPUT.write_text(
        json.dumps(build_payload(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())