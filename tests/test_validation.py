"""Executable Stage 8 validation, citation and composition boundaries."""

from __future__ import annotations

from hashlib import sha256
import unittest

from pydantic import ValidationError

from app.schemas.orchestration import ContextItem, ContextKind, FactState
from app.schemas.retrieval import JourneyPosition
from app.schemas.validation import (
    AnswerDraft,
    ClaimAction,
    ClaimKind,
    ClaimOrigin,
    FinalDisposition,
    FindingCode,
    ProvenanceCategory,
    SemanticSupport,
    Stage8Result,
    ValidationRequest,
)
from app.services.semantic_support import (
    ScriptedSemanticSupportEvaluator,
    SemanticEvaluatorUnavailable,
)
from app.services.validation import Stage8ValidationPipeline
from scripts.stage8_fixture_support import (
    base_validation_request,
    evidence_link,
    evidence_span,
    replace_claim,
    replace_packet,
    with_all_provenance_categories,
)


def codes(result):
    return {finding.code for finding in result.validation_report.findings}


def with_span(request, **updates):
    spans = list(request.evidence_packet.spans)
    spans[0] = spans[0].model_copy(update=updates)
    return replace_packet(request, spans=spans)


class Stage8HappyPathTests(unittest.TestCase):
    def test_fully_supported_answer_passes_all_seven_validators(self):
        result = Stage8ValidationPipeline().run(base_validation_request())
        self.assertEqual(result.validation_report.disposition, FinalDisposition.PASS)
        self.assertEqual(len(result.validation_report.checks), 7)
        self.assertTrue(all(check.status == "pass" for check in result.validation_report.checks))
        self.assertTrue(result.ordinary_composition_called)
        self.assertTrue(result.composed_answer.display_allowed)

    def test_valid_weekly_plan_validates_each_item_and_combined_schedule(self):
        request = base_validation_request(plan=True)
        result = Stage8ValidationPipeline().run(request)
        self.assertEqual(result.validation_report.disposition, FinalDisposition.PASS)
        self.assertEqual(
            {link.schedule_item_id for link in request.draft.plan_item_links},
            {item.schedule_item_id for item in request.draft.proposed_schedule.items},
        )

    def test_user_edited_plan_uses_same_validator_without_persistence(self):
        request = base_validation_request(plan=True)
        links = [link.model_copy(update={"user_edited": True})
                 for link in request.draft.plan_item_links]
        request = request.model_copy(update={
            "draft": request.draft.model_copy(update={"plan_item_links": links})
        })
        result = Stage8ValidationPipeline().run(request)
        self.assertEqual(result.validation_report.disposition, FinalDisposition.PASS)
        self.assertFalse(result.persistent_write_performed)
        self.assertTrue(result.proposal_only)

    def test_all_visible_provenance_categories_remain_distinct(self):
        result = Stage8ValidationPipeline().run(with_all_provenance_categories())
        labels = {section.provenance for section in result.composed_answer.sections}
        self.assertEqual(labels, set(ProvenanceCategory))

    def test_trace_records_versions_evidence_and_zero_write(self):
        result = Stage8ValidationPipeline().run(base_validation_request())
        trace = result.validation_report.trace
        self.assertEqual(trace.schema_version, "8.0.0")
        self.assertEqual(trace.evidence_ids, ["food-safe"])
        self.assertEqual(trace.persistent_write_count, 0)
        self.assertFalse(trace.raw_personal_text_logged)
        self.assertEqual(trace.ordinary_composition_call_count, 1)


