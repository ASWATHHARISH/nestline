# Ingestion review — BHC-WEEKS

- Run: `ING-8915e6f275572707c89b`
- Outcome: **review_required**
- Admission: `parse_for_review`
- Source artifact: `80ad52f59448eeb0d955df77fdc0e4b3f0d3abd2c391687d0b6ee9c0f092e566`
- Candidate units: 2
- Pending review tasks: 2

## Admission reasons

- source currency decision pending or source changed/withdrawn
- actual source approval is pending
- named source review is pending

## Parser and validation issues

- None.

## Human review queue

### REV-262cfa2775b98b54ae78

- Evidence: `E-P09-DEVELOPMENT`
- Locator: `Pregnancy week 9 / first sentence`
- Applies to: `pregnancy` `week 9–9`
- Jurisdiction: `IN`
- Domains: `journey`
- Dashboard slots: `hero, kpi_development, what_may_change`
- General development measurements: `none`
- Future personal facts: `confirmed_journey_timing`
- Profiles: `P09`
- Catalogue items: `none`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, content, clinical, india_localisation, product`

**Exact selected source text**

> The eyes, mouth and tongue are forming.

**Why it is blocked**

- source awaits actual named approval
- source currency decision is unresolved
- source admission requires review: source currency decision pending or source changed/withdrawn
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- India localisation awaits actual named review
- linked guidance wording awaits actual named review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- None.

**Record one decision for each pending reviewer role**

```text
Task ID: REV-262cfa2775b98b54ae78
Candidate ID: C-E-P09-DEVELOPMENT
Evidence ID: E-P09-DEVELOPMENT
Source ID: BHC-WEEKS
Role: licence | content | clinical | india_localisation | product
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 262cfa2775b98b54ae7867286033727d6b7c651d822aa1fd496a8cf5df79a68c
```

### REV-4ea44e6e04c231b2662a

- Evidence: `E-P10-DEVELOPMENT`
- Locator: `Pregnancy week 10 / first sentence`
- Applies to: `pregnancy` `week 10–10`
- Jurisdiction: `IN`
- Domains: `journey`
- Dashboard slots: `hero, kpi_development, what_may_change`
- General development measurements: `2.5 cm`
- Future personal facts: `confirmed_journey_timing`
- Profiles: `P10`
- Catalogue items: `none`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, clinical, india_localisation`

**Exact selected source text**

> The embryo is now known as a fetus and is about 2.5 cm in length.

**Why it is blocked**

- source awaits actual named approval
- source currency decision is unresolved
- source admission requires review: source currency decision pending or source changed/withdrawn
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- India localisation awaits actual named review
- linked guidance wording awaits actual named review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for P10. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for P10. Final rendered visual review remains pending.

**Record one decision for each pending reviewer role**

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
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 4ea44e6e04c231b2662abd63bca030adfd16005ed87588382ca45c16f07dc4ea
```


A checked box in this exported document does not change publication state. The named decision must be entered into the governed source, evidence, fragment, profile and catalogue records, then the ingestion run must be repeated. Machine-readable decisions belong in data/reviews/ingestion_decisions.json; the ingestion command rejects unknown task IDs and changed checksums.


---

# Ingestion review — NHM-CHO

- Run: `ING-d7bdb8a7b19e66c7a2a2`
- Outcome: **review_required**
- Admission: `parse_for_review`
- Source artifact: `e97347fc9ac72fa94c5668f04e5fc14c440a505cb0e49f28d7adabf4b862e7b8`
- Candidate units: 11
- Pending review tasks: 11

## Admission reasons

- source currency decision pending or source changed/withdrawn
- actual source approval is pending
- named source review is pending

## Parser and validation issues

- None.

## Human review queue

### REV-594728845df724f164a0

- Evidence: `E-IN-TEST-SUPPORT`
- Locator: `Page 11 / section 3.1 / first bullet`
- Applies to: `possible_pregnancy` `none None–None`
- Jurisdiction: `IN`
- Domains: `followup`
- Dashboard slots: `ask_a_professional, followup`
- General development measurements: `none`
- Future personal facts: `delivery_history, next_appointment`
- Profiles: `PC00`
- Catalogue items: `none`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, clinical, india_localisation`

**Exact selected source text**

> Early diagnosis of pregnancy using Nischay Kits.

**Why it is blocked**

- source awaits actual named approval
- source currency decision is unresolved
- source admission requires review: source currency decision pending or source changed/withdrawn
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- linked guidance wording awaits actual named review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for PC00. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for PC00. Final rendered visual review remains pending.

**Record one decision for each pending reviewer role**

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
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 594728845df724f164a00db77938b36c118f0ff2990d167621e0377f2c325d29
```

### REV-4f9763c7846632db8202

- Evidence: `E-IN-BIRTH-PLAN`
- Locator: `Page 11 / section 3.1 / birth planning bullet`
- Applies to: `pregnancy` `week 4–42`
- Jurisdiction: `IN`
- Domains: `preparation`
- Dashboard slots: `preparation`
- General development measurements: `none`
- Future personal facts: `medical_history, medications_and_supplements, next_appointment`
- Profiles: `P09, P10, P24, P36`
- Catalogue items: `none`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, clinical, india_localisation`

**Exact selected source text**

> Support in birth planning and birth preparedness including birth companion of choice.

**Why it is blocked**

- source awaits actual named approval
- source currency decision is unresolved
- source admission requires review: source currency decision pending or source changed/withdrawn
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- linked guidance wording awaits actual named review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for P10. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for P10. Final rendered visual review remains pending.

**Record one decision for each pending reviewer role**

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
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 4f9763c7846632db820200eb31d369cfb0967eff2f684fb35d009126d53d3964
```

### REV-77cd641c40cd2ef04a5e

- Evidence: `E-IN-PP-FOLLOWUP`
- Locator: `Page 11 / 3.1 / complete PNC home-visit bullet`
- Applies to: `postpartum` `week 6–6`
- Jurisdiction: `IN`
- Domains: `followup`
- Dashboard slots: `ask_a_professional, followup, hero`
- General development measurements: `none`
- Future personal facts: `delivery_history, next_appointment`
- Profiles: `PP06`
- Catalogue items: `none`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, content, clinical, india_localisation, product`

**Exact selected source text**

> Ensuring PNC home visits for delivered women (Institutional Delivery) on 3rd, 7th,14th, 21st, 28th and 42nd Day (6 Visits) and in case of Home Delivery follow up to be done on 1st, 3rd, 7th, 14th, 21st, 28th and 42nd Day (7 Visits).

**Why it is blocked**

- source awaits actual named approval
- source currency decision is unresolved
- source admission requires review: source currency decision pending or source changed/withdrawn
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- linked guidance wording awaits actual named review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- None.

**Record one decision for each pending reviewer role**

```text
Task ID: REV-77cd641c40cd2ef04a5e
Candidate ID: C-E-IN-PP-FOLLOWUP
Evidence ID: E-IN-PP-FOLLOWUP
Source ID: NHM-CHO
Role: licence | content | clinical | india_localisation | product
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 77cd641c40cd2ef04a5e4bfa85b5750417b8551193321b19d38eb4adb5bb1290
```

### REV-059cacced965f62696c7

- Evidence: `E-IN-REGISTRATION`
- Locator: `Page 11 / 3.1 / registration bullet`
- Applies to: `pregnancy` `week 4–12`
- Jurisdiction: `IN`
- Domains: `followup`
- Dashboard slots: `ask_a_professional, followup`
- General development measurements: `none`
- Future personal facts: `delivery_history, next_appointment, pregnancy_confirmation`
- Profiles: `P09, P10`
- Catalogue items: `ANC-REGISTER`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, clinical, india_localisation`

**Exact selected source text**

> Registration of all the pregnant women in the first trimester of pregnancy.

**Why it is blocked**

- source awaits actual named approval
- source currency decision is unresolved
- source admission requires review: source currency decision pending or source changed/withdrawn
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- linked guidance wording awaits actual named review and publication
- linked recommendation catalogue item awaits review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for P10. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for P10. Final rendered visual review remains pending.

**Record one decision for each pending reviewer role**

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
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 059cacced965f62696c7831fc27d2e43068cd88d031d9c2cfa14742655ec3fa1
```

### REV-bfb237dc232c8b309fd9

- Evidence: `E-IN-ANC-VISITS`
- Locator: `Page 11 / 3.1 / antenatal-check bullet`
- Applies to: `pregnancy` `week 4–42`
- Jurisdiction: `IN`
- Domains: `followup`
- Dashboard slots: `followup`
- General development measurements: `none`
- Future personal facts: `delivery_history, next_appointment`
- Profiles: `none`
- Catalogue items: `ANC-CHECKS`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, content, clinical, india_localisation, product`

**Exact selected source text**

> Ensuring four antenatal care checks in VHSND.

**Why it is blocked**

- source awaits actual named approval
- source currency decision is unresolved
- source admission requires review: source currency decision pending or source changed/withdrawn
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- linked guidance wording awaits actual named review and publication
- linked recommendation catalogue item awaits review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- None.

**Record one decision for each pending reviewer role**

```text
Task ID: REV-bfb237dc232c8b309fd9
Candidate ID: C-E-IN-ANC-VISITS
Evidence ID: E-IN-ANC-VISITS
Source ID: NHM-CHO
Role: licence | content | clinical | india_localisation | product
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: bfb237dc232c8b309fd96459eef45faa3f1369123f7fcba141a0321603c34a37
```

### REV-a62372f158dfc78f74e4

- Evidence: `E-IN-ANC-TESTS`
- Locator: `Page 11 / 3.1 / testing bullet`
- Applies to: `pregnancy` `week 4–42`
- Jurisdiction: `IN`
- Domains: `followup`
- Dashboard slots: `ask_a_professional, followup`
- General development measurements: `none`
- Future personal facts: `delivery_history, next_appointment`
- Profiles: `P09, P10, P24, P36`
- Catalogue items: `ANC-CHECKS`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, clinical, india_localisation`

