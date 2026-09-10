"""Reproducible, explicitly authored Stage 0 correction dataset (no model calls).

Selected text is from the cited official pages or licensed NHM PDFs. This command
creates drafts only; it cannot invent human approvals.
"""

import csv
from pathlib import Path
import json
from hashlib import sha256
from typing import get_args

from app.schemas.content import ConditionKey
from app.schemas.foundation import Plan
from scripts.validate_content import load_bundle

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
TODAY = "2026-09-10"


def write_json(path, value):
    (DATA / path).parent.mkdir(parents=True, exist_ok=True)
    (DATA / path).write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode())


def write_jsonl(path, values):
    (DATA / path).write_bytes(("\n".join(json.dumps(x, ensure_ascii=False) for x in values) + "\n").encode())


def write_csv(path, rows):
    with (DATA / path).open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) or k == "review"
                             else "" if v is None else v for k, v in row.items()})


def scope(stage, start=None, end=None, unit="week"):
    return dict(stage=stage, unit="none" if start is None else unit, start=start, end=end)


def ensure_drafts_only():
    """Curating drafts must never erase another person's actual review."""
    bundle = load_bundle(DATA)
    if any(r.review or r.status in {"reviewed", "published", "approved_for_capstone"}
           for group in (bundle.sources, bundle.evidence, bundle.fragments, bundle.profiles) for r in group):
        raise ValueError("Reviewed data exists; curate a new version instead of overwriting reviews.")
    ledger = DATA / "reviews/approvals.json"
    if ledger.exists() and json.loads(ledger.read_text(encoding="utf-8"))["reviews"]:
        raise ValueError("Human review ledger exists; create a separately reviewed revision.")


