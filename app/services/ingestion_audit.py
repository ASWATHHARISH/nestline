"""Build and verify the text-free, tracked Stage 1 source audit."""

from pathlib import Path

from app.schemas.content import ContentBundle
from app.schemas.ingestion import IngestionRun, Stage1Audit, Stage1AuditSource
from app.services.foundation import release_fingerprint


def _expected_by_source(bundle: ContentBundle) -> dict[str, set[str]]:
    expected: dict[str, set[str]] = {}
    for evidence in bundle.evidence:
        expected.setdefault(evidence.source_id, set()).add(evidence.evidence_id)
    return expected


def build_stage1_audit(runs: list[IngestionRun], bundle: ContentBundle,
                       data_root: Path) -> Stage1Audit:
    """Summarise exact captures without copying source or candidate text."""
    expected = _expected_by_source(bundle)
    by_source: dict[str, IngestionRun] = {}
    for run in runs:
        source_id = run.admission.source_id
        if source_id in by_source:
            raise ValueError(f"audit input contains duplicate source run: {source_id}")
        by_source[source_id] = run
    if set(by_source) != set(expected):
        missing = sorted(set(expected) - set(by_source))
        extra = sorted(set(by_source) - set(expected))
        raise ValueError(f"audit source coverage differs; missing={missing}, extra={extra}")

    sources = []
    for source_id in sorted(by_source):
        run = by_source[source_id]
        if run.artifact is None:
            raise ValueError(f"audit run has no source artifact: {source_id}")
        evidence_ids = sorted(candidate.evidence_id for candidate in run.candidates)
        if set(evidence_ids) != expected[source_id]:
            raise ValueError(f"audit evidence coverage differs for {source_id}")
        sources.append(Stage1AuditSource(
            source_id=source_id,
            logical_version_id=run.logical_version_id,
            artifact_sha256=run.artifact.original_sha256,
            source_version=run.artifact.source_version,
            parser_name=run.artifact.parser_name,
            parser_version=run.artifact.parser_version,
            outcome=run.outcome,
            candidate_ids=sorted(candidate.candidate_id for candidate in run.candidates),
            evidence_ids=evidence_ids,
            candidate_checksums=sorted(candidate.candidate_checksum for candidate in run.candidates),
            selected_content_checksums=sorted(candidate.original_text_sha256
                                              for candidate in run.candidates),
            source_governance_checksums=sorted({candidate.source_governance_checksum
                                                for candidate in run.candidates}),
            governed_block_ids=sorted(block.block_id for block in run.governed_blocks),
            review_task_ids=sorted(task.task_id for task in run.review_tasks),
            parsed_block_count=run.parsed_block_count,
            verified_anchor_count=sum(candidate.source_anchor_verified for candidate in run.candidates),
            review_task_count=len(run.review_tasks),
            embedding_count=len(run.embeddings),
            error_count=sum(issue.severity == "error" for issue in run.issues),
        ))
    return Stage1Audit(
        foundation_release_fingerprint=release_fingerprint(data_root),
        generated_from="exact_registered_https_sources",
        sources=sources,
    )


def validate_stage1_audit(audit: Stage1Audit, bundle: ContentBundle,
                          data_root: Path) -> list[str]:
    """Validate the committed audit from a clean checkout without live network access."""
    errors = []
    expected = _expected_by_source(bundle)
    source_ids = [source.source_id for source in audit.sources]
    if len(source_ids) != len(set(source_ids)):
        errors.append("canonical audit contains duplicate source IDs")
    if set(source_ids) != set(expected):
        errors.append("canonical audit does not cover every evidence-bearing source exactly")
    if audit.foundation_release_fingerprint != release_fingerprint(data_root):
        errors.append("canonical audit was generated for a different Stage 0 release fingerprint")
    for source in audit.sources:
        wanted = expected.get(source.source_id)
        if wanted is None:
            continue
        if set(source.evidence_ids) != wanted or len(source.evidence_ids) != len(wanted):
            errors.append(f"{source.source_id}: canonical audit evidence coverage differs")
        if len(source.candidate_ids) != len(wanted):
            errors.append(f"{source.source_id}: canonical audit candidate count differs")
        if len(source.candidate_checksums) != len(wanted):
            errors.append(f"{source.source_id}: canonical audit checksum count differs")
        if len(source.selected_content_checksums) != len(wanted):
            errors.append(f"{source.source_id}: selected-content checksum count differs")
        if not source.source_governance_checksums:
            errors.append(f"{source.source_id}: source governance checksum is absent")
        if source.verified_anchor_count != len(wanted):
            errors.append(f"{source.source_id}: not every candidate has a verified source anchor")
        if not source.governed_block_ids:
            errors.append(f"{source.source_id}: no governed source blocks were retained")
        if source.review_task_count != len(wanted):
            errors.append(f"{source.source_id}: pending review queue does not cover every candidate")
        if len(source.review_task_ids) != len(wanted):
            errors.append(f"{source.source_id}: canonical audit review-task IDs differ")
        if not source.parser_name or not source.parser_version or source.parsed_block_count < 1:
            errors.append(f"{source.source_id}: parser evidence is incomplete")
        if source.embedding_count:
            errors.append(f"{source.source_id}: pending content must not have embeddings")
        if source.error_count:
            errors.append(f"{source.source_id}: canonical source run contains errors")
        if source.outcome != "review_required":
            errors.append(f"{source.source_id}: expected safe review_required outcome")
    return errors
