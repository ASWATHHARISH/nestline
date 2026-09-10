"""Governed Stage 1 ingestion for public HTML and PDF knowledge."""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timezone
from hashlib import sha256
import re

import bs4
import fitz

from app.schemas.content import ContentBundle, EvidenceSpan, SourceRecord
from app.schemas.foundation import CatalogueItem
from app.schemas.ingestion import (DevelopmentMeasurement, EmbeddingRecord, EvidenceCandidate,
                                   EvidenceReviewDecision, EvidenceReviewTask, IngestionDiff, IngestionIssue,
                                   IngestionRun, ParsedBlock, SourceAdmission, SourceArtifact)
from app.services.content_validation import validate_bundle
from app.services.embeddings import EmbeddingProvider
from app.services.foundation import fingerprint, review_subject, source_freshness
from app.services.public_parsers import (OcrProvider, PARSER_VERSION, normalize_text,
                                         parse_html, parse_pdf)


CONDITION_FACTS = {
    "breastfeeding": "feeding_status",
    "early_home_recovery": "postpartum_recovery_context",
    "professional_care_for_postpartum_depression": "mental_health_care_context",
    "complicated_delivery_or_caesarean": "delivery_history",
    "uncomplicated_delivery": "delivery_history",
    "feels_ready_for_gentle_activity": "user_reported_activity_readiness",
    "exercise_clearance": "clinician_activity_instruction",
    "movement_restriction": "clinician_activity_instruction",
    "current_warning_symptom": "current_symptom_report",
    "home_birth": "delivery_place",
    "facility_birth": "delivery_place",
    "pregnancy_confirmed": "pregnancy_confirmation",
    "consents_to_wellbeing_activity": "user_consent",
    "persistent_emotional_concern": "current_emotional_concern",
    "trusted_support_available": "support_preference",
}

DOMAIN_DEPENDENCIES = {
    "nutrition": {"allergies", "dietary_restrictions", "medical_history"},
    "movement": {"medical_history", "clinician_activity_instruction", "current_symptom_report"},
    "wellbeing": {"mental_health_history", "current_emotional_concern", "user_consent"},
    "symptoms": {"current_symptom_report", "medical_history"},
    "preparation": {"medical_history", "medications_and_supplements", "next_appointment"},
    "followup": {"next_appointment", "delivery_history"},
    "journey": {"confirmed_journey_timing"},
}

DOMAIN_SLOT = {
    "nutrition": "nutrition_focus", "movement": "movement_focus", "wellbeing": "wellbeing_focus",
    "symptoms": "symptom_education", "preparation": "preparation", "followup": "followup",
    "journey": "kpi_development",
}

# This is a structured candidate copied from an exact selected passage, not a
# model guess or an ultrasound value. The checksum makes any text edit invalidate
# the annotation and send the record back for correction.
MEASUREMENT_ANNOTATIONS = {
    "E-P10-DEVELOPMENT": {
        "text_checksum": "bd52cfba5ca086bcbd57cd987d5c3167bf7ea8032f00d5f83d14ae345c7004ee",
        "measurements": [{"kind": "length", "value": 2.5, "unit": "cm",
                          "basis": "general_source_approximation",
                          "variability_notice": "General source approximation; never replace a measurement from the user's report."}],
    },
}


def development_measurements_for(evidence: EvidenceSpan) -> tuple[list[DevelopmentMeasurement], bool]:
    annotation = MEASUREMENT_ANNOTATIONS.get(evidence.evidence_id)
    if annotation is None:
        return [], True
    if evidence.text_checksum != annotation["text_checksum"]:
        return [], False
    return [DevelopmentMeasurement.model_validate(value) for value in annotation["measurements"]], True


