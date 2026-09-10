# Kajal's evidence-led Stage 1 review workbook

## Read this before making any decision

Do **not** type `YES` merely because a recommendation is written here.

Stage 1 does not contain a finished Streamlit dashboard. It contains draft profile records, draft user-facing cards, source passages and display conditions. Therefore this review has two separate parts:

1. **Now:** review the proposed content, its screen section and its conditional behaviour.
2. **Later:** review the actual rendered Streamlit screens after they exist.

A decision in this workbook is **not** final visual approval and is **not** clinical, licence or India-localisation approval.

## What each decision means

For every item, enter exactly one of these:

- `ACCEPT FOR PRODUCT`: the wording is understandable, the card belongs in that section and the proposed conditions make product sense.
- `CHANGE`: something should remain, but its wording, section, priority or condition must change. Write the exact change.
- `REJECT`: this item should not appear in the product. Write why.
- `NEEDS SPECIALIST REVIEW`: you cannot honestly decide because the question is clinical, legal/licensing or India-localisation-specific.

It is valid to accept the **product placement** and still send the medical claim to a specialist.

## Source files used

All paths below are inside `nestline-stage1-kajal-review`:

- Draft profiles: `data/weekly/weekly_content_manifest.jsonl`
- Draft cards: `data/guidelines/guidance_fragments.jsonl`
- Extracted source passages: `data/guidelines/section_manifest.jsonl`
- Source URLs/licence state: `data/guidelines/source_registry.csv`
- Reviewer tasks: `docs/STAGE-1-REVIEW-QUEUE.md`
- Baby-size proposals: `data/catalogues/fetal_size_comparisons.csv`

---

## Part 1 — Confirm the first review slice

The proposed first slice is:

- `PC00`: pregnancy may be possible, but is not confirmed;
- `P10`: confirmed pregnancy, week 10;
- `PP01`: week 1 after birth.

These three states test the beginning, pregnancy and postpartum portions of the journey. They do not cancel the other profiles.

**Decision:** `ACCEPT FOR PRODUCT` — confirmed by Kajal in Codex chat on 11 September 2026.

**If changing the slice, write the profile IDs and reason:**

____________________________________________________________________________

---

## Part 2 — The 42 baby-size comparisons

### What you are actually deciding

You are **not** being asked to confirm that these measurements are medically correct.

The comparison file currently has:

- 42 editorial proposals;
- no evidence IDs attached to any proposal;
- blank verified `measurement_value` fields;
- blank verified `object_dimension_mm` fields;
- no completed clinical, editorial, licence or product review;
- no finished artwork.

Therefore the only honest decisions available today are:

- `DEFER/HIDE`: do not show any comparison until evidence and object dimensions are verified; or
- `REQUEST VERIFICATION`: name the weeks the team should research, but keep them hidden in the meantime.

Do **not** write `ACCEPT` solely because a fruit or object sounds reasonable.

### What is currently proposed

