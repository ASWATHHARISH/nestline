# Stage 1 Kajal approval import record

## Imported decision

- Reviewer: **Kajal**
- Review capacity: **Product/content review**
- Decision date: **11 September 2026**
- Formal decision: **Proposed content, placement and conditional behaviour accepted for product**
- Scope: the proposed wording, placement and conditional behaviour for `PC00`, `P10` and `PP01`, including the individual cards identified by evidence ID in the worksheet
- Comparison decision: accept the revised rounder/repeatable sequence as product direction; keep all comparisons hidden until measurement, object-dimension and specialist verification is complete
- Confirmation type: explicit typed approval; not a cryptographic or legal signature

## Preserved approval evidence

| Artifact | SHA-256 |
|---|---|
| [Product-review handoff](reviews/KAJAL-STAGE-1-PRODUCT-REVIEW-HANDOFF-2026-09-11.md) | `80BBC211B03D825447622D65AE440832DB89857C41939C4BAE994B7AC412DC28` |
| [Product-review worksheet](reviews/KAJAL-STAGE-1-PRODUCT-REVIEW-WORKSHEET-2026-09-11.md) | `0B156AC48E26145B180AB56C5AA0C6E5CC4F58A7D139A51D310EF6D83481E1AB` |
| Applied comparison CSV | `D3554DFE325FE3DEBF8A7FFF78A391BA262200F885B305C08946448697E247E8` |

The supplied comparison CSV has the same SHA-256 as the catalogue already present on the active branch. No second catalogue mutation was required.

## Governed import result

- 27 current evidence tasks are in the approved slice.
- 27 `content` decisions and 27 `product` decisions are recorded.
- Every decision names Kajal, the stated capacity and decision date.
- Every decision is bound to the current task ID, candidate ID, evidence ID, source ID and candidate checksum.
- The two illustrative PC00 task IDs printed in the worksheet are from an older candidate version. They were not imported. Their stable evidence IDs were resolved to the current canonical task/checksum records.
- No clinical, India-localisation, licence, publication or final rendered-UI approval was inferred.

## Remaining review gates

- [ ] A qualified maternal-health clinician reviews all 27 exact tasks.
- [ ] An India maternal-health/localisation reviewer reviews all 27 exact tasks.
- [ ] A source/licence reviewer reviews all 27 exact tasks.
- [ ] Any requested corrections are applied and the affected checksums are regenerated.
- [ ] Kajal gives final visual/interaction approval on the post-specialist Streamlit render.
- [ ] All comparison measurements, object dimensions and artwork/licensing are verified before any comparison becomes visible.

Imported into the governed ledger on `feat/stage-1-governed-ingestion` under Aswath's explicit instruction. Git history is the immutable record of the importing commit.
