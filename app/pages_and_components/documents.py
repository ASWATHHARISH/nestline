"""Stage 4 Streamlit flow for exact fictional fixtures and explicit review."""

from __future__ import annotations

import json
import os
from uuid import UUID, uuid4

import streamlit as st

from app.schemas.documents import ConfirmationDecision, DocumentReviewRequest
from app.services.personal_documents import (
    DocumentProcessingError,
    FictionalFixture,
    FictionalFixtureScanner,
    SupabaseDocumentGateway,
    extract_fixture_candidates,
    load_fictional_fixture_registry,
    parse_document,
    validate_upload,
)


class _ControlledFixtureOcr:
    """Exact OCR replay for one registered, visibly fictional demo image."""

    def __init__(self, expected_text: str):
        self.expected_text = expected_text

    def extract_pages(self, data: bytes, *, media_type: str) -> list[str]:
        del data, media_type
        return [self.expected_text]


def _ocr_for_fixture(fixture: FictionalFixture):
    if fixture.ocr_truth_path is None:
        return None
    truth = json.loads(fixture.ocr_truth_path.read_text(encoding="utf-8"))
    if truth.get("image_sha256") != fixture.sha256:
        raise DocumentProcessingError(
            "fixture_registry", "The registered OCR truth does not match the fixture."
        )
    return _ControlledFixtureOcr(str(truth["expected_ocr_text"]))


def _prepare_registered_fixture(
    gateway: SupabaseDocumentGateway,
    workspace_id: UUID,
    fixture: FictionalFixture,
) -> None:
    data = fixture.path.read_bytes()
    scanner = FictionalFixtureScanner(frozenset({fixture.sha256}))
    validation = validate_upload(
        data,
        filename=fixture.path.name,
        claimed_media_type=fixture.media_type,
        scanner=scanner,
    )
    pages, fitz_pages = parse_document(
        data,
        media_type=validation.media_type,
        ocr_adapter=_ocr_for_fixture(fixture),
    )
    packet = extract_fixture_candidates(
        pages, document_sha256=validation.sha256, fitz_pages=fitz_pages
    )
    if not packet.fictional:
        raise DocumentProcessingError(
            "not_fictional", "This development flow accepts only fictional demo reports."
        )

    # Every fixture must match the selected demo profile. A source-level persona
    # wins when present; otherwise the exact-hash registry supplies the binding.
    validation = validate_upload(
        data,
        filename=fixture.path.name,
        claimed_media_type=fixture.media_type,
        scanner=scanner,
        expected_subject=fixture.expected_subject,
        subject_as_written=packet.subject_as_written,
        fixture_bound_subject=fixture.expected_subject,
    )
    document_id, created = gateway.upload_and_register(workspace_id, validation, data)
    review_version = gateway.record_extraction(
        workspace_id, document_id, validation, packet
    )
    st.session_state.stage4_document_review = {
        "document_id": str(document_id),
        "document_label": fixture.label,
        "identity_status": validation.identity_status,
        "review_version": review_version,
        "candidates": gateway.list_candidates(workspace_id, document_id),
    }
    if not created:
        st.info("This exact file already existed, so Nestline reused its one logical record.")


def _review_action_options(candidate: dict) -> tuple[list[str], dict[str, str]]:
    if candidate["disposition"] == "abstain":
        return ["reject"], {
            "reject": "Acknowledge the missing value and reject the proposal"
        }
    if candidate.get("conflict_document_keys"):
        return ["keep_conflict", "reject"], {
            "keep_conflict": "Keep both sources as an unresolved conflict",
            "reject": "Reject this proposal",
        }
    return ["confirm", "edit_and_confirm", "reject"], {
        "confirm": "Confirm exactly as extracted",
        "edit_and_confirm": "Correct the extracted value, then confirm",
        "reject": "Reject this proposal",
    }


