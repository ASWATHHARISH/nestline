"""Render the Stage 4 fixture selector and explicit review gate without network calls."""

from __future__ import annotations

import os
from pathlib import Path
from uuid import UUID

from streamlit.testing.v1 import AppTest

from app.services.onboarding import AuthSession, SupabaseOnboardingGateway


ROOT = Path(__file__).resolve().parents[1]
USER_ID = UUID("a0000000-0000-0000-0000-000000000001")
WORKSPACE_ID = "a1000000-0000-0000-0000-000000000001"


def _candidate(
    key: str,
    field_name: str,
    value: str,
    source_text: str,
    *,
    disposition: str = "extract_verbatim",
) -> dict:
    return {
        "candidate_key": key,
        "field_name": field_name,
        "fact_type": "test_result",
        "value": value,
        "source_page": 1,
        "source_text": source_text,
        "source_span": {
            "page": 1,
            "exact_text": source_text,
            "start": 10,
            "end": 35,
            "line": 4,
            "coordinates": [[50.0, 80.0, 220.0, 94.0]],
            "coordinate_system": "PDF points, top-left origin",
        },
        "confidence": 1.0 if disposition != "abstain" else 0.0,
        "completeness": "complete" if disposition != "abstain" else "missing",
        "disposition": disposition,
        "status": "proposed",
        "record_only": False,
        "source_value_matches": True,
        "conflict_document_keys": [],
    }


def main() -> int:
    os.environ["NESTLINE_SUPABASE_URL"] = "https://stage4-smoke.invalid"
    os.environ["NESTLINE_SUPABASE_PUBLISHABLE_KEY"] = "stage4-smoke-publishable-key"
    os.environ["NESTLINE_ENABLE_STAGE4_FIXTURE_DEMO"] = "true"
    original_list = SupabaseOnboardingGateway.list_workspaces
    original_fetch = SupabaseOnboardingGateway.fetch_current_journey_state
    try:
        SupabaseOnboardingGateway.list_workspaces = lambda self: [{
            "id": WORKSPACE_ID,
            "mode": "fictional_demo",
            "display_name": "Maya · fictional demo",
            "demo_session_key": "stage4-render",
            "demo_seed_version": "maya-v1",
            "updated_at": "2026-09-11T00:00:00+00:00",
        }]
        SupabaseOnboardingGateway.fetch_current_journey_state = lambda self, workspace_id: None
        app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=15)
        app.session_state.auth_session = AuthSession(
            user_id=USER_ID,
            access_token="fictional-stage4-session-token",
            refresh_token="fictional-stage4-refresh-token",
            expires_in=3600,
        )
        app.session_state.workspace_id = WORKSPACE_ID
        app.session_state.stage4_document_review = {
            "document_id": "a2000000-0000-0000-0000-000000000001",
            "document_label": "DOC-002 - Laboratory report",
            "identity_status": "verified_fixture_binding",
            "review_version": 1,
            "candidates": [
                _candidate(
                    "p1-l4-haemoglobin",
                    "haemoglobin",
                    "11.2 g/dL",
                    "haemoglobin: 11.2 g/dL",
                ),
                _candidate(
                    "p1-l6-reference-range",
                    "reference_range",
                    "not recorded",
                    "reference_range: not recorded",
                    disposition="abstain",
                ),
            ],
        }
        app.run()
        initial_decisions = [
            item for item in app.radio if item.label == "Decision"
        ]
        initial_decision_values = [item.value for item in initial_decisions]
        if initial_decisions:
            initial_decisions[0].set_value("confirm")
            app.run()
        partial_decision_values = [
            item.value for item in app.radio if item.label == "Decision"
        ]
        partial_save_disabled = all(
            item.disabled
            for item in app.button
            if item.label == "Save reviewed document"
        )

        os.environ["NESTLINE_ENABLE_STAGE4_FIXTURE_DEMO"] = "false"
        public_app = AppTest.from_file(
            str(ROOT / "streamlit_app.py"), default_timeout=15
        )
        public_app.session_state.auth_session = AuthSession(
            user_id=USER_ID,
            access_token="fictional-stage4-session-token",
            refresh_token="fictional-stage4-refresh-token",
            expires_in=3600,
        )
        public_app.session_state.workspace_id = WORKSPACE_ID
        public_app.run()
    finally:
        SupabaseOnboardingGateway.list_workspaces = original_list
        SupabaseOnboardingGateway.fetch_current_journey_state = original_fetch

    if app.exception:
        raise AssertionError(
            f"Stage 4 Streamlit render raised exceptions: {[str(item.value) for item in app.exception]}"
        )
    if "Medical reports" not in [item.value for item in app.subheader]:
        raise AssertionError("Stage 4 medical-report panel did not render")
    captions = [item.value for item in app.caption]
    if not any("Arbitrary uploads are disabled" in value for value in captions):
        raise AssertionError("the non-public upload boundary was not visible")
    if app.file_uploader:
        raise AssertionError("the public demo must not render an arbitrary file uploader")
    if "Choose a registered fictional report" not in [
        item.label for item in app.selectbox
    ]:
        raise AssertionError("the exact fixture selector did not render")
    if not any(
        "page 1; character span 10-35; confidence 100%" in value
        and "extraction disposition extract_verbatim" in value
        for value in captions
    ):
        raise AssertionError("review provenance was not rendered")
    if len(initial_decision_values) != 2 or any(
        value is not None for value in initial_decision_values
    ):
        raise AssertionError("every candidate decision must start unselected")
    if (
        partial_decision_values.count(None) != 1
        or not partial_save_disabled
    ):
        raise AssertionError("save must remain disabled when exactly one decision is missing")
    save_buttons = [
        item for item in app.button if item.label == "Save reviewed document"
    ]
    if len(save_buttons) != 1 or not save_buttons[0].disabled:
        raise AssertionError("save must remain disabled while decisions are missing")
    confirmations = [
        item
        for item in app.checkbox
        if item.label == "I reviewed every field and want to apply these decisions."
    ]
    if len(confirmations) != 1 or not confirmations[0].disabled:
        raise AssertionError("final confirmation must remain disabled before all decisions")
    if "Sign out" not in [button.label for button in app.button]:
        raise AssertionError("authenticated workspace controls did not render")
    if public_app.exception:
        raise AssertionError(
            "default-off Stage 4 render raised an exception: "
            f"{[str(item.value) for item in public_app.exception]}"
        )
    if public_app.file_uploader or any(
        item.label == "Choose a registered fictional report"
        for item in public_app.selectbox
    ):
        raise AssertionError("the default public build exposed document processing")
    if not any(
        "Document processing is closed in this build" in item.value
        for item in public_app.info
    ):
        raise AssertionError("the default public build did not explain its closed state")
    print(
        '{"valid": true, "rendered": "registered_fixture_explicit_review", '
        '"preselected_decisions": 0, "public_feature_closed": true, '
        '"network_calls": 0}'
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
