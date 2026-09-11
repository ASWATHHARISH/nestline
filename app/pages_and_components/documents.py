"""Stage 4 Streamlit flow for fictional report upload and explicit review."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID, uuid4

import streamlit as st

from app.schemas.documents import (
    ConfirmationDecision,
    DocumentReviewRequest,
)
from app.services.personal_documents import (
    DocumentProcessingError,
    FictionalFixtureScanner,
    SupabaseDocumentGateway,
    extract_fixture_candidates,
    parse_document,
    validate_upload,
)


ROOT = Path(__file__).resolve().parents[2]
NOISY_TRUTH = ROOT / "data/synthetic/noisy_variants/DOC-003-noisy.expected.json"


class _ControlledFixtureOcr:
    """Exact OCR replay for the one allowlisted, visibly fictional demo image."""

    def __init__(self, expected_text: str):
        self.expected_text = expected_text

    def extract_pages(self, data: bytes, *, media_type: str) -> list[str]:
        del data, media_type
        return [self.expected_text]


def _scanner_and_ocr(data: bytes):
    if not NOISY_TRUTH.exists():
        return FictionalFixtureScanner(), None
    truth = json.loads(NOISY_TRUTH.read_text(encoding="utf-8"))
    from hashlib import sha256

    digest = sha256(data).hexdigest()
    if digest == truth["image_sha256"]:
        return (
            FictionalFixtureScanner(frozenset({digest})),
            _ControlledFixtureOcr(truth["expected_ocr_text"]),
        )
    return FictionalFixtureScanner(), None


def _prepare_uploaded_fixture(gateway, workspace_id: UUID, uploaded) -> None:
    data = uploaded.getvalue()
    scanner, ocr = _scanner_and_ocr(data)
    validation = validate_upload(
        data,
        filename=uploaded.name,
        claimed_media_type=uploaded.type,
        scanner=scanner,
    )
    pages, fitz_pages = parse_document(
        data, media_type=validation.media_type, ocr_adapter=ocr
    )
    packet = extract_fixture_candidates(
        pages, document_sha256=validation.sha256, fitz_pages=fitz_pages
    )
    if not packet.fictional:
        raise DocumentProcessingError(
            "not_fictional", "This development flow accepts only fictional demo reports."
        )
    if packet.subject_as_written:
        validation = validate_upload(
            data,
            filename=uploaded.name,
            claimed_media_type=uploaded.type,
            scanner=scanner,
            expected_subject="Maya - fictional demo persona",
            subject_as_written=packet.subject_as_written,
        )
    document_id, created = gateway.upload_and_register(workspace_id, validation, data)
    review_version = gateway.record_extraction(
        workspace_id, document_id, validation, packet
    )
    st.session_state.stage4_document_review = {
        "document_id": str(document_id),
        "review_version": review_version,
        "candidates": gateway.list_candidates(workspace_id, document_id),
    }
    if not created:
        st.info("This exact file already existed, so Nestline reused its one logical record.")


def _render_candidate_review(gateway, workspace_id: UUID) -> None:
    review = st.session_state.get("stage4_document_review")
    if not review:
        return
    candidates = review["candidates"]
    st.markdown("#### Review every extracted field")
    st.caption(
        "Each row is only a proposal. Compare the value with the exact source text, "
        "then confirm, edit, reject, or keep a declared conflict."
    )
    decisions: list[ConfirmationDecision] = []
    with st.form("stage4_confirm_document"):
        for index, candidate in enumerate(candidates):
            st.markdown(f"**{candidate['field_name'].replace('_', ' ').title()}**")
            st.write(candidate["value"])
            st.code(candidate["source_text"], language=None)
            if candidate.get("record_only"):
                st.caption("Recorded text only · this does not recommend or change treatment.")
            if not candidate.get("source_value_matches", True):
                st.error("The proposed value does not exactly match the source. Edit or reject it.")
            key = candidate["candidate_key"]
            if candidate["disposition"] == "abstain":
                st.info("The source says this was not recorded. Nestline will abstain.")
                action = "reject"
            elif candidate.get("conflict_document_keys"):
                action = st.radio(
                    "Decision",
                    ["keep_conflict", "reject"],
                    format_func=lambda value: {
                        "keep_conflict": "Keep both sources as an unresolved conflict",
                        "reject": "Reject this proposal",
                    }[value],
                    key=f"stage4-action-{index}",
                )
            else:
                action = st.radio(
                    "Decision",
                    ["confirm", "edit_and_confirm", "reject"],
                    format_func=lambda value: value.replace("_", " ").title(),
                    key=f"stage4-action-{index}",
                    horizontal=True,
                )
            edited_value = None
            if action == "edit_and_confirm":
                current = candidate["value"]
                edited_value = st.text_input(
                    "Corrected value",
                    value=current if isinstance(current, str) else json.dumps(current),
                    key=f"stage4-edit-{index}",
                )
            decisions.append(ConfirmationDecision(
                candidate_key=key,
                action=action,
                edited_value=edited_value,
            ))
            st.divider()
        confirmed = st.checkbox(
            "I reviewed every field and want to apply these decisions."
        )
        save = st.form_submit_button("Save reviewed document", type="primary")
    if save:
        if not confirmed:
            st.error("Review confirmation is required before anything is applied.")
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
    st.caption(
        "Fictional demo only. Upload one of the watermarked DOC-001 to DOC-008 PDFs "
        "or the allowlisted controlled OCR image."
    )
    gateway = SupabaseDocumentGateway(
        project_url, publishable_key, user_access_token
    )
    uploaded = st.file_uploader(
        "Choose a fictional report",
        type=["pdf", "png", "jpg", "jpeg"],
        accept_multiple_files=False,
    )
    if uploaded and st.button("Extract reviewable fields", type="primary"):
        try:
            _prepare_uploaded_fixture(gateway, UUID(workspace["id"]), uploaded)
            st.success("Extraction finished. Nothing has been applied yet.")
        except (DocumentProcessingError, ValueError) as exc:
            st.error(str(exc))
    _render_candidate_review(gateway, UUID(workspace["id"]))
