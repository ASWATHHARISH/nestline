# Nestline Stage 0 content and dataset review

**Prepared:** 10 September 2026
**Branch reviewed:** `feat/stage-0-data-foundation` at `a39417c3840fb7d7c63a3ecb2a59cb3bc2d043ec`
**Compared with:** `main` at `ecc2315b17d295868cf48a33bde32ca0c0f15695`
**Purpose:** A plain-language correction plan that can be sent directly to the teammate responsible for Stage 0.

> This is a product/data review, not a medical sign-off. Nothing should be published to users until an appropriately qualified clinical reviewer and an India-localisation reviewer approve the exact wording and evidence.

## 1. What Stage 0 was supposed to do — in very simple words

Stage 0 was supposed to build the **trusted content shelf** that the later Nestline agents will use. It was not supposed to build the agents themselves.

By the end of Stage 0 we needed:

1. A separate address for every pregnancy week (`P01`–`P42`), postpartum week (`PP01`–`PP12`), the possible-pregnancy state (`PC00`), and the first eight postpartum day overlays (`PPD0`–`PPD7`).
2. A source register that says where every fact came from, whether it can legally be stored/embedded/displayed, which country it applies to, and when it was reviewed.
3. A small but complete, deeply reviewed demonstration set: `PC00`, `P01`, `P09`, `P10`, `P24`, `P36`, `PP01`, `PP06`, and `PP12`.
4. Reusable, evidence-linked content for all important lanes: pregnancy development, nutrition/diet, movement, mental wellbeing/self-love, antenatal preparation, postnatal recovery/follow-up, and symptom education boundaries.
5. No made-up medical content. If a week or topic was not reviewed, it should remain hidden and clearly marked as unfinished.
6. Named content, licence, clinical, and India-localisation reviews before anything becomes `published`.
7. Data contracts that later agents and evals can use, including evidence IDs, conditions, citations, versions, and publication blockers.

The architecture deliberately did **not** require 54 fully unique, clinically reviewed weekly articles in four days. It required all shells plus a carefully reviewed representative vertical slice. However, the representative slice still needed enough content breadth to prove the later nutrition, movement, wellbeing, follow-up, and safety flows.

## 2. Plain-English meaning of the IDs

| ID | Meaning | Example |
|---|---|---|
| `PC00` | Possible pregnancy, before a pregnancy week is confirmed | A user has a late period and is considering a test |
| `P01` | Pregnancy week 1 | The first week in clinical pregnancy dating; conception usually has not happened yet |
| `P42` | Pregnancy week 42 | A representable state, but it must stay unpublished until local wording and follow-up guidance are reviewed |
| `PP01` | Postpartum week 1 | Days after birth grouped into the first postpartum week |
| `PP12` | Postpartum week 12 | The twelfth week after birth |
| `PPD0` | Postpartum day 0 | The day of birth; a day-specific overlay on top of `PP01` |
| `PPD7` | Postpartum day 7 | Seven days after birth; another day-specific overlay on top of `PP01` |
| `PPD0`–`PPD7` | Early-postpartum day overlays | These add day-specific follow-up/safety information; they do not replace `PP01` |

`P4-2` is not the canonical format. If somebody says “P four-two,” the stored ID should be `P42`. Similarly, use `PP01`, not `PP1-2`. `PPD` means **postpartum day**; `PPD7` means postpartum day 7. Do not use `PPD` by itself to mean postpartum depression in IDs, because it would be ambiguous. Write `postpartum_depression` or a separate explicit code for that condition.

## 3. Executive verdict

**Do not describe this branch as “Stage 0 complete,” and do not merge it on that basis yet.**

The branch contains useful, largely well-tested engineering work and should not be thrown away. It creates the 63 records, contracts, checks, evidence snapshots, and a controlled source registry. But the actual content is still a thin draft:

- 63 records exist, but only 9 representative profiles contain content.
- 46 weekly profiles are intentionally empty shells.
- All 8 early-postpartum day overlays are completely empty.
- The repository contains 29 source rows, but only 13 sources currently have permitted snapshots.
- Those 13 sources produce only 28 evidence spans and 28 guidance fragments.
- 11 of the 13 permitted sources feed the representative profiles; 2 are staged but not assembled into them.
- All 9 representative profiles are still `draft`, have no named review object, and carry publication blockers.
- The execution plan itself still has the Stage 0 review/publish item unchecked.

### Merge recommendation

The branch can be merged only after one of these two honest outcomes:

1. **Preferred:** finish the Priority 0 and Priority 1 corrections in this document, complete named reviews, and publish the agreed representative profiles; or
2. **Foundation-only merge:** explicitly rename/reframe the work as an incomplete Stage 0 foundation, keep the Stage 0 completion box open, record all gaps as owned issues with dates, and prevent every draft/empty profile from appearing in the UI or RAG.

## 4. What was decided versus what was delivered

| Area | What we decided | What the branch delivered | Verdict |
|---|---|---|---|
| Journey coverage | Addresses for `PC00`, `P01`–`P42`, `PP01`–`PP12`, `PPD0`–`PPD7` | All 63 rows exist | **Good** |
| Deep demo profiles | Nine representative profiles, fully sourced/reviewed before publication | Nine profiles contain draft cards, but none is reviewed or published | **Partly done** |
| Pregnancy week-wise content | All weeks addressable; representative weeks should prove the design | Only P01, P09, P10, P24, and P36 are populated; 37 pregnancy weeks are shells | **Correct for shells, too shallow for a content-complete claim** |
| Postpartum week-wise content | All 12 weeks addressable; PP01, PP06, PP12 deeply reviewed | Only those three contain draft content; nine are shells | **Partly done** |
| Early postpartum | Day overlays `PPD0`–`PPD7` | Eight empty records with no title, evidence, cards, or blocker | **Missed** |
| Nutrition/diet | Trusted maternal nutrition evidence plus structured food components and constraints | A few general fragments about food variety, washing produce, and breastfeeding diet | **Far too thin** |
| Movement | Evidence for pregnancy and postpartum movement, conditions, stop signs, and safe progression | Mostly “rest,” “do not overexert,” and “ask a professional” | **Far too thin** |
| Mental wellbeing/self-love | Supportive, non-diagnostic exercises plus routine/persistent/urgent boundaries | Talk to someone, rest, do something enjoyable, ask for practical help | **Useful start, incomplete** |
| Antenatal care | India-local ANC timing/content supported by current official documents | Testing, generic birth planning, food/rest boundaries; no proper ANC schedule/evidence set | **Missed** |
| Postnatal care | India-local PNC timing, recovery, feeding, wellbeing, movement, and follow-up | A day-42 anchor, general rest, fertility, diet, and support | **Incomplete** |
| Fun weekly layer | Optional baby-size comparison with evidence and clear “illustrative” labelling | No fruit/seed/object comparison dataset | **Missed** |
| Safety foundation | Deterministic rule specification and must-pass examples | Source candidate recorded, but no `rule_spec.yaml` | **Missing foundation dependency** |
| Evals foundation | Stable inputs/expected outputs for contract tests | Engineering tests exist; no `evals/phase_1_contract.jsonl` | **Missing** |
| Clinical correctness | Every user-facing claim entailed by exact evidence and reviewed | Automated schema checks pass, but no clinical/semantic sign-off | **Not proven** |

