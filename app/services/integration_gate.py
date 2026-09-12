"""Fail-closed runtime and identity gate shared by Stages 5–8."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256

from app.schemas.integration import (
    CrossStageBinding,
    OnboardingState,
    ProviderAvailability,
    RuntimeGateInput,
    RuntimeGateResult,
    RuntimeOperation,
    RuntimeStopCode,
)
from app.schemas.orchestration import ContextOrigin, FactState, RuntimeMode
from app.schemas.retrieval import AuthenticatedRetrievalScope, RetrievalResult
from app.schemas.safety import SafetyGateResult
from app.schemas.validation import ValidationRequest
from app.services.safety_gate import normalize_safety_text


class CrossStageBindingError(ValueError):
    """Raised before a mismatched artifact can enter a downstream stage."""


_MATERIAL_PLAN_STATES = {
    "journey", "allergy", "intolerance", "condition", "restriction",
    "clinician_instruction", "medication", "supplement", "symptom",
    "document_fact", "delivery_recovery",
}


def _stopped(value: RuntimeGateInput, code: RuntimeStopCode, reason: str) -> RuntimeGateResult:
    return RuntimeGateResult(
        request_id=value.request_id,
        mode=value.mode,
        operation=value.operation,
        stop_code=code,
        proceed=False,
        retrieval_allowed=False,
        orchestration_allowed=False,
        composition_allowed=False,
        plan_requested=value.operation == RuntimeOperation.PLAN,
        fixture_context_used=False,
        provider_calls_allowed=False,
        reasons=[reason],
    )


def assess_runtime(value: RuntimeGateInput) -> RuntimeGateResult:
    """Return one typed preflight decision without inventing state or fixtures."""

    context = value.context
    if value.mode == RuntimeMode.PERSONAL:
        if value.onboarding_state != OnboardingState.CONFIRMED or context is None:
            return _stopped(value, RuntimeStopCode.ONBOARDING_REQUIRED,
                            "Confirmed onboarding state is required before Personal Mode retrieval or generation.")
        if value.context_origin != ContextOrigin.AUTHENTICATED_STORE:
            return _stopped(value, RuntimeStopCode.FIXTURE_CONTEXT_FORBIDDEN,
                            "Fictional fixture context is forbidden in Personal Mode.")
        if not context.onboarding_confirmed:
            return _stopped(value, RuntimeStopCode.ONBOARDING_REQUIRED,
                            "The authenticated onboarding snapshot is not confirmed.")
        if context.session_subject != value.session_subject:
            return _stopped(value, RuntimeStopCode.MODE_SCOPE_MISMATCH,
                            "The authenticated session does not own this context snapshot.")
    elif value.mode == RuntimeMode.DEMO:
        if context is not None and value.context_origin != ContextOrigin.FICTIONAL_FIXTURE:
            return _stopped(value, RuntimeStopCode.MODE_SCOPE_MISMATCH,
                            "Demo Mode accepts only the controlled fictional fixture snapshot.")

    if value.operation == RuntimeOperation.PLAN and not value.explicit_user_action:
        return _stopped(value, RuntimeStopCode.EXPLICIT_PLAN_REQUEST_REQUIRED,
                        "A plan may run only after an explicit user request.")

    if value.requires_personalization and context is not None:
        material = [item for item in context.items if item.kind.value in _MATERIAL_PLAN_STATES]
        if any(item.state == FactState.CONFLICTING for item in material):
            return _stopped(value, RuntimeStopCode.CONFLICT_REQUIRES_REVIEW,
                            "A relevant personal-context conflict must be reviewed before personalization.")
        if any(item.state == FactState.DOCUMENT_UNCONFIRMED for item in material):
            return _stopped(value, RuntimeStopCode.CONFIRMATION_REQUIRED,
                            "Relevant document-derived information needs confirmation before personalization.")
        if any(item.state == FactState.STALE for item in material):
            return _stopped(value, RuntimeStopCode.STALE_STATE,
                            "Relevant personal context is stale and must be refreshed before personalization.")

    needs_provider = value.operation in {
        RuntimeOperation.ORCHESTRATION, RuntimeOperation.COMPOSITION, RuntimeOperation.PLAN,
    }
    if needs_provider and value.mode == RuntimeMode.PERSONAL:
        if value.provider_availability != ProviderAvailability.CONFIGURED:
            return _stopped(value, RuntimeStopCode.PROVIDER_UNAVAILABLE,
                            "Personal Mode has no explicitly configured live provider; fixture fallback is disabled.")

    fixture_used = value.context_origin == ContextOrigin.FICTIONAL_FIXTURE
    provider_allowed = needs_provider and (
        value.provider_availability == ProviderAvailability.CONFIGURED
        or (value.mode in {RuntimeMode.DEMO, RuntimeMode.EVALUATION}
            and value.provider_availability == ProviderAvailability.FIXTURE_ONLY)
    )
    return RuntimeGateResult(
        request_id=value.request_id,
        mode=value.mode,
        operation=value.operation,
        stop_code=RuntimeStopCode.READY,
        proceed=True,
        retrieval_allowed=True,
        orchestration_allowed=value.operation in {
            RuntimeOperation.ORCHESTRATION, RuntimeOperation.COMPOSITION, RuntimeOperation.PLAN,
        },
        composition_allowed=value.operation in {RuntimeOperation.COMPOSITION, RuntimeOperation.PLAN},
        plan_requested=value.operation == RuntimeOperation.PLAN,
        fixture_context_used=fixture_used,
        provider_calls_allowed=provider_allowed,
        reasons=["The explicit mode, trusted context, trigger and provider boundaries passed."],
    )


def retrieval_scope(value: RuntimeGateInput) -> AuthenticatedRetrievalScope:
    gate = assess_runtime(value)
    if not gate.proceed or value.context is None:
        raise CrossStageBindingError(gate.stop_code.value)
    context = value.context
    return AuthenticatedRetrievalScope(
        workspace_id=context.workspace_id,
        care_episode_id=context.care_episode_id,
        owner_user_id=context.owner_user_id,
        session_subject=context.session_subject,
        state_version=context.state_version,
        authenticated_at=datetime.now(timezone.utc),
    )


def bind_safety(value: RuntimeGateInput, safety: SafetyGateResult) -> CrossStageBinding:
    gate = assess_runtime(value)
    if not gate.proceed or value.context is None:
        raise CrossStageBindingError(gate.stop_code.value)
    expected_hash = sha256(normalize_safety_text(value.query).encode("utf-8")).hexdigest()
    if safety.request_id != value.request_id or safety.trace.normalized_input_sha256 != expected_hash:
        raise CrossStageBindingError("safety_input_mismatch")
    context = value.context
    return CrossStageBinding(
        request_id=value.request_id,
        mode=value.mode,
        workspace_id=context.workspace_id,
        care_episode_id=context.care_episode_id,
        owner_user_id=context.owner_user_id,
        session_subject=context.session_subject,
        state_version=context.state_version,
        normalized_input_sha256=expected_hash,
        safety_trace_id=safety.trace.trace_id,
        trusted_context_origin=context.context_origin,
    )


def verify_retrieval(binding: CrossStageBinding, result: RetrievalResult) -> None:
    packet = result.packet
    scope = packet.trusted_state.scope
    observed = (
        packet.request_id, packet.workspace_id, packet.care_episode_id,
        scope.owner_user_id, scope.session_subject, packet.trusted_state.cache_state_version,
    )
    expected = (
        binding.request_id, binding.workspace_id, binding.care_episode_id,
        binding.owner_user_id, binding.session_subject, binding.state_version,
    )
    if observed != expected:
        raise CrossStageBindingError("retrieval_scope_or_state_mismatch")


def verify_validation(binding: CrossStageBinding, request: ValidationRequest) -> None:
    observed = (
        request.request_id,
        request.context.workspace_id,
        request.context.care_episode_id,
        request.context.owner_user_id,
        request.context.session_subject,
        request.context.state_version,
        request.safety_result.trace.trace_id,
    )
    expected = (
        binding.request_id,
        binding.workspace_id,
        binding.care_episode_id,
        binding.owner_user_id,
        binding.session_subject,
        binding.state_version,
        binding.safety_trace_id,
    )
    if observed != expected:
        raise CrossStageBindingError("validation_scope_state_or_safety_mismatch")