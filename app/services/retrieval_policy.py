"""Trusted Stage 5 policy, applicability, minimisation, and answerability.

This module is server-side infrastructure. RetrievalRequest never carries a purpose,
a workspace, a state version, or active conditions. A trusted caller selects one of
the fixed policies here; the gateway then rebuilds journey and condition state from
confirmed database records before any cache lookup or public applicability filter.
"""

from __future__ import annotations

from copy import deepcopy
import json
import re
from typing import Any

from app.schemas.content import ConditionKey, Domain
from app.schemas.retrieval import (
    AnswerabilityAssessment,
    AuthenticatedRetrievalScope,
    DOMAIN_PERSONAL_CONTEXTS,
    EvidenceRequirementPolicy,
    ExactPersonalContext,
    JourneyPosition,
    JourneyStateSnapshot,
    MissingInformation,
    PersonalFactCandidate,
    PersonalPassageCandidate,
    RetrievalPurpose, RuntimeBlocker,
    RetrievalRequest,
    TrustedRetrievalQuery,
    TrustedRetrievalState,
    UnresolvedConflict,
    canonical_evidence_policy_values, derive_answerability_values,
)

STOP_WORDS = {
    "a", "about", "after", "all", "am", "an", "and", "are", "at", "be",
    "can", "do", "for", "from", "give", "how", "i", "in", "is", "it",
    "me", "my", "of", "on", "or", "should", "the", "to", "what", "when",
    "which", "with", "you", "your",
}

# These words describe the container or journey, rather than the subject of a
# private passage. A match on only one of them must not make unrelated private
# text visible to a downstream worker (for example, a yoga question matching a
# peanut-allergy sentence only because both say "record").
PASSAGE_CONTAINER_TERMS = {
    "confirmed", "day", "document", "documents", "file", "files",
    "fictional", "pregnancy", "pregnant", "postpartum", "record", "records",
    "report", "reports", "says", "states", "week",
}

_CONTEXT_TERMS: dict[str, set[str]] = {
    "allergies": {"allergy", "allergies", "allergic", "peanut", "food"},
    "conditions": {"condition", "conditions", "history", "medical", "diagnosis"},
    "restrictions": {"restriction", "restrictions", "avoid", "clearance", "movement", "exercise", "activity"},
    "medications": {"medication", "medications", "medicine", "medicines", "dose", "prescription", "supplement"},
    "symptoms": {"symptom", "symptoms", "pain", "bleeding", "breathing", "fever", "nausea"},
    "appointments": {"appointment", "appointments", "visit", "visits", "scheduled", "date", "checkup", "check-up"},
    "plans": {"plan", "plans", "stale", "saved", "changed", "change"},
    "questions": {"question", "questions", "clarification", "followup", "follow-up"},
    "journey": {"pregnancy", "pregnant", "postpartum", "birth", "week", "day", "journey"},
    "documents": {"document", "documents", "report", "reports", "record", "records", "file", "files"},
}

_DOMAIN_CONTEXT = DOMAIN_PERSONAL_CONTEXTS

_FACT_CONTEXT: dict[str, str] = {
    "allergy": "allergies",
    "dietary_restriction": "restrictions",
    "medical_history": "conditions",
    "medication": "medications",
    "clinician_instruction": "restrictions",
    "feeding_status": "conditions",
    "delivery_history": "journey",
    "other": "documents",
}


def meaningful_tokens(value: str) -> set[str]:
    return {
        token for token in re.findall(r"[a-z0-9]+", value.casefold())
        if token not in STOP_WORDS and len(token) > 1
    }


def build_evidence_policy(
    purpose: RetrievalPurpose,
    domain: Domain,
) -> EvidenceRequirementPolicy:
    """Create one of four fixed policies in trusted application code."""

    return EvidenceRequirementPolicy(
        **canonical_evidence_policy_values(purpose, domain)
    )


def _journey_from_snapshot(snapshot: JourneyStateSnapshot | None) -> JourneyPosition | None:
    if snapshot is None or not snapshot.user_confirmed or snapshot.has_dating_conflict:
        return None
    if snapshot.stage == "possible_pregnancy":
        return JourneyPosition(stage="possible_pregnancy", unit="none")
    if snapshot.stage == "pregnancy" and snapshot.gestational_week is not None:
        return JourneyPosition(stage="pregnancy", unit="week", exact=snapshot.gestational_week)
    if snapshot.stage == "postpartum" and snapshot.postpartum_day is not None:
        return JourneyPosition(stage="postpartum", unit="day", exact=snapshot.postpartum_day)
    if snapshot.stage == "postpartum" and snapshot.postpartum_week is not None:
        return JourneyPosition(stage="postpartum", unit="week", exact=snapshot.postpartum_week)
    return None


