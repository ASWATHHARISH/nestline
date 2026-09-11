# Stage 5 self-verification and Stage 6 readiness

**Audit date:** 11 September 2026
**Auditor:** Codex engineering self-review
**Implementation commit:** a1f0489cd7b16cf2391cab58b8e558432c4f4bba
**Local engineering verdict:** GO for Stage 6 engineering
**Public/clinical release verdict:** NO-GO

## Completion-gate result

| Gate | Result |
|---|---|
| Expected evidence IDs retrieved | Pass: 2/2 expected public IDs across five development cases |
| Wrong-week evidence | Pass: 0 |
| Wrong-jurisdiction evidence | Pass: 0 |
| Unapproved/draft/rejected/retired evidence | Pass: 0 |
| Cross-workspace leakage | Pass: 0 |
| Confirmed personal fact precision | Pass: 8/8 |
| Confirmed personal fact recall | Pass: 8/8 |
| Proposal/conflict personalization violations | Pass: 0 |
| Graph path correctness | Pass: 1/1 with graph enabled |
| Deterministic expected behavior | Pass: 5/5 |
| SQL, full-text, vector and graph tests | Pass |
| Cache isolation and state-version invalidation | Pass |
| Exact Stage 4 -> Stage 5 upgrade | Pass; controlled rows preserved, backfilled and removed |
| Stage 3 -> Stage 4 -> Stage 5 upgrade | Pass |
| Clean migration history | Pass |
| Stage 1-4 regression gates | Pass |
| Secrets or real medical data | None found; Stage 5 corpus is synthetic |
| Public/provider/human gates | Open and explicitly recorded |

## Retrieval experiments

The order was frozen before tuning.

| Experiment | Recall@5 | Evidence precision | Confirmed fact recall | Graph correctness |
|---|---:|---:|---:|---:|
| Vector-only, same filtered corpus | 2/2 | 2/12 | 0/8 | 0/1 |
| Hybrid SQL + full text + vector | 2/2 | 2/10 | 8/8 | 0/1 |
| One authority/applicability score trial | 2/2 | 2/10 | 8/8 | 0/1 |
| Adopted hybrid, graph disabled | 2/2 | 2/10 | 8/8 | 0/1 |
| Adopted hybrid, graph enabled | 2/2 | 2/10 | 8/8 | 1/1 |

The score trial was not adopted because it improved neither Recall@5 nor precision.
Graph traversal adds required relationship information in S5-GRAPH-001. S5-SQL-001
is already answered by exact SQL, so no graph benefit is claimed for it.

## Latency from the final five-case in-memory run

These numbers are local development measurements, not production service-level
claims.

| Component | Calls | Mean ms | Maximum ms |
|---|---:|---:|---:|
| Exact SQL | 5 | 0.139 | 0.232 |
| Personal full text | 5 | 0.056 | 0.071 |
| Personal vector | 5 | 0.043 | 0.063 |
| Public full text | 5 | 0.558 | 0.607 |
| Public vector | 5 | 0.510 | 0.605 |
| Weekly profile | 5 | 0.002 | 0.002 |
| Graph | 5 | 0.030 | 0.078 |

The tracked machine-readable reports are docs/STAGE-5-CHECK-RESULTS.json and
docs/STAGE-5-RETRIEVAL-METRICS.json.

## Actual verification totals

- 203/203 Python tests.
- 64/64 content-contract cases.
- 26/26 journey cases.
- 254/254 pgTAP assertions: 122 Stage 2, 12 Stage 3 exit, 26 Stage 3 onboarding,
  11 Stage 4 API-role, 35 Stage 4 document and 48 Stage 5.
- 67/67 authenticated local API checks: 13 Storage, 17 onboarding, 15 documents and
  22 Stage 5 retrieval.
- Stage 3 and Stage 4 Streamlit smoke checks passed with zero network calls.
- Database lint: zero findings.
- Content authoring and review-ready validation: 63 profiles, zero published,
  31 sources, 55 evidence spans and 56 fragments; both modes passed.
- Both direct Stage 4 upgrade and clean installation passed. The older deployed
  Stage 3 upgrade path also passed through Stage 5.

## Exact commands used

