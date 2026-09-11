"""Nestline Streamlit entry point.

Stage 3 exposes authentication, isolated workspace selection, deterministic
journey resolution, optional onboarding details, and explicit confirmation.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
import streamlit as st

from app.pages_and_components.onboarding import render_onboarding
from app.schemas.foundation import SafetySpec


ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env", override=False)

st.set_page_config(
    page_title="Nestline · Compass",
    page_icon="🧭",
    layout="centered",
)

st.title("Nestline Compass")
st.write("A week-aware pregnancy and postpartum companion under active review.")
st.warning(
    "Development build: use fictional information only. Nestline cannot diagnose, "
    "replace a clinician, or provide emergency care."
)

project_url = os.environ.get("NESTLINE_SUPABASE_URL", "").strip()
publishable_key = os.environ.get("NESTLINE_SUPABASE_PUBLISHABLE_KEY", "").strip()
if not project_url or not publishable_key:
    st.error(
        "Supabase public configuration is missing. Add NESTLINE_SUPABASE_URL and "
        "NESTLINE_SUPABASE_PUBLISHABLE_KEY to the ignored .env file."
    )
    st.stop()

safety_spec = SafetySpec.model_validate_json(
    (ROOT / "data/safety/rule_spec.yaml").read_text(encoding="utf-8")
)
render_onboarding(project_url, publishable_key, safety_spec)