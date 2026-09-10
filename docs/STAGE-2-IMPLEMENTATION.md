# Stage 2 — Supabase storage and workspace isolation

Updated 11 September 2026. This is the technical source of truth for the Stage 2 storage foundation.

## Outcome

The Stage 2 database foundation is implemented, migrated to the `nestline-dev`
Supabase project and recorded in Supabase migration history. It contains 28
tables, Row Level Security on all 28 tables, a private `medical-documents`
bucket, dimension-neutral pgvector columns and bounded public/private vector
functions. The database currently contains no real medical data and no
published health corpus.

A transactional two-principal test exercised SQL rows, private vectors, graph
nodes, Storage object access and a cross-workspace update. All nine assertions
passed: user A saw A's records, user B saw zero A records, and B changed zero A
rows. A separate lifecycle transaction proved authenticated workspace creation,
atomic journey versions, stale-update rejection, document-hash deduplication and
demo reset. Every fictional test user and row was rolled back.

## Stored data

| Area | Tables | Access rule |
|---|---|---|
| Workspace and membership | `workspaces`, `workspace_members` | Authenticated owner/member only |
| Governed public knowledge | `content_releases`, `public_sources`, `source_artifacts`, `source_blocks`, `ingestion_runs`, `evidence_review_tasks`, `evidence_review_decisions`, `weekly_profiles`, `guidance_fragments`, `guideline_chunks` | API clients can read only explicitly published release data; ingestion/review internals are admin-only |
| Journey and private records | `journey_states`, `private_documents`, `document_chunks`, `document_facts`, `health_facts`, `medication_mentions`, `symptom_events`, `appointments`, `appointment_questions` | Database checks authenticated workspace membership |
| Plans and continuity | `plans`, `plan_items`, `graph_nodes`, `graph_edges` | Same workspace boundary; cross-workspace child references are rejected |
| Review and operation state | `human_review_cases`, `notifications`, `feedback` | Same workspace boundary; notifications have workspace-scoped idempotency keys |

## Security and correctness controls

- The client uses the authenticated Supabase user. Ordinary reads and writes do
  not need a service-role key.
- Workspace ownership comes from `auth.uid()`. A client cannot nominate a
  different owner through `create_workspace`.
- Owner membership cannot be inserted, rewritten or removed through the client
  membership policies. Non-owner membership changes remain owner-controlled.
- Public source, artifact, block, ingestion-run, review-task and review-decision
  relationships use composite release keys. A stable ID from one corpus release
  cannot silently point into another release.
- Every one of the 16 user-owned tables has a membership policy. Public knowledge
  has separate published-only policies; source artifacts and ingestion/review
  tables have no anon/authenticated grant.
- The private Storage bucket accepts PDF, PNG and JPEG objects up to 10 MB. Its
  first path segment must be a workspace UUID visible to the signed-in user.
- Deleting a private document cascades to its document chunks, extracted facts,
  document-sourced facts/medication mentions and document graph nodes/edges.
- Duplicate document bytes are blocked per workspace by `(workspace_id, sha256)`.
- Journey updates use `replace_current_journey_state`, which locks the workspace,
  checks the expected current version and atomically creates exactly one new
  current version. A stale caller receives a serialization error.
- `reset_demo_workspace_state` works only for the authenticated owner of a
  fictional demo workspace and checks the workspace timestamp. It refuses to
  proceed while Storage objects remain, because files must first be deleted via
  the Storage API rather than by removing database metadata directly.
- Plans cannot become saved/active until `user_confirmed_at` exists.
- Vector dimensions remain unset until the team chooses the exact embedding
  provider/model. No HNSW/IVFFlat index is created for an unknown dimension.
- Private vector search takes an explicit workspace and checks membership inside
  the database. Public vector search filters published release/status, journey
  scope, jurisdiction and vector dimension, and caps results at 20.

## Migrations

1. `20260910000100_stage2_storage.sql` creates the full schema, policies,
   Storage bucket and vector functions.
2. `20260910000200_protect_workspace_owner.sql` protects the immutable owner
   membership from client mutation.
3. `20260911000100_bind_public_release_provenance.sql` binds all public
   ingestion provenance to one content release.
4. `20260911000200_workspace_lifecycle.sql` adds authenticated workspace
   creation, atomic journey replacement, safe demo reset and document deduplication.
5. `20260911000300_workspace_owner_visibility.sql` fixes `INSERT ... RETURNING`
   for a newly created owner before the membership trigger completes.

All five appear in `supabase_migrations.schema_migrations`. The tracked,
secret-free evidence file binds each migration filename to its canonical-text
SHA-256 (UTF-8 with normalised line endings) and records the live check counts.

## Verification

Run locally from the repository root:

```powershell
.venv/Scripts/python.exe -m scripts.check_stage2
.venv/Scripts/python.exe -m unittest tests.test_storage -v
```

The first command checks all five SQL migrations, exported storage contracts,
tracked remote counts and the exact migration-file hashes. CI runs it after the
full Python tests and the Stage 0/1 checks.

Review these artifacts:

- `data/supabase/remote-verification.json` — secret-free live deployment proof;
- `docs/STAGE-2-CHECK-RESULTS.json` — generated check result;
- `data/schemas/storage.schema.json` — application/storage contracts;
- `tests/test_storage.py` — static and typed negative tests.

## Stage boundary

Stage 2 supplies secure places and controlled state transitions. Stage 3 will
connect Supabase Auth to onboarding and calculate journey timing. Stage 4 will
upload only fictional/demo documents, delete file objects through the Storage
API before a reset, extract proposed facts and ask the user to confirm them.
Stage 5 will select an embedding provider, load approved public records and use
the filtered retrieval functions.

Human approval remains a Stage 0 content-release gate. Therefore public evidence
tables and embeddings remain empty even though the database is ready to receive
a future approved release.
