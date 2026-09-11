"""Functional Stage 3 Streamlit onboarding flow."""

from __future__ import annotations

from datetime import date, datetime, time
from uuid import uuid4
from zoneinfo import ZoneInfo

import streamlit as st

from app.pages_and_components.documents import render_document_panel
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
from app.services.journey import JourneyResolutionError, JourneyResolver, SystemClock
from app.services.onboarding import (
    AuthSession,
    OnboardingError,
    SupabaseAuthClient,
    SupabaseOnboardingGateway,
    commit_onboarding,
    prepare_onboarding,
)


INDIA = ZoneInfo("Asia/Kolkata")


def _lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


def _auth_panel(auth: SupabaseAuthClient) -> AuthSession | None:
    session = st.session_state.get("auth_session")
    if session is not None:
        if st.button("Sign out"):
            for key in ["auth_session", "workspace_id", "onboarding_draft"]:
                st.session_state.pop(key, None)
            st.rerun()
        return session

    sign_in, sign_up = st.tabs(["Sign in", "Create account"])
    with sign_in:
        with st.form("sign_in"):
            email = st.text_input("Email", key="sign_in_email")
            password = st.text_input("Password", type="password", key="sign_in_password")
            submitted = st.form_submit_button("Sign in", type="primary")
        if submitted:
            try:
                st.session_state.auth_session = auth.sign_in(email, password)
                st.rerun()
            except OnboardingError as exc:
                st.error(str(exc))
    with sign_up:
        st.caption("Use fictional information while this public-demo build is under review.")
        with st.form("sign_up"):
            email = st.text_input("Email", key="sign_up_email")
            password = st.text_input("Password", type="password", key="sign_up_password")
            submitted = st.form_submit_button("Create account")
        if submitted:
            try:
                session = auth.sign_up(email, password)
                if session is None:
                    st.info("Account created. Complete email confirmation, then sign in.")
                else:
                    st.session_state.auth_session = session
                    st.rerun()
            except OnboardingError as exc:
                st.error(str(exc))
    return None


def _workspace_panel(gateway: SupabaseOnboardingGateway):
    workspaces = gateway.list_workspaces()
    selected = st.session_state.get("workspace_id")
    if selected and any(row["id"] == selected for row in workspaces):
        return next(row for row in workspaces if row["id"] == selected)

    if workspaces:
        labels = {
            row["id"]: f"{row['display_name']} · {'Fictional demo' if row['mode'] == 'fictional_demo' else 'Personal'}"
            for row in workspaces
        }
        workspace_id = st.selectbox(
            "Choose a workspace", list(labels), format_func=labels.get
        )
        if st.button("Open workspace", type="primary"):
            st.session_state.workspace_id = workspace_id
            st.rerun()

    st.subheader("Start a workspace")
    mode = st.radio(
        "Workspace type",
        ["Personal empty workspace", "Fictional demo mode"],
        help="Personal starts empty. Demo mode contains visibly fictional data.",
    )
    display_name = st.text_input(
        "Workspace name",
        value="My Nestline journey" if mode.startswith("Personal") else "Maya · fictional demo",
    )
    if st.button("Create workspace"):
        try:
            if mode.startswith("Personal"):
                workspace_id = gateway.create_personal_workspace(display_name)
            else:
                session_key = st.session_state.setdefault(
                    "demo_session_key", f"streamlit-{uuid4()}"
                )
                workspace_id = gateway.create_demo_workspace(session_key, display_name)
            st.session_state.workspace_id = str(workspace_id)
            st.rerun()
        except OnboardingError as exc:
            st.error(str(exc))
    return None


def _timing_inputs(stage_choice: str, today: date):
    if stage_choice == "I may be pregnant":
        return PossiblePregnancyTiming(effective_date=today)
    if stage_choice == "I am pregnant":
        method = st.selectbox(
            "What timing information do you have?",
            [
                "Estimated due date (recommended)",
                "Current gestational week and day",
                "Approximate pregnancy month",
            ],
        )
        if method.startswith("Estimated"):
            due_date = st.date_input("Estimated due date", value=today)
            return EstimatedDueDateTiming(
                effective_date=today,
                estimated_due_date=due_date,
                provenance="user_estimated_due_date",
            )
        if method.startswith("Current"):
            effective_date = st.date_input("This week/day was correct on", value=today)
            week = st.number_input("Gestational week", 1, 42, 24)
            day = st.number_input("Additional day", 0, 6, 0)
            return ManualWeekDayTiming(
                effective_date=effective_date,
                gestational_week=int(week),
                gestational_day=int(day),
            )
        effective_date = st.date_input("This approximate month was correct on", value=today)
        month = st.number_input("Approximate pregnancy month", 1, 9, 5)
        return ApproximateMonthTiming(
            effective_date=effective_date,
            pregnancy_month=int(month),
        )

    method = st.selectbox(
        "What timing information do you have?",
        ["Delivery date (recommended)", "Current postpartum week and day"],
    )
    if method.startswith("Delivery"):
        return DeliveryDateTiming(
            delivery_date=st.date_input("Delivery date", value=today)
        )
    effective_date = st.date_input("This week/day was correct on", value=today)
    week = st.number_input("Postpartum week", 1, 12, 1)
    day = st.number_input("Additional day", 0, 6, 0)
    return PostpartumWeekTiming(
        effective_date=effective_date,
        postpartum_week=int(week),
        postpartum_day=int(day),
    )


def _reported_facts(allergies: str, history: str, diet: str, movement: str):
    facts = []
    for category, text in [
        ("allergy", allergies),
        ("medical_history", history),
        ("dietary_restriction", diet),
        ("movement_restriction", movement),
    ]:
        facts.extend(ReportedFactInput(category=category, label=value) for value in _lines(text))
    return facts


