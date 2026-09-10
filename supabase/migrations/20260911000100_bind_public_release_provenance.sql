-- Bind every public-ingestion relationship to one immutable content release.
-- Stable source/evidence IDs may repeat in later releases without crossing provenance.

begin;

alter table public.ingestion_runs add column release_id uuid;
update public.ingestion_runs run
set release_id = coalesce(
  (select artifact.release_id from public.source_artifacts artifact
   where artifact.id = run.source_artifact_id),
  (select source.release_id from public.public_sources source
   where source.source_id = run.source_id)
);
alter table public.ingestion_runs alter column release_id set not null;
alter table public.ingestion_runs
  add constraint ingestion_runs_release_id_fkey
  foreign key (release_id) references public.content_releases(id) on delete restrict;

alter table public.evidence_review_decisions add column release_id uuid;
update public.evidence_review_decisions decision
set release_id = task.release_id
from public.evidence_review_tasks task
where task.task_id = decision.task_id;
alter table public.evidence_review_decisions alter column release_id set not null;

-- Remove single-column links before changing the referenced keys.
alter table public.evidence_review_decisions
  drop constraint if exists evidence_review_decisions_task_id_fkey;
alter table public.evidence_review_tasks
  drop constraint if exists evidence_review_tasks_run_id_fkey,
  drop constraint if exists evidence_review_tasks_source_id_fkey;
alter table public.guideline_chunks
  drop constraint if exists guideline_chunks_source_id_fkey;
alter table public.source_blocks
  drop constraint if exists source_blocks_source_id_fkey,
  drop constraint if exists source_blocks_source_artifact_id_fkey;
alter table public.ingestion_runs
  drop constraint if exists ingestion_runs_source_id_fkey,
  drop constraint if exists ingestion_runs_source_artifact_id_fkey;
alter table public.source_artifacts
  drop constraint if exists source_artifacts_source_id_fkey;

-- IDs identify records inside a release; UUID artifact/decision IDs remain global.
alter table public.public_sources drop constraint if exists public_sources_pkey;
alter table public.public_sources
  add constraint public_sources_pkey primary key (release_id, source_id);

alter table public.source_blocks drop constraint if exists source_blocks_pkey;
alter table public.source_blocks
  add constraint source_blocks_pkey primary key (release_id, block_id);

alter table public.ingestion_runs drop constraint if exists ingestion_runs_pkey;
alter table public.ingestion_runs
  add constraint ingestion_runs_pkey primary key (release_id, run_id);

alter table public.evidence_review_tasks drop constraint if exists evidence_review_tasks_pkey;
alter table public.evidence_review_tasks
  add constraint evidence_review_tasks_pkey primary key (release_id, task_id);

alter table public.source_artifacts
  drop constraint if exists source_artifacts_source_id_logical_version_id_key,
  drop constraint if exists source_artifacts_source_id_original_sha256_key;
alter table public.source_artifacts
  add constraint source_artifacts_release_logical_key
    unique (release_id, source_id, logical_version_id),
  add constraint source_artifacts_release_hash_key
    unique (release_id, source_id, original_sha256),
  add constraint source_artifacts_release_identity_key
    unique (release_id, source_id, id);

alter table public.ingestion_runs
  add constraint ingestion_runs_release_identity_key
    unique (release_id, source_id, run_id);

alter table public.evidence_review_tasks
  drop constraint if exists evidence_review_tasks_candidate_id_candidate_checksum_key;
alter table public.evidence_review_tasks
  add constraint evidence_review_tasks_release_candidate_key
    unique (release_id, candidate_id, candidate_checksum),
  add constraint evidence_review_tasks_release_identity_key
    unique (release_id, task_id);

alter table public.evidence_review_decisions
  drop constraint if exists evidence_review_decisions_task_id_role_key;
alter table public.evidence_review_decisions
  add constraint evidence_review_decisions_release_role_key
    unique (release_id, task_id, role);

-- Composite foreign keys make cross-release references impossible.
alter table public.source_artifacts
  add constraint source_artifacts_release_source_fkey
  foreign key (release_id, source_id)
  references public.public_sources(release_id, source_id) on delete restrict;

alter table public.source_blocks
  add constraint source_blocks_release_source_fkey
  foreign key (release_id, source_id)
  references public.public_sources(release_id, source_id) on delete restrict,
  add constraint source_blocks_release_artifact_fkey
  foreign key (release_id, source_id, source_artifact_id)
  references public.source_artifacts(release_id, source_id, id) on delete restrict;

alter table public.ingestion_runs
  add constraint ingestion_runs_release_source_fkey
  foreign key (release_id, source_id)
  references public.public_sources(release_id, source_id) on delete restrict,
  add constraint ingestion_runs_release_artifact_fkey
  foreign key (release_id, source_id, source_artifact_id)
  references public.source_artifacts(release_id, source_id, id) on delete restrict;

alter table public.evidence_review_tasks
  add constraint evidence_review_tasks_release_run_fkey
  foreign key (release_id, source_id, run_id)
  references public.ingestion_runs(release_id, source_id, run_id) on delete cascade;

alter table public.evidence_review_decisions
  add constraint evidence_review_decisions_release_task_fkey
  foreign key (release_id, task_id)
  references public.evidence_review_tasks(release_id, task_id) on delete cascade;

alter table public.guideline_chunks
  add constraint guideline_chunks_release_source_fkey
  foreign key (release_id, source_id)
  references public.public_sources(release_id, source_id) on delete restrict;

commit;
