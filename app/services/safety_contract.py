"""Conservative English rule contract for offline evaluation, not clinical triage.

The production entry point refuses a draft specification. A matched urgent rule
always wins over clarify rules; a model instruction cannot change that priority.
"""

import re
import unicodedata

from app.schemas.foundation import SafetySpec


def evaluate_safety_contract(spec: SafetySpec, message: str) -> dict:
    text = unicodedata.normalize("NFKC", message).lower().replace("’", "'")
    text = " ".join(text.split())
    matched = [rule for rule in spec.rules if any(re.search(p, text) for p in rule.patterns)]
    urgent = [r for r in matched if r.route == "urgent"]
    route = "urgent" if urgent else "clarify" if matched else "no_match"
    # No-match means only that this finite pattern set did not match. It is never
    # a medical reassurance, diagnosis, permission to exercise or dismissal.
    wording = spec.urgent_message if urgent else spec.clarify_message if matched else spec.no_match_message
    return {"route": route, "rule_ids": sorted(r.rule_id for r in urgent or matched),
            "message": wording, "generation_allowed": False,
            "evaluation_only": spec.status != "published", "spec_version": spec.version}


def route_safety(spec: SafetySpec, message: str) -> dict:
    if spec.status != "published":
        raise ValueError("Safety specification awaits qualified clinical and India review")
    return evaluate_safety_contract(spec, message)