## 5. What “24 candidate sources” and “5 excluded sources” actually mean

These numbers do **not** mean that 24 sources were ingested.

The register has 29 rows:

- **24 candidates:** 13 are currently marked reuse-permitted and have selected snapshots; 11 are still unverified and contribute no evidence.
- **5 excluded:** these were considered but deliberately not copied into the dataset because their terms restrict reuse or do not clearly permit RAG/dataset use.
- **13 permitted replacements:** these are controlled alternatives, not random additions. They are five Office on Women’s Health pages, five standard NHS pages, two NHM documents, and one Better Health Channel page.

The 13 replacements are **real replacements for legal access to a small demo slice**, but they do **not** replace the missing breadth. They do not give complete week-by-week development, ANC, PNC, nutrition, movement, wellbeing, safety, and fun-comparison coverage.

### The 13 permitted sources and whether they are actually used

| Source group | Count | Current use | Assessment |
|---|---:|---|---|
| U.S. Office on Women’s Health | 5 | Stages, test, and healthy/safe pages feed profiles. Recovery and postpartum-depression pages are staged but not assembled into the nine profiles. | Legally useful, but U.S. context needs India-localisation review |
| Standard NHS pages | 5 | Pregnancy mental health; postpartum body, diet, activity, and practical support | Good supplementary content; do not import UK care roles/schedules without localisation |
| NHM India documents | 2 | Indian food/rest, testing support, birth planning, and day-42 follow-up | Important local anchors; some excerpts are too narrow and documents need currency review |
| Better Health Channel | 1 | Exact week 9 and week 10 development | Only two short fixed quotes permitted; old 2012 review date and no embedding/paraphrase |

## 6. What was done well

Do not remove these parts while correcting the branch:

- The branch preserves all 63 journey addresses and distinguishes weekly profiles from day overlays.
- Unreviewed content is kept in `draft`; the release gate correctly fails with zero published profiles.
- Source permission status, allowed actions, jurisdiction, checksums, snapshots, locators, and publication blockers are recorded.
- Restricted sources were not silently copied.
- Stable guidance is reused across applicable week ranges rather than pretending every statement is uniquely weekly.
- Foreign content is explicitly marked for India-localisation review.
- The test suite passes 47 tests and the authoring/review-readiness checks pass.
- `P42` exists but is intentionally withheld pending reviewed local wording.
- Previous implementation issues were corrected: draft-validation loopholes, checksums not tied to actual bytes, mutable test fixtures, and treating a missing condition as if it were false.

These are strong engineering foundations. The problem is that the content and review layer is not yet sufficiently complete.

## 7. Concrete mistakes and corrections

