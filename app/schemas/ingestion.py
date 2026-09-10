"""Stage 1 contracts for traceable public-knowledge ingestion.

These records describe public evidence only. Private reports and confirmed user
facts use the later personal-document pipeline and must never enter this corpus.
"""

from datetime import date, datetime
from typing import Literal

from pydantic import Field, model_validator

from app.schemas.content import (Applicability, Checksum, ConditionKey, Contract,
                                 Domain, Identifier, Jurisdictions, Stage, Text)

BlockKind = Literal["heading", "paragraph", "list_item", "table"]
DisplaySlot = Literal[
    "hero", "kpi_development", "kpi_timing", "nutrition_focus",
    "movement_focus", "wellbeing_focus", "symptom_education", "preparation",
    "what_may_change", "consider", "avoid", "ask_a_professional", "followup",
]
AdmissionDecision = Literal["rejected", "parse_for_review", "eligible_for_publication"]
CandidateState = Literal["rejected", "review_required", "approved"]
ReviewCheck = Literal[
    "source_anchor", "domain", "stage_and_range", "wording", "jurisdiction",
    "conditions", "development_measurements", "profile_links", "catalogue_links",
    "reuse_and_attribution",
]


class IngestionIssue(Contract):
    code: Identifier
    severity: Literal["info", "warning", "error"]
    message: Text
    source_id: Identifier
    page: int | None = Field(default=None, ge=1)
    locator: str = ""


class SourceAdmission(Contract):
    source_id: Identifier
    decision: AdmissionDecision
    reasons: list[Text] = Field(min_length=1)
    may_store: bool
    may_embed: bool
    may_display: bool
    fixed_quote_only: bool


class SourceArtifact(Contract):
    source_id: Identifier
    canonical_url: Text
    source_version: Text
    document_type: Literal["html", "pdf"]
    retrieved_at: date
    original_sha256: Checksum
    byte_size: int = Field(ge=1)
    parser_name: Text
    parser_version: Text
    ingestion_schema_version: Literal["1.0.0"] = "1.0.0"


class ParsedBlock(Contract):
    block_id: Identifier
    source_id: Identifier
    ordinal: int = Field(ge=0)
    block_kind: BlockKind
    text: Text
    normalized_text: Text
    locator: Text
    heading_path: list[Text] = Field(default_factory=list)
    page: int | None = Field(default=None, ge=1)
    extraction_method: Literal["html_structure", "pdf_text", "ocr"]
    extraction_confidence: float = Field(ge=0, le=1)


class DevelopmentMeasurement(Contract):
    """General source measurement; never a measurement from a user's report."""

    kind: Literal["length", "weight"]
    value: float | None = Field(default=None, gt=0)
    minimum: float | None = Field(default=None, gt=0)
    maximum: float | None = Field(default=None, gt=0)
    unit: Literal["mm", "cm", "m", "in", "g", "kg", "oz", "lb"]
    basis: Literal["general_source_range", "general_source_approximation"]
    variability_notice: Text

    @model_validator(mode="after")
    def has_value_or_range(self):
        if self.value is None and (self.minimum is None or self.maximum is None):
            raise ValueError("measurement requires a value or complete range")
        if self.value is not None and (self.minimum is not None or self.maximum is not None):
            raise ValueError("measurement cannot mix a value and range")
        if self.minimum is not None and self.minimum > self.maximum:
            raise ValueError("measurement range must be ordered")
        return self


class EvidenceCandidate(Contract):
    candidate_id: Identifier
    evidence_id: Identifier
    source_id: Identifier
    artifact_sha256: Checksum
    source_version: Text
    source_locator: Text
    source_block_ids: list[Identifier] = Field(default_factory=list)
    page: int | None = Field(default=None, ge=1)
    heading_path: list[Text] = Field(default_factory=list)
    original_text: Text
    normalized_search_text: Text
    original_text_sha256: Checksum
    source_anchor_verified: bool
    domains: list[Domain] = Field(min_length=1)
    display_slots: list[DisplaySlot] = Field(min_length=1)
    applies_to: Applicability
    jurisdiction: Jurisdictions
    conditions_required: list[ConditionKey] = Field(default_factory=list)
    conditions_excluded: list[ConditionKey] = Field(default_factory=list)
    personal_fact_dependencies: list[Text] = Field(default_factory=list)
    development_measurements: list[DevelopmentMeasurement] = Field(default_factory=list)
    linked_profile_ids: list[Identifier] = Field(default_factory=list)
    linked_fragment_ids: list[Identifier] = Field(default_factory=list)
    linked_catalogue_item_ids: list[Identifier] = Field(default_factory=list)
    state: CandidateState
    review_reasons: list[Text] = Field(default_factory=list)
    candidate_checksum: Checksum

    @model_validator(mode="after")
    def conditions_are_consistent(self):
        if set(self.conditions_required) & set(self.conditions_excluded):
            raise ValueError("candidate condition cannot be required and excluded")
        if self.state == "approved" and (not self.source_anchor_verified or self.review_reasons):
            raise ValueError("approved candidate needs a verified anchor and no review reasons")
        if self.source_anchor_verified and not self.source_block_ids:
            raise ValueError("a verified source anchor must resolve to stored parsed blocks")
        return self