def admission_for(source: SourceRecord, today: date) -> SourceAdmission:
    reasons = []
    if source.status in {"excluded", "superseded"}:
        reasons.append(f"source status is {source.status}")
    if source.document_type == "index":
        reasons.append("discovery indexes cannot supply evidence")
    if not source.version_or_last_update.strip():
        reasons.append("source version is missing")
    if source.reuse_status != "permitted" or "store" not in source.allowed_use:
        reasons.append("documented storage permission is absent")
    if reasons:
        decision = "rejected"
    else:
        publication_reasons = source_freshness(source, today)
        if source.status != "approved_for_capstone":
            publication_reasons.append("actual source approval is pending")
        if source.review is None:
            publication_reasons.append("named source review is pending")
        if publication_reasons:
            reasons.extend(publication_reasons)
            decision = "parse_for_review"
        else:
            reasons.append("source permission, currency and named review allow publication checks")
            decision = "eligible_for_publication"
    return SourceAdmission(source_id=source.source_id, decision=decision, reasons=list(dict.fromkeys(reasons)),
                           may_store="store" in source.allowed_use and source.reuse_status == "permitted",
                           may_embed="embed" in source.allowed_use and source.reuse_status == "permitted"
                           and source.delivery_mode == "retrievable",
                           may_display="display" in source.allowed_use and source.reuse_status == "permitted",
                           fixed_quote_only=source.delivery_mode == "fixed_quote")


CATALOGUE_SLOT = {
    "food": "nutrition_focus", "movement": "movement_focus",
    "wellbeing": "wellbeing_focus", "followup": "followup",
    "comparison": "kpi_development",
}
CATALOGUE_DOMAIN = {
    "food": "nutrition", "movement": "movement", "wellbeing": "wellbeing",
    "followup": "followup", "comparison": "journey",
}


def _linked_metadata(bundle: ContentBundle, evidence: EvidenceSpan,
                     catalogue_items: list[CatalogueItem]) -> dict:
    fragments = [fragment for fragment in bundle.fragments if evidence.evidence_id in fragment.evidence_span_ids]
    catalogue = [item for item in catalogue_items if evidence.evidence_id in item.evidence_span_ids]
    profiles = []
    slots = set()
    for profile in bundle.profiles:
        linked = {fragment.fragment_id for fragment in fragments} & set(profile.guidance_fragment_ids)
        if evidence.evidence_id in profile.hero.development_evidence_ids:
            linked.add("__hero__")
            slots.add("hero")
            if profile.applies_to.stage == "pregnancy":
                slots.add("kpi_development")
        if linked:
            profiles.append(profile)
        for slot, references in profile.card_slots.model_dump().items():
            if set(references) & {fragment.fragment_id for fragment in fragments}:
                slots.add(slot)
    domains = sorted({fragment.domain for fragment in fragments})
    domains = sorted(set(domains) | {CATALOGUE_DOMAIN[item.kind] for item in catalogue})
    if not domains:
        source = next(source for source in bundle.sources if source.source_id == evidence.source_id)
        domains = sorted(set(source.topics))
    if not slots:
        slots.update(DOMAIN_SLOT[domain] for domain in domains)
    slots.update(CATALOGUE_SLOT[item.kind] for item in catalogue)
    if "followup" in domains:
        slots.add("followup")
    required = sorted({condition for record in [*fragments, *catalogue]
                       for condition in record.conditions_required})
    excluded = sorted({condition for record in [*fragments, *catalogue]
                       for condition in record.conditions_excluded})
    dependencies = {CONDITION_FACTS[condition] for condition in required + excluded}
    for domain in domains:
        dependencies.update(DOMAIN_DEPENDENCIES[domain])
    return dict(fragments=fragments, profiles=profiles, catalogue=catalogue,
                domains=domains, slots=sorted(slots),
                required=required, excluded=excluded, dependencies=sorted(dependencies))


def _best_anchor(blocks, evidence: EvidenceSpan):
    eligible = [block for block in blocks if evidence.page is None or block.page == evidence.page]
    def anchor_key(value: str) -> str:
        value = " ".join(re.sub(r"[\W_]+", " ", normalize_text(value)).split())
        # PDF text layers sometimes split the final letter of a printed word
        # (for example "registratio n"). Apply the same conservative repair to
        # the selected evidence and parsed source before comparing them.
        return re.sub(r"\b([a-z]{4,})\s+([a-z])\b", r"\1\2", value)

    needle = anchor_key(evidence.text)
    direct = next((block for block in eligible if needle in anchor_key(block.text)), None)
    if direct:
        return True, direct.heading_path, [direct.block_id]
    combined = anchor_key(" ".join(block.text for block in eligible))
    if needle in combined:
        matched = [block for block in eligible if anchor_key(block.text) in needle]
        return True, [], [block.block_id for block in matched] or [eligible[0].block_id]
    # Selected evidence may intentionally join several labelled bullets or
    # sections. Every sentence must still resolve on the selected page/source.
    segments = [anchor_key(value) for value in re.split(r"(?<=[.!?:])\s+", evidence.text)
                if anchor_key(value)]
    matched = []
    for segment in segments:
        block = next((item for item in eligible if segment in anchor_key(item.text)), None)
        if block is None:
            return False, [], []
        if block not in matched:
            matched.append(block)
    headings = list(dict.fromkeys(heading for block in matched for heading in block.heading_path))
    return bool(matched), headings, [block.block_id for block in matched]


