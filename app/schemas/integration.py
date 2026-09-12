"""Cross-stage runtime contracts for accepted Stages 5–8.

These contracts keep fictional fixture execution, authenticated Personal Mode and
controlled evaluation explicit.  They do not create UI or persistence behavior.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal
from uuid import UUID, uuid4

from pydantic import Field, model_validator

from app.schemas.content import Contract, Text
from app.schemas.orchestration import AuthenticatedContextSnapshot, ContextOrigin, RuntimeMode


INTEGRATION_CONTRACT_VERSION = "5-8.1.0"


class RuntimeOperation(StrEnum):
    RETRIEVAL = "retrieval"
    ORCHESTRATION = "orchestration"
    COMPOSITION = "composition"
    PLAN = "plan"


class OnboardingState(StrEnum):
    ABSENT = "absent"
    NEEDS_CONFIRMATION = "needs_confirmation"
    CONFIRMED = "confirmed"


class ProviderAvailability(StrEnum):
    CONFIGURED = "configured"
    FIXTURE_ONLY = "fixture_only"
    UNAVAILABLE = "unavailable"


class RuntimeStopCode(StrEnum):
    READY = "ready"
    ONBOARDING_REQUIRED = "onboarding_required"
    CONFIRMATION_REQUIRED = "confirmation_required"
    CONFLICT_REQUIRES_REVIEW = "conflict_requires_review"
    STALE_STATE = "stale_state"
    EXPLICIT_PLAN_REQUEST_REQUIRED = "explicit_plan_request_required"
    FIXTURE_CONTEXT_FORBIDDEN = "fixture_context_forbidden"
    MODE_SCOPE_MISMATCH = "mode_scope_mismatch"
    PROVIDER_UNAVAILABLE = "provider_unavailable"


class RuntimeGateInput(Contract):
    schema_version: Literal["5-8.1.0"] = INTEGRATION_CONTRACT_VERSION
    request_id: UUID = Field(default_factory=uuid4)
    mode: RuntimeMode
    operation: RuntimeOperation
    query: Text
    session_subject: UUID | None = None
    context: AuthenticatedContextSnapshot | None = None
    context_origin: ContextOrigin | None = None
    onboarding_state: OnboardingState = OnboardingState.ABSENT
    explicit_user_action: bool = False
    provider_availability: ProviderAvailability = ProviderAvailability.UNAVAILABLE
    requires_personalization: bool = False

    @model_validator(mode="after")
    def shape_is_explicit(self):
        if self.context is None and self.context_origin is not None:
            raise ValueError("context origin requires an actual trusted context")
        if self.context is not None and self.context_origin != self.context.context_origin:
            raise ValueError("runtime and snapshot context origins must agree")
        if self.mode == RuntimeMode.PERSONAL and self.session_subject is None:
            raise ValueError("Personal Mode requires an authenticated session subject")
        return self


class RuntimeGateResult(Contract):
    schema_version: Literal["5-8.1.0"] = INTEGRATION_CONTRACT_VERSION
    request_id: UUID
    mode: RuntimeMode
    operation: RuntimeOperation
    stop_code: RuntimeStopCode
    proceed: bool
    retrieval_allowed: bool
    orchestration_allowed: bool
    composition_allowed: bool
    plan_requested: bool
    fixture_context_used: bool
    provider_calls_allowed: bool
    reasons: list[Text] = Field(min_length=1)

    @model_validator(mode="after")
    def permission_flags_agree(self):
        ready = self.stop_code == RuntimeStopCode.READY
        if self.proceed != ready:
            raise ValueError("runtime proceed flag must equal the typed stop code")
        if not ready and any((
            self.retrieval_allowed,
            self.orchestration_allowed,
            self.composition_allowed,
            self.provider_calls_allowed,
        )):
            raise ValueError("a stopped runtime cannot call a downstream stage")
        if self.operation == RuntimeOperation.RETRIEVAL and ready and not self.retrieval_allowed:
            raise ValueError("ready retrieval must enable retrieval")
        if self.plan_requested != (self.operation == RuntimeOperation.PLAN):
            raise ValueError("plan-request flag must equal the requested operation")
        if self.mode == RuntimeMode.PERSONAL and self.fixture_context_used:
            raise ValueError("Personal Mode can never report fixture context")
        return self


class CrossStageBinding(Contract):
    schema_version: Literal["5-8.1.0"] = INTEGRATION_CONTRACT_VERSION
    request_id: UUID
    mode: RuntimeMode
    workspace_id: UUID
    care_episode_id: UUID
    owner_user_id: UUID
    session_subject: UUID
    state_version: int = Field(ge=1)
    normalized_input_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    safety_trace_id: UUID
    trusted_context_origin: ContextOrigin

    @model_validator(mode="after")
    def owner_scope_is_consistent(self):
        if self.owner_user_id != self.session_subject:
            raise ValueError("cross-stage binding must belong to the authenticated owner")
        if self.workspace_id != self.care_episode_id:
            raise ValueError("owner-only v1 binds care episode to workspace")
        if self.mode == RuntimeMode.PERSONAL and self.trusted_context_origin != ContextOrigin.AUTHENTICATED_STORE:
            raise ValueError("Personal Mode cannot bind fictional context")
        return self