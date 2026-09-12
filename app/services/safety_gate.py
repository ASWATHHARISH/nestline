"""Deterministic Stage 6 Safety Gate and generation boundary.

Runtime health routing must use a reviewed, published specification. The draft
specification may be exercised only through the explicit evaluation mode used by
the visible development set. No model or external provider is used here.
"""

from __future__ import annotations

from collections.abc import Callable
from hashlib import sha256
import json
from pathlib import Path
import re
from time import perf_counter
from typing import Literal, TypeVar
import unicodedata

from pydantic import ValidationError

from app.schemas.foundation import SafetySpec
from app.schemas.safety import (
    FixedSafetyMessage,
    MentionContext,
    SafetyClarificationState,
    SafetyConfigurationFailure,
    SafetyContentOrigin,
    SafetyGateInput,
    SafetyGateResult,
    SafetyGenerationGuardResult,
    SafetyInputChannel,
    SafetyRuleMatch,
    SafetyTrace,
)


ExecutionMode = Literal["evaluation_only", "public_runtime"]
SUPPORTED_SPECIFICATION_VERSIONS = frozenset({"1.0.0"})
FALLBACK_MESSAGE_VERSION = "1.0.0"
FALLBACK_SPEC_VERSION = "unavailable"
FALLBACK_CLARIFICATION = (
    "Safety routing is unavailable, so routine guidance cannot continue. "
    "If symptoms are severe, worsening or you feel unsafe, seek urgent medical "
    "help. In India, call 112 for an emergency or go to the nearest emergency "
    "department. This message does not confirm that a symptom is safe."
)
MINIMUM_CLARIFICATION_QUESTION = (
    "Is this happening to you now, and is it severe, worsening, or making you feel unsafe?"
)

_SCOPED_NEGATION = re.compile(
    r"(?:\b(?:do not|don't|did not|didn't|never)\s+(?:currently\s+)?(?:have|feel|experience)|"
    r"\b(?:no|without|deny|denies|denied)\s+(?:current\s+)?|"
    r"\b(?:am|is|was)\s+not\s+(?:having|experiencing))\s+(?:any\s+)?$"
)
_HISTORICAL = re.compile(
    r"\b(history of|previously|prior|used to|years? ago|before (my )?pregnancy|"
    r"in (19|20)\d{2}|when i was (younger|a child))\b"
)
_HYPOTHETICAL = re.compile(r"\b(what if|hypothetically|suppose|imagining|if i were to)\b")
_THIRD_PERSON = re.compile(
    r"\b(my (mother|mom|sister|friend|wife|partner|patient)|she|he|they|the patient)\b"
)
_UNCERTAIN = re.compile(r"\b(maybe|might|possibly|i think|not sure|unsure|seem(?:s)? to)\b")
_SYMPTOM_LANGUAGE = re.compile(
    r"\b(symptom|pain|ache|bleed|bleeding|dizzy|dizziness|fever|temperature|"
    r"nausea|vomit|vomiting|breath|breathing|faint|headache|vision|swelling|"
    r"rash|itching|cramp|weak|weakness|fluid|movement|sad|anxious|overwhelmed|"
    r"unsafe|worse|worsening|medicine|medication|dose|contraction)\w*\b"
)
_PRODUCT_LANGUAGE = re.compile(
    r"\b(show|list|open|upload|download|organize|organise|delete|dashboard|settings?|"
    r"reminder|appointment|plan|meal|diet|fitness|movement|week|baby size|document|"
    r"record|profile|help me use|how do i use)\b"
)
_CURRENT_EXPERIENCE = re.compile(
    r"\b(i am|i'm|i have|i've|i feel|having|currently|right now|today|getting worse)\b"
)
_STORED_CONTEXT_LANGUAGE = re.compile(
    r"\b(record|records|recorded|saved|uploaded|document|documented|report|"
    r"prior|previous|history|restriction|constraint|profile)\b"
)
_EXPLICIT_PRODUCT_REQUEST = re.compile(
    r"\b(show|create|make|build|draft|prepare|list|use|give|open|organize|organise)\b"
    r".{0,120}\b(plan|options?|ideas?|meal|diet|fitness|exercise|activity|record|"
    r"dashboard|appointment|document|profile)\b"
)