| Week | Proposed comparison | Unverified planning basis in the file |
|---:|---|---|
| 1 | Pregnancy clock; no embryo to size | Dating starts from last menstrual period |
| 2 | New cycle; no embryo to compare | Ovulation/conception timing varies |
| 3 | Speck of fine sand | Microscopic cell cluster; timing varies |
| 4 | Poppy seed | About 1–2 mm |
| 5 | Sesame seed | About 2–4 mm |
| 6 | Lentil | About 4–6 mm |
| 7 | Blueberry | About 7–10 mm |
| 8 | Pumpkin seed | About 14–16 mm |
| 9 | Rajma bean | About 22–24 mm |
| 10 | Cherry | About 30–35 mm |
| 11 | Strawberry | About 40–45 mm |
| 12 | Small lime | About 50–60 mm |
| 13 | Lemon | About 65–75 mm |
| 14 | Guava | About 80–90 mm CRL |
| 15 | Sweet lime (mosambi) | About 95–105 mm CRL |
| 16 | Avocado | About 110–120 mm CRL |
| 17 | Pomegranate | About 125–135 mm CRL |
| 18 | Bell pepper (shimla mirch) | About 135–145 mm CRL |
| 19 | Mango | About 145–155 mm CRL |
| 20 | Small orange | About 24–26 cm; comparison must still be verified |
| 21 | Orange | About 26–27 cm; comparison must still be verified |
| 22 | Grapefruit | About 27–28 cm; comparison must still be verified |
| 23 | Grapefruit (repeated intentionally) | About 28–29 cm; comparison must still be verified |
| 24 | Small muskmelon (kharbuja) | About 29–31 cm; comparison must still be verified |
| 25 | Small muskmelon (repeated intentionally) | About 33–35 cm; comparison must still be verified |
| 26 | Small cabbage | About 35–36 cm; comparison must still be verified |
| 27 | Cauliflower, approximate bulk | Roughly 0.8–0.9 kg |
| 28 | Cabbage, approximate bulk | Roughly 0.9–1.1 kg |
| 29 | Cabbage (repeated intentionally), approximate bulk | Roughly 1.1–1.3 kg |
| 30 | Cabbage, approximate bulk | Roughly 1.2–1.5 kg |
| 31 | Honeydew melon, approximate bulk | Roughly 1.4–1.7 kg |
| 32 | Honeydew melon (repeated intentionally), approximate bulk | Roughly 1.6–1.9 kg |
| 33 | Small watermelon, approximate bulk | Roughly 1.8–2.1 kg |
| 34 | Muskmelon (kharbuja), approximate bulk | Roughly 2.0–2.3 kg |
| 35 | Large honeydew melon, approximate bulk | Roughly 2.2–2.5 kg |
| 36 | Large muskmelon, approximate bulk | Roughly 2.4–2.8 kg |
| 37 | Small pumpkin, approximate bulk | Roughly 2.6–3.0 kg |
| 38 | Medium pumpkin, approximate bulk | Roughly 2.8–3.2 kg |
| 39 | Small watermelon, approximate bulk | Roughly 3.0–3.4 kg |
| 40 | Full-size watermelon, approximate bulk | Roughly 3.1–3.6 kg; size varies widely |
| 41 | Large watermelon, approximate bulk | No verified value; avoid uniform-growth implication |
| 42 | No generic size card; care-team message first | Intentional safety/product exception |

The planning basis came from the team-supplied correction plan, not a medical authority. It is shown so you can see what exists, not as proof.

### Record your comparison decision

**Decision:** `REQUEST VERIFICATION; KEEP HIDDEN UNTIL VERIFIED`

**Product decision recorded:** The comparison concept and the revised rounder/repeatable object sequence are accepted for product by Kajal. This does not verify the medical measurements or object dimensions.

**If requesting verification, list the weeks:** ______________________________________

**Product comments about familiarity, tone or cultural relevance:**

____________________________________________________________________________

Before any selected comparison is enabled, the team must attach a named fetal-measurement source, document the measurement convention, verify the size range and comparison-object dimensions, obtain clinical/product review, resolve image licensing, and show you the rendered card.

---

## Part 3 — PC00: possible pregnancy

`PC00` means **possible pregnancy**, not confirmed pregnancy. You are reviewing a proposed page for someone who thinks pregnancy may be possible.

### Reconstructed page preview

> **Possible pregnancy: testing and next steps**
>
> **Preparation**  
> Follow the instructions supplied with the home pregnancy test.
>
> **Ask a professional**  
> Ask your local maternal-health worker about pregnancy testing support.

The current profile intentionally contains no pregnancy-week number, fetal-size card, nutrition card, movement card or confirmed-pregnancy wording.

### PC00-A — Overall state and title

Check:

- Does the title make it clear that pregnancy is not confirmed?
- Would a user understand why she is seeing this page?
- Should the unused nutrition, movement and development sections remain hidden?
- Is an explicit action needed without interpreting a test result?

**Decision:** `ACCEPT FOR PRODUCT` — confirmed by Kajal on 11 September 2026.

**Reason or exact change:**

____________________________________________________________________________

### PC00-B — Home-test instructions