| Priority | Finding | Why it matters | Required correction | Acceptance test |
|---|---|---|---|---|
| P0 | All `PPD0`–`PPD7` records are empty | Early postpartum is a high-risk, rapidly changing period; an empty overlay cannot prove the design | Populate the agreed representative day overlays from reviewed India/WHO PNC sources, or formally remove/defer them through an architecture decision. At minimum prove day 0, day 1, day 3, and day 7 with explicit overlay rules. | Each retained PPD record has a title, evidence IDs, applicable cards, safe unavailable states, review, and tests |
| P0 | None of the nine representative profiles has named review approval | Automated tests cannot certify medical wording, local applicability, or permissions | Add source/licence, content, clinical, India-localisation, and product reviewers with dates, disposition, corrections, and version | Release gate passes only when all required reviews exist and corrections are resolved |
| P0 | Evidence for `E-IN-PP-FOLLOWUP` is only the text “42nd Day” | The fragment adds ASHA/ANM and “arrangements,” which the stored quote does not by itself support | Store the complete relevant NHM sentence/bullet and locator; regenerate its text checksum and review the paraphrase | Entailment check confirms every part of the fragment is supported by the evidence span |
| P0 | `E-PP-MOVEMENT-QUESTION` omits the preceding source sentence that contains the complicated-delivery/caesarean condition | The fragment has a condition that the stored evidence text does not contain | Expand the selected evidence to both relevant sentences, preserve the UK source, and complete India-localisation review | Evidence span visibly contains the condition used by the fragment |
| P0 | `F-PP-DIET` adds “personal dietary restrictions agreed with your care team” without linked support | This is sensible but still an unsupported user-facing claim | Remove that clause, add a separately evidenced restriction fragment, or make it a deterministic product rule with its own policy source | Claim-to-evidence evaluator finds no unsupported clause |
| P0 | Safety rule specification is absent | Later symptom and medication agents cannot be safely tested from prose alone | Add `data/safety/rule_spec.yaml`, fixed urgent wording, priority rules, India help routes, and must-pass cases under qualified review | Red-flag cases deterministically bypass normal generation; no model can override them |
| P0 | Stage 0 has no semantic/clinical entailment gate | Schema checks can pass while wording overstates evidence | Add a claim-to-span review/eval that checks entailment, timing, jurisdiction, conditions, and citation correctness | Nine profiles achieve agreed pass threshold with zero critical unsupported claims |
| P1 | P01 includes birth-planning guidance across week 1 | Clinical week 1 normally precedes conception, so the timing is confusing | Remove birth-planning from P01 or narrow the fragment to a reviewed later applicability range | P01 contains only dating/possible-pregnancy-appropriate content |
| P1 | Conditional fragments can hide an entire profile when the user condition is unknown | A breastfeeding or caesarean condition should suppress one card, not the whole week | Resolve eligibility per card and return `shown`, `not_applicable`, or `needs_information` with a reason | PP01/PP06/PP12 still show eligible cards when one condition is unknown |
| P1 | Conditions are free-form strings | Typos and mismatched wording will silently break eligibility | Create a versioned condition registry/enum with definitions, allowed values, provenance, and tests | Schema rejects unknown conditions and maps every conditional fragment to a registered key |
| P1 | BHC week 9/10 material is old and quote-only | It cannot be embedded or safely rewritten, and its currency is unconfirmed | Have a reviewer accept fixed-quote display or replace it with a newer reusable development source | No BHC text enters embeddings; display respects quote limit and citation; currency disposition recorded |
| P1 | Source freshness is manual | A hash proves local bytes are unchanged; it does not prove the publisher has not updated/retracted the page | Add `retrieved_at`, publisher update date, next-review date, canonical URL, and scheduled/manual revalidation status | Validator flags overdue sources and changed snapshots |
| P1 | Movement data is too thin | The later Movement Agent needs activity type, intensity, progression, contraindications, stop signs, and clearance state | Build a structured movement catalogue from approved sources and explicitly separate general activity from personalised clearance | Movement test set covers uncomplicated pregnancy, postpartum progression, caesarean/complication, symptom handback, and unknown clearance |
| P1 | Nutrition data is too thin and `food_components.csv` is absent | The Nutrition Agent cannot safely compose a plan from three generic sentences | Build reviewed food components, nutrients, allergens, restrictions, dietary patterns, Indian food examples, food-safety flags, and evidence links | Plans never violate hard restrictions and every recommendation maps to a component plus evidence |
| P1 | Wellbeing/self-love data is too thin | Supportive micro-actions require boundaries and escalation; “self-love” must not become diagnosis or therapy | Add reviewed, low-risk exercises; support-network actions; consent; routine/persistent/urgent routes; and local help options | Tests show normal support, persistent concern handoff, acute-risk bypass, and no diagnosis |
| P1 | ANC and PNC timing sets are incomplete | Follow-up and weekly briefing cannot give reliable organisational prompts | Add current India-local ANC/PNC milestones and WHO evidence where compatible, with exact jurisdiction/timing fields | Timeline tests cover each supported milestone and suppress unverified schedules |
| P1 | No structured fun-comparison dataset | The requested “seed/lime/papaya” layer cannot be generated safely from memory | Create an editorial comparison table from reviewed size measurements; mark comparisons illustrative and non-diagnostic | Every comparison has measured range, object dimensions, source, review, and disclaimer |
| P1 | Synthetic document corpus is not built | Record and Medication Record agents need safe fictional inputs and expected facts | Add fictional PDFs/images and exact expected extractions, including conflicts and missing fields | Extraction eval reports field accuracy, provenance accuracy, abstention, and conflict recall |
| P1 | `evals/phase_1_contract.jsonl` is absent | The UI/evals owner has no stable input/output contract to develop against in parallel | Create frozen cases for journey resolution, content eligibility, citations, safety, and empty states | Same dataset runs locally and in LangSmith with versioned results |
| P2 | Two permitted sources are staged but unused | Stored content can be mistaken for active coverage | Mark them `staged_unassembled`, or assemble reviewed fragments into relevant profiles | Registry/report clearly distinguishes registered, snapshotted, assembled, reviewed, and published |
| P2 | There is no editorial workflow for fruit/object choices | Copying a commercial app’s fruit sequence creates copyright and accuracy risk | Let editors create original mappings from measurements, then clinically/product review the labels | No wording/image is copied from BabyCenter, What to Expect, or similar sites |

## 8. Dataset needed for every later agent

There is no separate “diet agent” in the updated architecture; diet belongs to the **Nutrition Agent**. There is no separate “self-love agent”; self-love/supportive exercises belong to the **Well-being Agent**. The updated architecture also does not have a separate Video Agent; videos should be a reviewed catalogue used by Movement/Nutrition/Well-being if the team keeps that feature.

| Agent/control | Data needed before implementation | Typical input | Required output contract |
|---|---|---|---|
| Journey Orchestrator | Intent taxonomy, agent registry, journey-state schema, out-of-scope examples, minimum-agent routing cases | Safe user request + journey state + permissions | Typed route plan, chosen agents, reason, evidence lanes |
| Record Agent | Fictional documents, OCR text, expected extracted facts, source coordinates, contradictions, missing-field cases | Uploaded fictional record or record question | Exact sourced summary or proposed facts; abstain where unsupported |
| Medication Record Agent | Fictional medication records, normalized names, dose/frequency fields, conflicts, dates, “documented as” wording | Authorized medication record + question | Record-only timeline/questions; never prescribe or change treatment |
| Symptom Navigation Agent | Deterministic safety rules, reviewed symptom education, red-flag cases, clarify cases, local handoff wording | Safety result + user-reported symptom/context | Bounded next step or handback; no diagnosis |
| Nutrition Agent | Nutrition evidence shelf, `food_components.csv`, nutrient/allergen tags, restrictions, preferences, Indian food examples, food safety | Journey week + dietary constraints/preferences + evidence | Cited answer or plan contribution that satisfies every hard constraint |
| Movement Agent | Movement shelf, activity catalogue, intensity/progression, conditions, restrictions, stop signs, reviewed videos | Journey week + symptoms/restrictions + clearance state | Cited movement option or question for professional; never infer clearance |
| Well-being Agent | Reviewed self-care exercises, consent prompts, support-network actions, escalation boundaries, local support directory | Stage + check-in + prior preferences | Supportive action/follow-up; acute risk returns to Safety Gate; no diagnosis |
| Follow-up Agent | ANC/PNC milestone catalogue, confirmed appointments, task taxonomy, provenance, dedupe keys | Timeline + confirmed facts + open questions | Prioritised organisational tasks with confirmed-source dependency |
| Plan Composer Agent | Typed outputs from specialists, plan schema, conflicts, constraints, citation requirements, save eligibility | Validated specialist contributions | Editable weekly plan + unresolved conflicts + citations; no unsafe save |
| Human review workflow | Review roles, checklists, dispositions, corrections, version links, consent and escalation status | Proposed content/fact/packet | Approved/rejected/changes-requested with named reviewer and audit trail |
| Safety Gate (control) | Versioned deterministic rules and must-pass inputs | Raw message + allowed context | `urgent`, `clarify`, or `non_urgent`, with fixed next action |
| Evidence Planner (control) | Intent-to-evidence-lane mapping and allowed-source policy | Typed intent | Required and allowed evidence lanes |
| Citation Verifier (control) | Claims, evidence spans, applicability, jurisdiction, version | Draft response | Supported/unsupported claims and corrected citation map |
| Constraint Validator (control) | Hard allergy/restriction/condition registry | Proposed plan | Pass/fail plus exact violating item |
| State Committer (control) | Mutation schema, authority, confirmation, idempotency key, conflict/version rules | User-confirmed proposed change | One auditable state write or a safe rejection |

