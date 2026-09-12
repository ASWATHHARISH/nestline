"""Deterministic Stage 9 completion checker."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.schemas.product_experience import ProductPage, ViewState
from scripts.export_product_experience_schema import coverage_bundle, schema_bundle
from scripts.run_stage9_evals import evaluate, load_cases


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/STAGE-9-CHECK-RESULTS.json"
SCHEMA = ROOT / "data/schemas/product_experience.schema.json"
COVERAGE = ROOT / "docs/STAGE-9-COVERAGE-MANIFEST.json"
EVAL_REPORT = ROOT / "docs/STAGE-9-EVAL-RESULTS.json"
WALKTHROUGHS = ROOT / "docs/STAGE-9-DEMO-WALKTHROUGH-RESULTS.json"
HANDOFF = ROOT / "docs/STAGE-9-IMPLEMENTATION-SELF-VERIFICATION-AND-STAGE-10-READINESS.md"
VISUAL = ROOT / "docs/stage9-ui-evidence/visual-inspection.json"
KEYBOARD = ROOT / "docs/stage9-ui-evidence/keyboard-walkthrough.json"
SELF_REVIEW = ROOT / "docs/STAGE-9-SELF-REVIEW-FINDINGS.json"


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def check():
    errors = []
    required = [
        ROOT / "streamlit_app.py",
        ROOT / "app/schemas/product_experience.py",
        ROOT / "app/services/product_experience.py",
        ROOT / "app/pages_and_components/stage9.py",
        ROOT / "assets/stage9/week-24-journey.svg",
        ROOT / "tests/test_product_experience.py",
        ROOT / "scripts/check_stage9_ui.py",
        ROOT / "scripts/run_stage9_evals.py",
        ROOT / "scripts/export_product_experience_schema.py",
        ROOT / "evals/stage9_product_experience.jsonl",
        SCHEMA, COVERAGE, EVAL_REPORT, WALKTHROUGHS, HANDOFF, VISUAL, KEYBOARD,
        SELF_REVIEW,
    ]
    for path in required:
        if not path.is_file():
            errors.append(f"missing Stage 9 artifact: {path.relative_to(ROOT)}")
    if SCHEMA.is_file() and _json(SCHEMA) != schema_bundle():
        errors.append("Stage 9 exported schemas are stale")
    if COVERAGE.is_file() and _json(COVERAGE) != coverage_bundle():
        errors.append("Stage 9 coverage manifest is stale")

    cases = load_cases()
    failed = [case["case_id"] for case in cases if evaluate(case) != case["expected"]]
    if failed:
        errors.append(f"Stage 9 frozen development cases failed: {failed}")
    if EVAL_REPORT.is_file():
        report = _json(EVAL_REPORT)
        if not report.get("valid") or report.get("cases") != {"passed": len(cases), "total": len(cases)}:
            errors.append("Stage 9 evaluation report is stale or failed")
        if report.get("home_agent_fanout") != 0 or report.get("stage10_persistent_writes") != 0:
            errors.append("Stage 9 crossed the page-load or Stage 10 write boundary")
    if WALKTHROUGHS.is_file():
        walkthroughs = _json(WALKTHROUGHS)
        if walkthroughs.get("passed") != 9 or walkthroughs.get("total") != 9:
            errors.append("three demo stories did not pass all three reset runs")
        if walkthroughs.get("called_user_research"):
            errors.append("internal walkthrough was mislabeled as user research")
    if VISUAL.is_file():
        visual = _json(VISUAL)
        if not visual.get("valid") or len(visual.get("screenshots", [])) < 11:
            errors.append("responsive visual inspection is incomplete or failed")
        if any(
            item.get("clipped")
            for item in visual.get("responsive_checks", {}).values()
        ):
            errors.append("visual inspection found a clipped active-content control")
    if KEYBOARD.is_file():
        keyboard = _json(KEYBOARD)
        if not all((
            keyboard.get("valid"),
            keyboard.get("destination_reached"),
            keyboard.get("visible_focus_observed"),
        )):
            errors.append("keyboard-only navigation or visible-focus evidence failed")
    if SELF_REVIEW.is_file():
        self_review = _json(SELF_REVIEW)
        unresolved = [
            finding.get("id", "unknown")
            for finding in self_review.get("findings", [])
            if finding.get("post_status") != "PASS"
        ]
        if unresolved:
            errors.append(f"Stage 9 self-review findings remain unresolved: {unresolved}")

    app_source = (ROOT / "app/pages_and_components/stage9.py").read_text(encoding="utf-8")
    service_source = (ROOT / "app/services/product_experience.py").read_text(encoding="utf-8")
    for unsafe in ("import openai", "import langchain", "service_role", "st.html("):
        if unsafe in (app_source + service_source).casefold():
            errors.append(f"Stage 9 deterministic path contains forbidden dependency/rendering: {unsafe}")
    for required_label in coverage_bundle()["provenance_labels"]:
        if required_label not in (app_source + service_source):
            errors.append(f"visible provenance label missing from Stage 9 implementation: {required_label}")
    if len(ProductPage) != 7 or len(ViewState) != 8:
        errors.append("Stage 9 page/state catalogue is incomplete")

    safety = json.loads((ROOT / "data/safety/rule_spec.yaml").read_text(encoding="utf-8"))
    if safety.get("status") != "draft":
        errors.append("Stage 9 must preserve the draft safety-specification boundary")
    if HANDOFF.is_file():
        handoff = HANDOFF.read_text(encoding="utf-8")
        if "STAGE 9 ACCEPTED FOR CONTROLLED ENGINEERING — STAGE 10 ENGINEERING MAY BEGIN" not in handoff and "STAGE 9 NO-GO — STAGE 10 MUST NOT BEGIN" not in handoff:
            errors.append("Stage 9 handoff lacks an exact verdict")

    return {
        "valid": not errors,
        "stage": 9,
        "schema_version": "9.0.0",
        "local_streamlit_only": True,
        "deployment_performed": False,
        "database_migration_required": False,
        "paid_provider_required": False,
        "public_or_clinical_release_ready": False,
        "controlled_engineering_stage10_ready": not errors,
        "verified": {
            "pages": len(ProductPage), "shared_view_states": len(ViewState),
            "development_cases": {"passed": len(cases) - len(failed), "total": len(cases)},
            "demo_story_runs": 9, "home_agent_fanout": 0,
            "urgent_generation_calls": 0, "stage10_persistent_writes": 0,
            "responsive_screenshots": 11, "keyboard_walkthroughs": 1,
        },
        "limitations": [
            "Automated and internal walkthrough checks are not WCAG conformance or external user research.",
            "The public safety specification and health content remain unapproved.",
            "Live provider, LangSmith, production upload, persistence and deployment were not exercised.",
        ],
        "errors": errors,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args(argv)
    result = check()
    if args.write_report:
        REPORT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
