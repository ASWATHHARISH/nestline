"""Build the isolated, conspicuously fictional Stage 5 corpus and frozen dev truth."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from uuid import UUID

from app.services.embeddings import DeterministicTestEmbeddingProvider

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data/synthetic/stage5_retrieval_fixtures.json"
DEVSET = ROOT / "evals/stage5_retrieval_development.jsonl"

OWNER_A = "11111111-1111-4111-8111-111111111111"
OWNER_B = "22222222-2222-4222-8222-222222222222"
WORKSPACE_A = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
WORKSPACE_B = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
RELEASE = "55555555-5555-4555-8555-555555555555"
NOW = "2026-09-11T00:00:00Z"


def digest(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def public_record(candidate_id: str, evidence_id: str, text: str, *,
                  domain: str, stage: str = "pregnancy", unit: str = "week",
                  start: int | None = 24, end: int | None = 24,
                  jurisdiction: list[str] | None = None,
                  release_status: str = "published",
                  source_status: str = "published",
                  candidate_status: str = "published",
                  retired: bool = False, authority: float = 0.9,
                  applicability: float = 1.0) -> dict:
    source_id = f"SRC-{candidate_id}"
    span = {"source_id": source_id, "evidence_id": evidence_id,
            "source_block_ids": [f"BLOCK-{candidate_id}"], "page": 1,
            "locator": f"fixture/{candidate_id}", "start_char": 0,
            "end_char": len(text), "exact_text": text,
            "text_sha256": digest(text)}
    candidate = {
        "candidate_id": candidate_id, "evidence_id": evidence_id,
        "source_id": source_id, "source_title": f"Synthetic source {candidate_id}",
        "text": text, "evidence_lane": "guideline", "domain": domain,
        "journey": {"stage": stage, "unit": unit, "exact": start if start == end else None,
                    "range_start": start if start != end else None,
                    "range_end": end if start != end else None},
        "jurisdictions": jurisdiction or ["IN"], "conditions_required": [],
        "conditions_excluded": [], "release_status": "published",
        "source_status": "published", "candidate_status": "published",
        "allowed_use": ["store", "embed", "display"], "spans": [span],
        "authority_score": authority, "applicability_score": applicability,
        "provenance": {"corpus_version": "stage5-fixture-v1",
                       "release_id": RELEASE,
                       "release_fingerprint": "5" * 64,
                       "source_version": "fixture-1.0",
                       "embedding_provider": "TEST_ONLY",
                       "embedding_model": "sha256-test-vector-v1",
                       "filter_version": "stage5-filter-v1",
                       "fixture_only": True}}
    embedding = DeterministicTestEmbeddingProvider().embed([text])[0]
    return {"release_status": release_status, "source_status": source_status,
            "candidate_status": candidate_status, "retired": retired,
            "embedding": embedding, "candidate": candidate}


def personal_fact(fact_id: str, fact_type: str, value, *, record_only=False) -> dict:
    return {"fact_id": fact_id, "fact_type": fact_type, "value": value,
            "source_kind": "human_reviewed", "confirmation_status": "confirmed",
            "record_only": record_only, "source_document_id": None,
            "source_document_fact_id": None, "valid_from": NOW,
            "valid_to": None, "provenance": {"fixture": "Maya fictional"}}


def passage(workspace: str, chunk_id: str, document_id: str, text: str,
            *, status="confirmed", confirmation="confirmed") -> dict:
    candidate_id = f"personal-{chunk_id}"
    candidate = {"candidate_id": candidate_id, "chunk_id": chunk_id,
                 "document_id": document_id, "document_status": "confirmed",
                 "text": text,
                 "span": {"source_id": f"private:{document_id}",
                          "source_block_ids": [], "page": 1,
                          "locator": "fictional-document/page/1", "start_char": 0,
                          "end_char": len(text), "exact_text": text,
                          "text_sha256": digest(text)},
                 "provenance": {"corpus_version": "personal-state-v1",
                                "source_version": "review-1",
                                "embedding_provider": "TEST_ONLY",
                                "embedding_model": "sha256-test-vector-v1",
                                "filter_version": "stage5-filter-v1",
                                "fixture_only": True}}
    return {"workspace_id": workspace, "care_episode_id": workspace,
            "document_status": status, "confirmation_status": confirmation,
            "embedding": DeterministicTestEmbeddingProvider().embed([text])[0],
            "candidate": candidate}


def node(node_id: str, node_type: str, label: str, entity: str,
         document: str | None = None) -> dict:
    return {"node_id": node_id, "node_type": node_type, "entity_id": entity,
            "label": label, "source_document_id": document}


def edge(edge_id: str, relation: str, source: str, target: str) -> dict:
    return {"edge_id": edge_id, "relation": relation,
            "from_node_id": source, "to_node_id": target}


def build_fixture() -> dict:
    public = [
        public_record("PUB-NUT-24", "EV-NUT-24", "At week 24, include varied protein foods and discuss individual dietary restrictions with a qualified professional.", domain="nutrition"),
        public_record("PUB-MOVE-24", "EV-MOVE-24", "At week 24, gentle movement depends on confirmed restrictions and individual clinical guidance.", domain="movement"),
        public_record("PUB-NUT-GENERAL-1", "EV-NUT-GENERAL-1", "Choose a varied pattern of meals from eligible food groups.", domain="nutrition", start=20, end=28, authority=0.7, applicability=0.7),
    ]
    for index in range(1, 8):
        public.append(public_record(
            f"PUB-NUT-DECOY-{index}", f"EV-NUT-DECOY-{index}",
            f"Synthetic general nutrition passage number {index} about hydration and meal variety.",
            domain="nutrition", start=20, end=28, authority=0.4,
            applicability=0.6))
    public.extend([
        public_record("DECOY-WEEK-12", "EV-DECOY-WEEK-12", "Week 12 protein guidance decoy.", domain="nutrition", start=12, end=12),
        public_record("DECOY-US-24", "EV-DECOY-US-24", "US-only week 24 protein decoy.", domain="nutrition", jurisdiction=["US"]),
        public_record("DECOY-POSTPARTUM", "EV-DECOY-POSTPARTUM", "Postpartum nutrition decoy.", domain="nutrition", stage="postpartum", start=2, end=2),
        public_record("DECOY-DRAFT", "EV-DECOY-DRAFT", "Draft week 24 protein decoy.", domain="nutrition", release_status="draft"),
        public_record("DECOY-REJECTED", "EV-DECOY-REJECTED", "Rejected week 24 protein decoy.", domain="nutrition", source_status="rejected"),
        public_record("DECOY-RETIRED", "EV-DECOY-RETIRED", "Retired week 24 protein decoy.", domain="nutrition", retired=True),
    ])

    fact_allergy = personal_fact(
        "a1111111-1111-4111-8111-111111111111", "allergy",
        {"substance": "peanut", "subject": "Maya (fictional)"})
    fact_restriction = personal_fact(
        "a2222222-2222-4222-8222-222222222222", "dietary_restriction",
        {"restriction": "avoid high-impact movement", "subject": "Maya (fictional)"})
    proposed = personal_fact(
        "a3333333-3333-4333-8333-333333333333", "medical_history",
        {"condition": "unconfirmed fixture proposal"})
    conflict = personal_fact(
        "a4444444-4444-4444-8444-444444444444", "medical_history",
        {"condition": "unresolved fixture conflict"})
    superseded = personal_fact(
        "a5555555-5555-4555-8555-555555555555", "allergy",
        {"substance": "historical fixture value"})

    doc = "d1111111-1111-4111-8111-111111111111"
    restriction = fact_restriction["fact_id"]
    plan_item = "d2222222-2222-4222-8222-222222222222"
    plan = "d3333333-3333-4333-8333-333333333333"
    node_ids = ["e1111111-1111-4111-8111-111111111111",
                "e2222222-2222-4222-8222-222222222222",
                "e3333333-3333-4333-8333-333333333333",
                "e4444444-4444-4444-8444-444444444444"]
    path = {"path_id": "PATH-DOC-RESTRICTION-STALE-PLAN",
            "workspace_id": WORKSPACE_A,
            "nodes": [node(node_ids[0], "document", "Maya fictional report", doc, doc),
                      node(node_ids[1], "restriction", "Confirmed movement restriction", restriction, doc),
                      node(node_ids[2], "plan_item", "Movement plan item", plan_item),
                      node(node_ids[3], "plan", "Stale weekly plan", plan)],
            "edges": [edge("f1111111-1111-4111-8111-111111111111", "EXTRACTED_FROM", node_ids[0], node_ids[1]),
                      edge("f2222222-2222-4222-8222-222222222222", "CONSTRAINS", node_ids[1], node_ids[2]),
                      edge("f3333333-3333-4333-8333-333333333333", "TRIGGERED", node_ids[2], node_ids[3])],
            "depth": 3,
            "provenance": {"fixture_only": True, "document_id": doc}}

    return {
        "schema_version": "stage5-fixture-v1", "contains_real_medical_data": False,
        "production_release": False, "active_corpus_version": "stage5-fixture-v1",
        "active_release_id": RELEASE,
        "workspace_owners": {WORKSPACE_A: OWNER_A, WORKSPACE_B: OWNER_B},
        "public_records": public,
        "personal_fact_records": [
            {"workspace_id": WORKSPACE_A, "confirmation_status": "confirmed", "superseded": False, "valid_to": None, "candidate": fact_allergy},
            {"workspace_id": WORKSPACE_A, "confirmation_status": "confirmed", "superseded": False, "valid_to": None, "candidate": fact_restriction},
            {"workspace_id": WORKSPACE_A, "confirmation_status": "proposed", "superseded": False, "valid_to": None, "candidate": proposed},
            {"workspace_id": WORKSPACE_A, "confirmation_status": "conflict", "superseded": False, "valid_to": None, "candidate": conflict},
            {"workspace_id": WORKSPACE_A, "confirmation_status": "confirmed", "superseded": True, "valid_to": NOW, "candidate": superseded}],
        "personal_contexts": {
            WORKSPACE_A: {
                "journey_state": {"state_id": "c1111111-1111-4111-8111-111111111111", "stage": "pregnancy", "timing_source": "manual_week_day", "gestational_week": 24, "gestational_day": 2, "postpartum_week": None, "postpartum_day": None, "approximate_month_min": None, "approximate_month_max": None, "user_confirmed": True, "has_dating_conflict": False, "version": 3},
                "confirmed_facts": [],
                "medications": [{"medication_id": "c2222222-2222-4222-8222-222222222222", "name_as_written": "Fictional supplement record", "context_text": "record only", "status": "confirmed", "record_only": True}],
                "symptoms": [{"symptom_id": "c3333333-3333-4333-8333-333333333333", "description": "fictional prior symptom record", "reported_at": NOW, "safety_route": "no_match", "matched_rule_ids": [], "safety_evaluation_only": True}],
                "appointments": [{"appointment_id": "c4444444-4444-4444-8444-444444444444", "scheduled_for": "2026-09-20T09:00:00Z", "appointment_type": "fictional check-up", "status": "confirmed"}],
                "plan_states": [{"plan_id": plan, "version": 2, "status": "stale", "stale_reasons": ["confirmed_restriction_changed"]}],
                "open_questions": [], "unresolved_conflicts": [], "missing_information": []},
            WORKSPACE_B: {
                "journey_state": None, "confirmed_facts": [], "medications": [], "symptoms": [], "appointments": [], "plan_states": [], "open_questions": [],
                "unresolved_conflicts": [{"conflict_id": "c5555555-5555-4555-8555-555555555555", "fact_type": "medical_history", "proposed_values": ["fictional value A", "fictional value B"], "source_document_ids": [], "clarification_question_ids": [], "state": "requires_clarification"}],
                "missing_information": [{"field": "journey_week", "reason": "No confirmed journey timing", "required_for": ["week-specific guidance"]}]}}
        ,"personal_passages": [
            passage(WORKSPACE_A, "b1111111-1111-4111-8111-111111111111", doc, "Maya fictional record states a confirmed peanut allergy."),
            passage(WORKSPACE_B, "b2222222-2222-4222-8222-222222222222", "d9999999-9999-4999-8999-999999999999", "Other fictional workspace private passage.", confirmation="proposed"),
            passage(WORKSPACE_A, "b3333333-3333-4333-8333-333333333333", doc, "Unconfirmed private proposal decoy.", confirmation="proposed")],
        "weekly_profiles": [],
        "graph_paths": [{"keywords": ["why", "stale", "plan", "restriction"], "path": path},
                        {"keywords": ["cycle"], "path": {**path, "path_id": "DECOY-CYCLE", "nodes": [path["nodes"][0], path["nodes"][1], path["nodes"][0]], "edges": path["edges"][:2], "depth": 2}}]
    }


def build_devset() -> list[dict]:
    base = {"stage": "pregnancy", "unit": "week", "exact": 24,
            "range_start": None, "range_end": None}
    forbidden = ["EV-DECOY-WEEK-12", "EV-DECOY-US-24", "EV-DECOY-POSTPARTUM",
                 "EV-DECOY-DRAFT", "EV-DECOY-REJECTED", "EV-DECOY-RETIRED"]
    return [
        {"case_id": "S5-NUT-001", "question": "What protein foods matter at week 24?", "domain": "nutrition", "journey": base, "jurisdiction": "IN", "workspace_id": WORKSPACE_A, "owner_id": OWNER_A, "expected_public_evidence_ids": ["EV-NUT-24"], "expected_personal_fact_ids": ["a1111111-1111-4111-8111-111111111111", "a2222222-2222-4222-8222-222222222222"], "expected_graph_path_ids": [], "forbidden_evidence_ids": forbidden, "expected_behavior": "evidence", "criticality": "medium"},
        {"case_id": "S5-MOVE-001", "question": "What gentle movement fits week 24?", "domain": "movement", "journey": base, "jurisdiction": "IN", "workspace_id": WORKSPACE_A, "owner_id": OWNER_A, "expected_public_evidence_ids": ["EV-MOVE-24"], "expected_personal_fact_ids": ["a1111111-1111-4111-8111-111111111111", "a2222222-2222-4222-8222-222222222222"], "expected_graph_path_ids": [], "forbidden_evidence_ids": forbidden, "expected_behavior": "evidence", "criticality": "high"},
        {"case_id": "S5-SQL-001", "question": "What allergy is in my confirmed record?", "domain": "nutrition", "journey": base, "jurisdiction": "IN", "workspace_id": WORKSPACE_A, "owner_id": OWNER_A, "expected_public_evidence_ids": [], "expected_personal_fact_ids": ["a1111111-1111-4111-8111-111111111111", "a2222222-2222-4222-8222-222222222222"], "expected_graph_path_ids": [], "forbidden_evidence_ids": forbidden, "expected_behavior": "evidence", "criticality": "high", "sql_sufficient": True},
        {"case_id": "S5-GRAPH-001", "question": "Why is my movement plan stale after the restriction?", "domain": "movement", "journey": base, "jurisdiction": "IN", "workspace_id": WORKSPACE_A, "owner_id": OWNER_A, "expected_public_evidence_ids": [], "expected_personal_fact_ids": ["a1111111-1111-4111-8111-111111111111", "a2222222-2222-4222-8222-222222222222"], "expected_graph_path_ids": ["PATH-DOC-RESTRICTION-STALE-PLAN"], "forbidden_evidence_ids": forbidden, "expected_behavior": "evidence", "criticality": "high", "graph_required": True},
        {"case_id": "S5-ABSTAIN-001", "question": "Give week 42 preparation evidence", "domain": "preparation", "journey": {"stage": "pregnancy", "unit": "week", "exact": 42, "range_start": None, "range_end": None}, "jurisdiction": "IN", "workspace_id": WORKSPACE_B, "owner_id": OWNER_B, "expected_public_evidence_ids": [], "expected_personal_fact_ids": [], "expected_graph_path_ids": [], "forbidden_evidence_ids": forbidden, "expected_behavior": "clarification", "criticality": "high"},
    ]


def main() -> int:
    FIXTURE.write_text(json.dumps(build_fixture(), indent=2) + "\n", encoding="utf-8", newline="\n")
    DEVSET.write_text("".join(json.dumps(row, separators=(",", ":")) + "\n" for row in build_devset()), encoding="utf-8", newline="\n")
    print(json.dumps({"fixture": str(FIXTURE), "development_cases": len(build_devset())}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