**Exact selected source text**

> Test all pregnant women for urine (albumin and sugar), haemoglobin, syphilis, HIV and blood grouping.

**Why it is blocked**

- source awaits actual named approval
- source currency decision is unresolved
- source admission requires review: source currency decision pending or source changed/withdrawn
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- linked guidance wording awaits actual named review and publication
- linked recommendation catalogue item awaits review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for P10. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for P10. Final rendered visual review remains pending.

**Record one decision for each pending reviewer role**

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
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: a62372f158dfc78f74e47089c72eb44569f8ca6ff8ff17080dc468a7355fc15c
```

### REV-43a4e97d1f66c5c8b312

- Evidence: `E-IN-PNC-DAYS`
- Locator: `Page 11 / 3.1 / complete PNC home-visit bullet / day scope`
- Applies to: `postpartum` `day 0–7`
- Jurisdiction: `IN`
- Domains: `followup`
- Dashboard slots: `followup`
- General development measurements: `none`
- Future personal facts: `delivery_history, next_appointment`
- Profiles: `none`
- Catalogue items: `none`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, content, clinical, india_localisation, product`

**Exact selected source text**

> Ensuring PNC home visits for delivered women (Institutional Delivery) on 3rd, 7th,14th, 21st, 28th and 42nd Day (6 Visits) and in case of Home Delivery follow up to be done on 1st, 3rd, 7th, 14th, 21st, 28th and 42nd Day (7 Visits).

**Why it is blocked**

- source awaits actual named approval
- source currency decision is unresolved
- source admission requires review: source currency decision pending or source changed/withdrawn
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- linked guidance wording awaits actual named review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- None.

**Record one decision for each pending reviewer role**

```text
Task ID: REV-43a4e97d1f66c5c8b312
Candidate ID: C-E-IN-PNC-DAYS
Evidence ID: E-IN-PNC-DAYS
Source ID: NHM-CHO
Role: licence | content | clinical | india_localisation | product
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 43a4e97d1f66c5c8b312e0ce647df07df604412b56effb47a5518ad5e6e00bc2
```

### REV-2838a25b0435a21e3130

- Evidence: `E-IN-PNC-WEEKS`
- Locator: `Page 11 / 3.1 / complete PNC home-visit bullet / week scope`
- Applies to: `postpartum` `week 1–6`
- Jurisdiction: `IN`
- Domains: `followup`
- Dashboard slots: `followup`
- General development measurements: `none`
- Future personal facts: `delivery_history, delivery_place, next_appointment`
- Profiles: `none`
- Catalogue items: `PNC-DAY-1, PNC-DAY-14, PNC-DAY-21, PNC-DAY-28, PNC-DAY-3, PNC-DAY-42, PNC-DAY-7`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, content, clinical, india_localisation, product`

**Exact selected source text**

> Ensuring PNC home visits for delivered women (Institutional Delivery) on 3rd, 7th,14th, 21st, 28th and 42nd Day (6 Visits) and in case of Home Delivery follow up to be done on 1st, 3rd, 7th, 14th, 21st, 28th and 42nd Day (7 Visits).

**Why it is blocked**

- source awaits actual named approval
- source currency decision is unresolved
- source admission requires review: source currency decision pending or source changed/withdrawn
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- linked guidance wording awaits actual named review and publication
- linked recommendation catalogue item awaits review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- None.

**Record one decision for each pending reviewer role**

```text
Task ID: REV-2838a25b0435a21e3130
Candidate ID: C-E-IN-PNC-WEEKS
Evidence ID: E-IN-PNC-WEEKS
Source ID: NHM-CHO
Role: licence | content | clinical | india_localisation | product
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 2838a25b0435a21e3130cb6b71f31da55f3e72f6c65a80c52a1f10db13385f82
```

### REV-a842861ca186c2d3a431

- Evidence: `E-IN-PNC-DAY1`
- Locator: `Page 11 / complete PNC schedule / selected day 1`
- Applies to: `postpartum` `day 1–1`
- Jurisdiction: `IN`
- Domains: `followup`
- Dashboard slots: `ask_a_professional, followup`
- General development measurements: `none`
- Future personal facts: `delivery_history, delivery_place, next_appointment`
- Profiles: `PPD1`
- Catalogue items: `none`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, content, clinical, india_localisation, product`

**Exact selected source text**

> Ensuring PNC home visits for delivered women (Institutional Delivery) on 3rd, 7th,14th, 21st, 28th and 42nd Day (6 Visits) and in case of Home Delivery follow up to be done on 1st, 3rd, 7th, 14th, 21st, 28th and 42nd Day (7 Visits).

**Why it is blocked**

- source awaits actual named approval
- source currency decision is unresolved
- source admission requires review: source currency decision pending or source changed/withdrawn
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- linked guidance wording awaits actual named review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- None.

**Record one decision for each pending reviewer role**

```text
Task ID: REV-a842861ca186c2d3a431
Candidate ID: C-E-IN-PNC-DAY1
Evidence ID: E-IN-PNC-DAY1
Source ID: NHM-CHO
Role: licence | content | clinical | india_localisation | product
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: a842861ca186c2d3a4313a5a69f8fbe9d41405d573ce2c795239747083d961eb
```

### REV-3a6caf113d05d8188702

- Evidence: `E-IN-PNC-DAY3`
- Locator: `Page 11 / complete PNC schedule / selected day 3`
- Applies to: `postpartum` `day 3–3`
- Jurisdiction: `IN`
- Domains: `followup`
- Dashboard slots: `ask_a_professional, followup`
- General development measurements: `none`
- Future personal facts: `delivery_history, next_appointment`
- Profiles: `PPD3`
- Catalogue items: `none`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, content, clinical, india_localisation, product`

**Exact selected source text**

> Ensuring PNC home visits for delivered women (Institutional Delivery) on 3rd, 7th,14th, 21st, 28th and 42nd Day (6 Visits) and in case of Home Delivery follow up to be done on 1st, 3rd, 7th, 14th, 21st, 28th and 42nd Day (7 Visits).

**Why it is blocked**

- source awaits actual named approval
- source currency decision is unresolved
- source admission requires review: source currency decision pending or source changed/withdrawn
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- linked guidance wording awaits actual named review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- None.

**Record one decision for each pending reviewer role**

```text
Task ID: REV-3a6caf113d05d8188702
Candidate ID: C-E-IN-PNC-DAY3
Evidence ID: E-IN-PNC-DAY3
Source ID: NHM-CHO
Role: licence | content | clinical | india_localisation | product
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 3a6caf113d05d81887020ccc6b81a9bdad8db5f82198a3e63fb5024f97eab0e9
```

### REV-a96a1155952b4ce2daa8

- Evidence: `E-IN-PNC-DAY7`
- Locator: `Page 11 / complete PNC schedule / selected day 7`
- Applies to: `postpartum` `day 7–7`
- Jurisdiction: `IN`
- Domains: `followup`
- Dashboard slots: `ask_a_professional, followup`
- General development measurements: `none`
- Future personal facts: `delivery_history, next_appointment`
- Profiles: `PPD7`
- Catalogue items: `none`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, content, clinical, india_localisation, product`

**Exact selected source text**

> Ensuring PNC home visits for delivered women (Institutional Delivery) on 3rd, 7th,14th, 21st, 28th and 42nd Day (6 Visits) and in case of Home Delivery follow up to be done on 1st, 3rd, 7th, 14th, 21st, 28th and 42nd Day (7 Visits).

**Why it is blocked**

- source awaits actual named approval
- source currency decision is unresolved
- source admission requires review: source currency decision pending or source changed/withdrawn
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- linked guidance wording awaits actual named review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- None.

**Record one decision for each pending reviewer role**

```text
Task ID: REV-a96a1155952b4ce2daa8
Candidate ID: C-E-IN-PNC-DAY7
Evidence ID: E-IN-PNC-DAY7
Source ID: NHM-CHO
Role: licence | content | clinical | india_localisation | product
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: a96a1155952b4ce2daa8c2d82d0e499c3d3d135a1656f45fba59994a8353a413
```


A checked box in this exported document does not change publication state. The named decision must be entered into the governed source, evidence, fragment, profile and catalogue records, then the ingestion run must be repeated. Machine-readable decisions belong in data/reviews/ingestion_decisions.json; the ingestion command rejects unknown task IDs and changed checksums.


---

# Ingestion review — NHM-MOTHERHOOD

- Run: `ING-93979f08cfa80927c761`
- Outcome: **review_required**
- Admission: `parse_for_review`
- Source artifact: `e742063ab9f7acd34d5cde160169ad919603f8fe9c0224277091717a4f0f7947`
- Candidate units: 13
- Pending review tasks: 13

## Admission reasons

- source currency decision pending or source changed/withdrawn
- actual source approval is pending
- named source review is pending

## Parser and validation issues

- None.

## Human review queue

### REV-217ecfedf0f1b7f574bf

- Evidence: `E-IN-FOOD`
- Locator: `Page 10 / bottom banner opening`
- Applies to: `pregnancy` `week 1–42`
- Jurisdiction: `IN`
- Domains: `nutrition`
- Dashboard slots: `nutrition_focus`
- General development measurements: `none`
- Future personal facts: `allergies, dietary_restrictions, medical_history`
- Profiles: `P09, P10, P24, P36`
- Catalogue items: `FOOD-FRUIT`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, clinical, india_localisation`

**Exact selected source text**

> Prefer using variety of local seasonal foods, vegetables and fruits

**Why it is blocked**

- source awaits actual named approval
- source currency decision is unresolved
- source admission requires review: source currency decision pending or source changed/withdrawn
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- linked guidance wording awaits actual named review and publication
- linked recommendation catalogue item awaits review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for P10. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for P10. Final rendered visual review remains pending.

**Record one decision for each pending reviewer role**

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
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 217ecfedf0f1b7f574bf5bf542482365d0fcbe4e918aabceafb49f56eaf2fb95
```

