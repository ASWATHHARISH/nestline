"""Provider-neutral semantic-support assessment for Stage 8.

The deterministic evaluator is deliberately conservative and exists so CI can
exercise the support boundary without a paid model.  It is not a clinical or
language-quality benchmark.  A future bounded evaluator must implement the same
interface and uncertain/unavailable outcomes remain blocking.
"""

from __future__ import annotations

from collections import deque
import re
from time import perf_counter
from typing import Protocol

from app.schemas.validation import (
    Claim,
    EligibleEvidenceSpan,
    SemanticAssessment,
    SemanticSupport,
)


STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "for", "from", "in",
    "is", "it", "of", "on", "or", "that", "the", "this", "to", "with",
    "your", "you",
}
STRENGTHENING_TERMS = {
    "always", "certain", "certainly", "cure", "guarantee", "guaranteed",
    "must", "never", "proves", "safe", "will",
}


def _tokens(value: str) -> set[str]:
    return {
        token for token in re.findall(r"[a-z0-9]+", value.casefold())
        if token not in STOP_WORDS
    }


class SemanticEvaluatorUnavailable(RuntimeError):
    pass


class SemanticSupportEvaluator(Protocol):
    evaluator_id: str
    model_id: str

    def assess(self, claim: Claim, evidence: EligibleEvidenceSpan) -> SemanticAssessment: ...


class DeterministicSemanticSupportEvaluator:
    """Conservative lexical support evaluator for controlled fixtures only."""

    evaluator_id = "deterministic_fixture_support"
    model_id = "stage8-lexical-v1"

    def assess(self, claim: Claim, evidence: EligibleEvidenceSpan) -> SemanticAssessment:
        started = perf_counter()
        claim_tokens = _tokens(claim.text)
        span_tokens = _tokens(evidence.exact_span)
        shared = claim_tokens & span_tokens
        coverage = len(shared) / max(1, len(claim_tokens))
        unsupported_strength = (claim_tokens & STRENGTHENING_TERMS) - span_tokens
        if not shared:
            support = SemanticSupport.IRRELEVANT
            reason = "No material claim term appears in the cited span."
        elif unsupported_strength:
            support = SemanticSupport.WEAKER
            reason = "The claim is stronger than the cited span."
        elif coverage >= 0.75:
            support = SemanticSupport.SUPPORTED
            reason = "The controlled span covers the material claim terms."
        elif coverage >= 0.45:
            support = SemanticSupport.PARTIAL
            reason = "The span covers only part of the material claim."
        else:
            support = SemanticSupport.IRRELEVANT
            reason = "Term overlap is too weak to establish support."
        return SemanticAssessment(
            claim_id=claim.claim_id,
            evidence_id=evidence.evidence_id,
            support=support,
            explanation=reason,
            evaluator=self.evaluator_id,
            model=self.model_id,
            input_tokens=len(claim.text.split()) + len(evidence.exact_span.split()),
            output_tokens=len(reason.split()),
            estimated_cost_usd=0.0,
            latency_ms=(perf_counter() - started) * 1000,
        )


class ScriptedSemanticSupportEvaluator:
    """Deterministic test double for support, uncertainty and failure paths."""

    evaluator_id = "scripted_fixture_support"
    model_id = "stage8-scripted-v1"

    def __init__(self, outcomes: list[SemanticSupport | Exception]) -> None:
        self._outcomes = deque(outcomes)
        self.calls = 0

    def assess(self, claim: Claim, evidence: EligibleEvidenceSpan) -> SemanticAssessment:
        self.calls += 1
        if not self._outcomes:
            raise SemanticEvaluatorUnavailable("no scripted semantic result")
        outcome = self._outcomes.popleft()
        if isinstance(outcome, Exception):
            raise outcome
        return SemanticAssessment(
            claim_id=claim.claim_id,
            evidence_id=evidence.evidence_id,
            support=outcome,
            explanation=f"Scripted controlled result: {outcome.value}.",
            evaluator=self.evaluator_id,
            model=self.model_id,
            input_tokens=1,
            output_tokens=1,
            estimated_cost_usd=0.0,
            latency_ms=0.0,
        )