- Review task: `REV-f08ce8983ecf45cc288e`
- Evidence: `E-TEST`
- Proposed section: Preparation
- Proposed text: “Follow the instructions supplied with the home pregnancy test.”
- Source support: the source says the test's written directions must be followed exactly.
- Source: [Knowing if you are pregnant — Office on Women's Health](https://womenshealth.gov/pregnancy/you-get-pregnant/knowing-if-you-are-pregnant)

Check clarity, usefulness, placement and whether it avoids interpreting a result.

**Product decision:** `ACCEPT FOR PRODUCT` — confirmed by Kajal on 11 September 2026.

**Reason or exact replacement:**

____________________________________________________________________________

### PC00-C — Local testing-support card

- Review task: `REV-7bc2b9147fd2c4ff777b`
- Evidence: `E-IN-TEST-SUPPORT`
- Proposed section: Ask a professional
- Current text: “Ask your local maternal-health worker about pregnancy testing support.”
- Source support: an NHM Community Health Officer booklet refers to early pregnancy diagnosis using Nischay Kits.
- Source: [Maternal Health: Role of Community Health Officers — NHM PDF](https://www.nhm.gov.in/New_Update-2022-23/MH/GUIDELINES-%20MH/CHO_Booklet_%20Maternal_Health-English.pdf)

Check whether ordinary users understand the term, whether the sentence promises unavailable services, and whether the source is current/local enough. Use `NEEDS SPECIALIST REVIEW` for local applicability uncertainty.

Possible wording to assess, not an automatic decision:

> If you need help accessing a pregnancy test, ask a local healthcare professional or health worker what support is available.

**Product decision:** `ACCEPT FOR PRODUCT` — confirmed by Kajal on 11 September 2026.

**Reason or exact replacement:**

____________________________________________________________________________

### PC00 future-app behaviour check

Use only fictional data.

| Fictional input | Expected result |
|---|---|
| “I might be pregnant; not confirmed” | Resolve to `PC00` |
| Pregnancy not confirmed | No pregnancy week or fetal-size claim |
| Test not yet taken | Test-instruction card may appear; do not infer a result |
| Local service availability unknown | Do not promise a kit, appointment or named service |

**Behaviour decision:** `ACCEPT FOR PRODUCT` — confirmed by Kajal on 11 September 2026.

**Required change:** __________________________________________________________

**Rendered-UI review status:** PENDING — no final Streamlit page exists yet.

---

## Part 4 — P10: confirmed pregnancy, week 10

### Reconstructed page preview

> **Week 10: development and everyday support**
>
> Development: one general source measurement  
> Nutrition: four proposed cards  
> Movement: two conditional cards  
> Wellbeing: two cards  
> Symptoms: one stop-and-seek-help card  
> Preparation: two cards  
> Avoid: one food-safety card  
> Ask a professional: three cards

This is a content-and-placement preview. Final styling and ordering wait for Streamlit.

### P10-A — Overall page

Check whether the title is clear, whether 2.5 cm is labelled as a general source value rather than a user's scan, which cards should appear first, how unknown movement facts are explained, and whether source/country labels can be opened.

**Decision:** `ACCEPT FOR PRODUCT` — confirmed by Kajal on 11 September 2026.

**Exact ordering, labels or empty-state changes:**

____________________________________________________________________________

### P10-B — Inspect every proposed card

Open a linked source whenever the summary is not enough. Judge wording, usefulness, placement and understandable conditions. Send medical, India-local or licence uncertainty to a specialist.

| ID | Section | Proposed user-facing text | Source/support | Conditions | Your decision |
|---|---|---|---|---|---|
| `E-P10-DEVELOPMENT` | Development | The embryo is now known as a fetus and is about 2.5 cm in length. | [Better Health Victoria](https://www.betterhealth.vic.gov.au/health/healthyliving/pregnancy-week-by-week): week-10 statement | None recorded | `ACCEPT FOR PRODUCT` |
| `E-IN-FOOD` | Nutrition | Include a variety of locally available seasonal foods, vegetables and fruit. | [NHM Safe Motherhood booklet](https://www.nhm.gov.in/images/pdf/programmes/maternal-health/guidelines/my_safe_motherhood_booklet_english.pdf): varied local seasonal foods | None | `ACCEPT FOR PRODUCT` |
| `E-FOOD-HYGIENE` | Nutrition | Wash fruit and vegetables before eating them. | [Office on Women's Health](https://womenshealth.gov/pregnancy/youre-pregnant-now-what/staying-healthy-and-safe): wash produce | None | `ACCEPT FOR PRODUCT` |
| `E-IN-FOOD-GRAINS` | Nutrition | Cereals, whole grains and pulses are good sources of proteins. | [NHM Safe Motherhood booklet](https://www.nhm.gov.in/images/pdf/programmes/maternal-health/guidelines/my_safe_motherhood_booklet_english.pdf) | None | `ACCEPT FOR PRODUCT` |
| `E-IN-FOOD-GREENS` | Nutrition | Green leafy vegetables are a rich source of iron and folic acid. | [NHM Safe Motherhood booklet](https://www.nhm.gov.in/images/pdf/programmes/maternal-health/guidelines/my_safe_motherhood_booklet_english.pdf) | None | `ACCEPT FOR PRODUCT` |
| `E-PREG-MOVEMENT-OPTIONS` | Movement | After discussing suitability with your care professional, walking or swimming may be options for moderate, low-impact activity. | [Office on Women's Health](https://womenshealth.gov/pregnancy/youre-pregnant-now-what/staying-healthy-and-safe): clearance and low-impact options | Require exercise clearance; exclude restriction/warning symptom | `ACCEPT FOR PRODUCT` |
| `E-PREG-MOVEMENT-PACE` | Movement | Start slowly, build up gradually, and take breaks. You should be able to talk during activity. | [Office on Women's Health](https://womenshealth.gov/pregnancy/youre-pregnant-now-what/staying-healthy-and-safe): pacing and talk test | Same movement conditions | `ACCEPT FOR PRODUCT` |
| `E-PREG-TALK` | Wellbeing | You can talk about how you feel with someone supportive or your care professional. | [NHS mental health in pregnancy](https://www.nhs.uk/pregnancy/mental-health-in-pregnancy-and-after-the-birth/mental-health/) | None | `ACCEPT FOR PRODUCT` |
| `E-PREG-ENJOY` | Wellbeing | Try to leave some time for an activity you enjoy. | [NHS mental health in pregnancy](https://www.nhs.uk/pregnancy/mental-health-in-pregnancy-and-after-the-birth/mental-health/) | None | `ACCEPT FOR PRODUCT` |
| `E-PREG-MOVEMENT-STOP` | Symptoms | Stop activity and seek medical advice if warning symptoms such as chest pain, bleeding, fluid leakage or reduced fetal movement occur. | [Office on Women's Health](https://womenshealth.gov/pregnancy/youre-pregnant-now-what/staying-healthy-and-safe): exercise stop symptoms | Clinical/safety review required | `ACCEPT FOR PRODUCT` |
| `E-IN-BIRTH-PLAN` | Preparation | Discuss birth preparation and your choice of a birth companion with your care team. | [NHM CHO booklet](https://www.nhm.gov.in/New_Update-2022-23/MH/GUIDELINES-%20MH/CHO_Booklet_%20Maternal_Health-English.pdf) | Timing/priority needs review | `ACCEPT FOR PRODUCT` |
| `E-PREG-MEDICINE-BOUNDARY` | Preparation | Speak with your doctor before starting or stopping a medicine. | [Office on Women's Health](https://womenshealth.gov/pregnancy/youre-pregnant-now-what/staying-healthy-and-safe) | None | `ACCEPT FOR PRODUCT` |
| `E-PREG-FOOD-AVOID` | Avoid | The source advises avoiding unpasteurised milk or juice and raw sprouts during pregnancy. | [Office on Women's Health](https://womenshealth.gov/pregnancy/youre-pregnant-now-what/staying-healthy-and-safe) | Clinical/localisation review required | `ACCEPT FOR PRODUCT` |
| `E-MOVEMENT-CONSULT` | Ask a professional | Discuss exercise during pregnancy with your doctor or midwife before starting. | [Office on Women's Health](https://womenshealth.gov/pregnancy/youre-pregnant-now-what/staying-healthy-and-safe) | None | `ACCEPT FOR PRODUCT` |
| `E-IN-ANC-TESTS` | Ask a professional | The NHM booklet lists urine, haemoglobin, syphilis, HIV and blood-group tests in antenatal care. | [NHM CHO booklet](https://www.nhm.gov.in/New_Update-2022-23/MH/GUIDELINES-%20MH/CHO_Booklet_%20Maternal_Health-English.pdf) | India-programme/clinical review | `ACCEPT FOR PRODUCT` |
| `E-IN-REGISTRATION` | Ask a professional | The NHM booklet calls for pregnancy registration in the first trimester. | [NHM CHO booklet](https://www.nhm.gov.in/New_Update-2022-23/MH/GUIDELINES-%20MH/CHO_Booklet_%20Maternal_Health-English.pdf) | Show only when pregnancy confirmed | `ACCEPT FOR PRODUCT` |

For a changed row, record its evidence ID and exact replacement/placement:

____________________________________________________________________________

### P10 future-app behaviour checks

| Fictional input | Expected result |
|---|---|
| Confirmed pregnancy, week 10 | Resolve to `P10`, never `PC00` |
| No scan measurement | General 2.5 cm statement may be labelled as general source information |
| Fictional scan has a measurement | Show separately as user/document information |
| Exercise clearance unknown | Do not imply suitability; ask for missing information |
| Clearance true; no restriction/symptom | Conditional movement cards may be eligible after approval |
| Restriction or warning symptom present | Hide normal movement suggestions and follow reviewed safety routing |

**Behaviour decision:** `ACCEPT FOR PRODUCT` — confirmed by Kajal on 11 September 2026.

**Required change:** __________________________________________________________

**Rendered-UI review status:** PENDING — no final Streamlit page exists yet.

---

## Part 5 — PP01: first week after birth

### Reconstructed page preview

> **Week 1 after birth: rest and support**
>
> Nutrition: one breastfeeding-dependent card  
> Movement: two delivery/readiness-dependent cards  
> Wellbeing: three cards  
> Preparation: two cards  
> Ask a professional: one card

Several rest/help ideas overlap. Decide whether they should be combined or ranked.

### PP01-A — Overall page

Check the title, which rest/help cards should combine, whether professional help stays prominent, whether hidden cards explain missing facts, and whether the delivery/readiness terms are understandable.

**Decision:** `ACCEPT FOR PRODUCT` — confirmed by Kajal on 11 September 2026.

**Exact ordering, combination or empty-state changes:**

____________________________________________________________________________

### PP01-B — Inspect every proposed card

| ID | Section | Proposed user-facing text | Source/support | Conditions | Your decision |
|---|---|---|---|---|---|
| `E-PP-DIET` | Nutrition | You do not need to follow a special diet while you're breastfeeding. | [NHS breastfeeding and diet](https://www.nhs.uk/baby/breastfeeding-and-bottle-feeding/breastfeeding-and-lifestyle/diet/) | Only when breastfeeding confirmed; allergies/restrictions/advice still apply | `ACCEPT FOR PRODUCT` |
| `E-PP-GENTLE-MOVEMENT` | Movement | After a straightforward birth, gentle walking or stretches may be options when you feel ready. | [NHS keeping fit with a baby](https://www.nhs.uk/baby/support-and-services/keeping-fit-and-healthy-with-a-baby/) | Require uncomplicated delivery and readiness; exclude restrictions, symptoms, complicated delivery/caesarean | `ACCEPT FOR PRODUCT` |
| `E-PP-MOVEMENT-QUESTION` | Movement | After a complicated delivery or caesarean, ask your care professional before starting strenuous activity. | [NHS keeping fit with a baby](https://www.nhs.uk/baby/support-and-services/keeping-fit-and-healthy-with-a-baby/) | Show with complicated delivery or caesarean | `ACCEPT FOR PRODUCT` |
| `E-PP-MIND-REST` | Wellbeing | Allow yourself time to rest as part of caring for your wellbeing. | [NHS keeping fit with a baby](https://www.nhs.uk/baby/support-and-services/keeping-fit-and-healthy-with-a-baby/) | None | `ACCEPT FOR PRODUCT` |
| `E-PP-MIND-TALK` | Wellbeing | Talk with someone supportive about how you are feeling. | [NHS keeping fit with a baby](https://www.nhs.uk/baby/support-and-services/keeping-fit-and-healthy-with-a-baby/) | None | `ACCEPT FOR PRODUCT` |
| `E-PP-ASK-HELP` | Wellbeing | You can make room for rest and accept practical help from people you trust. | [NHS keeping fit with a baby](https://www.nhs.uk/baby/support-and-services/keeping-fit-and-healthy-with-a-baby/) | None | `ACCEPT FOR PRODUCT` |
| `E-PP-PRACTICAL-HELP` | Preparation | Tell a trusted, supportive person what practical help would be useful to you. | [NHS relationships after a baby](https://www.nhs.uk/baby/support-and-services/relationships-after-having-a-baby/) | None | `ACCEPT FOR PRODUCT` |
| `E-IN-REST-PP` | Preparation/hero | Make space for rest while recovering after birth. | [NHM Safe Motherhood booklet](https://www.nhm.gov.in/images/pdf/programmes/maternal-health/guidelines/my_safe_motherhood_booklet_english.pdf) | Postpartum weeks 1–6 | `ACCEPT FOR PRODUCT` |
| `E-PP-PERSISTENT-CONCERN` | Ask a professional | If you are worried about how you feel or are struggling to cope, talk to a care professional. | [NHS keeping fit with a baby](https://www.nhs.uk/baby/support-and-services/keeping-fit-and-healthy-with-a-baby/) | Keep visible; safety/clinical review required | `ACCEPT FOR PRODUCT` |

Assess this possible boundary beside the diet card:

> General information only. Your allergies, dietary restrictions and personal medical advice still apply.

**Diet-boundary decision:** `ACCEPT FOR PRODUCT` — confirmed by Kajal on 11 September 2026.

**Exact replacement if changing:**

____________________________________________________________________________

### PP01 future-app behaviour checks

| Fictional input | Expected result |
|---|---|
| Postpartum week 1 | Resolve to `PP01` |
| Breastfeeding unknown | Do not imply diet claim applies; ask for missing information |
| Breastfeeding confirmed | Diet card may be eligible after approval, with its boundary |
| Delivery/readiness unknown | Do not imply gentle movement is suitable |
| Uncomplicated delivery, ready, no restriction/symptom | Gentle movement card may be eligible after approval |
| Complicated delivery or caesarean | Show professional-discussion card; do not establish normal eligibility |
| User struggling to cope | Professional-help route remains visible; urgent symptoms use reviewed safety routing |

**Behaviour decision:** `ACCEPT FOR PRODUCT` — confirmed by Kajal on 11 September 2026.

**Required change:** __________________________________________________________

**Rendered-UI review status:** PENDING — no final Streamlit page exists yet.

---

## Part 6 — What happens after this workbook

1. Send the completed workbook to Aswath/your teammate.
2. Their Codex converts decisions into the structured review log; you do not edit IDs.
3. The team applies your exact wording, order, condition and empty-state changes.
4. Review packets are regenerated; changed text receives a new fingerprint and review.
5. A qualified maternal-health reviewer checks medical meaning and safety.
6. An India-localisation reviewer checks terminology, programmes and availability.
7. A licence/source reviewer decides what may be stored, quoted, embedded and displayed.
8. The team builds a real rendered preview or Streamlit screen for the three profiles.
9. You perform final visual/interaction review on those rendered screens.

Before a public demo uses the content, also review `P01`, `P09`, `P24`, `P36`, `PP06`, `PP12`, `PPD0–PPD7`, the remaining applicable evidence tasks, and the 34 practical catalogue items. Confirm evaluation cases for wrong-week retrieval, unknown facts, restrictions, citations, refusal and safety routing.

Stage 2 engineering may continue in parallel. Unreviewed content may remain draft test data, but it must not be treated as released health guidance or enter live RAG.

---

## Final confirmation for this pass

Complete only after inspecting the tables and the linked sources you need.

- [ ] I made only product/content decisions within my role.
- [ ] I did not treat a Codex recommendation as human evidence.
- [ ] I did not claim clinical, India-localisation or licence approval.
- [ ] I recorded uncertainty as `NEEDS SPECIALIST REVIEW`.
- [ ] I understand final visual approval waits for rendered Streamlit screens.
- [ ] I used fictional data only for behaviour checks.

**Reviewer name and capacity:** Kajal — product/content review

**Date:** 11 September 2026

**General notes:**

____________________________________________________________________________