### REV-136828c014659afee522

- Evidence: `E-IN-REST-PREG`
- Locator: `Page 12 / Rest during pregnancy / final bullet`
- Applies to: `pregnancy` `week 1–42`
- Jurisdiction: `IN`
- Domains: `movement`
- Dashboard slots: `movement_focus`
- General development measurements: `none`
- Future personal facts: `clinician_activity_instruction, current_symptom_report, medical_history`
- Profiles: `none`
- Catalogue items: `none`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, content, clinical, india_localisation, product`

**Exact selected source text**

> Do not overexert yourself and delegate few tasks to others.

**Why it is blocked**

- source awaits actual named approval
- source currency decision is unresolved
- source admission requires review: source currency decision pending or source changed/withdrawn
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- linked guidance wording awaits actual named review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- None.

**Record one decision for each pending reviewer role**

```text
Task ID: REV-136828c014659afee522
Candidate ID: C-E-IN-REST-PREG
Evidence ID: E-IN-REST-PREG
Source ID: NHM-MOTHERHOOD
Role: licence | content | clinical | india_localisation | product
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 136828c014659afee522ad5a777b94b02bbb3edc65a74fdbbdf2e6a206d003f1
```

### REV-91c6e3f3c23c7774b024

- Evidence: `E-IN-REST-PP`
- Locator: `Page 16 / Postpartum care / rest bullet`
- Applies to: `postpartum` `week 1–6`
- Jurisdiction: `IN`
- Domains: `preparation`
- Dashboard slots: `hero, preparation`
- General development measurements: `none`
- Future personal facts: `medical_history, medications_and_supplements, next_appointment`
- Profiles: `PP01, PP06`
- Catalogue items: `none`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, clinical, india_localisation`

**Exact selected source text**

> Take adequate rest.

**Why it is blocked**

- source awaits actual named approval
- source currency decision is unresolved
- source admission requires review: source currency decision pending or source changed/withdrawn
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- linked guidance wording awaits actual named review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for PP01. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for PP01. Final rendered visual review remains pending.

**Record one decision for each pending reviewer role**

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
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 91c6e3f3c23c7774b0244eab55107722904712947b54155f79f5433cb38c38b5
```

### REV-d5a69ed18c2ed1936b2e

- Evidence: `E-IN-FOOD-DAIRY`
- Locator: `Page 9 / dairy bullet`
- Applies to: `pregnancy` `week 4–42`
- Jurisdiction: `IN`
- Domains: `nutrition`
- Dashboard slots: `nutrition_focus`
- General development measurements: `none`
- Future personal facts: `allergies, dietary_restrictions, medical_history`
- Profiles: `none`
- Catalogue items: `FOOD-CURD, FOOD-MILK, FOOD-PANEER`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, content, clinical, india_localisation, product`

**Exact selected source text**

> Take milk and dairy products like curd, buttermilk, paneer-these are rich in calcium, proteins and vitamins.

**Why it is blocked**

- source awaits actual named approval
- source currency decision is unresolved
- source admission requires review: source currency decision pending or source changed/withdrawn
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- linked guidance wording awaits actual named review and publication
- linked recommendation catalogue item awaits review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- None.

**Record one decision for each pending reviewer role**

```text
Task ID: REV-d5a69ed18c2ed1936b2e
Candidate ID: C-E-IN-FOOD-DAIRY
Evidence ID: E-IN-FOOD-DAIRY
Source ID: NHM-MOTHERHOOD
Role: licence | content | clinical | india_localisation | product
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: d5a69ed18c2ed1936b2eb44b51edd708047af8c2a68f19c5dd39a2801a0ac574
```

### REV-1c40d463148587f7f2ed

- Evidence: `E-IN-FOOD-GRAINS`
- Locator: `Page 9 / cereals and pulses sentence`
- Applies to: `pregnancy` `week 4–42`
- Jurisdiction: `IN`
- Domains: `nutrition`
- Dashboard slots: `nutrition_focus`
- General development measurements: `none`
- Future personal facts: `allergies, dietary_restrictions, medical_history`
- Profiles: `P09, P10, P24, P36`
- Catalogue items: `FOOD-GRAINS, FOOD-PULSES`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, clinical, india_localisation`

**Exact selected source text**

> Cereals, whole grains and pulses are good sources of proteins.

**Why it is blocked**

- source awaits actual named approval
- source currency decision is unresolved
- source admission requires review: source currency decision pending or source changed/withdrawn
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- linked guidance wording awaits actual named review and publication
- linked recommendation catalogue item awaits review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for P10. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for P10. Final rendered visual review remains pending.

**Record one decision for each pending reviewer role**

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
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 1c40d463148587f7f2edaae2dda632582b4b7abaa3a63e0ec1bf6b40cabb9888
```

### REV-3e0ef5cc691249acf89e

- Evidence: `E-IN-FOOD-GREENS`
- Locator: `Page 9 / leafy-vegetables bullet`
- Applies to: `pregnancy` `week 4–42`
- Jurisdiction: `IN`
- Domains: `nutrition`
- Dashboard slots: `nutrition_focus`
- General development measurements: `none`
- Future personal facts: `allergies, dietary_restrictions, medical_history`
- Profiles: `P09, P10, P24, P36`
- Catalogue items: `FOOD-GREENS`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, clinical, india_localisation`

**Exact selected source text**

> Green leafy vegetables are a rich source of iron and folic acid.

**Why it is blocked**

- source awaits actual named approval
- source currency decision is unresolved
- source admission requires review: source currency decision pending or source changed/withdrawn
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- linked guidance wording awaits actual named review and publication
- linked recommendation catalogue item awaits review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for P10. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for P10. Final rendered visual review remains pending.

**Record one decision for each pending reviewer role**

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
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 3e0ef5cc691249acf89e932999f87097907a56edba7e1422c4cebbdb8e080cab
```

### REV-8a03e0bb56284628b8e5

- Evidence: `E-IN-FOOD-ANIMAL`
- Locator: `Page 9 / non-vegetarian sources bullet`
- Applies to: `pregnancy` `week 4–42`
- Jurisdiction: `IN`
- Domains: `nutrition`
- Dashboard slots: `nutrition_focus`
- General development measurements: `none`
- Future personal facts: `allergies, dietary_restrictions, medical_history`
- Profiles: `none`
- Catalogue items: `FOOD-CHICKEN, FOOD-EGG, FOOD-FISH`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, content, clinical, india_localisation, product`

**Exact selected source text**

> For non-vegetarians, meat, egg, chicken or fish are good sources of proteins, vitamins and iron.

**Why it is blocked**

- source awaits actual named approval
- source currency decision is unresolved
- source admission requires review: source currency decision pending or source changed/withdrawn
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- linked guidance wording awaits actual named review and publication
- linked recommendation catalogue item awaits review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- None.

**Record one decision for each pending reviewer role**

```text
Task ID: REV-8a03e0bb56284628b8e5
Candidate ID: C-E-IN-FOOD-ANIMAL
Evidence ID: E-IN-FOOD-ANIMAL
Source ID: NHM-MOTHERHOOD
Role: licence | content | clinical | india_localisation | product
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 8a03e0bb56284628b8e54dbfd14cf0639d93a2e87f43176b9173c9f576357423
```

### REV-bcc5338f9278b909988f

- Evidence: `E-IN-FOOD-PLANTS`
- Locator: `Page 10 / proteins row`
- Applies to: `pregnancy` `week 4–42`
- Jurisdiction: `IN`
- Domains: `nutrition`
- Dashboard slots: `nutrition_focus`
- General development measurements: `none`
- Future personal facts: `allergies, dietary_restrictions, medical_history`
- Profiles: `none`
- Catalogue items: `FOOD-NUTS, FOOD-SOYA`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, content, clinical, india_localisation, product`

**Exact selected source text**

> Paneer, milk and other milk products, combined grains, seeds, nuts, egg, meat, poultry, soya beans.

**Why it is blocked**

- source awaits actual named approval
- source currency decision is unresolved
- source admission requires review: source currency decision pending or source changed/withdrawn
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- linked guidance wording awaits actual named review and publication
- linked recommendation catalogue item awaits review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- None.

**Record one decision for each pending reviewer role**

```text
Task ID: REV-bcc5338f9278b909988f
Candidate ID: C-E-IN-FOOD-PLANTS
Evidence ID: E-IN-FOOD-PLANTS
Source ID: NHM-MOTHERHOOD
Role: licence | content | clinical | india_localisation | product
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: bcc5338f9278b909988fa2fc7c9958bfadd7c4e0b7df6a88cef1e379e25ab726
```

### REV-ffed1ea90fb72457a063

