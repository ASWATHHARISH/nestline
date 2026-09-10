"""Stage 0 selection contract for later retrieval and UI implementations.

This does not calculate due dates, answer symptoms, or replace the Safety Gate.
Callers must supply an already resolved time range and confirmed conditions.
"""

from typing import get_args

from app.schemas.content import Applicability, ConditionKey, ContentBundle
from app.services.content_validation import validate_bundle

# These are the architecture's approximate month ranges, not exact dating.
# Month nine extends through the representable range: it never chooses week 40.
MONTH_RANGES = {1: (1, 4), 2: (5, 8), 3: (9, 13), 4: (14, 17), 5: (18, 22),
                6: (23, 27), 7: (28, 31), 8: (32, 35), 9: (36, 42)}


def pregnancy_month_scope(month: int) -> Applicability:
    """Keep uncertainty explicit instead of silently selecting a weekly hero."""
    if type(month) is not int or month not in MONTH_RANGES:
        raise ValueError("pregnancy month must be an integer from 1 to 9")
    start, end = MONTH_RANGES[month]
    return Applicability(stage="pregnancy", unit="week", start=start, end=end)


def condition_state(required, excluded, confirmed, absent) -> tuple[str, str]:
    """Three-valued logic: missing is unknown, never permission or clearance."""
    if set(required) & absent or set(excluded) & confirmed:
        return "not_applicable", "A confirmed condition conflicts with this card."
    unknown = (set(required) - confirmed) | (set(excluded) - absent)
    if unknown:
        return "needs_information", "Confirm: " + ", ".join(sorted(unknown))
    return "shown", "Timing, country and recorded conditions match."


def postpartum_day_context(day: int) -> dict:
    """Birth is day 0. PP01 includes days 0-7; PP02 is 8-14; PP06 is 36-42.

    This explicit product convention preserves the agreed day-7 overlay on PP01.
    It is not an implicit Applicability.covers conversion or clinical scheduling.
    """
    if type(day) is not int or not 0 <= day <= 84:
        raise ValueError("postpartum day must be an integer from 0 to 84")
    return {"profile_id": f"PP{max(1, (day + 6) // 7):02d}",
            "overlay_id": f"PPD{day}" if day <= 7 else None}


def select_content(bundle: ContentBundle, scope: Applicability, jurisdiction: str,
                   confirmed_conditions: frozenset[str] = frozenset(),
                   confirmed_absent_conditions: frozenset[str] = frozenset()) -> dict:
    """Select published content per card; unknown conditions do not hide a week.

    All draft text remains withheld. Returned quotation cards must bypass model
    rewriting; only retrievable_fragment_ids may enter the later RAG pathway.
    """
    report = validate_bundle(bundle, require_coverage=False)
    if not report.valid:
        raise ValueError("invalid content bundle: " + "; ".join(report.errors))
    if confirmed_conditions & confirmed_absent_conditions:
        raise ValueError("condition cannot be both present and absent")
    if (confirmed_conditions | confirmed_absent_conditions) - set(get_args(ConditionKey)):
        raise ValueError("unknown condition key")
    for pair in ({"home_birth", "facility_birth"}, {"uncomplicated_delivery", "complicated_delivery_or_caesarean"}):
        if pair <= confirmed_conditions:
            raise ValueError("conflicting confirmed facts require clarification")

    def eligible(record):
        return (record.status == "published" and record.applies_to.covers(scope)
                and ("GLOBAL" in record.jurisdiction or jurisdiction in record.jurisdiction))

    decisions = {}
    for fragment in bundle.fragments:
        if eligible(fragment):
            decisions[fragment.fragment_id] = condition_state(
                fragment.conditions_required, fragment.conditions_excluded,
                confirmed_conditions, confirmed_absent_conditions)
    fragment_ids = sorted(key for key, (state, _) in decisions.items() if state == "shown")
    profiles = [p for p in bundle.profiles if eligible(p) and p.applies_to == scope]
    profile_cards = {}
    for profile in profiles:
        cards = {}
        for slot, refs in profile.card_slots.model_dump().items():
            cards[slot] = []
            for ref in refs:
                state, reason = decisions.get(ref, ("unavailable", "No published applicable content."))
                cards[slot].append({"fragment_id": ref, "state": state, "reason": reason})
            if not refs:
                cards[slot].append({"fragment_id": None, "state": "unavailable",
                                    "reason": profile.slot_notes.get(slot, "No reviewed content for this slot.")})
        profile_cards[profile.profile_id] = cards
    sources = {s.source_id: s for s in bundle.sources}
    evidence = {e.evidence_id: e for e in bundle.evidence}
    retrievable, quotations = [], []
    for fragment in bundle.fragments:
        if fragment.fragment_id not in fragment_ids:
            continue
        linked = [sources[evidence[ref].source_id] for ref in fragment.evidence_span_ids]
        if all(s.delivery_mode == "retrievable" and "embed" in s.allowed_use for s in linked):
            retrievable.append(fragment.fragment_id)
        else:
            source = linked[0]  # Validator requires one exact span for a fixed quote.
            quotations.append({"fragment_id": fragment.fragment_id, "text": fragment.text,
                               "presentation": "quotation", "attribution": source.attribution_text,
                               "source_url": source.canonical_url})
    return {"profile_ids": sorted(p.profile_id for p in profiles), "fragment_ids": fragment_ids,
            "profile_cards": profile_cards, "retrievable_fragment_ids": sorted(retrievable),
            "fixed_quote_fragment_ids": sorted(q["fragment_id"] for q in quotations),
            "quotation_cards": quotations,
            "status": "available" if profiles or fragment_ids else "content_unavailable"}
