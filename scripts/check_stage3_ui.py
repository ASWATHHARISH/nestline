"""Render the unauthenticated Stage 3 Streamlit entry point without network calls."""

from __future__ import annotations

import os
from pathlib import Path

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    os.environ["NESTLINE_SUPABASE_URL"] = "https://stage3-smoke.invalid"
    os.environ["NESTLINE_SUPABASE_PUBLISHABLE_KEY"] = "stage3-smoke-publishable-key"

    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=15).run()
    if app.exception:
        messages = [str(item.value) for item in app.exception]
        raise AssertionError(f"Streamlit render raised exceptions: {messages}")
    if not app.title or app.title[0].value != "Nestline Compass":
        raise AssertionError("Streamlit title did not render")
    if not any("fictional information only" in item.value.lower() for item in app.warning):
        raise AssertionError("development privacy warning did not render")
    if [tab.label for tab in app.tabs] != ["Sign in", "Create account"]:
        raise AssertionError("authentication tabs did not render")
    button_labels = [button.label for button in app.button]
    if "Sign in" not in button_labels or "Create account" not in button_labels:
        raise AssertionError("authentication form controls did not render")
    if len(app.text_input) != 4:
        raise AssertionError("authentication inputs did not render")

    print('{"valid": true, "rendered": "unauthenticated_onboarding", "network_calls": 0}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())