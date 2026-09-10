"""Export the current three-profile Stage 1 specialist review handoff."""

import argparse
from collections import defaultdict
import json
from pathlib import Path

from app.schemas.ingestion import Stage1Audit, Stage1ReviewLedger
from app.services.foundation import read_catalogues, release_fingerprint
from scripts.validate_content import load_bundle

ROOT = Path(__file__).resolve().parents[1]
PROFILE_IDS = ("PC00", "P10", "PP01")
REVIEW_ROLES = ("licence", "content", "clinical", "india_localisation", "product")


def _quoted(text: str) -> list[str]:
    return [f"> {line}" if line else ">" for line in text.splitlines()]


def _target_evidence(bundle) -> dict[str, list[str]]:
    profiles = {profile.profile_id: profile for profile in bundle.profiles}
    fragments = {fragment.fragment_id: fragment for fragment in bundle.fragments}
    evidence_profiles: dict[str, list[str]] = defaultdict(list)
    for profile_id in PROFILE_IDS:
        profile = profiles[profile_id]
        evidence_ids = set(profile.hero.development_evidence_ids)
        for fragment_id in profile.guidance_fragment_ids:
            evidence_ids.update(fragments[fragment_id].evidence_span_ids)
        for evidence_id in sorted(evidence_ids):
            evidence_profiles[evidence_id].append(profile_id)
    return dict(evidence_profiles)


