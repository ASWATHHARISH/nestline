"""Create a readable content-review worksheet from the maintained dataset.

This command never approves, publishes or changes source/content records.
Regenerate after data edits so reviewers inspect the actual current wording.
"""

from pathlib import Path

from app.services.content_validation import REPRESENTATIVE_PROFILE_IDS, validate_bundle
from app.services.source_snapshots import validate_snapshots
from scripts.validate_content import load_bundle

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    data = ROOT / "data"
    bundle = load_bundle(data)
    report = validate_bundle(bundle)
    errors = report.errors + validate_snapshots(bundle, data)
    if errors:
        raise ValueError("Fix dataset before review: " + "; ".join(errors))
    fragments = {f.fragment_id: f for f in bundle.fragments}
    lines = ["# Stage 0 content review packet", "",
             "Generated from the local dataset. Draft review material, not a patient-facing guide.", "",
             f"Inventory: {len(bundle.profiles)} records; {len(bundle.sources)} source entries; "
             f"{len(bundle.evidence)} evidence spans; {len(bundle.fragments)} fragments; "
             f"{report.published_profiles} published profiles.", "",
             "## How Kajal and the team use this", "",
             "Read each draft alongside its linked evidence and full official source context. "
             "Check wording, true timing, conditions, source permissions and country applicability. "
             "Record requested changes first. A product review is not a clinical review.", "",
             "Current drafts are US reference material. They cannot be served to an IN request. "
             "Changing a country label alone is not localisation. P09/P10 still lack a permitted "
             "exact-week development source, and PP12 needs broader recovery coverage.", "",
             "Reviewer name: PENDING", "Review date: PENDING", "Decision and scope: PENDING", "",
             "## Representative profiles", ""]
    for profile in bundle.profiles:
        if profile.profile_id not in REPRESENTATIVE_PROFILE_IDS:
            continue
        lines.extend([f"### {profile.profile_id}", "", f"Status: {profile.status}. "
                      f"Jurisdiction: {', '.join(profile.jurisdiction)}.", "",
                      f"Working hero label: {profile.hero.title}", "",
                      "Hero evidence: " + ", ".join(profile.hero.development_evidence_ids), ""])
        for slot, ids in profile.card_slots.model_dump().items():
            lines.append(f"- **{slot.replace('_', ' ')}:** " + (", ".join(ids) if ids else "Not populated; do not infer advice."))
        lines.extend(["", "Publication blockers:", ""])
        lines.extend(f"- {blocker}" for blocker in profile.publication_blockers)
        lines.append("")
    lines.extend(["## Draft wording and conditions", ""])
    for fragment in fragments.values():
        scope = fragment.applies_to
        lines.extend([f"### {fragment.fragment_id}", "", fragment.text, "",
                      f"Timing: {scope.stage}, {scope.unit}, {scope.start} to {scope.end}.",
                      "Evidence: " + ", ".join(fragment.evidence_span_ids),
                      "Required confirmed conditions: " + (", ".join(fragment.conditions_required) or "None specified."),
                      "Required confirmed absences: " + (", ".join(fragment.conditions_excluded) or "None specified."), ""])
    lines.extend(["## Evidence locators and scope rationale", "",
                  "Exact selected source text is stored in section_manifest.jsonl and the hashed "
                  "snapshots. This list gives the context needed to check each selection.", ""])
    sources = {s.source_id: s for s in bundle.sources}
    for span in bundle.evidence:
        source = sources[span.source_id]
        lines.extend([f"### {span.evidence_id}", "", f"Source: [{source.title}]({source.canonical_url})",
                      f"Locator: {span.locator}", f"Applicability rationale: {span.applicability_note}",
                      f"Snapshot: `{source.snapshot_path}`", f"Snapshot SHA-256: `{span.source_checksum}`", ""])
    lines.extend(["## Approval sequence", "",
                  "1. Resolve missing evidence and locality decisions; revise draft wording.",
                  "2. Record an actual named review of each selected source and evidence span.",
                  "3. Publish approved evidence before reviewing/publishing dependent fragments.",
                  "4. Review each complete profile, its conditions and remaining empty cards.",
                  "5. Clear blockers only after their stated work is complete, then run the release gate.",
                  "6. Keep superseded content for history; exclude it from selection.", "",
                  "No review identity has been invented. This worksheet itself does not grant approval.", ""])
    path = ROOT / "docs/STAGE-0-REVIEW-PACKET.md"
    path.write_bytes("\n".join(lines).encode("utf-8"))
    print(path)


if __name__ == "__main__":
    main()