class Stage8SchemaStateAndJourneyTests(unittest.TestCase):
    def test_extra_draft_field_is_rejected(self):
        payload = base_validation_request().draft.model_dump(mode="python")
        payload["unexpected"] = True
        with self.assertRaises(ValidationError):
            AnswerDraft.model_validate(payload)

    def test_malformed_claim_type_is_rejected(self):
        payload = base_validation_request().draft.model_dump(mode="python")
        payload["claims"][0]["kind"] = "medical_guess"
        with self.assertRaises(ValidationError):
            AnswerDraft.model_validate(payload)

    def test_request_identity_mutation_is_rejected_by_schema(self):
        payload = base_validation_request().model_dump(mode="python")
        payload["draft"]["request_id"] = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
        with self.assertRaises(ValidationError):
            ValidationRequest.model_validate(payload)

    def test_stale_draft_state_is_rejected(self):
        request = base_validation_request()
        request = request.model_copy(update={
            "draft": request.draft.model_copy(update={"journey_state_version": 2})
        })
        result = Stage8ValidationPipeline().run(request)
        self.assertIn(FindingCode.STALE_STATE_VERSION, codes(result))

    def test_stale_packet_state_is_rejected(self):
        result = Stage8ValidationPipeline().run(replace_packet(
            base_validation_request(), state_version=2,
        ))
        self.assertIn(FindingCode.STALE_STATE_VERSION, codes(result))

    def test_wrong_stage_is_rejected(self):
        request = replace_packet(
            base_validation_request(),
            journey=JourneyPosition(stage="postpartum", unit="week", exact=3),
        )
        result = Stage8ValidationPipeline().run(request)
        self.assertIn(FindingCode.JOURNEY_MISMATCH, codes(result))

    def test_wrong_week_span_is_rejected(self):
        request = with_span(
            base_validation_request(),
            journey=JourneyPosition(stage="pregnancy", unit="week", exact=12),
        )
        result = Stage8ValidationPipeline().run(request)
        self.assertIn(FindingCode.WRONG_WEEK, codes(result))

    def test_wrong_jurisdiction_span_is_rejected(self):
        result = Stage8ValidationPipeline().run(with_span(
            base_validation_request(), jurisdictions=["US"],
        ))
        self.assertIn(FindingCode.WRONG_JURISDICTION, codes(result))

    def test_wrong_producing_agent_is_rejected(self):
        request = base_validation_request()
        request = request.model_copy(update={
            "draft": request.draft.model_copy(update={"agent": "movement_agent"})
        })
        result = Stage8ValidationPipeline().run(request)
        self.assertIn(FindingCode.REQUEST_ID_MISMATCH, codes(result))


class Stage8ConstraintTests(unittest.TestCase):
    def test_allergen_included_directly_is_rejected(self):
        request = replace_claim(
            base_validation_request(), text="Peanut snack", risk_tags=["peanut"],
        )
        result = Stage8ValidationPipeline().run(request)
        self.assertIn(FindingCode.ALLERGY_VIOLATION, codes(result))

    def test_hidden_allergen_tag_is_rejected(self):
        request = replace_claim(
            base_validation_request(), text="Energy snack", risk_tags=["peanut"],
        )
        result = Stage8ValidationPipeline().run(request)
        self.assertIn(FindingCode.ALLERGY_VIOLATION, codes(result))

    def test_peanut_free_wording_is_not_a_violation(self):
        result = Stage8ValidationPipeline().run(base_validation_request())
        self.assertNotIn(FindingCode.ALLERGY_VIOLATION, codes(result))

    def test_confirmed_restriction_override_is_rejected(self):
        request = replace_claim(
            base_validation_request(), overrides_context_ids=["restriction-1"],
        )
        result = Stage8ValidationPipeline().run(request)
        self.assertIn(FindingCode.RESTRICTION_VIOLATION, codes(result))

    def test_confirmed_clinician_instruction_override_is_rejected(self):
        request = base_validation_request()
        instruction = ContextItem(
            item_id="instruction-1", kind=ContextKind.CLINICIAN_INSTRUCTION,
            state=FactState.CONFIRMED, value="avoid restricted activity",
        )
        context = request.context.model_copy(update={
            "items": [*request.context.items, instruction]
        })
        request = request.model_copy(update={"context": context})
        request = replace_claim(request, overrides_context_ids=["instruction-1"])
        result = Stage8ValidationPipeline().run(request)
        self.assertIn(FindingCode.CONFIRMED_INSTRUCTION_VIOLATION, codes(result))

    def test_confirmed_condition_cannot_be_silently_dropped(self):
        request = base_validation_request()
        condition = ContextItem(
            item_id="condition-1", kind=ContextKind.CONDITION,
            state=FactState.CONFIRMED, value="documented condition",
        )
        context = request.context.model_copy(update={
            "items": [*request.context.items, condition]
        })
        request = request.model_copy(update={"context": context})
        result = Stage8ValidationPipeline().run(request)
        self.assertIn(FindingCode.CONDITION_CONTEXT_DROPPED, codes(result))

    def test_required_constraint_inventory_cannot_be_dropped(self):
        request = base_validation_request()
        request = request.model_copy(update={
            "draft": request.draft.model_copy(update={"applied_context_ids": []})
        })
        result = Stage8ValidationPipeline().run(request)
        self.assertIn(FindingCode.REQUIRED_CONSTRAINT_DROPPED, codes(result))