- Evidence: `E-IN-PP-DAY0`
- Locator: `Page 16 / day-of-delivery follow-up bullet`
- Applies to: `postpartum` `day 0–0`
- Jurisdiction: `IN`
- Domains: `followup`
- Dashboard slots: `ask_a_professional, followup`
- General development measurements: `none`
- Future personal facts: `delivery_history, next_appointment`
- Profiles: `PPD0`
- Catalogue items: `none`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, content, clinical, india_localisation, product`

**Exact selected source text**

> You and your baby should be seen by a health worker on the day of delivery, and on 3rd day, 7th day and 6 weeks after delivery.

**Why it is blocked**

- source awaits actual named approval
- source currency decision is unresolved
- source admission requires review: source currency decision pending or source changed/withdrawn
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- linked guidance wording awaits actual named review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- None.

**Record one decision for each pending reviewer role**

```text
Task ID: REV-ffed1ea90fb72457a063
Candidate ID: C-E-IN-PP-DAY0
Evidence ID: E-IN-PP-DAY0
Source ID: NHM-MOTHERHOOD
Role: licence | content | clinical | india_localisation | product
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: ffed1ea90fb72457a06389b3e9d9d08bbbc7f0ed92f1597309c910de4b79249f
```

### REV-d368d2f53ced8aea14c3

- Evidence: `E-IN-PP-DAY-REST`
- Locator: `Page 16 / postpartum rest bullet / day scope`
- Applies to: `postpartum` `day 0–7`
- Jurisdiction: `IN`
- Domains: `preparation`
- Dashboard slots: `hero, preparation`
- General development measurements: `none`
- Future personal facts: `medical_history, medications_and_supplements, next_appointment`
- Profiles: `PPD0, PPD1, PPD2, PPD3, PPD4, PPD5, PPD6, PPD7`
- Catalogue items: `none`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, content, clinical, india_localisation, product`

**Exact selected source text**

> Take adequate rest.

**Why it is blocked**

- source awaits actual named approval
- source currency decision is unresolved
- source admission requires review: source currency decision pending or source changed/withdrawn
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- linked guidance wording awaits actual named review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- None.

**Record one decision for each pending reviewer role**

```text
Task ID: REV-d368d2f53ced8aea14c3
Candidate ID: C-E-IN-PP-DAY-REST
Evidence ID: E-IN-PP-DAY-REST
Source ID: NHM-MOTHERHOOD
Role: licence | content | clinical | india_localisation | product
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: d368d2f53ced8aea14c3558a531d2dfc23f39501756348456baac8614cf16ab5
```

### REV-3b722f2c58264d6e7dcf

- Evidence: `E-IN-PP-DAY-HELP`
- Locator: `Page 16 / immediate-help bullet`
- Applies to: `postpartum` `day 0–7`
- Jurisdiction: `IN`
- Domains: `symptoms`
- Dashboard slots: `symptom_education`
- General development measurements: `none`
- Future personal facts: `current_symptom_report, medical_history`
- Profiles: `PPD0, PPD1, PPD2, PPD3, PPD4, PPD5, PPD6, PPD7`
- Catalogue items: `none`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, content, clinical, india_localisation, product`

**Exact selected source text**

> Take immediate medical help if any complication occurs in yourself or your baby.

**Why it is blocked**

- source awaits actual named approval
- source currency decision is unresolved
- source admission requires review: source currency decision pending or source changed/withdrawn
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- linked guidance wording awaits actual named review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- None.

**Record one decision for each pending reviewer role**

```text
Task ID: REV-3b722f2c58264d6e7dcf
Candidate ID: C-E-IN-PP-DAY-HELP
Evidence ID: E-IN-PP-DAY-HELP
Source ID: NHM-MOTHERHOOD
Role: licence | content | clinical | india_localisation | product
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 3b722f2c58264d6e7dcf65cd89ff5c969491c2a5692d8875caa1dc6d1670267d
```

### REV-dff84e7ca466288bfe4c

- Evidence: `E-IN-PREG-WARNINGS`
- Locator: `Page 14 / pregnancy danger signals and immediate-help instruction`
- Applies to: `pregnancy` `week 4–42`
- Jurisdiction: `IN`
- Domains: `symptoms`
- Dashboard slots: `symptom_education`
- General development measurements: `none`
- Future personal facts: `current_symptom_report, medical_history`
- Profiles: `none`
- Catalogue items: `none`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, content, clinical, india_localisation, product`

**Exact selected source text**

> If any complications occur- seek help immediately to preserve your health and life. DANGER SIGNALS DURING PREGNANCY. Generalised weakness, easy fatigability and breathlessness. Severe pain in abdomen. Bleeding per vaginum. Excessive swelling in legs. Fever. Convulsions.

**Why it is blocked**

- source awaits actual named approval
- source currency decision is unresolved
- source admission requires review: source currency decision pending or source changed/withdrawn
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- linked guidance wording awaits actual named review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- None.

**Record one decision for each pending reviewer role**

```text
Task ID: REV-dff84e7ca466288bfe4c
Candidate ID: C-E-IN-PREG-WARNINGS
Evidence ID: E-IN-PREG-WARNINGS
Source ID: NHM-MOTHERHOOD
Role: licence | content | clinical | india_localisation | product
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: dff84e7ca466288bfe4c70d3741e908651c9ec2d3c3ff7b8456e2eb514496583
```

### REV-9c831475bbccd05a809b

- Evidence: `E-IN-PP-WARNINGS`
- Locator: `Page 16 / immediate-help instruction and Contact FRU list`
- Applies to: `postpartum` `week 1–12`
- Jurisdiction: `IN`
- Domains: `symptoms`
- Dashboard slots: `symptom_education`
- General development measurements: `none`
- Future personal facts: `current_symptom_report, medical_history`
- Profiles: `none`
- Catalogue items: `none`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, content, clinical, india_localisation, product`

**Exact selected source text**

> Take immediate medical help if any complication occurs in yourself or your baby. Contact F R U. Excessive vaginal bleeding. Inability to control defecation/urine. Foul smelling vaginal discharge. Difficulty in breathing. Blurred vision and fits. Fever. Fainting.

**Why it is blocked**

- source awaits actual named approval
- source currency decision is unresolved
- source admission requires review: source currency decision pending or source changed/withdrawn
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- linked guidance wording awaits actual named review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- None.

**Record one decision for each pending reviewer role**

```text
Task ID: REV-9c831475bbccd05a809b
Candidate ID: C-E-IN-PP-WARNINGS
Evidence ID: E-IN-PP-WARNINGS
Source ID: NHM-MOTHERHOOD
Role: licence | content | clinical | india_localisation | product
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 9c831475bbccd05a809b5cfb2327860a8e39dc91876c4ad8fd121cd72b0443c8
```


A checked box in this exported document does not change publication state. The named decision must be entered into the governed source, evidence, fragment, profile and catalogue records, then the ingestion run must be repeated. Machine-readable decisions belong in data/reviews/ingestion_decisions.json; the ingestion command rejects unknown task IDs and changed checksums.


---

# Ingestion review — NHS-PP-ACTIVE

- Run: `ING-32846075a7825f5dd858`
- Outcome: **review_required**
- Admission: `parse_for_review`
- Source artifact: `9bd10674595457997dd4e72da0e4d143d887fb9a11fe144e09f607c2d8073bb5`
- Candidate units: 6
- Pending review tasks: 6

## Admission reasons

- actual source approval is pending
- named source review is pending

## Parser and validation issues

- None.

## Human review queue

### REV-d7a6ab35600616505571

- Evidence: `E-PP-MOVEMENT-QUESTION`
- Locator: `When can I start exercising after birth? / complete complicated-delivery paragraph`
- Applies to: `postpartum` `week 1–12`
- Jurisdiction: `IN`
- Domains: `movement`
- Dashboard slots: `movement_focus`
- General development measurements: `none`
- Future personal facts: `clinician_activity_instruction, current_symptom_report, delivery_history, medical_history`
- Profiles: `PP01, PP06, PP12`
- Catalogue items: `MOVE-PP-CONSULT`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, clinical, india_localisation`

**Exact selected source text**

> If you had a more complicated delivery or a caesarean, your recovery time will be longer. Talk to your midwife, health visitor or GP before starting anything strenuous.

**Why it is blocked**

- source awaits actual named approval
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- India localisation awaits actual named review
- linked guidance wording awaits actual named review and publication
- linked recommendation catalogue item awaits review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for PP01. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for PP01. Final rendered visual review remains pending.

**Record one decision for each pending reviewer role**

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
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: d7a6ab35600616505571507fb9876075ec4625240a3211f44180e7411df452c6
```

### REV-ab9c6a8121188e53c181

- Evidence: `E-PP-MIND-REST`
- Locator: `Look after your mental health / first bullet`
- Applies to: `postpartum` `week 1–12`
- Jurisdiction: `IN`
- Domains: `wellbeing`
- Dashboard slots: `hero, wellbeing_focus`
- General development measurements: `none`
- Future personal facts: `current_emotional_concern, current_symptom_report, mental_health_history, user_consent`
- Profiles: `PP01, PP06, PP12`
- Catalogue items: `WELL-PP-REST`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, clinical, india_localisation`

**Exact selected source text**

> making time to rest

**Why it is blocked**

- source awaits actual named approval
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- India localisation awaits actual named review
- linked guidance wording awaits actual named review and publication
- linked recommendation catalogue item awaits review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for PP01. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for PP01. Final rendered visual review remains pending.

**Record one decision for each pending reviewer role**

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
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: ab9c6a8121188e53c18158c749086d9ebca22b773c97c6ad3f7173313c9fd87d
```

### REV-cede4dd7a7d4cb23f32a

- Evidence: `E-PP-MIND-TALK`
- Locator: `Look after your mental health / final bullet`
- Applies to: `postpartum` `week 1–12`
- Jurisdiction: `IN`
- Domains: `wellbeing`
- Dashboard slots: `wellbeing_focus`
- General development measurements: `none`
- Future personal facts: `current_emotional_concern, current_symptom_report, mental_health_history, user_consent`
- Profiles: `PP01, PP06, PP12`
- Catalogue items: `WELL-PP-TALK`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, clinical, india_localisation`

**Exact selected source text**

> talking to people about your feelings

**Why it is blocked**

- source awaits actual named approval
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- India localisation awaits actual named review
- linked guidance wording awaits actual named review and publication
- linked recommendation catalogue item awaits review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for PP01. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for PP01. Final rendered visual review remains pending.

