"""Canonical Stage 7 worker catalogue and context-minimisation policy."""

from __future__ import annotations

from app.schemas.orchestration import (
    AgentBudget,
    AgentDefinition,
    AgentName,
    ContextKind,
    EvidenceLane,
    RetrievalPurpose,
)


COMMON_PROHIBITIONS = [
    "diagnose or prescribe",
    "change medication or clinician instructions",
    "claim medical clearance or safety",
    "write persistent state",
    "use service-role credentials",
    "call another worker directly",
]


def _definition(
    agent: AgentName,
    trigger: str,
    tools: list[str],
    lanes: list[EvidenceLane],
    purpose: RetrievalPurpose,
    stop: list[str],
    *,
    steps: int = 6,
    timeout_ms: int = 8_000,
) -> AgentDefinition:
    return AgentDefinition(
        agent=agent,
        version="7.0.0",
        trigger=trigger,
        allowed_tools=tools,
        allowed_evidence_lanes=lanes,
        retrieval_purpose=purpose,
        prohibited_actions=COMMON_PROHIBITIONS,
        stop_conditions=stop,
        model_instructions=[
            "Use only supplied typed evidence and authenticated context.",
            "Keep uncertainty and provenance visible.",
            "Use warm, calm, respectful, concise wording without false reassurance.",
        ],
        budget=AgentBudget(
            max_model_calls=1,
            max_steps=steps,
            max_tokens=1200,
            max_retries=1,
            max_repairs=1,
            timeout_ms=timeout_ms,
        ),
    )


AGENT_CATALOGUE: dict[AgentName, AgentDefinition] = {
    AgentName.RECORD: _definition(
        AgentName.RECORD,
        "authenticated record question or extraction review",
        ["retrieval_gateway.personal_sql", "retrieval_gateway.personal_documents"],
        [EvidenceLane.PERSONAL_SQL, EvidenceLane.PERSONAL_DOCUMENT],
        RetrievalPurpose.PERSONAL_RECORD_LOOKUP,
        ["missing record", "poor OCR", "conflicting record"],
    ),
    AgentName.MEDICATION: _definition(
        AgentName.MEDICATION,
        "medication or supplement record question",
        ["retrieval_gateway.personal_sql", "retrieval_gateway.personal_documents"],
        [EvidenceLane.PERSONAL_SQL, EvidenceLane.PERSONAL_DOCUMENT],
        RetrievalPurpose.MEDICATION_RECORD_LOOKUP,
        ["medication-change request", "possible reaction", "conflicting instructions"],
    ),
    AgentName.SYMPTOM: _definition(
        AgentName.SYMPTOM,
        "symptom request after deterministic Safety Gate",
        ["safety_gate", "retrieval_gateway.public"],
        [EvidenceLane.SAFETY_RESULT, EvidenceLane.PUBLIC_GUIDELINE],
        RetrievalPurpose.SYMPTOM_NAVIGATION,
        ["urgent route", "unresolved clarification", "unsupported route"],
        steps=7,
    ),
    AgentName.NUTRITION: _definition(
        AgentName.NUTRITION,
        "nutrition question or requested plan contribution",
        ["retrieval_gateway.public", "catalogue.food"],
        [EvidenceLane.PUBLIC_GUIDELINE, EvidenceLane.WEEKLY_PROFILE, EvidenceLane.STRUCTURED_CATALOGUE],
        RetrievalPurpose.NUTRITION_GUIDANCE,
        ["missing evidence", "allergy/restriction conflict", "clinical diet request"],
    ),
    AgentName.MOVEMENT: _definition(
        AgentName.MOVEMENT,
        "movement question or requested plan contribution",
        ["safety_gate", "retrieval_gateway.public", "catalogue.movement"],
        [EvidenceLane.SAFETY_RESULT, EvidenceLane.PUBLIC_GUIDELINE, EvidenceLane.WEEKLY_PROFILE, EvidenceLane.STRUCTURED_CATALOGUE],
        RetrievalPurpose.MOVEMENT_GUIDANCE,
        ["new symptom", "unknown required clearance", "restriction conflict", "missing evidence"],
    ),
    AgentName.WELLBEING: _definition(
        AgentName.WELLBEING,
        "well-being request or check-in after deterministic Safety Gate",
        ["safety_gate", "retrieval_gateway.public", "catalogue.wellbeing"],
        [EvidenceLane.SAFETY_RESULT, EvidenceLane.PUBLIC_GUIDELINE, EvidenceLane.STRUCTURED_CATALOGUE],
        RetrievalPurpose.WELLBEING_SUPPORT,
        ["acute safety route", "persistent/worsening concern", "missing evidence"],
    ),
    AgentName.FOLLOWUP: _definition(
        AgentName.FOLLOWUP,
        "appointment, question, timeline or brief request",
        ["retrieval_gateway.personal_sql", "retrieval_gateway.personal_documents"],
        [EvidenceLane.PERSONAL_SQL, EvidenceLane.PERSONAL_DOCUMENT],
        RetrievalPurpose.FOLLOWUP_ORGANISATION,
        ["new symptom", "unresolved instruction", "missing provenance"],
    ),
    AgentName.PLAN_COMPOSER: _definition(
        AgentName.PLAN_COMPOSER,
        "one-day or one-week plan after validated contributor outputs",
        ["schedule_builder", "constraint_checker"],
        [EvidenceLane.PERSONAL_SQL, EvidenceLane.PUBLIC_GUIDELINE, EvidenceLane.WEEKLY_PROFILE, EvidenceLane.STRUCTURED_CATALOGUE],
        RetrievalPurpose.PLAN_COMPOSITION,
        ["state-version mismatch", "contradiction", "overlap", "missing availability"],
        steps=8,
        timeout_ms=10_000,
    ),
}