class Stage8EvidenceAndCitationTests(unittest.TestCase):
    def test_material_claim_without_evidence_is_rejected(self):
        result = Stage8ValidationPipeline().run(replace_claim(
            base_validation_request(), evidence_links=[],
        ), retrieval_retry=None)
        self.assertIn(FindingCode.MATERIAL_CLAIM_WITHOUT_EVIDENCE, codes(result))

    def test_fabricated_citation_is_rejected(self):
        request = base_validation_request()
        bad = request.draft.claims[0].evidence_links[0].model_copy(update={
            "evidence_id": "fabricated-evidence"
        })
        result = Stage8ValidationPipeline().run(replace_claim(
            request, evidence_links=[bad],
        ))
        self.assertIn(FindingCode.FABRICATED_CITATION, codes(result))

    def test_citation_absent_from_stage7_worker_packet_is_rejected(self):
        request = base_validation_request()
        extra = evidence_span(
            "extra-valid", "Extra valid evidence", journey=request.context.journey,
        )
        packet = request.evidence_packet.model_copy(update={
            "spans": [*request.evidence_packet.spans, extra]
        })
        request = request.model_copy(update={"evidence_packet": packet})
        request = replace_claim(request, text=extra.exact_span,
                                evidence_links=[evidence_link(extra)])
        result = Stage8ValidationPipeline().run(request)
        self.assertIn(FindingCode.CITATION_NOT_IN_PACKET, codes(result))

    def test_source_mismatch_is_rejected(self):
        request = base_validation_request()
        bad = request.draft.claims[0].evidence_links[0].model_copy(update={"source_id": "wrong"})
        result = Stage8ValidationPipeline().run(replace_claim(request, evidence_links=[bad]))
        self.assertIn(FindingCode.CITATION_SOURCE_MISMATCH, codes(result))

    def test_exact_span_text_mismatch_is_rejected(self):
        request = base_validation_request()
        text = "Plausible but different span"
        bad = request.draft.claims[0].evidence_links[0].model_copy(update={
            "exact_span": text,
            "span_sha256": sha256(text.encode("utf-8")).hexdigest(),
        })
        result = Stage8ValidationPipeline().run(replace_claim(request, evidence_links=[bad]))
        self.assertIn(FindingCode.SPAN_TEXT_MISMATCH, codes(result))

    def test_exact_span_hash_mismatch_is_rejected(self):
        request = base_validation_request()
        bad = request.draft.claims[0].evidence_links[0].model_copy(update={"span_sha256": "0" * 64})
        result = Stage8ValidationPipeline().run(replace_claim(request, evidence_links=[bad]))
        self.assertIn(FindingCode.SPAN_HASH_MISMATCH, codes(result))

    def test_retired_evidence_is_rejected(self):
        result = Stage8ValidationPipeline().run(with_span(
            base_validation_request(), current=False, retired=True,
        ))
        self.assertIn(FindingCode.EVIDENCE_RETIRED, codes(result))

    def test_unapproved_evidence_is_rejected(self):
        result = Stage8ValidationPipeline().run(with_span(
            base_validation_request(), approval_state="unapproved", fixture_only=False,
        ))
        self.assertIn(FindingCode.EVIDENCE_UNAPPROVED, codes(result))

    def test_wrong_workspace_personal_evidence_is_rejected(self):
        request = base_validation_request()
        other = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
        result = Stage8ValidationPipeline().run(with_span(
            request, approval_state="confirmed_personal", fixture_only=False,
            workspace_id=other, jurisdictions=[], journey=None,
        ))
        self.assertIn(FindingCode.EVIDENCE_WRONG_WORKSPACE, codes(result))

    def test_plausible_irrelevant_citation_is_rejected(self):
        evaluator = ScriptedSemanticSupportEvaluator([SemanticSupport.IRRELEVANT])
        result = Stage8ValidationPipeline(evaluator).run(base_validation_request())
        self.assertIn(FindingCode.CITATION_IRRELEVANT, codes(result))

    def test_partial_support_is_rejected(self):
        evaluator = ScriptedSemanticSupportEvaluator([SemanticSupport.PARTIAL])
        result = Stage8ValidationPipeline(evaluator).run(base_validation_request())
        self.assertIn(FindingCode.CITATION_PARTIAL_SUPPORT, codes(result))

    def test_weaker_support_is_rejected(self):
        evaluator = ScriptedSemanticSupportEvaluator([SemanticSupport.WEAKER])
        result = Stage8ValidationPipeline(evaluator).run(base_validation_request())
        self.assertIn(FindingCode.CITATION_WEAKER_SUPPORT, codes(result))

    def test_uncertain_semantic_support_is_not_pass(self):
        evaluator = ScriptedSemanticSupportEvaluator([SemanticSupport.UNCERTAIN])
        result = Stage8ValidationPipeline(evaluator).run(base_validation_request())
        self.assertIn(FindingCode.SEMANTIC_SUPPORT_UNCERTAIN, codes(result))

    def test_unavailable_semantic_evaluator_fails_closed(self):
        evaluator = ScriptedSemanticSupportEvaluator([
            SemanticEvaluatorUnavailable("offline")
        ])
        result = Stage8ValidationPipeline(evaluator).run(base_validation_request())
        self.assertIn(FindingCode.SEMANTIC_EVALUATOR_UNAVAILABLE, codes(result))

    def test_semantic_evaluator_timeout_fails_closed(self):
        evaluator = ScriptedSemanticSupportEvaluator([TimeoutError("timeout")])
        result = Stage8ValidationPipeline(evaluator).run(base_validation_request())
        self.assertIn(FindingCode.SEMANTIC_EVALUATOR_TIMEOUT, codes(result))


