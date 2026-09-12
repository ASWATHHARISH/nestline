"""Provider-neutral benchmark evidence contracts for Stages 7 and 8."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from app.schemas.content import Contract, Text


class ProviderBenchmarkObservation(Contract):
    case_id: Text
    dataset_version: Text
    provider_id: Text
    model_id: Text
    completed: bool
    stage8_disposition: Literal["pass", "clarify", "abstain", "escalate", "failed"]
    citation_claim_support_passed: bool
    allergy_restriction_medication_violations: int = Field(ge=0)
    retries: int = Field(ge=0)
    timed_out: bool
    latency_ms: float = Field(ge=0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    estimated_cost_usd: float = Field(ge=0)
    manual_tone_review: Literal["pending", "pass", "fail"] = "pending"


class ProviderBenchmarkReport(Contract):
    schema_version: Literal["stage7-8-provider-benchmark-v1"] = "stage7-8-provider-benchmark-v1"
    status: Literal["blocked_not_authorized", "completed"]
    dataset_version: Text
    provider_id: Text | None = None
    model_id: Text | None = None
    total_cases: int = Field(ge=0)
    completed_cases: int = Field(ge=0)
    stage8_passed_cases: int = Field(ge=0)
    citation_support_passed_cases: int = Field(ge=0)
    constraint_boundary_violations: int = Field(ge=0)
    timeouts: int = Field(ge=0)
    retries: int = Field(ge=0)
    latency_median_ms: float | None = Field(default=None, ge=0)
    latency_p95_ms: float | None = Field(default=None, ge=0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    estimated_cost_usd: float = Field(ge=0)
    manual_tone_reviews_pending: int = Field(ge=0)
    paid_calls_made: bool
    authorization_reference: str | None = None
    limitations: list[Text] = Field(min_length=1)

    @model_validator(mode="after")
    def report_is_honest(self):
        if self.status == "blocked_not_authorized":
            if self.paid_calls_made or self.completed_cases or self.estimated_cost_usd:
                raise ValueError("a blocked benchmark cannot claim calls or results")
            if self.authorization_reference is not None:
                raise ValueError("blocked benchmark cannot claim authorization")
        else:
            if not self.authorization_reference:
                raise ValueError("completed live benchmark requires explicit authorization evidence")
            if self.completed_cases > self.total_cases:
                raise ValueError("completed benchmark cases cannot exceed the dataset")
        return self