## 9. Source strategy: use more than WHO and NHM, but use sources correctly

### Source tiers

| Tier | Meaning | What we may do |
|---|---|---|
| A — ingestible candidate | Authority, exact page/document, permission/licence, date, and content have been checked | Store selected excerpts, embed/display only as allowed, attribute, review, and version |
| B — trusted reference/link-only | Reputable clinical/government/nonprofit information, but dataset reuse permission is absent or unclear | Human researchers may read and link to it; do not copy into RAG or generate close paraphrases without permission |
| C — UX/editorial inspiration only | Commercial pregnancy apps/sites that demonstrate week-wise presentation or fun comparisons | Learn the interaction pattern; do not treat as clinical truth and do not copy text, tables, sequences, or artwork |

### Tier A: strongest candidates to verify and ingest

The following links are intentionally broader than WHO/NHM. Each still needs a row-level licence decision and named content/localisation review.

| Domain | Source | Why it helps | Use note |
|---|---|---|---|
| India ANC/PNC | [NHM maternal-health guidelines index](https://www.nhm.gov.in/index1.php?lang=1&level=3&lid=377&sublinkid=839) | Gateway to current Indian maternal-health documents | Download the exact PDF, not just the index; record its date and permission |
| India pregnancy/postpartum | [NHM CHO maternal-health booklet](https://www.nhm.gov.in/New_Update-2022-23/MH/GUIDELINES-%20MH/CHO_Booklet_%20Maternal_Health-English.pdf) | Indian ANC/PNC roles and follow-up anchors | Free educational reproduction conditions are stated in the document; preserve attribution |
| India general guidance | [NHM My Safe Motherhood booklet](https://www.nhm.gov.in/images/pdf/programmes/maternal-health/guidelines/my_safe_motherhood_booklet_english.pdf) | Local food, rest, preparation, and postpartum context | Undated/older material needs currency review; exclude obsolete schedules/doses |
| India nutrition context | [UNICEF India women’s nutrition](https://www.unicef.org/india/what-we-do/womens-nutrition) | India-specific maternal nutrition priorities and service context | Verify UNICEF terms for the exact page/document before ingestion |
| Maternal nutrition | [UNICEF programme guidance on maternal nutrition](https://www.unicef.org/documents/programme-guidance-maternal-nutrition) | Structured maternal nutrition programme guidance | Check document licence; localise to India rather than importing globally |
| ANC | [WHO recommendations on antenatal care](https://www.who.int/publications/i/item/9789241549912/) | Comprehensive evidence-based ANC framework | Document page identifies CC BY-NC-SA 3.0 IGO; suitable only under its conditions, including non-commercial use |
| PNC | [WHO recommendations on maternal and newborn care for a positive postnatal experience](https://www.who.int/publications/i/item/9789240045989) | Detailed postnatal evidence and timing | Same document-specific licence check and India-localisation required |
| Maternal timing | [WHO maternal interventions across the life course](https://www.who.int/teams/maternal-newborn-child-adolescent-health-and-ageing/handbooks/programme-manager-s-handbook-mncah/recommendations-on-interventions-along-life-course/maternal) | Concise ANC/PNC timing cross-check | Do not replace Indian service schedules without local review |
| Movement | [WHO guidelines on physical activity and sedentary behaviour](https://www.who.int/publications/b/55518) | Includes pregnancy and postpartum populations | CC BY-NC-SA 3.0 IGO; turn recommendations into reviewed structured fields, not free text alone |
| Perinatal wellbeing | [WHO guide for integration of perinatal mental health](https://www.who.int/publications/i/item/9789240057142/) | Service integration and mental-health boundaries | Use for non-diagnostic pathways and handoff design; verify exact licensed sections |
| General pregnancy | [Office on Women’s Health: stages of pregnancy](https://womenshealth.gov/pregnancy/youre-pregnant-now-what/stages-pregnancy) | Reusable U.S. government text for selected development/context | Public-domain statement applies to original government text, not third-party images/content; localise |
| Pregnancy health | [Office on Women’s Health: staying healthy and safe](https://womenshealth.gov/pregnancy/youre-pregnant-now-what/staying-healthy-and-safe) | Nutrition, food safety, and movement boundaries | Use selected excerpts only and preserve U.S. jurisdiction |
| Postpartum recovery | [Office on Women’s Health: recovering from birth](https://womenshealth.gov/pregnancy/childbirth-and-beyond/recovering-birth) | Recovery and professional follow-up questions | Currently staged; decide explicitly where it is assembled |
| Postpartum wellbeing | [Office on Women’s Health: postpartum depression](https://womenshealth.gov/mental-health/mental-health-conditions/postpartum-depression) | Supportive context and escalation boundaries | Must not let the Well-being Agent diagnose; currently staged but unassembled |
| Postpartum movement | [HSE Ireland: exercise plan 12 weeks after pregnancy](https://www2.hse.ie/babies-children/parenting-advice/health-mental-wellbeing/exercise-12-weeks-after-pregnancy/) | Clear progression and “too much too soon” signs | Government page, but confirm exact reuse terms and localise before ingestion |
| Movement reference | [HSE physical-activity guidelines for pregnant and postpartum women](https://www.hse.ie/eng/about/who/healthwellbeing/our-priority-programmes/heal/every-move-counts/hse-physical-activity-guidelines-for-pregnant-and-postpartum-women.pdf) | Structured pregnancy/postpartum movement guidance | Check PDF licence and preserve Irish jurisdiction |

### Tier B: excellent human references, but link-only unless permission is obtained

These are useful precisely because we should not depend only on WHO/NHM. They improve coverage review and editorial quality, but the team must not automatically copy or embed them.

| Domain | Reference | How to use it safely |
|---|---|---|
| Week-wise development | [March of Dimes: Pregnancy week by week](https://www.marchofdimes.org/pregnancy-week-week) | Coverage checklist and reviewer reference; request permission before dataset copying |
| Week-wise development | [Cleveland Clinic: Fetal development](https://my.clevelandclinic.org/health/articles/7247-fetal-development-stages-of-growth) | Medically reviewed cross-check; link/reference only unless terms permit more |
| Week-wise pregnancy | [Mayo Clinic: Pregnancy week by week](https://www.mayoclinic.org/healthy-lifestyle/pregnancy-week-by-week/in-depth/healthy-pregnancy/hlv-20049471) | Editorial/clinical cross-check; copyrighted reference, not an ingestion shortcut |
| India week-wise UX | [BabyCenter India: fetal development](https://www.babycenter.in/pregnancy/fetal-development) | India-oriented vocabulary and coverage inspiration only; do not ingest text/artwork |
| India size measurements | [BabyCenter India: fetal growth chart](https://www.babycenter.in/a1004000/fetal-growth-chart-length-and-weight-week-by-week) | Use to identify questions for reviewers, not as the sole source or a copied table |
| Movement | [ACOG: Exercise During Pregnancy](https://www.acog.org/womens-health/faqs/exercise-during-pregnancy) | Current specialist reference for categories, precautions, and stop signs; link-only unless permission |
| Nutrition | [ACOG: Healthy Eating During Pregnancy](https://www.acog.org/womens-health/faqs/healthy-eating-during-pregnancy) | Reviewer checklist for food groups/nutrients; do not ingest without permission |
| Postpartum | [ACOG: My Postpartum Care Checklist](https://www.acog.org/womens-health/health-tools/my-postpartum-care-checklist) | Product/reviewer checklist; respect copyright |
| Mental wellbeing | [ACOG: Anxiety and Pregnancy](https://www.acog.org/womens-health/faqs/anxiety-and-pregnancy) | Boundary and support-path review; not a substitute for India emergency pathways |
| Postpartum body/wellbeing | [Tommy’s: Your body after the birth](https://www.tommys.org/pregnancy-information/after-birth/your-body-after-birth) | Plain-language coverage cross-check; link-only unless terms allow reuse |
| Postpartum planning | [Tommy’s: Planning ahead after birth](https://www.tommys.org/pregnancy-information/im-pregnant/mental-wellbeing/planning-ahead-after-birth) | Support network and wellbeing planning inspiration; review/licence first |
| Postpartum recovery | [March of Dimes: Your body after baby—the first 6 weeks](https://www.marchofdimes.org/find-support/topics/postpartum/your-body-after-baby-first-6-weeks) | Recovery coverage checklist; do not import U.S. service language |
| India professional reference | [FOGSI/ICOG: Care for the healthy pregnant woman](https://icogonline.org/wp-content/uploads/pdf/gcpr/Care_for_the_Healthy_Pregnant_Women.pdf) | India clinical reviewer reference; confirm currency and reuse rights before ingestion |
| India nutrition professional reference | [FOGSI: Nutrition in women across ages](https://fogsi.org/wp-content/uploads/fogsi-focus/fogsi-focus-nutrition-in-women-across-ages.pdf) | Indian nutrition coverage review; permission/licence required for dataset use |
| Open research | [AIIMS-DST/FOGSI postpartum weight-management guideline](https://pmc.ncbi.nlm.nih.gov/articles/PMC9008111/) | The PMC article can be assessed under its displayed licence; use only relevant, reviewed claims and do not turn it into personal treatment advice |

### Tier C: UX inspiration only

Commercial products such as BabyCenter, What to Expect, Ovia, Flo, and similar apps may be reviewed to understand week cards, progress views, reminders, and fun comparisons. They must **not** become the clinical source of truth, and their wording, fruit sequence, illustrations, or data tables must not be copied.

## 10. The five excluded sources and the correct workaround

| Excluded source | Link | Why excluded | Correct workaround |
|---|---|---|---|
| MedlinePlus/A.D.A.M. fetal development | [Open page](https://medlineplus.gov/ency/article/002398.htm) | A.D.A.M./Ebix terms restrict AI retrieval and dataset reuse | Keep link-only; use a licensed government/open source or obtain written permission |
| NHS Best Start week-by-week index | [Open index](https://www.nhs.uk/best-start-in-life/pregnancy/week-by-week-guide-to-pregnancy/) | Best Start content is excluded from the standard NHS reuse route | Do not download/feed it; use standard NHS OGL pages plus a separately licensed weekly-development source |
| Pregnancy, Birth and Baby week-by-week | [Open index](https://www.pregnancybirthbaby.org.au/pregnancy/pregnancy-stages/pregnancy-week-by-week) | Healthdirect terms do not give the required dataset/RAG reuse permission | Reference coverage only; request permission or replace with licensed material |
| NHS Best Start week 41 | [Open week 41](https://www.nhs.uk/best-start-in-life/pregnancy/week-by-week-guide-to-pregnancy/3rd-trimester/week-41/) | Same Best Start licence exclusion | Keep P41/P42 unpublished until locally reviewed content is sourced elsewhere |
| ICMR-NIN Dietary Guidelines for Indians 2024 | [Open PDF](https://nin.res.in/dietaryguidelines/pdfjs/locale/DGI_2024.pdf) | The PDF notice restricts electronic storage/reproduction for making a product without permission | Read as a human reference; request written permission or use compatible NHM/UNICEF/other licensed material. Do not feed this PDF into embeddings now |

Important: a download link is not permission to ingest. If the terms prohibit storage or AI reuse, downloading the PDF and manually uploading it to RAG would still be the wrong workaround.

## 11. How to add a source correctly

For every proposed page or PDF:

1. Open the canonical publisher page, not a search-result mirror.
2. Record publisher, title, canonical URL, publication/update date, jurisdiction, audience, and topic.
3. Open the exact copyright/licence/terms page. Record whether `store`, `embed`, `display`, `paraphrase`, and `commercial use` are allowed separately.
4. If permission is unclear, mark it `unverified` and keep it out of snapshots, embeddings, and user-visible content.
5. Download only when allowed. Preserve the original bytes, retrieval time, checksum, and document version.
6. Select the smallest complete passage that supports the intended claim. Include conditions and exceptions in the span.
7. Write a guidance fragment that says no more than the evidence says.
8. Add stage/week/day, jurisdiction, conditions, and localisation notes.
9. Run engineering validation plus claim-to-evidence/semantic checks.
10. Obtain named licence/content, clinical, India-localisation, and product review.
11. Resolve every correction, bump the version, and only then mark the fragment/profile `published`.

If a source is blocked or restricted, use this order of workarounds:

1. Find the publisher’s official landing page and alternate official download.
2. Find a compatible licensed source covering the same claim.
3. Ask the rights holder for written permission.
4. Keep a link-only human reference.
5. Narrow the feature or leave the profile unpublished.

Never ask Grok or another model to manufacture the missing medical claim.

## 12. Building the fun “baby is the size of…” layer safely

This is a good engagement feature, but it is an **editorial comparison, not a medical measurement**. The table below is an original Nestline draft and does not copy another pregnancy app's fruit sequence or wording.

### 12.1 Ready-to-review week-by-week draft

The early-week length is planned as crown-to-rump length (CRL). Around week 20 the display changes to approximate head-to-heel length; later cards use rough overall bulk because a long object is no longer a natural comparison. This change of basis must be stored, not hidden.

| ID | Suggested website line | Approximate planning basis | Picture/icon key | Comparison type |
|---|---|---:|---|---|
| `P01` | **The pregnancy clock has started—your body is preparing. There is no embryo to size yet.** | Gestational dating starts from the last menstrual period | `calendar-spark` 📅✨ | Special state; no size claim |
| `P02` | **A new cycle is unfolding. There is still no embryo to compare this week.** | Ovulation/conception timing varies | `tiny-spark` ✨ | Special state; no size claim |
| `P03` | **If fertilisation has happened, this tiny beginning is closer to a speck of fine sand than a seed.** | Microscopic cell cluster; timing varies | `sand-speck` • | Length; conditional |
| `P04` | **Your tiny beginning is about the size of a poppy seed.** | About 1–2 mm | `poppy-seed` 🌱 | CRL/editorial scale |
| `P05` | **Your tiny embryo is about the size of a sesame seed.** | About 2–4 mm | `sesame-seed` 🌾 | CRL/editorial scale |
| `P06` | **Your tiny embryo is about the size of a lentil.** | About 4–6 mm | `lentil` 🫘 | CRL/editorial scale |
| `P07` | **Your growing embryo is about the size of a blueberry.** | About 7–10 mm | `blueberry` 🫐 | CRL/editorial scale |
| `P08` | **Your growing embryo is about the size of a pumpkin seed.** | About 14–16 mm | `pumpkin-seed` 🌱 | CRL/editorial scale |
| `P09` | **Your baby is about the size of a rajma bean.** | About 22–24 mm | `rajma-bean` 🫘 | CRL/editorial scale |
| `P10` | **Your baby is about the size of a cherry.** | About 30–35 mm | `cherry` 🍒 | CRL/editorial scale |
| `P11` | **Your baby is about the size of a strawberry.** | About 40–45 mm | `strawberry` 🍓 | CRL/editorial scale |
| `P12` | **Your baby is about the size of a small lime.** | About 50–60 mm | `lime` 🍋‍🟩 | CRL/editorial scale |
| `P13` | **Your baby is about the size of a lemon.** | About 65–75 mm | `lemon` 🍋 | CRL/editorial scale |
| `P14` | **Your baby is about the size of a guava.** | About 80–90 mm CRL | `guava` | CRL/editorial scale |
| `P15` | **Your baby is about the size of a sweet lime (mosambi).** | About 95–105 mm CRL | `mosambi` 🍊 | CRL/editorial scale |
| `P16` | **Your baby is about the size of an avocado.** | About 110–120 mm CRL | `avocado` 🥑 | CRL/editorial scale |
| `P17` | **Your baby is about the size of a pomegranate.** | About 125–135 mm CRL | `pomegranate` | CRL/editorial scale |
| `P18` | **Your baby is about the size of a bell pepper (shimla mirch).** | About 135–145 mm CRL | `bell-pepper` 🫑 | CRL/editorial scale |
| `P19` | **Your baby is about the size of a mango.** | About 145–155 mm CRL | `mango` 🥭 | CRL/editorial scale |
| `P20` | **From head to heel, your baby is about as long as a banana.** | About 24–26 cm | `banana` 🍌 | Head-to-heel length |
| `P21` | **From head to heel, your baby is about as long as a large carrot.** | About 26–27 cm | `carrot` 🥕 | Head-to-heel length |
| `P22` | **From head to heel, your baby is about as long as an ear of sweet corn.** | About 27–28 cm | `sweet-corn` 🌽 | Head-to-heel length |
| `P23` | **From head to heel, your baby is about as long as a small papaya.** | About 28–29 cm | `small-papaya` | Head-to-heel length |
| `P24` | **From head to heel, your baby is about as long as a drumstick (moringa) pod.** | About 29–31 cm | `moringa-pod` | Head-to-heel length |
| `P25` | **From head to heel, your baby is about as long as a small bottle gourd (lauki).** | About 33–35 cm | `small-lauki` | Head-to-heel length |
| `P26` | **From head to heel, your baby is about as long as a ridge gourd (turai).** | About 35–36 cm | `ridge-gourd` | Head-to-heel length |
| `P27` | **Your baby now has roughly the overall bulk of a cauliflower.** | Roughly 0.8–0.9 kg | `cauliflower` 🥦 | Approximate bulk |
| `P28` | **Your baby now has roughly the overall bulk of a large brinjal.** | Roughly 0.9–1.1 kg | `large-brinjal` 🍆 | Approximate bulk |
| `P29` | **Your baby now has roughly the overall bulk of a butternut squash.** | Roughly 1.1–1.3 kg | `butternut-squash` | Approximate bulk |
| `P30` | **Your baby now has roughly the overall bulk of a cabbage.** | Roughly 1.2–1.5 kg | `cabbage` 🥬 | Approximate bulk |
| `P31` | **Your baby now has roughly the overall bulk of a coconut with its husk.** | Roughly 1.4–1.7 kg | `husked-coconut` 🥥 | Approximate bulk |
| `P32` | **Your baby now has roughly the overall bulk of a small ash gourd (petha).** | Roughly 1.6–1.9 kg | `small-ash-gourd` | Approximate bulk |
| `P33` | **Your baby now has roughly the overall bulk of a pineapple.** | Roughly 1.8–2.1 kg | `pineapple` 🍍 | Approximate bulk |
| `P34` | **Your baby now has roughly the overall bulk of a muskmelon (kharbuja).** | Roughly 2.0–2.3 kg | `muskmelon` 🍈 | Approximate bulk |
| `P35` | **Your baby now has roughly the overall bulk of a large honeydew melon.** | Roughly 2.2–2.5 kg | `honeydew` 🍈 | Approximate bulk |
| `P36` | **Your baby now has roughly the overall bulk of a ripe papaya.** | Roughly 2.4–2.8 kg | `papaya` | Approximate bulk |
| `P37` | **Your baby now has roughly the overall bulk of a small pumpkin.** | Roughly 2.6–3.0 kg | `small-pumpkin` 🎃 | Approximate bulk |
| `P38` | **Your baby now has roughly the overall bulk of a medium pumpkin.** | Roughly 2.8–3.2 kg | `medium-pumpkin` 🎃 | Approximate bulk |
| `P39` | **Your baby now has roughly the overall bulk of a small watermelon.** | Roughly 3.0–3.4 kg | `small-watermelon` 🍉 | Approximate bulk |
| `P40` | **Your baby now has roughly the overall bulk of a full-size watermelon.** | Roughly 3.1–3.6 kg; healthy term size varies widely | `watermelon` 🍉 | Approximate bulk |
| `P41` | **Still growing at their own pace, your baby is around the bulk of a large watermelon.** | Do not imply that every baby continues to gain at the same rate | `large-watermelon` 🍉 | Approximate bulk; review required |
| `P42` | **Do not show a generic size card. Show the reviewed local “contact your maternity professional” message first.** | Representable state; unpublished by architecture decision | `care-team-first` 💬 | Safety/product exception |

The words **about**, **roughly**, and **approximate** are intentional. Fruits and vegetables vary in size, and babies do too. The medical source supports a developmental measurement or range; the food/object match is a separately reviewed editorial choice.

### 12.2 Evidence and reference route for the table

Use these in the source packet; do not cite BabyCenter as the evidence behind the final medical measurement:

1. [Office on Women’s Health: Stages of pregnancy](https://womenshealth.gov/pregnancy/youre-pregnant-now-what/stages-pregnancy) — public-domain U.S. government anchor points at weeks 4–5, 8, 12, 16, 20, 24, 32, 36, and term. Preserve the source jurisdiction and page update date.
2. [ACOG: How your fetus grows during pregnancy](https://www.acog.org/womens-health/faqs/how-your-fetus-grows-during-pregnancy) — qualified human reviewer cross-check for developmental ranges. Treat as reference-only unless reuse permission is confirmed.
3. [INTERGROWTH-21st fetal growth standards](https://intergrowth21.tghn.org/standards-tools/) and its [estimated fetal-weight chart](https://intergrowth21.com/sites/default/files/2023-01/new_grow_efw_ct_en.pdf) — later-pregnancy weight-range cross-check. Confirm the exact chart licence/allowed use before storing or displaying chart data.
4. [Cleveland Clinic fetal development](https://my.clevelandclinic.org/health/articles/7247-fetal-development-stages-of-growth), [March of Dimes week by week](https://www.marchofdimes.org/pregnancy-week-week), and [Mayo Clinic pregnancy week by week](https://www.mayoclinic.org/healthy-lifestyle/pregnancy-week-by-week/in-depth/healthy-pregnancy/hlv-20049471) — human-review cross-checks only unless their permissions are separately approved.
5. [BabyCenter India fetal development](https://www.babycenter.in/pregnancy/fetal-development) — India-oriented UX inspiration only. Do not copy its fruit sequence, wording, measurements table, or artwork.

Before publication, a clinician must replace the planning bands with an approved, versioned measurement series or approve each displayed band. Weeks without reliable measurement support should keep the fun line hidden rather than borrowing a value from model memory.

### 12.3 Data contract

Create `data/catalogues/fetal_size_comparisons.csv` with at least:

```text
profile_id,measurement_basis,min_length_mm,max_length_mm,min_weight_g,max_weight_g,
comparison_object,object_dimension_mm,locale_label,source_evidence_ids,
illustrative_only,review_status,reviewer,version
```

Add these fields so the website can render the card correctly:

```text
display_line,comparison_type,measurement_method,image_key,image_path,image_alt,
source_jurisdiction,clinical_review_status,editorial_review_status,hide_reason
```

Every row should start as `draft`. `P01`, `P02`, and `P42` are intentional non-size states; they must not be filled with a made-up comparison merely to satisfy completeness.

### 12.4 Images are deliberately deferred

This Stage 0 handoff now provides the complete comparison table and stable `image_key` values only. The illustration pack and website card design will be handled as a separate later task.

Rules:

- Use a clinically reviewed measurement range from a legally usable source.
- Choose common India-friendly objects/foods whose approximate dimensions were independently recorded by the team.
- Write original comparison wording and create original artwork.
- Do not copy another app’s fruit sequence or images.
- Avoid misleading precision. The card must say the comparison is approximate and that individual fetal growth varies.
- Do not use the comparison to tell a user that their own baby is normal or abnormal.
- If a defensible comparison is unavailable for a week, show development text without a comparison.

## 13. Missing foundation artifacts to add

The updated architecture names these broader foundation files. Some belong to later implementation stages, but they must be planned now because the UI, agents, and evals depend on their contracts:

```text
data/synthetic/documents/
data/synthetic/expected_extractions/
data/safety/rule_spec.yaml
data/catalogues/food_components.csv
data/plans/plan_schema.json
evals/phase_1_contract.jsonl
```

Add one more project-specific catalogue for the requested engagement layer:

```text
data/catalogues/fetal_size_comparisons.csv
```

Also add:

```text
data/catalogues/movement_components.csv
data/catalogues/wellbeing_exercises.csv
data/catalogues/followup_milestones.csv
data/guidelines/condition_registry.yaml
```

## 14. Ordered correction plan

### Priority 0 — before claiming Stage 0 is done

1. Correct the three evidence/fragment mismatches: day-42 follow-up, postpartum movement condition, and postpartum diet unsupported clause.
2. Remove or retime birth-planning content from P01.
3. Decide and document the retained PPD overlay scope; populate at least the representative early-postpartum days with complete evidence.
4. Create the condition registry and make eligibility per-card rather than per-profile.
5. Complete source/licence, clinical, India-localisation, and product reviews for the nine representative profiles.
6. Add semantic claim-to-evidence checks and publish only the profiles that pass.
7. Keep `P42` unpublished until exact India-local wording is approved.

### Priority 1 — before the specialist agents depend on this data

1. Build the movement, nutrition, wellbeing/self-love, follow-up, and fun-comparison catalogues.
2. Add India ANC and PNC timing evidence, with WHO as a cross-check rather than the only source.
3. Add deterministic safety rules and reviewed urgent/clarify/routine examples.
4. Add fictional record/medication documents and expected extraction truth.
5. Freeze `evals/phase_1_contract.jsonl` so the eval and Streamlit work can continue in parallel.
6. Create an explicit source-state report: registered → permission verified → snapshotted → assembled → reviewed → published.

### Priority 2 — controlled expansion after the demo slice works

1. Expand pregnancy and postpartum weeks in reviewed batches.
2. Use stable fragments across ranges where the evidence is not uniquely weekly.
3. Add original, reviewed visuals/videos with licences and accessibility metadata.
4. Add freshness monitoring and scheduled re-review.

## 15. Stage 0 completion checklist

Stage 0 is complete only when all applicable boxes are checked:

- [ ] All 63 journey records exist and validate.
- [ ] Every empty shell is hidden and has an explicit reason/blocker.
- [ ] Agreed `PPD0`–`PPD7` scope is implemented or formally deferred.
- [ ] Nine representative profiles have complete evidence, citations, conditions, and card-level eligibility.
- [ ] No selected evidence omits a condition that appears in user-facing wording.
- [ ] No guidance fragment contains an unsupported clause.
- [ ] Source licences and allowed actions are verified at the exact page/document level.
- [ ] Foreign content has named India-localisation review.
- [ ] Clinical reviewer has approved exact user-facing wording.
- [ ] Product reviewer has approved empty states and conditional behaviour.
- [ ] `P42` is representable but unpublished unless its local review is complete.
- [ ] Movement, nutrition, wellbeing/self-love, ANC, PNC, and fun-layer gaps are recorded with owners and dates.
- [ ] Deterministic safety rule contract exists before symptom-agent work.
- [ ] Frozen eval contract covers input, expected output, citations, conditions, safety, and abstention.
- [ ] Release gate fails closed for drafts and passes only for fully reviewed profiles.
- [ ] Source freshness/review dates are machine-checkable.

## 16. Teammate handoff message

Copy and send this message with the file:

> Please treat the current branch as a useful Stage 0 engineering foundation, not completed Stage 0 content. Preserve the 63-profile schema, source registry, snapshots, validators, and tests. Before merge-as-complete, fix the P0 evidence mismatches, populate or formally defer the early-postpartum day overlays, implement card-level conditions, and complete named licence/clinical/India/product reviews for the nine representative profiles. Then add the P1 catalogues and frozen eval contracts before the specialist agents depend on the data. Do not ingest any excluded or unclear-licence source merely because it can be downloaded. Record a workaround and leave unsupported content unpublished.

## 17. Tool/model clarification

- **Grok:** remains a candidate language model behind a replaceable provider adapter. It comes **after** the Safety Gate and governed retrieval. It may draft a typed response from approved evidence; it is not the source of medical truth, the retriever, the safety system, or the database writer.
- **Fireworks:** the updated execution plan mentions Fireworks as a possible fallback/provider candidate. It is not automatically selected. Grok and one available fallback should be compared on the same frozen benchmark.
- **“Firebox AI”:** that exact product name is not present in the reviewed architecture or execution plan. If the intended tool is Fireworks, use the policy above. If the team means Firebase, Firecrawl, or another product, record its exact name, purpose, data handling, licence, and admission test before adding it.
- Neither Grok nor Fireworks fixes a missing dataset. Missing evidence must be obtained from an approved source, reviewed, or left unavailable.

---

### Repository evidence used for this review

- `docs/Nestline updated architecture.md`, especially Stage 0, the agent catalogue, deterministic controls, and foundation artifacts.
- `docs/NESTLINE-EXECUTION-PLAN.md`, especially S0 and its still-open named-review/publish gate.
- `data/guidelines/source_registry.csv`
- `data/guidelines/section_manifest.jsonl`
- `data/guidelines/guidance_fragments.jsonl`
- `data/weekly/weekly_content_manifest.jsonl`
- `data/weekly/coverage_matrix.csv`
- `docs/STAGE-0-HANDOFF.md`
- `docs/STAGE-0-CHECK-RESULTS.json`

Automated checks are evidence of engineering consistency, not medical correctness. The final approval must remain human, named, and versioned.