class Stage8BoundaryAndConsistencyTests(unittest.TestCase):
    def _boundary_case(self, text, action, code, kind=ClaimKind.HEALTH_GUIDANCE):
        request = replace_claim(
            base_validation_request(), text=text, action=action, kind=kind,
        )
        result = Stage8ValidationPipeline(
            ScriptedSemanticSupportEvaluator([SemanticSupport.SUPPORTED])
        ).run(request)
        self.assertIn(code, codes(result))

    def test_diagnosis_is_rejected(self):
        self._boundary_case("This means you have a diagnosis", ClaimAction.DIAGNOSE,
                            FindingCode.DIAGNOSIS)

    def test_medication_change_is_rejected(self):
        self._boundary_case(
            "Stop this medication", ClaimAction.PRESCRIBE_STOP,
            FindingCode.PRESCRIBING_OR_MEDICATION_CHANGE,
            ClaimKind.MEDICATION_RECORD,
        )

    def test_inferred_clearance_is_rejected(self):
        self._boundary_case("You are safe to exercise", ClaimAction.ASSERT_CLEARANCE,
                            FindingCode.INFERRED_CLEARANCE)

    def test_unsafe_reassurance_is_rejected(self):
        self._boundary_case("Nothing to worry about", ClaimAction.REASSURE,
                            FindingCode.UNSAFE_REASSURANCE)

    def test_fake_professional_review_is_rejected(self):
        self._boundary_case("A doctor reviewed this", ClaimAction.DESCRIBE,
                            FindingCode.FAKE_PROFESSIONAL_REVIEW)

    def test_model_support_cannot_override_medication_boundary(self):
        self._boundary_case(
            "Increase this medication dose", ClaimAction.PRESCRIBE_CHANGE,
            FindingCode.PRESCRIBING_OR_MEDICATION_CHANGE,
            ClaimKind.MEDICATION_RECORD,
        )

    def test_public_guidance_cannot_override_personal_record(self):
        result = Stage8ValidationPipeline().run(replace_claim(
            base_validation_request(), overrides_context_ids=["restriction-1"],
        ))
        self.assertIn(FindingCode.PUBLIC_OVERRIDES_PERSONAL, codes(result))

    def test_unauthorized_proposed_action_is_rejected(self):
        request = base_validation_request()
        request = request.model_copy(update={
            "draft": request.draft.model_copy(update={"unauthorized_action_requested": True})
        })
        result = Stage8ValidationPipeline().run(request)
        self.assertIn(FindingCode.UNAUTHORIZED_ACTION, codes(result))

    def test_urgent_stage6_result_bypasses_ordinary_composition(self):
        result = Stage8ValidationPipeline().run(base_validation_request(urgent=True))
        self.assertEqual(result.validation_report.disposition, FinalDisposition.ESCALATE)
        self.assertFalse(result.ordinary_composition_called)
        self.assertEqual(result.urgent_fixed_message, result.safety_result.fixed_message)
        self.assertIn(FindingCode.URGENT_COMPOSITION_BLOCKED, codes(result))

    def test_result_schema_rejects_urgent_with_composed_answer(self):
        valid = Stage8ValidationPipeline().run(base_validation_request())
        urgent = Stage8ValidationPipeline().run(base_validation_request(urgent=True))
        payload = urgent.model_dump(mode="python")
        payload["composed_answer"] = valid.composed_answer.model_dump(mode="python")
        payload["ordinary_composition_called"] = True
        with self.assertRaises(ValidationError):
            Stage8Result.model_validate(payload)


