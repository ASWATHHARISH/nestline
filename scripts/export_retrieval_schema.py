"""Export the versioned Stage 5 retrieval contracts as JSON Schema."""

from __future__ import annotations

import json
from pathlib import Path

from app.schemas.retrieval import (
    AbstentionState,
    AnswerabilityAssessment,
    AuthenticatedRetrievalScope,
    EvidencePacket,
    EvidenceRequirementPolicy,
    GraphPath,
    MissingInformation,
    PersonalFactCandidate,
    PersonalPassageCandidate,
    PublicEvidenceCandidate,
    RankedRetrievalCandidate,
    RerankerInput,
    RetrievalFailure,
    RetrievalRequest,
    RetrievalResult,
    RetrievalTrace,
    SafetyContextSnapshot,
    TrustedRetrievalQuery,
    TrustedRetrievalState,
    UnresolvedConflict,
)


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "data/schemas/retrieval.schema.json"


def build_payload() -> dict:
    models = {
        "retrieval_request": RetrievalRequest,
        "authenticated_scope": AuthenticatedRetrievalScope,
        "evidence_requirement_policy": EvidenceRequirementPolicy,
        "trusted_retrieval_state": TrustedRetrievalState,
        "trusted_retrieval_query": TrustedRetrievalQuery,
        "answerability_assessment": AnswerabilityAssessment,
        "safety_context_snapshot": SafetyContextSnapshot,
        "public_evidence_candidate": PublicEvidenceCandidate,
        "personal_fact_candidate": PersonalFactCandidate,
        "personal_passage_candidate": PersonalPassageCandidate,
        "graph_path": GraphPath,
        "ranked_candidate": RankedRetrievalCandidate,
        "reranker_input": RerankerInput,
        "missing_information": MissingInformation,
        "unresolved_conflict": UnresolvedConflict,
        "abstention": AbstentionState,
        "retrieval_failure": RetrievalFailure,
        "evidence_packet": EvidencePacket,
        "retrieval_trace": RetrievalTrace,
        "retrieval_result": RetrievalResult,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "schema_version": "5.0.0",
        "schemas": {name: model.model_json_schema() for name, model in models.items()},
    }


def main() -> int:
    TARGET.write_text(
        json.dumps(build_payload(), indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(TARGET)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