CONTEXT_POLICY: dict[AgentName, tuple[ContextKind, ...]] = {
    AgentName.RECORD: (
        ContextKind.JOURNEY, ContextKind.DOCUMENT_FACT, ContextKind.OPEN_QUESTION,
    ),
    AgentName.MEDICATION: (
        ContextKind.JOURNEY, ContextKind.MEDICATION, ContextKind.SUPPLEMENT,
        ContextKind.ALLERGY, ContextKind.CONDITION, ContextKind.CLINICIAN_INSTRUCTION,
        ContextKind.DOCUMENT_FACT, ContextKind.SYMPTOM,
    ),
    AgentName.SYMPTOM: (
        ContextKind.JOURNEY, ContextKind.SYMPTOM, ContextKind.CONDITION,
        ContextKind.RESTRICTION, ContextKind.CLINICIAN_INSTRUCTION,
        ContextKind.MEDICATION, ContextKind.DOCUMENT_FACT,
    ),
    AgentName.NUTRITION: (
        ContextKind.JOURNEY, ContextKind.ALLERGY, ContextKind.INTOLERANCE,
        ContextKind.CONDITION, ContextKind.RESTRICTION, ContextKind.CLINICIAN_INSTRUCTION,
        ContextKind.MEDICATION, ContextKind.SUPPLEMENT, ContextKind.PREFERENCE,
        ContextKind.ACCESSIBILITY, ContextKind.DOCUMENT_FACT,
    ),
    AgentName.MOVEMENT: (
        ContextKind.JOURNEY, ContextKind.CONDITION, ContextKind.RESTRICTION,
        ContextKind.CLINICIAN_INSTRUCTION, ContextKind.SYMPTOM,
        ContextKind.PREFERENCE, ContextKind.ACCESSIBILITY, ContextKind.DOCUMENT_FACT,
        ContextKind.DELIVERY_RECOVERY,
    ),
    AgentName.WELLBEING: (
        ContextKind.JOURNEY, ContextKind.CHECK_IN, ContextKind.SYMPTOM,
        ContextKind.CONDITION, ContextKind.PREFERENCE, ContextKind.APPOINTMENT,
    ),
    AgentName.FOLLOWUP: (
        ContextKind.JOURNEY, ContextKind.APPOINTMENT, ContextKind.OPEN_QUESTION,
        ContextKind.SYMPTOM, ContextKind.MEDICATION, ContextKind.SUPPLEMENT,
        ContextKind.DOCUMENT_FACT, ContextKind.PLAN_STATE,
        ContextKind.CLINICIAN_INSTRUCTION,
    ),
    AgentName.PLAN_COMPOSER: (
        ContextKind.JOURNEY, ContextKind.ALLERGY, ContextKind.INTOLERANCE,
        ContextKind.CONDITION, ContextKind.RESTRICTION, ContextKind.CLINICIAN_INSTRUCTION,
        ContextKind.MEDICATION, ContextKind.SUPPLEMENT, ContextKind.APPOINTMENT,
        ContextKind.SYMPTOM, ContextKind.PREFERENCE, ContextKind.ACCESSIBILITY,
        ContextKind.DOCUMENT_FACT, ContextKind.PLAN_STATE, ContextKind.DELIVERY_RECOVERY,
    ),
}


def definition_for(agent: AgentName) -> AgentDefinition:
    return AGENT_CATALOGUE[agent]
