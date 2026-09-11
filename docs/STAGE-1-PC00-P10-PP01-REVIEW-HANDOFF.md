# Stage 1 PC00/P10/PP01 review handoff

This is the current reviewer packet for the first demonstration slice. It is generated from the governed evidence tasks and decision ledger, so task IDs and checksums below name the exact versions reviewed.

- Current Stage 0 release fingerprint: `d3b25c36806c0e6a5f442d994b48a088b99e1a86d3c4174de3d6854f27fa788b`
- Profiles: `PC00, P10, PP01`
- Governed evidence tasks in this slice: **27**
- Recorded product/content decisions: **54**
- Fetal-size comparisons: **42 draft and hidden**
- Public corpus and production embeddings: **not released**
- Product approval evidence: [Kajal approval import record](STAGE-1-KAJAL-APPROVAL-IMPORT-RECORD.md)

## Where this fits in the plan

1. **Stage 0:** the source registry, evidence, fragments, weekly profiles and comparison proposals exist. The corrected comparison sequence is recorded, but measurements and object dimensions are blank.
2. **Stage 1:** Kajal's product/content decisions are recorded for this three-profile slice. The exact remaining work is the licence, clinical and India-localisation review below.
3. **Stage 2:** storage engineering may continue with draft/test-only records. No item in this packet may enter live RAG until all required roles accept the same checksum and the release gate passes.
4. **Visual gate:** the Streamlit reviewer preview is a draft view. Kajal's final visual decision is recorded only after specialist corrections are applied and the screens are rendered again.

## Recorded decisions and remaining people

| Role | Current decisions in this slice | Next action |
|---|---:|---|
| Product | 27 accepted by Kajal | Recheck rendered screens after specialist changes |
| Content | 27 accepted by Kajal | Recheck only if wording changes |
| Clinical | 0 | Qualified maternal-health clinician reviews every task below |
| India localisation | 0 | India maternal-health reviewer checks local meaning, terms and availability |
| Licence | 0 | Source/licence reviewer checks reuse, quotation, attribution and prototype/public-display scope |

A reviewer must use their real name, capacity/qualification and review date. A team member must not fill these fields on their behalf. `accepted` means only that the named reviewer accepts the exact candidate version within that role.

## Profile coverage

| Profile | Meaning | Evidence tasks | Product/content state |
|---|---|---:|---|
| PC00 | Possible pregnancy, not confirmed | 2 | Accepted by Kajal |
| P10 | Confirmed pregnancy, week 10 | 16 | Accepted by Kajal |
| PP01 | First week after birth | 9 | Accepted by Kajal |

## Specialist review queue

### PC00

#### E-IN-TEST-SUPPORT