def _same_journey(left: JourneyPosition, right: JourneyPosition) -> bool:
    return (
        left.stage == right.stage
        and left.unit == right.unit
        and left.start == right.start
        and left.end == right.end
    )


def _explicit_target(question: str, target: JourneyPosition) -> bool:
    text = question.casefold()
    if target.stage == "possible_pregnancy":
        return any(phrase in text for phrase in (
            "possible pregnancy", "might be pregnant", "pregnancy test",
        ))
    if target.start is None:
        return False
    values = {target.start, target.end}
    if target.unit == "week":
        position_named = any(
            re.search(rf"\bweek\s*{value}\b|\b{value}(?:st|nd|rd|th)?\s+week\b", text)
            for value in values if value is not None
        )
    else:
        position_named = any(
            re.search(rf"\bday\s*{value}\b|\b{value}(?:st|nd|rd|th)?\s+day\b", text)
            for value in values if value is not None
        )
    if not position_named:
        return False
    if target.stage == "postpartum":
        return any(phrase in text for phrase in ("postpartum", "after birth", "post-birth"))
    return "postpartum" not in text and "after birth" not in text


def _explicit_condition_keys(facts: list[PersonalFactCandidate]) -> set[ConditionKey]:
    result: set[ConditionKey] = set()
    allowed = set(ConditionKey.__args__)
    for fact in facts:
        if not isinstance(fact.value, dict):
            continue
        key = fact.value.get("condition_key")
        state = fact.value.get("condition_status", fact.value.get("status"))
        if key in allowed and state in {"confirmed_present", True, "present"}:
            result.add(key)
    return result


def build_trusted_query(
    request: RetrievalRequest,
    caller_scope: AuthenticatedRetrievalScope,
    resolved_scope: AuthenticatedRetrievalScope,
    exact: ExactPersonalContext,
    policy: EvidenceRequirementPolicy,
) -> tuple[TrustedRetrievalState, TrustedRetrievalQuery]:
    """Resolve applicability from database state before cache keys or filters."""

    if not policy.trusted_server_created or policy.domain != request.domain:
        raise ValueError("retrieval policy must be server-created for the request domain")
    current = _journey_from_snapshot(exact.journey_state)
    if current is None:
        effective = request.journey
        relation = "unconfirmed_current"
    elif _same_journey(current, request.journey):
        effective = current
        relation = "current"
    elif _explicit_target(request.question, request.journey):
        effective = request.journey
        relation = "explicit_other"
    else:
        effective = current
        relation = "overridden_to_current"

    conditions = _explicit_condition_keys(exact.confirmed_facts)
    if current is not None and current.stage == "pregnancy":
        conditions.add("pregnancy_confirmed")
    if relation == "explicit_other":
        conditions &= {"pregnancy_confirmed"}

    trusted_state = TrustedRetrievalState(
        scope=resolved_scope,
        current_journey=current,
        requested_journey=request.journey,
        effective_journey=effective,
        journey_relation=relation,
        active_conditions=sorted(conditions),
        caller_state_version_was_stale=(
            caller_scope.state_version != resolved_scope.state_version
        ),
        cache_state_version=resolved_scope.state_version,
        jurisdiction_source="request_profile",
    )
    query = TrustedRetrievalQuery(
        request_id=request.request_id,
        question=request.question,
        domain=request.domain,
        journey=effective,
        jurisdiction=request.jurisdiction,
        evidence_lanes=request.evidence_lanes,
        active_conditions=trusted_state.active_conditions,
        include_graph=request.include_graph,
        max_candidates=request.max_candidates,
        timeout_ms=request.timeout_ms,
        policy=policy,
        trusted_state=trusted_state,
    )
    return trusted_state, query


def _serialized_tokens(value: Any) -> set[str]:
    return meaningful_tokens(json.dumps(value, sort_keys=True, default=str))


def _query_mentions_context(query_tokens: set[str], context: str) -> bool:
    return bool(query_tokens & _CONTEXT_TERMS[context])


def _contexts_for_tokens(tokens: set[str]) -> set[str]:
    return {
        context for context, terms in _CONTEXT_TERMS.items()
        if tokens & terms
    }