def build_candidates(bundle: ContentBundle, source: SourceRecord, artifact: SourceArtifact,
                     blocks, *, admission: SourceAdmission | None = None,
                     catalogue_items: list[CatalogueItem] | None = None
                     ) -> tuple[list[EvidenceCandidate], list[IngestionIssue]]:
    catalogue_items = catalogue_items or []
    candidates = []
    issues = []
    evidence_records = [evidence for evidence in bundle.evidence if evidence.source_id == source.source_id]
    for evidence in evidence_records:
        verified, heading_path, block_ids = _best_anchor(blocks, evidence)
        metadata = _linked_metadata(bundle, evidence, catalogue_items)
        measurements, measurements_current = development_measurements_for(evidence)
        reasons = []
        hard_failure = not verified
        if not verified:
            reasons.append("selected evidence text was not found in the parsed source page/structure")
        if (evidence.source_version != source.version_or_last_update
                or evidence.source_checksum != source.content_checksum):
            reasons.append("evidence refers to a different source version or snapshot")
            hard_failure = True
        if sha256(evidence.text.encode("utf-8")).hexdigest() != evidence.text_checksum:
            reasons.append("evidence text checksum is invalid")
            hard_failure = True
        if not measurements_current:
            reasons.append("development measurement annotation is stale")
            hard_failure = True
        if len(normalize_text(evidence.text)) > 3000:
            reasons.append("evidence is too large for one meaningful search unit; manual split required")
        if source.status != "approved_for_capstone" or source.review is None:
            reasons.append("source awaits actual named approval")
        if source.revalidation_status != "current_capture":
            reasons.append("source currency decision is unresolved")
        if admission and admission.decision != "eligible_for_publication":
            reasons.extend(f"source admission requires review: {reason}" for reason in admission.reasons)
        if evidence.status != "published" or evidence.review is None:
            reasons.append("evidence awaits actual named review and publication")
        if evidence.localisation and evidence.localisation.review is None:
            reasons.append("India localisation awaits actual named review")
        if any(fragment.status != "published" or fragment.review is None for fragment in metadata["fragments"]):
            reasons.append("linked guidance wording awaits actual named review and publication")
        if any(item.status != "published" or item.blockers for item in metadata["catalogue"]):
            reasons.append("linked recommendation catalogue item awaits review and publication")
        for item in metadata["catalogue"]:
            if (not evidence.applies_to.covers(item.applies_to)
                    or ("GLOBAL" not in evidence.jurisdiction
                        and not set(item.jurisdiction) <= set(evidence.jurisdiction))):
                reasons.append("linked recommendation catalogue item has incompatible timing or jurisdiction")
                hard_failure = True
        state = "rejected" if hard_failure else "review_required" if reasons else "approved"
        search_text = normalize_text(f"{source.title}. {evidence.locator}. {evidence.text}")
        subject = dict(evidence_id=evidence.evidence_id, source_id=source.source_id,
                       artifact_sha256=artifact.original_sha256, source_version=source.version_or_last_update,
                       source_governance_checksum=fingerprint(
                           review_subject(source.model_dump(mode="json"))),
                       source_locator=evidence.locator, source_block_ids=block_ids,
                       page=evidence.page, heading_path=heading_path,
                       original_text=evidence.text, normalized_search_text=search_text,
                       original_text_sha256=evidence.text_checksum, source_anchor_verified=verified,
                       domains=metadata["domains"], display_slots=metadata["slots"],
                       applies_to=evidence.applies_to.model_dump(mode="json"), jurisdiction=evidence.jurisdiction,
                       conditions_required=metadata["required"], conditions_excluded=metadata["excluded"],
                       personal_fact_dependencies=metadata["dependencies"],
                       development_measurements=[measurement.model_dump(mode="json")
                                                 for measurement in measurements],
                       linked_profile_ids=sorted(profile.profile_id for profile in metadata["profiles"]),
                       linked_fragment_ids=sorted(fragment.fragment_id for fragment in metadata["fragments"]),
                       linked_catalogue_item_ids=sorted(item.item_id for item in metadata["catalogue"]))
        candidates.append(EvidenceCandidate(candidate_id=f"C-{evidence.evidence_id}", **subject, state=state,
                                             review_reasons=list(dict.fromkeys(reasons)),
                                             candidate_checksum=fingerprint(subject)))
        if not verified:
            issues.append(IngestionIssue(code="ANCHOR_NOT_FOUND", severity="error",
                                         message="Selected evidence is absent from parsed source; candidate rejected.",
                                         source_id=source.source_id, page=evidence.page, locator=evidence.locator))
    if not evidence_records:
        issues.append(IngestionIssue(code="NO_SELECTED_EVIDENCE", severity="warning",
                                     message="Source has no selected evidence; parser output remains review-only and is not chunked.",
                                     source_id=source.source_id))
    duplicate_keys = [fingerprint({"source_id": candidate.source_id,
                                   "text": normalize_text(candidate.original_text),
                                   "applies_to": candidate.applies_to.model_dump(mode="json"),
                                   "jurisdiction": sorted(candidate.jurisdiction)})
                      for candidate in candidates]
    for checksum, count in Counter(duplicate_keys).items():
        if count > 1:
            issues.append(IngestionIssue(code="DUPLICATE_CANDIDATE", severity="error",
                                         message="Identical evidence candidate metadata was produced more than once.",
                                         source_id=source.source_id))
    return candidates, issues


