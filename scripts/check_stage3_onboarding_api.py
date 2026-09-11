"""Exercise Stage 3 onboarding through local Auth and PostgREST.

All records are visibly fictional, use temporary users, and are removed before the
script reports success. Credentials and personal-looking payloads are never printed.
"""

from __future__ import annotations

from datetime import datetime, timedelta
import json
import os
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4
from zoneinfo import ZoneInfo

from app.schemas.foundation import SafetySpec
from app.schemas.onboarding import (
    AppointmentInput,
    ApproximateMonthTiming,
    DeliveryDateTiming,
    EstimatedDueDateTiming,
    ManualWeekDayTiming,
    OnboardingDetails,
    PossiblePregnancyTiming,
    PostpartumWeekTiming,
    ReportedFactInput,
    SymptomInput,
)
from app.services.journey import FixedClock
from app.services.onboarding import (
    OnboardingError,
    SupabaseAuthClient,
    SupabaseOnboardingGateway,
    commit_onboarding,
    prepare_onboarding,
)
from scripts.check_stage2_storage_api import LocalSupabase, _expect_success


ROOT = Path(__file__).resolve().parents[1]
INDIA = ZoneInfo("Asia/Kolkata")


def main() -> int:
    local = LocalSupabase()
    marker = uuid4().hex
    email_owner = f"stage3-owner-{marker}@example.invalid"
    email_other = f"stage3-other-{marker}@example.invalid"
    password = f"Nestline-{uuid4().hex}-A1!"
    user_ids: list[str] = []
    workspace_id = None
    workspace_ids: list[str] = []
    checks = 0

    try:
        for email in (email_owner, email_other):
            status, raw = local.request(
                "POST", "/auth/v1/admin/users", key=local.service_key,
                json_body={"email": email, "password": password, "email_confirm": True},
            )
            _expect_success(status, "temporary Stage 3 user creation")
            user_ids.append(local.json(raw)["id"])

        auth = SupabaseAuthClient(local.url, local.anon_key)
        owner_session = auth.sign_in(email_owner, password)
        other_session = auth.sign_in(email_other, password)
        checks += 1

        owner = SupabaseOnboardingGateway(
            local.url, local.anon_key, owner_session.access_token
        )
        workspace_id = owner.create_personal_workspace("Stage 3 fictional API fixture")
        workspace_ids.append(str(workspace_id))
        checks += 1
        if owner.fetch_current_journey_state(workspace_id) is not None:
            raise AssertionError("new personal workspace unexpectedly had a journey state")
        checks += 1

        now = datetime.now(INDIA)
        spec = SafetySpec.model_validate_json(
            (ROOT / "data/safety/rule_spec.yaml").read_text(encoding="utf-8")
        )

        # Manual week/day is exercised by the richer submission below. These
        # five cases complete the persisted matrix for every other UI timing path.
        timing_matrix = [
            (
                "possible",
                PossiblePregnancyTiming(effective_date=now.date()),
                "possible_pregnancy",
                "user_reported_possible_pregnancy",
            ),
            (
                "due-date",
                EstimatedDueDateTiming(
                    effective_date=now.date(),
                    estimated_due_date=now.date() + timedelta(days=112),
                ),
                "pregnancy",
                "user_estimated_due_date",
            ),
            (
                "month",
                ApproximateMonthTiming(
                    effective_date=now.date(),
                    pregnancy_month=5,
                ),
                "pregnancy",
                "approximate_month_range",
            ),
            (
                "delivery",
                DeliveryDateTiming(
                    delivery_date=now.date() - timedelta(days=8),
                ),
                "postpartum",
                "delivery_date",
            ),
            (
                "postpartum-week",
                PostpartumWeekTiming(
                    effective_date=now.date(),
                    postpartum_week=2,
                    postpartum_day=3,
                ),
                "postpartum",
                "postpartum_week",
            ),
        ]
        for label, timing_input, expected_stage, expected_source in timing_matrix:
            matrix_workspace = owner.create_personal_workspace(
                f"Stage 3 timing fixture {label}"
            )
            workspace_ids.append(str(matrix_workspace))
            matrix_draft = prepare_onboarding(
                timing_input, OnboardingDetails(), spec, clock=FixedClock(now)
            )
            matrix_result = commit_onboarding(
                owner,
                matrix_workspace,
                f"stage3-matrix-{label}-{marker}",
                matrix_draft,
                user_confirmed=True,
            )
            matrix_state = owner.fetch_current_journey_state(matrix_workspace)
            if (
                matrix_result.version != 1
                or matrix_state is None
                or matrix_state.stage != expected_stage
                or matrix_state.timing_source != expected_source
            ):
                raise AssertionError(f"{label} timing did not persist correctly")
            if label == "month" and (
                matrix_state.gestational_week is not None
                or matrix_state.approximate_month_min != 5
                or matrix_state.approximate_month_max != 5
            ):
                raise AssertionError("month timing became an invented exact week")
            checks += 1

        details = OnboardingDetails(
            facts=[
                ReportedFactInput(category="allergy", label="Fictional peanut allergy"),
                ReportedFactInput(
                    category="movement_restriction", label="Fictional lifting restriction"
                ),
            ],
            symptoms=[SymptomInput(
                description="Fictional breathing difficulty",
                reported_at=now - timedelta(minutes=1),
            )],
            appointments=[AppointmentInput(
                scheduled_for=now + timedelta(days=7),
                appointment_type="Fictional routine follow-up",
                location="Fictional clinic",
            )],
        )
        draft = prepare_onboarding(
            ManualWeekDayTiming(
                effective_date=now.date(), gestational_week=24, gestational_day=2
            ),
            details, spec, clock=FixedClock(now),
        )
        submission_key = f"stage3-api-{marker}"
        result = commit_onboarding(
            owner, workspace_id, submission_key, draft, user_confirmed=True
        )
        if result.version != 1 or result.idempotent_replay:
            raise AssertionError("first onboarding commit returned the wrong version")
        if not (
            len(result.fact_ids) == 2
            and len(result.symptom_event_ids) == 1
            and len(result.appointment_ids) == 1
        ):
            raise AssertionError("onboarding did not atomically create every detail")
        checks += 1

        replay = commit_onboarding(
            owner, workspace_id, submission_key, draft, user_confirmed=True
        )
        if not replay.idempotent_replay or replay.journey_state_id != result.journey_state_id:
            raise AssertionError("same onboarding submission was not idempotent")
        checks += 1

        persisted = owner.fetch_current_journey_state(workspace_id)
        if persisted is None or persisted.version != 1 or not persisted.user_confirmed:
            raise AssertionError("confirmed journey state was not persisted")
        checks += 1

        # A new token simulates reload/relogin; durable state must still be present.
        relogged = auth.sign_in(email_owner, password)
        relogged_gateway = SupabaseOnboardingGateway(
            local.url, local.anon_key, relogged.access_token
        )
        restored = relogged_gateway.fetch_current_journey_state(workspace_id)
        if restored is None or restored.id != persisted.id:
            raise AssertionError("relogin did not restore the confirmed journey state")
        checks += 1

        outsider = SupabaseOnboardingGateway(
            local.url, local.anon_key, other_session.access_token
        )
        if outsider.fetch_current_journey_state(workspace_id) is not None:
            raise AssertionError("outsider could read the owner's journey state")
        checks += 1
        try:
            commit_onboarding(
                outsider, workspace_id, f"stage3-other-{marker}", draft,
                user_confirmed=True,
            )
        except OnboardingError:
            pass
        else:
            raise AssertionError("outsider could commit into the owner's workspace")
        checks += 1

        conflicting_draft = prepare_onboarding(
            ManualWeekDayTiming(
                effective_date=now.date(), gestational_week=25, gestational_day=2
            ),
            OnboardingDetails(), spec, current_state=restored,
            clock=FixedClock(now),
        )
        if not conflicting_draft.conflict.has_conflict:
            raise AssertionError("disagreeing timing did not create a conflict")
        try:
            commit_onboarding(
                relogged_gateway, workspace_id, f"stage3-conflict-{marker}",
                conflicting_draft, user_confirmed=True,
            )
        except OnboardingError:
            pass
        else:
            raise AssertionError("conflicting timing committed without an explicit choice")
        checks += 1
        conflict_result = commit_onboarding(
            relogged_gateway, workspace_id, f"stage3-conflict-{marker}",
            conflicting_draft, user_confirmed=True,
            accept_conflicting_timing=True,
        )
        if conflict_result.version != 2:
            raise AssertionError("accepted conflict did not create journey version 2")
        checks += 1

        query = (
            f"workspace_id=eq.{quote(str(workspace_id))}"
            "&select=onboarding_submission_key"
        )
        status, raw = local.request(
            "GET", f"/rest/v1/health_facts?{query}", key=local.anon_key,
            token=relogged.access_token,
        )
        _expect_success(status, "owner detail verification")
        if len(local.json(raw)) != 2:
            raise AssertionError("idempotent replay duplicated reported facts")
        checks += 1

    finally:
        for created_workspace_id in reversed(workspace_ids):
            status, _ = local.request(
                "DELETE",
                f"/rest/v1/workspaces?id=eq.{quote(created_workspace_id)}",
                key=local.service_key,
            )
            _expect_success(status, "Stage 3 workspace cleanup")
        for user_id in user_ids:
            status, _ = local.request(
                "DELETE", f"/auth/v1/admin/users/{quote(user_id)}",
                key=local.service_key,
            )
            _expect_success(status, "Stage 3 user cleanup")

    print(json.dumps({"valid": True, "checks": checks, "fixtures_removed": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())