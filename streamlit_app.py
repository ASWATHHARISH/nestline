"""Nestline Streamlit entry point for the Stage 9 local product experience."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
import streamlit as st

from app.pages_and_components.onboarding import render_onboarding
from app.pages_and_components.stage9 import render_stage9_demo
from app.schemas.foundation import SafetySpec
from app.schemas.product_experience import ProductMode
from app.services.product_experience import load_runtime_config, personal_empty_home


ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env", override=False)

st.set_page_config(
    page_title="Nestline · Compass",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Nestline Compass")
st.write("A week-aware pregnancy and postpartum companion under active review.")
st.warning(
    "Development build: use fictional information only. Nestline cannot diagnose, "
    "replace a clinician, prescribe, or provide emergency care."
)

requested_mode = st.query_params.get("mode", "").casefold()
requested_evidence = st.query_params.get("evidence", "")
if requested_evidence:
    st.session_state.stage9_demo_requested_evidence = requested_evidence
requested_plan_draft = st.query_params.get("draft", "").casefold()
if requested_plan_draft in {"nutrition", "movement", "wellbeing", "holistic"}:
    # Preserve reproducible review links across Streamlit's initial query-param rerun.
    st.session_state.stage9_demo_requested_draft = requested_plan_draft
if "stage9_mode" not in st.session_state and requested_mode in {"personal", "demo"}:
    st.session_state.stage9_mode = (
        ProductMode.DEMO.value if requested_mode == "demo" else ProductMode.PERSONAL.value
    )
mode = st.sidebar.radio(
    "Experience mode",
    [ProductMode.PERSONAL.value, ProductMode.DEMO.value],
    key="stage9_mode",
    help="Personal starts empty. Demo uses a deterministic fictional workspace.",
)
st.query_params["mode"] = "demo" if mode == ProductMode.DEMO.value else "personal"

if mode == ProductMode.DEMO.value:
    render_stage9_demo()
else:
    config = load_runtime_config()
    st.markdown(
        "**Personal Mode starts empty.** Demo fixtures are never copied into this mode or another workspace."
    )
    if not config.personal_mode_available:
        home = personal_empty_home()
        st.info(home.hero_body)
        st.error(
            "Personal Mode configuration is incomplete. Missing: "
            + ", ".join(config.missing_fields)
            + ". Copy .env.example to .env, fill only the public Supabase URL and publishable key, then restart Streamlit."
        )
        st.caption("Demo Mode remains locally available without Supabase and uses fictional fixtures only.")
    else:
        safety_spec = SafetySpec.model_validate_json(
            (ROOT / "data/safety/rule_spec.yaml").read_text(encoding="utf-8")
        )
        render_onboarding(
            os.environ["NESTLINE_SUPABASE_URL"].strip(),
            os.environ["NESTLINE_SUPABASE_PUBLISHABLE_KEY"].strip(),
            safety_spec,
        )
