# Stage 0 correction status

Updated 10 September 2026. This document supersedes earlier claims that the only
remaining work was signing off a finished content dataset. Kajal's review identified
real evidence and selection defects. They are corrected below; source interpretation,
clinical approval and publication are not claimed to be complete.

## Findings and evidence of correction

| Review item | Implemented result | Verification | Status |
|---|---|---|---|
| P0.1 Day-42 claim exceeded its anchor | E-IN-PP-FOLLOWUP contains the complete home/facility schedule; wording describes the programme accurately. | test_complete_conditional_evidence_regressions; saved NHM snapshot | Corrected draft |
| P0.1 Missing complicated-delivery condition | Complete NHS paragraph retained; the same condition is required on the card. | Same regression; claim audit | Corrected draft |
| P0.1 Unsupported diet clause | Removed the extra clause; exact breastfeeding sentence retained with its condition. | Same regression | Corrected draft |
| P0.2 P01 birth planning | P01 contains pregnancy-timing education only; birth-plan fragment starts at week 4. | test_week_one_contains_timing_only | Fixed |
| P0.3 Empty day overlays | All PPD0-7 contain sourced rest/help cards; selected days have contact information. Day 7 maps to PP01 by explicit convention. | Overlay regression and day cases | Populated drafts; actual product review pending |
| P0.4 Conditions hid the whole week | Shared typed condition registry; card states shown/needs_information/not_applicable/unavailable. | Selection regression and 12 software cases | Fixed contract; UI not built |
| P0.5 Exact source/clinical/India/product approval | Five-role approval ledger and release fingerprint; empty actual reviewer list. | Release gate reports each missing role | Open; actual people must perform review |
| P0.6 Claim support | 56 individually recorded Codex assessments; changes invalidate them. Clipped timing, fertility and professional-care anchors expanded too. | Stale-claim/source tests; review packet | Agent assessment complete; human semantic approval open |
| P0.7 P42 | Hidden shell with explicit local-review blocker. | Draft selection and coverage validation | Withheld as required |
| P1.1 Catalogues | 12 food, 6 movement, 6 wellbeing, 10 follow-up and 42 comparison proposals. | Foundation validation and food/condition regressions | Draft contracts; catalogue content approval open |
| P1.2 Indian timing + WHO cross-check | NHM programme passages, current June 2026 PIB PMSMA information and source comparison note. | Snapshot checks; ANC-PNC-SOURCE-COMPARISON.md | Research documented; local clinical reconciliation open |
| P1.3 Safety contract | Draft English rule examples, explicit India help routes, priority and no-reassurance checks. | Draft runtime refusal; software cases | Contract exists; clinical routing validation remains open |
| P1.4 Synthetic documents | Eight fictional PDFs, texts and page/line/rectangle extraction truth. | PDF rendering/inspection; integrity and tampering tests | Fixtures complete; OCR/state pipeline is later work |
| P1.5 Future evaluation contract | 64 visible deterministic software cases with inputs, expected outputs and purpose. | Local runner 64/64 | Prepared; not a model benchmark or sealed holdout |
| P1.6 Source-state report | Registered, permission-researched, snapshotted, assembled, human-reviewed and published states. | Generated STAGE-0-SOURCE-STATE.json | Complete report, not source approval |
| P2.1-2 Remaining weekly coverage | 46 hidden shells retained; broad fragments reused without fake unique weekly claims. | Coverage/selection checks | Controlled later expansion as the review specifies |
| P2.3 Visuals | Original image keys/proposals retained; no third-party artwork copied. | Comparison checks | Artwork deferred under review section 12.4 |
| P2.4 Freshness | Capture/publisher/next-review dates and currency state; release rejects overdue/uncertain used sources. | Freshness tests | Offline gate exists; scheduled monitoring is future work |

## Work that still needs a real decision

| Open work | Responsible role | Proposed review target | Acceptance evidence |
|---|---|---|---|
| BHC P09/P10 text last reviewed in 2012; NHM booklet currency and current local service interpretation | Qualified India maternal-health reviewer, coordinated by Aswath | Before content publication; reviewer/date not yet confirmed | Current-source assessment or replacement passages, exact accepted scope/wording |
| Exact medical wording, conditions, safety patterns/omissions, urgent and ambiguous examples | Qualified clinical reviewer | Before safety/content release; date not yet confirmed | Reviewed changes, retained conditions, clinical decision for the exact fingerprint |
| Source use and commercial limitations, especially BHC, NHM CHO and link-only CDC/AIM | Licence reviewer coordinated by Aswath | Before any publication; date not yet confirmed | Actual per-source permission/attribution decision; no invented commercial rights |
| Empty/conditional states, wellbeing micro-actions, day convention and final catalogue scope | Kajal, product/content | Proposed next team review, 11 September 2026; not a commitment | Actual acceptance or changes_requested record |
| Measurement series and independently recorded comparison-object dimensions | Product/editorial with clinical review | Before enabling comparisons; date not yet confirmed | Verified source, measurement convention, dimensions and original wording |
| Apply accepted changes and publish dependencies in order | Codex after actual review decisions | Following the reviews above | Tests pass, current ledger, source/evidence/fragment/profile/catalogue gates pass |

The missing reviewers and editorial measurements are not being replaced with fake
names, approval flags or guessed numbers. If a comparison cannot be defended, the
agreed fallback is development text without a size object. All 42 comparison
proposals remain hidden; images are deliberately a later task.

## Current gates

- Authoring and review-readiness pass: records are internally consistent and have
  reviewable content. Neither is clinical approval.
- Local verification: 68 unit tests and 64 visible software cases pass. No AI model,
  OCR accuracy, medical sensitivity, UI or database behaviour was evaluated.
- Release fails: 17 profiles/overlays, 34 non-comparison catalogue items, five
  human roles, three source-currency decisions and the safety contract are pending.
- All 63 profiles remain unpublished. No PR is requested, and main is unchanged.

## Review and publication procedure

Run the source-state and review-packet exporters. Review the actual wording and
full original context, not only the summary. Record corrections first. After an
actual reviewer has made a decision, record their role, name, capacity, date,
disposition, release checksum and notes in data/reviews/approvals.json. The packet
prints the checksum; approval metadata does not change it, but content edits do.

Each source/evidence/localisation/fragment/profile also needs its real review
metadata and correct lifecycle state. Clear a blocker only after its work is done.
Catalogues require published evidence. Run --require-release before enabling any
content. This is a manual repository workflow; reviewer authentication and an
operational review UI belong to later implementation.
