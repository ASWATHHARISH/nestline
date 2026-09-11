"""Static validation helpers for the Stage 3 deterministic onboarding boundary."""

from pathlib import Path


def validate_stage3_migration(path: Path) -> list[str]:
    lowered = path.read_text(encoding="utf-8").casefold()
    errors = []
    required = {
        "effective date": "add column effective_date date",
        "calculation date": "add column calculation_date date",
        "confirmation time": "add column confirmed_at timestamptz",
        "confirmation identity": "add column confirmed_by_user_id uuid",
        "conflict counterpart": "add column conflicts_with_state_id uuid",
        "conflict difference": "add column dating_difference_days integer",
        "submission idempotency": "journey_states_workspace_onboarding_submission_key",
        "atomic commit": "function public.complete_onboarding",
        "authenticated owner": "not private.is_workspace_owner(requested_workspace_id)",
        "optimistic version": "stale journey version",
        "fact limit": "jsonb_array_length(requested_facts) > 40",
        "symptom timestamp": "(item->>'reported_at')::timestamptz > clock_timestamp()",
        "safety provenance": "safety_spec_version",
        "draft safety label": "safety_evaluation_only",
        "appointment validation": "invalid next appointment",
        "authenticated-only grant": "to authenticated",
        "read-only journey table": "revoke insert, update, delete on public.journey_states",
        "legacy mutation closed": "revoke execute on function public.replace_current_journey_state",
    }
    for label, fragment in required.items():
        if fragment not in lowered:
            errors.append(f"missing {label}")
    if "service_role" in lowered:
        errors.append("onboarding migration must not depend on a service-role client")
    return errors


def validate_deterministic_resolver(path: Path) -> list[str]:
    lowered = path.read_text(encoding="utf-8").casefold()
    errors = []
    required = {
        "testable clock": "class fixedclock",
        "verified due-day constant": "pregnancy_due_day = 280",
        "due-date calculation": "timing.estimated_due_date - resolved_on",
        "manual roll-forward": "timing.gestational_week * 7 + timing.gestational_day + elapsed",
        "month range": "resolve_approximate_month_range",
        "delivery calculation": "resolved_on - timing.delivery_date",
        "postpartum roll-forward": "timing.postpartum_week - 1",
        "conflict comparison": "compare_with_current",
        "episode regression": "episode_stage_regression",
    }
    for label, fragment in required.items():
        if fragment not in lowered:
            errors.append(f"missing {label}")
    for forbidden in ("openai", "langchain", "langgraph", "requests.post", "urllib.request"):
        if forbidden in lowered:
            errors.append(f"deterministic resolver unexpectedly depends on {forbidden}")
    return errors

def validate_stage3_hardening_migration(path: Path) -> list[str]:
    """Require every database-side invariant found by the Stage 3 exit audit."""

    lowered = path.read_text(encoding="utf-8").casefold()
    errors = []
    required = {
        "due-date arithmetic": "journey_states_edd_arithmetic_check",
        "delivery-date arithmetic": "journey_states_delivery_arithmetic_check",
        "confirmation provenance": "journey_states_confirmation_provenance_check",
        "draft safety enforcement": "symptom_events_onboarding_safety_draft_check",
        "deterministic position bounds": "function private.journey_state_position_bounds",
        "transition validator": "function private.validate_journey_state_transition",
        "transition trigger": "journey_states_validate_transition",
        "contiguous versions": "journey versions must be contiguous",
        "backward episode rejection": "start a new workspace for a new pregnancy after postpartum",
        "database conflict verification": "timing conflict provenance does not match the previous journey state",
        "private helper permissions": "from public, anon, authenticated",
        "demo confirmation provenance": "confirmed_by_user_id",
        "India date boundary": "asia/kolkata",
    }
    for label, fragment in required.items():
        if fragment not in lowered:
            errors.append(f"missing {label}")
    if "service_role" in lowered:
        errors.append("Stage 3 hardening must not depend on a service-role client")
    return errors
