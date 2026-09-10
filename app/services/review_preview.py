"""Read-only assembly for human review of draft weekly screens."""

from collections import defaultdict

from app.schemas.content import ContentBundle
from app.schemas.foundation import CatalogueItem
from app.schemas.ingestion import Stage1ReviewLedger
from app.services.content_selection import condition_state

RELEASE_ROLES = ("licence", "content", "clinical", "india_localisation", "product")


def comparison_gate(items: list[CatalogueItem]) -> dict:
    """Describe the comparison release state without returning display wording."""
    comparisons = [item for item in items if item.kind == "comparison"]
    verified = [item for item in comparisons
                if item.details.get("measurement_value") is not None
                and item.details.get("object_dimension_mm") is not None]
    published = [item for item in comparisons if item.status == "published"]
    partially_verified = [item for item in comparisons
                          if ((item.details.get("measurement_value") is None)
                              != (item.details.get("object_dimension_mm") is None))]
    safely_hidden = [item for item in comparisons
                     if item.status == "draft" and item.details.get("hide_reason")]
    return {
        "total": len(comparisons),
        "verified_count": len(verified),
        "published_count": len(published),
        "hidden_count": len(comparisons) - len(published),
        "partially_verified_count": len(partially_verified),
        "safe": (bool(comparisons) and not published and not partially_verified
                 and len(safely_hidden) == len(comparisons)),
    }


def build_review_preview(bundle: ContentBundle, ledger: Stage1ReviewLedger,
                         profile_id: str, *, confirmed: frozenset[str] = frozenset(),
                         absent: frozenset[str] = frozenset()) -> dict:
    """Assemble draft cards and review state without making them runtime content.

    This deliberately bypasses published-content selection only for the labelled
    reviewer screen. The returned state must never be used by live RAG.
    """
    profiles = {profile.profile_id: profile for profile in bundle.profiles}
    if profile_id not in {"PC00", "P10", "PP01"}:
        raise ValueError("review preview supports only PC00, P10 and PP01")
    profile = profiles[profile_id]
    fragments = {fragment.fragment_id: fragment for fragment in bundle.fragments}
    evidence = {item.evidence_id: item for item in bundle.evidence}
    sources = {source.source_id: source for source in bundle.sources}
    decisions: dict[str, dict[str, object]] = defaultdict(dict)
    for decision in ledger.decisions:
        decisions[decision.evidence_id][decision.role] = decision

    cards_by_slot = {}
    for slot, fragment_ids in profile.card_slots.model_dump().items():
        cards = []
        for fragment_id in fragment_ids:
            fragment = fragments[fragment_id]
            state, reason = condition_state(
                fragment.conditions_required, fragment.conditions_excluded,
                confirmed, absent)
            linked_evidence = [evidence[item] for item in fragment.evidence_span_ids]
            accepted_roles = [role for role in RELEASE_ROLES if all(
                decisions[item.evidence_id].get(role)
                and decisions[item.evidence_id][role].decision == "accepted"
                for item in linked_evidence)]
            cards.append({
                "fragment_id": fragment.fragment_id,
                "text": fragment.text,
                "state": state,
                "state_reason": reason,
                "required_conditions": list(fragment.conditions_required),
                "excluded_conditions": list(fragment.conditions_excluded),
                "evidence_ids": [item.evidence_id for item in linked_evidence],
                "sources": [{"title": sources[item.source_id].title,
                             "url": sources[item.source_id].canonical_url,
                             "source_id": item.source_id}
                            for item in linked_evidence],
                "accepted_roles": accepted_roles,
                "pending_roles": [role for role in RELEASE_ROLES if role not in accepted_roles],
            })
        cards_by_slot[slot] = cards

    card_count = sum(len(cards) for cards in cards_by_slot.values())
    if profile_id == "PC00":
        metrics = [
            ("Journey state", "Possible pregnancy", "Not confirmed"),
            ("Timing", "Not shown", "No week is inferred"),
            ("Baby size", "Not shown", "Pregnancy is not confirmed"),
            ("Proposed cards", str(card_count), "Product/content accepted"),
        ]
    elif profile_id == "P10":
        metrics = [
            ("Current stage", "Week 10", "Confirmed pregnancy preview"),
            ("Development", "About 2.5 cm*", "General source estimate"),
            ("Size comparison", "Hidden", "Measurement/object review pending"),
            ("Proposed cards", str(card_count), "Product/content accepted"),
        ]
    else:
        metrics = [
            ("Current stage", "Week 1", "After birth"),
            ("Main focus", "Rest & support", "Draft reviewer wording"),
            ("Baby size", "Not applicable", "Postpartum profile"),
            ("Proposed cards", str(card_count), "Product/content accepted"),
        ]
    return {
        "profile_id": profile.profile_id,
        "title": profile.hero.title,
        "profile_status": profile.status,
        "metrics": metrics,
        "cards_by_slot": cards_by_slot,
        "slot_notes": profile.slot_notes,
        "publication_blockers": profile.publication_blockers,
    }
