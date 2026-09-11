# Stage 2 independent-review response

**Reviewed handoff:** `NESTLINE-STAGE-2-INDEPENDENT-REVIEW-AND-CORRECTION-HANDOFF.md`  
**Correction date:** 11 September 2026  
**Result:** all eight findings accepted and addressed; no requested finding was rejected

| Finding | Decision and implementation | Evidence |
|---|---|---|
| S2-F01 roles | Adopted the owner-only capstone option. Non-owner rows and client membership mutation are rejected. | migration `00400`; decision 0003; live role test |
| S2-F02 reproducibility | Added project-local Supabase CLI, Docker pgTAP suite and CI for both upgrade and clean paths. | `package.json`, lockfile, workflow and the then-reported 141 assertions; see the later evidence correction |
| S2-F03 dependencies | Added five normalized dependency tables, same-workspace/current-fact validation, transactional stale transitions and graph cleanup. | migration `00600`; deletion assertions |
| S2-F04 reset | Added exact-prefix Storage listing/deletion service and versioned per-session create/reseed functions. | lifecycle service; migration `00700`; unit and live reset tests |
| S2-F05 episode model | Formally adopted one workspace as one care episode; owner/episode are derived through the workspace. | decision 0003; architecture update |
| S2-F06 live matrix | Expanded the two-principal suite across all 16 private tables and special boundaries. The current tracked file pins 122 assertions; the historical 141 source is unavailable. | `supabase/tests/stage2_security_and_lifecycle.test.sql` |
| S2-F07 journey rules | Added exact database and Pydantic rules for every supported stage/timing source, with positive and negative cases. | migration `00500`; `tests/test_storage.py` |
| S2-F08 typed records | Exported 18 complete records: all 16 personal tables plus workspace and owner membership. | `app/schemas/storage.py`; generated JSON schema |

## Additional defect found during correction

The original broad personal-table policy still allowed an owner to delete a
`private_documents` row directly, bypassing the intended Storage-first function.
Migration `00800` removes that policy, creates read/create/update-only metadata
policies, revokes direct delete permission and gives only the owner-checked
lifecycle functions the required delete right. The live suite proves both the
denied direct route and the successful post-Storage route.

## Verification result

- Clean database: all ten migrations replayed successfully.
- Upgrade database: migrations six through ten applied over the deployed five.
- Database: the historical run reported 141/141 assertions; the source for that exact run was not preserved. The current file pins 122/122, and lint returns zero errors.
- Local APIs: 13/13 Auth, REST and Storage checks passed; temporary users,
  workspaces and objects were removed.
- Python: 130/130 unit tests passed.
- Content contracts: 64/64 deterministic cases passed.
- Stage 1 continuity: 54 governed decisions remain valid with zero review-ledger,
  source or audit errors. The separate `PC00`/`P10`/`PP01` specialist handoff was
  not changed or treated as part of this Stage 2 review.
- Remote `nestline-dev`: ten migrations, 28 RLS-enabled tables, five normalized
  dependency tables, zero direct document-delete grants and zero test fixtures.
- GitHub: no push was performed during this correction pass.

Stage 2 engineering is complete. Stage 0 specialist approvals remain a separate
release gate and are not claimed here.
