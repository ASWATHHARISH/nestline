"""Synthetic-only builders for visible Stage 7 development evaluations."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from app.schemas.foundation import SafetySpec
from app.schemas.orchestration import (
    AgentName, AuthenticatedContextSnapshot, ContextItem, ContextKind,
    EvidenceLane, EvidenceReference, FactState, OrchestrationRequest,
    RetrievalPurpose,
    WorkerEvidence,
)
from app.schemas.retrieval import JourneyPosition
from app.services.orchestration_catalogue import definition_for
from app.services.safety_gate import SafetyGate, build_safety_input


ROOT = Path(__file__).resolve().parents[1]
OWNER = UUID("71111111-1111-4111-8111-111111111111")
WORKSPACE = UUID("72222222-2222-4222-8222-222222222222")
NOW = datetime(2026, 9, 12, 8, 0, tzinfo=timezone.utc)


def context_item(
    item_id: str, kind: ContextKind, value,
    *, state: FactState = FactState.CONFIRMED,
    source_id: str | None = None, span: str | None = None,
    confidence: float | None = None, record_only: bool = False,
    current: bool = True,
) -> ContextItem:
    return ContextItem(
        item_id=item_id, kind=kind, state=state, value=value,
        source_id=source_id, source_page=1 if source_id else None,
        exact_span=span, confidence=confidence, recorded_at=NOW,
        record_only=record_only, current=current,
    )


def make_context(modifier: str = "base", *, state_version: int = 3):
    rows = [
        context_item("doc-1", ContextKind.DOCUMENT_FACT, "haemoglobin recorded as 11.2",
                     source_id="DOC-001", span="Hb 11.2", confidence=0.98),
        context_item("med-1", ContextKind.SUPPLEMENT, {
            "name": "Documented supplement", "dose": "1", "unit": "tablet",
            "frequency": "daily", "timing": "08:00", "day": "monday", "time": "08:00",
            "exact_instruction": "Take one tablet at 08:00", "prescriber": "DOC-001",
        }, source_id="DOC-001", span="Take one tablet daily", record_only=True),
        context_item("allergy-1", ContextKind.ALLERGY, "peanut"),
        context_item("restriction-1", ContextKind.RESTRICTION, "avoid high impact movement"),
        context_item("appointment-1", ContextKind.APPOINTMENT, {
            "day": "wednesday", "start": "10:00", "end": "11:00", "label": "Appointment",
        }),
        context_item("question-1", ContextKind.OPEN_QUESTION, "Ask about the documented result"),
    ]
    for day in ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"):
        rows.append(context_item(
            f"availability-{day}", ContextKind.PREFERENCE,
            {"day": day, "start": "08:00", "end": "12:00"},
        ))
    if modifier == "allergy_conflict":
        rows.append(context_item(
            "allergy-conflict", ContextKind.ALLERGY, "tree nut",
            state=FactState.CONFLICTING, source_id="DOC-002", span="tree nut?",
        ))
    elif modifier == "poor_ocr":
        rows.append(context_item(
            "doc-poor", ContextKind.DOCUMENT_FACT, "unclear",
            source_id="DOC-003", span="unclear", confidence=0.2,
        ))
    elif modifier == "record_conflict":
        rows.append(context_item(
            "doc-conflict", ContextKind.DOCUMENT_FACT, "different value",
            state=FactState.CONFLICTING, source_id="DOC-004", span="different value",
        ))
    elif modifier == "medication_conflict":
        rows.append(context_item(
            "med-conflict", ContextKind.MEDICATION, {"name": "Recorded medicine", "dose": "2"},
            state=FactState.CONFLICTING, source_id="DOC-002", span="different dose",
            record_only=True,
        ))
    elif modifier == "current_symptom":
        rows.append(context_item("symptom-1", ContextKind.SYMPTOM, "new worsening pain"))
    elif modifier == "movement_conflict":
        rows.append(context_item(
            "restriction-conflict", ContextKind.RESTRICTION, "movement unclear",
            state=FactState.CONFLICTING, source_id="DOC-005", span="movement unclear",
        ))
    elif modifier == "report_conflict":
        rows.append(context_item(
            "report-conflict", ContextKind.DOCUMENT_FACT, "report instruction conflicts",
            state=FactState.CONFLICTING, source_id="DOC-006", span="conflicting report",
        ))
    elif modifier == "instruction_conflict":
        rows.append(context_item(
            "instruction-conflict", ContextKind.CLINICIAN_INSTRUCTION,
            "instruction differs between records", state=FactState.CONFLICTING,
            source_id="DOC-007", span="different instruction",
        ))
    elif modifier == "desired_movement_cadence":
        rows.append(context_item(
            "movement-cadence", ContextKind.PREFERENCE,
            {"domain": "movement", "cadence_per_week": 1},
        ))
    elif modifier == "condition_instruction":
        rows.extend([
            context_item("condition-1", ContextKind.CONDITION, "documented condition"),
            context_item(
                "instruction-1", ContextKind.CLINICIAN_INSTRUCTION,
                "avoid the documented restricted activity",
            ),
        ])
    elif modifier == "no_availability":
        rows = [row for row in rows if row.kind != ContextKind.PREFERENCE]
    elif modifier == "postpartum":
        journey = JourneyPosition(stage="postpartum", unit="day", exact=3)
    else:
        journey = JourneyPosition(stage="pregnancy", unit="week", exact=24)
    if modifier != "postpartum":
        journey = JourneyPosition(stage="pregnancy", unit="week", exact=24)
    return AuthenticatedContextSnapshot(
        workspace_id=WORKSPACE, care_episode_id=WORKSPACE,
        owner_user_id=OWNER, session_subject=OWNER,
        state_version=state_version, captured_at=NOW, journey=journey, items=rows,
    )


def ref(
    evidence_id: str,
    lane: EvidenceLane,
    *,
    label: str,
    tags: list[str] | None = None,
    duration: int | None = None,
    cadence: int | None = None,
    intensity: str | None = None,
    alternatives: list[str] | None = None,
    recovery: list[str] | None = None,
):
    public = lane in {EvidenceLane.PUBLIC_GUIDELINE, EvidenceLane.WEEKLY_PROFILE,
                      EvidenceLane.STRUCTURED_CATALOGUE}
    return EvidenceReference(
        evidence_id=evidence_id, source_id=f"source-{evidence_id}", lane=lane,
        exact_span=f"Synthetic exact span for {evidence_id}", candidate_label=label,
        constraint_tags=tags or [], duration_minutes=duration,
        cadence_per_week=cadence, intensity_wording=intensity,
        flexible_alternatives=alternatives or [], rest_recovery_notes=recovery or [],
        approval_state="controlled_fixture" if public else "confirmed_personal",
        journey=JourneyPosition(stage="pregnancy", unit="week", exact=24) if public else None,
        fixture_only=public,
    )


def make_evidence(agent: AgentName, modifier: str = "base") -> WorkerEvidence:
    refs: dict[AgentName, list[EvidenceReference]] = {
        AgentName.RECORD: [ref("personal-record", EvidenceLane.PERSONAL_DOCUMENT, label="Record")],
        AgentName.MEDICATION: [ref("personal-med", EvidenceLane.PERSONAL_SQL, label="Medication")],
        AgentName.SYMPTOM: [ref("symptom-policy", EvidenceLane.PUBLIC_GUIDELINE, label="Symptom policy")],
        AgentName.NUTRITION: [
            ref("food-peanut", EvidenceLane.STRUCTURED_CATALOGUE, label="Peanut snack", tags=["peanut"]),
            ref("food-safe", EvidenceLane.STRUCTURED_CATALOGUE, label="Peanut-free meal framework", duration=30, cadence=3, alternatives=["Use another verified allergen-free component"]),
        ],
        AgentName.MOVEMENT: [ref("movement-24", EvidenceLane.PUBLIC_GUIDELINE, label="Gentle walking option", duration=20, cadence=3, intensity="comfortable cited intensity", alternatives=["Use the cited shorter-duration option"], recovery=["Include rest between sessions as needed"])],
        AgentName.WELLBEING: [ref("wellbeing-24", EvidenceLane.PUBLIC_GUIDELINE, label="Optional grounding", duration=10, cadence=3, alternatives=["Choose the cited brief reflection option"], recovery=["Pause or decline the exercise at any time"])],
        AgentName.FOLLOWUP: [ref("personal-followup", EvidenceLane.PERSONAL_SQL, label="Follow-up")],
        AgentName.PLAN_COMPOSER: [],
    }
    if modifier == "wrong_lane":
        refs[agent] = [ref("wrong-public", EvidenceLane.PUBLIC_GUIDELINE, label="Wrong lane")]
    elif modifier == "postpartum_evidence" and agent == AgentName.MOVEMENT:
        refs[agent] = [refs[agent][0].model_copy(update={"journey": JourneyPosition(stage="postpartum", unit="day", exact=3)})]
    elif modifier == "missing_evidence":
        refs[agent] = []
    elif modifier == "only_allergen" and agent == AgentName.NUTRITION:
        refs[agent] = [ref("food-peanut", EvidenceLane.STRUCTURED_CATALOGUE,
                           label="Peanut snack", tags=["peanut"])]
    return WorkerEvidence(
        retrieval_purpose=(RetrievalPurpose.NUTRITION_GUIDANCE if modifier == "wrong_policy" else definition_for(agent).retrieval_purpose),
        references=refs[agent], corpus_mode="controlled_fixture",
        public_routing_eligible=False,
    )


def make_request(
    text: str,
    *,
    context_modifier: str = "base",
    horizon: str = "none",
    day=None,
    evidence_modifier: str = "base",
    max_calls: int = 5,
) -> OrchestrationRequest:
    spec = SafetySpec.model_validate_json((ROOT / "data/safety/rule_spec.yaml").read_text(encoding="utf-8"))
    safety_input = build_safety_input(channel="chat_message", text=text)
    safety = SafetyGate(spec, mode="evaluation_only").evaluate(safety_input)
    evidence = {agent: make_evidence(agent, evidence_modifier) for agent in AgentName}
    return OrchestrationRequest(
        request_id=safety_input.request_id, text=text,
        context=make_context(context_modifier), safety_result=safety,
        execution_mode="evaluation_only", requested_horizon=horizon,
        selected_day=day, evidence_by_agent=evidence,
        max_total_model_calls=max_calls,
    )
