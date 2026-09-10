"""Stage 0 selection contract for later retrieval and UI implementations.

This does not calculate due dates, answer symptoms, or replace the Safety Gate.
Callers must supply an already resolved time range and confirmed conditions.
"""

from app.schemas.content import Applicability, ContentBundle
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


def select_content(bundle: ContentBundle, scope: Applicability, jurisdiction: str,
                   confirmed_conditions: frozenset[str] = frozenset(),
                   confirmed_absent_conditions: frozenset[str] = frozenset()) -> dict:
    """Return only published IDs supported across the entire requested interval.

    Missing conditions are unknown. In particular, an unreported contraindication
    is not the same as a clinician confirming that it is absent.
    The file-loading boundary must also validate source snapshot bytes.
    """
    report = validate_bundle(bundle, require_coverage=False)
    if not report.valid:
        raise ValueError("invalid content bundle: " + "; ".join(report.errors))
    if confirmed_conditions & confirmed_absent_conditions:
        raise ValueError("condition cannot be both present and absent")

    def eligible(record) -> bool:
        return (record.status == "published" and record.applies_to.covers(scope)
                and ("GLOBAL" in record.jurisdiction or jurisdiction in record.jurisdiction))

    fragment_ids = sorted(f.fragment_id for f in bundle.fragments if eligible(f)
                          and set(f.conditions_required) <= confirmed_conditions
                          and set(f.conditions_excluded) <= confirmed_absent_conditions)
    # A range can use stable fragments, but never an exact-week dashboard.
    # Do not return a whole card assembly whose conditional items were filtered out.
    profile_ids = sorted(p.profile_id for p in bundle.profiles if eligible(p)
                         and p.applies_to == scope
                         and set(p.guidance_fragment_ids) <= set(fragment_ids))
    return {"profile_ids": profile_ids, "fragment_ids": fragment_ids,
            "status": "available" if profile_ids or fragment_ids else "content_unavailable"}
