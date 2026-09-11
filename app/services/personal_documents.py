"""Stage 4 private-document boundary, parser, and confirmation gateway.

Document bytes and extracted text are untrusted input. This module never gives a
document access to tools, policy, or a database credential. Extraction creates
proposals only; the database committer activates explicitly reviewed facts.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path, PurePath
import re
from time import perf_counter
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from uuid import UUID

import fitz
from PIL import Image, UnidentifiedImageError

from app.schemas.documents import (
    CandidateFactType,
    DocumentCandidate,
    DocumentExtractionPacket,
    DocumentKind,
    DocumentReviewRequest,
    DocumentReviewResult,
    ExtractionProviderTrace,
    MAX_DOCUMENT_BYTES,
    ParsedPage,
    SourceSpan,
    UploadValidationResult,
)


ALLOWED_MEDIA_TYPES = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}
MISSING_VALUES = {"not supplied", "not recorded", "unknown", "not provided"}
INJECTION_PATTERNS = (
    re.compile(r"ignore\s+(?:all\s+)?(?:prior|previous|system)\s+instructions", re.I),
    re.compile(r"(?:reveal|publish|export)\s+(?:all|every)\b", re.I),
    re.compile(r"(?:call|use|invoke)\s+(?:the\s+)?(?:tool|api|database)", re.I),
)
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_REGISTRY_PATH = (
    REPOSITORY_ROOT / "data/synthetic/stage4_fixture_registry.json"
)


class DocumentProcessingError(RuntimeError):
    """A safe, user-displayable Stage 4 processing failure."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ScanResult:
    status: str
    provider: str
    version: str


@dataclass(frozen=True)
class FictionalFixture:
    """One immutable, repository-owned file allowed in the public demo."""

    fixture_id: str
    label: str
    path: Path
    media_type: str
    sha256: str
    expected_subject: str
    ocr_truth_path: Path | None = None