def normalize_safety_text(value: str) -> str:
    """Normalize only representation; never interpret instructions as policy."""

    text = unicodedata.normalize("NFKC", value).translate(
        str.maketrans({"’": "'", "‘": "'", "`": "'", "“": '"', "”": '"'})
    )
    text = text.casefold()
    text = re.sub(r"\bcant\b", "can't", text)
    text = re.sub(r"\bdont\b", "don't", text)
    text = re.sub(r"\bcan\s+not\b", "cannot", text)
    text = re.sub(r"\bdificulty\b", "difficulty", text)
    text = re.sub(r"\bbrething\b", "breathing", text)
    return " ".join(text.split())


def _quoted(text: str, start: int, end: int) -> bool:
    # Apostrophes are deliberately excluded because contractions surrounding an
    # urgent phrase must not be mistaken for quotation marks.
    left = text.rfind('"', 0, start)
    right = text.find('"', end)
    if left >= 0 and right >= 0:
        return True
    prefix = text[max(0, start - 50):start]
    return bool(re.search(r"\b(quote|quoted|message says|document says|example:)\s*$", prefix))


def _mention_context(text: str, start: int, end: int) -> MentionContext:
    prefix = text[max(0, start - 90):start]
    clause = text[max(0, start - 90):min(len(text), end + 25)]
    if _quoted(text, start, end):
        return "quoted_text"
    if _THIRD_PERSON.search(prefix[-60:]):
        return "third_person"
    if _HISTORICAL.search(clause):
        return "historical_self"
    if _HYPOTHETICAL.search(prefix):
        return "hypothetical_self"
    if _SCOPED_NEGATION.search(prefix[-60:]):
        return "negated_self"
    if _UNCERTAIN.search(prefix):
        return "uncertain_self"
    return "current_self"


def _fixed_message(spec: SafetySpec, route: str) -> FixedSafetyMessage:
    if route == "urgent":
        message_id, wording = "S6-URGENT-IN", spec.urgent_message
        help_routes = sorted(spec.help_routes)
    elif route == "needs_clarification":
        message_id, wording = "S6-CLARIFY-IN", spec.clarify_message
        help_routes = sorted(spec.help_routes)
    else:
        message_id, wording = "S6-NON-URGENT-LIMIT-IN", spec.no_match_message
        help_routes = []
    return FixedSafetyMessage(
        message_id=message_id,
        message_version=spec.version,
        specification_version=spec.version,
        jurisdiction=spec.jurisdiction,
        text=wording,
        text_sha256=sha256(wording.encode("utf-8")).hexdigest(),
        help_route_ids=help_routes,
    )


def _fallback_message() -> FixedSafetyMessage:
    return FixedSafetyMessage(
        message_id="S6-CONFIGURATION-FAIL-CLOSED-IN",
        message_version=FALLBACK_MESSAGE_VERSION,
        specification_version=FALLBACK_SPEC_VERSION,
        jurisdiction="IN",
        text=FALLBACK_CLARIFICATION,
        text_sha256=sha256(FALLBACK_CLARIFICATION.encode("utf-8")).hexdigest(),
        help_route_ids=["emergency"],
    )


def _trace(
    request: SafetyGateInput,
    route: str,
    matches: list[SafetyRuleMatch],
    message: FixedSafetyMessage,
    latency_ms: float,
    stop_reason: str,
    normalized: str,
) -> SafetyTrace:
    return SafetyTrace(
        request_id=request.request_id,
        input_channel=request.input_channel,
        result_route=route,
        matched_rule_ids=sorted({match.rule_id for match in matches}),
        specification_version=message.specification_version,
        message_id=message.message_id,
        message_version=message.message_version,
        latency_ms=latency_ms,
        stop_reason=stop_reason,
        normalized_input_sha256=sha256(normalized.encode("utf-8")).hexdigest(),
        input_character_count=len(request.text),
    )


def _fail_closed(
    request: SafetyGateInput,
    failure: SafetyConfigurationFailure,
    *,
    started: float,
    spec: SafetySpec | None = None,
) -> SafetyGateResult:
    normalized = normalize_safety_text(request.text)
    message = _fixed_message(spec, "needs_clarification") if spec else _fallback_message()
    latency_ms = (perf_counter() - started) * 1000
    return SafetyGateResult(
        request_id=request.request_id,
        input_channel=request.input_channel,
        route="needs_clarification",
        matched_rules=[],
        clarification=SafetyClarificationState(
            required=True,
            question=MINIMUM_CLARIFICATION_QUESTION,
            reason=f"Safety routing stopped because of {failure.replace('_', ' ')}.",
        ),
        fixed_message=message,
        ordinary_generation_allowed=False,
        evaluation_only=False,
        public_routing_eligible=False,
        configuration_failure=failure,
        reasons=["configuration_failure", failure],
        trace=_trace(
            request, "needs_clarification", [], message, latency_ms,
            "configuration_failure", normalized,
        ),
    )