class Stage8AnswerabilityAndRetryTests(unittest.TestCase):
    def test_unsupported_packet_abstains(self):
        request = replace_packet(
            base_validation_request(), support_state="unsupported",
            ordinary_generation_allowed=False,
        )
        result = Stage8ValidationPipeline().run(request)
        self.assertEqual(result.validation_report.disposition, FinalDisposition.ABSTAIN)
        self.assertIn(FindingCode.UNSUPPORTED_EVIDENCE_PACKET, codes(result))

    def test_partial_packet_abstains(self):
        request = replace_packet(
            base_validation_request(), support_state="partially_supported",
            ordinary_generation_allowed=False,
        )
        result = Stage8ValidationPipeline().run(request)
        self.assertIn(FindingCode.PARTIAL_EVIDENCE_PACKET, codes(result))

    def test_relevant_conflict_requires_clarification(self):
        request = replace_packet(
            base_validation_request(), support_state="clarification_required",
            ordinary_generation_allowed=False,
            unresolved_conflict_ids=["conflict-1"],
        )
        result = Stage8ValidationPipeline().run(request)
        self.assertEqual(result.validation_report.disposition, FinalDisposition.CLARIFY)
        self.assertIn(FindingCode.RELEVANT_CONFLICT, codes(result))

    def test_required_missing_information_requires_clarification(self):
        request = replace_packet(
            base_validation_request(), support_state="clarification_required",
            ordinary_generation_allowed=False,
            missing_information_fields=["confirmed restriction"],
        )
        result = Stage8ValidationPipeline().run(request)
        self.assertEqual(result.validation_report.disposition, FinalDisposition.CLARIFY)
        self.assertIn(FindingCode.REQUIRED_INFORMATION_MISSING, codes(result))

    def test_missing_provenance_has_one_successful_mechanical_repair(self):
        request = replace_claim(base_validation_request(), provenance_category=None)
        result = Stage8ValidationPipeline().run(request)
        self.assertEqual(result.validation_report.disposition, FinalDisposition.PASS)
        self.assertEqual(result.validation_report.trace.repair_count, 1)
        self.assertEqual(result.validation_report.repair_trace.action, "mechanical_repair")

    def test_incorrect_provenance_is_not_mechanically_repaired(self):
        request = replace_claim(
            base_validation_request(),
            provenance_category=ProvenanceCategory.CONFIRMED,
        )
        result = Stage8ValidationPipeline().run(request)
        self.assertEqual(result.validation_report.trace.repair_count, 0)
        self.assertIn(FindingCode.PROVENANCE_LABEL_INVALID, codes(result))

    def test_failed_repair_stops(self):
        request = replace_claim(base_validation_request(), provenance_category=None)
        result = Stage8ValidationPipeline().run(
            request, repairer=lambda _: (_ for _ in ()).throw(ValueError("fail")),
        )
        self.assertEqual(result.validation_report.trace.repair_count, 1)
        self.assertIn(FindingCode.REPAIR_FAILED, codes(result))

    def test_second_repair_loop_is_prevented(self):
        request = replace_claim(base_validation_request(), provenance_category=None)
        result = Stage8ValidationPipeline().run(request, repairer=lambda value: value)
        self.assertTrue(result.validation_report.repair_trace.second_attempt_prevented)
        self.assertEqual(result.validation_report.trace.repair_count, 1)

    def test_one_successful_retrieval_retry(self):
        valid = base_validation_request()
        unsupported = replace_packet(
            valid, support_state="unsupported", ordinary_generation_allowed=False,
        )
        result = Stage8ValidationPipeline().run(
            unsupported, retrieval_retry=lambda _: valid,
        )
        self.assertEqual(result.validation_report.disposition, FinalDisposition.PASS)
        self.assertEqual(result.validation_report.trace.retry_count, 1)

    def test_second_retrieval_retry_is_prevented(self):
        unsupported = replace_packet(
            base_validation_request(), support_state="unsupported",
            ordinary_generation_allowed=False,
        )
        result = Stage8ValidationPipeline().run(
            unsupported, retrieval_retry=lambda value: value,
        )
        self.assertTrue(result.validation_report.repair_trace.second_attempt_prevented)
        self.assertEqual(result.validation_report.trace.retry_count, 1)


