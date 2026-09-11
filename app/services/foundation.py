"""Offline checks for source freshness, catalogues, claim audits and approvals.

Passing these checks proves explicit contracts. Only qualified people can approve
medical semantics, local practice or licences; their decisions are never inferred.
"""

import csv
from datetime import date
from hashlib import sha256
from io import StringIO
import json
import re
from pathlib import Path
from typing import get_args

from app.schemas.content import ConditionKey
from app.schemas.foundation import Approval, CatalogueItem, ClaimAudit, SafetySpec


def fingerprint(value) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def claim_fingerprint(fragment, evidence) -> str:
    return fingerprint({"fragment": review_subject(fragment.model_dump(mode="json")),
                        "evidence": [review_subject(evidence[ref].model_dump(mode="json")) for ref in fragment.evidence_span_ids]})


def review_subject(value):
    """Exclude workflow attestations so recording approval does not invalidate it.

    Text, conditions, permissions, source dates and versions remain bound. Separate
    publication checks enforce status and blockers; stripping them is not approval.
    """
    if isinstance(value, list):
        return [review_subject(v) for v in value]
    if isinstance(value, dict):
        return {k: review_subject(v) for k, v in value.items()
                if k not in {"review", "status", "publication_blockers", "blockers"}}
    return value


def read_catalogues(data: Path) -> list[CatalogueItem]:
    result = []
    structured = {"applies_to", "jurisdiction", "evidence_span_ids", "conditions_required",
                  "conditions_excluded", "blockers", "details"}
    for path in sorted((data / "catalogues").glob("*.csv")):
        with path.open(encoding="utf-8", newline="") as stream:
            for row in csv.DictReader(stream):
                for key in structured:
                    row[key] = json.loads(row[key])
                result.append(CatalogueItem.model_validate_json(json.dumps(row)))
    return result


def source_freshness(source, today: date) -> list[str]:
    errors = []
    if source.last_checked_at is None or source.last_checked_at > today:
        errors.append("source check date is missing or future-dated")
    if source.retrieved_at is None or source.next_review_at is None:
        errors.append("capture or next-review date missing")
    elif source.retrieved_at > today or source.next_review_at < today:
        errors.append("source capture is future-dated or revalidation is overdue")
    if source.revalidation_status != "current_capture":
        errors.append("source currency decision pending or source changed/withdrawn")
    return errors


def release_fingerprint(data: Path) -> str:
    """Hash the review subject, excluding workflow attestations and derived views.

    An approval cannot survive a content, catalogue, condition or safety edit.
    The review ledger is excluded to avoid a self-referential checksum.
    """
    files = []
    for folder in ("guidelines", "weekly", "catalogues", "safety", "plans", "synthetic"):
        for path in sorted((data / folder).rglob("*")):
            if path.is_file():
                if path.name == "coverage_matrix.csv":
                    continue  # Derived status view is checked against the manifest.
                if folder == "synthetic" and path.name == "stage5_retrieval_fixtures.json":
                    # Stage 5 retrieval truth is downstream test evidence, not part
                    # of the Stage 0 content subject approved by human reviewers.
                    continue
                if path.suffix.casefold() in {".pdf", ".png", ".jpg", ".jpeg"}:
                    digest = sha256(path.read_bytes()).hexdigest()
                else:
                    raw = path.read_text(encoding="utf-8")  # Normalises platform line endings.
                    if folder in {"guidelines", "weekly", "catalogues", "safety"}:
                        if path.suffix == ".csv":
                            value = list(csv.DictReader(StringIO(raw)))
                            # CSV review fields contain JSON but are removed as a whole.
                        elif path.suffix == ".jsonl":
                            value = [json.loads(line) for line in raw.splitlines() if line]
                        elif path.suffix in {".json", ".yaml"}:
                            value = json.loads(raw)
                        else:
                            value = raw
                        digest = fingerprint(review_subject(value))
                    else:
                        digest = sha256(raw.encode()).hexdigest()
                files.append((path.relative_to(data).as_posix(), digest))
    return fingerprint(files)


