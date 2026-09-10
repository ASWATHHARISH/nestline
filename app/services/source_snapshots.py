"""Verify saved excerpts offline; no network or medical judgement is involved."""

from hashlib import sha256
import json
from pathlib import Path

from app.schemas.content import ContentBundle


def validate_snapshots(bundle: ContentBundle, data_dir: Path) -> list[str]:
    """Bind every evidence locator and exact text to the bytes we actually saved.

    A snapshot contains selected excerpts, not the complete publisher webpage.
    Its checksum proves local integrity, not that a publisher signed the content.
    """
    errors: list[str] = []
    snapshot_root = (data_dir / "guidelines/snapshots").resolve()
    used_sources = {span.source_id for span in bundle.evidence}
    for source in bundle.sources:
        if source.source_id not in used_sources and not source.snapshot_path:
            continue
        try:
            path = (data_dir / source.snapshot_path).resolve()
            if not source.snapshot_path or not path.is_relative_to(snapshot_root):
                raise ValueError("snapshot path must stay inside guidelines/snapshots")
            raw = path.read_bytes()
            if sha256(raw).hexdigest() != source.content_checksum:
                raise ValueError("saved snapshot checksum mismatch")
            snapshot = json.loads(raw)
            expected = (source.source_id, source.canonical_url, source.version_or_last_update)
            actual = (snapshot["source_id"], snapshot["canonical_url"], snapshot["version"])
            if actual != expected:
                raise ValueError("snapshot identity, URL or version mismatch")
            sections = snapshot["sections"]
            locators = [section["locator"] for section in sections]
            if len(locators) != len(set(locators)):
                raise ValueError("duplicate snapshot locator")
            if set(locators) != set(source.selected_sections):
                raise ValueError("selected sections differ from snapshot")
            saved = {section["locator"]: section["text"] for section in sections}
            for span in bundle.evidence:
                if span.source_id == source.source_id and saved.get(span.locator) != span.text:
                    errors.append(f"{span.evidence_id}: exact text/locator absent from snapshot")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(f"{source.source_id}: {exc}")
    return errors
