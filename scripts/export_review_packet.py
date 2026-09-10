"""Create a readable content-review worksheet from the maintained dataset.

This command never approves, publishes or changes source/content records.
Regenerate after data edits so reviewers inspect the actual current wording.
"""

import argparse
from pathlib import Path
import json

from app.services.content_validation import REPRESENTATIVE_PROFILE_IDS, REQUIRED_DAY_IDS, validate_bundle
from app.services.foundation import read_catalogues, release_fingerprint, validate_foundation
from app.services.source_snapshots import validate_snapshots
from scripts.validate_content import load_bundle

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "docs/STAGE-0-REVIEW-PACKET.md")
    args = parser.parse_args(argv)
    data = ROOT / "data"
    bundle = load_bundle(data)
    report = validate_bundle(bundle)
    errors = report.errors + validate_snapshots(bundle, data) + validate_foundation(bundle, data)
    if errors:
        raise ValueError("Fix dataset before review: " + "; ".join(errors))
    fragments = {f.fragment_id: f for f in bundle.fragments}
    digest = release_fingerprint(data)
    audits = {r["fragment_id"]: r for r in [json.loads(line) for line in
              (data / "reviews/claim_audit.jsonl").read_text(encoding="utf-8").splitlines() if line]}
    lines = ["# Stage 0 content review packet", "",
             "Generated from the local dataset. Draft review material, not a patient-facing guide.", "",
             f"Inventory: {len(bundle.profiles)} records; {len(bundle.sources)} source entries; "
             f"{len(bundle.evidence)} evidence spans; {len(bundle.fragments)} fragments; "
             f"{report.published_profiles} published profiles.", "",
             "## How Kajal and the team use this", "",
             "Read each draft alongside its linked evidence and full official source context. "
             "Check wording, true timing, conditions, source permissions and country applicability. "
             "Record requested changes first. A product review is not a clinical review.", "",
             "Nine representative profiles and eight early-day overlays are proposed Indian educational content. Original source countries "
             "remain unchanged; each adopted foreign passage has an explicit, unapproved localisation "
             "record. Nothing is published. BHC week 9/10 text is quotation-only and was last reviewed "
             "by that publisher in 2012: explicitly review currency before approving it. NHM CHO use "
             "is limited to free distribution. This is not commercial launch clearance.", "",
             f"Release review fingerprint: `{digest}`", "",
             "Review this exact dataset version. Any content change requires a new packet and review.", "",
             "Reviewer name: PENDING", "Review date: PENDING", "Decision and scope: PENDING", "",
             "## Representative profiles", ""]
    for profile in bundle.profiles:
        if profile.profile_id not in REPRESENTATIVE_PROFILE_IDS | REQUIRED_DAY_IDS:
            continue
        lines.extend([f"### {profile.profile_id}", "", f"Status: {profile.status}. "
                      f"Jurisdiction: {', '.join(profile.jurisdiction)}.", "",
                      f"Working hero label: {profile.hero.title}", "",
                      "Hero evidence: " + ", ".join(profile.hero.development_evidence_ids), ""])
        for slot, ids in profile.card_slots.model_dump().items():
            lines.append(f"- **{slot.replace('_', ' ')}:**")
            if not ids:
                lines.append("  " + profile.slot_notes.get(slot, "Not populated; do not infer advice."))
            for ref in ids:
                fragment = fragments[ref]
                wording = f'\"{fragment.text}\"' if fragment.presentation == "quotation" else fragment.text
                lines.append(f"  {wording} (`{ref}`)")
                if fragment.conditions_required:
                    lines.append("  Show only when confirmed: " + ", ".join(fragment.conditions_required) + ".")
                if fragment.conditions_excluded:
                    lines.append("  Also confirm absence of: " + ", ".join(fragment.conditions_excluded) + ".")
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
        lines.extend(["Codex assessment (not human approval): " + audits[fragment.fragment_id]["rationale"], ""])
    lines.extend(["## Evidence locators and scope rationale", "",
                  "Exact selected source text is stored in section_manifest.jsonl and the hashed "
                  "snapshots. This list gives the context needed to check each selection.", ""])
    sources = {s.source_id: s for s in bundle.sources}
    for span in bundle.evidence:
        source = sources[span.source_id]
        lines.extend([f"### {span.evidence_id}", "", f"Source: [{source.title}]({source.canonical_url})",
                      f"Original country: {', '.join(source.jurisdiction)}; proposed evidence country: {', '.join(span.jurisdiction)}.",
                      f"Selected exact text: “{span.text}”",
                      f"Locator: {span.locator}", f"Applicability rationale: {span.applicability_note}",
                      f"Delivery: {source.delivery_mode}. Reuse: {source.license_or_reuse_note}",
                      "Localisation: " + (span.localisation.rationale + " Named review pending." if span.localisation and not span.localisation.review
                                          else "See recorded review." if span.localisation else "No cross-country adoption proposed."),
                      f"Snapshot: `{source.snapshot_path}`", f"Snapshot SHA-256: `{span.source_checksum}`", ""])
    lines.extend(["## Catalogue proposals", "",
                  "All items below are drafts. Editorial steps are proposals, not clinically validated interventions.", ""])
    for item in read_catalogues(data):
        lines.extend([f"### {item.item_id}: {item.title}", "", item.description, "",
                      "Evidence: " + (", ".join(item.evidence_span_ids) or "None: hidden comparison proposal."),
                      "Required: " + (", ".join(item.conditions_required) or "None specified."),
                      "Excluded: " + (", ".join(item.conditions_excluded) or "None specified."), "",
                      "```json", json.dumps(item.details, indent=2, ensure_ascii=False), "```", ""])
    lines.extend(["## Actual human decisions still required", "",
                  "Record actual licence, content, clinical, India-localisation and product decisions in "
                  "data/reviews/approvals.json. Each needs the role, reviewer, qualification_or_capacity, "
                  "reviewed_at, disposition, release_checksum (the fingerprint above), and notes. "
                  "Use changes_requested when revisions are needed. Do not insert a person's name without their actual review. "
                  "A JSON record cannot authenticate that person; repository review/account controls remain required.", "",
                  "Read STAGE-0-CORRECTION-STATUS.md for unresolved source currency, safety and comparison work. "
                  "Read data/safety/rule_spec.yaml and evals/phase_1_contract.jsonl before approving safety/product behaviour. "
                  "All 64 software cases are visible; they are not a sealed clinical or AI benchmark.", "",
                  "## Approval sequence", "",
                  "1. Resolve missing evidence and locality decisions; revise draft wording.",
                  "2. Record an actual named review of each selected source and evidence span.",
                  "3. Publish approved evidence before reviewing/publishing dependent fragments.",
                  "4. Review each complete profile, its conditions and remaining empty cards.",
                  "5. Clear blockers only after their stated work is complete, then run the release gate.",
                  "6. Keep superseded content for history; exclude it from selection.", "",
                  "No review identity has been invented. This worksheet itself does not grant approval.", ""])
    path = args.output
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes("\n".join(lines).encode("utf-8"))
    print(path)


if __name__ == "__main__":
    main()