**Record one decision for each pending reviewer role**

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
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: cede4dd7a7d4cb23f32a6f52c23dbe87d53831ddadb4f558436b75072d798d65
```

### REV-d55e6eaf9fa6a3910659

- Evidence: `E-PP-GENTLE-MOVEMENT`
- Locator: `When can I start exercising after birth? / straightforward-birth paragraph`
- Applies to: `postpartum` `week 1–12`
- Jurisdiction: `IN`
- Domains: `movement`
- Dashboard slots: `movement_focus`
- General development measurements: `none`
- Future personal facts: `clinician_activity_instruction, current_symptom_report, delivery_history, medical_history, user_reported_activity_readiness`
- Profiles: `PP01, PP06, PP12`
- Catalogue items: `MOVE-PP-STRETCH, MOVE-PP-WALK`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, clinical, india_localisation`

**Exact selected source text**

> If you had a straightforward birth, you can start gentle exercise as soon as you feel up to it. This could include walking, gentle stretches and pelvic floor exercises.

**Why it is blocked**

- source awaits actual named approval
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- India localisation awaits actual named review
- linked guidance wording awaits actual named review and publication
- linked recommendation catalogue item awaits review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for PP01. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for PP01. Final rendered visual review remains pending.

**Record one decision for each pending reviewer role**

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
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: d55e6eaf9fa6a39106598cae888a628d17d77eb2059f8b8ff746c0c29fb823c2
```

### REV-08627e8fd9c2176f011c

- Evidence: `E-PP-PERSISTENT-CONCERN`
- Locator: `Look after your mental health / concern paragraph`
- Applies to: `postpartum` `week 1–12`
- Jurisdiction: `IN`
- Domains: `wellbeing`
- Dashboard slots: `ask_a_professional`
- General development measurements: `none`
- Future personal facts: `current_emotional_concern, mental_health_history, user_consent`
- Profiles: `PP01, PP06, PP12`
- Catalogue items: `none`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, clinical, india_localisation`

**Exact selected source text**

> If you're worried about how you're feeling, feel like you're struggling to cope, or think you may be depressed, it's important that you talk to your midwife, health visitor or GP. Effective help is available.

**Why it is blocked**

- source awaits actual named approval
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- India localisation awaits actual named review
- linked guidance wording awaits actual named review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for PP01. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for PP01. Final rendered visual review remains pending.

**Record one decision for each pending reviewer role**

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
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 08627e8fd9c2176f011c541774b0a659696fdabdf52799d821795fac58968b48
```

### REV-fc7b4ad5e946d2871f88

- Evidence: `E-PP-ASK-HELP`
- Locator: `Look after your mental health / help and rest bullets`
- Applies to: `postpartum` `week 1–12`
- Jurisdiction: `IN`
- Domains: `wellbeing`
- Dashboard slots: `wellbeing_focus`
- General development measurements: `none`
- Future personal facts: `current_emotional_concern, current_symptom_report, mental_health_history, user_consent`
- Profiles: `PP01, PP06, PP12`
- Catalogue items: `WELL-PP-KINDNESS`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, clinical, india_localisation`

**Exact selected source text**

> making time to rest. not trying to "do it all". accepting help with caring for your baby from friends, family or your partner.

**Why it is blocked**

- source awaits actual named approval
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- India localisation awaits actual named review
- linked guidance wording awaits actual named review and publication
- linked recommendation catalogue item awaits review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for PP01. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for PP01. Final rendered visual review remains pending.

**Record one decision for each pending reviewer role**

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
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: fc7b4ad5e946d2871f8801929ab8590d1b7416ae6d3d491847ba27f3b88be048
```


A checked box in this exported document does not change publication state. The named decision must be entered into the governed source, evidence, fragment, profile and catalogue records, then the ingestion run must be repeated. Machine-readable decisions belong in data/reviews/ingestion_decisions.json; the ingestion command rejects unknown task IDs and changed checksums.


---

# Ingestion review — NHS-PP-BODY

- Run: `ING-52057b06226fd63f59df`
- Outcome: **review_required**
- Admission: `parse_for_review`
- Source artifact: `b1b4b1cebc59418b4d17c81636bc28ff515dc340ad7456af410668d92d011c1b`
- Candidate units: 1
- Pending review tasks: 1

## Admission reasons

- actual source approval is pending
- named source review is pending

## Parser and validation issues

- None.

## Human review queue

### REV-76223b6e3db0177d3034

- Evidence: `E-PP-FERTILITY`
- Locator: `How soon after giving birth can I get pregnant? / first clause / expanded supporting unit`
- Applies to: `postpartum` `week 3–12`
- Jurisdiction: `IN`
- Domains: `journey`
- Dashboard slots: `what_may_change`
- General development measurements: `none`
- Future personal facts: `confirmed_journey_timing`
- Profiles: `PP06, PP12`
- Catalogue items: `none`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, content, clinical, india_localisation, product`

**Exact selected source text**

> You can get pregnant again just 3 weeks after the birth of your baby, even if you're breastfeeding and your periods have not started again yet.

**Why it is blocked**

- source awaits actual named approval
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- India localisation awaits actual named review
- linked guidance wording awaits actual named review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- None.

**Record one decision for each pending reviewer role**

```text
Task ID: REV-76223b6e3db0177d3034
Candidate ID: C-E-PP-FERTILITY
Evidence ID: E-PP-FERTILITY
Source ID: NHS-PP-BODY
Role: licence | content | clinical | india_localisation | product
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 76223b6e3db0177d303455e3ea6c78d0bdd5a5d366d479b8c6a1f804e57633da
```


A checked box in this exported document does not change publication state. The named decision must be entered into the governed source, evidence, fragment, profile and catalogue records, then the ingestion run must be repeated. Machine-readable decisions belong in data/reviews/ingestion_decisions.json; the ingestion command rejects unknown task IDs and changed checksums.


---

# Ingestion review — NHS-PP-DIET

- Run: `ING-0a944fc2b3e6637fdcd8`
- Outcome: **review_required**
- Admission: `parse_for_review`
- Source artifact: `d57259b4a5d35255b48b56618747b685f7c993d58bcb09ee0c36c2aacd5405b0`
- Candidate units: 1
- Pending review tasks: 1

## Admission reasons

- actual source approval is pending
- named source review is pending

## Parser and validation issues

- None.

## Human review queue

### REV-7e9058cc6079480b1a62

- Evidence: `E-PP-DIET`
- Locator: `Introduction / first sentence`
- Applies to: `postpartum` `week 1–12`
- Jurisdiction: `IN`
- Domains: `nutrition`
- Dashboard slots: `nutrition_focus`
- General development measurements: `none`
- Future personal facts: `allergies, dietary_restrictions, feeding_status, medical_history`
- Profiles: `PP01, PP06, PP12`
- Catalogue items: `none`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, clinical, india_localisation`

**Exact selected source text**

> You do not need to follow a special diet while you're breastfeeding.

**Why it is blocked**

- source awaits actual named approval
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- India localisation awaits actual named review
- linked guidance wording awaits actual named review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for PP01. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for PP01. Final rendered visual review remains pending.

**Record one decision for each pending reviewer role**

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
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 7e9058cc6079480b1a62bcfaeddf2373274a4a1e3027771c72ce46d3ad23b647
```


A checked box in this exported document does not change publication state. The named decision must be entered into the governed source, evidence, fragment, profile and catalogue records, then the ingestion run must be repeated. Machine-readable decisions belong in data/reviews/ingestion_decisions.json; the ingestion command rejects unknown task IDs and changed checksums.


---

# Ingestion review — NHS-PP-SUPPORT

- Run: `ING-01ecc86ebbe438e80bba`
- Outcome: **review_required**
- Admission: `parse_for_review`
- Source artifact: `fc522a4e81776d1114ea9bb13085de741d36dc1996613f544eae06bb2ade2dac`
- Candidate units: 1
- Pending review tasks: 1

## Admission reasons

- actual source approval is pending
- named source review is pending

## Parser and validation issues

- None.

## Human review queue

### REV-f20e639a975950a1d27a

- Evidence: `E-PP-PRACTICAL-HELP`
- Locator: `Relationships with family and friends / help paragraph opening / expanded supporting unit`
- Applies to: `postpartum` `week 1–12`
- Jurisdiction: `IN`
- Domains: `preparation, wellbeing`
- Dashboard slots: `preparation, wellbeing_focus`
- General development measurements: `none`
- Future personal facts: `current_emotional_concern, current_symptom_report, medical_history, medications_and_supplements, mental_health_history, next_appointment, user_consent`
- Profiles: `PP01, PP06, PP12`
- Catalogue items: `WELL-PP-SUPPORT`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, clinical, india_localisation`

**Exact selected source text**

> It's best to be clear about the kind of help you want, rather than going along with what's offered and feeling resentful.

**Why it is blocked**

- source awaits actual named approval
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- India localisation awaits actual named review
- linked guidance wording awaits actual named review and publication
- linked recommendation catalogue item awaits review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for PP01. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for PP01. Final rendered visual review remains pending.

**Record one decision for each pending reviewer role**

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
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: f20e639a975950a1d27ad1114d72ead0c29a4205c61494870a012a1dcd7104a8
```


A checked box in this exported document does not change publication state. The named decision must be entered into the governed source, evidence, fragment, profile and catalogue records, then the ingestion run must be repeated. Machine-readable decisions belong in data/reviews/ingestion_decisions.json; the ingestion command rejects unknown task IDs and changed checksums.


---

# Ingestion review — NHS-PREG-MIND

- Run: `ING-98d06bc906658216678e`
- Outcome: **review_required**
- Admission: `parse_for_review`
- Source artifact: `c52c37230cb06a99529143c9cb76f1b11ef90bde27d2b09ee0d7cff2e758879b`
- Candidate units: 2
- Pending review tasks: 2

