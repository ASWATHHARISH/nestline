"""Build the isolated fictional Stage 5 corpus and frozen rectification truth."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from app.services.embeddings import DeterministicTestEmbeddingProvider

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data/synthetic/stage5_retrieval_fixtures.json"
DEVSET = ROOT / "evals/stage5_retrieval_development.jsonl"

OWNER_A = "11111111-1111-4111-8111-111111111111"
OWNER_B = "22222222-2222-4222-8222-222222222222"
OWNER_C = "33333333-3333-4333-8333-333333333333"
OWNER_D = "44444444-4444-4444-8444-444444444444"
OWNER_E = "55555555-5555-4555-8555-555555555555"
OWNER_F = "66666666-6666-4666-8666-666666666666"
WORKSPACE_A = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
WORKSPACE_B = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
WORKSPACE_C = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
WORKSPACE_D = "dddddddd-dddd-4ddd-8ddd-dddddddddddd"
WORKSPACE_E = "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"
WORKSPACE_F = "ffffffff-ffff-4fff-8fff-ffffffffffff"
RELEASE = "55555555-5555-4555-8555-555555555555"
NOW = "2026-09-11T00:00:00Z"


def digest(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def public_record(candidate_id: str, evidence_id: str, text: str, *,
                  domain: str, stage: str = "pregnancy", unit: str = "week",
                  start: int | None = 24, end: int | None = 24,
                  jurisdiction: list[str] | None = None,
                  conditions_required: list[str] | None = None,
                  conditions_excluded: list[str] | None = None,
                  release_status: str = "published",
                  source_status: str = "published",
                  candidate_status: str = "published",
                  retired: bool = False, authority: float = 0.9,
                  applicability: float = 1.0) -> dict:
    source_id = f"SRC-{candidate_id}"
    span = {
        "source_id": source_id, "evidence_id": evidence_id,
        "source_block_ids": [f"BLOCK-{candidate_id}"], "page": 1,
        "locator": f"fixture/{candidate_id}", "start_char": 0,
        "end_char": len(text), "exact_text": text,
        "text_sha256": digest(text),
    }
    exact = start if start is not None and start == end else None
    candidate = {
        "candidate_id": candidate_id, "evidence_id": evidence_id,
        "source_id": source_id,
        "source_title": f"Synthetic source {candidate_id}", "text": text,
        "evidence_lane": "guideline", "domain": domain,
        "journey": {
            "stage": stage, "unit": unit, "exact": exact,
            "range_start": start if exact is None else None,
            "range_end": end if exact is None else None,
        },
        "jurisdictions": jurisdiction or ["IN"],
        "conditions_required": conditions_required or [],
        "conditions_excluded": conditions_excluded or [],
        "release_status": "published", "source_status": "published",
        "candidate_status": "published",
        "allowed_use": ["store", "embed", "display"], "spans": [span],
        "authority_score": authority, "applicability_score": applicability,
        "provenance": {
            "corpus_version": "stage5-fixture-v2", "release_id": RELEASE,
            "release_fingerprint": "5" * 64,
            "source_version": "fixture-2.0",
            "embedding_provider": "TEST_ONLY",
            "embedding_model": "sha256-test-vector-v1",
            "filter_version": "stage5-filter-v1", "fixture_only": True,
        },
    }
    return {
        "release_status": release_status, "source_status": source_status,
        "candidate_status": candidate_status, "retired": retired,
        "embedding": DeterministicTestEmbeddingProvider().embed([text])[0],
        "candidate": candidate,
    }


def personal_fact(fact_id: str, fact_type: str, value, *, record_only=False) -> dict:
    return {
        "fact_id": fact_id, "fact_type": fact_type, "value": value,
        "source_kind": "human_reviewed", "confirmation_status": "confirmed",
        "record_only": record_only, "source_document_id": None,
        "source_document_fact_id": None, "valid_from": NOW, "valid_to": None,
        "provenance": {"fixture": "Maya fictional"},
    }


def passage(workspace: str, chunk_id: str, document_id: str, text: str,
            *, status="confirmed", confirmation="confirmed") -> dict:
    candidate_id = f"personal-{chunk_id}"
    candidate = {
        "candidate_id": candidate_id, "chunk_id": chunk_id,
        "document_id": document_id, "document_status": "confirmed",
        "text": text,
        "span": {
            "source_id": f"private:{document_id}", "source_block_ids": [],
            "page": 1, "locator": "fictional-document/page/1",
            "start_char": 0, "end_char": len(text), "exact_text": text,
            "text_sha256": digest(text),
        },
        "provenance": {
            "corpus_version": "personal-state-v2", "source_version": "review-2",
            "embedding_provider": "TEST_ONLY",
            "embedding_model": "sha256-test-vector-v1",
            "filter_version": "stage5-filter-v1", "fixture_only": True,
        },
    }
    return {
        "workspace_id": workspace, "care_episode_id": workspace,
        "document_status": status, "confirmation_status": confirmation,
        "embedding": DeterministicTestEmbeddingProvider().embed([text])[0],
        "candidate": candidate,
    }


def node(node_id: str, node_type: str, label: str, entity: str,
         document: str | None = None) -> dict:
    return {"node_id": node_id, "node_type": node_type, "entity_id": entity,
            "label": label, "source_document_id": document}


def edge(edge_id: str, relation: str, source: str, target: str) -> dict:
    return {"edge_id": edge_id, "relation": relation,
            "from_node_id": source, "to_node_id": target}


def journey(state_id: str, stage: str, *, week=None, day=None,
            confirmed=True, conflict=False, version=1) -> dict:
    return {
        "state_id": state_id, "stage": stage,
        "timing_source": "fictional_confirmed_state",
        "gestational_week": week if stage == "pregnancy" else None,
        "gestational_day": 2 if stage == "pregnancy" and week else None,
        "postpartum_week": week if stage == "postpartum" and day is None else None,
        "postpartum_day": day if stage == "postpartum" else None,
        "approximate_month_min": None, "approximate_month_max": None,
        "user_confirmed": confirmed, "has_dating_conflict": conflict,
        "version": version,
    }


def build_fixture() -> dict:
    public = [
        public_record("PUB-JOURNEY-24", "EV-JOURNEY-24", "Week 24 is the confirmed current pregnancy stage in this controlled fixture.", domain="journey"),
        public_record("PUB-NUT-24", "EV-NUT-24", "At week 24, include varied protein foods and account for confirmed dietary restrictions.", domain="nutrition"),
        public_record("PUB-MOVE-24", "EV-MOVE-24", "At week 24, gentle movement depends on confirmed restrictions and individual clinical guidance.", domain="movement"),
        public_record("PUB-WELL-24", "EV-WELL-24", "At week 24, use a repeatable rest and emotional wellbeing routine.", domain="wellbeing"),
        public_record("PUB-SYM-24", "EV-SYM-24", "At week 24, record symptoms and use the reviewed safety route rather than inferring safety.", domain="symptoms"),
        public_record("PUB-PREP-24", "EV-PREP-24", "At week 24, prepare questions and records for the next appointment.", domain="preparation"),
        public_record("PUB-FOLLOW-24", "EV-FOLLOW-24", "At week 24, follow up on saved questions with the care team.", domain="followup"),
        public_record("PUB-PREP-30", "EV-PREP-30", "At week 30, review future appointment preparation topics.", domain="preparation", start=30, end=30),
        public_record("PUB-POSSIBLE", "EV-POSSIBLE", "During possible pregnancy, confirm status before using week-specific guidance.", domain="followup", stage="possible_pregnancy", unit="none", start=None, end=None),
        public_record("PUB-PP-DAY3", "EV-PP-DAY3", "At postpartum day 3, prepare follow-up questions and recovery records.", domain="preparation", stage="postpartum", unit="day", start=3, end=3),
        public_record("PUB-PP-WEEK6", "EV-PP-WEEK6", "At postpartum week 6, review wellbeing support and follow-up needs.", domain="wellbeing", stage="postpartum", unit="week", start=6, end=6),
        public_record("PUB-COND-POS", "EV-COND-POS", "A confirmed movement restriction changes applicable movement guidance.", domain="movement", conditions_required=["movement_restriction"]),
        public_record("DECOY-COND-MISSING", "EV-DECOY-COND-MISSING", "Requires confirmed exercise clearance.", domain="movement", conditions_required=["exercise_clearance"]),
        public_record("DECOY-COND-EXCLUDED", "EV-DECOY-COND-EXCLUDED", "Only applies without a movement restriction.", domain="movement", conditions_excluded=["movement_restriction"]),
        public_record("DECOY-WEEK-12", "EV-DECOY-WEEK-12", "Week 12 protein guidance decoy.", domain="nutrition", start=12, end=12),
        public_record("DECOY-US-24", "EV-DECOY-US-24", "US-only week 24 protein decoy.", domain="nutrition", jurisdiction=["US"]),
        public_record("DECOY-POSTPARTUM", "EV-DECOY-POSTPARTUM", "Postpartum nutrition decoy.", domain="nutrition", stage="postpartum", start=2, end=2),
        public_record("DECOY-DRAFT", "EV-DECOY-DRAFT", "Draft week 24 protein decoy.", domain="nutrition", release_status="draft"),
        public_record("DECOY-REJECTED", "EV-DECOY-REJECTED", "Rejected week 24 protein decoy.", domain="nutrition", source_status="rejected"),
        public_record("DECOY-RETIRED", "EV-DECOY-RETIRED", "Retired week 24 protein decoy.", domain="nutrition", retired=True),
    ]

    fact_allergy = personal_fact(
        "a1111111-1111-4111-8111-111111111111", "allergy",
        {"substance": "peanut", "subject": "Maya (fictional)"})
    fact_restriction = personal_fact(
        "a2222222-2222-4222-8222-222222222222", "dietary_restriction",
        {"restriction": "avoid high-impact movement",
         "condition_key": "movement_restriction",
         "condition_status": "confirmed_present", "subject": "Maya (fictional)"})
    conflict_restriction_fact = personal_fact(
        "f2222222-2222-4222-8222-222222222222", "dietary_restriction",
        {"restriction": "avoid high-impact movement",
         "condition_key": "movement_restriction",
         "condition_status": "confirmed_present",
         "subject": "Riya (fictional)"})
    proposed = personal_fact(
        "a3333333-3333-4333-8333-333333333333", "medical_history",
        {"condition": "unconfirmed fixture proposal"})
    conflict_fact = personal_fact(
        "a4444444-4444-4444-8444-444444444444", "medical_history",
        {"condition": "unresolved fixture conflict"})
    superseded = personal_fact(
        "a5555555-5555-4555-8555-555555555555", "allergy",
        {"substance": "historical fixture value"})

    doc = "d1111111-1111-4111-8111-111111111111"
    plan_item = "d2222222-2222-4222-8222-222222222222"
    plan = "d3333333-3333-4333-8333-333333333333"
    nodes = ["e1111111-1111-4111-8111-111111111111",
             "e2222222-2222-4222-8222-222222222222",
             "e3333333-3333-4333-8333-333333333333",
             "e4444444-4444-4444-8444-444444444444"]
    path = {
        "path_id": "PATH-DOC-RESTRICTION-STALE-PLAN",
        "workspace_id": WORKSPACE_A,
        "nodes": [
            node(nodes[0], "document", "Maya fictional report", doc, doc),
            node(nodes[1], "restriction", "Confirmed movement restriction", fact_restriction["fact_id"], doc),
            node(nodes[2], "plan_item", "Movement plan item", plan_item),
            node(nodes[3], "plan", "Stale weekly plan", plan),
        ],
        "edges": [
            edge("f1111111-1111-4111-8111-111111111111", "EXTRACTED_FROM", nodes[0], nodes[1]),
            edge("f2222222-2222-4222-8222-222222222222", "CONSTRAINS", nodes[1], nodes[2]),
            edge("f3333333-3333-4333-8333-333333333333", "TRIGGERED", nodes[2], nodes[3]),
        ],
        "depth": 3, "provenance": {"fixture_only": True, "document_id": doc},
    }
    empty = {"confirmed_facts": [], "medications": [], "symptoms": [],
             "appointments": [], "plan_states": [], "open_questions": [],
             "unresolved_conflicts": [], "missing_information": []}
    return {
        "schema_version": "stage5-fixture-v2",
        "contains_real_medical_data": False, "production_release": False,
        "active_corpus_version": "stage5-fixture-v2",
        "active_release_id": RELEASE,
        "workspace_owners": {WORKSPACE_A: OWNER_A, WORKSPACE_B: OWNER_B,
                             WORKSPACE_C: OWNER_C, WORKSPACE_D: OWNER_D,
                             WORKSPACE_E: OWNER_E, WORKSPACE_F: OWNER_F},
        "personal_state_versions": {WORKSPACE_A: 3, WORKSPACE_B: 2,
                                    WORKSPACE_C: 1, WORKSPACE_D: 1,
                                    WORKSPACE_E: 1, WORKSPACE_F: 1},
        "public_records": public,
        "personal_fact_records": [
            {"workspace_id": WORKSPACE_A, "confirmation_status": "confirmed", "superseded": False, "valid_to": None, "candidate": fact_allergy},
            {"workspace_id": WORKSPACE_A, "confirmation_status": "confirmed", "superseded": False, "valid_to": None, "candidate": fact_restriction},
            {"workspace_id": WORKSPACE_F, "confirmation_status": "confirmed", "superseded": False, "valid_to": None, "candidate": conflict_restriction_fact},
            {"workspace_id": WORKSPACE_A, "confirmation_status": "proposed", "superseded": False, "valid_to": None, "candidate": proposed},
            {"workspace_id": WORKSPACE_A, "confirmation_status": "conflict", "superseded": False, "valid_to": None, "candidate": conflict_fact},
            {"workspace_id": WORKSPACE_A, "confirmation_status": "confirmed", "superseded": True, "valid_to": NOW, "candidate": superseded},
        ],
        "personal_contexts": {
            WORKSPACE_A: {
                **empty, "journey_state": journey(
                    "c1111111-1111-4111-8111-111111111111", "pregnancy",
                    week=24, version=3),
                "medications": [{"medication_id": "c2222222-2222-4222-8222-222222222222", "name_as_written": "Fictional supplement record", "context_text": "record only", "status": "confirmed", "record_only": True}],
                "symptoms": [{"symptom_id": "c3333333-3333-4333-8333-333333333333", "description": "fictional prior breathing symptom record", "reported_at": NOW, "safety_route": "no_match", "matched_rule_ids": [], "safety_evaluation_only": True}],
                "appointments": [{"appointment_id": "c4444444-4444-4444-8444-444444444444", "scheduled_for": "2026-09-20T09:00:00Z", "appointment_type": "fictional check-up", "status": "confirmed"}],
                "plan_states": [{"plan_id": plan, "version": 2, "status": "stale", "stale_reasons": ["confirmed_restriction_changed"]}],
            },
            WORKSPACE_B: {
                **empty, "journey_state": None,
                "appointments": [{"appointment_id": "b4444444-4444-4444-8444-444444444444", "scheduled_for": "2026-09-21T09:00:00Z", "appointment_type": "unrelated fictional visit", "status": "confirmed"}],
                "missing_information": [{"field": "journey_state", "reason": "No confirmed journey timing", "required_for": ["public_guidance"]}],
            },
            WORKSPACE_C: {**empty, "journey_state": journey("c6666666-6666-4666-8666-666666666666", "possible_pregnancy")},
            WORKSPACE_D: {**empty, "journey_state": journey("d6666666-6666-4666-8666-666666666666", "postpartum", day=3)},
            WORKSPACE_E: {**empty, "journey_state": journey("e6666666-6666-4666-8666-666666666666", "postpartum", week=6)},
            WORKSPACE_F: {
                **empty, "journey_state": journey(
                    "f6666666-6666-4666-8666-666666666666", "pregnancy",
                    week=24),
                "unresolved_conflicts": [{"conflict_id": "c5555555-5555-4555-8555-555555555555", "fact_type": "dietary_restriction", "proposed_values": [{"activity": "prenatal yoga allowed"}, {"activity": "prenatal yoga paused"}], "source_document_ids": [], "clarification_question_ids": [], "state": "requires_clarification"}],
            },
        },
        "personal_passages": [
            passage(WORKSPACE_A, "b1111111-1111-4111-8111-111111111111", doc, "Maya fictional record states a confirmed peanut allergy."),
            passage(WORKSPACE_B, "b2222222-2222-4222-8222-222222222222", "d9999999-9999-4999-8999-999999999999", "Other fictional workspace private passage.", confirmation="proposed"),
            passage(WORKSPACE_A, "b3333333-3333-4333-8333-333333333333", doc, "Unconfirmed private proposal decoy.", confirmation="proposed"),
        ],
        "weekly_profiles": [],
        "graph_paths": [
            {"keywords": ["why", "stale", "plan", "restriction"], "path": path},
            {"keywords": ["cycle"], "path": {**path, "path_id": "DECOY-CYCLE", "nodes": [path["nodes"][0], path["nodes"][1], path["nodes"][0]], "edges": path["edges"][:2], "depth": 2}},
        ],
    }


def position(stage="pregnancy", unit="week", exact=24):
    return {"stage": stage, "unit": unit, "exact": exact,
            "range_start": None, "range_end": None}


def build_devset() -> list[dict]:
    forbidden = ["EV-DECOY-WEEK-12", "EV-DECOY-US-24",
                 "EV-DECOY-POSTPARTUM", "EV-DECOY-DRAFT",
                 "EV-DECOY-REJECTED", "EV-DECOY-RETIRED"]
    cond_forbidden = forbidden + ["EV-DECOY-COND-MISSING",
                                  "EV-DECOY-COND-EXCLUDED"]

    def case(case_id, question, domain, *, purpose="public_guidance",
             journey_value=None, workspace=WORKSPACE_A, owner=OWNER_A,
             public=None, facts=None, paths=None, forbidden_ids=None,
             behavior="evidence", support="fully_supported", reason="none",
             graph=False, relation="current", stale_version=False,
             criticality="high"):
        return {
            "case_id": case_id, "question": question, "domain": domain,
            "purpose": purpose,
            "journey": journey_value or position(), "jurisdiction": "IN",
            "workspace_id": workspace, "owner_id": owner,
            "caller_state_version": 999 if stale_version else (
                2 if workspace == WORKSPACE_B else 1 if workspace != WORKSPACE_A else 3),
            "include_graph": graph,
            "expected_public_evidence_ids": public or [],
            "expected_personal_fact_ids": facts or [],
            "expected_graph_path_ids": paths or [],
            "forbidden_evidence_ids": forbidden_ids or forbidden,
            "expected_behavior": behavior,
            "expected_support_state": support,
            "expected_abstention_reason": reason,
            "expected_journey_relation": relation,
            "criticality": criticality,
        }

    allergy = "a1111111-1111-4111-8111-111111111111"
    restriction = "a2222222-2222-4222-8222-222222222222"
    conflict_restriction = "f2222222-2222-4222-8222-222222222222"
    return [
        case("S5-DEFECT-PUBLIC-001", "What hospital documents and finances should I prepare at week 25?", "preparation", journey_value=position(exact=25), behavior="abstain", support="unsupported", reason="no_approved_public_content", relation="explicit_other"),
        case("S5-IRRELEVANT-VECTOR-001", "What public preparation guidance applies at week 25?", "preparation", journey_value=position(exact=25), behavior="abstain", support="unsupported", reason="no_approved_public_content", relation="explicit_other"),
        case("S5-PERSONAL-ALLERGY-001", "What allergy is in my confirmed record?", "nutrition", purpose="personal_record_lookup", facts=[allergy], behavior="evidence"),
        case("S5-MIXED-PARTIAL-001", "How should my peanut allergy change week 25 nutrition guidance?", "nutrition", purpose="mixed_personalized_guidance", journey_value=position(exact=25), facts=[allergy], behavior="abstain", support="partially_supported", reason="partial_support", relation="explicit_other"),
        case("S5-DEFECT-CONFLICT-001", "How should my conflicting prenatal yoga record affect week 25 movement guidance?", "movement", purpose="mixed_personalized_guidance", journey_value=position(exact=25), workspace=WORKSPACE_F, owner=OWNER_F, facts=[conflict_restriction], behavior="clarification", support="clarification_required", reason="unresolved_conflict", relation="explicit_other"),
        case("S5-CONFLICT-GENERIC-RESTRICTION-001", "What restrictions are in my record?", "movement", purpose="personal_record_lookup", workspace=WORKSPACE_F, owner=OWNER_F, facts=[conflict_restriction], behavior="clarification", support="clarification_required", reason="unresolved_conflict"),
        case("S5-MISSING-GENERIC-JOURNEY-001", "What week am I in?", "journey", purpose="personal_record_lookup", workspace=WORKSPACE_B, owner=OWNER_B, behavior="clarification", support="clarification_required", reason="missing_information", relation="unconfirmed_current"),
        case("S5-MISSING-001", "What should I prepare now?", "preparation", workspace=WORKSPACE_B, owner=OWNER_B, behavior="clarification", support="clarification_required", reason="missing_information", relation="unconfirmed_current"),
        case("S5-CONFLICT-IRRELEVANT-001", "What protein foods matter at week 24?", "nutrition", public=["EV-NUT-24"], facts=[allergy]),
        case("S5-GRAPH-ON-001", "Why is my movement plan stale after the restriction?", "movement", purpose="causal_explanation", graph=True, facts=[restriction], paths=["PATH-DOC-RESTRICTION-STALE-PLAN"]),
        case("S5-GRAPH-OFF-001", "Why is my movement plan stale after the restriction?", "movement", purpose="causal_explanation", graph=False, facts=[restriction], behavior="abstain", support="unsupported", reason="no_eligible_evidence"),
        case("S5-COND-POS-001", "How does my confirmed movement restriction affect movement?", "movement", purpose="mixed_personalized_guidance", public=["EV-MOVE-24", "EV-COND-POS"], facts=[restriction], forbidden_ids=cond_forbidden),
        case("S5-COND-MISSING-001", "What gentle movement guidance applies without confirmed exercise clearance?", "movement", public=["EV-MOVE-24", "EV-COND-POS"], facts=[restriction], forbidden_ids=cond_forbidden),
        case("S5-COND-EXCLUDE-001", "What movement guidance applies with my restriction?", "movement", public=["EV-MOVE-24", "EV-COND-POS"], facts=[restriction], forbidden_ids=cond_forbidden),
        case("S5-CURRENT-MISMATCH-001", "What nutrition guidance applies to me now?", "nutrition", journey_value=position(exact=12), public=["EV-NUT-24"], facts=[allergy], relation="overridden_to_current"),
        case("S5-FUTURE-WEEK-001", "What should I prepare at week 30?", "preparation", journey_value=position(exact=30), public=["EV-PREP-30"], relation="explicit_other"),
        case("S5-STALE-VERSION-001", "What protein foods matter at week 24?", "nutrition", public=["EV-NUT-24"], facts=[allergy], stale_version=True),
        case("S5-POSSIBLE-001", "What follow-up applies during possible pregnancy?", "followup", journey_value=position("possible_pregnancy", "none", None), workspace=WORKSPACE_C, owner=OWNER_C, public=["EV-POSSIBLE"]),
        case("S5-PP-DAY-001", "What should I prepare at postpartum day 3?", "preparation", journey_value=position("postpartum", "day", 3), workspace=WORKSPACE_D, owner=OWNER_D, public=["EV-PP-DAY3"]),
        case("S5-PP-WEEK-001", "What wellbeing support applies at postpartum week 6?", "wellbeing", journey_value=position("postpartum", "week", 6), workspace=WORKSPACE_E, owner=OWNER_E, public=["EV-PP-WEEK6"]),
        case("S5-JOURNEY-001", "What is relevant about week 24 in this journey?", "journey", public=["EV-JOURNEY-24"]),
        case("S5-WELLBEING-001", "What wellbeing routine fits week 24?", "wellbeing", public=["EV-WELL-24"]),
        case("S5-SYMPTOMS-001", "How should symptoms be recorded at week 24?", "symptoms", public=["EV-SYM-24"]),
        case("S5-PREPARATION-001", "How should I prepare questions at week 24?", "preparation", public=["EV-PREP-24"]),
        case("S5-FOLLOWUP-001", "How should I follow up on questions at week 24?", "followup", public=["EV-FOLLOW-24"]),
        case("S5-MEDICATION-001", "What medication is in my confirmed record?", "followup", purpose="personal_record_lookup", behavior="evidence"),
        case("S5-SYMPTOM-RECORD-001", "What symptom is in my record?", "symptoms", purpose="personal_record_lookup", behavior="evidence"),
        case("S5-APPOINTMENT-001", "When is my next appointment?", "preparation", purpose="personal_record_lookup", behavior="evidence"),
    ]


def main() -> int:
    fixture = build_fixture()
    cases = build_devset()
    FIXTURE.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8", newline="\n")
    DEVSET.write_text("".join(json.dumps(row, separators=(",", ":")) + "\n" for row in cases), encoding="utf-8", newline="\n")
    print(json.dumps({"fixture": str(FIXTURE), "development_cases": len(cases)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
