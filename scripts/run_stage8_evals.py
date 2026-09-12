"""Run the visible deterministic Stage 8 development evaluation set."""

from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
from statistics import median
from time import perf_counter
from uuid import UUID

from pydantic import ValidationError

from app.schemas.orchestration import ContextItem, ContextKind, FactState
from app.schemas.retrieval import JourneyPosition
from app.schemas.validation import (
    AnswerDraft,
    ClaimAction,
    ClaimKind,
    ClaimOrigin,
    FindingCode,
    ProvenanceCategory,
    SemanticSupport,
)
from app.services.semantic_support import (
    ScriptedSemanticSupportEvaluator,
    SemanticEvaluatorUnavailable,
)
from app.services.validation import Stage8ValidationPipeline
from scripts.build_stage8_evals import build_devset
from scripts.stage8_fixture_support import (
    base_validation_request,
    evidence_link,
    evidence_span,
    replace_claim,
    replace_packet,
    with_all_provenance_categories,
)


ROOT = Path(__file__).resolve().parents[1]
DEVSET = ROOT / "evals/stage8_validation_development.jsonl"
REPORT = ROOT / "docs/STAGE-8-EVAL-RESULTS.json"
OTHER_WORKSPACE = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")


def _with_span(request, **updates):
    spans = list(request.evidence_packet.spans)
    spans[0] = spans[0].model_copy(update=updates)
    return replace_packet(request, spans=spans)


def _replace_span_and_claim(request, *, claim_text: str, span_text: str):
    span = request.evidence_packet.spans[0]
    digest = sha256(span_text.encode("utf-8")).hexdigest()
    changed_span = span.model_copy(update={"exact_span": span_text, "span_sha256": digest})
    link = request.draft.claims[0].evidence_links[0].model_copy(update={
        "exact_span": span_text, "span_sha256": digest,
    })
    request = replace_packet(request, spans=[changed_span])
    return replace_claim(request, text=claim_text, evidence_links=[link])

def _with_context_item(request, item, *, apply=False):
    context = request.context.model_copy(update={
        "items": [*request.context.items, item]
    })
    draft = request.draft
    if apply:
        ids = [*draft.applied_context_ids, item.item_id]
        claims = [claim.model_copy(update={
            "applied_context_ids": [*claim.applied_context_ids, item.item_id]
        }) for claim in draft.claims]
        draft = draft.model_copy(update={"applied_context_ids": ids, "claims": claims})
    return request.model_copy(update={"context": context, "draft": draft})


def _scripted(support, count=1):
    return ScriptedSemanticSupportEvaluator([support] * count)