def load_fictional_fixture_registry() -> list[FictionalFixture]:
    """Load the demo allowlist and prove every registered digest still matches."""

    payload = json.loads(FIXTURE_REGISTRY_PATH.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "stage4-fictional-fixture-registry-v1":
        raise DocumentProcessingError(
            "fixture_registry", "The fictional fixture registry version is invalid."
        )
    fixtures: list[FictionalFixture] = []
    seen_ids: set[str] = set()
    for item in payload.get("fixtures", []):
        fixture_id = str(item.get("id", "")).strip()
        relative_path = Path(str(item.get("relative_path", "")))
        path = (REPOSITORY_ROOT / relative_path).resolve()
        if (
            not fixture_id
            or fixture_id in seen_ids
            or not path.is_relative_to(REPOSITORY_ROOT)
            or not path.is_file()
        ):
            raise DocumentProcessingError(
                "fixture_registry", "The fictional fixture registry contains an invalid entry."
            )
        expected_digest = str(item.get("sha256", "")).casefold()
        if sha256(path.read_bytes()).hexdigest() != expected_digest:
            raise DocumentProcessingError(
                "fixture_registry",
                f"The registered digest for {fixture_id} does not match its file.",
            )
        ocr_truth_path = None
        if item.get("ocr_truth_path"):
            ocr_truth_path = (
                REPOSITORY_ROOT / Path(str(item["ocr_truth_path"]))
            ).resolve()
            if (
                not ocr_truth_path.is_relative_to(REPOSITORY_ROOT)
                or not ocr_truth_path.is_file()
            ):
                raise DocumentProcessingError(
                    "fixture_registry",
                    f"The registered OCR truth for {fixture_id} is unavailable.",
                )
        fixtures.append(FictionalFixture(
            fixture_id=fixture_id,
            label=str(item["label"]),
            path=path,
            media_type=str(item["media_type"]),
            sha256=expected_digest,
            expected_subject=str(item["expected_subject"]),
            ocr_truth_path=ocr_truth_path,
        ))
        seen_ids.add(fixture_id)
    if not fixtures:
        raise DocumentProcessingError(
            "fixture_registry", "No fictional demo fixtures are registered."
        )
    return fixtures


class MalwareScanner(Protocol):
    def scan(self, data: bytes, *, filename: str, media_type: str) -> ScanResult: ...


class OcrAdapter(Protocol):
    def extract_pages(self, data: bytes, *, media_type: str) -> list[str]: ...


@dataclass(frozen=True)
class UnavailableMalwareScanner:
    """Fail closed until a deployable scanning policy is selected."""

    def scan(self, data: bytes, *, filename: str, media_type: str) -> ScanResult:
        del data, filename, media_type
        raise DocumentProcessingError(
            "scan_unavailable",
            "Medical-document scanning is not configured, so this upload was not accepted.",
        )


@dataclass(frozen=True)
class FictionalFixtureScanner:
    """Development-only exact-hash allowlist for repository-owned fixtures."""

    allowed_sha256: frozenset[str] = frozenset()

    def scan(self, data: bytes, *, filename: str, media_type: str) -> ScanResult:
        del filename, media_type
        digest = sha256(data).hexdigest()
        if digest not in self.allowed_sha256:
            raise DocumentProcessingError(
                "scan_unavailable",
                "Only exact, registered fictional demo files are accepted in this build.",
            )
        return ScanResult("fixture_verified", "fictional-fixture-allowlist", "v2")


def _safe_filename(filename: str) -> str:
    name = PurePath(filename.strip()).name
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip(".-")
    if not name or len(name) > 160:
        raise DocumentProcessingError("invalid_filename", "The filename is not supported.")
    return name


def _media_type(filename: str, claimed_media_type: str, data: bytes) -> str:
    suffix = Path(filename).suffix.casefold()
    expected = ALLOWED_MEDIA_TYPES.get(suffix)
    if expected is None:
        raise DocumentProcessingError(
            "unsupported_format", "Use a PDF, PNG, JPG, or JPEG file."
        )
    claimed = claimed_media_type.split(";", 1)[0].strip().casefold()
    if claimed != expected:
        raise DocumentProcessingError(
            "media_type_mismatch", "The filename and declared file type do not match."
        )
    signatures = {
        "application/pdf": data.startswith(b"%PDF-"),
        "image/png": data.startswith(b"\x89PNG\r\n\x1a\n"),
        "image/jpeg": data.startswith(b"\xff\xd8\xff"),
    }
    if not signatures[expected]:
        raise DocumentProcessingError(
            "signature_mismatch", "The file contents do not match the declared type."
        )
    return expected


def _pdf_page_count(data: bytes) -> int:
    try:
        with fitz.open(stream=data, filetype="pdf") as document:
            if document.needs_pass:
                raise DocumentProcessingError(
                    "locked", "Remove the PDF password before uploading it."
                )
            if document.page_count < 1 or document.page_count > 100:
                raise DocumentProcessingError(
                    "page_count", "Documents must contain between 1 and 100 pages."
                )
            for page in document:
                page.get_text()
            return document.page_count
    except DocumentProcessingError:
        raise
    except Exception as exc:
        raise DocumentProcessingError("corrupt", "The PDF cannot be opened.") from exc


def _image_page_count(data: bytes) -> int:
    try:
        from io import BytesIO

        with Image.open(BytesIO(data)) as image:
            image.verify()
        return 1
    except (UnidentifiedImageError, OSError) as exc:
        raise DocumentProcessingError("corrupt", "The image cannot be opened.") from exc


def verify_document_identity(
    *,
    expected_subject: str | None,
    subject_as_written: str | None,
    fixture_bound_subject: str | None,
    fixture_is_verified: bool,
) -> str:
    """Require an exact subject match or a trusted exact-fixture binding."""

    if expected_subject is None:
        return "not_required"
    expected = expected_subject.strip().casefold()
    detected = (subject_as_written or "").strip()
    if detected:
        if detected.casefold() != expected:
            raise DocumentProcessingError(
                "wrong_person",
                "The name in this document does not match the selected fictional profile.",
            )
        return "matched_document_subject"
    bound = (fixture_bound_subject or "").strip()
    if fixture_is_verified and bound:
        if bound.casefold() != expected:
            raise DocumentProcessingError(
                "wrong_person",
                "The registered fixture belongs to another fictional profile.",
            )
        return "verified_fixture_binding"
    raise DocumentProcessingError(
        "identity_unverified",
        "Nestline could not verify that this document belongs to the selected profile.",
    )

def validate_upload(
    data: bytes,
    *,
    filename: str,
    claimed_media_type: str,
    scanner: MalwareScanner,
    expected_subject: str | None = None,
    subject_as_written: str | None = None,
    fixture_bound_subject: str | None = None,
) -> UploadValidationResult:
    if not data:
        raise DocumentProcessingError("empty", "The selected file is empty.")
    if len(data) > MAX_DOCUMENT_BYTES:
        raise DocumentProcessingError("oversize", "The file is larger than 10 MiB.")
    safe_name = _safe_filename(filename)
    media_type = _media_type(safe_name, claimed_media_type, data)
    page_count = (
        _pdf_page_count(data)
        if media_type == "application/pdf"
        else _image_page_count(data)
    )
    scan = scanner.scan(data, filename=safe_name, media_type=media_type)
    identity_status = verify_document_identity(
        expected_subject=expected_subject,
        subject_as_written=subject_as_written,
        fixture_bound_subject=fixture_bound_subject,
        fixture_is_verified=(
            scan.status == "fixture_verified"
            and scan.provider == "fictional-fixture-allowlist"
        ),
    )
    return UploadValidationResult(
        original_filename=filename,
        safe_filename=safe_name,
        media_type=media_type,
        byte_size=len(data),
        sha256=sha256(data).hexdigest(),
        page_count=page_count,
        scan_status=scan.status,
        scan_provider=scan.provider,
        scan_version=scan.version,
        expected_subject=expected_subject,
        subject_as_written=subject_as_written,
        identity_status=identity_status,
    )


def parse_document(
    data: bytes,
    *,
    media_type: str,
    ocr_adapter: OcrAdapter | None = None,
) -> tuple[list[ParsedPage], list[fitz.Page] | None]:
    page_texts: list[str] = []
    fitz_pages: list[fitz.Page] | None = None
    if media_type == "application/pdf":
        document = fitz.open(stream=data, filetype="pdf")
        if document.needs_pass:
            document.close()
            raise DocumentProcessingError("locked", "Remove the PDF password before uploading it.")
        # Keep the document alive only while coordinates are derived by the caller.
        fitz_pages = [page for page in document]
        page_texts = [page.get_text().strip() for page in fitz_pages]
        if all(page_texts):
            method = "embedded_text"
        else:
            document.close()
            fitz_pages = None
            if ocr_adapter is None:
                raise DocumentProcessingError(
                    "ocr_required", "This image-based document needs the configured OCR adapter."
                )
            page_texts = ocr_adapter.extract_pages(data, media_type=media_type)
            method = "ocr"
    else:
        if ocr_adapter is None:
            raise DocumentProcessingError(
                "ocr_required", "Image uploads need the configured OCR adapter."
            )
        page_texts = ocr_adapter.extract_pages(data, media_type=media_type)
        method = "ocr"
    if not page_texts or any(not text.strip() for text in page_texts):
        raise DocumentProcessingError("no_text", "No reviewable text could be extracted.")
    pages = [
        ParsedPage(
            page=index,
            text=text,
            extraction_method=method,
            text_sha256=sha256(text.encode("utf-8")).hexdigest(),
        )
        for index, text in enumerate(page_texts, start=1)
    ]
    return pages, fitz_pages


FIELD_TYPES: dict[str, CandidateFactType] = {
    "persona": CandidateFactType.SUBJECT,
    "pregnancy_week": CandidateFactType.JOURNEY_TIMING,
    "estimated_due_date": CandidateFactType.JOURNEY_TIMING,
    "delivery_date": CandidateFactType.JOURNEY_TIMING,
    "current_journey": CandidateFactType.JOURNEY_TIMING,
    "delivery_setting": CandidateFactType.OTHER,
    "delivery_type": CandidateFactType.OTHER,
    "feeding_method": CandidateFactType.OTHER,
    "discharge_instruction": CandidateFactType.OTHER,
    "reported_allergy": CandidateFactType.ALLERGY,
    "dietary_preference": CandidateFactType.OTHER,
    "workspace": CandidateFactType.OTHER,
    "new_allergy_information": CandidateFactType.ALLERGY,
    "condition": CandidateFactType.CONDITION,
    "prescriber": CandidateFactType.CLINICIAN,
    "medicine_name": CandidateFactType.MEDICATION,
    "recorded_dose": CandidateFactType.MEDICATION_INSTRUCTION,
    "recorded_frequency": CandidateFactType.MEDICATION_INSTRUCTION,
    "route": CandidateFactType.MEDICATION_INSTRUCTION,
    "recorded_instruction": CandidateFactType.RESTRICTION,
    "instruction_scope": CandidateFactType.RESTRICTION,
    "new_restriction": CandidateFactType.RESTRICTION,
    "followup_date": CandidateFactType.FOLLOW_UP,
    "followup_reason": CandidateFactType.FOLLOW_UP,
    "task_dedupe_key": CandidateFactType.FOLLOW_UP,
    "haemoglobin": CandidateFactType.TEST_RESULT,
    "specimen": CandidateFactType.TEST_RESULT,
    "reference_range": CandidateFactType.TEST_RESULT,
    "interpretation": CandidateFactType.TEST_RESULT,
    "conflicts_with": CandidateFactType.OTHER,
}


def _document_kind(text: str) -> DocumentKind:
    title = text.casefold()
    for phrase, kind in (
        ("pregnancy intake", DocumentKind.INTAKE_SUMMARY),
        ("laboratory report", DocumentKind.LAB_REPORT),
        ("medication instruction", DocumentKind.MEDICATION_NOTE),
        ("movement instruction", DocumentKind.MOVEMENT_NOTE),
        ("conflicting instruction", DocumentKind.MOVEMENT_NOTE),
        ("follow-up instruction", DocumentKind.FOLLOW_UP),
        ("postpartum discharge", DocumentKind.DISCHARGE_SUMMARY),
        ("visit summary", DocumentKind.VISIT_SUMMARY),
    ):
        if phrase in title:
            return kind
    return DocumentKind.OTHER


def _coordinates(page: fitz.Page | None, exact_text: str) -> list[list[float]]:
    if page is None:
        return []
    return [[rect.x0, rect.y0, rect.x1, rect.y1] for rect in page.search_for(exact_text)]


def extract_fixture_candidates(
    pages: list[ParsedPage],
    *,
    document_sha256: str,
    fitz_pages: list[fitz.Page] | None = None,
) -> DocumentExtractionPacket:
    """Deterministic golden extractor for the controlled fictional package.

    Production OCR/model extraction implements the same packet contract. This
    parser exists so confirmation, security, conflicts and state changes can be
    evaluated without treating a model output as ground truth.
    """

    started = perf_counter()
    candidates: list[DocumentCandidate] = []
    suspicious: list[str] = []
    subjects: list[str] = []
    combined = "\n".join(page.text for page in pages)
    for page_index, parsed in enumerate(pages):
        cursor = 0
        lines = parsed.text.splitlines(keepends=True)
        for line_number, raw_line in enumerate(lines, start=1):
            exact = raw_line.rstrip("\r\n")
            start = cursor
            cursor += len(raw_line)
            if any(pattern.search(exact) for pattern in INJECTION_PATTERNS):
                suspicious.append(exact)
                continue
            if ":" not in exact:
                continue
            field_name, raw_value = exact.split(":", 1)
            field_name = field_name.strip().casefold()
            value = raw_value.strip()
            fact_type = FIELD_TYPES.get(field_name)
            if fact_type is None:
                continue
            if field_name == "persona":
                subjects.append(value)
            missing = value.casefold() in MISSING_VALUES
            record_only = fact_type in {
                CandidateFactType.MEDICATION,
                CandidateFactType.MEDICATION_INSTRUCTION,
            }
            conflict_keys = [value] if field_name == "conflicts_with" else []
            source_value_matches = value.casefold() in exact.casefold()
            candidates.append(DocumentCandidate(
                candidate_key=f"p{page_index + 1}-l{line_number}-{field_name}",
                field_name=field_name,
                fact_type=fact_type,
                value=value,
                source=SourceSpan(
                    page=page_index + 1,
                    exact_text=exact,
                    start=start,
                    end=start + len(exact),
                    line=line_number,
                    coordinates=_coordinates(
                        fitz_pages[page_index] if fitz_pages else None, exact
                    ),
                    coordinate_system=(
                        "PDF points, top-left origin" if fitz_pages else None
                    ),
                ),
                confidence=0.0 if missing else 1.0,
                completeness="missing" if missing else "complete",
                disposition="abstain" if missing else "extract_verbatim",
                record_only=record_only,
                source_value_matches=source_value_matches,
                conflict_document_keys=conflict_keys,
            ))
    if len(subjects) > 1:
        if fitz_pages:
            fitz_pages[0].parent.close()
        raise DocumentProcessingError(
            "multiple_subjects",
            "The document contains more than one subject identity and needs manual review.",
        )
    subject = subjects[0] if subjects else None
    if fitz_pages:
        fitz_pages[0].parent.close()
    return DocumentExtractionPacket(
        document_sha256=document_sha256,
        document_kind=_document_kind(combined),
        classification_confidence=1.0,
        subject_as_written=subject,
        fictional="FICTIONAL DEMO DATA" in combined,
        pages=pages,
        candidates=candidates,
        untrusted_instruction_text=suspicious,
        provider_trace=ExtractionProviderTrace(
            provider="deterministic",
            model="canonical-fixture-parser-v1",
            latency_ms=round((perf_counter() - started) * 1000),
        ),
    )


def extraction_payload(packet: DocumentExtractionPacket) -> dict[str, Any]:
    chunks = [
        {
            "page": page.page,
            "source_span": {"start": 0, "end": len(page.text)},
            "text": page.text,
            "text_sha256": page.text_sha256,
            "extraction_method": page.extraction_method,
        }
        for page in packet.pages
    ]
    candidates = [candidate.model_dump(mode="json") for candidate in packet.candidates]
    body = {
        "schema_version": packet.schema_version,
        "document_sha256": packet.document_sha256,
        "document_kind": packet.document_kind.value,
        "classification_confidence": packet.classification_confidence,
        "subject_as_written": packet.subject_as_written,
        "fictional": packet.fictional,
        "untrusted_instruction_text": packet.untrusted_instruction_text,
        "provider_trace": packet.provider_trace.model_dump(mode="json"),
        "chunks": chunks,
        "candidates": candidates,
    }
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
    body["payload_sha256"] = sha256(canonical.encode("utf-8")).hexdigest()
    return body


@dataclass
class SupabaseDocumentGateway:
    project_url: str
    publishable_key: str
    user_access_token: str
    timeout_seconds: float = 30.0

    def _request(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any] | list[Any] | None = None,
        raw_data: bytes | None = None,
        content_type: str = "application/json",
        prefer: str | None = None,
    ) -> Any:
        headers = {
            "apikey": self.publishable_key,
            "Authorization": f"Bearer {self.user_access_token}",
            "Content-Type": content_type,
        }
        if prefer:
            headers["Prefer"] = prefer
        data = raw_data
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
        request = Request(
            f"{self.project_url.rstrip('/')}{path}", data=data, method=method, headers=headers
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read()
        except HTTPError as exc:
            # Never include response bodies because they may echo private text.
            raise DocumentProcessingError(
                "storage_request_failed",
                f"The private-document service returned HTTP {exc.code}.",
            ) from exc
        except URLError as exc:
            raise DocumentProcessingError(
                "storage_unavailable", "The private-document service could not be reached."
            ) from exc
        return json.loads(raw) if raw else None

    def find_document_by_hash(
        self, workspace_id: UUID, document_sha256: str
    ) -> UUID | None:
        query = urlencode({
            "workspace_id": f"eq.{workspace_id}",
            "sha256": f"eq.{document_sha256}",
            "select": "id",
            "limit": "1",
        })
        value = self._request("GET", f"/rest/v1/private_documents?{query}")
        if not isinstance(value, list):
            raise DocumentProcessingError("metadata_response", "Invalid document lookup response.")
        if not value:
            return None
        try:
            return UUID(value[0]["id"])
        except (KeyError, TypeError, ValueError) as exc:
            raise DocumentProcessingError(
                "metadata_response", "The document lookup returned an invalid ID."
            ) from exc

    def upload(
        self,
        workspace_id: UUID,
        validation: UploadValidationResult,
        data: bytes,
    ) -> str:
        object_path = f"{workspace_id}/{validation.sha256}/{validation.safe_filename}"
        self._request(
            "POST",
            "/storage/v1/object/medical-documents/" + quote(object_path, safe="/"),
            raw_data=data,
            content_type=validation.media_type,
        )
        return object_path

    def create_metadata(
        self,
        workspace_id: UUID,
        object_path: str,
        validation: UploadValidationResult,
    ) -> UUID:
        value = self._request(
            "POST",
            "/rest/v1/private_documents",
            payload={
                "workspace_id": str(workspace_id),
                "storage_object_path": object_path,
                "original_filename": validation.original_filename,
                "media_type": validation.media_type,
                "byte_size": validation.byte_size,
                "sha256": validation.sha256,
                "contains_real_medical_data": False,
                "fixture_document_key": (
                    match.group(0) if (match := re.search(r"DOC-[0-9]{3}", validation.safe_filename.upper())) else None
                ),
            },
            prefer="return=representation",
        )
        try:
            return UUID(value[0]["id"])
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise DocumentProcessingError(
                "metadata_response", "The document service returned invalid metadata."
            ) from exc

    def upload_and_register(
        self,
        workspace_id: UUID,
        validation: UploadValidationResult,
        data: bytes,
    ) -> tuple[UUID, bool]:
        """Return one logical document ID and whether a new upload was created."""

        existing = self.find_document_by_hash(workspace_id, validation.sha256)
        if existing is not None:
            return existing, False
        object_path = self.upload(workspace_id, validation, data)
        try:
            return self.create_metadata(workspace_id, object_path, validation), True
        except Exception:
            # Avoid an orphaned private object when metadata registration fails.
            self._request(
                "DELETE",
                "/storage/v1/object/medical-documents",
                payload={"prefixes": [object_path]},
            )
            raise

    def record_extraction(
        self,
        workspace_id: UUID,
        document_id: UUID,
        validation: UploadValidationResult,
        packet: DocumentExtractionPacket,
    ) -> int:
        body = extraction_payload(packet)
        value = self._request(
            "POST",
            "/rest/v1/rpc/record_document_extraction",
            payload={
                "requested_workspace_id": str(workspace_id),
                "requested_document_id": str(document_id),
                "requested_document_sha256": validation.sha256,
                "requested_scan_status": validation.scan_status,
                "requested_scan_provider": validation.scan_provider,
                "requested_scan_version": validation.scan_version,
                "requested_payload_sha256": body.pop("payload_sha256"),
                "requested_extraction": body,
            },
        )
        try:
            return int(value["review_version"])
        except (KeyError, TypeError, ValueError) as exc:
            raise DocumentProcessingError(
                "extraction_response", "The document service returned an invalid review version."
            ) from exc

    def list_candidates(self, workspace_id: UUID, document_id: UUID) -> list[dict[str, Any]]:
        query = urlencode({
            "workspace_id": f"eq.{workspace_id}",
            "document_id": f"eq.{document_id}",
            "select": "*",
            "order": "source_page.asc,candidate_key.asc",
        })
        value = self._request("GET", f"/rest/v1/document_facts?{query}")
        if not isinstance(value, list):
            raise DocumentProcessingError("candidate_response", "Invalid candidate response.")
        return value

    def commit_review(self, request: DocumentReviewRequest) -> DocumentReviewResult:
        decisions = [item.model_dump(mode="json") for item in request.decisions]
        body_without_hash = {
            "requested_workspace_id": str(request.workspace_id),
            "requested_document_id": str(request.document_id),
            "expected_review_version": request.expected_review_version,
            "requested_submission_key": request.submission_key,
            "requested_decisions": decisions,
        }
        canonical = json.dumps(body_without_hash, sort_keys=True, separators=(",", ":"))
        value = self._request(
            "POST",
            "/rest/v1/rpc/commit_document_review",
            payload={
                **body_without_hash,
                "requested_payload_sha256": sha256(canonical.encode("utf-8")).hexdigest(),
            },
        )
        return DocumentReviewResult.model_validate_json(json.dumps(value))
