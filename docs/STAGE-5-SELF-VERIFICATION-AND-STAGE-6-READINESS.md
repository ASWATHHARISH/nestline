# Stage 5 self-verification and Stage 6 readiness

**Verification date:** 11 September 2026
**Branch:** `feat/stage-1-governed-ingestion`
**Reviewed baseline:** 448eb6d2ab7b4e8cc7db9fc42ce5c523a7fe10a7
**Rectification implementation commit:** dcec1f9e847a64185330ba4406a886bcced688b2
**Local recommendation:** Stage 5 ready for independent re-review
**Stage 6 recommendation:** NO-GO until independent Stage 5 re-review accepts the rectification
**Public/clinical recommendation:** NO-GO

## What was verified

The rectification was checked against the attached independent review, the Stage 5 architecture/requirements, the existing Stage 1–4 gates, database RLS/RPC behavior and the frozen Stage 5 development truth.

The two reported answerability defects were first reproduced on the reviewed commit and then preserved as regression cases. The implementation now requires relevant evidence of the type selected by a fixed server-side policy.

## Reproduced defects

### Unsupported public guidance

Question: `What hospital documents and finances should I prepare at week 25?`

Before:

- approved public evidence: 0;
- unrelated personal facts: 2;
- unrelated personal passages: 1;
- `should_abstain=false`;
- reason: `none`.

After:

- approved public evidence: 0;
- relevant personal facts/passages: 0/0;
- support state: `unsupported`;
- `should_abstain=true`;
- reason: `no_approved_public_content`.

### Relevant unresolved conflict

Question: `How should my conflicting prenatal yoga record affect week 25 movement guidance?`

Before:

- approved public evidence: 0;
- personal facts: 2;
- personal passages: 1;
- unresolved conflicts: 1;
- `should_abstain=false`;
- reason: `none`.

After:

- approved public evidence: 0;
- relevant confirmed constraint: 1;
- unrelated personal passages: 0;
- relevant unresolved conflicts: 1;
- support state: `clarification_required`;
- `should_abstain=true`;
- reason: `unresolved_conflict`.

The full corrected packets are in `docs/STAGE-5-RECTIFICATION-EVIDENCE-PACKETS.json`.

## Retrieval evaluation

The truth set contains 26 deterministic synthetic cases. It covers:

- both reproduced defects;
- personal-record-only lookup;
- relevant and irrelevant conflicts;
- required missing information;
- graph enabled and disabled;
- positive, absent and excluded condition applicability;
- current-week mismatch and explicit future-week questions;
- stale caller state version;
- possible pregnancy;
- postpartum day and postpartum week;
- journey, nutrition, movement, wellbeing, symptoms, preparation and follow-up;
- medication, symptom-record and appointment lookup.

### Adopted hybrid metrics

| Metric | Result |
|---|---:|
| Recall@5 | 18/18 = 1.000 |
| Citation/evidence precision | 18/18 = 1.000 |
| Confirmed-personal-fact precision | 11/11 = 1.000 |
| Expected behavior accuracy | 26/26 = 1.000 |
| Support-state accuracy | 26/26 = 1.000 |
| Journey-relation accuracy | 26/26 = 1.000 |
| Graph-path correctness | 1/1 = 1.000 |
| Wrong-week retrieval | 0 |
| Wrong-jurisdiction retrieval | 0 |
| Unapproved-source retrieval | 0 |
| Cross-workspace leakage | 0 |
| Conflict/proposal personalization violations | 0 |
| Forbidden evidence IDs observed | 0 |

### Ordered experiments

1. Vector-only baseline ran under the same public filters/corpus. It found 18/18 expected public IDs but returned 27 public IDs, so precision was 18/27. It cannot answer exact personal-record, behavior or graph requirements.
2. Hybrid exact SQL + full text + vector found 18/18 expected public IDs with 18/18 precision, 11/11 personal-fact precision and 26/26 behavior/support/journey decisions.
3. One deterministic authority/applicability score trial matched the adopted results and was not adopted because it showed no improvement.
4. Graph ablation showed the required graph case fails without graph and succeeds 1/1 with graph. The exact-SQL record case is unchanged with graph on/off, so no false graph benefit is claimed.

Latency values are development-machine measurements only and are recorded per component in `docs/STAGE-5-RETRIEVAL-METRICS.json`.

## Application and content verification

| Check | Result |
|---|---:|
| Complete Python unit suite | 212/212 passed |
| Focused Stage 5 unit suite | 36/36 passed |
| Content authoring validation | passed: 63 profiles, 0 published, 31 sources, 55 evidence spans, 56 fragments |
| Content review-ready validation | passed with the same inventory |
| Content contract evaluation | 64/64 passed |
| Journey evaluation | 26/26 passed |
| Stage 1 check | passed: 212 tests, 55 candidates/anchors, 72 governed blocks, 54 review decisions |
| Stage 2 check | passed |
| Stage 3 UI smoke | passed; unauthenticated onboarding; 0 network calls |
| Stage 3 check | passed |
| Stage 4 readiness | passed |
| Stage 4 UI smoke | passed; explicit review; 0 preselected items; public feature closed; 0 network calls |
| Stage 4 full check | passed |
| Expanded Stage 5 evaluation | 26/26 behaviors passed |
| Stage 5 deterministic check | passed; ready_for_independent_re_review=true; ready_for_stage6_engineering=false |
| Database lint | 0 findings in Nestline public/private schemas |

## Database verification

No migration was added or modified during rectification.

### Exact Stage 4 to Stage 5 upgrade

Commands:

```powershell
pnpm exec supabase db reset --local --version 20260911001200
# controlled Stage 4 upgrade fixture inserted locally
pnpm exec supabase migration up --local
# stage5_stage4_upgrade_check.sql executed
```