def _render_candidate_review(gateway, workspace_id: UUID) -> None:
    review = st.session_state.get("stage4_document_review")
    if not review:
        return

    candidates = review["candidates"]
    st.markdown("#### Review every extracted field")
    st.caption(f"Registered source: {review.get('document_label', 'fictional fixture')}")
    st.caption(
        "Each row is only a proposal. Compare the value with the exact source and "
        "make one deliberate decision. No review choice is preselected."
    )
    decisions: list[ConfirmationDecision] = []
    incomplete: list[str] = []
    review_key = review["document_id"]

    for candidate in candidates:
        key = candidate["candidate_key"]
        st.markdown(f"**{candidate['field_name'].replace('_', ' ').title()}**")
        st.write(candidate["value"])
        st.code(candidate["source_text"], language=None)

        span = candidate.get("source_span") or {}
        page = span.get("page", candidate.get("source_page", "unknown"))
        start = span.get("start", "unknown")
        end = span.get("end", "unknown")
        confidence = candidate.get("confidence")
        confidence_text = (
            f"{float(confidence):.0%}" if confidence is not None else "unknown"
        )
        st.caption(
            "Provenance: "
            f"page {page}; character span {start}-{end}; confidence {confidence_text}; "
            f"completeness {candidate.get('completeness', 'unknown')}; "
            f"extraction disposition {candidate.get('disposition', 'unknown')}; "
            f"current state {candidate.get('status', 'proposed')}."
        )
        coordinates = span.get("coordinates") or []
        if coordinates:
            st.caption(
                f"Page coordinates ({span.get('coordinate_system', 'source units')}): "
                f"{json.dumps(coordinates)}"
            )
        if candidate.get("record_only"):
            st.caption("Recorded text only · this does not recommend or change treatment.")
        if candidate["disposition"] == "abstain":
            st.info(
                "The source says this value was not recorded. Rejecting it stores no "
                "positive health fact."
            )
        if not candidate.get("source_value_matches", True):
            st.error("The proposed value does not exactly match the source. Edit or reject it.")

        options, labels = _review_action_options(candidate)
        action = st.radio(
            "Decision",
            options,
            index=None,
            format_func=lambda value, labels=labels: labels[value],
            key=f"stage4-action-{review_key}-{key}",
            horizontal=len(options) > 1,
        )
        edited_value = None
        if action == "edit_and_confirm":
            current = candidate["value"]
            edited_value = st.text_input(
                "Corrected value",
                value=current if isinstance(current, str) else json.dumps(current),
                key=f"stage4-edit-{review_key}-{key}",
            )
            if not edited_value.strip():
                incomplete.append(key)
                st.error("Enter a corrected value before saving.")
                st.divider()
                continue
        if action is None:
            incomplete.append(key)
        else:
            decisions.append(ConfirmationDecision(
                candidate_key=key,
                action=action,
                edited_value=edited_value,
            ))
        st.divider()

    all_decided = len(incomplete) == 0 and len(decisions) == len(candidates)
    if not all_decided:
        st.warning(
            f"Choose a decision for every row. {len(incomplete)} "
            f"decision{'s are' if len(incomplete) != 1 else ' is'} still missing."
        )
    confirmed = st.checkbox(
        "I reviewed every field and want to apply these decisions.",
        disabled=not all_decided,
        key=f"stage4-confirm-{review_key}",
    )
    save = st.button(
        "Save reviewed document",
        type="primary",
        disabled=not (all_decided and confirmed),
        key=f"stage4-save-{review_key}",
    )
    if not save:
        return

    try:
        result = gateway.commit_review(DocumentReviewRequest(
            workspace_id=workspace_id,
            document_id=UUID(review["document_id"]),
            expected_review_version=review["review_version"],
            submission_key=f"streamlit-doc-{uuid4()}",
            decisions=decisions,
        ))
        st.session_state.pop("stage4_document_review", None)
        if result.conflict_fact_ids:
            st.warning("Saved with an unresolved conflict and a clarification route.")
        else:
            st.success("Saved the reviewed fields with their source evidence.")
        if result.stale_plan_ids:
            st.info("A saved movement plan is now stale because the confirmed record changed.")
        st.rerun()
    except (DocumentProcessingError, ValueError) as exc:
        st.error(str(exc))


def render_document_panel(
    project_url: str,
    publishable_key: str,
    user_access_token: str,
    workspace: dict,
) -> None:
    st.divider()
    st.subheader("Medical reports")
    if workspace["mode"] != "fictional_demo":
        st.info(
            "Personal medical-report upload is closed in this development build until "
            "the malware-scanning policy and human release gates are complete."
        )
        return

    if os.getenv("NESTLINE_ENABLE_STAGE4_FIXTURE_DEMO", "").casefold() != "true":
        st.info(
            "Document processing is closed in this build. The exact-fixture flow "
            "may be enabled only for a supervised development demo."
        )
        return
    st.caption(
        "Supervised fictional demo only. Arbitrary uploads are disabled. Choose "
        "one immutable, exact-hash fixture from the repository-owned list."
    )
    gateway = SupabaseDocumentGateway(
        project_url, publishable_key, user_access_token
    )
    fixtures = load_fictional_fixture_registry()
    fixtures_by_id = {fixture.fixture_id: fixture for fixture in fixtures}
    selected_id = st.selectbox(
        "Choose a registered fictional report",
        options=list(fixtures_by_id),
        index=None,
        format_func=lambda fixture_id: fixtures_by_id[fixture_id].label,
        placeholder="Select a fictional fixture",
    )
    if st.button(
        "Extract reviewable fields",
        type="primary",
        disabled=selected_id is None,
    ):
        try:
            _prepare_registered_fixture(
                gateway,
                UUID(workspace["id"]),
                fixtures_by_id[selected_id],
            )
            st.success("Extraction finished. Nothing has been applied yet.")
        except (DocumentProcessingError, ValueError) as exc:
            st.error(str(exc))
    _render_candidate_review(gateway, UUID(workspace["id"]))
