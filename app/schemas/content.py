"""Stage 0 content contracts; schema validity is not clinical approval."""

from __future__ import annotations

from datetime import date
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Identifier = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$")]
Checksum = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]
Stage = Literal["possible_pregnancy", "pregnancy", "postpartum"]
Status = Literal["draft", "reviewed", "published", "superseded"]
Domain = Literal["journey", "nutrition", "movement", "wellbeing", "symptoms", "preparation", "followup"]
Jurisdictions = Annotated[list[Text], Field(min_length=1)]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, validate_assignment=True)


class Review(Contract):
    """A real person's recorded review; passing validation is not a review."""
    reviewer: Text
    reviewed_at: date
    kind: Literal["content_reviewed", "clinician_reviewed"]
    notes: Text


class Applicability(Contract):
    """The complete time interval supported by a passage, not a guessed week."""
    stage: Stage
    unit: Literal["week", "day", "none"]
    start: int | None = None
    end: int | None = None

    @model_validator(mode="after")
    def valid_range(self) -> Self:
        if self.stage == "possible_pregnancy":
            if self.unit != "none" or self.start is not None or self.end is not None:
                raise ValueError("possible pregnancy must not assert a week or day")
            return self
        if self.start is None or self.end is None or self.start > self.end:
            raise ValueError("a complete ordered applicability range is required")
        if self.stage == "pregnancy":
            valid = self.unit == "week" and 1 <= self.start <= self.end <= 42
        elif self.unit == "week":
            valid = 1 <= self.start <= self.end <= 12
        else:
            valid = self.unit == "day" and 0 <= self.start <= self.end <= 7
        if not valid:
            raise ValueError("applicability is outside the canonical journey scope")
        return self

    def covers(self, other: Applicability) -> bool:
        """Day overlays and weeks stay separate; no implicit day/week conversion."""
        if self.stage != other.stage or self.unit != other.unit:
            return False
        if self.unit == "none":
            return True
        return self.start <= other.start <= other.end <= self.end


class SourceRecord(Contract):
    """Permission and provenance for one version of selected source material."""
    source_id: Identifier
    title: Text
    publisher: Text
    canonical_url: Annotated[str, StringConstraints(pattern=r"^https://[^\s]+$")]
    jurisdiction: Jurisdictions
    document_type: Literal["html", "pdf", "index"]
    topics: Annotated[list[Domain], Field(min_length=1)]
    evidence_lane: Literal["guideline", "weekly_profile", "safety"]
    status: Literal["candidate", "approved_for_capstone", "excluded", "superseded"] = "candidate"
    publication_date: date | None = None
    version_or_last_update: str = ""
    last_checked_at: date | None = None
    reuse_status: Literal["unverified", "permitted", "restricted"] = "unverified"
    allowed_use: list[Literal["store", "embed", "display"]] = Field(default_factory=list)
    license_or_reuse_note: str = ""
    prohibited_inferences: Text
    review: Review | None = None
    content_checksum: Checksum | None = None
    supersedes_source_id: Identifier | None = None
    journey_stages: list[Stage] = Field(default_factory=list)
    selected_sections: list[Text] = Field(default_factory=list)
    snapshot_path: str = ""
    delivery_mode: Literal["retrievable", "fixed_quote"] = "retrievable"
    attribution_text: str = ""
    max_quote_sections: Annotated[int, Field(ge=1)] | None = None

    @model_validator(mode="after")
    def approved_metadata(self) -> Self:
        if self.delivery_mode == "fixed_quote" and "embed" in self.allowed_use:
            raise ValueError("fixed quotations cannot be granted embedding permission")
        if self.delivery_mode == "fixed_quote":
            if not self.attribution_text.strip() or self.max_quote_sections is None:
                raise ValueError("fixed quotations require attribution and an explicit excerpt limit")
            if len(self.selected_sections) > self.max_quote_sections:
                raise ValueError("selected quotations exceed the source permission limit")
        if self.status == "approved_for_capstone":
            required = {"store", "display"} if self.delivery_mode == "fixed_quote" else {"store", "embed", "display"}
            if self.reuse_status != "permitted" or set(self.allowed_use) != required:
                raise ValueError("approval requires documented permissions for the selected delivery mode")
            if not all((self.version_or_last_update.strip(), self.last_checked_at,
                        self.license_or_reuse_note.strip(), self.review, self.content_checksum,
                        self.journey_stages, self.selected_sections, self.snapshot_path.strip())):
                raise ValueError("approval requires version, date, permission, review, checksum, stages, sections and snapshot")
            if self.document_type == "index":
                raise ValueError("a discovery index cannot be an approved evidence source")
        return self