- Task: `REV-594728845df724f164a0`
- Candidate: `C-E-IN-TEST-SUPPORT`
- Candidate checksum: `594728845df724f164a00db77938b36c118f0ff2990d167621e0377f2c325d29`
- Source: [Maternal Health: Role of Community Health Officers](https://www.nhm.gov.in/New_Update-2022-23/MH/GUIDELINES-%20MH/CHO_Booklet_%20Maternal_Health-English.pdf) (`NHM-CHO`)
- Source jurisdiction: `IN`
- Source reuse state: `permitted` — Document page 4 explicitly permits reproduction and excerpts when distributed free of cost with source acknowledgement. Acknowledge Ministry of Health and Family Welfare, Government of India, February 2022. Free capstone only; no commercial clearance. Text only. Candidate pending named review.
- Timing: `possible_pregnancy` / `none` / `None–None`
- Required conditions: `none`
- Excluded conditions: `none`
- Recorded roles: `content, product`
- Pending roles: `licence, clinical, india_localisation`

**Exact selected source text**

> Early diagnosis of pregnancy using Nischay Kits.

**Proposed user-facing wording**

- Ask your local maternal-health worker about pregnancy testing support. (`F-IN-TEST-SUPPORT`)

**Decisions already recorded**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for PC00. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for PC00. Final rendered visual review remains pending.

**Each remaining reviewer records one decision**

```text
Task ID: REV-594728845df724f164a0
Candidate ID: C-E-IN-TEST-SUPPORT
Evidence ID: E-IN-TEST-SUPPORT
Source ID: NHM-CHO
Role: licence | clinical | india_localisation
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (required when wording changes):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 594728845df724f164a00db77938b36c118f0ff2990d167621e0377f2c325d29
```

#### E-TEST

- Task: `REV-abdc2b2a6fe6fb8e9350`
- Candidate: `C-E-TEST`
- Candidate checksum: `abdc2b2a6fe6fb8e93507ab5740d1de6812c1489b82756da954e079e0cd35bf1`
- Source: [Knowing if you are pregnant](https://womenshealth.gov/pregnancy/you-get-pregnant/knowing-if-you-are-pregnant) (`OWH-TEST`)
- Source jurisdiction: `US`
- Source reuse state: `permitted` — Page footer expressly permits copying/reproduction without permission. Text only; exclude linked third-party content and images. Attribute HHS Office on Women’s Health and page URL/date. No endorsement. Publication still requires actual content review.
- Timing: `possible_pregnancy` / `none` / `None–None`
- Required conditions: `none`
- Excluded conditions: `none`
- Recorded roles: `content, product`
- Pending roles: `licence, clinical, india_localisation`

**Exact selected source text**

> The most important part of using any HPT is to follow the directions exactly as written.

**Proposed user-facing wording**

- Follow the instructions supplied with the home pregnancy test. (`F-TEST`)

**Decisions already recorded**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for PC00. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for PC00. Final rendered visual review remains pending.

**Each remaining reviewer records one decision**

```text
Task ID: REV-abdc2b2a6fe6fb8e9350
Candidate ID: C-E-TEST
Evidence ID: E-TEST
Source ID: OWH-TEST
Role: licence | clinical | india_localisation
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (required when wording changes):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: abdc2b2a6fe6fb8e93507ab5740d1de6812c1489b82756da954e079e0cd35bf1
```

### P10

#### E-FOOD-HYGIENE

- Task: `REV-d39505d2e4c7e7b722c4`
- Candidate: `C-E-FOOD-HYGIENE`
- Candidate checksum: `d39505d2e4c7e7b722c4be32742e24ec511b3f8db9b53e177d3079b3b3bc199f`
- Source: [Staying healthy and safe](https://womenshealth.gov/pregnancy/youre-pregnant-now-what/staying-healthy-and-safe) (`OWH-HEALTH`)
- Source jurisdiction: `US`
- Source reuse state: `permitted` — Page footer expressly permits copying/reproduction without permission. Text only; exclude linked third-party content and images. Attribute HHS Office on Women’s Health and page URL/date. No endorsement. Publication still requires actual content review.
- Timing: `pregnancy` / `week` / `1–42`
- Required conditions: `none`
- Excluded conditions: `none`
- Recorded roles: `content, product`
- Pending roles: `licence, clinical, india_localisation`

**Exact selected source text**

> Wash produce before eating.

**Proposed user-facing wording**

- Wash fruit and vegetables before eating them. (`F-FOOD-HYGIENE`)

**Decisions already recorded**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for P10. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for P10. Final rendered visual review remains pending.

**Each remaining reviewer records one decision**

```text
Task ID: REV-d39505d2e4c7e7b722c4
Candidate ID: C-E-FOOD-HYGIENE
Evidence ID: E-FOOD-HYGIENE
Source ID: OWH-HEALTH
Role: licence | clinical | india_localisation
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (required when wording changes):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: d39505d2e4c7e7b722c4be32742e24ec511b3f8db9b53e177d3079b3b3bc199f
```

#### E-IN-ANC-TESTS

- Task: `REV-a62372f158dfc78f74e4`
- Candidate: `C-E-IN-ANC-TESTS`
- Candidate checksum: `a62372f158dfc78f74e47089c72eb44569f8ca6ff8ff17080dc468a7355fc15c`
- Source: [Maternal Health: Role of Community Health Officers](https://www.nhm.gov.in/New_Update-2022-23/MH/GUIDELINES-%20MH/CHO_Booklet_%20Maternal_Health-English.pdf) (`NHM-CHO`)
- Source jurisdiction: `IN`
- Source reuse state: `permitted` — Document page 4 explicitly permits reproduction and excerpts when distributed free of cost with source acknowledgement. Acknowledge Ministry of Health and Family Welfare, Government of India, February 2022. Free capstone only; no commercial clearance. Text only. Candidate pending named review.
- Timing: `pregnancy` / `week` / `4–42`
- Required conditions: `none`
- Excluded conditions: `none`
- Recorded roles: `content, product`
- Pending roles: `licence, clinical, india_localisation`

**Exact selected source text**

> Test all pregnant women for urine (albumin and sugar), haemoglobin, syphilis, HIV and blood grouping.

**Proposed user-facing wording**

- The NHM booklet lists urine, haemoglobin, syphilis, HIV and blood-group tests in antenatal care. (`F-IN-ANC-TESTS`)

**Decisions already recorded**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for P10. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for P10. Final rendered visual review remains pending.

**Each remaining reviewer records one decision**

```text
Task ID: REV-a62372f158dfc78f74e4
Candidate ID: C-E-IN-ANC-TESTS
Evidence ID: E-IN-ANC-TESTS
Source ID: NHM-CHO
Role: licence | clinical | india_localisation
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (required when wording changes):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: a62372f158dfc78f74e47089c72eb44569f8ca6ff8ff17080dc468a7355fc15c
```

#### E-IN-BIRTH-PLAN

- Task: `REV-4f9763c7846632db8202`
- Candidate: `C-E-IN-BIRTH-PLAN`
- Candidate checksum: `4f9763c7846632db820200eb31d369cfb0967eff2f684fb35d009126d53d3964`
- Source: [Maternal Health: Role of Community Health Officers](https://www.nhm.gov.in/New_Update-2022-23/MH/GUIDELINES-%20MH/CHO_Booklet_%20Maternal_Health-English.pdf) (`NHM-CHO`)
- Source jurisdiction: `IN`
- Source reuse state: `permitted` — Document page 4 explicitly permits reproduction and excerpts when distributed free of cost with source acknowledgement. Acknowledge Ministry of Health and Family Welfare, Government of India, February 2022. Free capstone only; no commercial clearance. Text only. Candidate pending named review.
- Timing: `pregnancy` / `week` / `4–42`
- Required conditions: `none`
- Excluded conditions: `none`
- Recorded roles: `content, product`
- Pending roles: `licence, clinical, india_localisation`

**Exact selected source text**

> Support in birth planning and birth preparedness including birth companion of choice.

**Proposed user-facing wording**

- Discuss birth preparation and your choice of a birth companion with your care team. (`F-IN-BIRTH-PLAN`)

**Decisions already recorded**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for P10. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for P10. Final rendered visual review remains pending.

**Each remaining reviewer records one decision**

```text
Task ID: REV-4f9763c7846632db8202
Candidate ID: C-E-IN-BIRTH-PLAN
Evidence ID: E-IN-BIRTH-PLAN
Source ID: NHM-CHO
Role: licence | clinical | india_localisation
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (required when wording changes):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 4f9763c7846632db820200eb31d369cfb0967eff2f684fb35d009126d53d3964
```

#### E-IN-FOOD

- Task: `REV-217ecfedf0f1b7f574bf`
- Candidate: `C-E-IN-FOOD`
- Candidate checksum: `217ecfedf0f1b7f574bf5bf542482365d0fcbe4e918aabceafb49f56eaf2fb95`
- Source: [My Safe Motherhood: Booklet for Expecting Mothers](https://www.nhm.gov.in/images/pdf/programmes/maternal-health/guidelines/my_safe_motherhood_booklet_english.pdf) (`NHM-MOTHERHOOD`)
- Source jurisdiction: `IN`
- Source reuse state: `permitted` — NHM copyright policy permits attributed reproduction in accurate context: https://www.nhm.gov.in/nhm/about-nhm/index4.php?lang=1&level=0&lid=13&linkid=8 . Only original government text selected; no credited UNICEF/WHO illustrations. Source date not printed; older schedules/doses are excluded. Acknowledge Ministry of Health and Family Welfare, Government of India. Candidate pending currency/content review.
- Timing: `pregnancy` / `week` / `1–42`
- Required conditions: `none`
- Excluded conditions: `none`
- Recorded roles: `content, product`
- Pending roles: `licence, clinical, india_localisation`

**Exact selected source text**

> Prefer using variety of local seasonal foods, vegetables and fruits

**Proposed user-facing wording**

- Include a variety of locally available seasonal foods, vegetables and fruit. (`F-IN-FOOD`)

**Decisions already recorded**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for P10. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for P10. Final rendered visual review remains pending.

**Each remaining reviewer records one decision**

```text
Task ID: REV-217ecfedf0f1b7f574bf
Candidate ID: C-E-IN-FOOD
Evidence ID: E-IN-FOOD
Source ID: NHM-MOTHERHOOD
Role: licence | clinical | india_localisation
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (required when wording changes):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 217ecfedf0f1b7f574bf5bf542482365d0fcbe4e918aabceafb49f56eaf2fb95
```

#### E-IN-FOOD-GRAINS

- Task: `REV-1c40d463148587f7f2ed`
- Candidate: `C-E-IN-FOOD-GRAINS`
- Candidate checksum: `1c40d463148587f7f2edaae2dda632582b4b7abaa3a63e0ec1bf6b40cabb9888`
- Source: [My Safe Motherhood: Booklet for Expecting Mothers](https://www.nhm.gov.in/images/pdf/programmes/maternal-health/guidelines/my_safe_motherhood_booklet_english.pdf) (`NHM-MOTHERHOOD`)
- Source jurisdiction: `IN`
- Source reuse state: `permitted` — NHM copyright policy permits attributed reproduction in accurate context: https://www.nhm.gov.in/nhm/about-nhm/index4.php?lang=1&level=0&lid=13&linkid=8 . Only original government text selected; no credited UNICEF/WHO illustrations. Source date not printed; older schedules/doses are excluded. Acknowledge Ministry of Health and Family Welfare, Government of India. Candidate pending currency/content review.
- Timing: `pregnancy` / `week` / `4–42`
- Required conditions: `none`
- Excluded conditions: `none`
- Recorded roles: `content, product`
- Pending roles: `licence, clinical, india_localisation`

**Exact selected source text**

> Cereals, whole grains and pulses are good sources of proteins.

**Proposed user-facing wording**

- Cereals, whole grains and pulses are good sources of proteins. (`F-IN-FOOD-GRAINS`)

**Decisions already recorded**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for P10. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for P10. Final rendered visual review remains pending.

**Each remaining reviewer records one decision**

```text
Task ID: REV-1c40d463148587f7f2ed
Candidate ID: C-E-IN-FOOD-GRAINS
Evidence ID: E-IN-FOOD-GRAINS
Source ID: NHM-MOTHERHOOD
Role: licence | clinical | india_localisation
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (required when wording changes):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 1c40d463148587f7f2edaae2dda632582b4b7abaa3a63e0ec1bf6b40cabb9888
```

#### E-IN-FOOD-GREENS

- Task: `REV-3e0ef5cc691249acf89e`
- Candidate: `C-E-IN-FOOD-GREENS`
- Candidate checksum: `3e0ef5cc691249acf89e932999f87097907a56edba7e1422c4cebbdb8e080cab`
- Source: [My Safe Motherhood: Booklet for Expecting Mothers](https://www.nhm.gov.in/images/pdf/programmes/maternal-health/guidelines/my_safe_motherhood_booklet_english.pdf) (`NHM-MOTHERHOOD`)
- Source jurisdiction: `IN`
- Source reuse state: `permitted` — NHM copyright policy permits attributed reproduction in accurate context: https://www.nhm.gov.in/nhm/about-nhm/index4.php?lang=1&level=0&lid=13&linkid=8 . Only original government text selected; no credited UNICEF/WHO illustrations. Source date not printed; older schedules/doses are excluded. Acknowledge Ministry of Health and Family Welfare, Government of India. Candidate pending currency/content review.
- Timing: `pregnancy` / `week` / `4–42`
- Required conditions: `none`
- Excluded conditions: `none`
- Recorded roles: `content, product`
- Pending roles: `licence, clinical, india_localisation`

**Exact selected source text**

> Green leafy vegetables are a rich source of iron and folic acid.

**Proposed user-facing wording**

- Green leafy vegetables are a rich source of iron and folic acid. (`F-IN-FOOD-GREENS`)

**Decisions already recorded**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for P10. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for P10. Final rendered visual review remains pending.

**Each remaining reviewer records one decision**

```text
Task ID: REV-3e0ef5cc691249acf89e
Candidate ID: C-E-IN-FOOD-GREENS
Evidence ID: E-IN-FOOD-GREENS
Source ID: NHM-MOTHERHOOD
Role: licence | clinical | india_localisation
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (required when wording changes):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 3e0ef5cc691249acf89e932999f87097907a56edba7e1422c4cebbdb8e080cab
```

#### E-IN-REGISTRATION

- Task: `REV-059cacced965f62696c7`
- Candidate: `C-E-IN-REGISTRATION`
- Candidate checksum: `059cacced965f62696c7831fc27d2e43068cd88d031d9c2cfa14742655ec3fa1`
- Source: [Maternal Health: Role of Community Health Officers](https://www.nhm.gov.in/New_Update-2022-23/MH/GUIDELINES-%20MH/CHO_Booklet_%20Maternal_Health-English.pdf) (`NHM-CHO`)
- Source jurisdiction: `IN`
- Source reuse state: `permitted` — Document page 4 explicitly permits reproduction and excerpts when distributed free of cost with source acknowledgement. Acknowledge Ministry of Health and Family Welfare, Government of India, February 2022. Free capstone only; no commercial clearance. Text only. Candidate pending named review.
- Timing: `pregnancy` / `week` / `4–12`
- Required conditions: `pregnancy_confirmed`
- Excluded conditions: `none`
- Recorded roles: `content, product`
- Pending roles: `licence, clinical, india_localisation`

**Exact selected source text**

> Registration of all the pregnant women in the first trimester of pregnancy.

**Proposed user-facing wording**

- The NHM booklet calls for pregnancy registration in the first trimester. (`F-IN-REGISTRATION`)

**Decisions already recorded**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for P10. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for P10. Final rendered visual review remains pending.

**Each remaining reviewer records one decision**

```text
Task ID: REV-059cacced965f62696c7
Candidate ID: C-E-IN-REGISTRATION
Evidence ID: E-IN-REGISTRATION
Source ID: NHM-CHO
Role: licence | clinical | india_localisation
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (required when wording changes):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 059cacced965f62696c7831fc27d2e43068cd88d031d9c2cfa14742655ec3fa1
```

#### E-MOVEMENT-CONSULT

- Task: `REV-9171d005e40390e49409`
- Candidate: `C-E-MOVEMENT-CONSULT`
- Candidate checksum: `9171d005e40390e4940916e7b2d0f8683aa6e8a163964f9216a6c476df8b9138`
- Source: [Staying healthy and safe](https://womenshealth.gov/pregnancy/youre-pregnant-now-what/staying-healthy-and-safe) (`OWH-HEALTH`)
- Source jurisdiction: `US`
- Source reuse state: `permitted` — Page footer expressly permits copying/reproduction without permission. Text only; exclude linked third-party content and images. Attribute HHS Office on Women’s Health and page URL/date. No endorsement. Publication still requires actual content review.
- Timing: `pregnancy` / `week` / `1–42`
- Required conditions: `none`
- Excluded conditions: `none`
- Recorded roles: `content, product`
- Pending roles: `licence, clinical, india_localisation`

**Exact selected source text**

> Even so, talk to your doctor or midwife before exercising during pregnancy.

**Proposed user-facing wording**

- Discuss exercise during pregnancy with your doctor or midwife before starting. (`F-MOVEMENT-CONSULT`)

**Decisions already recorded**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for P10. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for P10. Final rendered visual review remains pending.

**Each remaining reviewer records one decision**

```text
Task ID: REV-9171d005e40390e49409
Candidate ID: C-E-MOVEMENT-CONSULT
Evidence ID: E-MOVEMENT-CONSULT
Source ID: OWH-HEALTH
Role: licence | clinical | india_localisation
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (required when wording changes):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 9171d005e40390e4940916e7b2d0f8683aa6e8a163964f9216a6c476df8b9138
```

#### E-P10-DEVELOPMENT

- Task: `REV-4ea44e6e04c231b2662a`
- Candidate: `C-E-P10-DEVELOPMENT`
- Candidate checksum: `4ea44e6e04c231b2662abd63bca030adfd16005ed87588382ca45c16f07dc4ea`
- Source: [Pregnancy - week by week](https://www.betterhealth.vic.gov.au/health/healthyliving/pregnancy-week-by-week) (`BHC-WEEKS`)
- Source jurisdiction: `AU`
- Source reuse state: `permitted` — Two short direct quotations only, with quotation marks and Better Health Channel citation/link: https://www.betterhealth.vic.gov.au/about/terms-of-use section Reproducing information on the Internet. No embedding, model rewriting, images or paid access. Free capstone Internet display only; not commercial clearance. Candidate pending named content/localisation/currency review.
- Timing: `pregnancy` / `week` / `10–10`
- Required conditions: `none`
- Excluded conditions: `none`
- Recorded roles: `content, product`
- Pending roles: `licence, clinical, india_localisation`

**Exact selected source text**

> The embryo is now known as a fetus and is about 2.5 cm in length.

**Proposed user-facing wording**

- The embryo is now known as a fetus and is about 2.5 cm in length. (`F-P10-DEVELOPMENT`)

**Decisions already recorded**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for P10. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for P10. Final rendered visual review remains pending.

**Each remaining reviewer records one decision**

```text
Task ID: REV-4ea44e6e04c231b2662a
Candidate ID: C-E-P10-DEVELOPMENT
Evidence ID: E-P10-DEVELOPMENT
Source ID: BHC-WEEKS
Role: licence | clinical | india_localisation
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (required when wording changes):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 4ea44e6e04c231b2662abd63bca030adfd16005ed87588382ca45c16f07dc4ea
```

#### E-PREG-ENJOY

- Task: `REV-5efbb9d4c28f4307a7fb`
- Candidate: `C-E-PREG-ENJOY`
- Candidate checksum: `5efbb9d4c28f4307a7fb6a5e9599631f17307698bee23e2a5f86167a4f9d9b8d`
- Source: [Mental health in pregnancy](https://www.nhs.uk/pregnancy/mental-health-in-pregnancy-and-after-the-birth/mental-health/) (`NHS-PREG-MIND`)
- Source jurisdiction: `UK`
- Source reuse state: `permitted` — Selected original text only; standard NHS terms section 3 and OGL v3.0: https://www.nhs.uk/our-policies/terms-and-conditions/ . Excludes Best Start in Life, third-party content, images and videos. Unchanged quotations must carry Information from the NHS website, as at 100926, linked to the source, and the OGL notice/link. Adapted wording uses the generic OGL attribution rather than implying NHS approval of Nestline wording. No endorsement. Named review pending.
- Timing: `pregnancy` / `week` / `1–42`
- Required conditions: `consents_to_wellbeing_activity`
- Excluded conditions: `current_warning_symptom`
- Recorded roles: `content, product`
- Pending roles: `licence, clinical, india_localisation`

**Exact selected source text**

> try to make time to regularly do something you enjoy

**Proposed user-facing wording**

- Try to leave some time for an activity you enjoy. (`F-PREG-ENJOY`)

**Decisions already recorded**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for P10. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for P10. Final rendered visual review remains pending.

**Each remaining reviewer records one decision**

```text
Task ID: REV-5efbb9d4c28f4307a7fb
Candidate ID: C-E-PREG-ENJOY
Evidence ID: E-PREG-ENJOY
Source ID: NHS-PREG-MIND
Role: licence | clinical | india_localisation
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (required when wording changes):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 5efbb9d4c28f4307a7fb6a5e9599631f17307698bee23e2a5f86167a4f9d9b8d
```

#### E-PREG-FOOD-AVOID

- Task: `REV-80df28d01f7c24fe6b8a`
- Candidate: `C-E-PREG-FOOD-AVOID`
- Candidate checksum: `80df28d01f7c24fe6b8ad7ce85d4fbdf94f7811549108669a5ffcdefc02b52da`
- Source: [Staying healthy and safe](https://womenshealth.gov/pregnancy/youre-pregnant-now-what/staying-healthy-and-safe) (`OWH-HEALTH`)
- Source jurisdiction: `US`
- Source reuse state: `permitted` — Page footer expressly permits copying/reproduction without permission. Text only; exclude linked third-party content and images. Attribute HHS Office on Women’s Health and page URL/date. No endorsement. Publication still requires actual content review.
- Timing: `pregnancy` / `week` / `4–42`
- Required conditions: `none`
- Excluded conditions: `none`
- Recorded roles: `content, product`
- Pending roles: `licence, clinical, india_localisation`

**Exact selected source text**

> Unpasteurized milk or juices. Raw sprouts of any kind (including alfalfa, clover, radish, and mung bean).

**Proposed user-facing wording**

- The source advises avoiding unpasteurised milk or juice and raw sprouts during pregnancy. (`F-PREG-FOOD-AVOID`)

**Decisions already recorded**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for P10. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for P10. Final rendered visual review remains pending.

**Each remaining reviewer records one decision**

```text
Task ID: REV-80df28d01f7c24fe6b8a
Candidate ID: C-E-PREG-FOOD-AVOID
Evidence ID: E-PREG-FOOD-AVOID
Source ID: OWH-HEALTH
Role: licence | clinical | india_localisation
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (required when wording changes):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 80df28d01f7c24fe6b8ad7ce85d4fbdf94f7811549108669a5ffcdefc02b52da
```

#### E-PREG-MEDICINE-BOUNDARY

- Task: `REV-e9a6b716570ed5b1e9b8`
- Candidate: `C-E-PREG-MEDICINE-BOUNDARY`
- Candidate checksum: `e9a6b716570ed5b1e9b8c6dcc73f5d5c83c99322c3b91e578d08d9f12c6e41e2`
- Source: [Staying healthy and safe](https://womenshealth.gov/pregnancy/youre-pregnant-now-what/staying-healthy-and-safe) (`OWH-HEALTH`)
- Source jurisdiction: `US`
- Source reuse state: `permitted` — Page footer expressly permits copying/reproduction without permission. Text only; exclude linked third-party content and images. Attribute HHS Office on Women’s Health and page URL/date. No endorsement. Publication still requires actual content review.
- Timing: `pregnancy` / `week` / `4–42`
- Required conditions: `none`
- Excluded conditions: `none`
- Recorded roles: `content, product`
- Pending roles: `licence, clinical, india_localisation`

**Exact selected source text**

> Always speak with your doctor before you start or stop any medicine. Not using medicine that you need may be more harmful to you and your baby than using the medicine.

**Proposed user-facing wording**

- Speak with your doctor before starting or stopping a medicine. (`F-PREG-MEDICINE-BOUNDARY`)

**Decisions already recorded**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for P10. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for P10. Final rendered visual review remains pending.

**Each remaining reviewer records one decision**

```text
Task ID: REV-e9a6b716570ed5b1e9b8
Candidate ID: C-E-PREG-MEDICINE-BOUNDARY
Evidence ID: E-PREG-MEDICINE-BOUNDARY
Source ID: OWH-HEALTH
Role: licence | clinical | india_localisation
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (required when wording changes):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: e9a6b716570ed5b1e9b8c6dcc73f5d5c83c99322c3b91e578d08d9f12c6e41e2
```

#### E-PREG-MOVEMENT-OPTIONS

- Task: `REV-a744138f53722bafa498`
- Candidate: `C-E-PREG-MOVEMENT-OPTIONS`
- Candidate checksum: `a744138f53722bafa4982cabf30c9ecc2799c118e4be3082b3d09af4e766ab7d`
- Source: [Staying healthy and safe](https://womenshealth.gov/pregnancy/youre-pregnant-now-what/staying-healthy-and-safe) (`OWH-HEALTH`)
- Source jurisdiction: `US`
- Source reuse state: `permitted` — Page footer expressly permits copying/reproduction without permission. Text only; exclude linked third-party content and images. Attribute HHS Office on Women’s Health and page URL/date. No endorsement. Publication still requires actual content review.
- Timing: `pregnancy` / `week` / `4–42`
- Required conditions: `exercise_clearance`
- Excluded conditions: `current_warning_symptom, movement_restriction`
- Recorded roles: `content, product`
- Pending roles: `licence, clinical, india_localisation`

**Exact selected source text**

> For most healthy moms-to-be who do not have any pregnancy-related problems, exercise is a safe and valuable habit. Even so, talk to your doctor or midwife before exercising during pregnancy. Low-impact activities at a moderate level of effort are comfortable and enjoyable for many pregnant women. Walking, swimming, dancing, cycling, and low-impact aerobics are some examples.

**Proposed user-facing wording**

- After discussing suitability with your care professional, walking or swimming may be options for moderate, low-impact activity. (`F-PREG-MOVEMENT-OPTIONS`)

**Decisions already recorded**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for P10. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for P10. Final rendered visual review remains pending.

**Each remaining reviewer records one decision**

```text
Task ID: REV-a744138f53722bafa498
Candidate ID: C-E-PREG-MOVEMENT-OPTIONS
Evidence ID: E-PREG-MOVEMENT-OPTIONS
Source ID: OWH-HEALTH
Role: licence | clinical | india_localisation
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (required when wording changes):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: a744138f53722bafa4982cabf30c9ecc2799c118e4be3082b3d09af4e766ab7d
```

#### E-PREG-MOVEMENT-PACE

- Task: `REV-fb20021d2bdde298f1a7`
- Candidate: `C-E-PREG-MOVEMENT-PACE`
- Candidate checksum: `fb20021d2bdde298f1a7fe19a376329c6e613d301397f6d450e3183bcda8bb56`
- Source: [Staying healthy and safe](https://womenshealth.gov/pregnancy/youre-pregnant-now-what/staying-healthy-and-safe) (`OWH-HEALTH`)
- Source jurisdiction: `US`
- Source reuse state: `permitted` — Page footer expressly permits copying/reproduction without permission. Text only; exclude linked third-party content and images. Attribute HHS Office on Women’s Health and page URL/date. No endorsement. Publication still requires actual content review.
- Timing: `pregnancy` / `week` / `4–42`
- Required conditions: `exercise_clearance`
- Excluded conditions: `current_warning_symptom, movement_restriction`
- Recorded roles: `content, product`
- Pending roles: `licence, clinical, india_localisation`

**Exact selected source text**

> When you exercise, start slowly, progress gradually, and cool down slowly. You should be able to talk while exercising. If not, you may be overdoing it. Take frequent breaks.

**Proposed user-facing wording**

- Start slowly, build up gradually, and take breaks. You should be able to talk during activity. (`F-PREG-MOVEMENT-PACE`)

**Decisions already recorded**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for P10. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for P10. Final rendered visual review remains pending.

**Each remaining reviewer records one decision**

```text
Task ID: REV-fb20021d2bdde298f1a7
Candidate ID: C-E-PREG-MOVEMENT-PACE
Evidence ID: E-PREG-MOVEMENT-PACE
Source ID: OWH-HEALTH
Role: licence | clinical | india_localisation
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (required when wording changes):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: fb20021d2bdde298f1a7fe19a376329c6e613d301397f6d450e3183bcda8bb56
```

#### E-PREG-MOVEMENT-STOP

- Task: `REV-8d49aa866c092bca5fe6`
- Candidate: `C-E-PREG-MOVEMENT-STOP`
- Candidate checksum: `8d49aa866c092bca5fe67ef427c1e23559162060bc20b880ab0dcb7ba9fe39f4`
- Source: [Staying healthy and safe](https://womenshealth.gov/pregnancy/youre-pregnant-now-what/staying-healthy-and-safe) (`OWH-HEALTH`)
- Source jurisdiction: `US`
- Source reuse state: `permitted` — Page footer expressly permits copying/reproduction without permission. Text only; exclude linked third-party content and images. Attribute HHS Office on Women’s Health and page URL/date. No endorsement. Publication still requires actual content review.
- Timing: `pregnancy` / `week` / `4–42`
- Required conditions: `exercise_clearance`
- Excluded conditions: `current_warning_symptom, movement_restriction`
- Recorded roles: `content, product`
- Pending roles: `licence, clinical, india_localisation`

**Exact selected source text**

> Stop exercising and call your doctor as soon as possible if you have any of the following: Dizziness. Headache. Chest pain. Calf pain or swelling. Abdominal pain. Blurred vision. Fluid leaking from the vagina. Vaginal bleeding. Less fetal movement. Contractions.

**Proposed user-facing wording**

- Stop activity and seek medical advice if warning symptoms such as chest pain, bleeding, fluid leakage or reduced fetal movement occur. (`F-PREG-MOVEMENT-STOP`)

**Decisions already recorded**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for P10. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for P10. Final rendered visual review remains pending.

**Each remaining reviewer records one decision**

```text
Task ID: REV-8d49aa866c092bca5fe6
Candidate ID: C-E-PREG-MOVEMENT-STOP
Evidence ID: E-PREG-MOVEMENT-STOP
Source ID: OWH-HEALTH
Role: licence | clinical | india_localisation
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (required when wording changes):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 8d49aa866c092bca5fe67ef427c1e23559162060bc20b880ab0dcb7ba9fe39f4
```

#### E-PREG-TALK

- Task: `REV-339bc693632d7454391d`
- Candidate: `C-E-PREG-TALK`
- Candidate checksum: `339bc693632d7454391dba814571af49e04f7af6d4a517a83d60c157adb98036`
- Source: [Mental health in pregnancy](https://www.nhs.uk/pregnancy/mental-health-in-pregnancy-and-after-the-birth/mental-health/) (`NHS-PREG-MIND`)
- Source jurisdiction: `UK`
- Source reuse state: `permitted` — Selected original text only; standard NHS terms section 3 and OGL v3.0: https://www.nhs.uk/our-policies/terms-and-conditions/ . Excludes Best Start in Life, third-party content, images and videos. Unchanged quotations must carry Information from the NHS website, as at 100926, linked to the source, and the OGL notice/link. Adapted wording uses the generic OGL attribution rather than implying NHS approval of Nestline wording. No endorsement. Named review pending.
- Timing: `pregnancy` / `week` / `1–42`
- Required conditions: `consents_to_wellbeing_activity`
- Excluded conditions: `current_warning_symptom`
- Recorded roles: `content, product`
- Pending roles: `licence, clinical, india_localisation`

**Exact selected source text**

> talk about your feelings to a friend, family member, midwife or doctor

**Proposed user-facing wording**

- You can talk about how you feel with someone supportive or your care professional. (`F-PREG-TALK`)

**Decisions already recorded**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for P10. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for P10. Final rendered visual review remains pending.

**Each remaining reviewer records one decision**

```text
Task ID: REV-339bc693632d7454391d
Candidate ID: C-E-PREG-TALK
Evidence ID: E-PREG-TALK
Source ID: NHS-PREG-MIND
Role: licence | clinical | india_localisation
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (required when wording changes):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 339bc693632d7454391dba814571af49e04f7af6d4a517a83d60c157adb98036
```

### PP01

#### E-IN-REST-PP

- Task: `REV-91c6e3f3c23c7774b024`
- Candidate: `C-E-IN-REST-PP`
- Candidate checksum: `91c6e3f3c23c7774b0244eab55107722904712947b54155f79f5433cb38c38b5`
- Source: [My Safe Motherhood: Booklet for Expecting Mothers](https://www.nhm.gov.in/images/pdf/programmes/maternal-health/guidelines/my_safe_motherhood_booklet_english.pdf) (`NHM-MOTHERHOOD`)
- Source jurisdiction: `IN`
- Source reuse state: `permitted` — NHM copyright policy permits attributed reproduction in accurate context: https://www.nhm.gov.in/nhm/about-nhm/index4.php?lang=1&level=0&lid=13&linkid=8 . Only original government text selected; no credited UNICEF/WHO illustrations. Source date not printed; older schedules/doses are excluded. Acknowledge Ministry of Health and Family Welfare, Government of India. Candidate pending currency/content review.
- Timing: `postpartum` / `week` / `1–6`
- Required conditions: `none`
- Excluded conditions: `none`
- Recorded roles: `content, product`
- Pending roles: `licence, clinical, india_localisation`

**Exact selected source text**

> Take adequate rest.

**Proposed user-facing wording**

- Make space for rest while recovering after birth. (`F-IN-REST-PP`)

**Decisions already recorded**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for PP01. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for PP01. Final rendered visual review remains pending.

**Each remaining reviewer records one decision**

```text
Task ID: REV-91c6e3f3c23c7774b024
Candidate ID: C-E-IN-REST-PP
Evidence ID: E-IN-REST-PP
Source ID: NHM-MOTHERHOOD
Role: licence | clinical | india_localisation
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (required when wording changes):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 91c6e3f3c23c7774b0244eab55107722904712947b54155f79f5433cb38c38b5
```

#### E-PP-ASK-HELP

- Task: `REV-fc7b4ad5e946d2871f88`
- Candidate: `C-E-PP-ASK-HELP`
- Candidate checksum: `fc7b4ad5e946d2871f8801929ab8590d1b7416ae6d3d491847ba27f3b88be048`
- Source: [Keeping fit and healthy with a baby](https://www.nhs.uk/baby/support-and-services/keeping-fit-and-healthy-with-a-baby/) (`NHS-PP-ACTIVE`)
- Source jurisdiction: `UK`
- Source reuse state: `permitted` — Selected original text only; standard NHS terms section 3 and OGL v3.0: https://www.nhs.uk/our-policies/terms-and-conditions/ . Excludes Best Start in Life, third-party content, images and videos. Unchanged quotations must carry Information from the NHS website, as at 100926, linked to the source, and the OGL notice/link. Adapted wording uses the generic OGL attribution rather than implying NHS approval of Nestline wording. No endorsement. Named review pending.
- Timing: `postpartum` / `week` / `1–12`
- Required conditions: `consents_to_wellbeing_activity`
- Excluded conditions: `current_warning_symptom`
- Recorded roles: `content, product`
- Pending roles: `licence, clinical, india_localisation`

**Exact selected source text**

> making time to rest. not trying to "do it all". accepting help with caring for your baby from friends, family or your partner.

**Proposed user-facing wording**

- You can make room for rest and accept practical help from people you trust. (`F-PP-ASK-HELP`)

**Decisions already recorded**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for PP01. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for PP01. Final rendered visual review remains pending.

**Each remaining reviewer records one decision**

```text
Task ID: REV-fc7b4ad5e946d2871f88
Candidate ID: C-E-PP-ASK-HELP
Evidence ID: E-PP-ASK-HELP
Source ID: NHS-PP-ACTIVE
Role: licence | clinical | india_localisation
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (required when wording changes):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: fc7b4ad5e946d2871f8801929ab8590d1b7416ae6d3d491847ba27f3b88be048
```

#### E-PP-DIET

- Task: `REV-7e9058cc6079480b1a62`
- Candidate: `C-E-PP-DIET`
- Candidate checksum: `7e9058cc6079480b1a62bcfaeddf2373274a4a1e3027771c72ce46d3ad23b647`
- Source: [Breastfeeding and diet](https://www.nhs.uk/baby/breastfeeding-and-bottle-feeding/breastfeeding-and-lifestyle/diet/) (`NHS-PP-DIET`)
- Source jurisdiction: `UK`
- Source reuse state: `permitted` — Selected original text only; standard NHS terms section 3 and OGL v3.0: https://www.nhs.uk/our-policies/terms-and-conditions/ . Excludes Best Start in Life, third-party content, images and videos. Unchanged quotations must carry Information from the NHS website, as at 100926, linked to the source, and the OGL notice/link. Adapted wording uses the generic OGL attribution rather than implying NHS approval of Nestline wording. No endorsement. Named review pending.
- Timing: `postpartum` / `week` / `1–12`
- Required conditions: `breastfeeding`
- Excluded conditions: `none`
- Recorded roles: `content, product`
- Pending roles: `licence, clinical, india_localisation`

**Exact selected source text**

> You do not need to follow a special diet while you're breastfeeding.

**Proposed user-facing wording**

- You do not need to follow a special diet while you're breastfeeding. (`F-PP-DIET`)

**Decisions already recorded**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for PP01. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for PP01. Final rendered visual review remains pending.

**Each remaining reviewer records one decision**

```text
Task ID: REV-7e9058cc6079480b1a62
Candidate ID: C-E-PP-DIET
Evidence ID: E-PP-DIET
Source ID: NHS-PP-DIET
Role: licence | clinical | india_localisation
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (required when wording changes):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 7e9058cc6079480b1a62bcfaeddf2373274a4a1e3027771c72ce46d3ad23b647
```

#### E-PP-GENTLE-MOVEMENT

- Task: `REV-d55e6eaf9fa6a3910659`
- Candidate: `C-E-PP-GENTLE-MOVEMENT`
- Candidate checksum: `d55e6eaf9fa6a39106598cae888a628d17d77eb2059f8b8ff746c0c29fb823c2`
- Source: [Keeping fit and healthy with a baby](https://www.nhs.uk/baby/support-and-services/keeping-fit-and-healthy-with-a-baby/) (`NHS-PP-ACTIVE`)
- Source jurisdiction: `UK`
- Source reuse state: `permitted` — Selected original text only; standard NHS terms section 3 and OGL v3.0: https://www.nhs.uk/our-policies/terms-and-conditions/ . Excludes Best Start in Life, third-party content, images and videos. Unchanged quotations must carry Information from the NHS website, as at 100926, linked to the source, and the OGL notice/link. Adapted wording uses the generic OGL attribution rather than implying NHS approval of Nestline wording. No endorsement. Named review pending.
- Timing: `postpartum` / `week` / `1–12`
- Required conditions: `feels_ready_for_gentle_activity, uncomplicated_delivery`
- Excluded conditions: `complicated_delivery_or_caesarean, current_warning_symptom, movement_restriction`
- Recorded roles: `content, product`
- Pending roles: `licence, clinical, india_localisation`

**Exact selected source text**

> If you had a straightforward birth, you can start gentle exercise as soon as you feel up to it. This could include walking, gentle stretches and pelvic floor exercises.

**Proposed user-facing wording**

- After a straightforward birth, gentle walking or stretches may be options when you feel ready. (`F-PP-GENTLE-MOVEMENT`)

**Decisions already recorded**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for PP01. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for PP01. Final rendered visual review remains pending.

**Each remaining reviewer records one decision**

```text
Task ID: REV-d55e6eaf9fa6a3910659
Candidate ID: C-E-PP-GENTLE-MOVEMENT
Evidence ID: E-PP-GENTLE-MOVEMENT
Source ID: NHS-PP-ACTIVE
Role: licence | clinical | india_localisation
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (required when wording changes):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: d55e6eaf9fa6a39106598cae888a628d17d77eb2059f8b8ff746c0c29fb823c2
```

#### E-PP-MIND-REST

- Task: `REV-ab9c6a8121188e53c181`
- Candidate: `C-E-PP-MIND-REST`
- Candidate checksum: `ab9c6a8121188e53c18158c749086d9ebca22b773c97c6ad3f7173313c9fd87d`
- Source: [Keeping fit and healthy with a baby](https://www.nhs.uk/baby/support-and-services/keeping-fit-and-healthy-with-a-baby/) (`NHS-PP-ACTIVE`)
- Source jurisdiction: `UK`
- Source reuse state: `permitted` — Selected original text only; standard NHS terms section 3 and OGL v3.0: https://www.nhs.uk/our-policies/terms-and-conditions/ . Excludes Best Start in Life, third-party content, images and videos. Unchanged quotations must carry Information from the NHS website, as at 100926, linked to the source, and the OGL notice/link. Adapted wording uses the generic OGL attribution rather than implying NHS approval of Nestline wording. No endorsement. Named review pending.
- Timing: `postpartum` / `week` / `1–12`
- Required conditions: `consents_to_wellbeing_activity`
- Excluded conditions: `current_warning_symptom`
- Recorded roles: `content, product`
- Pending roles: `licence, clinical, india_localisation`

**Exact selected source text**

> making time to rest

**Proposed user-facing wording**

- Allow yourself time to rest as part of caring for your wellbeing. (`F-PP-MIND-REST`)

**Decisions already recorded**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for PP01. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for PP01. Final rendered visual review remains pending.

**Each remaining reviewer records one decision**

```text
Task ID: REV-ab9c6a8121188e53c181
Candidate ID: C-E-PP-MIND-REST
Evidence ID: E-PP-MIND-REST
Source ID: NHS-PP-ACTIVE
Role: licence | clinical | india_localisation
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (required when wording changes):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: ab9c6a8121188e53c18158c749086d9ebca22b773c97c6ad3f7173313c9fd87d
```

#### E-PP-MIND-TALK

- Task: `REV-cede4dd7a7d4cb23f32a`
- Candidate: `C-E-PP-MIND-TALK`
- Candidate checksum: `cede4dd7a7d4cb23f32a6f52c23dbe87d53831ddadb4f558436b75072d798d65`
- Source: [Keeping fit and healthy with a baby](https://www.nhs.uk/baby/support-and-services/keeping-fit-and-healthy-with-a-baby/) (`NHS-PP-ACTIVE`)
- Source jurisdiction: `UK`
- Source reuse state: `permitted` — Selected original text only; standard NHS terms section 3 and OGL v3.0: https://www.nhs.uk/our-policies/terms-and-conditions/ . Excludes Best Start in Life, third-party content, images and videos. Unchanged quotations must carry Information from the NHS website, as at 100926, linked to the source, and the OGL notice/link. Adapted wording uses the generic OGL attribution rather than implying NHS approval of Nestline wording. No endorsement. Named review pending.
- Timing: `postpartum` / `week` / `1–12`
- Required conditions: `consents_to_wellbeing_activity`
- Excluded conditions: `current_warning_symptom`
- Recorded roles: `content, product`
- Pending roles: `licence, clinical, india_localisation`

**Exact selected source text**

> talking to people about your feelings

**Proposed user-facing wording**

- Talk with someone supportive about how you are feeling. (`F-PP-MIND-TALK`)

**Decisions already recorded**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for PP01. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for PP01. Final rendered visual review remains pending.

**Each remaining reviewer records one decision**

```text
Task ID: REV-cede4dd7a7d4cb23f32a
Candidate ID: C-E-PP-MIND-TALK
Evidence ID: E-PP-MIND-TALK
Source ID: NHS-PP-ACTIVE
Role: licence | clinical | india_localisation
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (required when wording changes):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: cede4dd7a7d4cb23f32a6f52c23dbe87d53831ddadb4f558436b75072d798d65
```

#### E-PP-MOVEMENT-QUESTION

- Task: `REV-d7a6ab35600616505571`
- Candidate: `C-E-PP-MOVEMENT-QUESTION`
- Candidate checksum: `d7a6ab35600616505571507fb9876075ec4625240a3211f44180e7411df452c6`
- Source: [Keeping fit and healthy with a baby](https://www.nhs.uk/baby/support-and-services/keeping-fit-and-healthy-with-a-baby/) (`NHS-PP-ACTIVE`)
- Source jurisdiction: `UK`
- Source reuse state: `permitted` — Selected original text only; standard NHS terms section 3 and OGL v3.0: https://www.nhs.uk/our-policies/terms-and-conditions/ . Excludes Best Start in Life, third-party content, images and videos. Unchanged quotations must carry Information from the NHS website, as at 100926, linked to the source, and the OGL notice/link. Adapted wording uses the generic OGL attribution rather than implying NHS approval of Nestline wording. No endorsement. Named review pending.
- Timing: `postpartum` / `week` / `1–12`
- Required conditions: `complicated_delivery_or_caesarean`
- Excluded conditions: `none`
- Recorded roles: `content, product`
- Pending roles: `licence, clinical, india_localisation`

**Exact selected source text**

> If you had a more complicated delivery or a caesarean, your recovery time will be longer. Talk to your midwife, health visitor or GP before starting anything strenuous.

**Proposed user-facing wording**

- After a complicated delivery or caesarean, ask your care professional before starting strenuous activity. (`F-PP-MOVEMENT-QUESTION`)

**Decisions already recorded**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for PP01. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for PP01. Final rendered visual review remains pending.

**Each remaining reviewer records one decision**

```text
Task ID: REV-d7a6ab35600616505571
Candidate ID: C-E-PP-MOVEMENT-QUESTION
Evidence ID: E-PP-MOVEMENT-QUESTION
Source ID: NHS-PP-ACTIVE
Role: licence | clinical | india_localisation
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (required when wording changes):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: d7a6ab35600616505571507fb9876075ec4625240a3211f44180e7411df452c6
```

#### E-PP-PERSISTENT-CONCERN

- Task: `REV-08627e8fd9c2176f011c`
- Candidate: `C-E-PP-PERSISTENT-CONCERN`
- Candidate checksum: `08627e8fd9c2176f011c541774b0a659696fdabdf52799d821795fac58968b48`
- Source: [Keeping fit and healthy with a baby](https://www.nhs.uk/baby/support-and-services/keeping-fit-and-healthy-with-a-baby/) (`NHS-PP-ACTIVE`)
- Source jurisdiction: `UK`
- Source reuse state: `permitted` — Selected original text only; standard NHS terms section 3 and OGL v3.0: https://www.nhs.uk/our-policies/terms-and-conditions/ . Excludes Best Start in Life, third-party content, images and videos. Unchanged quotations must carry Information from the NHS website, as at 100926, linked to the source, and the OGL notice/link. Adapted wording uses the generic OGL attribution rather than implying NHS approval of Nestline wording. No endorsement. Named review pending.
- Timing: `postpartum` / `week` / `1–12`
- Required conditions: `none`
- Excluded conditions: `none`
- Recorded roles: `content, product`
- Pending roles: `licence, clinical, india_localisation`

**Exact selected source text**

> If you're worried about how you're feeling, feel like you're struggling to cope, or think you may be depressed, it's important that you talk to your midwife, health visitor or GP. Effective help is available.

**Proposed user-facing wording**

- If you are worried about how you feel or are struggling to cope, talk to a care professional. (`F-PP-PERSISTENT-CONCERN`)

**Decisions already recorded**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for PP01. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for PP01. Final rendered visual review remains pending.

**Each remaining reviewer records one decision**

```text
Task ID: REV-08627e8fd9c2176f011c
Candidate ID: C-E-PP-PERSISTENT-CONCERN
Evidence ID: E-PP-PERSISTENT-CONCERN
Source ID: NHS-PP-ACTIVE
Role: licence | clinical | india_localisation
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (required when wording changes):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 08627e8fd9c2176f011c541774b0a659696fdabdf52799d821795fac58968b48
```

#### E-PP-PRACTICAL-HELP

- Task: `REV-f20e639a975950a1d27a`
- Candidate: `C-E-PP-PRACTICAL-HELP`
- Candidate checksum: `f20e639a975950a1d27ad1114d72ead0c29a4205c61494870a012a1dcd7104a8`
- Source: [Relationships after having a baby](https://www.nhs.uk/baby/support-and-services/relationships-after-having-a-baby/) (`NHS-PP-SUPPORT`)
- Source jurisdiction: `UK`
- Source reuse state: `permitted` — Selected original text only; standard NHS terms section 3 and OGL v3.0: https://www.nhs.uk/our-policies/terms-and-conditions/ . Excludes Best Start in Life, third-party content, images and videos. Unchanged quotations must carry Information from the NHS website, as at 100926, linked to the source, and the OGL notice/link. Adapted wording uses the generic OGL attribution rather than implying NHS approval of Nestline wording. No endorsement. Named review pending.
- Timing: `postpartum` / `week` / `1–12`
- Required conditions: `consents_to_wellbeing_activity`
- Excluded conditions: `current_warning_symptom`
- Recorded roles: `content, product`
- Pending roles: `licence, clinical, india_localisation`

**Exact selected source text**

> It's best to be clear about the kind of help you want, rather than going along with what's offered and feeling resentful.

**Proposed user-facing wording**

- Tell a trusted, supportive person what practical help would be useful to you. (`F-PP-PRACTICAL-HELP`)

**Decisions already recorded**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for PP01. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for PP01. Final rendered visual review remains pending.

**Each remaining reviewer records one decision**

```text
Task ID: REV-f20e639a975950a1d27a
Candidate ID: C-E-PP-PRACTICAL-HELP
Evidence ID: E-PP-PRACTICAL-HELP
Source ID: NHS-PP-SUPPORT
Role: licence | clinical | india_localisation
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (required when wording changes):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: f20e639a975950a1d27ad1114d72ead0c29a4205c61494870a012a1dcd7104a8
```

## Rendered draft previews

These images are reviewer-only artifacts generated from the current governed records. They must be regenerated if a specialist review changes wording, timing or conditions.

- [PC00 default review](previews/PC00-review.jpg)
- [P10 default review](previews/P10-review.jpg)
- [P10 movement facts missing](previews/P10-movement-missing.jpg)
- [P10 movement clearance recorded](previews/P10-movement-cleared.jpg)
- [PP01 default review](previews/PP01-review.jpg)
- [PP01 feeding details missing](previews/PP01-diet-missing.jpg)
- [PP01 caesarean movement conditions](previews/PP01-movement-caesarean.jpg)

## Release and visual-review gates

- [ ] A real licence decision exists for all 27 exact tasks.
- [ ] A qualified clinical decision exists for all 27 exact tasks.
- [ ] A real India-localisation decision exists for all 27 exact tasks.
- [ ] Every requested correction is applied and creates fresh checksums/packets.
- [ ] Kajal reviews the freshly rendered PC00, P10 and PP01 screens.
- [ ] All 42 comparison records remain hidden until measurement convention, source values, object dimensions and artwork/licensing are independently verified.
- [ ] The five-role release gate passes before public embeddings or live RAG are created.

Checking a box in this Markdown file does not alter the governed ledger. Decisions must be entered in `data/reviews/ingestion_decisions.json`; the Stage 1 checker rejects stale task IDs and candidate checksums.
