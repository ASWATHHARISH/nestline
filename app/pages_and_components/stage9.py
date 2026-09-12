"""Separated Streamlit views for the Stage 9 local product experience."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import streamlit as st

from app.schemas.orchestration import Weekday
from app.schemas.product_experience import PlanDisplayState, ProductPage
from app.services.product_experience import (
    ProductExecution,
    authentic_failed_trace,
    demo_documents,
    demo_weekly_home,
    load_evaluator_metrics,
    reset_demo_state_keys,
    run_compass,
    simulated_review,
)


ROOT = Path(__file__).resolve().parents[2]
PAGES = [page.value for page in ProductPage]
WEEKDAYS = [day.value for day in Weekday]


def _css() -> None:
    st.markdown(
        """
        <style>
        :root { --nest-ink:#20352f; --nest-mint:#dff1e9; --nest-rose:#f8e9e8; --nest-gold:#f4e8c8; }
        .stApp { color: var(--nest-ink); }
        .block-container { max-width: 1180px; padding-top: 1.2rem; }
        .nest-banner { padding:.8rem 1rem; border:2px solid #6c837b; border-radius:14px; background:#f6faf8; margin:.4rem 0 1rem; }
        .nest-demo { padding:.65rem 1rem; border-left:6px solid #8a5b3d; background:#fff4e8; margin-bottom:1rem; }
        .nest-hero { padding:1.2rem; border-radius:18px; background:linear-gradient(135deg,var(--nest-mint),#fff); border:1px solid #9bb8ad; }
        .nest-status { display:inline-block; padding:.18rem .55rem; margin:.15rem .25rem .15rem 0; border-radius:99px; border:1px solid #6c837b; font-weight:650; }
        .nest-evidence { border-left:4px solid #586e75; padding:.4rem .8rem; background:#f6f7f7; overflow-wrap:anywhere; }
        .nest-danger { border:3px solid #9c2d2d; background:#fff0f0; padding:1rem; border-radius:12px; }
        div[data-testid="stButton"] button:focus-visible,
        input:focus-visible, textarea:focus-visible, a:focus-visible { outline:4px solid #1d6a78 !important; outline-offset:2px; }
        button, [role="button"] { min-height:44px; }
        @media (max-width: 640px) {
          .block-container { padding-left:.8rem; padding-right:.8rem; }
          .nest-hero { padding:.8rem; }
          div[data-testid="stHorizontalBlock"] { flex-wrap:wrap; }
          div[data-testid="stHorizontalBlock"] > div { min-width:100%; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _boundary_banner() -> None:
    st.markdown(
        """<div class="nest-banner"><strong>Educational and organizational prototype.</strong>
        Nestline is not a doctor, diagnostic tool, prescriber, medical device, or emergency service.
        This local demo uses fictional information only.</div>""",
        unsafe_allow_html=True,
    )


def _demo_banner() -> None:
    st.markdown(
        """<div class="nest-demo"><strong>Demo Mode · fictional data.</strong>
        Do not enter or upload real medical or personal information. Controlled fixtures are not public clinical guidance.</div>""",
        unsafe_allow_html=True,
    )


def _navigate(page: ProductPage) -> None:
    st.session_state.stage9_demo_page = page.value
    st.query_params["page"] = page.value


def _emergency_access() -> None:
    with st.expander("Need immediate safety help? Open this now", expanded=False):
        st.error(
            "If you may be in immediate danger, contact local emergency services now. "
            "For a symptom message, open Compass; deterministic safety routing runs before any ordinary response."
        )
        if st.button("Open Compass safety route", key="stage9_demo_emergency_open"):
            _navigate(ProductPage.COMPASS)
            st.rerun()


def _go(page: ProductPage, label: str, key: str) -> None:
    if st.button(label, key=key, width="stretch"):
        _navigate(page)
        st.rerun()


def _home() -> None:
    plan = st.session_state.get("stage9_demo_plan_execution")
    home = demo_weekly_home(plan_state=PlanDisplayState.DRAFT if plan else PlanDisplayState.NONE)
    st.header("Weekly Home")
    st.caption("Primary action: review this week, then ask Compass or draft a plan.")
    with st.container(border=True):
        st.subheader(home.journey.display_label)
        st.markdown(f"**{home.hero_title}**")
        st.write(home.hero_body)
    image_path = ROOT / (home.hero_asset or "")
    if image_path.exists():
        st.image(str(image_path), caption=home.hero_alt, width=330)
    st.caption("Accessible image description: " + home.hero_alt)

    st.subheader("Your confirmed information")
    for item in home.confirmed_context:
        st.markdown(f"- {item}")

    for section in home.sections:
        st.subheader(section.heading)
        for item in section.items:
            st.write(item)
        if section.state.value != "success":
            st.caption(f"Status: {section.state.value.replace('_', ' ')}")

    st.subheader("Plan status")
    if home.plan_state == PlanDisplayState.NONE:
        st.info("No plan draft yet. Build a session-only draft when you are ready.")
    else:
        st.success("A validated session-only draft is ready to inspect. It has not been saved.")

    st.subheader("Needs confirmation")
    for item in home.unresolved_items:
        st.warning(item)

    c1, c2, c3 = st.columns(3)
    with c1:
        _go(ProductPage.COMPASS, "Ask Compass", "stage9_demo_home_compass")
    with c2:
        _go(ProductPage.PLAN, "Draft a plan", "stage9_demo_home_plan")
    with c3:
        _go(ProductPage.RECORDS, "Review records", "stage9_demo_home_records")
    st.caption(f"Home assembly specialist calls: {home.agent_fanout_count}")


def _render_evidence_button(item, index: int, prefix: str) -> None:
    st.markdown(f"**{item.evidence_id}** · {item.source_title}")
    st.caption(f"{item.review_status} · {item.locator}")
    if st.button("Open supporting evidence", key=f"{prefix}_evidence_{index}"):
        st.session_state.stage9_demo_selected_evidence = item.model_dump(mode="json")
        _navigate(ProductPage.EVIDENCE)
        st.rerun()


def _render_chat_result(execution: ProductExecution, *, prefix: str) -> None:
    result = execution.display
    if result.route == "urgent":
        st.markdown("<div class='nest-danger'><strong>Get urgent help now</strong></div>", unsafe_allow_html=True)
        st.error(result.summary)
        st.caption("Fixed Stage 6 wording · shown before ordinary generation · ordinary generation calls: 0")
        return
    if result.route == "clarification":
        st.warning(result.title)
        st.write(result.summary)
        for item in result.uncertainties:
            st.caption(item)
        return
    if result.route in {"abstained", "unsupported"}:
        st.warning(result.title)
        st.write(result.summary)
        for item in result.uncertainties:
            st.caption(item)
        return

    st.success(result.title)
    st.write(result.summary)
    for label, statements in result.provenance_sections.items():
        st.markdown(f"#### {label}")
        for statement in statements:
            st.write(statement)
    if result.applied_constraints:
        st.markdown("#### Your confirmed information applied")
        for item in result.applied_constraints:
            st.write(f"- {item}")
    if result.uncertainties:
        st.markdown("#### Needs confirmation")
        for item in result.uncertainties:
            st.write(f"- {item}")
    if result.proposed_actions:
        st.markdown("#### Proposed actions")
        for item in result.proposed_actions:
            st.write(f"- {item} *(proposal only)*")
    if result.citations:
        st.markdown("#### Evidence")
        for index, item in enumerate(result.citations):
            _render_evidence_button(item, index, prefix)
    st.caption("Validated by the accepted Stage 8 display gate · controlled fixtures · no durable write")


def _compass() -> None:
    st.header("Compass")
    st.caption("Primary action: choose a suggested task or enter one fictional question.")
    _emergency_access()
    examples = {
        "Choose a supported demo task": "",
        "Public nutrition guidance": "Show meal options",
        "Explain my fictional record": "Show what my document says",
        "Organize recorded medication": "List my medication record",
        "Movement options": "Show movement options",
        "Well-being support": "Show my wellbeing support plan",
        "Prepare for appointment": "Show appointment questions",
        "Weekly plan": "Show my weekly plan",
        "Urgent bypass example": "I cannot breathe. Show my weekly plan.",
    }
    selected = st.selectbox("Suggested fictional task", list(examples), key="stage9_demo_example")
    with st.form("stage9_demo_compass_form", clear_on_submit=False):
        query = st.text_area(
            "Message Compass",
            value=examples[selected],
            placeholder="Use fictional information only",
            help="Every message enters the deterministic Safety Gate first.",
            key="stage9_demo_query",
        )
        submitted = st.form_submit_button("Send to Compass", type="primary")
    if submitted:
        normalized = " ".join(query.split())
        if not normalized:
            st.session_state.stage9_demo_input_error = "Enter a fictional question before sending."
        else:
            fingerprint = sha256(normalized.encode("utf-8")).hexdigest()
            if st.session_state.get("stage9_demo_processing"):
                st.session_state.stage9_demo_input_error = "The current request is still processing."
            elif fingerprint == st.session_state.get("stage9_demo_last_submission"):
                st.session_state.stage9_demo_input_error = "Duplicate send prevented. Edit the message before sending again."
            else:
                st.session_state.stage9_demo_processing = True
                horizon = "week" if "weekly plan" in normalized.casefold() else "none"
                with st.spinner("Checking safety, evidence, and constraints…"):
                    execution = run_compass(normalized, horizon=horizon)
                st.session_state.setdefault("stage9_demo_chat_history", []).extend([
                    {"role": "user", "text": normalized},
                    {"role": "assistant", "execution": execution},
                ])
                st.session_state.stage9_demo_last_submission = fingerprint
                st.session_state.stage9_demo_processing = False
                st.session_state.pop("stage9_demo_input_error", None)

    if error := st.session_state.get("stage9_demo_input_error"):
        st.error(error)
        if st.button("Clear validation message", key="stage9_demo_clear_input_error"):
            st.session_state.pop("stage9_demo_input_error", None)
            st.rerun()

    history = st.session_state.get("stage9_demo_chat_history", [])
    if not history:
        st.info("No messages yet. The fictional demo conversation starts empty after every reset.")
    for index, message in enumerate(history):
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.write(message["text"])
            else:
                _render_chat_result(message["execution"], prefix=f"chat_{index}")


def _records() -> None:
    st.header("Records")
    st.caption("Primary action: inspect the exact fictional source span before proposing confirmation or correction.")
    st.info("Production document upload is unavailable. These registered files are controlled fictional fixtures.")
    for document in demo_documents():
        status_label = document.status.replace("_", " ")
        with st.expander(f"{document.document_id} · {document.label} · {status_label}"):
            st.write(f"**Subject:** {document.subject}")
            for field in document.fields:
                st.markdown(f"**{field.label}:** {field.value}")
                st.caption(
                    f"{field.status} · {field.source_id} · {field.locator} · "
                    f"confidence {field.confidence:.0%}"
                )
                st.code(field.exact_span, language=None)
                if field.record_only:
                    st.warning("Recorded/documented as only. Nestline does not suggest a medication change.")
            if document.status != "ready":
                st.warning(document.recovery)
            else:
                st.info(document.recovery)
            st.button(
                "Record confirmation intent (Stage 10 unavailable)",
                key=f"stage9_demo_record_{document.document_id}", disabled=True,
            )


def _build_plan(label: str) -> ProductExecution:
    prompts = {
        "Nutrition only": "Show my nutrition weekly plan",
        "Movement only": "Show my movement weekly plan",
        "Well-being only": "Show my wellbeing weekly plan",
        "Holistic": "Show my weekly plan",
    }
    return run_compass(prompts[label], horizon="week")


def _plan() -> None:
    st.header("Plan")
    st.caption("Primary action: draft one session-only plan variant, then inspect its constraints and evidence.")
    variant = st.radio(
        "Plan type", ["Nutrition only", "Movement only", "Well-being only", "Holistic"],
        horizontal=True, key="stage9_demo_plan_variant",
    )
    if st.button("Build validated fictional week", type="primary", key="stage9_demo_build_plan"):
        st.session_state.stage9_demo_plan_execution = _build_plan(variant)
    execution = st.session_state.get("stage9_demo_plan_execution")
    requested_draft = st.session_state.get(
        "stage9_demo_requested_draft", st.query_params.get("draft", "")
    )
    draft_labels = {
        "nutrition": "Nutrition only",
        "movement": "Movement only",
        "wellbeing": "Well-being only",
        "holistic": "Holistic",
    }
    if execution is None and requested_draft in draft_labels:
        execution = _build_plan(draft_labels[requested_draft])
        st.session_state.stage9_demo_plan_execution = execution
    if execution is None:
        st.info("Plan state: none. No draft has been created.")
        st.button("Save plan (Stage 10 unavailable)", disabled=True, key="stage9_demo_save_none")
        return
    if execution.display.route != "validated" or execution.stage7.proposed_schedule is None:
        st.error("Plan state: invalid or unavailable. The draft cannot be displayed as active.")
        _render_chat_result(execution, prefix="plan_invalid")
        return

    schedule = execution.stage7.proposed_schedule
    if schedule.stale:
        st.error("Plan state: stale. Refresh the journey/context before using it.")
    elif schedule.conflicts or schedule.unresolved_uncertainties:
        st.warning("Plan state: conflict. This proposal is not eligible to save.")
    else:
        st.success("Plan state: draft · validated · session only · not saved")
    st.write(f"Journey state version: {schedule.state_version} · horizon: {schedule.horizon}")
    for day in WEEKDAYS:
        title = day.title() + (" · weekend" if day in {"saturday", "sunday"} else " · weekday")
        st.subheader(title)
        items = [item for item in schedule.items if item.day.value == day]
        if not items:
            st.caption("No fixed item. This day remains flexible.")
        for item in items:
            st.markdown(f"**{item.start}–{item.end} · {item.domain.replace('_', ' ').title()}**")
            st.write(item.item)
            st.caption(
                f"Contributor: {item.contributor} · {'optional' if item.optional else 'planned'} · "
                f"{'flexible' if item.flexible else 'fixed'} · evidence: {', '.join(item.evidence_ids)}"
            )
            if item.record_only:
                st.warning("Read-only recorded reminder. Timing was not invented or changed.")
            for note in item.constraint_notes + item.rest_recovery_notes:
                st.write(f"- {note}")

    st.subheader("Your confirmed information applied")
    for item in schedule.applied_constraints:
        st.write(f"- {item}")
    if schedule.assumptions:
        st.subheader("Assumptions")
        for item in schedule.assumptions:
            st.write(f"- {item}")
    if schedule.conflicts or schedule.unresolved_uncertainties:
        st.subheader("Needs confirmation")
        for item in schedule.conflicts + schedule.unresolved_uncertainties:
            st.write(f"- {item}")

    change = st.text_input(
        "Describe a change request (proposal only)", key="stage9_demo_plan_change",
        placeholder="Example: move an optional item to another open window",
    )
    if st.button("Record session change intent", key="stage9_demo_plan_change_button"):
        if change.strip():
            st.session_state.stage9_demo_plan_change_intent = change.strip()
        else:
            st.error("Describe the change before recording the intent.")
    if intent := st.session_state.get("stage9_demo_plan_change_intent"):
        st.info(f"Session-only change intent: {intent}. It has not been applied or saved.")
    st.button("Save plan (Stage 10 unavailable)", disabled=True, key="stage9_demo_save_plan")
    if st.button("Discard session draft", key="stage9_demo_discard_plan"):
        st.session_state.pop("stage9_demo_plan_execution", None)
        st.session_state.pop("stage9_demo_plan_change_intent", None)
        st.rerun()
    with st.expander("Other plan states this product handles"):
        st.write("Saved: display-only when a trusted storage layer reports it; Stage 9 cannot create one.")
        st.write("Stale: visibly inactive after a material state-version change.")
        st.write("Conflict or invalid: blocked from active display and save intent.")
        st.write("Unavailable: explains the missing service or evidence and offers a recovery step.")


def _evidence() -> None:
    st.header("Evidence drawer")
    st.caption("Primary action: check the source, exact span, applicability, and support status.")
    with st.expander("How Nestline labels information"):
        st.write("**Your confirmed information** — information confirmed in your current record.")
        st.write("**Your uploaded record says** — wording traced to an uploaded record; it is not a diagnosis.")
        st.write("**You reported** — information you entered that has not been presented as a clinician fact.")
        st.write("**Public guidance says** — guidance tied to an eligible exact source span.")
        st.write("**Needs confirmation** — missing, conflicting, or uncertain information that must stay unresolved.")
    raw = st.session_state.get("stage9_demo_selected_evidence")
    requested_evidence = st.session_state.get(
        "stage9_demo_requested_evidence", st.query_params.get("evidence", "")
    )
    if not raw and requested_evidence:
        # A reproducible local evidence deep-link still passes through the accepted
        # Stage 7/8 fixture path before the drawer is populated.
        execution = run_compass("Show meal options")
        match = next(
            (item for item in execution.display.citations if item.evidence_id == requested_evidence),
            None,
        )
        if match is not None:
            raw = match.model_dump(mode="json")
    if not raw:
        st.info("No citation selected. Open one from Compass or a validated plan.")
        if st.button(
            "Load controlled fictional evidence example",
            type="primary",
            key="stage9_demo_evidence_example",
        ):
            execution = run_compass("Show meal options")
            if execution.display.citations:
                st.session_state.stage9_demo_selected_evidence = (
                    execution.display.citations[0].model_dump(mode="json")
                )
                st.rerun()
            else:
                st.error(
                    "The controlled example has no eligible citation to display."
                )
        _go(ProductPage.COMPASS, "Return to Compass", "stage9_demo_evidence_back")
        return
    from app.schemas.product_experience import EvidenceDrawerItem
    item = EvidenceDrawerItem.model_validate(raw)
    if item.workspace_id and item.workspace_id != "72222222-2222-4222-8222-222222222222":
        st.error("This private source does not belong to the active fictional workspace.")
        return
    st.subheader(item.source_title)
    st.write(f"**Publisher:** {item.publisher}")
    st.write(f"**Type:** {item.source_type.replace('_', ' ')}")
    st.write(f"**Review/current status:** {item.review_status} · {item.current_status}")
    st.write(f"**Applicability:** {item.journey_applicability or 'authenticated personal record only'}")
    st.write(f"**Locator:** {item.locator}")
    st.markdown("#### Supporting passage")
    st.code(item.supporting_passage, language=None)
    st.success("Supports the displayed claim" if item.supports_claim else "Support is insufficient")
    st.warning("Controlled fictional evidence. This is not a public clinical release.")


def _review() -> None:
    st.header("Simulated review")
    st.caption("Primary action: inspect what would be shared; no request is submitted in Stage 9.")
    status = st.selectbox(
        "Simulated status",
        ["offered", "consented", "queued", "responded", "declined", "unavailable", "timed_out"],
        key="stage9_demo_review_status",
    )
    review = simulated_review(status)
    st.warning("Simulated review only. No doctor or authorized reviewer is connected to this screen.")
    st.write(f"Current state: **{review.status}**")
    st.write("Minimum fictional context proposed for sharing:")
    for item in review.context_proposed:
        st.write(f"- {item}")
    st.button("Submit review (Stage 10 unavailable)", disabled=True, key="stage9_demo_review_submit")
    st.caption("An urgent safety result bypasses this queue immediately.")


def _evaluator() -> None:
    st.header("Evaluator view")
    st.warning("Evaluator-only evidence. It is separate from the maternal-health product experience.")
    st.caption("Metrics are read from repository-generated artifacts at render time.")
    metrics = load_evaluator_metrics()
    st.dataframe(
        [
            {
                "stage": row.stage,
                "passed": row.passed,
                "total": row.total,
                "failed": row.failed,
                "skipped": row.skipped,
                "dataset": row.dataset_version,
                "artifact": row.artifact,
            }
            for row in metrics
        ],
        hide_index=True,
        width="stretch",
    )
    st.info("Provider and LangSmith live runs: unavailable/unrun. Displayed evidence is local, deterministic, synthetic, and redacted.")
    failed = authentic_failed_trace()
    st.subheader("Authentic failed-trace walkthrough")
    first = failed["first_pass"]
    st.write(f"First Stage 8 pass: {first['passed']}/{first['total']} cases; critical {first['critical_passed']}/{first['critical_total']}.")
    st.write(first["interpretation"])
    st.write(f"Observed finding: {failed['finding']['finding']}")
    st.write(f"Correction: {failed['finding']['rectification']}")
    st.caption(f"Source artifact: {failed['artifact']}")
    st.warning("These software-contract results do not establish clinical validity, production quality, or usability research.")


def render_stage9_demo() -> None:
    _css()
    _boundary_banner()
    _demo_banner()
    st.sidebar.markdown("### Nestline")
    requested_page = st.query_params.get("page", "")
    page = (
        requested_page if requested_page in PAGES
        else st.session_state.get("stage9_demo_page", ProductPage.HOME.value)
    )
    if page not in PAGES:
        page = ProductPage.HOME.value
    st.sidebar.caption("Navigate")
    for destination in PAGES:
        if st.sidebar.button(
            destination,
            type="primary" if destination == page else "secondary",
            key=f"stage9_demo_nav_{destination}",
            use_container_width=True,
        ):
            _navigate(ProductPage(destination))
            st.rerun()
    st.session_state.stage9_demo_page = page
    st.query_params["page"] = page
    if st.sidebar.button("Reset fictional Demo Mode", key="stage9_demo_reset"):
        reset_demo_state_keys(st.session_state)
        st.session_state.stage9_mode = "Demo Mode"
        st.rerun()
    st.sidebar.caption("Journey: fictional pregnancy week 24 · state v3")
    st.sidebar.caption("Compass safety route is always available")

    renderers = {
        ProductPage.HOME.value: _home,
        ProductPage.COMPASS.value: _compass,
        ProductPage.RECORDS.value: _records,
        ProductPage.PLAN.value: _plan,
        ProductPage.EVIDENCE.value: _evidence,
        ProductPage.REVIEW.value: _review,
        ProductPage.EVALUATOR.value: _evaluator,
    }
    renderers[page]()
    if page != ProductPage.COMPASS.value:
        _emergency_access()
