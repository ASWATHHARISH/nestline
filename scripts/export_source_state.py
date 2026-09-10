"""Export current source states from actual dependencies; retain audit history."""

from collections import Counter
from datetime import date
import json
from pathlib import Path

from app.services.foundation import read_catalogues, source_freshness
from scripts.validate_content import load_bundle

ROOT = Path(__file__).resolve().parents[1]


def main():
    data = ROOT / "data"
    bundle = load_bundle(data)
    items = read_catalogues(data)
    referenced = {ref for p in bundle.profiles for ref in p.source_evidence_ids + p.hero.development_evidence_ids}
    referenced |= {ref for item in items for ref in item.evidence_span_ids}
    rows = []
    for source in bundle.sources:
        selected = [e for e in bundle.evidence if e.source_id == source.source_id]
        rows.append(dict(source_id=source.source_id, url=source.canonical_url, state=source.status,
                         permission_researched=source.reuse_status == "permitted", allowed_use=source.allowed_use,
                         snapshotted=bool(source.snapshot_path), evidence_count=len(selected),
                         assembled=any(e.evidence_id in referenced for e in selected),
                         human_source_review=source.review is not None,
                         published_evidence=sum(e.status == "published" for e in selected),
                         source_country=source.jurisdiction,
                         freshness_issues=source_freshness(source, date.today()) if selected else ["not admitted to content corpus"]))
    report = dict(checked_on=date.today().isoformat(),
                  interpretation="Permission researched is a documented reuse assessment, not a named legal approval. Assembled can mean draft.",
                  summary=dict(registered=len(rows), permission_researched=sum(r["permission_researched"] for r in rows),
                               snapshotted=sum(r["snapshotted"] for r in rows), assembled=sum(r["assembled"] for r in rows),
                               human_source_review=sum(r["human_source_review"] for r in rows),
                               published_evidence=sum(r["published_evidence"] for r in rows)),
                  catalogues=dict(Counter(i.kind for i in items)), sources=rows)
    (ROOT / "docs/STAGE-0-SOURCE-STATE.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8", newline="\n")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
