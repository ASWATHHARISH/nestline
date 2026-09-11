"""Export Stage 2 application/storage contracts for editor and API integration."""

import json
from pathlib import Path

from app.schemas.storage import (Appointment, AppointmentQuestion, DocumentChunk,
                                 DocumentFact, Feedback, GraphEdge, GraphNode,
                                 HealthFact, HumanReviewCase, JourneyState,
                                 MedicationMention, Notification, PlanItem,
                                 PrivateDocument, SavedPlan, STAGE2_TABLES,
                                 SymptomEvent, USER_OWNED_TABLES, Workspace,
                                 WorkspaceMember)

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    target = ROOT / "data/schemas/storage.schema.json"
    records = {
        "workspace": Workspace.model_json_schema(),
        "workspace_member": WorkspaceMember.model_json_schema(),
        "journey_state": JourneyState.model_json_schema(),
        "private_document": PrivateDocument.model_json_schema(),
        "document_chunk": DocumentChunk.model_json_schema(),
        "document_fact": DocumentFact.model_json_schema(),
        "health_fact": HealthFact.model_json_schema(),
        "medication_mention": MedicationMention.model_json_schema(),
        "symptom_event": SymptomEvent.model_json_schema(),
        "appointment": Appointment.model_json_schema(),
        "appointment_question": AppointmentQuestion.model_json_schema(),
        "saved_plan": SavedPlan.model_json_schema(),
        "plan_item": PlanItem.model_json_schema(),
        "graph_node": GraphNode.model_json_schema(),
        "graph_edge": GraphEdge.model_json_schema(),
        "human_review_case": HumanReviewCase.model_json_schema(),
        "notification": Notification.model_json_schema(),
        "feedback": Feedback.model_json_schema(),
    }
    payload = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "database_tables": sorted(STAGE2_TABLES),
        "workspace_owned_tables": sorted(USER_OWNED_TABLES),
        "records": records,
    }
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
