"""Render an ingestion run as a reviewer-friendly Markdown queue."""

import argparse
from pathlib import Path

from app.schemas.ingestion import IngestionRun, Stage1ReviewLedger
from app.services.public_ingestion import apply_review_decisions


def render(run: IngestionRun) -> str:
    lines = [f"# Ingestion review — {run.admission.source_id}", "",
             f"- Run: `{run.run_id}`", f"- Outcome: **{run.outcome}**",
             f"- Admission: `{run.admission.decision}`",
             f"- Source artifact: `{run.artifact.original_sha256 if run.artifact else 'not stored'}`",
             f"- Candidate units: {len(run.candidates)}",
             f"- Pending review tasks: {len(run.review_tasks)}", "",
             "## Admission reasons", ""]
    lines.extend(f"- {reason}" for reason in run.admission.reasons)
    lines.extend(["", "## Parser and validation issues", ""])
    if run.issues:
        lines.extend(f"- **{issue.severity.upper()} `{issue.code}`:** {issue.message}"
                     for issue in run.issues)
    else:
        lines.append("- None.")
    lines.extend(["", "## Human review queue", ""])
    if not run.review_tasks:
        lines.append("No pending review tasks were generated.")
    candidates = {candidate.candidate_id: candidate for candidate in run.candidates}
    for task in run.review_tasks:
        candidate = candidates[task.candidate_id]
        decided_roles = {decision.role for decision in task.decisions}
        pending_roles = [role for role in task.required_roles if role not in decided_roles]
        measurements = ", ".join(
            f"{measurement.value if measurement.value is not None else f'{measurement.minimum}–{measurement.maximum}'} "
            f"{measurement.unit}" for measurement in candidate.development_measurements)
        lines.extend([f"### {task.task_id}", "",
                      f"- Evidence: `{task.evidence_id}`",
                      f"- Locator: `{candidate.source_locator}`",
                      f"- Applies to: `{candidate.applies_to.stage}` "
                      f"`{candidate.applies_to.unit} {candidate.applies_to.start}–{candidate.applies_to.end}`",
                      f"- Jurisdiction: `{', '.join(candidate.jurisdiction)}`",
                      f"- Domains: `{', '.join(candidate.domains)}`",
                      f"- Dashboard slots: `{', '.join(candidate.display_slots)}`",
                      f"- General development measurements: `{measurements or 'none'}`",
                      f"- Future personal facts: `{', '.join(candidate.personal_fact_dependencies)}`",
                      f"- Profiles: `{', '.join(candidate.linked_profile_ids) or 'none'}`",
                      f"- Catalogue items: `{', '.join(candidate.linked_catalogue_item_ids) or 'none'}`",
                      f"- Required review roles: `{', '.join(task.required_roles)}`",
                      f"- Current task status: `{task.status}`",
                      f"- Pending review roles: `{', '.join(pending_roles) or 'none'}`",
                      "", "**Exact selected source text**", "", f"> {candidate.original_text}", "",
                      "**Why it is blocked**", ""])
        lines.extend(f"- {reason}" for reason in task.blocking_reasons)
        lines.extend(["", "**Reviewer checklist**", ""])
        lines.extend(f"- [ ] {check.replace('_', ' ')}" for check in task.required_checks)
        lines.extend(["", "**Recorded governed decisions**", ""])
        if task.decisions:
            lines.extend(
                f"- `{decision.role}` — **{decision.decision}** by {decision.reviewer_name} "
                f"({decision.reviewer_capacity}) on {decision.reviewed_at}: {decision.reason}"
                for decision in task.decisions
            )
        else:
            lines.append("- None.")
        lines.extend(["", "**Record one decision for each pending reviewer role**", "",
                      "```text",
                      f"Task ID: {task.task_id}",
                      f"Candidate ID: {task.candidate_id}",
                      f"Evidence ID: {task.evidence_id}",
                      f"Source ID: {task.source_id}",
                      f"Role: {' | '.join(pending_roles) if pending_roles else 'no pending role'}",
                      "Decision: accepted | changes_requested | rejected | needs_specialist_review",
                      "Reviewer name:", "Reviewer capacity/qualification:", "Review date: YYYY-MM-DD",
                      "Reason:", "Exact replacement wording (when changing):",
                      "Supporting reference:", "Timing/week change:", "Condition change:",
                      "Jurisdiction change:", f"Candidate checksum: {task.candidate_checksum}",
                      "```", ""])
    lines.extend(["", "A checked box in this exported document does not change publication state. "
                  "The named decision must be entered into the governed source, evidence, fragment, "
                  "profile and catalogue records, then the ingestion run must be repeated. "
                  "Machine-readable decisions belong in data/reviews/ingestion_decisions.json; "
                  "the ingestion command rejects unknown task IDs and changed checksums.", ""])
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="append", type=Path,
                        help="schema-valid ingestion run; repeat for more than one")
    parser.add_argument("--run-directory", type=Path,
                        help="directory containing stage1-*.json dry-run files")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--review-decisions", type=Path,
                        help="optional schema-valid role-decision ledger to join to current tasks")
    args = parser.parse_args(argv)
    paths = list(args.run or [])
    if args.run_directory:
        paths.extend(sorted(args.run_directory.glob("stage1-*.json")))
    if not paths:
        parser.error("supply at least one --run or --run-directory")
    runs = [IngestionRun.model_validate_json(path.read_text(encoding="utf-8")) for path in paths]
    if args.review_decisions:
        ledger = Stage1ReviewLedger.model_validate_json(
            args.review_decisions.read_text(encoding="utf-8"))
        runs = [apply_review_decisions(run, ledger.decisions) for run in runs]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n\n---\n\n".join(render(run) for run in runs),
                           encoding="utf-8", newline="\n")
    print(args.output)


if __name__ == "__main__":
    main()
