"""Stage 9 product-view assembly over accepted Stage 3-8 interfaces.

The service deliberately keeps controlled fictional fixtures separate from an
empty Personal Mode. It never performs a durable write and never treats fixture
evidence as a public health release.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Iterable

from app.schemas.orchestration import (
    AgentName,
    ContextKind,
    EvidenceLane,
    FactState,
    OrchestrationResult,
    Weekday,
)
from app.schemas.product_experience import (
    ChatDisplayResult,
    DocumentView,
    EvaluatorMetric,
    EvidenceDrawerItem,
    HomeSection,
    JourneyHeader,
    PlanDisplayState,
    ProductMode,
    RecordFieldView,
    RuntimeConfig,
    SimulatedReviewView,
    ViewState,
    WeeklyHomeView,
)
from app.schemas.validation import (
    AnswerDraft,
    Claim,
    ClaimAction,
    ClaimEvidenceLink,
    ClaimKind,
    ClaimOrigin,
    EligibleEvidenceSpan,
    FinalDisposition,
    PlanItemValidationLink,
    ProvenanceCategory,
    Stage8Result,
    ValidationEvidencePacket,
    ValidationRequest,
)
from app.services.orchestration import JourneyOrchestrator
from app.services.validation import Stage8ValidationPipeline
from scripts.stage7_fixture_support import make_request as make_stage7_request


ROOT = Path(__file__).resolve().parents[2]
DEMO_WORKSPACE = "72222222-2222-4222-8222-222222222222"
VISIBLE_PROVENANCE = tuple(item.value for item in ProvenanceCategory)


@dataclass(frozen=True)
class ProductExecution:
    display: ChatDisplayResult
    stage7: OrchestrationResult
    stage8: Stage8Result | None


def _configured(value: str) -> bool:
    normalized = value.strip()
    return bool(normalized) and not any(
        marker in normalized.upper()
        for marker in ("YOUR_PROJECT", "YOUR_PUBLISHABLE", "REPLACE_ME")
    )


def load_runtime_config(environ: dict[str, str] | None = None) -> RuntimeConfig:
    values = environ if environ is not None else os.environ
    missing = []
    if not _configured(values.get("NESTLINE_SUPABASE_URL", "")):
        missing.append("NESTLINE_SUPABASE_URL")
    if not _configured(values.get("NESTLINE_SUPABASE_PUBLISHABLE_KEY", "")):
        missing.append("NESTLINE_SUPABASE_PUBLISHABLE_KEY")
    return RuntimeConfig(
        supabase_configured=not missing,
        personal_mode_available=not missing,
        missing_fields=missing,
    )


def personal_empty_home() -> WeeklyHomeView:
    return WeeklyHomeView(
        mode=ProductMode.PERSONAL,
        fictional=False,
        hero_title="Start with your journey",
        hero_body="Confirm your timing and information before Nestline assembles a weekly view.",
        hero_alt="An empty journey card waiting for confirmed information.",
        sections=[
            HomeSection(
                heading="Nothing has been added yet",
                items=["Sign in, choose an empty Personal workspace, and confirm your journey."],
                state=ViewState.EMPTY,
                primary_action="Start onboarding",
            ),
        ],
        plan_state=PlanDisplayState.NONE,
        state=ViewState.EMPTY,
    )


def _demo_context_lines(kind: ContextKind) -> list[str]:
    context = make_stage7_request("Show meal options").context
    lines = []
    for item in context.items:
        if item.kind == kind and item.state == FactState.CONFIRMED and item.current:
            lines.append(str(item.value))
    return lines


def demo_weekly_home(*, approximate: bool = False, plan_state: PlanDisplayState = PlanDisplayState.NONE) -> WeeklyHomeView:
    journey = JourneyHeader(
        stage="pregnancy",
        display_label=("Pregnancy weeks 23–25 · approximate fictional range" if approximate
                       else "Pregnancy week 24 · fictional demo"),
        exact=not approximate,
        position_start=23 if approximate else 24,
        position_end=25 if approximate else 24,
        unit="week",
        state_version=3,
    )
    allergies = _demo_context_lines(ContextKind.ALLERGY)
    restrictions = _demo_context_lines(ContextKind.RESTRICTION)
    conditions = _demo_context_lines(ContextKind.CONDITION)
    confirmed = [f"Allergy: {value}" for value in allergies]
    confirmed += [f"Restriction: {value}" for value in restrictions]
    confirmed += [f"Condition: {value}" for value in conditions]
    return WeeklyHomeView(
        mode=ProductMode.DEMO,
        fictional=True,
        journey=journey,
        hero_title="Your week, gathered in one calm place",
        hero_body=(
            "This original journey illustration marks the controlled week-24 fixture. "
            "No public weekly-development profile has been released, so Nestline does not display an unreviewed size or development claim."
        ),
        hero_asset="assets/stage9/week-24-journey.svg",
        hero_alt="Abstract circular illustration with 24 dots representing fictional pregnancy week 24; it makes no size or clinical claim.",
        confirmed_context=confirmed,
        sections=[
            HomeSection(
                heading="What may be changing now",
                items=["Weekly development guidance is unavailable until reviewed content is released."],
                state=ViewState.UNAVAILABLE,
                primary_action="See why this is unavailable",
            ),
            HomeSection(
                heading="Nutrition focus",
                items=["Ask Compass for a validated fictional meal framework that applies the recorded peanut allergy."],
                primary_action="Draft nutrition options",
            ),
            HomeSection(
                heading="Movement focus",
                items=["Ask Compass for a conservative fictional movement option that preserves the recorded restriction."],
                primary_action="Draft movement options",
            ),
            HomeSection(
                heading="Well-being focus",
                items=["Choose an optional, evidence-linked fictional grounding or reflection activity."],
                primary_action="Open well-being support",
            ),
            HomeSection(
                heading="Preparation and follow-up",
                items=["Fictional appointment: Wednesday, 10:00–11:00.", "Open question: ask about the documented result."],
                primary_action="Prepare appointment questions",
            ),
            HomeSection(
                heading="Consider",
                items=["Peanut-free options that pass the accepted fixture constraints."],
            ),
            HomeSection(
                heading="Avoid",
                items=["Peanut and high-impact movement in this fictional profile."],
            ),
            HomeSection(
                heading="Ask first",
                items=["Clarify any conflicting or missing record instruction with an appropriate professional."],
            ),
            HomeSection(
                heading="Reported symptoms",
                items=["No current symptom is recorded in this fictional home snapshot."],
                primary_action="Open immediate safety help",
            ),
        ],
        plan_state=plan_state,
        unresolved_items=[
            "Public weekly profiles: 0 released",
            "Clinical and India-localisation review: still open",
            "Review surfaces in this build are simulated",
        ],
        state=ViewState.SUCCESS,
    )


def _span_for_reference(reference, *, exact_span: str | None = None, kind: ClaimKind | None = None):
    personal = reference.lane in {EvidenceLane.PERSONAL_DOCUMENT, EvidenceLane.PERSONAL_SQL}
    text = exact_span or reference.exact_span
    digest = sha256(text.encode("utf-8")).hexdigest()
    source_id = reference.source_id
    span_id = "span-" + sha256(
        f"{reference.evidence_id}|{source_id}|{digest}".encode("utf-8")
    ).hexdigest()[:20]
    return EligibleEvidenceSpan(
        span_id=span_id,
        evidence_id=reference.evidence_id,
        source_id=source_id,
        exact_span=text,
        span_sha256=digest,
        approval_state="confirmed_personal" if personal else "controlled_fixture",
        fixture_only=not personal,
        workspace_id=make_stage7_request("Show meal options").context.workspace_id if personal else None,
        journey=None if personal else reference.journey,
        jurisdictions=[] if personal else ["IN"],
        evidence_version="stage9-fixture-v1",
        allowed_claim_kinds=[kind or (
            ClaimKind.PERSONAL_RECORD if personal else ClaimKind.HEALTH_GUIDANCE
        )],
    )


def _link(span: EligibleEvidenceSpan) -> ClaimEvidenceLink:
    return ClaimEvidenceLink(
        span_id=span.span_id,
        evidence_id=span.evidence_id,
        source_id=span.source_id,
        exact_span=span.exact_span,
        span_sha256=span.span_sha256,
    )


def _constraints(context) -> list[str]:
    return [
        item.item_id for item in context.items
        if item.kind in {
            ContextKind.ALLERGY,
            ContextKind.INTOLERANCE,
            ContextKind.CONDITION,
            ContextKind.RESTRICTION,
            ContextKind.CLINICIAN_INSTRUCTION,
        }
        and item.state == FactState.CONFIRMED and item.current
    ]


def _reference_index(result: OrchestrationResult):
    return {
        ref.evidence_id: ref
        for worker in result.worker_results
        for ref in worker.citations
    }


def build_stage8_request(stage7_request, result: OrchestrationResult) -> ValidationRequest:
    """Adapt a completed Stage 7 fixture result into the accepted Stage 8 gate."""

    if not result.worker_results:
        raise ValueError("Stage 8 requires a completed Stage 7 worker result")
    context = stage7_request.context
    constraint_ids = _constraints(context)
    spans: list[EligibleEvidenceSpan] = []
    claims: list[Claim] = []
    plan_links: list[PlanItemValidationLink] = []
    references = _reference_index(result)

    if result.proposed_schedule is not None:
        for index, item in enumerate(result.proposed_schedule.items, start=1):
            item_spans: list[EligibleEvidenceSpan] = []
            for evidence_id in item.evidence_ids:
                reference = references.get(evidence_id)
                if reference is None:
                    # Recorded reminders are trusted personal fixture records emitted by the composer.
                    from scripts.stage7_fixture_support import ref
                    reference = ref(
                        evidence_id,
                        EvidenceLane.PERSONAL_DOCUMENT if item.record_only else EvidenceLane.STRUCTURED_CATALOGUE,
                        label=item.item,
                    )
                kind = ClaimKind.MEDICATION_RECORD if item.record_only else ClaimKind.PLAN_ITEM
                # Repeated weekly items share one evidence ID. The trusted span
                # keeps the displayed item plus its deterministic slot so each
                # citation has a unique stable span identity.
                span = _span_for_reference(
                    reference,
                    exact_span=f"{item.item} Scheduled {item.day.value} at {item.start}.",
                    kind=kind,
                )
                spans.append(span)
                item_spans.append(span)
            claim = Claim(
                claim_id=f"stage9-plan-{index}",
                text=item.item,
                kind=ClaimKind.MEDICATION_RECORD if item.record_only else ClaimKind.PLAN_ITEM,
                origin=ClaimOrigin.UPLOADED_RECORD if item.record_only else ClaimOrigin.PUBLIC_GUIDANCE,
                provenance_category=(ProvenanceCategory.UPLOADED_RECORD if item.record_only
                                     else ProvenanceCategory.PUBLIC_GUIDANCE),
                material_health_claim=True,
                action=ClaimAction.RECORD_ONLY if item.record_only else ClaimAction.RECOMMEND,
                evidence_links=[_link(span) for span in item_spans],
                applied_context_ids=[] if item.record_only else constraint_ids,
                schedule_item_id=None if item.record_only else item.schedule_item_id,
            )
            claims.append(claim)
            plan_links.append(PlanItemValidationLink(
                schedule_item_id=item.schedule_item_id,
                claim_id=claim.claim_id,
                evidence_ids=list(item.evidence_ids),
                span_ids=[span.span_id for span in item_spans],
                applied_context_ids=[] if item.record_only else constraint_ids,
            ))
        draft_agent = AgentName.PLAN_COMPOSER
    else:
        worker = result.worker_results[-1]
        for index, reference in enumerate(worker.citations, start=1):
            if worker.agent == AgentName.MEDICATION:
                kind, origin, category, action = (
                    ClaimKind.MEDICATION_RECORD, ClaimOrigin.UPLOADED_RECORD,
                    ProvenanceCategory.UPLOADED_RECORD, ClaimAction.RECORD_ONLY,
                )
            elif reference.lane in {EvidenceLane.PERSONAL_DOCUMENT, EvidenceLane.PERSONAL_SQL}:
                kind, origin, category, action = (
                    ClaimKind.PERSONAL_RECORD, ClaimOrigin.UPLOADED_RECORD,
                    ProvenanceCategory.UPLOADED_RECORD, ClaimAction.DESCRIBE,
                )
            else:
                kind, origin, category, action = (
                    ClaimKind.HEALTH_GUIDANCE, ClaimOrigin.PUBLIC_GUIDANCE,
                    ProvenanceCategory.PUBLIC_GUIDANCE, ClaimAction.RECOMMEND,
                )
            span = _span_for_reference(reference, kind=kind)
            spans.append(span)
            claims.append(Claim(
                claim_id=f"stage9-claim-{index}",
                text=span.exact_span,
                kind=kind,
                origin=origin,
                provenance_category=category,
                material_health_claim=True,
                action=action,
                evidence_links=[_link(span)],
                applied_context_ids=constraint_ids if action == ClaimAction.RECOMMEND else [],
            ))
        draft_agent = worker.agent

    allowed_types = []
    if any(claim.origin == ClaimOrigin.PUBLIC_GUIDANCE for claim in claims):
        allowed_types.append("approved_guideline_paraphrase")
    if any(claim.kind == ClaimKind.MEDICATION_RECORD for claim in claims):
        allowed_types.append("record_only_medication")
    if any(claim.origin == ClaimOrigin.UPLOADED_RECORD and claim.kind != ClaimKind.MEDICATION_RECORD for claim in claims):
        allowed_types.append("confirmed_personal_record")
    packet = ValidationEvidencePacket(
        request_id=stage7_request.request_id,
        workspace_id=context.workspace_id,
        care_episode_id=context.care_episode_id,
        state_version=context.state_version,
        journey=context.journey,
        jurisdiction="IN",
        retrieval_policy_id=f"stage9-ui:{result.route_plan.intent.value}",
        retrieval_policy_version="stage9-controlled-fixture-v1",
        support_state="fully_supported",
        ordinary_generation_allowed=True,
        allowed_claim_types=allowed_types,
        required_citation_ids=sorted({span.evidence_id for span in spans}),
        spans=spans,
        corpus_mode="controlled_fixture",
    )
    draft = AnswerDraft(
        request_id=stage7_request.request_id,
        agent=draft_agent,
        journey_state_version=context.state_version,
        summary=result.worker_results[-1].summary,
        claims=claims,
        applied_context_ids=constraint_ids,
        proposed_actions=[
            action for worker in result.worker_results for action in worker.proposed_actions
        ],
        proposed_schedule=result.proposed_schedule,
        plan_item_links=plan_links,
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


def _drawer(span, claim_id: str) -> EvidenceDrawerItem:
    personal = span.workspace_id is not None
    return EvidenceDrawerItem(
        evidence_id=span.evidence_id,
        source_id=span.source_id,
        source_title=("Fictional uploaded record" if personal else "Controlled development evidence"),
        publisher=("Fictional demo workspace" if personal else "Nestline synthetic development set"),
        source_type="personal_document_fixture" if personal else "public_fixture",
        review_status=("confirmed fictional record" if personal else "controlled fixture; not publicly released"),
        current_status="current fixture",
        journey_applicability=(None if span.journey is None else
                               f"{span.journey.stage} {span.journey.unit} {span.journey.start}–{span.journey.end}"),
        locator=f"{span.source_id} · exact span {span.span_id} · claim {claim_id}",
        supporting_passage=span.exact_span,
        supports_claim=True,
        workspace_id=str(span.workspace_id) if personal else None,
    )


def run_compass(
    text: str,
    *,
    horizon: str = "none",
    day: Weekday | None = None,
) -> ProductExecution:
    request = make_stage7_request(text, horizon=horizon, day=day)
    result = JourneyOrchestrator().run(request)
    safety = result.safety_result
    if safety.route == "urgent":
        display = ChatDisplayResult(
            request_id=str(request.request_id), route="urgent",
            title="Get urgent help now", summary=safety.fixed_message.text,
            uncertainties=[], ordinary_generation_calls=0,
            validation_display_allowed=False, trace_id=str(safety.trace.trace_id),
            state=ViewState.BLOCKED,
        )
        return ProductExecution(display, result, None)
    if safety.route == "needs_clarification":
        display = ChatDisplayResult(
            request_id=str(request.request_id), route="clarification",
            title="One detail is needed first", summary=safety.clarification.question,
            uncertainties=[safety.clarification.reason], ordinary_generation_calls=0,
            validation_display_allowed=False, trace_id=str(safety.trace.trace_id),
            state=ViewState.VALIDATION_ERROR,
        )
        return ProductExecution(display, result, None)
    if not result.worker_results:
        display = ChatDisplayResult(
            request_id=str(request.request_id), route="unsupported",
            title="I cannot complete that request", summary=result.route_plan.reason,
            uncertainties=["No accepted specialist route was available."],
            ordinary_generation_calls=result.trace.total_model_calls,
            validation_display_allowed=False, trace_id=str(result.trace.trace_id),
            state=ViewState.UNAVAILABLE,
        )
        return ProductExecution(display, result, None)
    if any(worker.status.value != "completed" for worker in result.worker_results):
        stopped = next(worker for worker in result.worker_results if worker.status.value != "completed")
        display = ChatDisplayResult(
            request_id=str(request.request_id), route="abstained",
            title="More information is needed", summary=stopped.summary,
            uncertainties=stopped.uncertainties or [stopped.stop_reason or "The worker stopped safely."],
            ordinary_generation_calls=result.trace.total_model_calls,
            validation_display_allowed=False, trace_id=str(result.trace.trace_id),
            state=ViewState.RECOVERABLE_ERROR,
        )
        return ProductExecution(display, result, None)

    validation_request = build_stage8_request(request, result)
    stage8 = Stage8ValidationPipeline().run(validation_request)
    if not stage8.composed_answer:
        display = ChatDisplayResult(
            request_id=str(request.request_id), route="abstained",
            title="This draft was not shown", summary="The validation gate did not permit display.",
            uncertainties=[finding.detail for finding in stage8.validation_report.findings],
            ordinary_generation_calls=result.trace.total_model_calls,
            validation_display_allowed=False,
            trace_id=str(stage8.validation_report.trace.trace_id),
            state=ViewState.VALIDATION_ERROR,
        )
        return ProductExecution(display, result, stage8)

    packet_spans = {span.span_id: span for span in validation_request.evidence_packet.spans}
    citations = []
    sections: dict[str, list[str]] = {}
    for section in stage8.composed_answer.sections:
        sections[section.provenance.value] = list(section.statements)
        for citation in section.citations:
            citations.append(_drawer(packet_spans[citation.span_id], citation.claim_id))
    workers = result.worker_results
    display = ChatDisplayResult(
        request_id=str(request.request_id), route="validated",
        title="Validated controlled-fixture result",
        summary=stage8.composed_answer.summary,
        provenance_sections=sections,
        citations=citations,
        uncertainties=[item for worker in workers for item in worker.uncertainties],
        applied_constraints=sorted({item for worker in workers for item in worker.applied_constraints}),
        proposed_actions=[action.description for worker in workers for action in worker.proposed_actions],
        ordinary_generation_calls=result.trace.total_model_calls,
        validation_display_allowed=True,
        trace_id=str(stage8.validation_report.trace.trace_id),
        state=ViewState.SUCCESS,
    )
    return ProductExecution(display, result, stage8)


def demo_documents() -> list[DocumentView]:
    return [
        DocumentView(
            document_id="DOC-001", label="Pregnancy intake summary", status="ready",
            subject="Maya · fictional demo persona",
            fields=[
                RecordFieldView(
                    label="Recorded result", value="haemoglobin recorded as 11.2",
                    status="confirmed", source_id="DOC-001", locator="page 1 · exact span",
                    exact_span="Hb 11.2", confidence=0.98,
                ),
                RecordFieldView(
                    label="Supplement instruction", value="Documented supplement · one tablet daily",
                    status="confirmed", source_id="DOC-001", locator="page 1 · exact span",
                    exact_span="Take one tablet daily", confidence=1.0, record_only=True,
                ),
            ],
            recovery="Review the exact span before proposing a correction. No durable fact write is available in Stage 9.",
        ),
        DocumentView(
            document_id="DOC-003-NOISY", label="Controlled OCR image", status="low_confidence",
            subject="Maya · fictional demo persona", fields=[
                RecordFieldView(
                    label="OCR candidate", value="unclear medication line", status="unconfirmed",
                    source_id="DOC-003-NOISY", locator="image · candidate span",
                    exact_span="unclear", confidence=0.2, record_only=True,
                )
            ],
            recovery="Open the source image and correct or decline the proposed field; do not infer the missing instruction.",
        ),
        DocumentView(
            document_id="DOC-005+006", label="Conflicting movement instructions", status="conflict",
            subject="Maya · fictional demo persona", fields=[
                RecordFieldView(
                    label="Movement instruction", value="two fictional records disagree",
                    status="conflicting", source_id="DOC-005 / DOC-006",
                    locator="page 1 in both sources", exact_span="movement instruction differs",
                    confidence=1.0,
                )
            ],
            recovery="Keep both records visible and ask for professional clarification; neither value becomes active automatically.",
        ),
        DocumentView(
            document_id="EDGE-LOCKED", label="Locked fictional PDF", status="locked",
            subject="Fictional edge case", recovery="Unlock the file locally, then retry with a registered fictional fixture.",
        ),
        DocumentView(
            document_id="EDGE-CORRUPT", label="Corrupt fictional PDF", status="corrupt",
            subject="Fictional edge case", recovery="Replace the damaged file with a readable source and retry.",
        ),
        DocumentView(
            document_id="EDGE-UNSUPPORTED", label="Unsupported fictional RTF", status="unsupported",
            subject="Fictional edge case", recovery="Use a currently supported PDF or image fixture.",
        ),
        DocumentView(
            document_id="EDGE-WRONG-PERSON", label="Wrong-person fictional report", status="wrong_person",
            subject="Other Fictional Person", recovery="Do not extract or confirm facts; choose a record bound to the fictional demo persona.",
        ),
    ]


def simulated_review(status: str = "offered") -> SimulatedReviewView:
    return SimulatedReviewView(
        status=status,
        context_proposed=[
            "Fictional journey position",
            "Selected validated answer and evidence IDs",
            "Explicit uncertainties and questions",
        ],
    )


def load_evaluator_metrics() -> list[EvaluatorMetric]:
    rows = []
    specs = [
        (5, "docs/STAGE-5-CHECK-RESULTS.json", lambda d: (d["verified"]["development_cases"], d["verified"]["development_cases"]), "stage5-development-v1"),
        (6, "docs/STAGE-6-SAFETY-EVAL-RESULTS.json", lambda d: (d["cases"]["passed"], d["cases"]["total"]), "stage6-visible-development-set"),
        (7, "docs/STAGE-7-EVAL-RESULTS.json", lambda d: (d["cases"]["passed"], d["cases"]["total"]), "stage7-visible-synthetic-set"),
        (8, "docs/STAGE-8-EVAL-RESULTS.json", lambda d: (d["cases"]["passed"], d["cases"]["total"]), "stage8-visible-development-set"),
    ]
    for stage, artifact, counter, version in specs:
        data = json.loads((ROOT / artifact).read_text(encoding="utf-8"))
        passed, total = counter(data)
        rows.append(EvaluatorMetric(
            stage=f"Stage {stage}", artifact=artifact, passed=passed, total=total,
            failed=total - passed, skipped=0, dataset_version=version,
            live_provider_run=False,
        ))
    return rows


def authentic_failed_trace() -> dict:
    data = json.loads((ROOT / "docs/STAGE-8-SELF-REVIEW-FINDINGS.json").read_text(encoding="utf-8"))
    return {
        "artifact": "docs/STAGE-8-SELF-REVIEW-FINDINGS.json",
        "first_pass": data["first_generated_evaluation"],
        "finding": data["validator_matrix"][1],
        "post_rectification": data["post_rectification"],
    }


def reset_demo_state_keys(state) -> None:
    """Deterministically clear Stage 9 UI state without touching Personal Mode."""

    for key in list(state.keys()):
        if str(key).startswith("stage9_demo_"):
            del state[key]


def demo_story_results() -> list[dict]:
    stories = [
        ("week-aware-plan", "Show my weekly plan", "week"),
        ("record-to-action", "Show what my document says", "none"),
        ("urgent-bypass", "I cannot breathe. Show my weekly plan.", "week"),
    ]
    outcomes = []
    for run_number in range(1, 4):
        for story, query, horizon in stories:
            execution = run_compass(query, horizon=horizon)
            outcomes.append({
                "run": run_number,
                "story": story,
                "route": execution.display.route,
                "passed": (
                    execution.display.route == "urgent" if story == "urgent-bypass"
                    else execution.display.route == "validated"
                ),
                "ordinary_generation_calls": execution.display.ordinary_generation_calls,
                "stage10_persistence": "unavailable",
            })
    return outcomes