def approval_errors(data: Path, today: date) -> list[str]:
    ledger = json.loads((data / "reviews/approvals.json").read_text(encoding="utf-8"))
    records = [Approval.model_validate_json(json.dumps(r)) for r in ledger["reviews"]]
    checksum = release_fingerprint(data)
    errors = []
    for role in get_args(Approval.model_fields["role"].annotation):
        matches = [r for r in records if r.role == role and r.release_checksum == checksum]
        if not matches or matches[-1].disposition != "approved" or matches[-1].reviewed_at > today:
            errors.append(f"release needs actual {role} approval for current data fingerprint")
    return errors


def validate_foundation(bundle, data: Path) -> list[str]:
    errors = []
    evidence = {e.evidence_id: e for e in bundle.evidence}
    fragments = {f.fragment_id: f for f in bundle.fragments}
    registry = json.loads((data / "guidelines/condition_registry.yaml").read_text(encoding="utf-8"))
    keys = [r["key"] for r in registry["conditions"]]
    if set(keys) != set(get_args(ConditionKey)) or len(keys) != len(set(keys)):
        errors.append("condition registry differs from typed condition keys")
    items = read_catalogues(data)
    if len({i.item_id for i in items}) != len(items):
        errors.append("duplicate catalogue ID")
    required_details = {
        "food": {"ingredients", "allergens", "nutrient_roles", "dietary_patterns", "food_safety", "quantity_basis"},
        "movement": {"intensity", "progression", "stop_rule_ids", "clearance_policy"},
        "wellbeing": {"steps", "consent_prompt", "persistent_route", "urgent_route"},
        "followup": {"timing_unit", "start", "end", "schedule_context", "dedupe_key"},
        "comparison": {"profile_id", "measurement_basis", "measurement_value", "object_dimension_mm",
                       "illustrative_only", "image_key", "hide_reason"},
    }
    for item in items:
        if not required_details[item.kind] <= item.details.keys():
            errors.append(f"{item.item_id}: missing structured catalogue details")
        # An unverified editorial comparison is retained as an explicit hidden draft.
        exception = item.kind == "comparison" and item.status == "draft" and item.details.get("hide_reason")
        if not item.evidence_span_ids and not exception:
            errors.append(f"{item.item_id}: evidence required")
        for ref in item.evidence_span_ids:
            span = evidence.get(ref)
            if span is None:
                errors.append(f"{item.item_id}: unknown evidence {ref}")
            elif not span.applies_to.covers(item.applies_to):
                errors.append(f"{item.item_id}: evidence does not cover timing")
            elif "GLOBAL" not in span.jurisdiction and not set(item.jurisdiction) <= set(span.jurisdiction):
                errors.append(f"{item.item_id}: evidence does not cover jurisdiction")
            elif item.status == "published" and span.status != "published":
                errors.append(f"{item.item_id}: evidence is unpublished")
        if item.status == "published" and item.blockers:
            errors.append(f"{item.item_id}: unresolved blockers")
        if item.status == "draft" and not item.blockers:
            errors.append(f"{item.item_id}: draft needs explicit blockers")
        if set(item.conditions_required) & set(item.conditions_excluded):
            errors.append(f"{item.item_id}: contradictory conditions")
        if item.kind == "comparison" and item.status == "published":
            errors.append(f"{item.item_id}: comparison publication is not implemented; measurement and editorial review still required")
    audits = [ClaimAudit.model_validate_json(line) for line in
              (data / "reviews/claim_audit.jsonl").read_text(encoding="utf-8").splitlines() if line]
    if {a.fragment_id for a in audits} != fragments.keys() or len(audits) != len(fragments):
        errors.append("claim audit must cover every fragment exactly once")
    for audit in audits:
        fragment = fragments.get(audit.fragment_id)
        if fragment is None:
            continue
        if audit.record_checksum != claim_fingerprint(fragment, evidence):
            errors.append(f"{audit.fragment_id}: stale claim assessment")
        if set(audit.evidence_ids) != set(fragment.evidence_span_ids):
            errors.append(f"{audit.fragment_id}: claim assessment has different citations")
        if audit.support == "exact_quote" and fragment.text not in [evidence[r].text for r in audit.evidence_ids]:
            errors.append(f"{audit.fragment_id}: claimed quotation is not exact")
        if audit.support == "needs_correction" or not all((audit.conditions_supported, audit.timing_supported,
                                                         audit.jurisdiction_proposal_explicit)):
            errors.append(f"{audit.fragment_id}: unresolved claim assessment")
        if audit.checked_at > date.today():
            errors.append(f"{audit.fragment_id}: assessment is future-dated")
    spec = SafetySpec.model_validate_json((data / "safety/rule_spec.yaml").read_text(encoding="utf-8"))
    rule_ids = {r.rule_id for r in spec.rules}
    if len(rule_ids) != len(spec.rules):
        errors.append("duplicate safety rule ID")
    sources = {s.source_id: s for s in bundle.sources}
    for rule in spec.rules:
        if not set(rule.evidence_span_ids) <= evidence.keys():
            errors.append(f"{rule.rule_id}: unknown safety evidence")
        for ref in rule.reference_locators:
            if ref.get("source_id") not in sources or not ref.get("locator") or ref.get("use") != "link_only_clinical_review_reference":
                errors.append(f"{rule.rule_id}: invalid external clinical reference")
        for pattern in rule.patterns:
            try:
                re.compile(pattern)
            except re.error:
                errors.append(f"{rule.rule_id}: invalid regular expression")
    for item in items:
        if item.kind == "movement" and not set(item.details.get("stop_rule_ids", [])) <= rule_ids:
            errors.append(f"{item.item_id}: unknown movement stop rule")
    if spec.status == "published":
        errors.extend(approval_errors(data, date.today()))
    return errors


