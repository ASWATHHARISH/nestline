"""Strict, versioned contracts for the deterministic Stage 6 Safety Gate.

These models describe software routing. They do not diagnose, establish that a
symptom is safe, or represent clinical validation.
"""

from __future__ import annotations

from hashlib import sha256
from typing import Literal, Self
from uuid import UUID, uuid4

from pydantic import Field, model_validator

from app.schemas.content import Contract, Identifier, Text


SAFETY_CONTRACT_VERSION = "6.0.0"

SafetyRoute = Literal["urgent", "needs_clarification", "non_urgent"]
SafetyInputChannel = Literal[
    "onboarding_symptom",
    "chat_message",
    "symptom_check_in",
    "extracted_document_fact",
    "plan_generation_input",
]
SafetyContentOrigin = Literal["user_text", "untrusted_document", "system_plan_input"]
MentionContext = Literal[
    "current_self",
    "uncertain_self",
    "negated_self",
    "historical_self",
    "hypothetical_self",
    "quoted_text",
    "third_person",
]
SafetyConfigurationFailure = Literal[
    "missing_specification",
    "malformed_specification",
    "unsupported_specification_version",
    "draft_specification",
]


class SafetyGateInput(Contract):
    """Data accepted by the gate; execution mode is trusted gate configuration."""

    contract_version: Literal["6.0.0"] = SAFETY_CONTRACT_VERSION
    request_id: UUID = Field(default_factory=uuid4)
    input_channel: SafetyInputChannel
    content_origin: SafetyContentOrigin
    text: str = Field(min_length=1, max_length=10_000)
    jurisdiction: Literal["IN"] = "IN"
    requested_spec_version: str | None = Field(default=None, min_length=1, max_length=100)

    @model_validator(mode="after")
    def channel_origin_agree(self) -> Self:
        if not self.text.strip():
            raise ValueError("safety input text cannot be blank")
        expected = {
            "onboarding_symptom": "user_text",
            "chat_message": "user_text",
            "symptom_check_in": "user_text",
            "extracted_document_fact": "untrusted_document",
            "plan_generation_input": "system_plan_input",
        }[self.input_channel]
        if self.content_origin != expected:
            raise ValueError(f"{self.input_channel} requires content_origin={expected}")
        return self


class SafetyRuleMatch(Contract):
    rule_id: Identifier
    configured_route: Literal["urgent", "clarify"]
    matched_text_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    mention_context: MentionContext
    attributed_to_user: bool

    @model_validator(mode="after")
    def valid_span_and_attribution(self) -> Self:
        if self.end <= self.start:
            raise ValueError("matched span must be ordered")
        should_attribute = self.mention_context in {"current_self", "uncertain_self"}
        if self.attributed_to_user != should_attribute:
            raise ValueError("attribution must agree with mention context")
        return self


class SafetyClarificationState(Contract):
    required: bool
    question: str = ""
    reason: str = ""

    @model_validator(mode="after")
    def complete_when_required(self) -> Self:
        if self.required and (not self.question.strip() or not self.reason.strip()):
            raise ValueError("required clarification needs a question and reason")
        if not self.required and (self.question or self.reason):
            raise ValueError("non-required clarification must be empty")
        return self


class FixedSafetyMessage(Contract):
    message_id: Identifier
    message_version: Text
    specification_version: Text
    jurisdiction: Literal["IN"]
    text: Text
    text_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    help_route_ids: list[Identifier] = Field(default_factory=list)


    @model_validator(mode="after")
    def text_matches_checksum(self) -> Self:
        expected = sha256(self.text.encode("utf-8")).hexdigest()
        if self.text_sha256 != expected:
            raise ValueError("fixed-message text checksum does not match")
        return self


class SafetyTrace(Contract):
    trace_id: UUID = Field(default_factory=uuid4)
    request_id: UUID
    contract_version: Literal["6.0.0"] = SAFETY_CONTRACT_VERSION
    input_channel: SafetyInputChannel
    result_route: SafetyRoute
    matched_rule_ids: list[Identifier] = Field(default_factory=list)
    specification_version: Text
    message_id: Identifier
    message_version: Text
    latency_ms: float = Field(ge=0)
    generation_call_count: Literal[0] = 0
    stop_reason: Literal[
        "urgent_match",
        "minimum_clarification_required",
        "context_not_attributed_to_user",
        "clearly_non_symptom_product_request",
        "stored_constraint_product_request",
        "record_management_product_request",
        "explicit_non_symptom_product_request",
        "configuration_failure",
    ]
    normalized_input_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    input_character_count: int = Field(ge=1, le=10_000)
    raw_input_recorded: Literal[False] = False