def candidate_diff(current: list[EvidenceCandidate], previous: IngestionRun | None,
                   *, source_changed: bool) -> IngestionDiff:
    before = {candidate.evidence_id: candidate for candidate in previous.candidates} if previous else {}
    after = {candidate.evidence_id: candidate for candidate in current}
    new = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    unchanged = sorted(key for key in set(after) & set(before)
                       if after[key].candidate_checksum == before[key].candidate_checksum)
    changed = sorted((set(after) & set(before)) - set(unchanged))
    affected = sorted({profile for key in changed + removed
                       for profile in (after.get(key) or before[key]).linked_profile_ids})
    affected_catalogue = sorted({item for key in changed + removed
                                 for item in (after.get(key) or before[key]).linked_catalogue_item_ids})
    source_ids = {candidate.source_id for candidate in current} | {candidate.source_id for candidate in before.values()}
    cache = []
    if changed or removed or source_changed:
        cache.extend(f"public-source:{source_id}" for source_id in sorted(source_ids))
    cache.extend(f"weekly-profile:{profile_id}" for profile_id in affected)
    cache.extend(f"catalogue-item:{item_id}" for item_id in affected_catalogue)
    return IngestionDiff(new_candidate_ids=[after[key].candidate_id for key in new],
                         unchanged_candidate_ids=[after[key].candidate_id for key in unchanged],
                         changed_evidence_ids=changed, removed_evidence_ids=removed,
                         invalidated_profile_ids=affected,
                         invalidated_catalogue_item_ids=affected_catalogue,
                         invalidate_cache_scopes=cache)


def _embeddings(candidates: list[EvidenceCandidate], admission: SourceAdmission,
                provider: EmbeddingProvider | None) -> tuple[list[EmbeddingRecord], list[IngestionIssue]]:
    approved = [candidate for candidate in candidates if candidate.state == "approved"]
    if not admission.may_embed:
        return [], []
    if approved and provider is None:
        return [], [IngestionIssue(code="EMBEDDING_PROVIDER_REQUIRED", severity="error",
                                   message="Approved retrievable units require an explicitly configured embedding provider/model.",
                                   source_id=admission.source_id)]
    if not approved:
        return [], []
    try:
        vectors = provider.embed([candidate.normalized_search_text for candidate in approved])
        if len(vectors) != len(approved):
            raise ValueError("provider returned a different number of vectors")
        records = []
        for candidate, vector in zip(approved, vectors, strict=True):
            records.append(EmbeddingRecord(chunk_id=f"CH-{candidate.candidate_checksum[:20]}",
                                           evidence_id=candidate.evidence_id, source_id=candidate.source_id,
                                           candidate_checksum=candidate.candidate_checksum,
                                           provider=provider.name, model=provider.model,
                                           dimensions=len(vector), vector=vector))
    except Exception as exc:
        return [], [IngestionIssue(code="EMBEDDING_FAILED", severity="error",
                                   message=f"Embedding creation failed safely: {type(exc).__name__}.",
                                   source_id=admission.source_id)]
    return records, []