- .venv/Scripts/python.exe -m unittest discover -s tests -q
- .venv/Scripts/python.exe -m scripts.validate_content
- .venv/Scripts/python.exe -m scripts.validate_content --require-review-ready
- .venv/Scripts/python.exe -m scripts.run_contract_evals
- .venv/Scripts/python.exe -m scripts.run_journey_evals
- .venv/Scripts/python.exe -m scripts.check_stage1
- .venv/Scripts/python.exe -m scripts.check_stage2
- .venv/Scripts/python.exe -m scripts.check_stage3_ui
- .venv/Scripts/python.exe -m scripts.check_stage3
- .venv/Scripts/python.exe -m scripts.check_stage4_readiness
- .venv/Scripts/python.exe -m scripts.check_stage4_ui
- .venv/Scripts/python.exe -m scripts.check_stage4
- .venv/Scripts/python.exe -m scripts.run_stage5_retrieval_evals
- .venv/Scripts/python.exe -m scripts.check_stage5 --write-report
- pnpm exec supabase db reset --local --version 20260911001200
- pnpm exec supabase migration up --local
- pnpm exec supabase db reset --local --version 20260911001000
- pnpm exec supabase db reset --local
- pnpm exec supabase test db --local supabase/tests/stage2_security_and_lifecycle.test.sql
- pnpm exec supabase test db --local supabase/tests/stage3_exit_hardening.test.sql
- pnpm exec supabase test db --local supabase/tests/stage3_onboarding.test.sql
- pnpm exec supabase test db --local supabase/tests/stage4_api_role_hardening.test.sql
- pnpm exec supabase test db --local supabase/tests/stage4_document_confirmation.test.sql
- pnpm exec supabase test db --local supabase/tests/stage5_hybrid_retrieval.test.sql
- .venv/Scripts/python.exe -m scripts.check_stage2_storage_api
- .venv/Scripts/python.exe -m scripts.check_stage3_onboarding_api
- .venv/Scripts/python.exe -m scripts.check_stage4_document_api
- .venv/Scripts/python.exe -m scripts.check_stage5_retrieval_api
- pnpm exec supabase db lint --local
- git diff --check

## Failures found and corrected

1. PostgreSQL could not resolve a component_score alias in a SQL-function ORDER BY.
   The query now orders by the output column position.
2. Replacing the legacy graph uniqueness constraint broke Stage 4 ON CONFLICT
   upserts. The UUID constraint was restored and a separate partial index was added
   for public release-bound nodes.
3. Revoking legacy retrieval RPCs broke Stage 2/4 compatibility. They were restored
   as stricter wrappers while the Stage 5 gateway uses the new RPCs.
4. A Stage 2 assertion expected an unconfirmed private document chunk. Its expected
   result now reflects the confirmed-document boundary.
5. The graph validator lacked architecture-approved canonical node types. The
   additive vocabulary and entity-reference validation now cover them.
6. Cache version triggers collided with workspace cascade cleanup. The trigger now
   treats the deleted workspace foreign-key race as an expected no-cache condition.
7. Graph query matching initially required every word in one node. It now matches a
   meaningful query term across the bounded path.
8. The authenticated API fixture initially conflicted with the supervised-demo
   ingestion rules. It now uses the controlled fictional workspace and seeded
   journey/plan state.
9. Multi-domain SQL evidence was labelled with the first array item. The candidate
   now carries the requested domain that already passed the SQL membership filter.
10. Adding Stage 5 synthetic truth changed the broad Stage 0 fingerprint and made a
    governed Stage 1 handoff stale. The Stage 5 fixture is now explicitly outside the
    Stage 0 human-review subject, with a regression test.
11. The one ranking adjustment did not improve the frozen metrics. It remains a
    documented trial and is not active.

## Honest limitations

The deterministic SHA-256 embedding verifies interfaces, filters, provider
independence and repeatability, but it is not semantic and cannot predict production
embedding quality. The five-case development set is small and is not a sealed final
holdout. Evidence precision is only 2/10 because the deliberately noisy eligible
corpus returns broad passages; this should guide a later, separately measured
retrieval improvement. It is not hidden or described as clinical quality.

The graph reader is complete, but Stage 5 is read-only. Existing confirmed records
need the Stage 4/10 State Committer to create all causal plan-dependency edges.
Stage 5 never writes missing edges.

## Open gates and owners

| Owner | Open gate | Blocks Stage 6 engineering | Blocks public use |
|---|---|---:|---:|
| Aswath/Kajal | Approve commit and push, then require both GitHub jobs to pass | Shared baseline only | Yes |
| Qualified clinician | Approve applicable health and safety content | No | Yes |
| India-localisation reviewer | Approve India-specific wording and navigation | No | Yes |
| Licence reviewer | Approve source reuse and embedding rights | No | Yes |
| Kajal/product | Complete rendered product acceptance and publication decisions | No | Yes |
| Stage 6 engineering/reviewers | Implement and approve the Safety Gate | Next work | Yes |
| Platform/product | Select and benchmark a production embedding provider/model | No | Yes |
| Product/security/platform | Finish trusted real-upload malware scanning | No | Yes |

## Decision

GO for local Stage 6 engineering because the Stage 5 completion gate and all earlier
regressions pass. NO-GO for public, clinical or production use. GitHub CI cannot be
claimed until the local changes are approved, committed and pushed.

The implementation is committed as a1f0489cd7b16cf2391cab58b8e558432c4f4bba. No migration was deployed; branch publication and remote CI are verified separately.