class SafetyGateResult(Contract):
    contract_version: Literal["6.0.0"] = SAFETY_CONTRACT_VERSION
    request_id: UUID
    input_channel: SafetyInputChannel
    route: SafetyRoute
    matched_rules: list[SafetyRuleMatch] = Field(default_factory=list)
    clarification: SafetyClarificationState
    fixed_message: FixedSafetyMessage
    ordinary_generation_allowed: bool
    evaluation_only: bool
    public_routing_eligible: bool
    configuration_failure: SafetyConfigurationFailure | None = None
    reasons: list[Text] = Field(min_length=1)
    no_medical_safety_claim: Literal[True] = True
    trace: SafetyTrace

    @model_validator(mode="after")
    def enforce_route_invariants(self) -> Self:
        if self.trace.request_id != self.request_id:
            raise ValueError("trace and result request IDs must agree")
        if self.trace.input_channel != self.input_channel or self.trace.result_route != self.route:
            raise ValueError("trace channel and route must agree with the result")
        match_ids = sorted({match.rule_id for match in self.matched_rules})
        if self.trace.matched_rule_ids != match_ids:
            raise ValueError("trace matched rules must agree with result matches")
        if self.trace.specification_version != self.fixed_message.specification_version:
            raise ValueError("trace and fixed-message specification versions must agree")
        if (self.trace.message_id, self.trace.message_version) != (
            self.fixed_message.message_id,
            self.fixed_message.message_version,
        ):
            raise ValueError("trace and fixed-message identity must agree")
        if self.route == "urgent":
            if not any(match.configured_route == "urgent" and match.attributed_to_user for match in self.matched_rules):
                raise ValueError("urgent result requires an urgent rule match")
            if self.ordinary_generation_allowed or self.clarification.required:
                raise ValueError("urgent result must stop generation without clarification delay")
        elif self.route == "needs_clarification":
            if self.ordinary_generation_allowed or not self.clarification.required:
                raise ValueError("clarification result must block generation and ask a question")
        else:
            if not self.ordinary_generation_allowed or self.clarification.required:
                raise ValueError("non-urgent product flow must permit generation without clarification")
        expected_message_ids = {
            "urgent": {"S6-URGENT-IN"},
            "needs_clarification": {"S6-CLARIFY-IN", "S6-CONFIGURATION-FAIL-CLOSED-IN"},
            "non_urgent": {"S6-NON-URGENT-LIMIT-IN"},
        }[self.route]
        if self.fixed_message.message_id not in expected_message_ids:
            raise ValueError("fixed-message identity does not match the route")
        if self.route == "urgent" and self.trace.stop_reason != "urgent_match":
            raise ValueError("urgent route requires the urgent stop reason")
        product_stop_reasons = {
            "clearly_non_symptom_product_request",
            "stored_constraint_product_request",
            "record_management_product_request",
            "explicit_non_symptom_product_request",
        }
        if self.route == "non_urgent" and self.trace.stop_reason not in product_stop_reasons:
            raise ValueError("non-urgent route requires a recognized product-intent reason")
        if self.configuration_failure is not None:
            if self.route != "needs_clarification" or self.ordinary_generation_allowed:
                raise ValueError("configuration failures must fail closed")
            if self.public_routing_eligible:
                raise ValueError("configuration failures cannot be public-routing eligible")
        if self.evaluation_only and self.public_routing_eligible:
            raise ValueError("evaluation-only routing cannot be publicly eligible")
        return self


class SafetyGenerationGuardResult(Contract):
    request_id: UUID
    route: SafetyRoute
    generation_called: bool
    generation_call_count: int = Field(ge=0, le=1)
    blocked_reason: str = ""

    @model_validator(mode="after")
    def consistent_call_state(self) -> Self:
        if self.generation_called != (self.generation_call_count == 1):
            raise ValueError("generation call count and called flag disagree")
        if self.route != "non_urgent" and self.generation_called:
            raise ValueError("urgent and clarification routes cannot call generation")
        if self.route == "non_urgent" and not self.generation_called:
            raise ValueError("an allowed non-urgent guard must call its supplied continuation")
        return self
