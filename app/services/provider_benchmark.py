"""Aggregation-only provider benchmark harness; it never calls a provider."""

from __future__ import annotations

from math import ceil
from statistics import median

from app.schemas.provider_benchmark import ProviderBenchmarkObservation, ProviderBenchmarkReport


def blocked_benchmark(dataset_version: str) -> ProviderBenchmarkReport:
    return ProviderBenchmarkReport(
        status="blocked_not_authorized",
        dataset_version=dataset_version,
        total_cases=0,
        completed_cases=0,
        stage8_passed_cases=0,
        citation_support_passed_cases=0,
        constraint_boundary_violations=0,
        timeouts=0,
        retries=0,
        input_tokens=0,
        output_tokens=0,
        estimated_cost_usd=0,
        manual_tone_reviews_pending=0,
        paid_calls_made=False,
        limitations=[
            "No provider/model is selected and no paid call was authorized or made.",
            "Deterministic fixtures do not establish live-provider answer quality.",
        ],
    )


def aggregate_authorized_benchmark(
    observations: list[ProviderBenchmarkObservation],
    *,
    authorization_reference: str,
) -> ProviderBenchmarkReport:
    if not observations:
        raise ValueError("an authorized benchmark report requires observations")
    identities = {(item.provider_id, item.model_id, item.dataset_version) for item in observations}
    if len(identities) != 1:
        raise ValueError("one benchmark report may cover only one provider/model/dataset")
    provider_id, model_id, dataset_version = next(iter(identities))
    latencies = sorted(item.latency_ms for item in observations if item.completed)
    p95 = latencies[max(0, ceil(0.95 * len(latencies)) - 1)] if latencies else None
    return ProviderBenchmarkReport(
        status="completed",
        dataset_version=dataset_version,
        provider_id=provider_id,
        model_id=model_id,
        total_cases=len(observations),
        completed_cases=sum(item.completed for item in observations),
        stage8_passed_cases=sum(item.stage8_disposition == "pass" for item in observations),
        citation_support_passed_cases=sum(item.citation_claim_support_passed for item in observations),
        constraint_boundary_violations=sum(
            item.allergy_restriction_medication_violations for item in observations
        ),
        timeouts=sum(item.timed_out for item in observations),
        retries=sum(item.retries for item in observations),
        latency_median_ms=median(latencies) if latencies else None,
        latency_p95_ms=p95,
        input_tokens=sum(item.input_tokens for item in observations),
        output_tokens=sum(item.output_tokens for item in observations),
        estimated_cost_usd=sum(item.estimated_cost_usd for item in observations),
        manual_tone_reviews_pending=sum(item.manual_tone_review == "pending" for item in observations),
        paid_calls_made=True,
        authorization_reference=authorization_reference,
        limitations=[
            "A completed benchmark compares this named provider/model only on the named frozen dataset.",
            "Automated validation does not replace the separate human tone or clinical review.",
        ],
    )