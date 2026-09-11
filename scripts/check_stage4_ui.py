"""Render the authenticated fictional Stage 4 upload panel without network calls."""

from __future__ import annotations

import os
from pathlib import Path
from uuid import UUID

from streamlit.testing.v1 import AppTest

from app.services.onboarding import AuthSession, SupabaseOnboardingGateway


ROOT = Path(__file__).resolve().parents[1]
USER_ID = UUID("a0000000-0000-0000-0000-000000000001")
WORKSPACE_ID = "a1000000-0000-0000-0000-000000000001"


def main() -> int:
    os.environ["NESTLINE_SUPABASE_URL"] = "https://stage4-smoke.invalid"
    os.environ["NESTLINE_SUPABASE_PUBLISHABLE_KEY"] = "stage4-smoke-publishable-key"
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
        app.run()
    finally:
        SupabaseOnboardingGateway.list_workspaces = original_list
        SupabaseOnboardingGateway.fetch_current_journey_state = original_fetch

    if app.exception:
        raise AssertionError(
            f"Stage 4 Streamlit render raised exceptions: {[str(item.value) for item in app.exception]}"
        )
    subheaders = [item.value for item in app.subheader]
    if "Medical reports" not in subheaders:
        raise AssertionError("Stage 4 medical-report panel did not render")
    captions = [item.value for item in app.caption]
    if not any("Fictional demo only" in value for value in captions):
        raise AssertionError("fictional-only upload boundary was not visible")
    if len(app.file_uploader) != 1:
        raise AssertionError("exactly one private-document uploader should render")
    if "Sign out" not in [button.label for button in app.button]:
        raise AssertionError("authenticated workspace controls did not render")
    print('{"valid": true, "rendered": "fictional_document_review", "network_calls": 0}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
