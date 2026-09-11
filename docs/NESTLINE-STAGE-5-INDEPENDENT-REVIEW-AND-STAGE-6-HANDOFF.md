# Stage 5 final verification, independent review and Stage 6 handoff

**Prepared:** 11 September 2026
**Branch:** `feat/stage-1-governed-ingestion`
**Baseline before Stage 5:** `b57f37b`
**Stage 5 commit:** PENDING - awaiting Kajal/Aswath authorization
**Scope:** typed hybrid retrieval, permission-safe personalization and bounded PostgreSQL causal graph
**Engineering verdict:** local Stage 5 completion gate passed
**Public/clinical verdict:** NO-GO; required human and release gates remain open
**Remote actions at preparation time:** none

## Purpose and review boundary

This is the single reviewer-facing guide for Stage 5. It joins the agreed architecture, implementation inventory, security boundaries, frozen retrieval truth, measured experiments, failure/recovery evidence and Stage 6 entry rules.

A Stage 5 engineering pass means that the controlled synthetic retrieval pipeline behaves as specified. It does not approve health content, select a production embedding provider, validate clinical quality, implement Stage 6 safety, or permit public use. Retrieval remains read-only.

## Exact bundle under review

| Item | Identity |
|---|---|
| Baseline before Stage 5 | b57f37b |
| Retrieval contract version | 5.0.0 |
| Migration | 20260911001300_stage5_hybrid_retrieval.sql |
| Migration SHA-256 | d384b4ce550d835e3899931a33a5ab6f5d5f8136bd15ef1542529dd42ac4e7d2 |
| Frozen development set | evals/stage5_retrieval_development.jsonl; five synthetic cases |
| Controlled corpus | data/synthetic/stage5_retrieval_fixtures.json; no real medical data |
| Machine verdict | docs/STAGE-5-CHECK-RESULTS.json: valid true |
| Weekly release state | 63 draft profiles; zero published profiles |
| Database verification | 254/254 pgTAP assertions |
| Authenticated API verification | 67/67 checks; 22 Stage 5 |
| Paid model required by CI | No |
| Stage 5 implementation commit | PENDING until the authorized commit is created |

## Decision requested from the reviewer

Decide whether the local Stage 5 engineering is ready to become the shared baseline for Stage 6, or list concrete corrections. This review does not approve medical content, public use, or Stage 6 safety behavior.

## Read these first

1. `docs/NESTLINE-EXECUTION-PLAN.md`
2. `docs/Nestline updated architecture.md`
3. `docs/STAGE-2-3-4-INDEPENDENT-REVIEW-RESPONSE-AND-STAGE-5-GATE.md`
4. `docs/STAGE-4-REVIEW-HANDOFF.md`
5. `docs/decisions/0003-owner-only-workspace-care-episode.md`
6. `docs/decisions/0004-document-extraction-provider-selection.md`
7. `docs/STAGE-5-IMPLEMENTATION.md`
8. `docs/STAGE-5-PLAIN-LANGUAGE.md`
9. `docs/STAGE-5-SELF-VERIFICATION-AND-STAGE-6-READINESS.md`
10. `docs/STAGE-5-CHECK-RESULTS.json`
11. `docs/STAGE-5-RETRIEVAL-METRICS.json`

## What to review

| Area | Primary evidence | Question |
|---|---|---|
| Typed boundary | `app/schemas/retrieval.py`, exported JSON Schema | Is every request, candidate, path, trace, failure and packet state explicit and versioned? |
| One gateway | `app/services/retrieval.py` | Do future specialists share one read-only SQL, FTS, vector and graph gateway? |
| Scope and permissions | Migration, pgTAP and authenticated API checker | Is scope derived from `auth.uid()` and are ordinary calls free of service-role credentials? |
| Hard filters | Migration and Stage 5 tests | Are private, wrong-week, wrong-stage, wrong-country, draft, retired and wrong-lane rows removed before ranking? |
| Deterministic ranking | Service and evaluation report | Is reciprocal-rank fusion stable, bounded and reproducible? Was the ineffective score trial rejected honestly? |
| Causal graph | Migration, graph fixtures and tests | Is document-to-restriction/conflict-to-plan-to-stale-plan/question traversal bounded, cycle-safe and workspace-safe? |
| Caching | Service, migration and negative tests | Are public and personal caches separate, version-bound and invalidated after confirmed state changes? |
| Frozen truth | Development JSONL and fixture builder | Were expected and forbidden IDs defined before the measured experiments? |
| Evaluation | Runner and metrics JSON | Are vector-only, hybrid, one ranking trial and graph on/off results comparable and reported with denominators? |
| Migration histories | Upgrade fixtures and CI workflow | Do exact Stage 4 upgrade, deployed Stage 3 through Stage 5, and clean replay all pass? |
| Regression | Stage 5 checker and CI workflow | Do Stage 1-4 gates remain present and green without paid-model credentials? |

## Architecture and completion map

