"""Stage 3 onboarding preparation, confirmation, and Supabase boundary."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import json
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from uuid import UUID

from app.schemas.foundation import SafetySpec
from app.schemas.onboarding import (
    ApproximateMonthTiming,
    DeliveryDateTiming,
    EstimatedDueDateTiming,
    JourneyTimingInput,
    ManualWeekDayTiming,
    OnboardingCommitResult,
    OnboardingDetails,
    OnboardingDraft,
    PostpartumWeekTiming,
    PreparedSymptom,
)
from app.schemas.storage import JourneyState
from app.services.journey import Clock, JourneyResolver, SystemClock
from app.services.safety_gate import SafetyGate, evaluate_onboarding_symptom


class OnboardingError(RuntimeError):
    """Onboarding stopped without applying a partial state change."""


class OnboardingGateway(Protocol):
    def fetch_current_journey_state(self, workspace_id: UUID) -> JourneyState | None: ...

    def complete_onboarding(self, payload: dict[str, Any]) -> OnboardingCommitResult: ...


@dataclass(frozen=True)
class AuthSession:
    user_id: UUID
    access_token: str
    refresh_token: str
    expires_in: int


@dataclass
class SupabaseAuthClient:
    project_url: str
    publishable_key: str
    timeout_seconds: float = 20.0

    def _request(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        request = Request(
            f"{self.project_url.rstrip('/')}{path}",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "apikey": self.publishable_key,
                "Content-Type": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read()
        except HTTPError as exc:
            raise OnboardingError(f"Authentication failed with HTTP {exc.code}.") from exc
        except URLError as exc:
            raise OnboardingError("Authentication service could not be reached.") from exc
        value = json.loads(raw) if raw else {}
        if not isinstance(value, dict):
            raise OnboardingError("Authentication service returned an invalid response.")
        return value

    def sign_in(self, email: str, password: str) -> AuthSession:
        value = self._request(
            "/auth/v1/token?grant_type=password",
            {"email": email.strip(), "password": password},
        )
        try:
            return AuthSession(
                user_id=UUID(value["user"]["id"]),
                access_token=value["access_token"],
                refresh_token=value["refresh_token"],
                expires_in=int(value["expires_in"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise OnboardingError("Sign-in response did not contain a usable session.") from exc

    def sign_up(self, email: str, password: str) -> AuthSession | None:
        value = self._request(
            "/auth/v1/signup",
            {"email": email.strip(), "password": password},
        )
        if not value.get("access_token"):
            return None
        try:
            return AuthSession(
                user_id=UUID(value["user"]["id"]),
                access_token=value["access_token"],
                refresh_token=value["refresh_token"],
                expires_in=int(value["expires_in"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise OnboardingError("Sign-up response did not contain a usable session.") from exc


@dataclass
class SupabaseOnboardingGateway:
    """User-token REST adapter. RLS derives the owner from this session token."""

    project_url: str
    publishable_key: str
    user_access_token: str
    timeout_seconds: float = 20.0

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        request = Request(
            f"{self.project_url.rstrip('/')}{path}",
            data=(json.dumps(payload).encode("utf-8") if payload is not None else None),
            method=method,
            headers={
                "apikey": self.publishable_key,
                "Authorization": f"Bearer {self.user_access_token}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read()
        except HTTPError as exc:
            raise OnboardingError(
                f"Supabase onboarding request failed with HTTP {exc.code}."
            ) from exc
        except URLError as exc:
            raise OnboardingError("Supabase onboarding service could not be reached.") from exc
        return json.loads(raw) if raw else None

    def list_workspaces(self) -> list[dict[str, Any]]:
        query = urlencode({
            "select": "id,mode,display_name,demo_session_key,demo_seed_version,updated_at",
            "order": "created_at.asc",
        })
        value = self._request("GET", f"/rest/v1/workspaces?{query}")
        if not isinstance(value, list):
            raise OnboardingError("Supabase returned an invalid workspace list.")
        return value

    def create_personal_workspace(self, display_name: str) -> UUID:
        value = self._request(
            "POST",
            "/rest/v1/rpc/create_workspace",
            {
                "requested_mode": "personal_empty",
                "requested_display_name": display_name.strip(),
            },
        )
        try:
            return UUID(value)
        except (TypeError, ValueError) as exc:
            raise OnboardingError("Supabase returned an invalid workspace ID.") from exc

    def create_demo_workspace(self, session_key: str, display_name: str) -> UUID:
        value = self._request(
            "POST",
            "/rest/v1/rpc/create_demo_workspace",
            {
                "requested_session_key": session_key,
                "requested_display_name": display_name.strip(),
                "requested_seed_version": "maya-v1",
            },
        )
        try:
            return UUID(value)
        except (TypeError, ValueError) as exc:
            raise OnboardingError("Supabase returned an invalid demo workspace ID.") from exc

    def fetch_current_journey_state(self, workspace_id: UUID) -> JourneyState | None:
        query = urlencode({
            "workspace_id": f"eq.{workspace_id}",
            "is_current": "eq.true",
            "select": "*",
            "limit": "1",
        })
        value = self._request("GET", f"/rest/v1/journey_states?{query}")
        if not isinstance(value, list):
            raise OnboardingError("Supabase returned an invalid journey response.")
        if not value:
            return None
        return JourneyState.model_validate_json(json.dumps(value[0]))

    def complete_onboarding(self, payload: dict[str, Any]) -> OnboardingCommitResult:
        value = self._request(
            "POST", "/rest/v1/rpc/complete_onboarding", payload
        )
        return OnboardingCommitResult.model_validate_json(json.dumps(value))


def _prepare_symptom(spec: SafetySpec, description: str, reported_at: datetime) -> PreparedSymptom:
    gate = SafetyGate(
        spec,
        mode="evaluation_only" if spec.status == "draft" else "public_runtime",
    )
    result = evaluate_onboarding_symptom(gate, description)
    return PreparedSymptom(
        description=description,
        reported_at=reported_at,
        safety_route=result.route,
        matched_rule_ids=result.trace.matched_rule_ids,
        safety_message=result.fixed_message.text,
        safety_spec_version=spec.version,
        safety_evaluation_only=result.evaluation_only,
        safety_trace_id=result.trace.trace_id,
    )


def _legacy_storage_route(route: str) -> str:
    """The sole boundary from canonical Stage 6 routes to the Stage 2 DB enum."""

    return {
        "urgent": "urgent",
        "needs_clarification": "clarify",
        "non_urgent": "no_match",
    }[route]


def prepare_onboarding(
    timing: JourneyTimingInput,
    details: OnboardingDetails,
    safety_spec: SafetySpec,
    *,
    current_state: JourneyState | None = None,
    clock: Clock | None = None,
) -> OnboardingDraft:
    active_clock = clock or SystemClock()
    resolver = JourneyResolver(active_clock)
    resolution = resolver.resolve(timing)
    conflict = resolver.compare_with_current(current_state, resolution)
    now = active_clock.now()
    if now.tzinfo is None:
        raise OnboardingError("onboarding clock must be timezone-aware")

    prepared_symptoms = []
    for symptom in details.symptoms:
        if symptom.reported_at.tzinfo is None:
            raise OnboardingError("symptom time must include a timezone")
        if symptom.reported_at > now:
            raise OnboardingError("symptom time cannot be in the future")
        prepared_symptoms.append(
            _prepare_symptom(safety_spec, symptom.description, symptom.reported_at)
        )
    for appointment in details.appointments:
        if appointment.scheduled_for.tzinfo is None:
            raise OnboardingError("appointment time must include a timezone")
        if appointment.scheduled_for <= now:
            raise OnboardingError("next appointment must be in the future")

    return OnboardingDraft(
        timing=timing,
        resolution=resolution,
        conflict=conflict,
        details=details,
        prepared_symptoms=prepared_symptoms,
    )


def _journey_storage_values(draft: OnboardingDraft) -> dict[str, Any]:
    timing = draft.timing
    resolved = draft.resolution
    values = {
        "stage": resolved.stage,
        "timing_source": resolved.timing_source,
        "gestational_week": resolved.gestational_week,
        "gestational_day": resolved.gestational_day,
        "postpartum_week": resolved.postpartum_week,
        "postpartum_day": resolved.postpartum_day,
        "estimated_due_date": resolved.estimated_due_date,
        "delivery_date": resolved.delivery_date,
        "approximate_month_min": resolved.approximate_month_min,
        "approximate_month_max": resolved.approximate_month_max,
        "effective_date": resolved.effective_date,
        "calculation_date": resolved.calculation_date,
        "derived_from_fact_ids": resolved.source_fact_ids,
    }
    # Week/day inputs are observations at their effective date. Store that source
    # value; the resolver rolls it forward again whenever the state is loaded.
    if isinstance(timing, ManualWeekDayTiming):
        values["gestational_week"] = timing.gestational_week
        values["gestational_day"] = timing.gestational_day
    elif isinstance(timing, PostpartumWeekTiming):
        values["postpartum_week"] = timing.postpartum_week
        values["postpartum_day"] = timing.postpartum_day
    elif isinstance(timing, ApproximateMonthTiming):
        values["approximate_month_min"] = timing.pregnancy_month
        values["approximate_month_max"] = timing.pregnancy_month
    elif isinstance(timing, DeliveryDateTiming):
        values["effective_date"] = timing.delivery_date
    elif isinstance(timing, EstimatedDueDateTiming):
        values["effective_date"] = timing.effective_date
    return values


def _fact_payload(details: OnboardingDetails) -> list[dict[str, Any]]:
    result = []
    for fact in details.facts:
        if fact.category in {"movement_restriction", "other_restriction"}:
            fact_type = "other"
            value = {"label": fact.label, "category": fact.category}
        else:
            fact_type = fact.category
            value = {"label": fact.label}
        result.append({"fact_type": fact_type, "value": value})
    return result


def build_onboarding_payload(
    workspace_id: UUID,
    submission_key: str,
    draft: OnboardingDraft,
) -> dict[str, Any]:
    if not 16 <= len(submission_key.strip()) <= 128:
        raise OnboardingError("submission key must contain 16 to 128 characters")
    body = {
        "requested_workspace_id": str(workspace_id),
        "expected_current_version": draft.conflict.current_version,
        "requested_submission_key": submission_key.strip(),
        "requested_journey": _journey_storage_values(draft),
        "requested_has_dating_conflict": draft.conflict.has_conflict,
        "requested_conflicts_with_state_id": (
            str(draft.conflict.current_state_id)
            if draft.conflict.has_conflict and draft.conflict.current_state_id
            else None
        ),
        "requested_dating_difference_days": draft.conflict.difference_days,
        "requested_facts": _fact_payload(draft.details),
        "requested_symptoms": [
            {
                "description": item.description,
                "reported_at": item.reported_at,
                "safety_route": _legacy_storage_route(item.safety_route),
                "matched_rule_ids": item.matched_rule_ids,
                "safety_spec_version": item.safety_spec_version,
                "safety_evaluation_only": item.safety_evaluation_only,
            }
            for item in draft.prepared_symptoms
        ],
        "requested_appointments": [
            {
                "scheduled_for": item.scheduled_for,
                "appointment_type": item.appointment_type,
                "location": item.location,
            }
            for item in draft.details.appointments
        ],
    }
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), default=str)
    body["requested_payload_sha256"] = sha256(canonical.encode("utf-8")).hexdigest()
    return json.loads(json.dumps(body, default=str))


def commit_onboarding(
    gateway: OnboardingGateway,
    workspace_id: UUID,
    submission_key: str,
    draft: OnboardingDraft,
    *,
    user_confirmed: bool,
    accept_conflicting_timing: bool = False,
) -> OnboardingCommitResult:
    if not user_confirmed:
        raise OnboardingError("explicit user confirmation is required before saving")
    if draft.conflict.commit_blocked:
        raise OnboardingError(
            "this timing would move the care episode backwards; keep the current "
            "state or start a new workspace for a new pregnancy"
        )
    if draft.conflict.requires_user_choice and not accept_conflicting_timing:
        raise OnboardingError("conflicting timing requires an explicit user choice")
    return gateway.complete_onboarding(
        build_onboarding_payload(workspace_id, submission_key, draft)
    )