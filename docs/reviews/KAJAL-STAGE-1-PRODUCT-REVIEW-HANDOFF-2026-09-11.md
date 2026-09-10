# Nestline Stage 1 product-review handoff

**Reviewer:** Kajal  
**Review capacity:** Product/content review  
**Decision date:** 11 September 2026

## What is approved for product

Kajal reviewed and accepted the proposed product wording, content placement and expected conditional behaviour for the first demonstration slice:

- `PC00`: possible pregnancy;
- `P10`: confirmed pregnancy, week 10;
- `PP01`: first week after birth.

The individual proposed cards shown in `KAJAL-STAGE-1-PRODUCT-REVIEW-WORKSHEET.md` are accepted for product use, subject to their existing display conditions and the specialist approvals described below.

The product direction for the playful baby-size feature is also accepted, with the revised rounder and intentionally repeatable object sequence in `fetal_size_comparisons.csv`.

## Product changes requested and applied to the draft

The elongated or visually awkward comparisons from week 20 onward were replaced as follows:

| Weeks | Revised product comparison |
|---|---|
| 20–21 | Small orange / orange |
| 22–23 | Grapefruit, repeated intentionally |
| 24–25 | Small muskmelon, repeated intentionally |
| 26 | Small cabbage |
| 28–30 | Cabbage sequence |
| 31–32 | Honeydew melon, repeated intentionally |
| 33 | Small watermelon |
| 36 | Large muskmelon |

Repeated comparisons across two or three weeks are acceptable when they make the visual progression more natural.

## Important boundary

This is **product/content approval only**. It is not:

- clinical approval of a health statement or fetal measurement;
- verification of comparison-object dimensions;
- India-localisation approval;
- source/licence approval;
- permission to create embeddings or publish the content;
- final visual approval of Streamlit screens that have not yet been rendered.

All 42 comparison records must remain draft and hidden until the measurement source, measurement convention, size range, object dimensions, artwork/licence state and required specialist reviews are recorded.

## What the teammate/Codex should do next

1. Apply or preserve the attached `fetal_size_comparisons.csv` changes in the active Stage 1 branch.
2. Convert Kajal's product decisions from the workbook into the project's governed review/approval records. Do not manually invent reviewer IDs, signatures or specialist approvals.
3. Regenerate affected checksums, review packets and snapshots using the repository's supported scripts.
4. Keep all comparison entries hidden and excluded from live RAG/embeddings while verification is pending.
5. Arrange qualified maternal-health, India-localisation and source/licence review for the released `PC00`, `P10` and `PP01` slice.
6. Apply any specialist-requested corrections and regenerate the corresponding review artifacts.
7. Produce actual rendered Streamlit previews for `PC00`, `P10` and `PP01`, including conditional and missing-information states.
8. Return those rendered screens to Kajal for final visual and interaction review.
9. Continue Stage 2 engineering in parallel using draft/test-only content. Do not describe the content as release-ready.

## Files included in the handoff bundle

- `KAJAL-STAGE-1-PRODUCT-REVIEW-HANDOFF.md` — this decision summary and next-action list.
- `KAJAL-STAGE-1-PRODUCT-REVIEW-WORKSHEET.md` — the evidence reviewed and recorded product decisions.
- `fetal_size_comparisons.csv` — corrected draft comparison catalogue.

## Local verification already performed

- Authoring validation passed.
- 51 relevant automated tests passed.
- The comparison catalogue still contains 42 records.
- Changed comparison records remain `draft`, without evidence IDs or verified measurements.

These are software/data-integrity checks, not clinical validation.