def _prepare(case_id):
    request = base_validation_request()
    evaluator = None
    kwargs = {}
    schema_payload = None
    if case_id == "valid_week_plan":
        request = base_validation_request(plan=True)
    elif case_id == "valid_day_plan":
        request = base_validation_request(plan=True, day_plan=True)
    elif case_id == "valid_user_edited_plan":
        request = base_validation_request(plan=True)
        links = [link.model_copy(update={"user_edited": True}) for link in request.draft.plan_item_links]
        request = request.model_copy(update={
            "draft": request.draft.model_copy(update={"plan_item_links": links})
        })
    elif case_id == "five_visible_provenance_labels":
        request = with_all_provenance_categories()
    elif case_id == "fabricated_citation":
        link = request.draft.claims[0].evidence_links[0].model_copy(update={
            "evidence_id": "fabricated"
        })
        request = replace_claim(request, evidence_links=[link])
    elif case_id == "citation_not_in_stage7_packet":
        span = evidence_span("extra-valid", "Extra valid evidence", journey=request.context.journey)
        request = replace_packet(request, spans=[*request.evidence_packet.spans, span])
        request = replace_claim(request, text=span.exact_span, evidence_links=[evidence_link(span)])
    elif case_id == "missing_material_citation":
        request = replace_claim(request, evidence_links=[])
        kwargs["retrieval_retry"] = None
    elif case_id == "retired_evidence":
        request = _with_span(request, current=False, retired=True)
    elif case_id == "unapproved_evidence":
        request = _with_span(request, approval_state="unapproved", fixture_only=False)
    elif case_id == "wrong_source":
        link = request.draft.claims[0].evidence_links[0].model_copy(update={"source_id": "wrong"})
        request = replace_claim(request, evidence_links=[link])
    elif case_id == "wrong_span_text":
        text = "Plausible but different span"
        link = request.draft.claims[0].evidence_links[0].model_copy(update={
            "exact_span": text, "span_sha256": sha256(text.encode("utf-8")).hexdigest(),
        })
        request = replace_claim(request, evidence_links=[link])
    elif case_id == "wrong_span_hash":
        link = request.draft.claims[0].evidence_links[0].model_copy(update={"span_sha256": "0" * 64})
        request = replace_claim(request, evidence_links=[link])
    elif case_id == "wrong_workspace":
        request = _with_span(
            request, approval_state="confirmed_personal", fixture_only=False,
            workspace_id=OTHER_WORKSPACE, journey=None, jurisdictions=[],
        )
    elif case_id == "wrong_stage":
        request = replace_packet(request, journey=JourneyPosition(
            stage="postpartum", unit="week", exact=3,
        ))
    elif case_id == "wrong_week":
        request = _with_span(request, journey=JourneyPosition(
            stage="pregnancy", unit="week", exact=12,
        ))
    elif case_id == "wrong_week_range":
        request = _with_span(request, journey=JourneyPosition(
            stage="pregnancy", unit="week", range_start=20, range_end=23,
        ))
    elif case_id == "wrong_jurisdiction":
        request = _with_span(request, jurisdictions=["US"])
    elif case_id == "stale_state":
        request = replace_packet(request, state_version=2)
    elif case_id == "allergy_direct":
        request = replace_claim(request, text="Peanut snack", risk_tags=["peanut"])
    elif case_id == "allergy_hidden_tag":
        request = replace_claim(request, text="Energy snack", risk_tags=["peanut"])
    elif case_id == "restriction_override":
        request = replace_claim(request, overrides_context_ids=["restriction-1"])
    elif case_id == "public_overrides_record":
        item = ContextItem(
            item_id="appointment-public-override", kind=ContextKind.APPOINTMENT,
            state=FactState.CONFIRMED,
            value={"day": "wednesday", "start": "10:00", "end": "11:00"},
        )
        request = _with_context_item(request, item, apply=True)
        request = replace_claim(request, overrides_context_ids=[item.item_id])
    elif case_id == "condition_dropped":
        request = _with_context_item(request, ContextItem(
            item_id="condition-1", kind=ContextKind.CONDITION,
            state=FactState.CONFIRMED, value="documented condition",
        ))
    elif case_id == "instruction_override":
        item = ContextItem(
            item_id="instruction-1", kind=ContextKind.CLINICIAN_INSTRUCTION,
            state=FactState.CONFIRMED, value="avoid restricted activity",
        )
        request = _with_context_item(request, item, apply=True)
        request = replace_claim(request, overrides_context_ids=["instruction-1"])
    elif case_id == "condition_required_missing":
        request = _with_span(request, required_condition_ids=["condition-required"])
    elif case_id == "condition_excluded_present":
        item = ContextItem(
            item_id="condition-1", kind=ContextKind.CONDITION,
            state=FactState.CONFIRMED, value="documented condition",
        )
        request = _with_context_item(request, item, apply=True)
        request = _with_span(request, excluded_condition_ids=["condition-1"])
    elif case_id in {"medication_change", "supplement_timing_change"}:
        request = base_validation_request(plan=case_id == "supplement_timing_change")
        claims = list(request.draft.claims)
        index = (next(i for i, claim in enumerate(claims)
                      if claim.kind == ClaimKind.MEDICATION_RECORD)
                 if case_id == "supplement_timing_change" else 0)
        claims[index] = claims[index].model_copy(update={
            "text": "Stop this medication",
            "kind": ClaimKind.MEDICATION_RECORD,
            "origin": ClaimOrigin.CONFIRMED_PERSONAL,
            "provenance_category": ProvenanceCategory.CONFIRMED,
            "action": ClaimAction.PRESCRIBE_STOP,
        })
        if case_id == "medication_change":
            request = _with_span(
                request,
                allowed_claim_kinds=[ClaimKind.HEALTH_GUIDANCE, ClaimKind.MEDICATION_RECORD],
            )
        draft_updates = {"claims": claims}
        if case_id == "supplement_timing_change":
            schedule = request.draft.proposed_schedule
            items = list(schedule.items)
            items[index] = items[index].model_copy(update={"item": "Stop this medication"})
            draft_updates["proposed_schedule"] = schedule.model_copy(update={"items": items})
            draft_updates["plan_item_links"] = [
                link.model_copy(update={"user_edited": True})
                for link in request.draft.plan_item_links
            ]
        request = request.model_copy(update={
            "draft": request.draft.model_copy(update=draft_updates)
        })
        evaluator = _scripted(SemanticSupport.SUPPORTED, len(claims))
    elif case_id == "diagnosis":
        request = replace_claim(request, text="This means you have a diagnosis", action=ClaimAction.DIAGNOSE)
        evaluator = _scripted(SemanticSupport.SUPPORTED)
    elif case_id == "inferred_clearance":
        request = replace_claim(request, text="You are cleared to exercise", action=ClaimAction.ASSERT_CLEARANCE)
        evaluator = _scripted(SemanticSupport.SUPPORTED)
    elif case_id == "unsafe_reassurance":
        request = replace_claim(request, text="Nothing to worry about", action=ClaimAction.REASSURE)
        evaluator = _scripted(SemanticSupport.SUPPORTED)
    elif case_id == "fake_review":
        request = replace_claim(request, text="A doctor reviewed this")
        evaluator = _scripted(SemanticSupport.SUPPORTED)
    elif case_id == "summary_boundary_bypass":
        request = request.model_copy(update={
            "draft": request.draft.model_copy(update={"summary": "Stop this medication"})
        })
    elif case_id == "unauthorized_action":
        request = request.model_copy(update={
            "draft": request.draft.model_copy(update={"unauthorized_action_requested": True})
        })
    elif case_id == "unsupported_packet":
        request = replace_packet(request, support_state="unsupported", ordinary_generation_allowed=False)
    elif case_id == "partial_packet":
        request = replace_packet(request, support_state="partially_supported", ordinary_generation_allowed=False)
    elif case_id == "relevant_conflict":
        request = replace_packet(
            request, support_state="clarification_required", ordinary_generation_allowed=False,
            unresolved_conflict_ids=["conflict-1"],
        )
    elif case_id == "required_missing_information":
        request = replace_packet(
            request, support_state="clarification_required", ordinary_generation_allowed=False,
            missing_information_fields=["restriction"],
        )
    elif case_id == "urgent_composition_attempt":
        request = base_validation_request(urgent=True)
    elif case_id in {
        "plausible_irrelevant", "partial_semantic_support", "weaker_semantic_support",
        "uncertain_semantic_support",
    }:
        outcome = {
            "plausible_irrelevant": SemanticSupport.IRRELEVANT,
            "partial_semantic_support": SemanticSupport.PARTIAL,
            "weaker_semantic_support": SemanticSupport.WEAKER,
            "uncertain_semantic_support": SemanticSupport.UNCERTAIN,
        }[case_id]
        evaluator = _scripted(outcome)
    elif case_id == "similar_words_opposite_conclusion":
        request = _replace_span_and_claim(
            request,
            claim_text="Walking is safe at this intensity.",
            span_text="Walking is not safe at this intensity.",
        )
    elif case_id == "two_claims_one_supporting_span":
        first = request.draft.claims[0]
        second = first.model_copy(update={
            "claim_id": "claim-guidance-2",
            "text": "High intensity running is recommended every day.",
        })
        request = request.model_copy(update={
            "draft": request.draft.model_copy(update={"claims": [first, second]})
        })
    elif case_id == "general_nutrition_not_allergy_support":
        request = _replace_span_and_claim(
            request,
            claim_text="This meal will prevent allergic reactions.",
            span_text="A balanced eating pattern can include grains and vegetables.",
        )
    elif case_id == "movement_intensity_mismatch":
        request = _replace_span_and_claim(
            request,
            claim_text="High intensity exercise is recommended.",
            span_text="Gentle movement at a comfortable pace may be considered.",
        )
    elif case_id == "raw_recorded_constraint_plan":
        request = base_validation_request(
            plan=True,
            raw_text="Create a weekly nutrition plan using my recorded peanut allergy.",
        )
    elif case_id == "raw_urgent_plan":
        request = base_validation_request(
            plan=True,
            raw_text="I have heavy bleeding; create a nutrition plan too.",
        )
    elif case_id == "raw_ambiguous_plan":
        request = base_validation_request(
            plan=True,
            raw_text="I am dizzy and want a nutrition plan.",
        )
    elif case_id == "semantic_evaluator_unavailable":
        evaluator = ScriptedSemanticSupportEvaluator([SemanticEvaluatorUnavailable("offline")])
    elif case_id == "semantic_evaluator_timeout":
        evaluator = ScriptedSemanticSupportEvaluator([TimeoutError("timeout")])
    elif case_id == "one_mechanical_repair":
        request = replace_claim(request, provenance_category=None)
    elif case_id == "repair_not_allowed":
        request = replace_claim(request, provenance_category=ProvenanceCategory.CONFIRMED)
    elif case_id == "repair_failure":
        request = replace_claim(request, provenance_category=None)
        kwargs["repairer"] = lambda _: (_ for _ in ()).throw(ValueError("repair failed"))
    elif case_id == "second_repair_prevented":
        request = replace_claim(request, provenance_category=None)
        kwargs["repairer"] = lambda value: value
    elif case_id == "one_retrieval_retry":
        valid = request
        request = replace_packet(request, support_state="unsupported", ordinary_generation_allowed=False)
        kwargs["retrieval_retry"] = lambda _: valid
    elif case_id == "second_retry_prevented":
        request = replace_packet(request, support_state="unsupported", ordinary_generation_allowed=False)
        kwargs["retrieval_retry"] = lambda value: value
    elif case_id in {
        "plan_item_link_missing", "plan_item_evidence_mismatch",
        "plan_claim_evidence_mismatch", "plan_constraint_link_dropped",
        "combined_plan_conflict", "stale_plan",
    }:
        request = base_validation_request(plan=True)
        draft = request.draft
        if case_id == "plan_item_link_missing":
            draft = draft.model_copy(update={"plan_item_links": draft.plan_item_links[1:]})
        elif case_id == "plan_item_evidence_mismatch":
            links = list(draft.plan_item_links)
            links[1] = links[1].model_copy(update={"evidence_ids": ["DOC-001"]})
            draft = draft.model_copy(update={"plan_item_links": links})
        elif case_id == "plan_claim_evidence_mismatch":
            claims = list(draft.claims)
            index = next(i for i, claim in enumerate(claims) if claim.kind == ClaimKind.PLAN_ITEM)
            doc_span = request.evidence_packet.spans[1].model_copy(update={
                "allowed_claim_kinds": [
                    ClaimKind.PERSONAL_RECORD, ClaimKind.MEDICATION_RECORD, ClaimKind.PLAN_ITEM
                ]
            })
            spans = list(request.evidence_packet.spans)
            spans[1] = doc_span
            request = replace_packet(request, spans=spans)
            claims[index] = claims[index].model_copy(update={"evidence_links": [evidence_link(doc_span)]})
            draft = draft.model_copy(update={"claims": claims})
            evaluator = _scripted(SemanticSupport.SUPPORTED, len(claims))
        elif case_id == "plan_constraint_link_dropped":
            claims = list(draft.claims)
            index = next(i for i, claim in enumerate(claims) if claim.kind == ClaimKind.PLAN_ITEM)
            claims[index] = claims[index].model_copy(update={"applied_context_ids": []})
            draft = draft.model_copy(update={"claims": claims})
        else:
            schedule = draft.proposed_schedule.model_copy(update={
                "conflicts": ["combined conflict"] if case_id == "combined_plan_conflict" else [],
                "stale": case_id == "stale_plan",
                "save_eligible": False,
            })
            links = [link.model_copy(update={"user_edited": True})
                     for link in draft.plan_item_links]
            draft = draft.model_copy(update={
                "proposed_schedule": schedule, "plan_item_links": links,
            })
        request = request.model_copy(update={"draft": draft})
    elif case_id == "schema_extra_field":
        schema_payload = request.draft.model_dump(mode="python")
        schema_payload["unexpected"] = True
    elif case_id == "schema_invalid_claim_kind":
        schema_payload = request.draft.model_dump(mode="python")
        schema_payload["claims"][0]["kind"] = "medical_guess"
    return request, evaluator, kwargs, schema_payload


