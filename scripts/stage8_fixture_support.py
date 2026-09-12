"""Synthetic Stage 8 fixtures built on the accepted Stage 7 runtime."""

from __future__ import annotations

from hashlib import sha256

from app.schemas.orchestration import AgentName, Weekday
from app.schemas.validation import (
    AnswerDraft,
    Claim,
    ClaimAction,
    ClaimEvidenceLink,
    ClaimKind,
    ClaimOrigin,
    EligibleEvidenceSpan,
    PlanItemValidationLink,
    ProvenanceCategory,
    ValidationEvidencePacket,
    ValidationRequest,
)
from app.services.orchestration import JourneyOrchestrator
from scripts.stage7_fixture_support import make_request as make_stage7_request


def evidence_span(
    evidence_id: str,
    exact_span: str,
    *,
    source_id: str | None = None,
    kinds: list[ClaimKind] | None = None,
    approval: str = "controlled_fixture",
    current: bool = True,
    retired: bool = False,
    workspace_id=None,
    journey=None,
    jurisdictions: list[str] | None = None,
):
    fixture_only = approval == "controlled_fixture"
    resolved_source_id = source_id or f"source-{evidence_id}"
    span_hash = sha256(exact_span.encode("utf-8")).hexdigest()
    span_id = "span-" + sha256(
        f"{evidence_id}|{resolved_source_id}|{span_hash}".encode("utf-8")
    ).hexdigest()[:20]
    return EligibleEvidenceSpan(
        span_id=span_id,
        evidence_id=evidence_id,
        source_id=resolved_source_id,
        exact_span=exact_span,
        span_sha256=span_hash,
        approval_state=approval,
        current=current,
        retired=retired,
        fixture_only=fixture_only,
        workspace_id=workspace_id,
        journey=journey,
        jurisdictions=jurisdictions or ["IN"],
        evidence_version="fixture-v1",
        allowed_claim_kinds=kinds or [ClaimKind.HEALTH_GUIDANCE, ClaimKind.PLAN_ITEM],
    )


def evidence_link(span: EligibleEvidenceSpan) -> ClaimEvidenceLink:
    return ClaimEvidenceLink(
        span_id=span.span_id,
        evidence_id=span.evidence_id,
        source_id=span.source_id,
        exact_span=span.exact_span,
        span_sha256=span.span_sha256,
    )


def base_validation_request(
    *, plan: bool = False, day_plan: bool = False,
    urgent: bool = False, clarification: bool = False,
    raw_text: str | None = None,
) -> ValidationRequest:
    if raw_text is not None:
        stage7_request = make_stage7_request(
            raw_text,
            horizon=("day" if day_plan else "week" if plan else "none"),
            day=(Weekday.SATURDAY if day_plan else None),
        )
    elif urgent:
        stage7_request = make_stage7_request(
            "I have heavy bleeding and also want a nutrition plan",
            horizon="week",
        )
    elif clarification:
        stage7_request = make_stage7_request("I feel dizzy")
    elif plan and day_plan:
        stage7_request = make_stage7_request(
            "Show my nutrition day plan",
            horizon="day", day=Weekday.SATURDAY,
        )
    elif plan:
        stage7_request = make_stage7_request(
            "Show my nutrition weekly plan",
            horizon="week",
        )
    else:
        stage7_request = make_stage7_request("Show nutrition options")
    result = JourneyOrchestrator().run(stage7_request)
    context = stage7_request.context
    food = evidence_span(
        "food-safe", "Peanut-free meal framework",
        journey=context.journey,
    )
    spans = [food]
    claims: list[Claim] = []
    links: list[PlanItemValidationLink] = []
    if plan and result.proposed_schedule is not None:
        reminder = evidence_span(
            "DOC-001", "Recorded reminder: Documented supplement",
            source_id="DOC-001",
            kinds=[ClaimKind.MEDICATION_RECORD],
            approval="confirmed_personal",
            workspace_id=context.workspace_id,
            journey=None,
            jurisdictions=[],
        )
        spans.append(reminder)
        for index, item in enumerate(result.proposed_schedule.items, start=1):
            if item.record_only:
                claim = Claim(
                    claim_id=f"claim-plan-{index}",
                    text=item.item,
                    kind=ClaimKind.MEDICATION_RECORD,
                    origin=ClaimOrigin.UPLOADED_RECORD,
                    provenance_category=ProvenanceCategory.UPLOADED_RECORD,
                    material_health_claim=True,
                    action=ClaimAction.RECORD_ONLY,
                    evidence_links=[evidence_link(reminder)],
                )
            else:
                claim = Claim(
                    claim_id=f"claim-plan-{index}",
                    text=item.item,
                    kind=ClaimKind.PLAN_ITEM,
                    origin=ClaimOrigin.PUBLIC_GUIDANCE,
                    provenance_category=ProvenanceCategory.PUBLIC_GUIDANCE,
                    material_health_claim=True,
                    action=ClaimAction.RECOMMEND,
                    evidence_links=[evidence_link(food)],
                    applied_context_ids=([] if item.record_only else ["allergy-1", "restriction-1"]),
                    schedule_item_id=item.schedule_item_id,
                )
            claims.append(claim)
            links.append(PlanItemValidationLink(
                schedule_item_id=item.schedule_item_id,
                claim_id=claim.claim_id,
                evidence_ids=item.evidence_ids,
                span_ids=[link.span_id for link in claim.evidence_links],
                applied_context_ids=([] if item.record_only else ["allergy-1", "restriction-1"]),
            ))
        agent = AgentName.PLAN_COMPOSER
        schedule = result.proposed_schedule
    else:
        claims = [Claim(
            claim_id="claim-guidance-1",
            text=food.exact_span,
            kind=ClaimKind.HEALTH_GUIDANCE,
            origin=ClaimOrigin.PUBLIC_GUIDANCE,
            provenance_category=ProvenanceCategory.PUBLIC_GUIDANCE,
            material_health_claim=True,
            action=ClaimAction.RECOMMEND,
            evidence_links=[evidence_link(food)],
            applied_context_ids=["allergy-1", "restriction-1"],
        )]
        agent = AgentName.NUTRITION
        schedule = None
    packet = ValidationEvidencePacket(
        request_id=stage7_request.request_id,
        workspace_id=context.workspace_id,
        care_episode_id=context.care_episode_id,
        state_version=context.state_version,
        journey=context.journey,
        jurisdiction="IN",
        retrieval_policy_id="stage8-fixture-policy:nutrition",
        retrieval_policy_version="fixture-v1",
        support_state="fully_supported",
        ordinary_generation_allowed=True,
        allowed_claim_types=["approved_guideline_paraphrase", "record_only_medication"],
        required_citation_ids=[span.evidence_id for span in spans],
        spans=spans,
        corpus_mode="controlled_fixture",
    )
    draft = AnswerDraft(
        request_id=stage7_request.request_id,
        agent=agent,
        journey_state_version=context.state_version,
        summary=("Here is an evidence-linked editable plan proposal."
                 if plan else "Here is an evidence-linked nutrition option."),
        claims=claims,
        applied_context_ids=["allergy-1", "restriction-1"],
        proposed_schedule=schedule,
        plan_item_links=links,
        evaluation_only=True,
        public_eligible=False,
    )
    return ValidationRequest(
        request_id=stage7_request.request_id,
        context=context,
        safety_result=stage7_request.safety_result,
        orchestration_result=result,
        draft=draft,
        evidence_packet=packet,
        execution_mode="evaluation_only",
    )


