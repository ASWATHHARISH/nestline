"""Cross-record integrity checks for authoring; does not verify medical semantics."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256

from app.schemas.content import ContentBundle


def expected_profile_ids() -> set[str]:
    return ({"PC00"} | {f"P{i:02d}" for i in range(1, 43)}
            | {f"PP{i:02d}" for i in range(1, 13)} | {f"PPD{i}" for i in range(8)})


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    published_profiles: int = 0

    @property
    def valid(self) -> bool:
        return not self.errors


def _index(records, key, report):
    indexed = {}
    for record in records:
        value = getattr(record, key)
        if value in indexed:
            report.errors.append(f"duplicate {key}: {value}")
        indexed[value] = record
    return indexed


def validate_bundle(bundle: ContentBundle, *, require_coverage: bool = True) -> ValidationReport:
    report = ValidationReport()
    sources = _index(bundle.sources, "source_id", report)
    evidence = _index(bundle.evidence, "evidence_id", report)
    fragments = _index(bundle.fragments, "fragment_id", report)
    profiles = _index(bundle.profiles, "profile_id", report)

    if require_coverage:
        for missing in sorted(expected_profile_ids() - profiles.keys()):
            report.errors.append(f"missing journey record: {missing}")

    def error(owner, message):
        report.errors.append(f"{owner}: {message}")

    def require_review(owner, record):
        if record.status in {"reviewed", "published"} and record.review is None:
            error(owner, "review metadata required")

    def require_scope(owner, parent, child):
        if not child.applies_to.covers(parent.applies_to):
            error(owner, "linked evidence/fragment does not cover the entire applicability range")
        # GLOBAL can support an IN profile, but IN/UK must not become GLOBAL authority.
        if "GLOBAL" not in child.jurisdiction and not set(parent.jurisdiction) <= set(child.jurisdiction):
            error(owner, "linked evidence/fragment has incompatible jurisdiction")

    for span in bundle.evidence:
        key = span.evidence_id
        require_review(key, span)
        source = sources.get(span.source_id)
        if source is None:
            error(key, "unknown source")
            continue
        if span.text_checksum != sha256(span.text.encode("utf-8")).hexdigest():
            error(key, "evidence text checksum mismatch")
        if "GLOBAL" not in source.jurisdiction and not set(span.jurisdiction) <= set(source.jurisdiction):
            error(key, "evidence jurisdiction exceeds source jurisdiction")
        if span.status in {"reviewed", "published"}:
            if source.status != "approved_for_capstone":
                error(key, "source is not approved")
            if span.source_version != source.version_or_last_update or span.source_checksum != source.content_checksum:
                error(key, "source version/checksum mismatch")

    for fragment in bundle.fragments:
        key = fragment.fragment_id
        require_review(key, fragment)
        for ref in fragment.evidence_span_ids:
            span = evidence.get(ref)
            if span is None:
                error(key, f"unknown evidence: {ref}")
                continue
            require_scope(key, fragment, span)
            if fragment.status in {"reviewed", "published"} and span.status != "published":
                error(key, f"evidence is not published: {ref}")

    for profile in bundle.profiles:
        key = profile.profile_id
        require_review(key, profile)
        if profile.status == "published":
            report.published_profiles += 1
            if not profile.hero.title.strip() or not profile.hero.development_evidence_ids:
                error(key, "published profile needs a sourced hero")
            if not profile.guidance_fragment_ids:
                error(key, "published profile needs guidance fragments")
        for card_refs in profile.card_slots.model_dump().values():
            for ref in card_refs:
                if ref not in profile.guidance_fragment_ids:
                    error(key, f"card references undeclared fragment: {ref}")
        direct_refs = set(profile.source_evidence_ids) | set(profile.hero.development_evidence_ids)
        for ref in profile.guidance_fragment_ids:
            fragment = fragments.get(ref)
            if fragment is None:
                error(key, f"unknown fragment: {ref}")
                continue
            require_scope(key, profile, fragment)
            direct_refs.update(fragment.evidence_span_ids)
            if profile.status in {"reviewed", "published"} and fragment.status != "published":
                error(key, f"fragment is not published: {ref}")
        for ref in direct_refs:
            span = evidence.get(ref)
            if span is None:
                error(key, f"unknown evidence: {ref}")
                continue
            require_scope(key, profile, span)
            if profile.status in {"reviewed", "published"} and span.status != "published":
                error(key, f"evidence is not published: {ref}")
    return report
