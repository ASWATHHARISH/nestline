# Source verification work log

## Update: 10 September 2026

The first-pass outcomes now live in `data/guidelines/source_audit.jsonl`. Five
permitted OWH selected-text snapshots have been saved; all content remains draft.
See DEMO-WORK-LOG.md and STAGE-0-REVIEW-PACKET.md for current state.

The NHS possibility described below was investigated and **did not pass**:
[NHS exclusions](https://www.nhs.uk/our-policies/terms-and-conditions/content-not-licensed-for-re-use/)
specifically list Best Start in Life. Its
[separate terms](https://www.nhs.uk/best-start-in-life/terms-and-conditions/)
do not establish permission for our planned ingestion. NHS-01 and NHS-02 are
excluded. No Best Start content was stored as evidence. The 9 September notes
below are history, not current approval.

Recovery locations for failed original PDF URLs (not verified source files):
- NIN: https://nin.res.in/dietaryguidelines/pdfjs/locale/DGI_2024.pdf
- WHO activity landing page: https://www.who.int/publications/i/item/9789240015128
- WHO ANC DAK landing page: https://www.who.int/publications/i/item/9789240020306

## Original audit: 9 September 2026

Checked: 2026-09-09. This is an initial engineering audit, not clinical approval.
The full source inventory is not yet verified. No medical passages were ingested
or published during this audit.

## MEDLINEPLUS-01: exclude from ingestion

The [fetal-development article](https://medlineplus.gov/ency/article/002398.htm)
is supplied by A.D.A.M./Ebix. Its footer requires express written consent for AI
reuse, including retrieval datasets and embeddings. A government-hosted URL does
not make this particular article freely reusable. Keep allowed_use empty and mark
the source excluded/restricted. Find a permitted replacement before filling the
development cards. Do not copy this article into fixtures or evaluations.

## NHS: conditional candidate, not approved

[NHS terms, section 3](https://www.nhs.uk/our-policies/terms-and-conditions/)
provide an Open Government Licence route with exceptions and attribution rules.
Check each page's exclusions before ingestion. Unchanged and adapted content have
different attribution requirements; record that distinction in the ingestion and
display design. Images and third-party materials are not automatically covered.
England-specific service arrangements must not become Indian care instructions.

The [week 10 page](https://www.nhs.uk/best-start-in-life/pregnancy/week-by-week-guide-to-pregnancy/1st-trimester/week-10/)
is a candidate for the P10 evidence-selection pass. Next: verify page-specific
exceptions, capture a permitted version with its checksum, select exact passages
and applicability, then request actual content review. No review is pre-filled.

## Next deliverable

Continue checking the remaining sources and prepare draft evidence for PC00, P10
and PP01 first, then the other representative profiles. Keep source permission,
content review and software validation as separate checks. The existing weekly
records remain empty draft structures until reviewed evidence is available.
