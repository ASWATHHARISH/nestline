"""Run the frozen Stage 5 paraphrase set against the accepted hybrid gateway."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.build_stage5_paraphrase_evals import build_set
from scripts.run_stage5_retrieval_evals import FIXTURE, gateway_run, metrics


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/STAGE-5-PARAPHRASE-EVAL-RESULTS.json"


def run(*, write_report: bool = False) -> dict:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    cases = build_set()
    observations, _ = gateway_run(payload, cases)
    values = metrics(cases, observations)
    valid = all((
        values["recall_at_5"]["value"] == 1.0,
        values["citation_evidence_precision"]["value"] == 1.0,
        values["wrong_week_retrieval_count"] == 0,
        values["wrong_jurisdiction_retrieval_count"] == 0,
        values["unapproved_source_retrieval_count"] == 0,
        values["cross_workspace_leakage_count"] == 0,
        values["conflict_proposal_personalization_violations"] == 0,
        values["expected_behavior_accuracy"]["value"] == 1.0,
        values["support_state_accuracy"]["value"] == 1.0,
        values["journey_relation_accuracy"]["value"] == 1.0,
    ))
    report = {
        "schema_version": "stage5-paraphrase-report-v1",
        "valid": valid,
        "dataset_version": "stage5-paraphrases-v1",
        "frozen_before_first_run": True,
        "original_expected_truth_unchanged": True,
        "fixture_only": True,
        "paid_provider_calls": 0,
        "cases": {"passed": sum(
            observation["abstained"] == (case["expected_behavior"] != "evidence")
            and observation["abstention_reason"] == case["expected_abstention_reason"]
            and observation["support_state"] == case["expected_support_state"]
            and observation["journey_relation"] == case["expected_journey_relation"]
            for case, observation in zip(cases, observations)
        ), "total": len(cases)},
        "metrics": values,
        "observations": observations,
        "limitation": "This small controlled paraphrase set does not prove production-language retrieval quality.",
    }
    if write_report:
        REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    return report


def main() -> int:
    report = run(write_report=True)
    print(json.dumps({
        "valid": report["valid"], "cases": report["cases"], "metrics": report["metrics"],
    }, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())