def replace_claim(request: ValidationRequest, **updates) -> ValidationRequest:
    claims = list(request.draft.claims)
    claims[0] = claims[0].model_copy(update=updates)
    return request.model_copy(update={
        "draft": request.draft.model_copy(update={"claims": claims})
    })


def replace_packet(request: ValidationRequest, **updates) -> ValidationRequest:
    return request.model_copy(update={
        "evidence_packet": request.evidence_packet.model_copy(update=updates)
    })


def with_all_provenance_categories() -> ValidationRequest:
    request = base_validation_request()
    templates = [
        ("confirmed", ClaimOrigin.CONFIRMED_PERSONAL, ProvenanceCategory.CONFIRMED),
        ("uploaded", ClaimOrigin.UPLOADED_RECORD, ProvenanceCategory.UPLOADED_RECORD),
        ("reported", ClaimOrigin.USER_REPORTED, ProvenanceCategory.USER_REPORTED),
        ("public", ClaimOrigin.PUBLIC_GUIDANCE, ProvenanceCategory.PUBLIC_GUIDANCE),
        ("confirmation", ClaimOrigin.NEEDS_CONFIRMATION, ProvenanceCategory.NEEDS_CONFIRMATION),
    ]
    spans = []
    claims = []
    stage7_result = request.orchestration_result
    worker = stage7_result.worker_results[0]
    citations = list(worker.citations)
    for index, (word, origin, category) in enumerate(templates, start=1):
        evidence_id = f"origin-{index}"
        personal = origin != ClaimOrigin.PUBLIC_GUIDANCE
        span = evidence_span(
            evidence_id, f"{word} information",
            source_id=f"source-{evidence_id}",
            kinds=[ClaimKind.PERSONAL_RECORD],
            approval="confirmed_personal" if personal else "controlled_fixture",
            workspace_id=request.context.workspace_id if personal else None,
            journey=request.context.journey if not personal else None,
            jurisdictions=[] if personal else ["IN"],
        )
        spans.append(span)
        claims.append(Claim(
            claim_id=f"origin-claim-{index}",
            text=span.exact_span,
            kind=ClaimKind.PERSONAL_RECORD,
            origin=origin,
            provenance_category=category,
            material_health_claim=True,
            evidence_links=[evidence_link(span)],
        ))
        citations.append(worker.citations[0].model_copy(update={
            "evidence_id": evidence_id,
            "source_id": span.source_id,
            "exact_span": span.exact_span,
            "approval_state": "confirmed_personal" if personal else "controlled_fixture",
            "fixture_only": not personal,
        }))
    worker = worker.model_copy(update={
        "citations": citations,
        "trace": worker.trace.model_copy(update={
            "evidence_ids": sorted({item.evidence_id for item in citations})
        }),
    })
    stage7_result = stage7_result.model_copy(update={
        "worker_results": [worker],
    })
    draft = request.draft.model_copy(update={"claims": claims, "applied_context_ids": []})
    packet = request.evidence_packet.model_copy(update={
        "spans": spans,
        "required_citation_ids": [span.evidence_id for span in spans],
        "allowed_claim_types": [
            "confirmed_personal_record", "approved_guideline_paraphrase",
            "clarification_required", "evaluation_only_symptom_record",
        ],
    })
    return request.model_copy(update={
        "draft": draft, "evidence_packet": packet,
        "orchestration_result": stage7_result,
    })