class Stage8PlanNegativeTests(unittest.TestCase):
    def test_missing_plan_item_link_is_rejected(self):
        request = base_validation_request(plan=True)
        request = request.model_copy(update={
            "draft": request.draft.model_copy(update={
                "plan_item_links": request.draft.plan_item_links[1:]
            })
        })
        result = Stage8ValidationPipeline().run(request)
        self.assertIn(FindingCode.PLAN_ITEM_UNVALIDATED, codes(result))

    def test_plan_evidence_mismatch_is_rejected(self):
        request = base_validation_request(plan=True)
        links = list(request.draft.plan_item_links)
        links[1] = links[1].model_copy(update={"evidence_ids": ["DOC-001"]})
        request = request.model_copy(update={
            "draft": request.draft.model_copy(update={"plan_item_links": links})
        })
        result = Stage8ValidationPipeline().run(request)
        self.assertIn(FindingCode.PLAN_EVIDENCE_MISMATCH, codes(result))

    def test_combined_schedule_conflict_is_rejected(self):
        request = base_validation_request(plan=True)
        schedule = request.draft.proposed_schedule.model_copy(update={
            "conflicts": ["combined workload conflict"], "save_eligible": False,
        })
        request = request.model_copy(update={
            "draft": request.draft.model_copy(update={"proposed_schedule": schedule})
        })
        result = Stage8ValidationPipeline().run(request)
        self.assertIn(FindingCode.PLAN_COMBINED_CONSTRAINT_FAILURE, codes(result))

    def test_stale_schedule_is_rejected(self):
        request = base_validation_request(plan=True)
        schedule = request.draft.proposed_schedule.model_copy(update={
            "stale": True, "save_eligible": False,
        })
        request = request.model_copy(update={
            "draft": request.draft.model_copy(update={"proposed_schedule": schedule})
        })
        result = Stage8ValidationPipeline().run(request)
        self.assertIn(FindingCode.PLAN_COMBINED_CONSTRAINT_FAILURE, codes(result))

    def test_recorded_supplement_timing_cannot_be_changed(self):
        request = base_validation_request(plan=True)
        claims = list(request.draft.claims)
        index = next(i for i, claim in enumerate(claims) if claim.kind == ClaimKind.MEDICATION_RECORD)
        claims[index] = claims[index].model_copy(update={
            "text": "Reschedule this supplement",
            "action": ClaimAction.PRESCRIBE_CHANGE,
        })
        request = request.model_copy(update={
            "draft": request.draft.model_copy(update={"claims": claims})
        })
        evaluator = ScriptedSemanticSupportEvaluator(
            [SemanticSupport.SUPPORTED] * len(request.draft.claims)
        )
        result = Stage8ValidationPipeline(evaluator).run(request)
        self.assertIn(FindingCode.PRESCRIBING_OR_MEDICATION_CHANGE, codes(result))


