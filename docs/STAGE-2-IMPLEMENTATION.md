# Stage 2 — Supabase storage and workspace isolation

Updated 11 September 2026 after the independent review correction pass. This is
the technical source of truth for Stage 2.

## Outcome

Stage 2 is implemented and deployed to the `nestline-dev` Supabase project. Ten
ordered migrations create 28 tables, enable Row Level Security on all 28, create
the private `medical-documents` bucket, add dimension-neutral pgvector columns,
and enforce authenticated workspace lifecycle operations. The remote database
contains no real medical data, published health corpus, production embeddings or
Stage 2 test fixtures.

The capstone uses an explicit owner-only model. One workspace represents one
pregnancy-through-postpartum care episode. A later pregnancy begins in a new
workspace. Ownership is derived from `workspaces.owner_user_id`; child rows do not
duplicate an `owner_id` or `episode_id`. The decision and future collaboration
boundary are recorded in `docs/decisions/0003-owner-only-workspace-care-episode.md`.

## Stored data

| Area | Tables | Access rule |
|---|---|---|
| Workspace and owner | `workspaces`, `workspace_members` | One authenticated owner; non-owner roles are rejected |
| Governed public knowledge | `content_releases`, `public_sources`, `source_artifacts`, `source_blocks`, `ingestion_runs`, `evidence_review_tasks`, `evidence_review_decisions`, `weekly_profiles`, `guidance_fragments`, `guideline_chunks` | API clients read only published release data; ingestion/review internals remain administrative |
| Journey and private records | `journey_states`, `private_documents`, `document_chunks`, `document_facts`, `health_facts`, `medication_mentions`, `symptom_events`, `appointments`, `appointment_questions` | Database derives access from the authenticated workspace owner |
| Plans and continuity | `plans`, `plan_items`, `graph_nodes`, `graph_edges` | Same owner boundary; cross-workspace parent references are rejected |
| Review and operation state | `human_review_cases`, `notifications`, `feedback` | Same owner boundary; notifications use workspace-scoped idempotency keys |

## Independent-review corrections

1. Non-owner membership is disabled. The database rejects `editor`, `reviewer`
   and `viewer` rows instead of giving misleading labels identical powers.
2. CI starts Supabase in Docker and tests both an upgrade from migration five and
   a clean installation from zero.
3. Five private dependency tables validate fact, public-guidance and evidence
   relationships. Deleting or superseding a current health fact makes dependent
   plans, plan items and appointment questions stale, forces journey
   reconfirmation and removes its graph node in one transaction.
4. `reset_seeded_demo_workspace` lists and deletes the exact Storage prefix before
   invoking the database reseed. Storage failure prevents the database reset.
5. Demo workspaces are session-scoped, use the versioned `maya-v1` seed, and are
   idempotent for the same owner/session key.
6. Journey-stage checks now define each allowed timing-source combination,
   including unresolved possible pregnancy, manual week/day, due-date-derived,
   approximate month, delivery-date and postpartum week/day input.
7. Typed application contracts cover all 16 personal tables plus workspace and
   owner membership.
8. Direct `DELETE` permission on `private_documents` is revoked. The owner-checked
   deletion function succeeds only after the corresponding Storage object is gone.

## Migrations

1. `20260910000100_stage2_storage.sql` — base schema, RLS, Storage and vector functions.
2. `20260910000200_protect_workspace_owner.sql` — protects owner membership.
3. `20260911000100_bind_public_release_provenance.sql` — binds ingestion records to one release.
4. `20260911000200_workspace_lifecycle.sql` — workspace creation, journey compare-and-set and reset.
5. `20260911000300_workspace_owner_visibility.sql` — permits owner visibility during creation.
6. `20260911000400_owner_only_episode_boundary.sql` — owner-only access and workspace-as-episode rule.
7. `20260911000500_journey_state_invariants.sql` — strict journey/timing combinations.
8. `20260911000600_personal_dependency_invalidation.sql` — normalized dependencies and stale transitions.
9. `20260911000700_versioned_demo_workspaces.sql` — per-session deterministic demo creation/reseed.
10. `20260911000800_enforce_storage_first_documents.sql` — closes direct metadata-deletion bypass.

All ten appear in remote migration history. The secret-free verification record
binds each file to its canonical SHA-256 and records the remote schema counts.

## Verification

The current database suite pins 122 pgTAP assertions. It uses two fictional authenticated
principals and covers policy inventory, owner/non-owner read and update behavior for
all 16 personal tables, permitted deletes, the protected document exception,
cross-workspace parent references, private vector retrieval, Storage policies,
owner-only roles, dependency invalidation, document cascades and three demo resets.
The transaction rolls back every fixture.

A separate local API check uses two temporary authenticated users to exercise the
real Auth, REST and Storage endpoints. Its 13 checks cover owner upload, listing,
reading, updating and deleting; outsider denial; the Storage-first metadata gate;
and complete fixture cleanup. It never prints credentials, file contents or
personal data.

Run from the repository root:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe -m scripts.check_stage2
pnpm exec supabase start
pnpm exec supabase db reset --local
pnpm exec supabase test db --local
pnpm exec supabase db lint --local
```

The CI workflow repeats the live suite twice: after upgrading the previously
deployed five-migration schema and after a clean ten-migration replay.

Review these artifacts:

- `data/supabase/remote-verification.json` — secret-free remote deployment proof;
- `docs/STAGE-2-CHECK-RESULTS.json` — generated static/remote contract result;
- `data/schemas/storage.schema.json` — 18 application record contracts;
- `supabase/tests/stage2_security_and_lifecycle.test.sql` — live database matrix;
- `scripts/check_stage2_storage_api.py` — local Auth/REST/Storage boundary check;
- `docs/STAGE-2-INDEPENDENT-REVIEW-RESPONSE.md` — finding-by-finding closure.

## Stage boundary

Stage 2 supplies storage, isolation, dependency integrity and repeatable demo
state. Stage 3 connects Auth to onboarding and calculates journey timing. Stage 4
uploads fictional documents and implements extraction plus user confirmation.
Stage 5 selects the embedding model, loads only approved public records and builds
hybrid retrieval. Human approval remains the Stage 0 release gate, so public health
content and production embeddings remain unpublished.