Result: passed. The controlled upgrade data survived/backfilled as expected and cleanup left no temporary fixture rows.

### Clean replay

Command:

```powershell
pnpm exec supabase db reset --local
```

Result: every migration from `20260911000100` through `20260911001300` applied successfully.

### pgTAP

| File | Result |
|---|---:|
| `stage2_security_and_lifecycle.test.sql` | 122/122 |
| `stage3_exit_hardening.test.sql` | 12/12 |
| `stage3_onboarding.test.sql` | 26/26 |
| `stage4_api_role_hardening.test.sql` | 11/11 |
| `stage4_document_confirmation.test.sql` | 35/35 |
| `stage5_hybrid_retrieval.test.sql` | 48/48 |
| **Total** | **254/254** |

### Authenticated API checks

| Checker | Result |
|---|---:|
| Stage 2 Storage | 13/13 |
| Stage 3 onboarding | 17/17 |
| Stage 4 document | 15/15 |
| Stage 5 retrieval | 25/25 |
| **Total** | **70/70** |

The Stage 5 API checker uses two authenticated principals and verifies authenticated scope, trusted state version/policy, cross-workspace denial and expected retrieval behavior.

Database lint returned zero findings.

## Exact commands used

```powershell
.venv\Scripts\python.exe -m unittest tests.test_retrieval -v
.venv\Scripts\python.exe -m unittest discover -s tests -q
.venv\Scripts\python.exe -m scripts.validate_content
.venv\Scripts\python.exe -m scripts.validate_content --require-review-ready
.venv\Scripts\python.exe -m scripts.run_contract_evals
.venv\Scripts\python.exe -m scripts.run_journey_evals
.venv\Scripts\python.exe -m scripts.check_stage1
.venv\Scripts\python.exe -m scripts.check_stage2
.venv\Scripts\python.exe -m scripts.check_stage3_ui
.venv\Scripts\python.exe -m scripts.check_stage3
.venv\Scripts\python.exe -m scripts.check_stage4_readiness
.venv\Scripts\python.exe -m scripts.check_stage4_ui
.venv\Scripts\python.exe -m scripts.check_stage4
.venv\Scripts\python.exe -m scripts.export_retrieval_schema
.venv\Scripts\python.exe -m scripts.run_stage5_retrieval_evals
.venv\Scripts\python.exe -m scripts.check_stage5 --write-report
pnpm exec supabase db reset --local --version 20260911001200
pnpm exec supabase migration up --local
pnpm exec supabase db reset --local
pnpm exec supabase test db --local supabase/tests/stage2_security_and_lifecycle.test.sql
pnpm exec supabase test db --local supabase/tests/stage3_exit_hardening.test.sql
pnpm exec supabase test db --local supabase/tests/stage3_onboarding.test.sql
pnpm exec supabase test db --local supabase/tests/stage4_api_role_hardening.test.sql
pnpm exec supabase test db --local supabase/tests/stage4_document_confirmation.test.sql
pnpm exec supabase test db --local supabase/tests/stage5_hybrid_retrieval.test.sql
.venv\Scripts\python.exe -m scripts.check_stage2_storage_api
.venv\Scripts\python.exe -m scripts.check_stage3_onboarding_api
.venv\Scripts\python.exe -m scripts.check_stage4_document_api
.venv\Scripts\python.exe -m scripts.check_stage5_retrieval_api
pnpm exec supabase db lint --local --schema public --schema private
git diff --check
```

## Failures found and corrected

1. The reviewed gateway’s broad “any evidence” test let unrelated private records satisfy unsupported requests. Fixed with typed purpose-aware requirements.
2. Relevant conflicts/missing information were checked only after broad evidence was empty. Fixed with relevance filtering and blocking clarification precedence.
3. Caller request data could participate in applicability before the trusted journey/state boundary was explicit. Fixed by resolving authenticated database state first.
4. Personal context was collected too broadly. Fixed by purpose/domain/query minimisation and a separate safety-context contract.
5. During final evidence inspection, the yoga-conflict packet still included a peanut-allergy passage because both text strings contained “record.” Fixed by excluding generic container words as sole passage relevance and adding a regression assertion.
6. The original five-case development truth did not cover the rectification contract. Replaced with 26 frozen cases spanning all required states and domains.
7. The previous handoff contained stale counts and a Stage 6 GO. Rewritten with current evidence and the required independent re-review gate.
8. Unscoped lint after pgTAP included third-party functions in the extensions schema and reported extension-internal findings. The final lint command explicitly scopes Nestline application schemas public/private and returns zero findings.

## Honest limitations

Fixture embeddings are deterministic SHA-256 vectors, not a production semantic embedding. The synthetic development set is intentionally small and does not prove real-world retrieval or clinical correctness. Latency is local and does not establish a production service level.

The repository has 63 draft weekly profiles and zero publicly released weekly profiles. Controlled fixture evidence is isolated test data. Clinical, India-localisation, licence, product/publication and production-provider work remains open.

## Open gates

| Owner | Gate |
|---|---|
| Independent reviewer | Accept or return this Stage 5 rectification |
| Clinical reviewer | Approve applicable health and safety content |
| India-localisation reviewer | Approve local wording and care navigation |
| Licence reviewer | Approve source reuse/embedding rights |
| Product reviewer | Complete rendered review and publication decisions |
| Platform/product | Benchmark and select a production embedding provider |
| Stage 6 engineering/reviewers | Implement and independently review the Safety Gate after Stage 5 acceptance |

## Final decision

Stage 5 is ready for independent re-review. The regenerated Stage 5 checker and final Git check pass. Stage 6 is not started and remains blocked until review acceptance. Public, clinical and production release remain blocked.

The rectification implementation commit was pushed to the review branch. Nothing was merged or deployed.
