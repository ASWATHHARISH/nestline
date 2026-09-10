# Stage 1 independent-review correction status

Updated 11 September 2026 against
`STAGE-1-INDEPENDENT-REVIEW-AND-STAGE-2-HANDOFF.md`.

The handoff contains seven engineering changes plus one TLS reproduction check.
All seven changes are implemented. The TLS failure did not reproduce: all five
OWH sources and all nine other evidence-bearing sources were captured with normal
certificate and hostname verification.

| Finding | Result | Verification |
|---:|---|---|
| 1. Update branch from `main` | Complete | Current upstream `main` merged without conflict; Stage 0 release gates preserved |
| 2. Reproducible 14-source audit | Complete | Tracked `data/ingestion/audit/stage1-source-audit.json`; clean-checkout checker and CI step |
| 3. Stored parsed blocks | Complete | 72 governed blocks; every one of 55 candidates resolves to same-source stored blocks; corpus includes hashed `blocks.jsonl` |
| 4. Changed-source re-review | Complete | Full artifact, selected text and governance hashes; changed bytes/version/permission state forces review and zero embeddings |
| 5. Review-decision structure | Complete | Five separate roles; four dispositions; reviewer identity/capacity/reason/reference/change fields; validated reload ledger |
| 6. Publication approval gate | Complete | Corpus publisher rechecks current Stage 0 fingerprint and five separate roles |
| 7. Logical idempotency | Complete | Same bytes across dates retain one logical version; latest same-source run loads automatically; wrong-source previous run rejected |
| 8. OWH verified TLS | Passed without code bypass | Five OWH sources captured with verified HTTPS; no insecure option added |

Current canonical audit:

- 14 source runs;
- 55 evidence candidates;
- 55 verified anchors;
- 72 retained governed blocks;
- 55 exact review-task IDs;
- 0 source/parser errors;
- 0 production embeddings;
- 0 published corpus records.

The engineering machinery is corrected. Kajal's content/product decisions for
the 27 tasks behind `PC00`, `P10` and `PP01` are now recorded. The medical content
release remains blocked by clinical, licence and India-localisation review for
that slice, applicable review for the rest of the release, and final visual review.
See `docs/STAGE-1-PC00-P10-PP01-REVIEW-HANDOFF.md`.
