"""Run the frozen, visible Stage 9 development evaluations."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from statistics import mean
from time import perf_counter

from app.schemas.product_experience import ProductMode, ViewState
from app.services.product_experience import (
    authentic_failed_trace, demo_documents, demo_story_results, demo_weekly_home,
    load_evaluator_metrics, personal_empty_home, reset_demo_state_keys,
    run_compass, simulated_review,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "evals/stage9_product_experience.jsonl"
REPORT = ROOT / "docs/STAGE-9-EVAL-RESULTS.json"
WALKTHROUGHS = ROOT / "docs/STAGE-9-DEMO-WALKTHROUGH-RESULTS.json"


def load_cases():
    return [json.loads(line) for line in MANIFEST.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def evaluate(case):
    kind, variant = case["kind"], case.get("variant")
    if kind == "home":
        home = demo_weekly_home(approximate=variant == "approximate")
        if variant == "exact": return home.state.value
        if variant == "approximate": return "range" if not home.journey.exact else "exact"
        if variant == "fanout": return str(home.agent_fanout_count)
        if variant == "unreleased_profile": return "blocked" if "No public weekly-development profile" in home.hero_body else "claimed"
    if kind == "mode":
        if variant == "personal": return personal_empty_home().state.value
        if variant == "demo": return "fictional" if demo_weekly_home().fictional else "unlabeled"
        if variant == "reset":
            state = {"stage9_demo_x": 1, "auth_session": "keep", "workspace_id": "keep"}
            reset_demo_state_keys(state)
            return "isolated" if state == {"auth_session": "keep", "workspace_id": "keep"} else "leaked"
    if kind == "chat":
        return run_compass(case["query"], horizon=case["horizon"]).display.route
    if kind == "document":
        return "present" if variant in {item.status for item in demo_documents()} else "missing"
    if kind == "review":
        view = simulated_review(variant)
        return "simulated" if view.label == "Simulated review" and not view.persistence_available else "misleading"
    if kind == "evaluator":
        if variant == "generated": return str(len(load_evaluator_metrics()))
        if variant == "failed_trace":
            first = authentic_failed_trace()["first_pass"]
            return f"{first['passed']}/{first['total']}"
    if kind == "contract":
        if variant == "view_states": return str(len(ViewState))
        if variant == "writes":
            executions = [
                run_compass("Show meal options"),
                run_compass("Show my weekly plan", horizon="week"),
            ]
            writes = sum(item.stage7.trace.direct_write_count for item in executions)
            writes += sum(int(item.stage8.persistent_write_performed) for item in executions if item.stage8)
            return str(writes)
    raise ValueError(f"unknown case {case['case_id']}")


def main() -> int:
    cases = load_cases()
    results, latencies = [], []
    for case in cases:
        started = perf_counter()
        observed = evaluate(case)
        latency = (perf_counter() - started) * 1000
        latencies.append(latency)
        results.append({
            "case_id": case["case_id"], "domain": case["domain"],
            "critical": case["critical"], "expected": case["expected"],
            "observed": observed, "passed": observed == case["expected"],
            "latency_ms": round(latency, 4),
        })
    passed = sum(item["passed"] for item in results)
    critical = [item for item in results if item["critical"]]
    by_domain = {}
    for domain in sorted({item["domain"] for item in results}):
        subset = [item for item in results if item["domain"] == domain]
        by_domain[domain] = {"passed": sum(item["passed"] for item in subset), "total": len(subset)}

    story_results = demo_story_results()
    WALKTHROUGHS.write_text(json.dumps({
        "schema_version": "9.0.0", "fictional": True, "reset_before_each_run": True,
        "runs": story_results,
        "passed": sum(item["passed"] for item in story_results),
        "total": len(story_results),
        "stage10_boundary": "durable save/review submission unavailable in every run",
        "called_user_research": False,
    }, indent=2) + "\n", encoding="utf-8")

    report = {
        "valid": passed == len(results) and all(item["passed"] for item in story_results),
        "stage": 9, "schema_version": "9.0.0",
        "dataset": "visible deterministic Stage 9 development set; sealed final holdout not accessed",
        "fixture_only": True, "clinical_validation": False, "user_research": False,
        "cases": {"passed": passed, "total": len(results)},
        "critical_cases": {"passed": sum(item["passed"] for item in critical), "total": len(critical)},
        "by_domain": by_domain,
        "demo_stories": {"passed": sum(item["passed"] for item in story_results), "total": len(story_results)},
        "urgent_zero_generation": {
            "passed": sum(item["story"] != "urgent-bypass" or item["ordinary_generation_calls"] == 0 for item in story_results),
            "total": len(story_results),
        },
        "home_agent_fanout": 0,
        "stage10_persistent_writes": 0,
        "provider_live_runs": 0,
        "latency_ms": {"samples": len(latencies), "mean": round(mean(latencies), 4), "maximum": round(max(latencies), 4)},
        "case_results": results,
        "failures": [item for item in results if not item["passed"]],
        "limitations": [
            "Component checks and internal walkthroughs are not external usability research.",
            "Fixture-only Stage 7/8 output does not establish production retrieval or clinical quality.",
            "Automated structure checks do not prove WCAG conformance.",
            "Stage 10 durable plan/fact/review writes and deployment remain unavailable.",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "valid": report["valid"], "cases": report["cases"],
        "critical_cases": report["critical_cases"], "demo_stories": report["demo_stories"],
        "report": str(REPORT.relative_to(ROOT)),
    }, sort_keys=True))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