def _review_tasks(candidates: list[EvidenceCandidate],
                  decisions: list[EvidenceReviewDecision] | None = None) -> list[EvidenceReviewTask]:
    checks = ["source_anchor", "domain", "stage_and_range", "wording", "jurisdiction",
              "conditions", "development_measurements", "profile_links", "catalogue_links",
              "reuse_and_attribution"]
    roles = ["licence", "content", "clinical", "india_localisation", "product"]
    supplied = decisions or []
    grouped: dict[str, list[EvidenceReviewDecision]] = {}
    for decision in supplied:
        grouped.setdefault(decision.task_id, []).append(decision)
    tasks = []
    for candidate in candidates:
        if candidate.state != "review_required":
            continue
        task_id = f"REV-{candidate.candidate_checksum[:20]}"
        task_decisions = grouped.pop(task_id, [])
        dispositions = {decision.decision for decision in task_decisions}
        decided_roles = {decision.role for decision in task_decisions}
        if "rejected" in dispositions:
            status = "rejected"
        elif "changes_requested" in dispositions:
            status = "changes_requested"
        elif "needs_specialist_review" in dispositions:
            status = "needs_specialist_review"
        elif decided_roles == set(roles) and dispositions == {"accepted"}:
            status = "accepted"
        else:
            status = "pending"
        tasks.append(EvidenceReviewTask(
            task_id=task_id, candidate_id=candidate.candidate_id,
            evidence_id=candidate.evidence_id, source_id=candidate.source_id,
            candidate_checksum=candidate.candidate_checksum,
            required_checks=checks, required_roles=roles,
            blocking_reasons=candidate.review_reasons,
            decisions=task_decisions, status=status))
    if grouped:
        raise ValueError("review decisions refer to absent or stale tasks: "
                         + ", ".join(sorted(grouped)))
    return tasks


def apply_review_decisions(run: IngestionRun,
                           decisions: list[EvidenceReviewDecision]) -> IngestionRun:
    """Attach role decisions to an existing exact-source run.

    This is useful when a reviewer responds after parsing. The same task/checksum
    validation used during ingestion is retained, so a stale decision cannot be
    copied onto changed evidence.
    """
    source_decisions = [decision for decision in decisions
                        if decision.source_id == run.admission.source_id]
    review_tasks = _review_tasks(run.candidates, source_decisions)
    return run.model_copy(update={"review_tasks": review_tasks})


def _governed_blocks(blocks: list[ParsedBlock],
                     candidates: list[EvidenceCandidate]) -> list[ParsedBlock]:
    """Retain only blocks used by selected evidence, never an unbounded page dump."""
    wanted = {block_id for candidate in candidates for block_id in candidate.source_block_ids}
    by_id = {block.block_id: block for block in blocks}
    missing = wanted - by_id.keys()
    if missing:
        raise ValueError(f"candidate source blocks are absent from parser output: {sorted(missing)}")
    return [block for block in blocks if block.block_id in wanted]


