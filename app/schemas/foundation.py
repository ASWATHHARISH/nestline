"""Typed catalogues and review records shared by later agents and offline evals."""

from datetime import date
import re
from typing import Literal, Self

from pydantic import Field, model_validator

from app.schemas.content import Applicability, Checksum, ConditionKey, Contract, Identifier, Text


class CatalogueItem(Contract):
    item_id: Identifier
    kind: Literal["food", "movement", "wellbeing", "followup", "comparison"]
    title: Text
    description: Text
    applies_to: Applicability
    jurisdiction: list[Text] = Field(min_length=1)
    evidence_span_ids: list[Identifier] = Field(default_factory=list)
    conditions_required: list[ConditionKey] = Field(default_factory=list)
    conditions_excluded: list[ConditionKey] = Field(default_factory=list)
    status: Literal["draft", "published"] = "draft"
    version: Text = "1.0.0"
    blockers: list[Text] = Field(default_factory=list)
    # Structured details vary by catalogue; the validator checks kind-specific keys.
    details: dict = Field(default_factory=dict)


class ClaimAudit(Contract):
    fragment_id: Identifier
    record_checksum: Checksum
    evidence_ids: list[Identifier] = Field(min_length=1)
    support: Literal["exact_quote", "supported_paraphrase", "needs_correction"]
    assessment_kind: Literal["agent_assessment", "human_review"]
    assessor: Text
    checked_at: date
    conditions_supported: bool
    timing_supported: bool
    jurisdiction_proposal_explicit: bool
    rationale: Text


class Approval(Contract):
    """A human attestation binds a role and decision to the reviewed release content."""
    role: Literal["licence", "content", "clinical", "india_localisation", "product"]
    reviewer: Text
    qualification_or_capacity: Text
    reviewed_at: date
    disposition: Literal["approved", "changes_requested", "rejected"]
    release_checksum: Checksum
    notes: Text


class PlanItem(Contract):
    item_id: Identifier
    catalogue_id: Identifier
    evidence_span_ids: list[Identifier] = Field(min_length=1)
    confirmed_fact_ids: list[Identifier] = Field(default_factory=list)
    constraint_tags: list[Text] = Field(default_factory=list)
    state: Literal["proposed", "confirmed", "stale"] = "proposed"


class Plan(Contract):
    plan_id: Identifier
    workspace_id: Identifier
    version: int = Field(ge=1)
    journey: Applicability
    items: list[PlanItem] = Field(min_length=1)
    unresolved_conflicts: list[Text] = Field(default_factory=list)
    user_confirmed: bool = False
    source_release_checksum: Checksum


class SafetyRule(Contract):
    rule_id: Identifier
    route: Literal["urgent", "clarify"]
    patterns: list[Text] = Field(min_length=1)
    evidence_span_ids: list[Identifier] = Field(min_length=1)
    reference_locators: list[dict] = Field(default_factory=list)
    rationale: Text


    @model_validator(mode="after")
    def patterns_compile(self) -> Self:
        for pattern in self.patterns:
            try:
                re.compile(pattern)
            except re.error as exc:
                raise ValueError(f"invalid safety-rule pattern for {self.rule_id}") from exc
        return self


class SafetyHelpRoute(Contract):
    number: Text
    jurisdiction: Literal["IN"]
    source_url: str = Field(pattern=r"^https://[^\s]+$")
    verified_on: date
    use: str = ""


class SafetySpec(Contract):
    version: Text
    status: Literal["draft", "published"]
    jurisdiction: Literal["IN"]
    language: Literal["en"]
    urgent_message: Text
    clarify_message: Text
    no_match_message: Text
    help_routes: dict[Identifier, SafetyHelpRoute]
    rules: list[SafetyRule] = Field(min_length=1)
    limitations: list[Text] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_rule_ids(self) -> Self:
        rule_ids = [rule.rule_id for rule in self.rules]
        if len(rule_ids) != len(set(rule_ids)):
            raise ValueError("safety specification contains duplicate rule IDs")
        return self