def _render_personal_onboarding(
    gateway: SupabaseOnboardingGateway,
    workspace_id,
    safety_spec: SafetySpec,
) -> None:
    clock = SystemClock()
    current = gateway.fetch_current_journey_state(workspace_id)
    if current is not None:
        try:
            displayed = JourneyResolver(clock).refresh_stored_state(current)
            st.success(f"Saved timing: {displayed.display_label} · version {current.version}")
            if current.has_dating_conflict:
                st.warning("This saved timing has recorded dating conflict provenance.")
        except JourneyResolutionError:
            st.warning("Saved timing has crossed the supported range. Please confirm an updated state.")

    st.subheader("Confirm your journey")
    st.caption("Timing is calculated deterministically. A language model is never used here.")
    with st.form("calculate_onboarding"):
        today = datetime.now(INDIA).date()
        stage_choice = st.radio(
            "Where are you now?",
            ["I may be pregnant", "I am pregnant", "I am postpartum"],
        )
        timing = _timing_inputs(stage_choice, today)
        st.markdown("#### Optional information")
        st.caption("Enter one item per line. During development, use fictional information only.")
        allergies = st.text_area("Allergies")
        history = st.text_area("Medical history or conditions")
        diet = st.text_area("Dietary restrictions")
        movement = st.text_area("Movement restrictions")
        symptom = st.text_area("Current symptom to record")
        has_appointment = st.checkbox("I have a next appointment")
        appointment_date = st.date_input("Appointment date", value=today)
        appointment_time = st.time_input("Appointment time", value=time(10, 0))
        appointment_type = st.text_input("Appointment type", value="Routine follow-up")
        appointment_location = st.text_input("Appointment location")
        calculate = st.form_submit_button("Calculate and review", type="primary")

    if calculate:
        now = datetime.now(INDIA)
        symptoms = (
            [SymptomInput(description=symptom, reported_at=now)] if symptom.strip() else []
        )
        appointments = []
        if has_appointment:
            appointments.append(AppointmentInput(
                scheduled_for=datetime.combine(
                    appointment_date, appointment_time, tzinfo=INDIA
                ),
                appointment_type=appointment_type,
                location=appointment_location,
            ))
        try:
            details = OnboardingDetails(
                facts=_reported_facts(allergies, history, diet, movement),
                symptoms=symptoms,
                appointments=appointments,
            )
            st.session_state.onboarding_draft = prepare_onboarding(
                timing, details, safety_spec, current_state=current, clock=clock
            )
        except (ValueError, OnboardingError) as exc:
            st.error(str(exc))

    draft = st.session_state.get("onboarding_draft")
    if draft is None:
        return

    st.markdown("#### Review before saving")
    st.metric("Calculated journey", draft.resolution.display_label)
    for limitation in draft.resolution.limitations:
        st.caption(limitation)
    if draft.conflict.has_conflict:
        st.error(
            f"Timing conflict: saved value is “{draft.conflict.current_display}”; "
            f"new value is “{draft.conflict.proposed_display}”. Nestline will not choose for you."
        )
    if draft.conflict.commit_blocked:
        st.error(
            "This change would move the same care episode backwards. Keep the "
            "current state, or start a new workspace for a new pregnancy."
        )
        st.info("Nothing from this draft can be saved in the current workspace.")
        return

    for symptom_result in draft.prepared_symptoms:
        if symptom_result.safety_route == "urgent":
            st.error(symptom_result.safety_message)
        else:
            st.warning(symptom_result.safety_message)
        if symptom_result.safety_evaluation_only:
            st.caption("Safety rule draft awaiting specialist clinical and India review.")

    with st.form("confirm_onboarding"):
        confirmed = st.checkbox("I confirm that the timing and optional details shown are correct.")
        accept_conflict = False
        if draft.conflict.requires_user_choice:
            accept_conflict = st.checkbox(
                "I choose the new timing and understand the earlier value remains in history."
            )
        save = st.form_submit_button("Save confirmed information", type="primary")
    if save:
        try:
            result = commit_onboarding(
                gateway,
                workspace_id,
                f"streamlit-{uuid4()}",
                draft,
                user_confirmed=confirmed,
                accept_conflicting_timing=accept_conflict,
            )
            st.session_state.pop("onboarding_draft", None)
            st.success(f"Saved journey version {result.version}.")
            st.rerun()
        except OnboardingError as exc:
            st.error(str(exc))



def render_onboarding(
    project_url: str,
    publishable_key: str,
    safety_spec: SafetySpec,
) -> None:
    auth = SupabaseAuthClient(project_url, publishable_key)
    session = _auth_panel(auth)
    if session is None:
        return
    gateway = SupabaseOnboardingGateway(
        project_url, publishable_key, session.access_token
    )
    workspace = _workspace_panel(gateway)
    if workspace is None:
        return
    workspace_id = workspace["id"]
    if workspace["mode"] == "fictional_demo":
        state = gateway.fetch_current_journey_state(workspace_id)
        st.success("Fictional Maya demo workspace is ready.")
        if state:
            st.metric("Seeded journey", f"Pregnancy week {state.gestational_week}, day {state.gestational_day}")
        st.caption("This workspace is isolated and resettable for a repeatable demo.")
        render_document_panel(
            project_url, publishable_key, session.access_token, workspace
        )
        return
    _render_personal_onboarding(gateway, workspace_id, safety_spec)
    render_document_panel(
        project_url, publishable_key, session.access_token, workspace
    )