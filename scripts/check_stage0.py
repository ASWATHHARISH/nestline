"""Record reproducible local Stage 0 checks without changing publication state."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run(arguments: list[str]) -> dict:
    result = subprocess.run([sys.executable, *arguments], cwd=ROOT, capture_output=True, text=True)
    return {"arguments": arguments, "exit_code": result.returncode,
            "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "docs/STAGE-0-CHECK-RESULTS.json")
    args = parser.parse_args(argv)
    tests = run(["-m", "unittest", "discover", "-s", "tests", "-q"])
    count = re.search(r"Ran (\d+) tests?", tests["stderr"])
    checks = {"software_tests": tests}
    for name, extra in (("authoring_validation", []), ("review_readiness", ["--require-review-ready"]),
                        ("publication_gate", ["--require-release"])):
        checks[name] = run(["-m", "scripts.validate_content", *extra])
    checks["dependencies"] = run(["-m", "pip", "check"])
    checks["software_contract_cases"] = run(["-m", "scripts.run_contract_evals"])
    report = {"checked_at_utc": datetime.now(timezone.utc).isoformat(),
              "execution": "Local checks; this report does not attest a GitHub Actions run",
              "tests_run": int(count.group(1)) if count else None,
              "checks": checks,
              "limitations": ["Engineering tests are not model or clinical evaluations.",
                              "Review readiness is not content approval or publication.",
                              "Checksums establish local integrity, not publisher authenticity."]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(
        (json.dumps(report, indent=2) + "\n").encode())
    for name, result in checks.items():
        print(f"{name}: exit {result['exit_code']}")
    # Release is reported independently: an unpublished draft must not look like
    # a release simply because its engineering checks passed.
    if any(result["exit_code"] for name, result in checks.items() if name != "publication_gate"):
        return 1
    return checks["publication_gate"]["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
