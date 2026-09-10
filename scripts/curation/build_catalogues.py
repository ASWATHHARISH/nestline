"""Authored catalogue drafts and safety contract; no automatic publication."""

import re

from scripts.curation.correct_stage0 import DATA, ROOT, scope, write_csv, write_json, ensure_drafts_only


def item(key, kind, title, description, timing, refs, details, required=(), excluded=()):
    return dict(item_id=key, kind=kind, title=title, description=description, applies_to=timing,
                jurisdiction=["IN"], evidence_span_ids=refs, conditions_required=list(required),
                conditions_excluded=list(excluded), status="draft", version="1.0.0",
                blockers=["Named content, clinical, India-localisation, licence and product review pending."], details=details)


def main():
    ensure_drafts_only()
    preg, pp = scope("pregnancy", 4, 42), scope("postpartum", 1, 12)
    foods = []
    examples = [
        ("MILK", "Pasteurised milk", "milk", ["milk"], ["calcium", "protein"], "IN-FOOD-DAIRY", ["vegetarian"], "Use pasteurised milk."),
        ("CURD", "Plain curd", "curd", ["milk"], ["calcium", "protein"], "IN-FOOD-DAIRY", ["vegetarian"], "Check milk source and refrigeration."),
        ("PANEER", "Paneer", "paneer", ["milk"], ["calcium", "protein"], "IN-FOOD-DAIRY", ["vegetarian"], "Check milk source and storage."),
        ("PULSES", "Cooked pulses or plain dal", "pulses", [], ["protein"], "IN-FOOD-GRAINS", ["vegetarian", "vegan"], "Check every ingredient in a prepared dal; no raw sprouts."),
        ("GRAINS", "Whole-grain cereal", "whole_grains", [], ["protein"], "IN-FOOD-GRAINS", ["vegetarian", "vegan"], "Identify the exact grain; allergen status is unknown until then."),
        ("GREENS", "Green leafy vegetables", "leafy_vegetables", [], ["iron", "folate"], "IN-FOOD-GREENS", ["vegetarian", "vegan"], "Wash produce and prepare hygienically."),
        ("EGG", "Cooked egg", "egg", ["egg"], ["protein", "iron"], "IN-FOOD-ANIMAL", ["includes_eggs"], "Confirm thorough cooking and ingredients."),
        ("CHICKEN", "Cooked chicken", "chicken", [], ["protein", "iron"], "IN-FOOD-ANIMAL", ["nonvegetarian"], "Cook thoroughly and separate raw meat."),
        ("FISH", "Cooked fish, species to confirm", "fish", ["fish"], ["protein", "iron"], "IN-FOOD-ANIMAL", ["nonvegetarian"], "Species/mercury suitability needs a separate reviewed decision; not eligible by default."),
        ("SOYA", "Soya beans", "soya", ["soy"], ["protein"], "IN-FOOD-PLANTS", ["vegetarian", "vegan"], "Check processed-product ingredients and prepare hygienically."),
        ("NUTS", "Nuts, exact type to confirm", "nuts", ["tree_nuts", "peanut"], ["protein"], "IN-FOOD-PLANTS", ["vegetarian", "vegan"], "Do not assume the nut species or cross-contact status."),
        ("FRUIT", "Seasonal fruit", "fruit", [], [], "IN-FOOD", ["vegetarian", "vegan"], "Wash produce; record the exact fruit and any personal restriction."),
    ]
    for key, title, ingredient, allergens, nutrients, ref, diets, handling in examples:
        foods.append(item("FOOD-"+key, "food", title, "Qualitative ingredient example for a reviewed plan; no portion or therapeutic prescription.", preg,
            ["E-"+ref, "E-PREG-FOOD-SAFETY"], dict(ingredients=[ingredient], allergens=allergens, nutrient_roles=nutrients,
            dietary_patterns=diets, food_safety=handling, quantity_basis="qualitative_only_no_grams_or_calorie_claim",
            ingredient_detail_required=key in {"GRAINS", "FISH", "NUTS", "FRUIT", "PULSES"},
            additional_review_required=key == "FISH", allergen_basis="ingredient identity; cross-contact and prepared recipes are not established",
            local_example_status="editorial_example_pending_product_review")))
    write_csv("catalogues/food_components.csv", foods)
    movements = []
    for key, title in [("WALK", "Walking in pregnancy"), ("SWIM", "Swimming in pregnancy"), ("LOW-IMPACT", "Low-impact activity in pregnancy")]:
        movements.append(item("MOVE-"+key, "movement", title, "Discuss a suitable activity with the care professional before selecting an option.", preg,
            ["E-PREG-MOVEMENT-OPTIONS", "E-PREG-MOVEMENT-PACE", "E-PREG-MOVEMENT-STOP"],
            dict(intensity="moderate; able to talk", progression="start slowly; progress gradually; breaks and gradual cool-down",
                 stop_rule_ids=["S-BREATHING", "S-CHEST", "S-BLEEDING", "S-FETAL", "S-FLUID", "S-NEURO"],
                 clearance_policy="requires explicit exercise_clearance and confirmed absence of restriction/warning symptom; no calendar-based clearance"),
            required=["exercise_clearance"], excluded=["movement_restriction", "current_warning_symptom"]))
    for key, title in [("PP-WALK", "Gentle walking after birth"), ("PP-STRETCH", "Gentle stretches after birth")]:
        movements.append(item("MOVE-"+key, "movement", title, "An option only after a straightforward birth and when the user feels ready.", pp,
            ["E-PP-GENTLE-MOVEMENT"], dict(intensity="gentle", progression="individual readiness; no fixed daily duration or universal return date",
            stop_rule_ids=["S-BREATHING", "S-CHEST", "S-BLEEDING", "S-NEURO"], clearance_policy="unknown delivery/restriction means needs_information"),
            required=["uncomplicated_delivery", "feels_ready_for_gentle_activity"],
            excluded=["complicated_delivery_or_caesarean", "movement_restriction", "current_warning_symptom"]))
    movements.append(item("MOVE-PP-CONSULT", "movement", "Activity question after a complicated birth", "Ask before starting strenuous activity.", pp,
        ["E-PP-MOVEMENT-QUESTION"], dict(intensity="no exercise prescribed", progression="care-professional decision",
        stop_rule_ids=["S-BREATHING", "S-CHEST", "S-BLEEDING"], clearance_policy="question only, never clearance"),
        required=["complicated_delivery_or_caesarean"]))
    write_csv("catalogues/movement_components.csv", movements)
    wellbeing = []
    actions = [
        ("PREG-FEELINGS", "Name how you feel", preg, "PREG-TALK", ["If you want, name how you feel today.", "Choose whether to share it with someone supportive."], "care_professional"),
        ("PREG-ENJOY", "Choose a small enjoyable activity", preg, "PREG-ENJOY", ["Choose something you usually enjoy.", "Make room for it if you wish; you can stop or skip it."], "care_professional"),
        ("PP-REST", "Make room for rest", pp, "PP-MIND-REST", ["Choose one task that can wait.", "Use that space to rest if you want."], "care_professional_or_tele_manas"),
        ("PP-SUPPORT", "Ask for specific practical help", pp, "PP-PRACTICAL-HELP", ["Choose a person you trust.", "Tell them one practical task you would like help with."], "care_professional_or_tele_manas"),
        ("PP-TALK", "Share a feeling", pp, "PP-MIND-TALK", ["Choose someone supportive.", "Share as much or as little about your feelings as you want."], "care_professional_or_tele_manas"),
        ("PP-KINDNESS", "Let one task wait", pp, "PP-ASK-HELP", ["You do not have to do every task at once.", "Choose something to postpone or ask someone trusted to help with."], "care_professional_or_tele_manas"),
    ]
    for key, title, timing, ref, steps, handoff in actions:
        wellbeing.append(item("WELL-"+key, "wellbeing", title, "Optional editorial micro-action based on the linked general support guidance; not therapy or diagnosis.",
            timing, ["E-"+ref], dict(steps=steps, consent_prompt="Would you like to try this, or skip it?", persistent_route=handoff,
            urgent_route="S-SELF-HARM or other urgent safety rule; do not start an exercise or wait for a check-in",
            duration="user_chosen", consent_withdrawable=True, effect_claim="none"), required=["consents_to_wellbeing_activity"], excluded=["current_warning_symptom"]))
    write_csv("catalogues/wellbeing_exercises.csv", wellbeing)
    followup = [item("ANC-REGISTER", "followup", "First-trimester registration", "Discuss registration with the local care team.", scope("pregnancy",4,12),
        ["E-IN-REGISTRATION"], dict(timing_unit="pregnancy_week", start=4, end=12, schedule_context="NHM CHO first-trimester registration; no invented exact appointment",
        dedupe_key="episode:ANC-REGISTER", source_currency="February 2022 programme needs local currency review"), required=["pregnancy_confirmed"]),
        item("ANC-CHECKS", "followup", "Antenatal checks and tests", "Record the appointments agreed with your care professional.", preg,
        ["E-IN-ANC-VISITS", "E-IN-ANC-TESTS"], dict(timing_unit="pregnancy_week", start=4, end=42, schedule_context="NHM CHO programme: four checks; not a maximum or a complete current clinical schedule",
        dedupe_key="episode:ANC-CHECKS", source_currency="requires current Indian clinical reconciliation before scheduling"))]
    followup.append(item("ANC-PMSMA", "followup", "Monthly PMSMA antenatal service", "Programme information; confirm local facility arrangements.", scope("pregnancy",13,42),
        ["E-IN-PMSMA"], dict(timing_unit="calendar_day_of_month", start=9, end=9, schedule_context="second/third trimester at designated government facilities; supplementary to routine ANC",
        dedupe_key="episode:PMSMA:year-month", source_currency="PIB 8 June 2026")))
    for day in (1, 3, 7, 14, 21, 28, 42):
        week = max(1, (day+6)//7)
        followup.append(item(f"PNC-DAY-{day}", "followup", f"Postnatal programme contact: day {day}",
            "Check locally agreed arrangements; warning symptoms must not wait for this contact.", scope("postpartum",week,week),
            ["E-IN-PNC-WEEKS"], dict(timing_unit="postpartum_day", start=day, end=day,
            schedule_context="home-birth additional contact" if day==1 else "facility- and home-birth programme contact",
            dedupe_key=f"episode:PNC-DAY-{day}", source_currency="NHM CHO February 2022; review local availability and current policy"),
            required=["home_birth"] if day==1 else []))
    write_csv("catalogues/followup_milestones.csv", followup)
    # Preserve the teammate's engagement proposals as explicitly unverified data.
    # No clinical measurements are manufactured to make this table look complete.
    review=(ROOT/"docs/STAGE-0-CONTENT-DATASET-REVIEW-AND-CORRECTION-PLAN.md").read_text(encoding="utf-8")
    comparison=[]
    for line in review.splitlines():
        match=re.match(r"\| `P(\d{2})` \| \*\*(.*?)\*\* \| (.*?) \| (.*?) \| (.*?) \|",line)
        if not match:continue
        week=int(match[1]); pid=f"P{week:02d}"
        comparison.append(item("SIZE-"+pid,"comparison",pid+" illustrative comparison", match[2],scope("pregnancy",week,week),[],
            dict(profile_id=pid,measurement_basis=match[5],measurement_value=None,object_dimension_mm=None,
            illustrative_only=True,image_key=re.search(r"`([^`]+)`",match[4])[1],image_path=None,image_alt=match[2],
            hide_reason="Intentional non-size state" if week in {1,2,42} else "Teammate editorial proposal: measurement series, object dimensions and clinical review not verified",
            proposed_planning_basis=match[3],proposal_source="Team-supplied correction plan section 12.1; not a medical authority",
            clinical_review_status="pending",editorial_review_status="pending",artwork_status="deferred_by_review_section_12_4")))
    write_csv("catalogues/fetal_size_comparisons.csv",comparison)
    rules = [
        ("BREATHING", [r"\b(can't|cannot|can not|not able to) breathe\b",r"\b(shortness of breath|short of breath|breathing (issue|problem|difficulty)|difficulty breathing|trouble breathing)\b"]),
        ("CHEST", [r"\b(chest pain|chest pressure|tight chest|chest feels tight)\b"]),
        ("BLEEDING", [r"\b(heavy bleeding|bleeding heavily|soaking.*pad|large blood clots)\b"]),
        ("FETAL", [r"\b(baby.*(not moving|stopped moving|moving less)|reduced fetal movement|less fetal movement)\b"]),
        ("SELF-HARM", [r"\b(kill myself|hurt myself|harm myself|hurt my baby|harm my baby|end my life|suicid)\w*\b"]),
        ("NEURO", [r"\b(fainted|fainting|passed out|blurred vision|blurry vision|worst headache|severe headache)\b"]),
        ("FEVER", [r"\b(fever|temperature).*(38|39|40|100\.4|101|102|103)\b"]),
        ("PAIN", [r"\b(severe|unbearable) (abdominal|belly|stomach) pain\b"]),
        ("FLUID", [r"\b(fluid leaking|leaking fluid|water broke)\b"]),
        ("VOMITING", [r"\b(can't|cannot|unable to) keep (water|fluids|anything) down\b"]),
    ]
    spec=dict(version="1.0.0",status="draft",jurisdiction="IN",language="en",
        urgent_message="This may need urgent medical attention. Seek medical help now. In India, call 112 for an emergency or go to the nearest emergency department. Tell the team you are pregnant or recently gave birth. Do not wait for Compass or a scheduled appointment.",
        clarify_message="More context is needed before routine advice. If symptoms are severe, worsening or you feel unsafe, seek urgent medical help. Compass cannot diagnose or confirm that a symptom is safe.",
        no_match_message="No configured warning pattern matched. This does not rule out a medical problem.",
        help_routes={"emergency":{"number":"112","jurisdiction":"IN","source_url":"https://112.gov.in/","verified_on":"2026-09-10"},
                     "mental_health_support":{"number":"14416","jurisdiction":"IN","source_url":"https://mohfw.gov.in/sites/default/files/Rapid%20Assessment%20report%20on%20TeleMANAS.pdf",
                     "verified_on":"2026-09-10","use":"Tele-MANAS support; do not substitute it for emergency care"}},
        rules=[dict(rule_id="S-"+key,route="urgent",patterns=patterns,evidence_span_ids=["E-IN-PREG-WARNINGS", "E-IN-PP-WARNINGS"],
                    reference_locators=[dict(source_id="CDC-WARNINGS", locator="Urgent maternal warning signs: " + key, use="link_only_clinical_review_reference")],
                    rationale="Draft product escalation examples: NHM supports general escalation, while the specific symptom interpretation requires review against the linked CDC/AIM section. No copied CDC list, diagnosis, or validated triage claim.") for key,patterns in rules],
        limitations=["Not a clinically validated triage system. Runtime refuses draft rules.",
                     "English patterns only; paraphrases, spelling variations, other languages and unknown symptoms are not comprehensively covered.",
                     "Negation, historical and third-person mentions can over-trigger; no automatic de-escalation is attempted.",
                     "No-match is not medical clearance. These are contract fixtures, not evidence of population-level sensitivity."])
    spec["rules"].append(dict(rule_id="S-CLARIFY",route="clarify",patterns=[r"\b(pain|bleeding|dizzy|fever|sad|anxious|overwhelmed|nausea|vomiting|medicine|dose|symptom)\b"],
                              evidence_span_ids=["E-PREG-MEDICINE-BOUNDARY","E-PP-PERSISTENT-CONCERN"],
                              rationale="Product policy: ambiguous symptoms, medication changes and emotional concerns require clarification or professional handoff; no diagnosis."))
    write_json("safety/rule_spec.yaml",spec)
    print(f"Catalogues: {len(foods)} food, {len(movements)} movement, {len(wellbeing)} wellbeing, {len(followup)} follow-up, {len(comparison)} hidden comparison proposals.")


if __name__ == "__main__":main()