class Stage8RectificationTests(unittest.TestCase):
    def test_stage6_clarification_bypasses_composition(self):
        request = base_validation_request(clarification=True)
        self.assertEqual(request.safety_result.route, "needs_clarification")
        result = Stage8ValidationPipeline().run(request)
        self.assertEqual(result.validation_report.disposition, FinalDisposition.CLARIFY)
        self.assertIn(FindingCode.SAFETY_CLARIFICATION_BLOCKED, codes(result))
        self.assertFalse(result.ordinary_composition_called)

    def test_stale_stage7_worker_state_is_rejected(self):
        request = base_validation_request()
        workers = [worker.model_copy(update={"journey_state_version": 2})
                   for worker in request.orchestration_result.worker_results]
        orchestration = request.orchestration_result.model_copy(update={"worker_results": workers})
        request = request.model_copy(update={"orchestration_result": orchestration})
        result = Stage8ValidationPipeline().run(request)
        self.assertIn(FindingCode.STALE_STATE_VERSION, codes(result))

    def test_packet_allowed_claim_types_are_enforced(self):
        request = replace_packet(
            base_validation_request(), allowed_claim_types=["record_only_medication"]
        )
        result = Stage8ValidationPipeline().run(request)
        self.assertIn(FindingCode.CLAIM_TYPE_NOT_ALLOWED, codes(result))

    def test_two_exact_spans_can_share_one_evidence_id(self):
        request = base_validation_request()
        second = evidence_span(
            "food-safe", "Alternative meal framework",
            source_id="source-food-safe", journey=request.context.journey,
        )
        request = replace_packet(
            request,
            spans=[*request.evidence_packet.spans, second],
            required_citation_ids=["food-safe"],
        )
        request = replace_claim(
            request, text=second.exact_span, evidence_links=[evidence_link(second)]
        )
        result = Stage8ValidationPipeline(
            ScriptedSemanticSupportEvaluator([SemanticSupport.SUPPORTED])
        ).run(request)
        self.assertEqual(result.validation_report.disposition, FinalDisposition.PASS)
        self.assertIn(second.span_id, result.validation_report.trace.span_ids)

    def test_plan_item_text_cannot_change_without_matching_claim(self):
        request = base_validation_request(plan=True)
        schedule = request.draft.proposed_schedule
        items = list(schedule.items)
        items[1] = items[1].model_copy(update={"item": "Unvalidated changed item"})
        changed = schedule.model_copy(update={"items": items})
        links = [link.model_copy(update={"user_edited": True})
                 for link in request.draft.plan_item_links]
        request = request.model_copy(update={
            "draft": request.draft.model_copy(update={
                "proposed_schedule": changed, "plan_item_links": links,
            })
        })
        result = Stage8ValidationPipeline().run(request)
        self.assertIn(FindingCode.PLAN_ITEM_UNVALIDATED, codes(result))

    def test_plan_span_link_mismatch_is_rejected(self):
        request = base_validation_request(plan=True)
        links = list(request.draft.plan_item_links)
        links[1] = links[1].model_copy(update={"span_ids": ["span-fabricated"]})
        request = request.model_copy(update={
            "draft": request.draft.model_copy(update={"plan_item_links": links})
        })
        result = Stage8ValidationPipeline().run(request)
        self.assertIn(FindingCode.PLAN_EVIDENCE_MISMATCH, codes(result))

    def test_validation_report_display_contradiction_is_rejected(self):
        result = Stage8ValidationPipeline().run(base_validation_request())
        payload = result.validation_report.model_dump(mode="python")
        payload["display_allowed"] = False
        with self.assertRaises(ValidationError):
            type(result.validation_report).model_validate(payload)

    def test_validation_report_trace_disposition_contradiction_is_rejected(self):
        result = Stage8ValidationPipeline().run(base_validation_request())
        payload = result.validation_report.model_dump(mode="python")
        payload["trace"]["final_disposition"] = "abstain"
        with self.assertRaises(ValidationError):
            type(result.validation_report).model_validate(payload)

    def test_composed_answer_duplicate_provenance_is_rejected(self):
        result = Stage8ValidationPipeline().run(base_validation_request())
        payload = result.composed_answer.model_dump(mode="python")
        payload["sections"].append(dict(payload["sections"][0]))
        with self.assertRaises(ValidationError):
            type(result.composed_answer).model_validate(payload)


    def test_stage5_packet_adapter_preserves_authenticated_inventory(self):
        from tests.test_retrieval import gateway, request as retrieval_request, retrieve
        from app.services.validation import validation_packet_from_retrieval

        original = retrieve(gateway(), retrieval_request()).packet
        packet = validation_packet_from_retrieval(original)
        self.assertEqual(packet.request_id, original.request_id)
        self.assertEqual(packet.workspace_id, original.workspace_id)
        self.assertEqual(packet.care_episode_id, original.care_episode_id)
        self.assertEqual(packet.state_version, original.trusted_state.cache_state_version)
        self.assertEqual(packet.required_citation_ids, original.required_citations)
        self.assertEqual(len(packet.spans), 1)
        self.assertEqual(packet.spans[0].exact_span, original.approved_guideline_passages[0].spans[0].exact_text)