def run_ingestion(bundle: ContentBundle, source_id: str, raw: bytes, *, retrieved_at: date,
                  dry_run: bool = True, previous: IngestionRun | None = None,
                  embedding_provider: EmbeddingProvider | None = None,
                  review_decisions: list[EvidenceReviewDecision] | None = None,
                  catalogue_items: list[CatalogueItem] | None = None,
                  ocr_provider: OcrProvider | None = None,
                  as_of: date | None = None) -> IngestionRun:
    source = next((source for source in bundle.sources if source.source_id == source_id), None)
    if source is None:
        raise ValueError(f"source is not registered: {source_id}")
    if previous is not None and previous.admission.source_id != source_id:
        raise ValueError("previous ingestion run belongs to a different source")
    evaluated_at = as_of or date.today()
    admission = admission_for(source, evaluated_at)
    artifact_checksum = sha256(raw).hexdigest()
    logical_seed = fingerprint({"source_id": source_id, "raw": artifact_checksum,
                                "source_version": source.version_or_last_update,
                                "parser_version": PARSER_VERSION,
                                "ingestion_schema_version": "1.1.0"})[:20]
    logical_version_id = f"LV-{logical_seed}"
    run_seed = fingerprint({"logical_version_id": logical_version_id,
                            "retrieved_at": retrieved_at.isoformat(),
                            "evaluated_at": evaluated_at.isoformat()})[:20]
    run_id = f"ING-{run_seed}"
    if admission.decision == "rejected":
        issues = [IngestionIssue(code="SOURCE_REJECTED", severity="error", message="; ".join(admission.reasons),
                                 source_id=source_id)]
        return IngestionRun(run_id=run_id, logical_version_id=logical_version_id,
                            created_at=datetime.now(timezone.utc), evaluated_at=evaluated_at,
                            dry_run=dry_run,
                            admission=admission, parsed_block_count=0, issues=issues, outcome="rejected")
    bundle_report = validate_bundle(bundle, require_coverage=False)
    if not bundle_report.valid:
        issue = IngestionIssue(code="CONTENT_BUNDLE_INVALID", severity="error",
                               message="Public content contracts failed: " + "; ".join(bundle_report.errors[:5]),
                               source_id=source_id)
        return IngestionRun(run_id=run_id, logical_version_id=logical_version_id,
                            created_at=datetime.now(timezone.utc), evaluated_at=evaluated_at,
                            dry_run=dry_run, admission=admission, parsed_block_count=0,
                            issues=[issue], outcome="rejected")
    parser_name = "beautifulsoup4" if source.document_type == "html" else "pymupdf"
    parser_version = bs4.__version__ if source.document_type == "html" else fitz.VersionBind
    artifact = SourceArtifact(source_id=source_id, canonical_url=source.canonical_url,
                              source_version=source.version_or_last_update,
                              document_type=source.document_type, retrieved_at=retrieved_at,
                              original_sha256=artifact_checksum, byte_size=len(raw),
                              parser_name=parser_name, parser_version=f"{parser_version};nestline-{PARSER_VERSION}")
    selected = [evidence.page for evidence in bundle.evidence
                if evidence.source_id == source_id and evidence.page is not None]
    if source.document_type == "html":
        blocks, issues = parse_html(source_id, raw)
    elif source.document_type == "pdf":
        blocks, issues = parse_pdf(source_id, raw, selected_pages=set(selected) or None,
                                   ocr_provider=ocr_provider)
    else:
        raise ValueError("only admitted HTML and PDF sources can be parsed")
    candidates, candidate_issues = build_candidates(bundle, source, artifact, blocks, admission=admission,
                                                     catalogue_items=catalogue_items)
    issues.extend(candidate_issues)
    previous_candidates = ({candidate.evidence_id: candidate for candidate in previous.candidates}
                           if previous else {})
    governed_candidate_changed = any(
        candidate.evidence_id in previous_candidates
        and candidate.candidate_checksum
        != previous_candidates[candidate.evidence_id].candidate_checksum
        for candidate in candidates
    )
    source_changed = bool(previous and (
        governed_candidate_changed
        or (previous.artifact and (
            previous.artifact.original_sha256 != artifact.original_sha256
            or previous.artifact.source_version != artifact.source_version
        ))
        or previous.admission != admission
    ))
    if source_changed:
        candidates = [candidate.model_copy(update={
            "state": "review_required",
            "review_reasons": list(dict.fromkeys([
                *candidate.review_reasons,
                "source content, version or permission state changed since the prior capture",
            ])),
        }) if candidate.state == "approved" else candidate for candidate in candidates]
    governed_blocks = _governed_blocks(blocks, candidates)
    if any(issue.severity == "error" for issue in issues):
        embeddings, embedding_issues = [], []
    else:
        embeddings, embedding_issues = _embeddings(candidates, admission, embedding_provider)
    issues.extend(embedding_issues)
    review_tasks = _review_tasks(candidates, review_decisions)
    diff = candidate_diff(candidates, previous, source_changed=source_changed)
    has_error = any(issue.severity == "error" for issue in issues)
    if has_error or any(candidate.state == "rejected" for candidate in candidates):
        outcome = "rejected"
    elif not candidates or any(candidate.state == "review_required" for candidate in candidates):
        outcome = "review_required"
    else:
        outcome = "publishable"
    return IngestionRun(run_id=run_id, logical_version_id=logical_version_id,
                        created_at=datetime.now(timezone.utc), evaluated_at=evaluated_at,
                        dry_run=dry_run,
                        artifact=artifact, admission=admission, parsed_block_count=len(blocks),
                        governed_blocks=governed_blocks,
                        candidates=candidates, review_tasks=review_tasks,
                        embeddings=embeddings, issues=issues, diff=diff, outcome=outcome)