## Admission reasons

- actual source approval is pending
- named source review is pending

## Parser and validation issues

- None.

## Human review queue

### REV-339bc693632d7454391d

- Evidence: `E-PREG-TALK`
- Locator: `Things you can do / Do / feelings bullet`
- Applies to: `pregnancy` `week 1–42`
- Jurisdiction: `IN`
- Domains: `wellbeing`
- Dashboard slots: `wellbeing_focus`
- General development measurements: `none`
- Future personal facts: `current_emotional_concern, current_symptom_report, mental_health_history, user_consent`
- Profiles: `P09, P10, P24, P36`
- Catalogue items: `WELL-PREG-FEELINGS`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, clinical, india_localisation`

**Exact selected source text**

> talk about your feelings to a friend, family member, midwife or doctor

**Why it is blocked**

- source awaits actual named approval
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- India localisation awaits actual named review
- linked guidance wording awaits actual named review and publication
- linked recommendation catalogue item awaits review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for P10. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for P10. Final rendered visual review remains pending.

**Record one decision for each pending reviewer role**

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
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 339bc693632d7454391dba814571af49e04f7af6d4a517a83d60c157adb98036
```

### REV-5efbb9d4c28f4307a7fb

- Evidence: `E-PREG-ENJOY`
- Locator: `Things you can do / Do / enjoyment bullet`
- Applies to: `pregnancy` `week 1–42`
- Jurisdiction: `IN`
- Domains: `wellbeing`
- Dashboard slots: `wellbeing_focus`
- General development measurements: `none`
- Future personal facts: `current_emotional_concern, current_symptom_report, mental_health_history, user_consent`
- Profiles: `P09, P10, P24, P36`
- Catalogue items: `WELL-PREG-ENJOY`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, clinical, india_localisation`

**Exact selected source text**

> try to make time to regularly do something you enjoy

**Why it is blocked**

- source awaits actual named approval
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- India localisation awaits actual named review
- linked guidance wording awaits actual named review and publication
- linked recommendation catalogue item awaits review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for P10. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for P10. Final rendered visual review remains pending.

**Record one decision for each pending reviewer role**

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
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 5efbb9d4c28f4307a7fb6a5e9599631f17307698bee23e2a5f86167a4f9d9b8d
```


A checked box in this exported document does not change publication state. The named decision must be entered into the governed source, evidence, fragment, profile and catalogue records, then the ingestion run must be repeated. Machine-readable decisions belong in data/reviews/ingestion_decisions.json; the ingestion command rejects unknown task IDs and changed checksums.


---

# Ingestion review — OWH-HEALTH

- Run: `ING-92521a99edc0b63e43be`
- Outcome: **review_required**
- Admission: `parse_for_review`
- Source artifact: `10b599352d40e883f8a87ec0d4f5ca588fe05f7b2ab584cb873199f9813b6003`
- Candidate units: 8
- Pending review tasks: 8

## Admission reasons

- actual source approval is pending
- named source review is pending

## Parser and validation issues

- None.

## Human review queue

### REV-d39505d2e4c7e7b722c4

- Evidence: `E-FOOD-HYGIENE`
- Locator: `Food safety / produce bullet`
- Applies to: `pregnancy` `week 1–42`
- Jurisdiction: `IN`
- Domains: `nutrition`
- Dashboard slots: `nutrition_focus`
- General development measurements: `none`
- Future personal facts: `allergies, dietary_restrictions, medical_history`
- Profiles: `P09, P10, P24, P36`
- Catalogue items: `none`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, clinical, india_localisation`

**Exact selected source text**

> Wash produce before eating.

**Why it is blocked**

- source awaits actual named approval
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- India localisation awaits actual named review
- linked guidance wording awaits actual named review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for P10. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for P10. Final rendered visual review remains pending.

**Record one decision for each pending reviewer role**

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
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: d39505d2e4c7e7b722c4be32742e24ec511b3f8db9b53e177d3079b3b3bc199f
```

### REV-9171d005e40390e49409

- Evidence: `E-MOVEMENT-CONSULT`
- Locator: `Getting started / consultation sentence`
- Applies to: `pregnancy` `week 1–42`
- Jurisdiction: `IN`
- Domains: `movement`
- Dashboard slots: `ask_a_professional`
- General development measurements: `none`
- Future personal facts: `clinician_activity_instruction, current_symptom_report, medical_history`
- Profiles: `P09, P10, P24, P36`
- Catalogue items: `none`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, clinical, india_localisation`

**Exact selected source text**

> Even so, talk to your doctor or midwife before exercising during pregnancy.

**Why it is blocked**

- source awaits actual named approval
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- India localisation awaits actual named review
- linked guidance wording awaits actual named review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for P10. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for P10. Final rendered visual review remains pending.

**Record one decision for each pending reviewer role**

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
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 9171d005e40390e4940916e7b2d0f8683aa6e8a163964f9216a6c476df8b9138
```

### REV-fbd3d8038d9175d3dda9

- Evidence: `E-PREG-FOOD-SAFETY`
- Locator: `Food safety / handling instruction and bullets`
- Applies to: `pregnancy` `week 4–42`
- Jurisdiction: `IN`
- Domains: `nutrition`
- Dashboard slots: `nutrition_focus`
- General development measurements: `none`
- Future personal facts: `allergies, dietary_restrictions, medical_history`
- Profiles: `none`
- Catalogue items: `FOOD-CHICKEN, FOOD-CURD, FOOD-EGG, FOOD-FISH, FOOD-FRUIT, FOOD-GRAINS, FOOD-GREENS, FOOD-MILK, FOOD-NUTS, FOOD-PANEER, FOOD-PULSES, FOOD-SOYA`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, content, clinical, india_localisation, product`

**Exact selected source text**

> Clean, handle, cook, and chill food properly to prevent foodborne illness, including listeria and toxoplasmosis. Wash hands with soap after touching soil or raw meat. Keep raw meats, poultry, and seafood from touching other foods or surfaces. Cook meat completely. Wash produce before eating. Wash cooking utensils with hot, soapy water.

**Why it is blocked**

- source awaits actual named approval
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- India localisation awaits actual named review
- linked guidance wording awaits actual named review and publication
- linked recommendation catalogue item awaits review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- None.

**Record one decision for each pending reviewer role**

```text
Task ID: REV-fbd3d8038d9175d3dda9
Candidate ID: C-E-PREG-FOOD-SAFETY
Evidence ID: E-PREG-FOOD-SAFETY
Source ID: OWH-HEALTH
Role: licence | content | clinical | india_localisation | product
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: fbd3d8038d9175d3dda96cbc3553ca3e8d32023f9171d945003899b390d02d71
```

### REV-80df28d01f7c24fe6b8a

- Evidence: `E-PREG-FOOD-AVOID`
- Locator: `Food safety / Do not eat / milk and sprouts bullets`
- Applies to: `pregnancy` `week 4–42`
- Jurisdiction: `IN`
- Domains: `nutrition`
- Dashboard slots: `avoid`
- General development measurements: `none`
- Future personal facts: `allergies, dietary_restrictions, medical_history`
- Profiles: `P09, P10, P24, P36`
- Catalogue items: `none`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, clinical, india_localisation`

**Exact selected source text**

> Unpasteurized milk or juices. Raw sprouts of any kind (including alfalfa, clover, radish, and mung bean).

**Why it is blocked**

- source awaits actual named approval
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- India localisation awaits actual named review
- linked guidance wording awaits actual named review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for P10. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for P10. Final rendered visual review remains pending.

**Record one decision for each pending reviewer role**

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
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 80df28d01f7c24fe6b8ad7ce85d4fbdf94f7811549108669a5ffcdefc02b52da
```

### REV-e9a6b716570ed5b1e9b8

- Evidence: `E-PREG-MEDICINE-BOUNDARY`
- Locator: `Using medicines / start-stop paragraph`
- Applies to: `pregnancy` `week 4–42`
- Jurisdiction: `IN`
- Domains: `preparation`
- Dashboard slots: `preparation`
- General development measurements: `none`
- Future personal facts: `medical_history, medications_and_supplements, next_appointment`
- Profiles: `P09, P10, P24, P36`
- Catalogue items: `none`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, clinical, india_localisation`

**Exact selected source text**

> Always speak with your doctor before you start or stop any medicine. Not using medicine that you need may be more harmful to you and your baby than using the medicine.

**Why it is blocked**

- source awaits actual named approval
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- India localisation awaits actual named review
- linked guidance wording awaits actual named review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for P10. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for P10. Final rendered visual review remains pending.

**Record one decision for each pending reviewer role**

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
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: e9a6b716570ed5b1e9b8c6dcc73f5d5c83c99322c3b91e578d08d9f12c6e41e2
```

### REV-a744138f53722bafa498

- Evidence: `E-PREG-MOVEMENT-OPTIONS`
- Locator: `Getting started and Best activity for moms-to-be`
- Applies to: `pregnancy` `week 4–42`
- Jurisdiction: `IN`
- Domains: `movement`
- Dashboard slots: `movement_focus`
- General development measurements: `none`
- Future personal facts: `clinician_activity_instruction, current_symptom_report, medical_history`
- Profiles: `P09, P10, P24, P36`
- Catalogue items: `MOVE-LOW-IMPACT, MOVE-SWIM, MOVE-WALK`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, clinical, india_localisation`

**Exact selected source text**

> For most healthy moms-to-be who do not have any pregnancy-related problems, exercise is a safe and valuable habit. Even so, talk to your doctor or midwife before exercising during pregnancy. Low-impact activities at a moderate level of effort are comfortable and enjoyable for many pregnant women. Walking, swimming, dancing, cycling, and low-impact aerobics are some examples.

**Why it is blocked**

