# Stage 2–4 independent-review response and Stage 5 gate

**Review received:** NESTLINE-STAGE-2-3-AND-STAGE-4-READINESS-INDEPENDENT-REVIEW.md
**Reviewed baseline:** 68722f8039dcb5202ec105033f8b242f6dff64cb
**Correction date:** 11 September 2026
**Correction owner:** Codex engineering self-review
**Repository state:** local working tree on feat/stage-1-governed-ingestion; not committed or pushed
**Decision:** locally ready for deterministic Stage 5 engineering; not yet a GitHub merge baseline; not ready for real or public medical use

## Decision rules used

Every finding was checked against the source, tests, tracked evidence and both
local database histories. A finding is marked fixed only when its implementation
and an appropriate regression check pass. Work that requires a named human,
vendor, product decision or paid-model benchmark is recorded as open rather than
invented.

## Finding-by-finding response

| Finding | Decision | Action and evidence | Current status |
|---|---|---|---|
| S2-01: 141 historical versus 122 current | Agree. The prior documents described 141 as current even though the tracked file runs 122. The exact historical 141 SQL is not in Git, so the requested one-to-one mapping of nineteen assertions cannot be honestly reconstructed. | The Stage 2 file now pins plan(122). data/supabase/stage2-assertion-coverage.json inventories all 122 by category and records 206 across the current Stage 2–4 suites. scripts/check_stage2.py validates the plan, inventory and historical distinction. Current documents and STAGE-2-CHECK-RESULTS.json were corrected. | Fixed with one explicit evidence limitation |
| S2-02: API checks red in CI | Agree. Bash eval created shell variables that were not exported to Python. | Both workflow paths now place set -a before the Supabase environment eval and set +a after it. Locally, both database histories ran all three API scripts: 13 Storage, 17 onboarding and 15 document checks. | Locally fixed; GitHub confirmation waits for an approved push |
| S3-01: final Safety Gate absent | Agree. Capture/storage is complete; live Stage 6 routing is not. | The execution plan now separates timestamped symptom capture, atomic storage and forced evaluation-only state from the still-open reviewed Stage 6 route. Symptoms cannot be used as proof that a situation is safe. | Accurate and safe; Stage 6 routing remains open |
| S3-02: onboarding API did not run in CI | Agree; same root cause as S2-02. | The workflow export fix is shared. The 17-check onboarding API suite passed on both the exact upgrade and clean replay locally. | Locally fixed; GitHub confirmation waits for an approved push |
| S3-03: render smoke is not product acceptance | Agree. Automated rendering cannot sign a product decision. | Kept as a named Kajal/product review with screenshots and decisions for all timing paths, conflicts, privacy language and postpartum chronology versus profile keys. | Open; blocks public release, not deterministic Stage 5 |
| C4-01: preselected decisions | Agree. This violated the field-by-field confirmation promise. | Every decision radio now uses no default selection. Abstentions require an explicit reject acknowledgement. The final checkbox and save button stay disabled until every row has a valid decision. The rendered test proves two decisions start empty and save remains disabled. | Fixed |
| C4-02: Windows-sensitive SQL hashes | Agree. Raw bytes made valid CRLF checkouts fail. | SQL hashes are canonicalized to LF; .gitattributes now pins SQL and YML to LF. A regression creates equivalent LF and CRLF SQL files and proves identical hashes. The full Stage 4 checker passes on this Windows machine. | Fixed |
| C4-03: hidden provenance | Agree. A reviewer lacked evidence needed for a responsible choice. | The review screen now shows registered document name, page, character span, coordinates, exact quote, confidence, completeness, disposition and current state. It explains abstention, record-only medication and source mismatch. Rendered regression evidence checks these fields. | Fixed |
| C4-04: missing identity bypass | Agree. No detected subject cannot mean correct subject. | Identity now requires an exact source-level subject match or an exact-hash fixture binding to Maya. Missing, blank/unreadable, multiple, near-match and wrong subjects fail closed. The identity result is typed in UploadValidationResult. | Fixed for the supervised fixture flow |
| C4-05: client-asserted fictional/scanner state | Agree with the risk. The review offered seeded fixtures as an accepted controlled option. | Arbitrary file upload was removed. The document feature defaults off through NESTLINE_ENABLE_STAGE4_FIXTURE_DEMO. In a supervised development run it exposes only nine repository-owned fixture choices, validates their exact hashes, and rejects a modified watermarked PDF. The default-off state and absence of an uploader are render-tested. | Controlled for Stage 5 demos; real/public uploads remain prohibited |
| C4-06: Stage 4 API did not run in CI | Agree; same export defect. | The workflow was fixed. The 15-check Stage 4 API suite passed on both local histories, together with the other 30 API checks and zero lint findings. | Locally fixed; GitHub confirmation waits for an approved push |
| C4-07: provider plan mismatch | Agree that OpenAI must not become an accidental permanent choice. | ADR 0004 makes DocumentExtractionPacket the provider-neutral boundary, keeps the deterministic parser as the reproducible baseline, and leaves OpenAI, Grok or another accessible model as benchmark candidates. No winner is claimed without model IDs, cost ceiling and measured results. | Architecture decision fixed; live benchmark remains open |
| C4-08: human and operational gates | Agree. Tests cannot self-approve these items. | Product, clinical, India-localisation, licence, server-side scanner policy and provider benchmark remain named gates. Public content and real-document processing stay closed. | Open by design; blocks public release |