class Localisation(Contract):
    """An explicit proposed adoption; the publisher's country remains unchanged."""
    source_jurisdiction: Jurisdictions
    target_jurisdiction: Jurisdictions
    category: Literal["basic_biology", "general_education"]
    rationale: Text
    review: Review | None = None


class EvidenceSpan(Contract):
    """Exact selected source text. The fragment below contains our draft wording."""
    evidence_id: Identifier
    source_id: Identifier
    source_version: Text
    source_checksum: Checksum
    locator: Text
    page: Annotated[int, Field(ge=1)] | None = None
    text: Text
    text_checksum: Checksum
    applies_to: Applicability
    jurisdiction: Jurisdictions
    status: Status = "draft"
    review: Review | None = None
    applicability_note: str = ""
    localisation: Localisation | None = None


class GuidanceFragment(Contract):
    """One reusable claim; conditions must survive retrieval and composition."""
    fragment_id: Identifier
    domain: Domain
    text: Text
    applies_to: Applicability
    jurisdiction: Jurisdictions
    evidence_span_ids: Annotated[list[Identifier], Field(min_length=1)]
    status: Status = "draft"
    review: Review | None = None
    conditions_required: list[Text] = Field(default_factory=list)
    conditions_excluded: list[Text] = Field(default_factory=list)
    presentation: Literal["paraphrase", "quotation"] = "paraphrase"


class Hero(Contract):
    title: str = ""
    development_evidence_ids: list[Identifier] = Field(default_factory=list)
    visual_asset_id: Identifier | None = None


class CardSlots(Contract):
    """Values are fragment IDs, never uncited free-form generated prose."""

    what_may_change: list[Identifier] = Field(default_factory=list)
    nutrition_focus: list[Identifier] = Field(default_factory=list)
    movement_focus: list[Identifier] = Field(default_factory=list)
    wellbeing_focus: list[Identifier] = Field(default_factory=list)
    symptom_education: list[Identifier] = Field(default_factory=list)
    preparation: list[Identifier] = Field(default_factory=list)
    consider: list[Identifier] = Field(default_factory=list)
    avoid: list[Identifier] = Field(default_factory=list)
    ask_a_professional: list[Identifier] = Field(default_factory=list)


class WeeklyProfile(Contract):
    """An assembly of evidence links. Empty slots mean missing content, not advice."""
    profile_id: Identifier
    applies_to: Applicability
    status: Status = "draft"
    hero: Hero = Field(default_factory=Hero)
    card_slots: CardSlots = Field(default_factory=CardSlots)
    guidance_fragment_ids: list[Identifier] = Field(default_factory=list)
    source_evidence_ids: list[Identifier] = Field(default_factory=list)
    jurisdiction: Jurisdictions = Field(default_factory=lambda: ["IN"])
    review: Review | None = None
    version: Text = "1.0.0"
    content_priority: Literal["representative", "coverage_shell", "day_overlay"]
    publication_blockers: list[Text] = Field(default_factory=list)
    slot_notes: dict[str, Text] = Field(default_factory=dict)

    @model_validator(mode="after")
    def identity_matches_time(self) -> Self:
        scope = self.applies_to
        if scope.stage == "possible_pregnancy":
            expected = "PC00"
        elif scope.start != scope.end:
            raise ValueError("profiles represent a single week/day, not a range")
        elif scope.stage == "pregnancy":
            expected = f"P{scope.start:02d}"
        elif scope.unit == "day":
            expected = f"PPD{scope.start}"
        else:
            expected = f"PP{scope.start:02d}"
        if self.profile_id != expected:
            raise ValueError(f"profile identity must be {expected} for this timing")
        return self


class ContentBundle(Contract):
    schema_version: Literal["1.0.0"] = "1.0.0"
    sources: list[SourceRecord]
    evidence: list[EvidenceSpan]
    fragments: list[GuidanceFragment]
    profiles: list[WeeklyProfile]