- source awaits actual named approval
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- India localisation awaits actual named review
- linked guidance wording awaits actual named review and publication
- linked recommendation catalogue item awaits review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for P10. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for P10. Final rendered visual review remains pending.

**Record one decision for each pending reviewer role**

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
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: a744138f53722bafa4982cabf30c9ecc2799c118e4be3082b3d09af4e766ab7d
```

### REV-fb20021d2bdde298f1a7

- Evidence: `E-PREG-MOVEMENT-PACE`
- Locator: `Tips for safe and healthy physical activity / first three bullets`
- Applies to: `pregnancy` `week 4–42`
- Jurisdiction: `IN`
- Domains: `movement`
- Dashboard slots: `movement_focus`
- General development measurements: `none`
- Future personal facts: `clinician_activity_instruction, current_symptom_report, medical_history`
- Profiles: `P09, P10, P24, P36`
- Catalogue items: `MOVE-LOW-IMPACT, MOVE-SWIM, MOVE-WALK`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, clinical, india_localisation`

**Exact selected source text**

> When you exercise, start slowly, progress gradually, and cool down slowly. You should be able to talk while exercising. If not, you may be overdoing it. Take frequent breaks.

**Why it is blocked**

- source awaits actual named approval
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- India localisation awaits actual named review
- linked guidance wording awaits actual named review and publication
- linked recommendation catalogue item awaits review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for P10. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for P10. Final rendered visual review remains pending.

**Record one decision for each pending reviewer role**

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
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: fb20021d2bdde298f1a7fe19a376329c6e613d301397f6d450e3183bcda8bb56
```

### REV-8d49aa866c092bca5fe6

- Evidence: `E-PREG-MOVEMENT-STOP`
- Locator: `Tips / Stop exercising and call your doctor / complete list`
- Applies to: `pregnancy` `week 4–42`
- Jurisdiction: `IN`
- Domains: `movement, symptoms`
- Dashboard slots: `movement_focus, symptom_education`
- General development measurements: `none`
- Future personal facts: `clinician_activity_instruction, current_symptom_report, medical_history`
- Profiles: `P09, P10, P24, P36`
- Catalogue items: `MOVE-LOW-IMPACT, MOVE-SWIM, MOVE-WALK`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, clinical, india_localisation`

**Exact selected source text**

> Stop exercising and call your doctor as soon as possible if you have any of the following: Dizziness. Headache. Chest pain. Calf pain or swelling. Abdominal pain. Blurred vision. Fluid leaking from the vagina. Vaginal bleeding. Less fetal movement. Contractions.

**Why it is blocked**

- source awaits actual named approval
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- India localisation awaits actual named review
- linked guidance wording awaits actual named review and publication
- linked recommendation catalogue item awaits review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for P10. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for P10. Final rendered visual review remains pending.

**Record one decision for each pending reviewer role**

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
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 8d49aa866c092bca5fe67ef427c1e23559162060bc20b880ab0dcb7ba9fe39f4
```


A checked box in this exported document does not change publication state. The named decision must be entered into the governed source, evidence, fragment, profile and catalogue records, then the ingestion run must be repeated. Machine-readable decisions belong in data/reviews/ingestion_decisions.json; the ingestion command rejects unknown task IDs and changed checksums.


---

# Ingestion review — OWH-RECOVERY

- Run: `ING-c2ef62448a8e4c7dd6e0`
- Outcome: **review_required**
- Admission: `parse_for_review`
- Source artifact: `136278dc3f910c29f43b05817540726cbb62627e18043d85c7f6ddf3302691c0`
- Candidate units: 2
- Pending review tasks: 2

## Admission reasons

- actual source approval is pending
- named source review is pending

## Parser and validation issues

- None.

## Human review queue

### REV-1b2b012ff77e5e6acc29

- Evidence: `E-PP-REST`
- Locator: `Getting rest / second paragraph`
- Applies to: `postpartum` `week 1–1`
- Jurisdiction: `US`
- Domains: `preparation`
- Dashboard slots: `preparation`
- General development measurements: `none`
- Future personal facts: `medical_history, medications_and_supplements, next_appointment, postpartum_recovery_context`
- Profiles: `none`
- Catalogue items: `none`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, content, clinical, india_localisation, product`

**Exact selected source text**

> Try to lie down or nap while the baby naps.

**Why it is blocked**

- source awaits actual named approval
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- linked guidance wording awaits actual named review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- None.

**Record one decision for each pending reviewer role**

```text
Task ID: REV-1b2b012ff77e5e6acc29
Candidate ID: C-E-PP-REST
Evidence ID: E-PP-REST
Source ID: OWH-RECOVERY
Role: licence | content | clinical | india_localisation | product
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 1b2b012ff77e5e6acc2967d173beb352bdd4d47ae6d22fdecba2a2767664d697
```

### REV-dcf3f978e9718a5a7559

- Evidence: `E-PP-ACTIVITY-QUESTION`
- Locator: `Physical changes / postpartum visit paragraph / selected clause`
- Applies to: `postpartum` `week 6–6`
- Jurisdiction: `US`
- Domains: `followup`
- Dashboard slots: `followup`
- General development measurements: `none`
- Future personal facts: `delivery_history, next_appointment`
- Profiles: `none`
- Catalogue items: `none`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, content, clinical, india_localisation, product`

**Exact selected source text**

> Ask about resuming normal activities

**Why it is blocked**

- source awaits actual named approval
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- linked guidance wording awaits actual named review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- None.

**Record one decision for each pending reviewer role**

```text
Task ID: REV-dcf3f978e9718a5a7559
Candidate ID: C-E-PP-ACTIVITY-QUESTION
Evidence ID: E-PP-ACTIVITY-QUESTION
Source ID: OWH-RECOVERY
Role: licence | content | clinical | india_localisation | product
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: dcf3f978e9718a5a75597cd6a9e0cb5ed761f3210b8d6d5d40f9b4996256af14
```


A checked box in this exported document does not change publication state. The named decision must be entered into the governed source, evidence, fragment, profile and catalogue records, then the ingestion run must be repeated. Machine-readable decisions belong in data/reviews/ingestion_decisions.json; the ingestion command rejects unknown task IDs and changed checksums.


---

# Ingestion review — OWH-STAGES

- Run: `ING-ed2827b314e4fe9b5f21`
- Outcome: **review_required**
- Admission: `parse_for_review`
- Source artifact: `132165fa797e8189ebd904481c14401f34412b3f15f70bb8528597da21a475d2`
- Candidate units: 4
- Pending review tasks: 4

## Admission reasons

- actual source approval is pending
- named source review is pending

## Parser and validation issues

- None.

## Human review queue

### REV-7774b0b8b978a642c05a

- Evidence: `E-DATING`
- Locator: `Introduction / gestational dating clause / expanded supporting unit`
- Applies to: `pregnancy` `week 1–42`
- Jurisdiction: `IN`
- Domains: `journey`
- Dashboard slots: `hero, kpi_development, what_may_change`
- General development measurements: `none`
- Future personal facts: `confirmed_journey_timing`
- Profiles: `P01`
- Catalogue items: `none`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, content, clinical, india_localisation, product`

**Exact selected source text**

> Pregnancy lasts about 40 weeks, counting from the first day of your last normal period.

**Why it is blocked**

- source awaits actual named approval
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- India localisation awaits actual named review
- linked guidance wording awaits actual named review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- None.

**Record one decision for each pending reviewer role**

```text
Task ID: REV-7774b0b8b978a642c05a
Candidate ID: C-E-DATING
Evidence ID: E-DATING
Source ID: OWH-STAGES
Role: licence | content | clinical | india_localisation | product
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 7774b0b8b978a642c05a5cdf09fc7fa8ca43286f3d896e653b5a7efb2bb438ee
```

### REV-6c2bb329513583654e27

- Evidence: `E-FIRST-TRIMESTER`
- Locator: `First trimester (week 1-week 12) / symptom list / expanded supporting unit`
- Applies to: `pregnancy` `week 1–12`
- Jurisdiction: `IN`
- Domains: `journey`
- Dashboard slots: `kpi_development`
- General development measurements: `none`
- Future personal facts: `confirmed_journey_timing`
- Profiles: `none`
- Catalogue items: `none`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, content, clinical, india_localisation, product`

**Exact selected source text**

> First trimester (week 1-week 12). Other changes may include: Mood swings. Just as each woman is different, so is each pregnancy.

**Why it is blocked**

- source awaits actual named approval
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- India localisation awaits actual named review
- linked guidance wording awaits actual named review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- None.

**Record one decision for each pending reviewer role**

```text
Task ID: REV-6c2bb329513583654e27
Candidate ID: C-E-FIRST-TRIMESTER
Evidence ID: E-FIRST-TRIMESTER
Source ID: OWH-STAGES
Role: licence | content | clinical | india_localisation | product
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 6c2bb329513583654e27ed7f28aa320497f5a336b3ff28f9af2647d16904f3dd
```

### REV-11cb2913d6c8531bd89d

- Evidence: `E-P24-DEVELOPMENT`
- Locator: `Your developing baby / At 24 weeks / first bullet`
- Applies to: `pregnancy` `week 24–24`
- Jurisdiction: `IN`
- Domains: `journey`
- Dashboard slots: `hero, kpi_development, what_may_change`
- General development measurements: `none`
- Future personal facts: `confirmed_journey_timing`
- Profiles: `P24`
- Catalogue items: `none`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, content, clinical, india_localisation, product`

**Exact selected source text**

> Bone marrow begins to make blood cells.

**Why it is blocked**

- source awaits actual named approval
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- India localisation awaits actual named review
- linked guidance wording awaits actual named review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- None.

**Record one decision for each pending reviewer role**

