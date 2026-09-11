"""Provider-neutral, bounded Stage 7 structured-output adapter.

The shipped adapter is deterministic and offline.  It does not pretend to be a
model benchmark or a production model.  A paid provider can implement the same
protocol only after separate authorization and evaluation.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from time import perf_counter
from typing import Any, Protocol

from app.schemas.orchestration import AgentBudget, AgentName


class ProviderFailure(RuntimeError):
    """Raised when an adapter cannot return a bounded structured result."""


@dataclass(frozen=True)
class ProviderResponse:
    payload: dict[str, Any]
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
    latency_ms: float


class StructuredProvider(Protocol):
    provider_id: str
    model_id: str

    def complete(
        self,
        *,
        agent: AgentName,
        instructions: list[str],
        draft: dict[str, Any],
        budget: AgentBudget,
    ) -> ProviderResponse: ...


class DeterministicFixtureProvider:
    """Offline test adapter that echoes an already bounded synthetic draft."""

    provider_id = "deterministic_fixture"
    model_id = "stage7-offline-v1"

    def complete(
        self,
        *,
        agent: AgentName,
        instructions: list[str],
        draft: dict[str, Any],
        budget: AgentBudget,
    ) -> ProviderResponse:
        started = perf_counter()
        input_tokens = min(budget.max_tokens, max(1, sum(len(v.split()) for v in instructions)))
        output_tokens = min(budget.max_tokens, max(1, len(str(draft).split())))
        return ProviderResponse(
            payload=draft,
            provider=self.provider_id,
            model=self.model_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=0.0,
            latency_ms=(perf_counter() - started) * 1000,
        )


class ScriptedTestProvider:
    """Test double for invalid output, timeout and provider-failure boundaries."""

    provider_id = "scripted_test_fixture"
    model_id = "stage7-scripted-v1"

    def __init__(
        self,
        payloads: list[dict[str, Any] | Exception],
        *,
        latency_ms: float = 0.0,
    ) -> None:
        self._payloads = deque(payloads)
        self.latency_ms = latency_ms
        self.calls = 0

    def complete(
        self,
        *,
        agent: AgentName,
        instructions: list[str],
        draft: dict[str, Any],
        budget: AgentBudget,
    ) -> ProviderResponse:
        self.calls += 1
        if self.latency_ms > budget.timeout_ms:
            raise TimeoutError("provider exceeded the worker timeout")
        if not self._payloads:
            raise ProviderFailure("scripted provider has no response")
        value = self._payloads.popleft()
        if isinstance(value, Exception):
            raise value
        return ProviderResponse(
            payload=value,
            provider=self.provider_id,
            model=self.model_id,
            input_tokens=min(budget.max_tokens, 5),
            output_tokens=min(budget.max_tokens, max(1, len(str(value).split()))),
            estimated_cost_usd=0.0,
            latency_ms=self.latency_ms,
        )