def run(*, write_report=False):
    expected = build_devset()
    tracked = [json.loads(line) for line in DEVSET.read_text(encoding="utf-8").splitlines()
               if line.strip()] if DEVSET.is_file() else []
    failures = []
    case_results = []
    groups = defaultdict(lambda: {"passed": 0, "total": 0})
    validators = defaultdict(lambda: {"positive": 0, "negative": 0})
    critical_passed = critical_total = 0
    latency = []
    max_retry = max_repair = composition_on_failure = urgent_composition = 0
    no_write_passed = no_write_total = 0
    for row in expected:
        started = perf_counter()
        problems = []
        observed_codes = []
        observed_disposition = ""
        try:
            request, evaluator, kwargs, schema_payload = _prepare(row["case_id"])
            if schema_payload is not None:
                try:
                    AnswerDraft.model_validate(schema_payload)
                    observed_disposition = "schema_accepted"
                except ValidationError:
                    observed_disposition = "schema_rejected"
                    observed_codes = [FindingCode.SCHEMA_INVALID.value]
            else:
                result = Stage8ValidationPipeline(evaluator).run(request, **kwargs)
                report = result.validation_report
                observed_disposition = report.disposition.value
                observed_codes = [code.value for code in report.trace.finding_codes]
                latency.append(report.trace.latency_ms)
                max_retry = max(max_retry, report.trace.retry_count)
                max_repair = max(max_repair, report.trace.repair_count)
                if report.disposition != "pass":
                    composition_on_failure += report.trace.ordinary_composition_call_count
                if request.safety_result.route == "urgent":
                    urgent_composition += report.trace.ordinary_composition_call_count
                no_write_total += 1
                if (report.trace.persistent_write_count == 0
                        and not result.persistent_write_performed):
                    no_write_passed += 1
                for check in report.checks:
                    if check.status == "pass":
                        validators[check.validator.value]["positive"] += 1
                    elif check.status == "fail":
                        validators[check.validator.value]["negative"] += 1
                if row["case_id"] == "five_visible_provenance_labels" and result.composed_answer:
                    if {section.provenance.value for section in result.composed_answer.sections} != {
                        category.value for category in ProvenanceCategory
                    }:
                        problems.append("visible provenance categories were merged or omitted")
                if row["case_id"] in {"second_repair_prevented", "second_retry_prevented"}:
                    if not report.repair_trace.second_attempt_prevented:
                        problems.append("second bounded attempt was not explicitly prevented")
            if observed_disposition != row["expected_disposition"]:
                problems.append(
                    f"disposition {observed_disposition} != {row['expected_disposition']}"
                )
            if set(observed_codes) != set(row["expected_finding_codes"]):
                problems.append(
                    f"finding codes {observed_codes} != {row['expected_finding_codes']}"
                )
        except Exception as exc:  # reported as an eval failure; never silently waived
            problems.append(f"unexpected {type(exc).__name__}: {exc}")
        passed = not problems
        groups[row["group"]]["total"] += 1
        groups[row["group"]]["passed"] += int(passed)
        if row["criticality"] == "critical":
            critical_total += 1
            critical_passed += int(passed)
        if not passed:
            failures.append({"case_id": row["case_id"], "problems": problems})
        case_results.append({
            "case_id": row["case_id"], "passed": passed,
            "expected_disposition": row["expected_disposition"],
            "observed_disposition": observed_disposition,
            "expected_finding_codes": row["expected_finding_codes"],
            "observed_finding_codes": observed_codes,
            "latency_ms": round((perf_counter() - started) * 1000, 6),
        })
    result = {
        "valid": tracked == expected and not failures,
        "stage": 8,
        "schema_version": "8.0.0",
        "dataset": "visible synthetic Stage 8 development set; sealed final holdout not accessed",
        "cases": {"passed": len(expected) - len(failures), "total": len(expected)},
        "critical_cases": {"passed": critical_passed, "total": critical_total},
        "groups": dict(sorted(groups.items())),
        "validator_coverage": dict(sorted(validators.items())),
        "bounded_attempts": {
            "maximum_retrieval_retries_observed": max_retry,
            "maximum_repairs_observed": max_repair,
            "composition_calls_on_failed_validation": composition_on_failure,
            "urgent_ordinary_composition_calls": urgent_composition,
        },
        "zero_persistent_writes": {"passed": no_write_passed, "total": no_write_total},
        "latency_ms": {
            "count": len(latency),
            "median": round(median(latency), 6) if latency else 0,
            "max": round(max(latency), 6) if latency else 0,
        },
        "provider": {
            "live_semantic_benchmark_run": False,
            "deterministic_fixture_evaluator": True,
            "paid_provider_required": False,
        },
        "case_results": case_results,
        "failures": failures,
        "limitations": [
            "The deterministic lexical fixture evaluator is not a production entailment benchmark.",
            "The visible synthetic set does not establish clinical validity or public-release readiness.",
            "No paid-provider or sealed-holdout result is claimed.",
        ],
    }
    if write_report:
        REPORT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                          encoding="utf-8", newline="\n")
    return result


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args(argv)
    result = run(write_report=args.write_report)
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