def _fact_context(fact: PersonalFactCandidate) -> str:
    if isinstance(fact.value, dict):
        key = fact.value.get("condition_key")
        if key in {"movement_restriction", "exercise_clearance", "feels_ready_for_gentle_activity"}:
            return "restrictions"
        if key == "current_warning_symptom":
            return "symptoms"
    return _FACT_CONTEXT[fact.fact_type]


def _fact_relevant(
    fact: PersonalFactCandidate,
    query_tokens: set[str],
    policy: EvidenceRequirementPolicy,
) -> bool:
    context = _fact_context(fact)
    if context not in policy.personal_context_kinds:
        return False
    condition_key = (
        fact.value.get("condition_key") if isinstance(fact.value, dict) else None
    )
    if (
        condition_key in {
            "movement_restriction", "exercise_clearance",
            "feels_ready_for_gentle_activity",
        }
        and policy.domain != "movement"
    ):
        return False
    if condition_key == "current_warning_symptom" and policy.domain != "symptoms":
        return False
    if policy.purpose == "personal_record_lookup":
        value_tokens = _serialized_tokens(fact.value) - {
            "confirmed", "present", "subject", "fictional",
            "condition", "status",
        }
        return (
            _query_mentions_context(query_tokens, context)
            or bool(query_tokens & value_tokens)
        )
    if policy.purpose == "causal_explanation":
        return context in {"restrictions", "plans", "questions"}
    return context in _DOMAIN_CONTEXT[policy.domain]

def _conflict_relevant(
    conflict: UnresolvedConflict,
    query_tokens: set[str],
    policy: EvidenceRequirementPolicy,
) -> bool:
    type_tokens = meaningful_tokens(conflict.fact_type.replace("_", " "))
    value_tokens = _serialized_tokens(conflict.proposed_values)
    conflict_contexts = {
        _FACT_CONTEXT.get(conflict.fact_type, "documents"),
        *_contexts_for_tokens(type_tokens | value_tokens),
    }
    allowed_contexts = conflict_contexts & set(policy.personal_context_kinds)
    query_contexts = _contexts_for_tokens(query_tokens)
    value_overlap = bool(query_tokens & value_tokens)
    explicitly_conflicted = bool(
        query_tokens & {"conflict", "conflicting", "contradiction", "disagree"}
    )
    category_match = bool(
        (query_contexts - {"documents"})
        & (allowed_contexts - {"documents"})
    )
    return bool(allowed_contexts) and (
        value_overlap or category_match or explicitly_conflicted
    )

def _missing_relevant(
    missing: MissingInformation,
    query_tokens: set[str],
    policy: EvidenceRequirementPolicy,
    trusted_state: TrustedRetrievalState,
) -> bool:
    """Match a missing field to its subject, never only to a broad support lane."""

    field_tokens = meaningful_tokens(missing.field.replace("_", " "))
    field_contexts = _contexts_for_tokens(field_tokens)
    query_contexts = _contexts_for_tokens(query_tokens)
    allowed_contexts = set(policy.personal_context_kinds)
    is_journey_gap = "journey" in field_contexts
    if (
        is_journey_gap
        and "public_guidance" in policy.required_support
        and trusted_state.journey_relation == "unconfirmed_current"
    ):
        return True

    # `documents` and support labels such as `personal_record` describe a
    # container/lane, not the missing subject. They cannot make an allergy gap
    # block an appointment lookup merely because both mention a record.
    specific_field = field_contexts - {"documents"}
    specific_query = query_contexts - {"documents"}
    if specific_field & specific_query & allowed_contexts:
        return True
    generic_field_tokens = {
        "detail", "details", "information", "missing", "personal",
        "record", "records", "required",
    }
    meaningful_field = field_tokens - generic_field_tokens
    if meaningful_field and query_tokens & meaningful_field:
        return True
    global_markers = {item.casefold().replace("-", "_")
                      for item in missing.required_for}
    return bool(global_markers & {"global", "all_requests"})