class SafetyGate:
    """One deterministic gate shared by every Stage 6 entry channel."""

    def __init__(self, spec: SafetySpec, *, mode: ExecutionMode):
        if mode not in {"evaluation_only", "public_runtime"}:
            raise ValueError("unsupported Safety Gate execution mode")
        self.spec = spec
        self.mode = mode

    def evaluate(self, request: SafetyGateInput) -> SafetyGateResult:
        started = perf_counter()
        if self.spec.version not in SUPPORTED_SPECIFICATION_VERSIONS:
            return _fail_closed(
                request, "unsupported_specification_version", started=started, spec=self.spec
            )
        if request.requested_spec_version and request.requested_spec_version != self.spec.version:
            return _fail_closed(
                request, "unsupported_specification_version", started=started, spec=self.spec
            )
        if self.mode == "public_runtime" and self.spec.status != "published":
            return _fail_closed(request, "draft_specification", started=started, spec=self.spec)

        normalized = normalize_safety_text(request.text)
        matches: list[SafetyRuleMatch] = []
        for rule in self.spec.rules:
            for pattern in rule.patterns:
                for found in re.finditer(pattern, normalized):
                    context = _mention_context(normalized, found.start(), found.end())
                    matches.append(SafetyRuleMatch(
                        rule_id=rule.rule_id,
                        configured_route=rule.route,
                        matched_text_sha256=sha256(found.group(0).encode("utf-8")).hexdigest(),
                        start=found.start(),
                        end=found.end(),
                        mention_context=context,
                        attributed_to_user=context in {"current_self", "uncertain_self"},
                    ))

        # Keep one deterministic match per rule/context/span, then sort independently
        # of specification ordering.
        unique = {
            (m.rule_id, m.start, m.end, m.mention_context): m for m in matches
        }
        matches = sorted(unique.values(), key=lambda m: (m.rule_id, m.start, m.end, m.mention_context))
        direct_urgent = [
            match for match in matches
            if match.configured_route == "urgent" and match.attributed_to_user
        ]
        contextual_urgent = [
            match for match in matches
            if match.configured_route == "urgent" and not match.attributed_to_user
        ]
        clarify_matches = [match for match in matches if match.configured_route == "clarify"]

        if direct_urgent:
            route = "urgent"
            clarification = SafetyClarificationState(required=False)
            allowed = False
            stop_reason = "urgent_match"
            reasons = ["deterministic_urgent_rule_match", "urgent_precedence_enforced"]
        elif contextual_urgent:
            route = "needs_clarification"
            clarification = SafetyClarificationState(
                required=True,
                question=MINIMUM_CLARIFICATION_QUESTION,
                reason="An urgent phrase was negated, historical, hypothetical, quoted, or about another person.",
            )
            allowed = False
            stop_reason = "context_not_attributed_to_user"
            reasons = ["urgent_phrase_context_requires_clarification", "no_user_attribution"]
        elif (product_reason := _non_symptom_product_reason(
            normalized, request.input_channel
        )) is not None:
            route = "non_urgent"
            clarification = SafetyClarificationState(required=False)
            allowed = True
            stop_reason = product_reason
            reasons = [product_reason, "no_medical_safety_claim"]
        elif clarify_matches or _SYMPTOM_LANGUAGE.search(normalized):
            route = "needs_clarification"
            clarification = SafetyClarificationState(
                required=True,
                question=MINIMUM_CLARIFICATION_QUESTION,
                reason="The text is symptom-like or medically ambiguous and does not meet an urgent rule.",
            )
            allowed = False
            stop_reason = "minimum_clarification_required"
            reasons = ["symptom_or_medical_ambiguity", "no_match_is_not_safety_clearance"]
        else:
            route = "needs_clarification"
            clarification = SafetyClarificationState(
                required=True,
                question=MINIMUM_CLARIFICATION_QUESTION,
                reason="The gate cannot determine that this is a clearly non-symptom product request.",
            )
            allowed = False
            stop_reason = "minimum_clarification_required"
            reasons = ["uncertain_request_type", "conservative_stop"]

        message = _fixed_message(self.spec, route)
        latency_ms = (perf_counter() - started) * 1000
        evaluation_only = self.mode == "evaluation_only" or self.spec.status != "published"
        return SafetyGateResult(
            request_id=request.request_id,
            input_channel=request.input_channel,
            route=route,
            matched_rules=matches,
            clarification=clarification,
            fixed_message=message,
            ordinary_generation_allowed=allowed,
            evaluation_only=evaluation_only,
            public_routing_eligible=(self.mode == "public_runtime" and self.spec.status == "published"),
            reasons=reasons,
            trace=_trace(request, route, matches, message, latency_ms, stop_reason, normalized),
        )