```text
Task ID: REV-11cb2913d6c8531bd89d
Candidate ID: C-E-P24-DEVELOPMENT
Evidence ID: E-P24-DEVELOPMENT
Source ID: OWH-STAGES
Role: licence | content | clinical | india_localisation | product
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 11cb2913d6c8531bd89d14406cf7a40a87138fad3645129bae7639daa4b8550c
```

### REV-b8524bf1668af20b1719

- Evidence: `E-P36-DEVELOPMENT`
- Locator: `Your developing baby / At 36 weeks / second bullet opening`
- Applies to: `pregnancy` `week 36–36`
- Jurisdiction: `IN`
- Domains: `journey`
- Dashboard slots: `hero, kpi_development, what_may_change`
- General development measurements: `none`
- Future personal facts: `confirmed_journey_timing`
- Profiles: `P36`
- Catalogue items: `none`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, content, clinical, india_localisation, product`

**Exact selected source text**

> Body fat increases.

**Why it is blocked**

- source awaits actual named approval
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- India localisation awaits actual named review
- linked guidance wording awaits actual named review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- None.

**Record one decision for each pending reviewer role**

```text
Task ID: REV-b8524bf1668af20b1719
Candidate ID: C-E-P36-DEVELOPMENT
Evidence ID: E-P36-DEVELOPMENT
Source ID: OWH-STAGES
Role: licence | content | clinical | india_localisation | product
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: b8524bf1668af20b171991da00d3ed110a14e578fa3c9fa787b66982ea8adcb4
```


A checked box in this exported document does not change publication state. The named decision must be entered into the governed source, evidence, fragment, profile and catalogue records, then the ingestion run must be repeated. Machine-readable decisions belong in data/reviews/ingestion_decisions.json; the ingestion command rejects unknown task IDs and changed checksums.


---

# Ingestion review — OWH-TEST

- Run: `ING-aea4b8f4759f5bb5b184`
- Outcome: **review_required**
- Admission: `parse_for_review`
- Source artifact: `ed990e5e57ba9f0103d11e5ffa0778eabe14b75fd8ad349d600b0b563894bc67`
- Candidate units: 1
- Pending review tasks: 1

## Admission reasons

- actual source approval is pending
- named source review is pending

## Parser and validation issues

- None.

## Human review queue

### REV-abdc2b2a6fe6fb8e9350

- Evidence: `E-TEST`
- Locator: `Home pregnancy tests / directions paragraph`
- Applies to: `possible_pregnancy` `none None–None`
- Jurisdiction: `IN`
- Domains: `preparation`
- Dashboard slots: `hero, preparation`
- General development measurements: `none`
- Future personal facts: `medical_history, medications_and_supplements, next_appointment`
- Profiles: `PC00`
- Catalogue items: `none`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, clinical, india_localisation`

**Exact selected source text**

> The most important part of using any HPT is to follow the directions exactly as written.

**Why it is blocked**

- source awaits actual named approval
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- India localisation awaits actual named review
- linked guidance wording awaits actual named review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- `content` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed user-facing wording for PC00. This content decision does not provide clinical, India-localisation or licence approval.
- `product` — **accepted** by Kajal (Product/content review) on 2026-09-11: Accepted the proposed placement and conditional behaviour for PC00. Final rendered visual review remains pending.

**Record one decision for each pending reviewer role**

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
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: abdc2b2a6fe6fb8e93507ab5740d1de6812c1489b82756da954e079e0cd35bf1
```


A checked box in this exported document does not change publication state. The named decision must be entered into the governed source, evidence, fragment, profile and catalogue records, then the ingestion run must be repeated. Machine-readable decisions belong in data/reviews/ingestion_decisions.json; the ingestion command rejects unknown task IDs and changed checksums.


---

# Ingestion review — OWH-WELLBEING

- Run: `ING-3eaf360c73a4a342a299`
- Outcome: **review_required**
- Admission: `parse_for_review`
- Source artifact: `795fe3c16f713364eb28536c49159280d66a76af7a2b42fe5420bae31339e707`
- Candidate units: 2
- Pending review tasks: 2

## Admission reasons

- actual source approval is pending
- named source review is pending

## Parser and validation issues

- None.

## Human review queue

### REV-44ed32e51114a1ae82b5

- Evidence: `E-PP-SUPPORT-CONTEXT`
- Locator: `What can I do at home to feel better while seeing a doctor for postpartum depression? / introduction clause / expanded supporting unit`
- Applies to: `postpartum` `week 1–12`
- Jurisdiction: `US`
- Domains: `wellbeing`
- Dashboard slots: `wellbeing_focus`
- General development measurements: `none`
- Future personal facts: `current_emotional_concern, mental_health_care_context, mental_health_history, user_consent`
- Profiles: `none`
- Catalogue items: `none`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, content, clinical, india_localisation, product`

**Exact selected source text**

> Here are some ways to begin feeling better or getting more rest, in addition to talking to a health care professional:

**Why it is blocked**

- source awaits actual named approval
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- linked guidance wording awaits actual named review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- None.

**Record one decision for each pending reviewer role**

```text
Task ID: REV-44ed32e51114a1ae82b5
Candidate ID: C-E-PP-SUPPORT-CONTEXT
Evidence ID: E-PP-SUPPORT-CONTEXT
Source ID: OWH-WELLBEING
Role: licence | content | clinical | india_localisation | product
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 44ed32e51114a1ae82b59e28161785d6748bb6e8749d8938db9b2b08ed3e018a
```

### REV-54a3639b0dd48b7bb034

- Evidence: `E-PP-SUPPORT-TALK`
- Locator: `What can I do at home to feel better while seeing a doctor for postpartum depression? / feelings bullet / expanded supporting unit`
- Applies to: `postpartum` `week 1–12`
- Jurisdiction: `US`
- Domains: `wellbeing`
- Dashboard slots: `wellbeing_focus`
- General development measurements: `none`
- Future personal facts: `current_emotional_concern, mental_health_care_context, mental_health_history, user_consent`
- Profiles: `none`
- Catalogue items: `none`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, content, clinical, india_localisation, product`

**Exact selected source text**

> Here are some ways to begin feeling better or getting more rest, in addition to talking to a health care professional: Talk about your feelings with your partner, supportive family members, and friends.

**Why it is blocked**

- source awaits actual named approval
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- linked guidance wording awaits actual named review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- None.

**Record one decision for each pending reviewer role**

```text
Task ID: REV-54a3639b0dd48b7bb034
Candidate ID: C-E-PP-SUPPORT-TALK
Evidence ID: E-PP-SUPPORT-TALK
Source ID: OWH-WELLBEING
Role: licence | content | clinical | india_localisation | product
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 54a3639b0dd48b7bb0348a4d4e49dc90b6b142f8c94e26671f9e98da9dd46291
```


A checked box in this exported document does not change publication state. The named decision must be entered into the governed source, evidence, fragment, profile and catalogue records, then the ingestion run must be repeated. Machine-readable decisions belong in data/reviews/ingestion_decisions.json; the ingestion command rejects unknown task IDs and changed checksums.


---

# Ingestion review — PIB-PMSMA

- Run: `ING-038eadebed33f9e22be1`
- Outcome: **review_required**
- Admission: `parse_for_review`
- Source artifact: `65b8fe632d47531d38a535fc3ff3bd3def8487c26f4d8d431f6620638ff901eb`
- Candidate units: 1
- Pending review tasks: 1

## Admission reasons

- actual source approval is pending
- named source review is pending

## Parser and validation issues

- None.

## Human review queue

### REV-24a1dde66fc57afaf702

- Evidence: `E-IN-PMSMA`
- Locator: `Page 2 / programme opening paragraph`
- Applies to: `pregnancy` `week 13–42`
- Jurisdiction: `IN`
- Domains: `followup`
- Dashboard slots: `ask_a_professional, followup`
- General development measurements: `none`
- Future personal facts: `delivery_history, next_appointment`
- Profiles: `P24, P36`
- Catalogue items: `ANC-PMSMA`
- Required review roles: `licence, content, clinical, india_localisation, product`
- Current task status: `pending`
- Pending review roles: `licence, content, clinical, india_localisation, product`

**Exact selected source text**

> Launched on June 9, 2016, PMSMA provides free, comprehensive antenatal care to pregnant women - particularly those in their second and third trimesters - at designated government health facilities on the 9th of every month.

**Why it is blocked**

- source awaits actual named approval
- source admission requires review: actual source approval is pending
- source admission requires review: named source review is pending
- evidence awaits actual named review and publication
- linked guidance wording awaits actual named review and publication
- linked recommendation catalogue item awaits review and publication

**Reviewer checklist**

- [ ] source anchor
- [ ] domain
- [ ] stage and range
- [ ] wording
- [ ] jurisdiction
- [ ] conditions
- [ ] development measurements
- [ ] profile links
- [ ] catalogue links
- [ ] reuse and attribution

**Recorded governed decisions**

- None.

**Record one decision for each pending reviewer role**

```text
Task ID: REV-24a1dde66fc57afaf702
Candidate ID: C-E-IN-PMSMA
Evidence ID: E-IN-PMSMA
Source ID: PIB-PMSMA
Role: licence | content | clinical | india_localisation | product
Decision: accepted | changes_requested | rejected | needs_specialist_review
Reviewer name:
Reviewer capacity/qualification:
Review date: YYYY-MM-DD
Reason:
Exact replacement wording (when changing):
Supporting reference:
Timing/week change:
Condition change:
Jurisdiction change:
Candidate checksum: 24a1dde66fc57afaf702949ea49e581acfbfe7e38277dd213dec162336f03bd0
```


A checked box in this exported document does not change publication state. The named decision must be entered into the governed source, evidence, fragment, profile and catalogue records, then the ingestion run must be repeated. Machine-readable decisions belong in data/reviews/ingestion_decisions.json; the ingestion command rejects unknown task IDs and changed checksums.