## Important boundary retained for C4-05

Supabase does not currently inspect document bytes with a trusted server-side
malware scanner or independently prove that a caller-declared SHA belongs to the
uploaded Storage object. The authenticated database path still accepts extraction
metadata through the protected development RPC.

For that reason, Nestline does not claim that arbitrary authenticated API callers
are technically prevented from submitting real data. The engineering correction
uses the review's non-public option: the feature is closed by default and the
supervised UI has no arbitrary uploader. Before real or public uploads, route
upload, scanning and registration through a trusted server or Edge Function,
remove client authority to assert scan provenance, and test forged scan/provider/
fictional declarations end to end.

This remaining production boundary does not block deterministic Stage 5 work
against controlled fixtures and confirmed state. It does block any real or public
medical-document claim.

## Verification evidence after correction

| Gate | Result |
|---|---:|
| Python regression | 175/175 |
| Content contract cases | 64/64 |
| Journey cases | 26/26 |
| Stage 1 continuity | 14 source runs, 55 candidates/anchors, 54 governed decisions, zero errors |
| Stage 2 current pgTAP | 122/122, fixed plan |
| Stage 3 pgTAP | 12 exit hardening + 26 onboarding |
| Stage 4 pgTAP | 11 role hardening + 35 document confirmation |
| Full database total | 206/206 on exact upgrade and 206/206 on clean replay |
| Authenticated API checks | 45/45 on exact upgrade and 45/45 on clean replay |
| Database lint | zero findings on both histories |
| Streamlit Stage 4 | full provenance visible, zero preselected decisions, save blocked, default public feature closed, zero network calls |
| Stage 4 checker | passed on Windows with remote evidence |
| Temporary API fixtures | all removed |
| Diff whitespace check | passed |

The tracked remote Stage 4 evidence still matches both existing migration hashes
and reports 14 migrations, 206 assertions, zero pending migrations, zero lint
findings, zero application-role drift and zero temporary personal fixtures. This
correction changes no database migration, so no new Supabase deployment is needed.

## Failures found during this correction and recovery

1. The first full Python run failed because adding the fixture registry changed
   the broad foundation fingerprint. The guarded rebind refused all changes except
   that fingerprint, confirmed 14 sources and 54 governed decisions were intact,
   updated the audit, regenerated the specialist handoff and restored a green run.
2. The first Stage 4 check reported a stale document JSON Schema after adding the
   typed identity status. The schema was regenerated from the Pydantic contracts
   and the checker passed.
3. The first default-off UI render exposed a missing os import. The render test
   caught it before handoff; the import was added and both enabled and default-off
   render paths passed.
4. The attached review exposed that historical Stage 2 evidence could not be
   reproduced exactly. The response preserves the old 141 record, states that its
   SQL source is unavailable, and pins the current 122 instead of inventing a
   migration story.

## Work still required from the team

| Owner | Required work | Blocks deterministic Stage 5 | Blocks real/public use |
|---|---|---:|---:|
| Aswath | Approve commit/push when ready, then require both GitHub jobs to pass | Yes for a shared GitHub baseline; no for local work | Yes for release |
| Kajal/product | Review rendered Stage 3 timing routes and Stage 4 proposal screens; record screenshots and decisions | No | Yes |
| Qualified clinician | Review applicable health and safety content | No | Yes |
| India-localisation reviewer | Review India-specific claims and navigation | No | Yes |
| Licence reviewer | Close remaining source-use decisions before publication/embedding | No | Yes |
| Product/security/platform | Select scanner vendor, region, retention, quarantine and failure policy; implement trusted server boundary | No | Yes |
| Aswath/product | Name exact accessible extraction candidates and cost ceiling; run frozen benchmark | No | Yes |
| Stage 6 reviewers | Approve and implement urgent/clarify/non-urgent routing | No for retrieval engineering | Yes for public symptom navigation |

## Stage 5 starting constraints

Stage 5 may begin locally after this correction. It must:

1. retrieve only confirmed personal facts;
2. keep evaluation-only symptoms out of any claim that a situation is safe;
3. retrieve only content whose lane and publication state allow it;
4. apply workspace, care episode, country, week/range, condition and approval
   filters before ranking;
5. use controlled fixtures where human publication gates are still open;
6. prove graph expansion adds value on relationship-dependent cases and avoid
   claiming graph benefit where exact SQL already answers the query;
7. retain deterministic tests that require no paid model.

The branch cannot be called a green GitHub Stage 5 baseline until these local
changes are committed, pushed with Aswath's approval, and both validate and
supabase-integration pass on the resulting commit.
