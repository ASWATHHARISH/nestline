"""Export the versioned Stage 6 Safety Gate JSON Schema bundle."""

from __future__ import annotations

import json
from pathlib import Path

from app.schemas.safety import (
    FixedSafetyMessage,
    SafetyClarificationState,
    SafetyGateInput,
    SafetyGateResult,
    SafetyGenerationGuardResult,
    SafetyRuleMatch,
    SafetyTrace,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data/schemas/safety.schema.json"


def build_payload() -> dict:
    models = {
        "safety_gate_input": SafetyGateInput,
        "safety_rule_match": SafetyRuleMatch,
        "clarification_state": SafetyClarificationState,
        "fixed_safety_message": FixedSafetyMessage,
        "safety_trace": SafetyTrace,
        "safety_gate_result": SafetyGateResult,
        "generation_guard_result": SafetyGenerationGuardResult,
    }
    return {
        "stage": 6,
        "schema_version": "6.0.0",
        "schemas": {name: model.model_json_schema() for name, model in models.items()},
    }


def main() -> int:
    OUTPUT.write_text(
        json.dumps(build_payload(), indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
