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
from typing import Callable, Protocol

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
NEGATION_TERMS = {"no", "not", "never", "without", "avoid", "unsafe"}

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
        polarity_mismatch = bool(claim_tokens & NEGATION_TERMS) != bool(span_tokens & NEGATION_TERMS)
        if polarity_mismatch and shared:
            support = SemanticSupport.IRRELEVANT
            reason = "The claim and cited span use opposing negative/positive wording."
        elif not shared:
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


class ConfiguredSemanticSupportEvaluator:
    """Explicit fail-closed adapter for a separately authorized semantic assessor.

    This class performs no network call and selects no model.  A caller must inject
    an authorized bounded assessor.  The returned identity is checked so a fixture
    or different provider cannot masquerade as the configured evaluator.
    """

    fixture_only = False

    def __init__(
        self,
        *,
        evaluator_id: str,
        model_id: str,
        assessor: Callable[[Claim, EligibleEvidenceSpan], SemanticAssessment] | None = None,
    ) -> None:
        if not evaluator_id.strip() or not model_id.strip():
            raise ValueError("semantic evaluator and model identities are required")
        if "fixture" in evaluator_id.casefold() or "fixture" in model_id.casefold():
            raise ValueError("fixture identities cannot claim configured-evaluator status")
        self.evaluator_id = evaluator_id
        self.model_id = model_id
        self._assessor = assessor

    def assess(self, claim: Claim, evidence: EligibleEvidenceSpan) -> SemanticAssessment:
        if self._assessor is None:
            raise SemanticEvaluatorUnavailable("configured semantic assessor is unavailable")
        try:
            assessment = self._assessor(claim, evidence)
        except TimeoutError:
            raise
        except SemanticEvaluatorUnavailable:
            raise
        except Exception as exc:
            raise SemanticEvaluatorUnavailable("configured semantic assessor failed") from exc
        if assessment.claim_id != claim.claim_id or assessment.evidence_id != evidence.evidence_id:
            raise SemanticEvaluatorUnavailable("semantic assessment identity mismatch")
        if assessment.evaluator != self.evaluator_id or assessment.model != self.model_id:
            raise SemanticEvaluatorUnavailable("semantic evaluator identity mismatch")
        return assessment
