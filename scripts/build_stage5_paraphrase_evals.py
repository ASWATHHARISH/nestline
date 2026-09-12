"""Build a separate frozen Stage 5 paraphrase set from existing expected truth."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "evals/stage5_retrieval_development.jsonl"
OUTPUT = ROOT / "evals/stage5_retrieval_paraphrases_v1.jsonl"

PARAPHRASES = [
    ("S5-PERSONAL-ALLERGY-001", "PARA-ALLERGY-IN-01", "my confirmed allergy record pls?"),
    ("S5-GRAPH-ON-001", "PARA-GRAPH-IN-01", "why exercise plan stale after restriction, tell me"),
    ("S5-CONFLICT-IRRELEVANT-001", "PARA-NUTRITION-IN-01", "week 24 protein food ideas pls"),
    ("S5-COND-EXCLUDE-001", "PARA-MOVEMENT-IN-01", "movement guidance with my restriction, week 24"),
    ("S5-JOURNEY-001", "PARA-JOURNEY-IN-01", "tell me what matters in 24th week"),
    ("S5-WELLBEING-001", "PARA-WELLBEING-IN-01", "wellbeing routine for week 24 pls"),
    ("S5-SYMPTOMS-001", "PARA-SYMPTOM-RECORD-IN-01", "week 24 symptoms record how?"),
    ("S5-PREPARATION-001", "PARA-PREPARATION-IN-01", "questions prep for wk 24 pls"),
    ("S5-FOLLOWUP-001", "PARA-FOLLOWUP-IN-01", "follow up my questions in week 24"),
    ("S5-MEDICATION-001", "PARA-MEDICATION-IN-01", "medicines documented in my record pls"),
    ("S5-APPOINTMENT-001", "PARA-APPOINTMENT-IN-01", "next doctor appointment when?"),
    ("S5-PP-DAY-001", "PARA-POSTPARTUM-IN-01", "after delivery day 3, what preparation?"),
]


def build_set() -> list[dict]:
    originals = {
        row["case_id"]: row
        for row in (
            json.loads(line) for line in SOURCE.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }
    rows = []
    for source_id, case_id, question in PARAPHRASES:
        row = deepcopy(originals[source_id])
        row.update({
            "case_id": case_id,
            "question": question,
            "paraphrase_of": source_id,
            "dataset_version": "stage5-paraphrases-v1",
            "frozen_before_run": True,
            "language_scope": "English including concise/noisy Indian-English phrasing",
        })
        rows.append(row)
    return rows


def main() -> int:
    rows = build_set()
    OUTPUT.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8", newline="\n",
    )
    print(f"wrote {len(rows)} frozen paraphrases to {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())