def _non_symptom_product_reason(
    text: str, channel: SafetyInputChannel,
) -> str | None:
    """Identify a product intent without treating stored constraints as symptoms.

    Urgent matching runs before this function. Current-experience language always
    remains on the safety path. A symptom vocabulary term may pass only when the
    sentence is an explicit product/record request or clearly attributes that term
    to stored context. The reason is recorded for cross-stage trace review.
    """

    if channel in {"onboarding_symptom", "symptom_check_in", "extracted_document_fact"}:
        return None
    if not _PRODUCT_LANGUAGE.search(text):
        return None
    if _CURRENT_EXPERIENCE.search(text):
        return None
    stored_context = _STORED_CONTEXT_LANGUAGE.search(text) is not None
    explicit_product = _EXPLICIT_PRODUCT_REQUEST.search(text) is not None
    if stored_context and explicit_product:
        return "stored_constraint_product_request"
    symptom_like = _SYMPTOM_LANGUAGE.search(text) is not None
    if not symptom_like:
        return "clearly_non_symptom_product_request"
    if stored_context:
        return "record_management_product_request"
    if explicit_product:
        return "explicit_non_symptom_product_request"
    return None


def _is_clearly_non_symptom_product_request(
    text: str, channel: SafetyInputChannel,
) -> bool:
    """Compatibility predicate retained for callers that need a boolean."""

    return _non_symptom_product_reason(text, channel) is not None


def build_safety_input(
    *,
    channel: SafetyInputChannel,
    text: str,
    requested_spec_version: str | None = None,
) -> SafetyGateInput:
    origins: dict[SafetyInputChannel, SafetyContentOrigin] = {
        "onboarding_symptom": "user_text",
        "chat_message": "user_text",
        "symptom_check_in": "user_text",
        "extracted_document_fact": "untrusted_document",
        "plan_generation_input": "system_plan_input",
    }
    return SafetyGateInput(
        input_channel=channel,
        content_origin=origins[channel],
        text=text,
        requested_spec_version=requested_spec_version,
    )


def evaluate_onboarding_symptom(gate: SafetyGate, text: str) -> SafetyGateResult:
    return gate.evaluate(build_safety_input(channel="onboarding_symptom", text=text))


def evaluate_chat_message(gate: SafetyGate, text: str) -> SafetyGateResult:
    return gate.evaluate(build_safety_input(channel="chat_message", text=text))


def evaluate_symptom_check_in(gate: SafetyGate, text: str) -> SafetyGateResult:
    return gate.evaluate(build_safety_input(channel="symptom_check_in", text=text))


def evaluate_extracted_document_fact(gate: SafetyGate, text: str) -> SafetyGateResult:
    return gate.evaluate(build_safety_input(channel="extracted_document_fact", text=text))


def evaluate_plan_generation_input(gate: SafetyGate, text: str) -> SafetyGateResult:
    return gate.evaluate(build_safety_input(channel="plan_generation_input", text=text))


def evaluate_safety_from_path(
    request: SafetyGateInput,
    spec_path: Path,
    *,
    mode: ExecutionMode,
) -> SafetyGateResult:
    started = perf_counter()
    try:
        raw = spec_path.read_text(encoding="utf-8")
    except OSError:
        return _fail_closed(request, "missing_specification", started=started)
    try:
        spec = SafetySpec.model_validate_json(raw)
    except (json.JSONDecodeError, ValidationError):
        return _fail_closed(request, "malformed_specification", started=started)
    return SafetyGate(spec, mode=mode).evaluate(request)


T = TypeVar("T")


def continue_after_safety_gate(
    result: SafetyGateResult,
    continuation: Callable[[], T],
) -> tuple[SafetyGenerationGuardResult, T | None]:
    """Typed pre-generation guard for the future Stage 7 boundary."""

    if not result.ordinary_generation_allowed:
        return (
            SafetyGenerationGuardResult(
                request_id=result.request_id,
                route=result.route,
                generation_called=False,
                generation_call_count=0,
                blocked_reason=result.trace.stop_reason,
            ),
            None,
        )
    value = continuation()
    return (
        SafetyGenerationGuardResult(
            request_id=result.request_id,
            route=result.route,
            generation_called=True,
            generation_call_count=1,
        ),
        value,
    )
