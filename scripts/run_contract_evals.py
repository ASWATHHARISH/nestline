"""Run frozen visible software cases. No language model, OCR or clinical eval."""

import argparse
from hashlib import sha256
import json
from pathlib import Path

from app.schemas.foundation import SafetySpec
from app.services.content_selection import condition_state, postpartum_day_context, pregnancy_month_scope
from app.services.fixture_integrity import document_integrity
from app.services.foundation import read_catalogues
from app.services.safety_contract import evaluate_safety_contract

ROOT = Path(__file__).resolve().parents[1]


def run_case(case, data, spec, items):
    inputs, expected = case["inputs"], case["outputs"]
    kind = case["kind"]
    if kind == "safety":
        result = evaluate_safety_contract(spec, inputs["message"])
        rule = expected["required_rule"]
        return (result["route"] == expected["route"] and result["generation_allowed"] == expected["generation_allowed"]
                and (rule is None or rule in result["rule_ids"])), result
    if kind == "conditions":
        result = {"state": condition_state(inputs["required"], inputs["excluded"], set(inputs["present"]), set(inputs["absent"]))[0]}
    elif kind == "day":
        result = postpartum_day_context(inputs["day"])
    elif kind == "month":
        scope = pregnancy_month_scope(inputs["month"])
        result = dict(start=scope.start, end=scope.end)
    elif kind == "food":
        from app.services.foundation import food_eligibility
        result = {"state": food_eligibility(items[inputs["item_id"]], set(inputs["allergies"]), set(inputs["restrictions"]),
                                            facts_confirmed=inputs["facts_confirmed"])["state"]}
    elif kind == "document":
        errors = document_integrity(data, inputs["document_id"])
        result = dict(integrity_valid=not errors, facts_proposed=not errors)
    else:
        raise ValueError(f"Unknown contract kind: {kind}")
    return result == expected, result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "reports/local/contract-evals.json")
    args = parser.parse_args(argv)
    data = ROOT / "data"
    path = ROOT / "evals/phase_1_contract.jsonl"
    cases = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    if not cases or len({c["id"] for c in cases}) != len(cases):
        raise ValueError("Empty eval contract or duplicate case ID")
    spec = SafetySpec.model_validate_json((data / "safety/rule_spec.yaml").read_text(encoding="utf-8"))
    items = {i.item_id: i for i in read_catalogues(data)}
    results = []
    for case in cases:
        passed, observed = run_case(case, data, spec, items)
        results.append(dict(id=case["id"], kind=case["kind"], passed=passed, observed=observed))
    report = dict(dataset_sha256=sha256(path.read_bytes()).hexdigest(),
                  scope="Visible deterministic regression cases; no model/OCR execution or clinical validation",
                  total=len(results), passed=sum(r["passed"] for r in results), results=results)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in report.items() if k != "results"}, indent=2))
    for result in results:
        if not result["passed"]:
            print(json.dumps(result))
    return int(report["passed"] != report["total"])


if __name__ == "__main__":
    raise SystemExit(main())
