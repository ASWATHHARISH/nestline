"""Local Stage 1 staging and corpus publication.

Stage 2 will move these records into Supabase. These functions already fail on
overwrites and use atomic file replacement for individual staging records.
"""

from datetime import date, datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import shutil
from tempfile import NamedTemporaryFile
from tempfile import mkdtemp

from app.schemas.ingestion import CorpusManifest, IngestionRun
from app.services.foundation import approval_errors, release_fingerprint

REQUIRED_RELEASE_ROLES = ["licence", "content", "clinical", "india_localisation", "product"]


def _json_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _jsonl_bytes(values) -> bytes:
    return b"".join(_json_bytes(value) for value in values)


def write_staging_run(run: IngestionRun, root: Path) -> tuple[Path, str]:
    if run.dry_run:
        raise ValueError("dry-run results cannot be committed to staging")
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{run.run_id}.json"
    payload = _json_bytes(run.model_dump(mode="json"))
    if path.exists():
        existing = IngestionRun.model_validate_json(path.read_text(encoding="utf-8"))
        same = (existing.logical_version_id == run.logical_version_id
                and existing.artifact == run.artifact and existing.admission == run.admission
                and existing.governed_blocks == run.governed_blocks
                and existing.candidates == run.candidates and existing.review_tasks == run.review_tasks
                and existing.embeddings == run.embeddings
                and existing.issues == run.issues and existing.diff == run.diff
                and existing.outcome == run.outcome)
        if not same:
            raise ValueError("staging run ID collision with different content")
        return path, "unchanged"
    with NamedTemporaryFile("wb", dir=root, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(payload)
    temporary.replace(path)
    return path, "created"


def latest_staging_run(root: Path, source_id: str) -> IngestionRun | None:
    """Find the newest valid capture for one source; unrelated sources are ignored."""
    matches = []
    for path in root.glob("*.json") if root.exists() else []:
        run = IngestionRun.model_validate_json(path.read_text(encoding="utf-8"))
        if run.admission.source_id == source_id:
            matches.append(run)
    if not matches:
        return None
    return max(matches, key=lambda run: (
        run.artifact.retrieved_at if run.artifact else date.min,
        run.evaluated_at,
        run.created_at,
    ))


def write_source_artifact(run: IngestionRun, raw: bytes, root: Path) -> tuple[Path, str]:
    """Save the admitted source bytes under their content hash, without overwriting."""
    if run.dry_run:
        raise ValueError("dry-run artifacts cannot be committed")
    if run.admission.fixed_quote_only:
        raise ValueError("fixed-quote sources store governed excerpts, not the full source artifact")
    if run.artifact is None or not run.admission.may_store or run.outcome == "rejected":
        raise ValueError("only admitted, non-rejected source artifacts may be stored")
    if len(raw) != run.artifact.byte_size or sha256(raw).hexdigest() != run.artifact.original_sha256:
        raise ValueError("source bytes differ from the ingestion artifact record")
    folder = root / run.artifact.source_id
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{run.artifact.original_sha256}.{run.artifact.document_type}"
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError("artifact hash collision with different bytes")
        return path, "unchanged"
    with NamedTemporaryFile("wb", dir=folder, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(raw)
    temporary.replace(path)
    return path, "created"


def publish_corpus(runs: list[IngestionRun], root: Path, corpus_version: str, *,
                   governance_data: Path, as_of: date | None = None) -> CorpusManifest:
    """Publish only against the current Stage 0 fingerprint and five approvals."""
    gate_errors = approval_errors(governance_data, as_of or date.today())
    if gate_errors:
        raise ValueError("current Stage 0 release approvals are incomplete: " + "; ".join(gate_errors))
    approved_fingerprint = release_fingerprint(governance_data)
    if not runs:
        raise ValueError("at least one ingestion run is required")
    if any(run.outcome != "publishable" or run.dry_run for run in runs):
        raise ValueError("only committed, publishable ingestion runs may form a corpus")
    if any(run.admission.decision != "eligible_for_publication" or run.review_tasks
           or any(issue.severity == "error" for issue in run.issues) for run in runs):
        raise ValueError("corpus runs contain unresolved admission, review or validation state")
    candidates = [candidate for run in runs for candidate in run.candidates]
    embeddings = [embedding for run in runs for embedding in run.embeddings]
    if not candidates or any(candidate.state != "approved" for candidate in candidates):
        raise ValueError("published corpus requires approved evidence candidates")
    evidence_ids = [candidate.evidence_id for candidate in candidates]
    if len(evidence_ids) != len(set(evidence_ids)):
        raise ValueError("duplicate evidence IDs across ingestion runs")
    if any(embedding.provider == "TEST_ONLY" for embedding in embeddings):
        raise ValueError("test embeddings cannot be published")
    candidate_by_evidence = {candidate.evidence_id: candidate for candidate in candidates}
    blocks = [block for run in runs for block in run.governed_blocks]
    block_ids = [block.block_id for block in blocks]
    if len(block_ids) != len(set(block_ids)):
        raise ValueError("duplicate governed source block IDs across ingestion runs")
    if {block_id for candidate in candidates for block_id in candidate.source_block_ids} != set(block_ids):
        raise ValueError("published candidate source blocks are not exactly resolvable")
    if any(sha256(candidate.original_text.encode("utf-8")).hexdigest()
           != candidate.original_text_sha256 for candidate in candidates):
        raise ValueError("candidate citation text checksum is invalid")
    if any(embedding.candidate_checksum != candidate_by_evidence[embedding.evidence_id].candidate_checksum
           for embedding in embeddings):
        raise ValueError("embedding refers to a different candidate version")
    required_embeddings = {candidate.evidence_id for run in runs if run.admission.may_embed
                           for candidate in run.candidates}
    if {embedding.evidence_id for embedding in embeddings} != required_embeddings:
        raise ValueError("published retrievable evidence requires exactly one embedding")
    providers = {(embedding.provider, embedding.model) for embedding in embeddings}
    if len(providers) > 1:
        raise ValueError("one corpus version must use one embedding provider/model")
    provider, model = next(iter(providers), ("none-fixed-quote-only", "none"))
    target = root / corpus_version
    if target.exists():
        raise FileExistsError("corpus version already exists and is immutable")
    root.mkdir(parents=True, exist_ok=True)
    temporary = Path(mkdtemp(prefix=f".{corpus_version}-", dir=root))
    block_bytes = _jsonl_bytes([block.model_dump(mode="json") for block in blocks])
    candidate_bytes = _jsonl_bytes([candidate.model_dump(mode="json") for candidate in candidates])
    embedding_bytes = _jsonl_bytes([embedding.model_dump(mode="json") for embedding in embeddings])
    (temporary / "blocks.jsonl").write_bytes(block_bytes)
    (temporary / "candidates.jsonl").write_bytes(candidate_bytes)
    (temporary / "embeddings.jsonl").write_bytes(embedding_bytes)
    manifest = CorpusManifest(corpus_version=corpus_version, created_at=datetime.now(timezone.utc),
                              status="published", source_artifacts=[run.artifact for run in runs],
                              release_fingerprint=approved_fingerprint,
                              approval_roles=REQUIRED_RELEASE_ROLES,
                              block_file_sha256=sha256(block_bytes).hexdigest(),
                              candidate_file_sha256=sha256(candidate_bytes).hexdigest(),
                              embedding_file_sha256=sha256(embedding_bytes).hexdigest(),
                              embedding_provider=provider, embedding_model=model,
                              evidence_ids=sorted(evidence_ids),
                              profile_ids=sorted({profile for candidate in candidates
                                                  for profile in candidate.linked_profile_ids}),
                              limitations=["Public reviewed evidence only; no user reports or personal facts.",
                                           "Fixed-quote sources retain governed excerpts without a full-page artifact.",
                                           "Retrieval and answer generation require separate Stage 5 and Stage 8 controls."])
    (temporary / "manifest.json").write_bytes(_json_bytes(manifest.model_dump(mode="json")))
    try:
        temporary.replace(target)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return manifest
