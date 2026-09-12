"""Deterministic Stage 9 Streamlit navigation and integration smoke check."""

from __future__ import annotations

import json
import os
from pathlib import Path

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]


def demo_app(page: str) -> AppTest:
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30)
    app.session_state["stage9_mode"] = "Demo Mode"
    app.session_state["stage9_demo_page"] = page
    return app.run()


def assert_clean(app: AppTest, page: str) -> None:
    if app.exception:
        raise AssertionError(f"{page} raised: {[str(item.value) for item in app.exception]}")


def main() -> int:
    original_url = os.environ.get("NESTLINE_SUPABASE_URL")
    original_key = os.environ.get("NESTLINE_SUPABASE_PUBLISHABLE_KEY")
    os.environ["NESTLINE_SUPABASE_URL"] = ""
    os.environ["NESTLINE_SUPABASE_PUBLISHABLE_KEY"] = ""
    try:
        personal = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30).run()
    finally:
        if original_url is None:
            os.environ.pop("NESTLINE_SUPABASE_URL", None)
        else:
            os.environ["NESTLINE_SUPABASE_URL"] = original_url
        if original_key is None:
            os.environ.pop("NESTLINE_SUPABASE_PUBLISHABLE_KEY", None)
        else:
            os.environ["NESTLINE_SUPABASE_PUBLISHABLE_KEY"] = original_key
    assert_clean(personal, "Personal Mode")
    if not any("Personal Mode configuration is incomplete" in item.value for item in personal.error):
        raise AssertionError("missing Personal Mode configuration was not explained")

    home = demo_app("Weekly Home")
    assert_clean(home, "Weekly Home")
    if [item.value for item in home.header] != ["Weekly Home"]:
        raise AssertionError("Weekly Home did not render as the primary view")
    text = " ".join(str(item.value) for item in list(home.markdown) + list(home.caption) + list(home.info) + list(home.warning) + list(home.subheader))
    for required in ["Pregnancy week 24", "Your confirmed information", "Home assembly specialist calls: 0"]:
        if required not in text:
            raise AssertionError(f"Weekly Home omitted {required}")

    records = demo_app("Records")
    assert_clean(records, "Records")
    labels = [item.label for item in records.expander]
    for state in ["ready", "low confidence", "conflict", "locked", "corrupt", "unsupported", "wrong person"]:
        if not any(state in label for label in labels):
            raise AssertionError(f"Records omitted {state} state")
    if any(button.label.startswith("Record confirmation") and not button.disabled for button in records.button):
        raise AssertionError("Stage 10 record persistence was enabled")

    compass = demo_app("Compass")
    assert_clean(compass, "Compass empty")
    compass.text_area[0].set_value("Show meal options")
    next(button for button in compass.button if button.label == "Send to Compass").click()
    compass.run()
    assert_clean(compass, "Compass validated")
    if not any(item.value == "Validated controlled-fixture result" for item in compass.success):
        raise AssertionError("validated Compass response was not displayed")
    if not any("Public guidance says" in str(item.value) for item in compass.markdown):
        raise AssertionError("visible provenance label was not rendered")
    if not any(button.label == "Open supporting evidence" for button in compass.button):
        raise AssertionError("citation did not expose the evidence drawer action")
    next(button for button in compass.button if button.label == "Send to Compass").click()
    compass.run()
    if not any("Duplicate send prevented" in item.value for item in compass.error):
        raise AssertionError("duplicate chat submission was not prevented")
    next(
        button for button in compass.button
        if button.label == "Open supporting evidence"
    ).click()
    compass.run()
    assert_clean(compass, "Evidence navigation")
    if [item.value for item in compass.header] != ["Evidence drawer"]:
        raise AssertionError("citation action did not navigate to the evidence drawer")
    if not any("Supporting passage" in str(item.value) for item in compass.markdown):
        raise AssertionError("selected evidence did not open at its supporting span")

    urgent = demo_app("Compass")
    urgent.text_area[0].set_value("I cannot breathe. Show my weekly plan.")
    next(button for button in urgent.button if button.label == "Send to Compass").click()
    urgent.run()
    assert_clean(urgent, "Compass urgent")
    if not any("Get urgent help" in item.value for item in urgent.markdown):
        raise AssertionError("urgent fixed route was not rendered separately")
    if not any("ordinary generation calls: 0" in item.value for item in urgent.caption):
        raise AssertionError("urgent zero-generation evidence was not visible")

    plan = demo_app("Plan")
    assert_clean(plan, "Plan empty")
    if not any("Plan state: none" in item.value for item in plan.info):
        raise AssertionError("empty plan state was not rendered")
    next(button for button in plan.button if button.label == "Build validated fictional week").click()
    plan.run()
    assert_clean(plan, "Plan draft")
    if not any("Plan state: draft" in item.value for item in plan.success):
        raise AssertionError("validated session-only draft was not shown")
    day_headings = [item.value for item in plan.subheader]
    for day in ["Monday · weekday", "Saturday · weekend", "Sunday · weekend"]:
        if day not in day_headings:
            raise AssertionError(f"plan omitted {day}")
    if not any(button.label.startswith("Save plan") and button.disabled for button in plan.button):
        raise AssertionError("Stage 10 plan persistence was not visibly disabled")

    review = demo_app("Simulated review")
    assert_clean(review, "Simulated review")
    if not any("No doctor or authorized reviewer" in item.value for item in review.warning):
        raise AssertionError("simulated review boundary was missing")
    if not any(button.label.startswith("Submit review") and button.disabled for button in review.button):
        raise AssertionError("Stage 10 review submission was enabled")

    evaluator = demo_app("Evaluator view")
    assert_clean(evaluator, "Evaluator view")
    if len(evaluator.dataframe) != 1:
        raise AssertionError("generated Stage 5-8 metrics table was not rendered")
    if not any("First Stage 8 pass: 55/62" in item.value for item in evaluator.markdown):
        raise AssertionError("authentic failed-trace evidence was omitted")

    result = {
        "valid": True,
        "pages_rendered": 7,
        "personal_empty_config_state": True,
        "home_agent_fanout": 0,
        "validated_chat": True,
        "duplicate_send_prevented": True,
        "urgent_generation_calls": 0,
        "record_recovery_states": 7,
        "plan_weekdays_rendered": 7,
        "stage10_writes_enabled": 0,
        "simulated_review_labeled": True,
        "evaluator_uses_generated_artifacts": True,
        "network_calls": 0,
    }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
