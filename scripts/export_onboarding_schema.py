"""Export Stage 3 onboarding contracts for UI and API integrations."""

from __future__ import annotations

import json
from pathlib import Path

from app.schemas.onboarding import (
    DatingConflict,
    JOURNEY_TIMING_ADAPTER,
    JourneyResolution,
    OnboardingCommitResult,
    OnboardingDetails,
    OnboardingDraft,
    PreparedSymptom,
)


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "data/schemas/onboarding.schema.json"


def build_payload() -> dict:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "journey_timing_input": JOURNEY_TIMING_ADAPTER.json_schema(),
        "journey_resolution": JourneyResolution.model_json_schema(),
        "dating_conflict": DatingConflict.model_json_schema(),
        "onboarding_details": OnboardingDetails.model_json_schema(),
        "prepared_symptom": PreparedSymptom.model_json_schema(),
        "onboarding_draft": OnboardingDraft.model_json_schema(),
        "onboarding_commit_result": OnboardingCommitResult.model_json_schema(),
    }


def main() -> int:
    TARGET.write_text(
        json.dumps(build_payload(), indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(TARGET)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())