class Stage8IndependentReviewSemanticHardCases(unittest.TestCase):
    @staticmethod
    def _replace_span_and_claim(request, *, claim_text: str, span_text: str):
        span = request.evidence_packet.spans[0]
        digest = sha256(span_text.encode("utf-8")).hexdigest()
        changed_span = span.model_copy(update={
            "exact_span": span_text,
            "span_sha256": digest,
        })
        changed_link = request.draft.claims[0].evidence_links[0].model_copy(update={
            "exact_span": span_text,
            "span_sha256": digest,
        })
        request = replace_packet(request, spans=[changed_span])
        return replace_claim(request, text=claim_text, evidence_links=[changed_link])

    def test_similar_words_with_opposite_conclusion_fail_closed(self):
        request = self._replace_span_and_claim(
            base_validation_request(),
            claim_text="Walking is safe at this intensity.",
            span_text="Walking is not safe at this intensity.",
        )
        result = Stage8ValidationPipeline().run(request)
        self.assertIn(FindingCode.CITATION_IRRELEVANT, codes(result))
        self.assertFalse(result.ordinary_composition_called)

    def test_two_material_claims_with_one_supporting_span_rejects_unsupported_claim(self):
        request = base_validation_request()
        first = request.draft.claims[0]
        second = first.model_copy(update={
            "claim_id": "claim-guidance-2",
            "text": "High intensity running is recommended every day.",
        })
        request = request.model_copy(update={
            "draft": request.draft.model_copy(update={"claims": [first, second]})
        })
        result = Stage8ValidationPipeline().run(request)
        self.assertIn(FindingCode.CITATION_IRRELEVANT, codes(result))
        self.assertEqual(len(result.validation_report.trace.semantic_assessments), 2)
        self.assertFalse(result.ordinary_composition_called)

    def test_general_nutrition_span_does_not_prove_allergy_specific_safety(self):
        request = self._replace_span_and_claim(
            base_validation_request(),
            claim_text="This meal will prevent allergic reactions.",
            span_text="A balanced eating pattern can include grains and vegetables.",
        )
        result = Stage8ValidationPipeline().run(request)
        self.assertIn(FindingCode.CITATION_IRRELEVANT, codes(result))
        self.assertFalse(result.ordinary_composition_called)

    def test_gentle_movement_span_does_not_support_high_intensity_instruction(self):
        request = self._replace_span_and_claim(
            base_validation_request(),
            claim_text="High intensity exercise is recommended.",
            span_text="Gentle movement at a comfortable pace may be considered.",
        )
        result = Stage8ValidationPipeline().run(request)
        self.assertTrue(
            {FindingCode.CITATION_IRRELEVANT, FindingCode.CITATION_WEAKER_SUPPORT}
            & codes(result)
        )
        self.assertFalse(result.ordinary_composition_called)

if __name__ == "__main__":
    unittest.main()