| Requirement | Implemented evidence | Result |
|---|---|---|
| Versioned typed contracts | 15 exported request, scope, candidate, graph, rank, packet, trace and failure contracts | Pass |
| One retrieval gateway | Exact SQL, full text, pgvector and bounded graph share one service boundary | Pass |
| Server-derived scope | auth.uid() resolves owner workspace/care episode; request exposes no scope override | Pass |
| Confirmed-only personalization | Proposed, rejected, superseded and conflicted facts are excluded from active context | Pass |
| Hard filters before ranking | Release, lane, lifecycle, stage, week/range, country, domain, conditions, versions and retirement apply in SQL | Pass |
| Deterministic ranking | Stable reciprocal-rank fusion with bounded counts and tie-breaking; learned reranker disabled | Pass |
| Bounded graph | Document-only starts, depth four, path limit eight, cycle protection and workspace isolation | Pass |
| Cache isolation | Separate public/personal keys; workspace/state/release/filter versions and invalidation tested | Pass |
| Explicit failures | Abstention, clarification, missing information, timeout, database and vector-degradation states | Pass |
| Security negatives | Cross-user SQL/vector/graph/cache, decoy and lifecycle tests are executable | Pass |
| Frozen evaluations | Expected, forbidden and graph IDs were recorded before tuning | Pass |
| Required experiments | Vector baseline, hybrid, one rejected ranking trial and graph on/off ablation reported | Pass |
| Migration discipline | Exact Stage 4 upgrade, deployed Stage 3 path and clean replay passed; migration remains undeployed | Pass |
| Regression and CI | Stage 1-4 gates remain green; deterministic Stage 5 job needs no paid model | Pass |

## Reproduced local results

- Python unit tests: **203/203 passed**.
- Content contract cases: **64/64 passed**.
- Journey cases: **26/26 passed**.
- Database pgTAP: **254/254 passed** on exact upgrades and clean replay.
- Authenticated API checks: **67/67 passed**.
- Frozen Stage 5 behaviors: **5/5 passed**.
- Public Recall@5: **2/2 = 1.00**.
- Public evidence precision: **2/10 = 0.20**.
- Confirmed personal fact precision and recall: **8/8 = 1.00** each.
- Graph correctness: **0/1 without graph; 1/1 with graph**.
- Wrong-week, wrong-jurisdiction, unapproved-source, cross-workspace and proposal/conflict personalization violations: **0 each**.
- Database lint: **zero findings**.
- Weekly profiles: **63 draft, 0 published**.

The low public evidence precision is retained as a visible limitation. The small controlled corpus proves filtering, provenance and deterministic behavior; it does not prove production retrieval or clinical quality.

## Focused reproduction commands

Run these from the repository root with Docker Desktop running:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -q
.venv\Scripts\python.exe -m scripts.run_contract_evals
.venv\Scripts\python.exe -m scripts.run_journey_evals
.venv\Scripts\python.exe -m scripts.check_stage1
.venv\Scripts\python.exe -m scripts.check_stage2
.venv\Scripts\python.exe -m scripts.check_stage3
.venv\Scripts\python.exe -m scripts.check_stage3_ui
.venv\Scripts\python.exe -m scripts.check_stage4_readiness
.venv\Scripts\python.exe -m scripts.check_stage4_ui
.venv\Scripts\python.exe -m scripts.check_stage4
.venv\Scripts\python.exe -m scripts.check_stage5 --write-report
.venv\Scripts\python.exe -m scripts.check_stage5_retrieval_api
pnpm exec supabase db lint --local
```

The exact migration-history commands and per-file pgTAP commands are recorded in `docs/STAGE-5-SELF-VERIFICATION-AND-STAGE-6-READINESS.md`.

## Reviewer questions

1. Can any client-supplied workspace or care-episode value alter the authenticated scope?
2. Can a proposed, conflicted, rejected or superseded fact reach active personal context?
3. Can any filtered decoy survive and merely receive a low ranking score?
4. Can a graph path cross a workspace, exceed four edges, repeat a node or begin from an unpermitted node?
5. Can public cache data contain personal information, or can one workspace reuse another workspace's personal entry?
6. Do medication and symptom records stay within their record-only and safety-evaluation-only claim types?
7. Do the reported graph results distinguish the relationship-dependent case from the SQL-sufficient case?
8. Do any documents overstate clinical approval, public readiness, provider superiority, agent completion or Stage 6 behavior?

## Failures found and corrected

1. PostgreSQL result ordering used an alias unavailable inside one SQL function; ordering now uses the stable output position.
2. A graph-identity change broke a Stage 4 ON CONFLICT path; the original UUID constraint was restored and public release identity uses a separate partial index.
3. Removing legacy RPCs broke earlier contracts; strict compatibility wrappers preserve Stage 1-4 behavior while the Stage 5 gateway uses the new reads.
4. An old Stage 2 expectation exposed an unconfirmed chunk; the test now enforces the confirmed-document retrieval boundary.
5. Graph traversal originally matched every query word in one node; it now accepts a meaningful path term while retaining every hard scope and permission filter.
6. A multi-domain evidence row could inherit the wrong displayed domain; SQL now returns the requested domain that passed the membership filter.
7. The Stage 5 fixture changed a broad Stage 0 review fingerprint; downstream retrieval fixtures are now explicitly outside that human-review subject, with a regression test.
8. The single score-ranking trial improved neither Recall@5 nor evidence precision, so it was documented and rejected.

## Known limitations and open gates

- The deterministic SHA-256 embedding is a CI fixture technique, not a semantic production embedding model.
- The development set has five synthetic cases and is separate from the future sealed project holdout.
- No weekly profile is publicly released, so development uses an isolated controlled release lane.
- Clinical, India-localisation, licence and full product/publication reviews remain open with their named human owners.
- A production embedding provider still needs a separately controlled benchmark and approval; Stage 5 does not silently choose one.
- Stage 6 must still implement and obtain review for the live Safety Gate.
- Real document upload remains blocked by its scanning and human-review gates.

## Recommendation

**GO** for local Stage 6 engineering after reviewer acceptance of this local change set. **NO-GO** for public, clinical or production use. The Git commit field must remain pending until Kajal/Aswath authorizes a commit, and remote CI can only be claimed after an approved push.