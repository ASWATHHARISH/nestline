"""Rebind an otherwise-current Stage 1 audit to the governed data fingerprint.

This is intentionally narrower than rebuilding the audit from transient ingestion
runs.  It refuses to write when source coverage, candidates, evidence, parser
provenance, checksums, or review tasks have changed.  The only accepted mismatch
is the top-level foundation fingerprint, which can change when a later stage adds
governed fixtures without changing the audited public-source runs.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.schemas.ingestion import Stage1Audit
from app.services.foundation import release_fingerprint
from app.services.ingestion_audit import validate_stage1_audit
from scripts.validate_content import load_bundle


ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "data/ingestion/audit/stage1-source-audit.json"
FINGERPRINT_ONLY_ERROR = (
    "canonical audit was generated for a different Stage 0 release fingerprint"
)


def main() -> int:
    bundle = load_bundle(ROOT / "data")
    audit = Stage1Audit.model_validate_json(AUDIT_PATH.read_text(encoding="utf-8"))
    errors = validate_stage1_audit(audit, bundle, ROOT / "data")
    if errors != [FINGERPRINT_ONLY_ERROR]:
        raise RuntimeError(
            "Refusing to rebind: the audit has changes beyond the release fingerprint: "
            + json.dumps(errors)
        )

    rebound = audit.model_copy(update={
        "foundation_release_fingerprint": release_fingerprint(ROOT / "data")
    })
    remaining = validate_stage1_audit(rebound, bundle, ROOT / "data")
    if remaining:
        raise RuntimeError("Rebound audit did not validate: " + json.dumps(remaining))
    AUDIT_PATH.write_text(
        json.dumps(rebound.model_dump(mode="json"), indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps({
        "valid": True,
        "sources": len(rebound.sources),
        "mode": "fingerprint_only_rebind",
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