def minimise_personal_context(
    exact: ExactPersonalContext,
    trusted_state: TrustedRetrievalState,
    policy: EvidenceRequirementPolicy,
    question: str,
) -> ExactPersonalContext:
    """Return only context relevant to this worker/purpose; keep broad state internal."""

    query_tokens = meaningful_tokens(question)
    facts = [
        fact for fact in exact.confirmed_facts
        if _fact_relevant(fact, query_tokens, policy)
    ]
    wants_medications = _query_mentions_context(query_tokens, "medications")
    wants_symptoms = _query_mentions_context(query_tokens, "symptoms")
    wants_appointments = _query_mentions_context(query_tokens, "appointments")
    wants_plans = _query_mentions_context(query_tokens, "plans")
    wants_questions = _query_mentions_context(query_tokens, "questions")

    medications = exact.medications if (
        policy.purpose == "personal_record_lookup" and wants_medications
    ) else []
    symptoms = exact.symptoms if (
        policy.purpose == "personal_record_lookup" and wants_symptoms
    ) else []
    appointments = exact.appointments if (
        wants_appointments and policy.domain in {"preparation", "followup"}
    ) else []
    plan_states = exact.plan_states if (
        wants_plans and policy.purpose in {"personal_record_lookup", "causal_explanation"}
    ) else []
    open_questions = exact.open_questions if (
        wants_questions and policy.domain in {"preparation", "followup"}
    ) else []
    conflicts = [
        conflict for conflict in exact.unresolved_conflicts
        if _conflict_relevant(conflict, query_tokens, policy)
    ]
    missing = [
        item for item in exact.missing_information
        if _missing_relevant(item, query_tokens, policy, trusted_state)
    ]
    if (
        trusted_state.current_journey is None
        and trusted_state.journey_relation == "unconfirmed_current"
        and "public_guidance" in policy.required_support
        and not any("journey" in item.field or "week" in item.field for item in missing)
    ):
        missing.append(MissingInformation(
            field="journey_state",
            reason="No confirmed current journey state is available for current-stage guidance.",
            required_for=["public_guidance"],
        ))
    return ExactPersonalContext(
        journey_state=exact.journey_state,
        confirmed_facts=facts,
        medications=medications,
        symptoms=symptoms,
        appointments=appointments,
        plan_states=plan_states,
        open_questions=open_questions,
        unresolved_conflicts=conflicts,
        missing_information=missing,
    )


def personal_passage_relevant(
    passage: PersonalPassageCandidate,
    policy: EvidenceRequirementPolicy,
    question: str,
    *, component: str,
) -> bool:
    query_tokens = meaningful_tokens(question)
    passage_tokens = meaningful_tokens(passage.text)
    informative_overlap = bool(
        (query_tokens - PASSAGE_CONTAINER_TERMS)
        & (passage_tokens - PASSAGE_CONTAINER_TERMS)
    )
    query_topics = {
        context for context, terms in _CONTEXT_TERMS.items()
        if context not in {"documents", "journey"} and query_tokens & terms
    }
    passage_topics = {
        context for context, terms in _CONTEXT_TERMS.items()
        if context not in {"documents", "journey"} and passage_tokens & terms
    }
    if component == "personal_full_text":
        return informative_overlap or bool(query_topics & passage_topics)
    # Vector-only private hits are candidates, not answerability support, until a
    # semantic provider is benchmarked. This prevents deterministic fixture hashes
    # from turning unrelated private text into evidence.
    return False


def assess_answerability(
    policy: EvidenceRequirementPolicy,
    exact: ExactPersonalContext,
    public_count: int,
    weekly_present: bool,
    personal_passage_count: int,
    graph_count: int,
    blocking_reasons: list[RuntimeBlocker] | None = None,
) -> AnswerabilityAssessment:
    """Decide support through the same derivation enforced by the contract."""

    public_supported = bool(public_count or weekly_present)
    personal_supported = bool(
        exact.confirmed_facts or exact.medications or exact.symptoms
        or exact.appointments or exact.plan_states or exact.open_questions
        or personal_passage_count
    )
    constraint_supported = bool(exact.confirmed_facts)
    graph_supported = bool(graph_count)
    relevant_conflicts = [str(item.conflict_id) for item in exact.unresolved_conflicts]
    relevant_missing = [item.field for item in exact.missing_information]
    blockers = blocking_reasons or []
    derived = derive_answerability_values(
        policy.required_support,
        public_guidance_supported=public_supported,
        personal_record_supported=personal_supported,
        personal_constraints_present=constraint_supported,
        graph_relationship_supported=graph_supported,
        relevant_conflict_ids=relevant_conflicts,
        relevant_missing_fields=relevant_missing,
        blocking_reasons=blockers,
    )
    return AnswerabilityAssessment(
        policy_id=policy.policy_id, purpose=policy.purpose,
        public_guidance_supported=public_supported,
        personal_record_supported=personal_supported,
        personal_constraints_present=constraint_supported,
        graph_relationship_supported=graph_supported,
        required_support=policy.required_support,
        relevant_conflict_ids=relevant_conflicts,
        relevant_missing_fields=relevant_missing,
        blocking_reasons=blockers,
        **derived,
    )