def render(ledger_path: Path, audit_path: Path) -> str:
    bundle = load_bundle(ROOT / "data")
    ledger = Stage1ReviewLedger.model_validate_json(ledger_path.read_text(encoding="utf-8"))
    audit = Stage1Audit.model_validate_json(audit_path.read_text(encoding="utf-8"))

    evidence_profiles = _target_evidence(bundle)
    decisions_by_evidence: dict[str, dict[str, object]] = defaultdict(dict)
    for decision in ledger.decisions:
        if decision.evidence_id in evidence_profiles:
            decisions_by_evidence[decision.evidence_id][decision.role] = decision
    missing = sorted(evidence_id for evidence_id in evidence_profiles
                     if set(decisions_by_evidence[evidence_id]) < {"content", "product"})
    if missing:
        raise ValueError(f"product/content decisions are missing for target evidence: {missing}")

    audit_sources = {source.source_id: source for source in audit.sources}
    for evidence_id, roles in decisions_by_evidence.items():
        decisions = list(roles.values())
        subject = {(decision.task_id, decision.candidate_id, decision.source_id,
                    decision.candidate_checksum) for decision in decisions}
        if len(subject) != 1:
            raise ValueError(f"recorded roles do not bind the same candidate: {evidence_id}")
        decision = decisions[0]
        source_audit = audit_sources.get(decision.source_id)
        if (source_audit is None or evidence_id not in source_audit.evidence_ids
                or decision.candidate_id not in source_audit.candidate_ids
                or decision.task_id not in source_audit.review_task_ids
                or decision.candidate_checksum not in source_audit.candidate_checksums):
            raise ValueError(f"decision is absent or stale in the canonical audit: {evidence_id}")

    evidence = {item.evidence_id: item for item in bundle.evidence}
    sources = {item.source_id: item for item in bundle.sources}
    fragments_by_evidence: dict[str, list] = defaultdict(list)
    for fragment in bundle.fragments:
        for evidence_id in fragment.evidence_span_ids:
            if evidence_id in evidence_profiles:
                fragments_by_evidence[evidence_id].append(fragment)

    catalogues = read_catalogues(ROOT / "data")
    catalogues_by_evidence: dict[str, list] = defaultdict(list)
    for item in catalogues:
        for evidence_id in item.evidence_span_ids:
            if evidence_id in evidence_profiles:
                catalogues_by_evidence[evidence_id].append(item)
    comparisons = [item for item in catalogues if item.kind == "comparison"]
    unsafe_comparisons = [item.item_id for item in comparisons
                          if item.status != "draft"
                          or not item.details.get("hide_reason")
                          or ((item.details.get("measurement_value") is None)
                              != (item.details.get("object_dimension_mm") is None))]
    if unsafe_comparisons:
        raise ValueError("comparison preview gate failed: " + ", ".join(unsafe_comparisons))

    profile_counts = {profile_id: sum(profile_id in profile_ids
                                      for profile_ids in evidence_profiles.values())
                      for profile_id in PROFILE_IDS}
    target_decisions = [decision for decision in ledger.decisions
                        if decision.evidence_id in evidence_profiles]
    role_counts = {role: sum(decision.role == role for decision in target_decisions)
                   for role in REVIEW_ROLES}
    fingerprint = release_fingerprint(ROOT / "data")

    lines = [
        "# Stage 1 PC00/P10/PP01 review handoff",
        "",
        "This is the current reviewer packet for the first demonstration slice. It is generated from "
        "the governed evidence tasks and decision ledger, so task IDs and checksums below name the exact "
        "versions reviewed.",
        "",
        f"- Current Stage 0 release fingerprint: `{fingerprint}`",
        f"- Profiles: `{', '.join(PROFILE_IDS)}`",
        f"- Governed evidence tasks in this slice: **{len(evidence_profiles)}**",
        f"- Recorded product/content decisions: **{len(target_decisions)}**",
        f"- Fetal-size comparisons: **{len(comparisons)} draft and hidden**",
        "- Public corpus and production embeddings: **not released**",
        "- Product approval evidence: [Kajal approval import record](STAGE-1-KAJAL-APPROVAL-IMPORT-RECORD.md)",
        "",
        "## Where this fits in the plan",
        "",
        "1. **Stage 0:** the source registry, evidence, fragments, weekly profiles and comparison proposals exist. "
        "The corrected comparison sequence is recorded, but measurements and object dimensions are blank.",
        "2. **Stage 1:** Kajal's product/content decisions are recorded for this three-profile slice. "
        "The exact remaining work is the licence, clinical and India-localisation review below.",
        "3. **Stage 2:** storage engineering may continue with draft/test-only records. No item in this packet "
        "may enter live RAG until all required roles accept the same checksum and the release gate passes.",
        "4. **Visual gate:** the Streamlit reviewer preview is a draft view. Kajal's final visual decision is "
        "recorded only after specialist corrections are applied and the screens are rendered again.",
        "",
        "## Recorded decisions and remaining people",
        "",
        "| Role | Current decisions in this slice | Next action |",
        "|---|---:|---|",
        f"| Product | {role_counts['product']} accepted by Kajal | Recheck rendered screens after specialist changes |",
        f"| Content | {role_counts['content']} accepted by Kajal | Recheck only if wording changes |",
        f"| Clinical | {role_counts['clinical']} | Qualified maternal-health clinician reviews every task below |",
        f"| India localisation | {role_counts['india_localisation']} | India maternal-health reviewer checks local meaning, terms and availability |",
        f"| Licence | {role_counts['licence']} | Source/licence reviewer checks reuse, quotation, attribution and prototype/public-display scope |",
        "",
        "A reviewer must use their real name, capacity/qualification and review date. A team member must "
        "not fill these fields on their behalf. `accepted` means only that the named reviewer accepts the "
        "exact candidate version within that role.",
        "",
        "## Profile coverage",
        "",
        "| Profile | Meaning | Evidence tasks | Product/content state |",
        "|---|---|---:|---|",
        f"| PC00 | Possible pregnancy, not confirmed | {profile_counts['PC00']} | Accepted by Kajal |",
        f"| P10 | Confirmed pregnancy, week 10 | {profile_counts['P10']} | Accepted by Kajal |",
        f"| PP01 | First week after birth | {profile_counts['PP01']} | Accepted by Kajal |",
        "",
        "## Specialist review queue",
        "",
    ]

    for profile_id in PROFILE_IDS:
        lines.extend([f"### {profile_id}", ""])
        profile_evidence = sorted(evidence_id for evidence_id, profile_ids
                                  in evidence_profiles.items() if profile_id in profile_ids)
        for evidence_id in profile_evidence:
            evidence_record = evidence[evidence_id]
            source = sources[evidence_record.source_id]
            current = decisions_by_evidence[evidence_id]
            decision_subject = next(iter(current.values()))
            pending = [role for role in REVIEW_ROLES if role not in current]
            proposed = fragments_by_evidence.get(evidence_id, [])
            linked_records = [*proposed, *catalogues_by_evidence.get(evidence_id, [])]
            required = sorted({condition for record in linked_records
                               for condition in record.conditions_required})
            excluded = sorted({condition for record in linked_records
                               for condition in record.conditions_excluded})
            lines.extend([
                f"#### {evidence_id}", "",
                f"- Task: `{decision_subject.task_id}`",
                f"- Candidate: `{decision_subject.candidate_id}`",
                f"- Candidate checksum: `{decision_subject.candidate_checksum}`",
                f"- Source: [{source.title}]({source.canonical_url}) (`{source.source_id}`)",
                f"- Source jurisdiction: `{', '.join(source.jurisdiction)}`",
                f"- Source reuse state: `{source.reuse_status}` — {source.license_or_reuse_note}",
                f"- Timing: `{evidence_record.applies_to.stage}` / `{evidence_record.applies_to.unit}` / "
                f"`{evidence_record.applies_to.start}–{evidence_record.applies_to.end}`",
                f"- Required conditions: `{', '.join(required) or 'none'}`",
                f"- Excluded conditions: `{', '.join(excluded) or 'none'}`",
                f"- Recorded roles: `{', '.join(sorted(current)) or 'none'}`",
                f"- Pending roles: `{', '.join(pending) or 'none'}`",
                "",
                "**Exact selected source text**",
                "",
            ])
            lines.extend(_quoted(evidence_record.text))
            lines.extend(["", "**Proposed user-facing wording**", ""])
            if proposed:
                lines.extend(f"- {fragment.text} (`{fragment.fragment_id}`)"
                             for fragment in proposed)
            else:
                lines.append("- Hero/source evidence only; see the profile title and measurement display.")
            lines.extend(["", "**Decisions already recorded**", ""])
            for role in sorted(current):
                decision = current[role]
                lines.append(
                    f"- `{role}` — **{decision.decision}** by {decision.reviewer_name} "
                    f"({decision.reviewer_capacity}) on {decision.reviewed_at}: {decision.reason}")
            lines.extend([
                "", "**Each remaining reviewer records one decision**", "",
                "```text",
                f"Task ID: {decision_subject.task_id}",
                f"Candidate ID: {decision_subject.candidate_id}",
                f"Evidence ID: {decision_subject.evidence_id}",
                f"Source ID: {decision_subject.source_id}",
                f"Role: {' | '.join(pending)}",
                "Decision: accepted | changes_requested | rejected | needs_specialist_review",
                "Reviewer name:",
                "Reviewer capacity/qualification:",
                "Review date: YYYY-MM-DD",
                "Reason:",
                "Exact replacement wording (required when wording changes):",
                "Supporting reference:",
                "Timing/week change:",
                "Condition change:",
                "Jurisdiction change:",
                f"Candidate checksum: {decision_subject.candidate_checksum}",
                "```", "",
            ])

    lines.extend([
        "## Rendered draft previews",
        "",
        "These images are reviewer-only artifacts generated from the current governed records. "
        "They must be regenerated if a specialist review changes wording, timing or conditions.",
        "",
        "- [PC00 default review](previews/PC00-review.jpg)",
        "- [P10 default review](previews/P10-review.jpg)",
        "- [P10 movement facts missing](previews/P10-movement-missing.jpg)",
        "- [P10 movement clearance recorded](previews/P10-movement-cleared.jpg)",
        "- [PP01 default review](previews/PP01-review.jpg)",
        "- [PP01 feeding details missing](previews/PP01-diet-missing.jpg)",
        "- [PP01 caesarean movement conditions](previews/PP01-movement-caesarean.jpg)",
        "",
        "## Release and visual-review gates",
        "",
        "- [ ] A real licence decision exists for all 27 exact tasks.",
        "- [ ] A qualified clinical decision exists for all 27 exact tasks.",
        "- [ ] A real India-localisation decision exists for all 27 exact tasks.",
        "- [ ] Every requested correction is applied and creates fresh checksums/packets.",
        "- [ ] Kajal reviews the freshly rendered PC00, P10 and PP01 screens.",
        "- [ ] All 42 comparison records remain hidden until measurement convention, source values, "
        "object dimensions and artwork/licensing are independently verified.",
        "- [ ] The five-role release gate passes before public embeddings or live RAG are created.",
        "",
        "Checking a box in this Markdown file does not alter the governed ledger. Decisions must be "
        "entered in `data/reviews/ingestion_decisions.json`; the Stage 1 checker rejects stale task IDs "
        "and candidate checksums.",
        "",
    ])
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-decisions", type=Path,
                        default=ROOT / "data/reviews/ingestion_decisions.json")
    parser.add_argument("--audit", type=Path,
                        default=ROOT / "data/ingestion/audit/stage1-source-audit.json")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "docs/STAGE-1-PC00-P10-PP01-REVIEW-HANDOFF.md")
    args = parser.parse_args(argv)
    content = render(args.review_decisions, args.audit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(content, encoding="utf-8", newline="\n")
    print(json.dumps({"output": str(args.output), "profiles": list(PROFILE_IDS)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