def release_errors(bundle, data: Path, today: date) -> list[str]:
    """Complete Stage 0 release gate; engineering success never grants approval."""
    from app.services.content_validation import REPRESENTATIVE_PROFILE_IDS, REQUIRED_DAY_IDS

    errors = approval_errors(data, today)
    published = {p.profile_id for p in bundle.profiles if p.status == "published"}
    for missing in sorted((REPRESENTATIVE_PROFILE_IDS | REQUIRED_DAY_IDS) - published):
        errors.append(f"release requires reviewed, published profile: {missing}")
    items = read_catalogues(data)
    for item in items:
        if item.kind != "comparison" and item.status != "published":
            errors.append(f"release requires reviewed catalogue item: {item.item_id}")
    used = {e.source_id for e in bundle.evidence}
    for source in bundle.sources:
        if source.source_id in used:
            errors.extend(f"{source.source_id}: {e}" for e in source_freshness(source, today))
    spec = SafetySpec.model_validate_json((data / "safety/rule_spec.yaml").read_text(encoding="utf-8"))
    if spec.status != "published":
        errors.append("reviewed safety contract required; draft regex examples cannot protect live users")
    return errors


def food_eligibility(item, allergies: set[str], restrictions: set[str], *, facts_confirmed: bool) -> dict:
    """Constraint contract, not a meal prescriber. No inferred allergy-free state."""
    if not facts_confirmed:
        return {"state": "needs_information", "reason": "Confirm dietary constraints first."}
    if item.kind != "food":
        raise ValueError("food eligibility requires a food catalogue item")
    allergies = {a.strip().lower().replace(" ", "_") for a in allergies}
    restrictions = {r.strip().lower().replace(" ", "_") for r in restrictions}
    known_allergens = {"milk", "egg", "soy", "fish", "peanut", "tree_nuts", "wheat", "sesame", "shellfish"}
    known_restrictions = {"milk", "curd", "paneer", "pulses", "whole_grains", "leafy_vegetables", "egg",
                          "chicken", "fish", "soya", "nuts", "fruit", "vegan", "vegetarian"}
    if allergies - known_allergens or restrictions - known_restrictions:
        return {"state": "needs_information", "reason": "Unrecognised constraint needs clarification; never assume it is harmless."}
    allergens = set(item.details["allergens"])
    ingredients = set(item.details["ingredients"])
    conflicts = (allergens & allergies) | (ingredients & restrictions)
    patterns = set(item.details["dietary_patterns"])
    conflicts |= (restrictions & {"vegan", "vegetarian"}) - patterns
    if conflicts:
        return {"state": "not_applicable", "reason": "Conflicts with: " + ", ".join(sorted(conflicts))}
    if item.details.get("ingredient_detail_required") or item.details.get("additional_review_required"):
        return {"state": "needs_information", "reason": "Exact ingredient, recipe or species needs checking."}
    return {"state": "eligible_for_review", "reason": "Known constraints match; labels and cross-contact still need checking."}