class EmbeddingRecord(Contract):
    chunk_id: Identifier
    evidence_id: Identifier
    source_id: Identifier
    candidate_checksum: Checksum
    provider: Text
    model: Text
    dimensions: int = Field(ge=1)
    vector: list[float] = Field(min_length=1)

    @model_validator(mode="after")
    def dimensions_match(self):
        if len(self.vector) != self.dimensions:
            raise ValueError("embedding dimensions differ from vector length")
        return self


class EvidenceReviewTask(Contract):
    """A pending human decision; its presence never counts as approval."""

    task_id: Identifier
    candidate_id: Identifier
    evidence_id: Identifier
    source_id: Identifier
    candidate_checksum: Checksum
    required_checks: list[ReviewCheck] = Field(min_length=1)
    blocking_reasons: list[Text] = Field(min_length=1)
    status: Literal["pending", "approved", "rejected"] = "pending"
    reviewer: Text | None = None
    reviewed_at: date | None = None

    @model_validator(mode="after")
    def decided_tasks_name_a_reviewer(self):
        if self.status != "pending" and (self.reviewer is None or self.reviewed_at is None):
            raise ValueError("a review decision requires a named reviewer and date")
        if self.status == "pending" and (self.reviewer is not None or self.reviewed_at is not None):
            raise ValueError("a pending review task cannot contain a decision attestation")
        return self


class IngestionDiff(Contract):
    new_candidate_ids: list[Identifier] = Field(default_factory=list)
    unchanged_candidate_ids: list[Identifier] = Field(default_factory=list)
    changed_evidence_ids: list[Identifier] = Field(default_factory=list)
    removed_evidence_ids: list[Identifier] = Field(default_factory=list)
    invalidated_profile_ids: list[Identifier] = Field(default_factory=list)
    invalidated_catalogue_item_ids: list[Identifier] = Field(default_factory=list)
    invalidate_cache_scopes: list[Text] = Field(default_factory=list)


class IngestionRun(Contract):
    run_id: Identifier
    created_at: datetime
    evaluated_at: date = Field(default_factory=date.today)
    dry_run: bool
    artifact: SourceArtifact | None = None
    admission: SourceAdmission
    parsed_block_count: int = Field(ge=0)
    candidates: list[EvidenceCandidate] = Field(default_factory=list)
    review_tasks: list[EvidenceReviewTask] = Field(default_factory=list)
    embeddings: list[EmbeddingRecord] = Field(default_factory=list)
    issues: list[IngestionIssue] = Field(default_factory=list)
    diff: IngestionDiff = Field(default_factory=IngestionDiff)
    outcome: Literal["rejected", "review_required", "publishable", "published"]

    @model_validator(mode="after")
    def layers_agree(self):
        if len({candidate.candidate_id for candidate in self.candidates}) != len(self.candidates):
            raise ValueError("ingestion run contains duplicate candidate IDs")
        if len({candidate.evidence_id for candidate in self.candidates}) != len(self.candidates):
            raise ValueError("ingestion run contains duplicate evidence IDs")
        candidates = {candidate.evidence_id: candidate for candidate in self.candidates}
        embedded = [record.evidence_id for record in self.embeddings]
        if len(embedded) != len(set(embedded)):
            raise ValueError("ingestion run contains duplicate embeddings")
        if any(evidence_id not in candidates or candidates[evidence_id].state != "approved"
               for evidence_id in embedded):
            raise ValueError("embeddings may reference approved candidates only")
        pending = {candidate.candidate_id for candidate in self.candidates
                   if candidate.state == "review_required"}
        tasks = {task.candidate_id for task in self.review_tasks}
        task_ids = {task.task_id for task in self.review_tasks}
        if len(tasks) != len(self.review_tasks) or len(task_ids) != len(self.review_tasks):
            raise ValueError("ingestion run contains duplicate review tasks")
        if pending != tasks:
            raise ValueError("review queue must cover every review-required candidate exactly")
        if self.artifact and any(candidate.source_id != self.artifact.source_id
                                 or candidate.artifact_sha256 != self.artifact.original_sha256
                                 for candidate in self.candidates):
            raise ValueError("candidate provenance differs from the run artifact")
        errors = any(issue.severity == "error" for issue in self.issues)
        if self.outcome in {"publishable", "published"}:
            if (self.artifact is None or self.admission.decision != "eligible_for_publication"
                    or errors or not self.candidates
                    or any(candidate.state != "approved" for candidate in self.candidates)
                    or self.review_tasks):
                raise ValueError("publishable run has unresolved admission, evidence or review state")
            required = set(candidates) if self.admission.may_embed else set()
            if set(embedded) != required:
                raise ValueError("publishable run has missing or forbidden embeddings")
        elif self.outcome == "review_required":
            if self.admission.decision == "rejected" or errors or any(
                    candidate.state == "rejected" for candidate in self.candidates):
                raise ValueError("review-required run cannot contain a rejection condition")
        elif not (self.admission.decision == "rejected" or errors or any(
                candidate.state == "rejected" for candidate in self.candidates)):
            raise ValueError("rejected run needs an explicit rejection condition")
        return self


class CorpusManifest(Contract):
    corpus_version: Identifier
    created_at: datetime
    status: Literal["draft", "published"]
    source_artifacts: list[SourceArtifact] = Field(min_length=1)
    candidate_file_sha256: Checksum
    embedding_file_sha256: Checksum
    embedding_provider: Text
    embedding_model: Text
    evidence_ids: list[Identifier] = Field(min_length=1)
    profile_ids: list[Identifier] = Field(default_factory=list)
    limitations: list[Text] = Field(min_length=1)