def main():
    ensure_drafts_only()
    bundle = load_bundle(DATA).model_dump(mode="json")
    sources = {s["source_id"]: s for s in bundle["sources"]}
    evidence = {e["evidence_id"]: e for e in bundle["evidence"]}
    fragments = {f["fragment_id"]: f for f in bundle["fragments"]}
    profiles = {p["profile_id"]: p for p in bundle["profiles"]}
    changed = set()
    preg = scope("pregnancy", 4, 42)
    pp = scope("postpartum", 1, 12)
    days = scope("postpartum", 0, 7, "day")

    def add(key, sid, locator, text, timing, domain, wording=None, required=(), excluded=(), page=None, note=""):
        source = sources[sid]
        adoption = None
        if source["jurisdiction"] != ["IN"]:
            adoption = dict(source_jurisdiction=source["jurisdiction"], target_jurisdiction=["IN"],
                            category="general_education", rationale="Proposed education only for the stated scope. "
                            "Original foreign authority retained; no imported service schedule, drug dose or emergency number. "
                            "Full evidence, conditions and local wording require named review.", review=None)
        eid, fid = "E-" + key, "F-" + key
        evidence[eid] = dict(evidence_id=eid, source_id=sid, source_version=source["version_or_last_update"],
                             source_checksum=source["content_checksum"], locator=locator, page=page, text=text,
                             text_checksum=sha256(text.encode()).hexdigest(), applies_to=timing, jurisdiction=["IN"],
                             status="draft", review=None, applicability_note=note or "The stated source context supports this bounded educational scope.",
                             localisation=adoption)
        fragments[fid] = dict(fragment_id=fid, domain=domain, text=wording or text, applies_to=timing,
                             jurisdiction=["IN"], evidence_span_ids=[eid], status="draft", review=None,
                             conditions_required=list(required), conditions_excluded=list(excluded),
                             presentation="quotation" if not wording or wording == text else "paraphrase")
        changed.add(sid)
        return eid, fid

    # Expand older keyword anchors into complete supporting units.
    replacements = {
        "E-DATING": "Pregnancy lasts about 40 weeks, counting from the first day of your last normal period.",
        "E-FIRST-TRIMESTER": "First trimester (week 1-week 12). Other changes may include: Mood swings. Just as each woman is different, so is each pregnancy.",
        "E-PP-SUPPORT-CONTEXT": "Here are some ways to begin feeling better or getting more rest, in addition to talking to a health care professional:",
        "E-PP-SUPPORT-TALK": "Here are some ways to begin feeling better or getting more rest, in addition to talking to a health care professional: Talk about your feelings with your partner, supportive family members, and friends.",
        "E-PP-FERTILITY": "You can get pregnant again just 3 weeks after the birth of your baby, even if you're breastfeeding and your periods have not started again yet.",
        "E-PP-PRACTICAL-HELP": "It's best to be clear about the kind of help you want, rather than going along with what's offered and feeling resentful.",
    }
    for eid, text in replacements.items():
        span = evidence[eid]
        span.update(text=text, text_checksum=sha256(text.encode()).hexdigest())
        span["locator"] = span["locator"].split(" / expanded supporting unit")[0] + " / expanded supporting unit"
        changed.add(span["source_id"])
    fragments["F-DATING"]["text"] = "Pregnancy weeks are counted from the first day of the last normal menstrual period."
    # Both fertility fragments are distinct wording supported by the same full
    # source sentence. Keep one evidence unit and link both fragments to it.
    evidence.pop("E-PP-FERTILITY-FEEDING", None)
    fragments["F-PP-FERTILITY-FEEDING"]["evidence_span_ids"] = ["E-PP-FERTILITY"]
    # Empty duration and population-specific headings remain explicit in the locator.

    # Preserve complete clinical conditions, not a short anchor plus an unsourced note.
    visits = ("Ensuring PNC home visits for delivered women (Institutional Delivery) on 3rd, 7th,14th, 21st, "
              "28th and 42nd Day (6 Visits) and in case of Home Delivery follow up to be done on 1st, 3rd, "
              "7th, 14th, 21st, 28th and 42nd Day (7 Visits).")
    add("IN-PP-FOLLOWUP", "NHM-CHO", "Page 11 / 3.1 / complete PNC home-visit bullet", visits,
        scope("postpartum", 6, 6), "followup", "The NHM booklet includes a postnatal home visit on day 42 for both facility and home births.",
        page=11, note="Indian programme schedule, not a guarantee of service availability or advice to wait with symptoms. PP06 includes days 36-42.")
    add("PP-MOVEMENT-QUESTION", "NHS-PP-ACTIVE", "When can I start exercising after birth? / complete complicated-delivery paragraph",
        "If you had a more complicated delivery or a caesarean, your recovery time will be longer. Talk to your midwife, health visitor or GP before starting anything strenuous.",
        pp, "movement", "After a complicated delivery or caesarean, ask your care professional before starting strenuous activity.",
        required=["complicated_delivery_or_caesarean"], note="The condition is included in the evidence itself. No automatic week-6 or week-12 clearance.")
    fragments["F-PP-DIET"]["text"] = evidence["E-PP-DIET"]["text"]
    fragments["F-PP-DIET"]["presentation"] = "quotation"

    add("IN-REGISTRATION", "NHM-CHO", "Page 11 / 3.1 / registration bullet",
        "Registration of all the pregnant women in the first trimester of pregnancy.", scope("pregnancy", 4, 12), "followup",
        "The NHM booklet calls for pregnancy registration in the first trimester.", required=["pregnancy_confirmed"], page=11)
    add("IN-ANC-VISITS", "NHM-CHO", "Page 11 / 3.1 / antenatal-check bullet",
        "Ensuring four antenatal care checks in VHSND.", preg, "followup",
        "The NHM CHO booklet describes four antenatal checks in the Village Health Sanitation and Nutrition Day programme.", page=11,
        note="Programme description from February 2022; not a maximum number of visits or a personalised schedule. Currency/local review required.")
    add("IN-ANC-TESTS", "NHM-CHO", "Page 11 / 3.1 / testing bullet",
        "Test all pregnant women for urine (albumin and sugar), haemoglobin, syphilis, HIV and blood grouping.", preg, "followup",
        "The NHM booklet lists urine, haemoglobin, syphilis, HIV and blood-group tests in antenatal care.", page=11,
        note="Organisational discussion of the programme; the app does not order tests or interpret results.")
    if "PIB-PMSMA" not in sources:
        source = dict(sources["NHM-CHO"])
        source.update(source_id="PIB-PMSMA", title="Pradhan Mantri Surakshit Matritva Abhiyaan: A Decade of Inclusive Maternal Healthcare Delivery",
                      publisher="Press Information Bureau, Government of India", canonical_url="https://static.pib.gov.in/WriteReadData/specificdocs/documents/2026/jun/doc202668887301.pdf",
                      version_or_last_update="2026-06-08", publication_date="2026-06-08", publisher_updated_at="2026-06-08",
                      license_or_reuse_note="PIB copyright policy allows free attributed reproduction of original material without prior approval, except third-party content: "
                      "https://www.pib.gov.in/ContentPage.aspx?lang=2&menuid=3604&reg=48 . Only original programme text selected; no pictures. "
                      "No entitlement or local availability guarantee by Nestline.",
                      attribution_text="Source: Press Information Bureau, Government of India, 8 June 2026.", status="candidate", review=None)
        sources["PIB-PMSMA"] = source
    add("IN-PMSMA", "PIB-PMSMA", "Page 2 / programme opening paragraph",
        "Launched on June 9, 2016, PMSMA provides free, comprehensive antenatal care to pregnant women - particularly those in their second and third trimesters - at designated government health facilities on the 9th of every month.",
        scope("pregnancy",13,42), "followup", "PMSMA offers antenatal care on the 9th of each month at designated government facilities during the second and third trimesters.",
        page=2, note="Programme information current in the 8 June 2026 PIB publication. This supplements routine ANC, never replaces a personalised schedule or urgent care.")
    add("IN-FOOD-DAIRY", "NHM-MOTHERHOOD", "Page 9 / dairy bullet",
        "Take milk and dairy products like curd, buttermilk, paneer-these are rich in calcium, proteins and vitamins.", preg, "nutrition",
        "The NHM booklet lists milk, curd, buttermilk and paneer as sources of calcium and protein.", page=9)
    add("IN-FOOD-GRAINS", "NHM-MOTHERHOOD", "Page 9 / cereals and pulses sentence",
        "Cereals, whole grains and pulses are good sources of proteins.", preg, "nutrition", page=9)
    add("IN-FOOD-GREENS", "NHM-MOTHERHOOD", "Page 9 / leafy-vegetables bullet",
        "Green leafy vegetables are a rich source of iron and folic acid.", preg, "nutrition", page=9)
    add("IN-FOOD-ANIMAL", "NHM-MOTHERHOOD", "Page 9 / non-vegetarian sources bullet",
        "For non-vegetarians, meat, egg, chicken or fish are good sources of proteins, vitamins and iron.", preg, "nutrition", page=9)
    add("IN-FOOD-PLANTS", "NHM-MOTHERHOOD", "Page 10 / proteins row",
        "Paneer, milk and other milk products, combined grains, seeds, nuts, egg, meat, poultry, soya beans.", preg, "nutrition",
        "The booklet includes soya beans, grains, seeds and nuts among protein-source examples.", page=10,
        note="Qualitative food-group examples only; no nutrient grams, calorie totals or therapeutic diet inferred.")
    add("PREG-FOOD-SAFETY", "OWH-HEALTH", "Food safety / handling instruction and bullets",
        "Clean, handle, cook, and chill food properly to prevent foodborne illness, including listeria and toxoplasmosis. "
        "Wash hands with soap after touching soil or raw meat. Keep raw meats, poultry, and seafood from touching other foods or surfaces. "
        "Cook meat completely. Wash produce before eating. Wash cooking utensils with hot, soapy water.", preg, "nutrition",
        "Wash produce and utensils, cook meat completely, and keep raw meat separate from other food.")
    add("PREG-FOOD-AVOID", "OWH-HEALTH", "Food safety / Do not eat / milk and sprouts bullets",
        "Unpasteurized milk or juices. Raw sprouts of any kind (including alfalfa, clover, radish, and mung bean).", preg, "nutrition",
        "The source advises avoiding unpasteurised milk or juice and raw sprouts during pregnancy.",
        note="Two selected complete list items under Do not eat; list heading retained in locator. No fish or herb recommendations adopted.")
    add("PREG-MEDICINE-BOUNDARY", "OWH-HEALTH", "Using medicines / start-stop paragraph",
        "Always speak with your doctor before you start or stop any medicine. Not using medicine that you need may be more harmful to you and your baby than using the medicine.",
        preg, "preparation", "Speak with your doctor before starting or stopping a medicine.")
    add("PREG-MOVEMENT-OPTIONS", "OWH-HEALTH", "Getting started and Best activity for moms-to-be",
        "For most healthy moms-to-be who do not have any pregnancy-related problems, exercise is a safe and valuable habit. "
        "Even so, talk to your doctor or midwife before exercising during pregnancy. "
        "Low-impact activities at a moderate level of effort are comfortable and enjoyable for many pregnant women. "
        "Walking, swimming, dancing, cycling, and low-impact aerobics are some examples.", preg, "movement",
        "After discussing suitability with your care professional, walking or swimming may be options for moderate, low-impact activity.",
        required=["exercise_clearance"], excluded=["movement_restriction", "current_warning_symptom"])
    add("PREG-MOVEMENT-PACE", "OWH-HEALTH", "Tips for safe and healthy physical activity / first three bullets",
        "When you exercise, start slowly, progress gradually, and cool down slowly. You should be able to talk while exercising. "
        "If not, you may be overdoing it. Take frequent breaks.", preg, "movement",
        "Start slowly, build up gradually, and take breaks. You should be able to talk during activity.",
        required=["exercise_clearance"], excluded=["movement_restriction", "current_warning_symptom"])
    add("PREG-MOVEMENT-STOP", "OWH-HEALTH", "Tips / Stop exercising and call your doctor / complete list",
        "Stop exercising and call your doctor as soon as possible if you have any of the following: Dizziness. Headache. "
        "Chest pain. Calf pain or swelling. Abdominal pain. Blurred vision. Fluid leaking from the vagina. Vaginal bleeding. "
        "Less fetal movement. Contractions.", preg, "symptoms",
        "Stop activity and seek medical advice if warning symptoms such as chest pain, bleeding, fluid leakage or reduced fetal movement occur.")
    add("PP-GENTLE-MOVEMENT", "NHS-PP-ACTIVE", "When can I start exercising after birth? / straightforward-birth paragraph",
        "If you had a straightforward birth, you can start gentle exercise as soon as you feel up to it. "
        "This could include walking, gentle stretches and pelvic floor exercises.", pp, "movement",
        "After a straightforward birth, gentle walking or stretches may be options when you feel ready.",
        required=["uncomplicated_delivery", "feels_ready_for_gentle_activity"],
        excluded=["movement_restriction", "current_warning_symptom", "complicated_delivery_or_caesarean"])
    add("PP-PERSISTENT-CONCERN", "NHS-PP-ACTIVE", "Look after your mental health / concern paragraph",
        "If you're worried about how you're feeling, feel like you're struggling to cope, or think you may be depressed, "
        "it's important that you talk to your midwife, health visitor or GP. Effective help is available.", pp, "wellbeing",
        "If you are worried about how you feel or are struggling to cope, talk to a care professional.",
        note="Not a diagnosis or a recommendation to wait. Acute warning signs use the separate urgent route.")
    add("PP-ASK-HELP", "NHS-PP-ACTIVE", "Look after your mental health / help and rest bullets",
        "making time to rest. not trying to \"do it all\". accepting help with caring for your baby from friends, family or your partner.",
        pp, "wellbeing", "You can make room for rest and accept practical help from people you trust.")
    add("IN-PP-DAY0", "NHM-MOTHERHOOD", "Page 16 / day-of-delivery follow-up bullet",
        "You and your baby should be seen by a health worker on the day of delivery, and on 3rd day, 7th day and 6 weeks after delivery.",
        scope("postpartum", 0, 0, "day"), "followup", "The booklet calls for a health-worker check for mother and baby on the day of birth.", page=16)
    add("IN-PP-DAY-REST", "NHM-MOTHERHOOD", "Page 16 / postpartum rest bullet / day scope",
        "Take adequate rest.", days, "preparation", "Make space for rest during recovery.", page=16)
    add("IN-PP-DAY-HELP", "NHM-MOTHERHOOD", "Page 16 / immediate-help bullet",
        "Take immediate medical help if any complication occurs in yourself or your baby.", days, "symptoms", page=16)
    add("IN-PNC-DAYS", "NHM-CHO", "Page 11 / 3.1 / complete PNC home-visit bullet / day scope",
        visits, days, "followup", "The NHM programme lists different early home-visit schedules for facility and home births.", page=11)
    add("IN-PNC-WEEKS", "NHM-CHO", "Page 11 / 3.1 / complete PNC home-visit bullet / week scope",
        visits, scope("postpartum", 1, 6), "followup",
        "The NHM programme lists postnatal home visits through day 42, with an additional day-1 visit after a home birth.", page=11)
    # Individual day cards reference the whole conditional schedule.
    for day in (1, 3, 7):
        required = ["home_birth"] if day == 1 else []
        add(f"IN-PNC-DAY{day}", "NHM-CHO", f"Page 11 / complete PNC schedule / selected day {day}", visits,
            scope("postpartum", day, day, "day"), "followup",
            f"The NHM programme includes a day-{day} home visit " + ("after a home birth." if day == 1 else "after either a facility or home birth."),
            required=required, page=11)

    # CDC's page credits an AIM/ACOG list. Federal hosting is not sufficient
    # permission to copy third-party text. Retain the link, remove copied drafts.
    sid = "CDC-WARNINGS"
    source = sources[sid]
    source.update(reuse_status="unverified", allowed_use=[], snapshot_path="", content_checksum=None,
                  selected_sections=[], status="candidate", review=None, paraphrase_permission="unverified",
                  commercial_permission="unverified", revalidation_status="needs_currency_review",
                  version_or_last_update="page-2024-05-15;link-checked-2026-09-10",
                  publisher_updated_at="2024-05-15", retrieved_at="2026-09-10", next_review_at="2026-12-09",
                  license_or_reuse_note="Link-only reference. CDC credits AIM for this list; CDC policy excludes some third-party works. "
                  "AIM/ACOG permits whole unmodified noncommercial documents, not automatically this extracted/adapted list. "
                  "No copied CDC/AIM warning text or embedding is admitted. Review permissions before any ingestion. "
                  "https://www.cdc.gov/other/agencymaterials.html ; https://saferbirth.org/aim-resources/aim-cornerstones/urgent-maternal-warning-signs/",
                  attribution_text="Linked reference: CDC HEAR HER / AIM; no endorsement.")
    evidence = {k:v for k,v in evidence.items() if v["source_id"] != sid}
    fragments = {k:v for k,v in fragments.items() if not k.startswith("F-WARN-")}
    add("IN-PREG-WARNINGS", "NHM-MOTHERHOOD", "Page 14 / pregnancy danger signals and immediate-help instruction",
        "If any complications occur- seek help immediately to preserve your health and life. DANGER SIGNALS DURING PREGNANCY. "
        "Generalised weakness, easy fatigability and breathlessness. Severe pain in abdomen. Bleeding per vaginum. "
        "Excessive swelling in legs. Fever. Convulsions.", preg, "symptoms",
        "The booklet calls for immediate help for pregnancy danger signs, including breathlessness, bleeding, severe abdominal pain, fever or convulsions.", page=14,
        note="Selected danger-sign panel; source layout read. No diagnosis or wait-until-next-visit inference. Current clinical review required.")
    add("IN-PP-WARNINGS", "NHM-MOTHERHOOD", "Page 16 / immediate-help instruction and Contact FRU list",
        "Take immediate medical help if any complication occurs in yourself or your baby. Contact F R U. "
        "Excessive vaginal bleeding. Inability to control defecation/urine. Foul smelling vaginal discharge. "
        "Difficulty in breathing. Blurred vision and fits. Fever. Fainting.", pp, "symptoms",
        "The booklet identifies post-birth problems requiring referral, including excessive bleeding, difficulty breathing, blurred vision or fits, fever and fainting.", page=16,
        note="Complete FRU list retained; reference to referral services needs local clinical review. Not a diagnosis.")

    # P01 is deliberately a timing state, not a pregnancy routine.
    for p in profiles.values():
        if p["content_priority"] == "coverage_shell":
            p["publication_blockers"] = ["Outside the agreed representative content release; no reviewed weekly content."]
        if p["profile_id"] == "P42":
            p["publication_blockers"] = ["Exact India-local wording and clinical review required. Generic week-42 wellness content is withheld."]
        if p["content_priority"] != "representative" and p["content_priority"] != "day_overlay":
            continue
        p["version"] = "1.2.0"
        p["status"] = "draft"
        p["review"] = None
        p["publication_blockers"] = ["Exact content, licence, clinical, India-localisation and product reviews pending."]
        pid = p["profile_id"]
        slots = p["card_slots"]
        if pid == "P01":
            slots = {k: [] for k in slots}
            slots["what_may_change"] = ["F-DATING"]
            p["hero"]["title"] = "Week 1: understanding pregnancy timing"
        elif pid.startswith("PPD"):
            day = int(pid[3:])
            slots = {k: [] for k in slots}
            slots["preparation"] = ["F-IN-PP-DAY-REST"]
            slots["symptom_education"] = ["F-IN-PP-DAY-HELP"]
            if day == 0:
                slots["ask_a_professional"] = ["F-IN-PP-DAY0"]
            elif day in {1, 3, 7}:
                slots["ask_a_professional"] = [f"F-IN-PNC-DAY{day}"]
            p["hero"] = dict(title=f"Day {day} after birth: recovery and follow-up", development_evidence_ids=["E-IN-PP-DAY-REST"], visual_asset_id=None)
        elif pid.startswith("PP"):
            slots["movement_focus"] = ["F-PP-GENTLE-MOVEMENT", "F-PP-MOVEMENT-QUESTION"]
            slots["wellbeing_focus"] = ["F-PP-MIND-REST", "F-PP-MIND-TALK", "F-PP-ASK-HELP"]
            slots["ask_a_professional"] = ["F-PP-PERSISTENT-CONCERN"] + (["F-IN-PP-FOLLOWUP"] if pid == "PP06" else [])
        elif pid != "PC00":
            slots["nutrition_focus"] += ["F-IN-FOOD-GRAINS", "F-IN-FOOD-GREENS"]
            slots["movement_focus"] = ["F-PREG-MOVEMENT-OPTIONS", "F-PREG-MOVEMENT-PACE"]
            slots["avoid"] = ["F-PREG-FOOD-AVOID"]
            slots["symptom_education"] = ["F-PREG-MOVEMENT-STOP"]
            slots["preparation"] = ["F-IN-BIRTH-PLAN", "F-PREG-MEDICINE-BOUNDARY"]
            slots["ask_a_professional"] = ["F-MOVEMENT-CONSULT", "F-IN-ANC-TESTS"]
            if pid in {"P24", "P36"}:
                slots["ask_a_professional"].append("F-IN-PMSMA")
            if pid in {"P09", "P10"}:
                slots["ask_a_professional"].append("F-IN-REGISTRATION")
        p["card_slots"] = {k: list(dict.fromkeys(v)) for k, v in slots.items()}
        p["guidance_fragment_ids"] = sorted({ref for refs in slots.values() for ref in refs})
        p["source_evidence_ids"] = sorted(set(p["hero"]["development_evidence_ids"]) |
                                           {ref for fid in p["guidance_fragment_ids"] for ref in fragments[fid]["evidence_span_ids"]})
        p["slot_notes"] = {slot: ("Pregnancy timing only: do not imply conception or prescribe a pregnancy routine." if pid == "P01"
                                 else "No separate sourced card for this slot. Do not generate advice to fill it; use the applicable named cards.")
                           for slot, refs in slots.items() if not refs}
    # Retiming the reusable preparation claim also prevents accidental future P01 reuse.
    for key in ("E-IN-BIRTH-PLAN",):
        evidence[key]["applies_to"] = preg
    fragments["F-IN-BIRTH-PLAN"]["applies_to"] = preg

    for sid in changed:
        source = sources[sid]
        spans = [e for e in evidence.values() if e["source_id"] == sid]
        version = "selected-2026-09-10-correction-v2"
        sections = {e["locator"]: e["text"] for e in spans}
        snapshot = dict(source_id=sid, canonical_url=source["canonical_url"], version=version, captured_at=TODAY,
                        capture_method="Selected complete supporting passages; whitespace and list punctuation normalised. "
                        "Source conditions preserved. Official source context read; not a full-page archive.",
                        sections=[dict(locator=k, text=v) for k, v in sections.items()])
        path = f"guidelines/snapshots/{sid}-2026-09-10-v2.json"
        write_json(path, snapshot)
        checksum = sha256((DATA / path).read_bytes()).hexdigest()
        source.update(snapshot_path=path, content_checksum=checksum, version_or_last_update=version,
                      selected_sections=list(sections), journey_stages=sorted({e["applies_to"]["stage"] for e in spans}),
                      topics=sorted({f["domain"] for f in fragments.values() if any(evidence[r]["source_id"] == sid for r in f["evidence_span_ids"])}))
        for span in spans:
            span.update(source_version=version, source_checksum=checksum)
    nhs_dates = {"NHS-PREG-MIND": "2026-03-11", "NHS-PP-BODY": "2024-04-25",
                 "NHS-PP-DIET": "2026-05-15", "NHS-PP-ACTIVE": "2026-04-20", "NHS-PP-SUPPORT": "2026-05-20"}
    for source in sources.values():
        if source["source_id"] in nhs_dates:
            source["publisher_updated_at"] = nhs_dates[source["source_id"]]
        if source["snapshot_path"]:
            source.update(retrieved_at=TODAY, next_review_at="2026-12-09",
                          revalidation_status="needs_currency_review" if source["source_id"] in {"BHC-WEEKS", "NHM-MOTHERHOOD", "NHM-CHO"} else "current_capture",
                          paraphrase_permission="restricted" if source["delivery_mode"] == "fixed_quote" else "permitted",
                          commercial_permission="restricted" if source["source_id"] in {"BHC-WEEKS", "NHM-CHO"} else "unverified")
            if source["source_id"] == "BHC-WEEKS":
                source["publisher_updated_at"] = "2012-02-28"
            elif source["source_id"].startswith("OWH-"):
                source["publisher_updated_at"] = "2023-10-17" if source["source_id"] == "OWH-WELLBEING" else "2025-09-26"
            elif source["source_id"] == "CDC-WARNINGS":
                source["publisher_updated_at"] = "2024-05-15"
    # YAML files use the JSON subset of YAML 1.2, avoiding an unnecessary parser dependency.
    definitions = {
        "breastfeeding": "The user explicitly reports currently breastfeeding.",
        "early_home_recovery": "The user confirms being in the early days of recovery at home.",
        "professional_care_for_postpartum_depression": "The user confirms professional care for postpartum depression; no diagnosis inferred.",
        "complicated_delivery_or_caesarean": "Confirmed complicated delivery or caesarean; no inference from a missing delivery detail.",
        "uncomplicated_delivery": "The user or confirmed record explicitly describes an uncomplicated birth.",
        "feels_ready_for_gentle_activity": "The user explicitly feels ready for gentle activity; this is not clinical clearance.",
        "exercise_clearance": "A confirmed care-professional instruction establishes activity suitability in this context.",
        "movement_restriction": "A confirmed active movement restriction exists; absence requires confirmation too.",
        "current_warning_symptom": "A current concerning symptom is reported or the reviewed safety route flags one.",
        "home_birth": "Confirmed delivery at home.", "facility_birth": "Confirmed delivery in a health facility.",
        "pregnancy_confirmed": "The user explicitly confirms pregnancy; a late period alone does not establish it.",
        "consents_to_wellbeing_activity": "The user chooses an optional wellbeing activity and may stop at any time.",
        "persistent_emotional_concern": "The user reports persistent concern or difficulty coping; no diagnosis inferred.",
        "trusted_support_available": "The user identifies someone they trust and want to involve; no partner assumed.",
    }
    write_json("guidelines/condition_registry.yaml", dict(version="1.0.0", unknown_policy="needs_information",
               conditions=[dict(key=k, definition=definitions[k], values=["confirmed_present", "confirmed_absent", "unknown"],
                                provenance=["user_confirmation", "confirmed_document_fact"], owner="product_and_clinical_review")
                           for k in get_args(ConditionKey)]))
    write_csv("guidelines/source_registry.csv", list(sources.values()))
    write_jsonl("guidelines/section_manifest.jsonl", evidence.values())
    write_jsonl("guidelines/guidance_fragments.jsonl", fragments.values())
    write_jsonl("weekly/weekly_content_manifest.jsonl", profiles.values())
    write_csv("weekly/coverage_matrix.csv", [dict(profile_id=p["profile_id"], status=p["status"], content_priority=p["content_priority"],
              blocker="; ".join(p["publication_blockers"])) for p in profiles.values()])
    if not (DATA / "reviews/approvals.json").exists():
        write_json("reviews/approvals.json", dict(schema_version="1.0.0", reviews=[]))
    write_json("plans/plan_schema.json", Plan.model_json_schema())
    print(f"Corrected {len(evidence)} spans, {len(fragments)} fragments and all eight day overlays; no human reviews invented.")


if __name__ == "__main__":
    main()
