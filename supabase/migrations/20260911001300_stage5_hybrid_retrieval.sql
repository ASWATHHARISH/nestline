-- Nestline Stage 5: filter-first hybrid retrieval and bounded causal graph.
-- This migration is additive and remains undeployed until explicitly approved.

begin;

-- Extend the personal graph vocabulary without replacing any Stage 4 values.
alter table public.graph_nodes drop constraint if exists graph_nodes_node_type_check;
alter table public.graph_nodes add constraint graph_nodes_node_type_check check (node_type in (
  'document', 'fact', 'restriction', 'symptom', 'appointment', 'question',
  'plan', 'plan_item', 'person', 'journey_state', 'weekly_profile',
  'document_fact', 'medication_mention', 'allergy', 'condition',
  'guideline_evidence', 'human_review_case', 'symptom_event'
));

-- UUID-backed personal entities and composite-key public entities use explicit,
-- non-overlapping reference shapes. Existing Stage 4 rows remain valid.
alter table public.graph_nodes
  alter column entity_id drop not null,
  add column entity_release_id uuid references public.content_releases(id) on delete restrict,
  add column entity_key text;
alter table public.graph_nodes
  drop constraint if exists graph_nodes_workspace_id_node_type_entity_id_key;
alter table public.graph_nodes add constraint graph_nodes_entity_reference_check check (
  (
    node_type in ('weekly_profile', 'guideline_evidence')
    and entity_id is null and entity_release_id is not null
    and length(trim(entity_key)) > 0
  ) or (
    node_type not in ('weekly_profile', 'guideline_evidence')
    and entity_id is not null and entity_release_id is null and entity_key is null
  )
);
alter table public.graph_nodes add constraint
  graph_nodes_workspace_id_node_type_entity_id_key
  unique (workspace_id, node_type, entity_id);
create unique index graph_nodes_public_entity_unique
  on public.graph_nodes(workspace_id, node_type, entity_release_id, entity_key)
  where entity_release_id is not null;

create or replace function private.validate_graph_node_entity()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare entity_exists boolean := false;
begin
  case new.node_type
    when 'person' then
      select exists(select 1 from public.workspaces
        where id = new.workspace_id and owner_user_id = new.entity_id)
        into entity_exists;
    when 'journey_state' then
      select exists(select 1 from public.journey_states
        where workspace_id = new.workspace_id and id = new.entity_id)
        into entity_exists;
    when 'weekly_profile' then
      select exists(select 1 from public.weekly_profiles profile
        join public.content_releases release on release.id = profile.release_id
        where profile.release_id = new.entity_release_id
          and profile.profile_id = new.entity_key
          and profile.status = 'published' and release.status = 'published')
        into entity_exists;
    when 'document' then
      select exists(select 1 from public.private_documents
        where workspace_id = new.workspace_id and id = new.entity_id)
        into entity_exists;
    when 'document_fact' then
      select exists(select 1 from public.document_facts
        where workspace_id = new.workspace_id and id = new.entity_id)
        into entity_exists;
    when 'medication_mention' then
      select exists(select 1 from public.medication_mentions
        where workspace_id = new.workspace_id and id = new.entity_id)
        into entity_exists;
    when 'allergy' then
      select exists(select 1 from public.health_facts
        where workspace_id = new.workspace_id and id = new.entity_id
          and fact_type = 'allergy') into entity_exists;
    when 'condition' then
      select exists(select 1 from public.health_facts
        where workspace_id = new.workspace_id and id = new.entity_id
          and fact_type in ('medical_history', 'other')) into entity_exists;
    when 'fact' then
      select exists(select 1 from public.document_facts
        where workspace_id = new.workspace_id and id = new.entity_id)
        or exists(select 1 from public.health_facts
        where workspace_id = new.workspace_id and id = new.entity_id)
        into entity_exists;
    when 'restriction' then
      select exists(select 1 from public.health_facts
        where workspace_id = new.workspace_id and id = new.entity_id)
        into entity_exists;
    when 'symptom', 'symptom_event' then
      select exists(select 1 from public.symptom_events
        where workspace_id = new.workspace_id and id = new.entity_id)
        into entity_exists;
    when 'appointment' then
      select exists(select 1 from public.appointments
        where workspace_id = new.workspace_id and id = new.entity_id)
        into entity_exists;
    when 'question' then
      select exists(select 1 from public.appointment_questions
        where workspace_id = new.workspace_id and id = new.entity_id)
        into entity_exists;
    when 'plan' then
      select exists(select 1 from public.plans
        where workspace_id = new.workspace_id and id = new.entity_id)
        into entity_exists;
    when 'plan_item' then
      select exists(select 1 from public.plan_items
        where workspace_id = new.workspace_id and id = new.entity_id)
        into entity_exists;
    when 'guideline_evidence' then
      select exists(select 1 from public.guideline_chunks chunk
        join public.content_releases release on release.id = chunk.release_id
        where chunk.release_id = new.entity_release_id
          and chunk.evidence_id = new.entity_key
          and chunk.status = 'published' and release.status = 'published')
        into entity_exists;
    when 'human_review_case' then
      select exists(select 1 from public.human_review_cases
        where workspace_id = new.workspace_id and id = new.entity_id)
        into entity_exists;
    else
      entity_exists := false;
  end case;
  if not entity_exists then
    raise exception 'graph node entity does not exist in this workspace or published release'
      using errcode = '23503';
  end if;
  return new;
end;
$$;
-- PostgreSQL full-text indexes support terminology and exact phrase discovery.
alter table public.guideline_chunks
  add column if not exists search_vector tsvector
  generated always as (to_tsvector('english', text)) stored;
alter table public.document_chunks
  add column if not exists search_vector tsvector
  generated always as (to_tsvector('english', text)) stored;
create index if not exists guideline_chunks_search_idx
  on public.guideline_chunks using gin(search_vector);
create index if not exists document_chunks_search_idx
  on public.document_chunks using gin(search_vector);

-- This monotonic version invalidates personal cache keys after relevant state writes.
create table public.personal_retrieval_versions (
  workspace_id uuid primary key references public.workspaces(id) on delete cascade,
  version bigint not null default 1 check (version >= 1),
  updated_at timestamptz not null default timezone('utc', now())
);

insert into public.personal_retrieval_versions(workspace_id, version)
select id, 1 from public.workspaces
on conflict (workspace_id) do nothing;

alter table public.personal_retrieval_versions enable row level security;
create policy "owners read personal retrieval versions"
on public.personal_retrieval_versions for select to authenticated
using (private.is_workspace_owner(workspace_id));
revoke all on public.personal_retrieval_versions from anon, authenticated;
grant select on public.personal_retrieval_versions to authenticated;

create or replace function private.bump_personal_retrieval_version()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare target_workspace_id uuid;
begin
  target_workspace_id := case when tg_op = 'DELETE' then old.workspace_id else new.workspace_id end;
  begin
    insert into public.personal_retrieval_versions(workspace_id, version, updated_at)
    values (target_workspace_id, 1, timezone('utc', now()))
    on conflict (workspace_id) do update
    set version = public.personal_retrieval_versions.version + 1,
        updated_at = excluded.updated_at;
  exception when foreign_key_violation then
    -- The owning workspace is already being cascade-deleted; no cache survives it.
    null;
  end;
  return case when tg_op = 'DELETE' then old else new end;
end;
$$;
revoke all on function private.bump_personal_retrieval_version() from public, anon, authenticated;

do $$
declare table_name text;
begin
  foreach table_name in array array[
    'journey_states', 'private_documents', 'document_chunks', 'document_facts',
    'health_facts', 'medication_mentions', 'symptom_events', 'appointments',
    'appointment_questions', 'plans', 'plan_items', 'graph_nodes', 'graph_edges'
  ] loop
    execute format(
      'create trigger %I after insert or update or delete on public.%I '
      'for each row execute function private.bump_personal_retrieval_version()',
      table_name || '_bump_stage5_retrieval_version', table_name);
  end loop;
end;
$$;

-- The application resolves this typed scope from the authenticated session.
create or replace function public.stage5_authenticated_scope(requested_workspace_id uuid)
returns jsonb
language sql
stable
security invoker
set search_path = public, pg_temp
as $$
  select jsonb_build_object(
    'schema_version', '5.0.0',
    'workspace_id', workspace.id,
    'care_episode_id', workspace.id,
    'owner_user_id', workspace.owner_user_id,
    'session_subject', auth.uid(),
    'state_version', coalesce(version.version, 1),
    'authenticated_at', timezone('utc', now())
  )
  from public.workspaces workspace
  left join public.personal_retrieval_versions version
    on version.workspace_id = workspace.id
  where workspace.id = requested_workspace_id
    and workspace.owner_user_id = auth.uid()
    and private.is_workspace_owner(workspace.id);
$$;
revoke all on function public.stage5_authenticated_scope(uuid) from public, anon, authenticated;
grant execute on function public.stage5_authenticated_scope(uuid) to authenticated;
comment on function public.stage5_authenticated_scope(uuid) is
  'Returns owner-only Stage 5 scope from auth.uid(); never a client-asserted identity.';

-- Exact state never uses similarity. Only active confirmed facts personalize.
create or replace function public.stage5_exact_personal_context(requested_workspace_id uuid)
returns jsonb
language sql
stable
security invoker
set search_path = public, pg_temp
as $$
  select jsonb_build_object(
    'journey_state', (
      select jsonb_build_object(
        'state_id', state.id, 'stage', state.stage,
        'timing_source', state.timing_source,
        'gestational_week', state.gestational_week,
        'gestational_day', state.gestational_day,
        'postpartum_week', state.postpartum_week,
        'postpartum_day', state.postpartum_day,
        'approximate_month_min', state.approximate_month_min,
        'approximate_month_max', state.approximate_month_max,
        'user_confirmed', state.user_confirmed,
        'has_dating_conflict', state.has_dating_conflict,
        'version', state.version)
      from public.journey_states state
      where state.workspace_id = requested_workspace_id and state.is_current
      order by state.version desc limit 1),
    'confirmed_facts', coalesce((
      select jsonb_agg(jsonb_build_object(
        'fact_id', fact.id, 'fact_type', fact.fact_type, 'value', fact.value,
        'source_kind', fact.source_kind, 'confirmation_status', 'confirmed',
        'record_only', fact.record_only,
        'source_document_id', fact.source_document_id,
        'source_document_fact_id', fact.source_document_fact_id,
        'valid_from', fact.valid_from, 'valid_to', fact.valid_to,
        'provenance', fact.provenance) order by fact.fact_type, fact.id)
      from public.health_facts fact
      where fact.workspace_id = requested_workspace_id
        and fact.confirmation_status = 'confirmed' and fact.valid_to is null
        and not exists (
          select 1 from public.health_facts later
          where later.workspace_id = fact.workspace_id
            and later.supersedes_fact_id = fact.id
            and later.confirmation_status = 'confirmed'
            and later.valid_to is null)), '[]'::jsonb),
    'medications', coalesce((
      select jsonb_agg(jsonb_build_object(
        'medication_id', medication.id,
        'name_as_written', medication.name_as_written,
        'context_text', medication.context_text,
        'status', 'confirmed', 'record_only', true) order by medication.id)
      from public.medication_mentions medication
      where medication.workspace_id = requested_workspace_id
        and medication.status = 'confirmed'), '[]'::jsonb),
    'symptoms', coalesce((
      select jsonb_agg(jsonb_build_object(
        'symptom_id', symptom.id, 'description', symptom.description,
        'reported_at', symptom.reported_at, 'safety_route', symptom.safety_route,
        'matched_rule_ids', symptom.matched_rule_ids,
        'safety_evaluation_only', true) order by symptom.reported_at desc)
      from public.symptom_events symptom
      where symptom.workspace_id = requested_workspace_id
        and symptom.user_confirmed), '[]'::jsonb),
    'appointments', coalesce((
      select jsonb_agg(jsonb_build_object(
        'appointment_id', appointment.id,
        'scheduled_for', coalesce(appointment.scheduled_for,
          appointment.scheduled_date::timestamptz),
        'appointment_type', appointment.appointment_type,
        'status', appointment.status) order by coalesce(
          appointment.scheduled_for, appointment.scheduled_date::timestamptz))
      from public.appointments appointment
      where appointment.workspace_id = requested_workspace_id
        and appointment.status <> 'cancelled'), '[]'::jsonb),
    'plan_states', coalesce((
      select jsonb_agg(jsonb_build_object(
        'plan_id', plan.id, 'version', plan.version,
        'status', plan.status, 'stale_reasons', plan.stale_reasons)
        order by plan.version desc)
      from public.plans plan
      where plan.workspace_id = requested_workspace_id
        and plan.status not in ('replaced', 'archived')), '[]'::jsonb),
    'open_questions', coalesce((
      select jsonb_agg(jsonb_build_object(
        'question_id', question.id, 'question', question.question,
        'status', question.status, 'source_fact_ids', question.source_fact_ids,
        'stale_reasons', question.stale_reasons) order by question.created_at)
      from public.appointment_questions question
      where question.workspace_id = requested_workspace_id
        and question.status in ('draft', 'saved', 'stale')), '[]'::jsonb),
    'unresolved_conflicts', coalesce((
      select jsonb_agg(jsonb_build_object(
        'conflict_id', fact.id, 'fact_type', fact.fact_type,
        'proposed_values', jsonb_build_array(fact.value),
        'source_document_ids', case when fact.source_document_id is null
          then '[]'::jsonb else jsonb_build_array(fact.source_document_id) end,
        'clarification_question_ids', coalesce((
          select jsonb_agg(question.id)
          from public.appointment_questions question
          where question.workspace_id = fact.workspace_id
            and fact.id = any(question.source_fact_ids)), '[]'::jsonb),
        'state', 'requires_clarification') order by fact.id)
      from public.health_facts fact
      where fact.workspace_id = requested_workspace_id
        and fact.confirmation_status = 'conflict'
        and fact.valid_to is null), '[]'::jsonb),
    'missing_information', case when exists (
      select 1 from public.journey_states state
      where state.workspace_id = requested_workspace_id and state.is_current)
      then '[]'::jsonb else jsonb_build_array(jsonb_build_object(
        'field', 'journey_state', 'reason', 'No current journey state is confirmed.',
        'required_for', jsonb_build_array('week-specific retrieval'))) end
  )
  where private.is_workspace_owner(requested_workspace_id);
$$;
revoke all on function public.stage5_exact_personal_context(uuid) from public, anon, authenticated;
grant execute on function public.stage5_exact_personal_context(uuid) to authenticated;
comment on function public.stage5_exact_personal_context(uuid) is
  'Read-only exact owner-scoped context; excludes proposed, rejected, conflict, superseded, and expired facts from personalization.';

create or replace function private.stage5_public_candidate_json(
  chunk public.guideline_chunks,
  source public.public_sources,
  release public.content_releases,
  requested_domain text
)
returns jsonb
language sql
stable
security invoker
set search_path = public, extensions, pg_temp
as $$
  select jsonb_build_object(
    'candidate_id', chunk.chunk_id,
    'evidence_id', chunk.evidence_id,
    'source_id', chunk.source_id,
    'source_title', source.title,
    'text', chunk.text,
    'evidence_lane', 'guideline',
    -- The SQL filters prove this requested domain is present. Returning it
    -- avoids mislabelling multi-domain evidence with the array's first item.
    'domain', requested_domain,
    'journey', jsonb_build_object(
      'stage', chunk.stage, 'unit', chunk.unit,
      'exact', case when chunk.range_start = chunk.range_end
        then chunk.range_start else null end,
      'range_start', case when chunk.range_start <> chunk.range_end
        then chunk.range_start else null end,
      'range_end', case when chunk.range_start <> chunk.range_end
        then chunk.range_end else null end),
    'jurisdictions', to_jsonb(chunk.jurisdiction),
    'conditions_required', to_jsonb(chunk.conditions_required),
    'conditions_excluded', to_jsonb(chunk.conditions_excluded),
    'release_status', 'published', 'source_status', 'published',
    'candidate_status', 'published',
    'allowed_use', to_jsonb(source.allowed_use),
    'spans', coalesce((
      select jsonb_agg(jsonb_build_object(
        'source_id', block.source_id,
        'evidence_id', chunk.evidence_id,
        'source_block_ids', jsonb_build_array(block.block_id),
        'page', block.page, 'locator', block.locator,
        'start_char', null, 'end_char', null,
        'exact_text', block.original_text,
        'text_sha256', encode(extensions.digest(
          convert_to(block.original_text, 'UTF8'), 'sha256'), 'hex'))
        order by block.ordinal)
      from public.source_blocks block
      where block.release_id = chunk.release_id
        and block.block_id = any(chunk.source_block_ids)),
      jsonb_build_array(jsonb_build_object(
        'source_id', chunk.source_id, 'evidence_id', chunk.evidence_id,
        'source_block_ids', to_jsonb(chunk.source_block_ids),
        'page', null, 'locator', 'guideline_chunk/' || chunk.chunk_id,
        'start_char', 0, 'end_char', length(chunk.text),
        'exact_text', chunk.text,
        'text_sha256', encode(extensions.digest(
          convert_to(chunk.text, 'UTF8'), 'sha256'), 'hex')))),
    'authority_score', 1.0,
    'applicability_score', case when chunk.range_start = chunk.range_end
      then 1.0 else 0.8 end,
    'provenance', jsonb_build_object(
      'corpus_version', release.corpus_version,
      'release_id', release.id,
      'release_fingerprint', release.release_fingerprint,
      'source_version', source.source_version,
      'embedding_provider', chunk.embedding_provider,
      'embedding_model', chunk.embedding_model,
      'filter_version', 'stage5-filter-v1',
      'fixture_only', release.corpus_version like 'stage5-fixture-%'));
$$;
revoke all on function private.stage5_public_candidate_json(
  public.guideline_chunks, public.public_sources, public.content_releases, text)
  from public, anon, authenticated;
grant execute on function private.stage5_public_candidate_json(
  public.guideline_chunks, public.public_sources, public.content_releases, text)
  to authenticated;

create or replace function public.stage5_public_full_text(
  search_query text,
  requested_stage text,
  requested_unit text,
  requested_range_start integer,
  requested_range_end integer,
  requested_jurisdiction text,
  requested_domain text,
  requested_conditions text[],
  requested_evidence_lanes text[],
  requested_corpus_version text,
  requested_release_id uuid,
  match_count integer default 10
)
returns table(candidate jsonb, component_score double precision)
language sql
stable
security invoker
set search_path = public, extensions, pg_temp
as $$
  select private.stage5_public_candidate_json(chunk, source, release, requested_domain),
         ts_rank_cd(chunk.search_vector,
           websearch_to_tsquery('english', search_query))::double precision
  from public.guideline_chunks chunk
  join public.content_releases release on release.id = chunk.release_id
  join public.public_sources source
    on source.source_id = chunk.source_id and source.release_id = chunk.release_id
  where release.status = 'published'
    and release.published_at is not null
    and release.corpus_version = requested_corpus_version
    and release.id = requested_release_id
    and source.status = 'published'
    and chunk.status = 'published'
    and 'guideline' = any(requested_evidence_lanes)
    and 'display' = any(source.allowed_use)
    and chunk.stage = requested_stage
    and chunk.unit = requested_unit
    and (requested_unit = 'none' or (
      chunk.range_start <= requested_range_start
      and chunk.range_end >= requested_range_end))
    and (upper(requested_jurisdiction) = any(chunk.jurisdiction)
      or 'GLOBAL' = any(chunk.jurisdiction))
    and requested_domain = any(chunk.domains)
    and chunk.conditions_required <@ coalesce(requested_conditions, '{}'::text[])
    and not (chunk.conditions_excluded && coalesce(requested_conditions, '{}'::text[]))
    and chunk.search_vector @@ websearch_to_tsquery('english', search_query)
  order by 2 desc, source.source_version desc, chunk.chunk_id
  limit greatest(1, least(match_count, 20));
$$;

create or replace function public.stage5_public_vector(
  query_embedding extensions.vector,
  requested_stage text,
  requested_unit text,
  requested_range_start integer,
  requested_range_end integer,
  requested_jurisdiction text,
  requested_domain text,
  requested_conditions text[],
  requested_evidence_lanes text[],
  requested_corpus_version text,
  requested_release_id uuid,
  match_count integer default 10
)
returns table(candidate jsonb, component_score double precision)
language sql
stable
security invoker
set search_path = public, extensions, pg_temp
as $$
  select private.stage5_public_candidate_json(chunk, source, release, requested_domain),
         (1 - (chunk.embedding <=> query_embedding))::double precision
  from public.guideline_chunks chunk
  join public.content_releases release on release.id = chunk.release_id
  join public.public_sources source
    on source.source_id = chunk.source_id and source.release_id = chunk.release_id
  where release.status = 'published'
    and release.published_at is not null
    and release.corpus_version = requested_corpus_version
    and release.id = requested_release_id
    and source.status = 'published'
    and chunk.status = 'published'
    and chunk.embedding is not null
    and extensions.vector_dims(chunk.embedding) = extensions.vector_dims(query_embedding)
    and 'guideline' = any(requested_evidence_lanes)
    and 'embed' = any(source.allowed_use)
    and 'display' = any(source.allowed_use)
    and chunk.stage = requested_stage
    and chunk.unit = requested_unit
    and (requested_unit = 'none' or (
      chunk.range_start <= requested_range_start
      and chunk.range_end >= requested_range_end))
    and (upper(requested_jurisdiction) = any(chunk.jurisdiction)
      or 'GLOBAL' = any(chunk.jurisdiction))
    and requested_domain = any(chunk.domains)
    and chunk.conditions_required <@ coalesce(requested_conditions, '{}'::text[])
    and not (chunk.conditions_excluded && coalesce(requested_conditions, '{}'::text[]))
  order by chunk.embedding <=> query_embedding,
           source.source_version desc, chunk.chunk_id
  limit greatest(1, least(match_count, 20));
$$;

revoke all on function public.stage5_public_full_text(
  text, text, text, integer, integer, text, text, text[], text[], text, uuid, integer)
  from public, anon, authenticated;
revoke all on function public.stage5_public_vector(
  extensions.vector, text, text, integer, integer, text, text, text[], text[], text, uuid, integer)
  from public, anon, authenticated;
grant execute on function public.stage5_public_full_text(
  text, text, text, integer, integer, text, text, text[], text[], text, uuid, integer)
  to authenticated;
grant execute on function public.stage5_public_vector(
  extensions.vector, text, text, integer, integer, text, text, text[], text[], text, uuid, integer)
  to authenticated;

create or replace function private.stage5_personal_passage_json(
  chunk public.document_chunks,
  document public.private_documents
)
returns jsonb
language sql
stable
security invoker
set search_path = public, extensions, pg_temp
as $$
  select jsonb_build_object(
    'candidate_id', 'personal-' || chunk.id::text,
    'chunk_id', chunk.id, 'document_id', chunk.document_id,
    'document_status', 'confirmed', 'text', chunk.text,
    'span', jsonb_build_object(
      'source_id', 'private_document:' || chunk.document_id::text,
      'evidence_id', null, 'source_block_ids', '[]'::jsonb,
      'page', chunk.page,
      'locator', coalesce(chunk.source_span->>'locator',
        'document/' || chunk.document_id::text || '/chunk/' || chunk.id::text),
      'start_char', case when chunk.source_span ? 'start_char'
        then (chunk.source_span->>'start_char')::integer else null end,
      'end_char', case when chunk.source_span ? 'end_char'
        then (chunk.source_span->>'end_char')::integer else null end,
      'exact_text', chunk.text, 'text_sha256', chunk.text_sha256),
    'provenance', jsonb_build_object(
      'corpus_version', 'personal-state', 'release_id', null,
      'release_fingerprint', null,
      'source_version', 'review-' || document.review_version::text,
      'embedding_provider', chunk.embedding_provider,
      'embedding_model', chunk.embedding_model,
      'filter_version', 'stage5-filter-v1',
      'fixture_only', document.fixture_document_key is not null));
$$;
revoke all on function private.stage5_personal_passage_json(
  public.document_chunks, public.private_documents)
  from public, anon, authenticated;
grant execute on function private.stage5_personal_passage_json(
  public.document_chunks, public.private_documents) to authenticated;

create or replace function public.stage5_personal_full_text(
  requested_workspace_id uuid,
  search_query text,
  match_count integer default 10
)
returns table(candidate jsonb, component_score double precision)
language sql
stable
security invoker
set search_path = public, extensions, pg_temp
as $$
  select private.stage5_personal_passage_json(chunk, document),
         ts_rank_cd(chunk.search_vector,
           websearch_to_tsquery('english', search_query))::double precision
  from public.document_chunks chunk
  join public.private_documents document
    on document.workspace_id = chunk.workspace_id
   and document.id = chunk.document_id
  where chunk.workspace_id = requested_workspace_id
    and private.is_workspace_owner(requested_workspace_id)
    and document.status = 'confirmed'
    and not document.has_unresolved_conflicts
    and document.scan_status in ('clean', 'fixture_verified')
    and chunk.search_vector @@ websearch_to_tsquery('english', search_query)
  order by 2 desc, document.review_version desc, chunk.id
  limit greatest(1, least(match_count, 20));
$$;

create or replace function public.stage5_personal_vector(
  requested_workspace_id uuid,
  query_embedding extensions.vector,
  match_count integer default 10
)
returns table(candidate jsonb, component_score double precision)
language sql
stable
security invoker
set search_path = public, extensions, pg_temp
as $$
  select private.stage5_personal_passage_json(chunk, document),
         (1 - (chunk.embedding <=> query_embedding))::double precision
  from public.document_chunks chunk
  join public.private_documents document
    on document.workspace_id = chunk.workspace_id
   and document.id = chunk.document_id
  where chunk.workspace_id = requested_workspace_id
    and private.is_workspace_owner(requested_workspace_id)
    and document.status = 'confirmed'
    and not document.has_unresolved_conflicts
    and document.scan_status in ('clean', 'fixture_verified')
    and chunk.embedding is not null
    and extensions.vector_dims(chunk.embedding) = extensions.vector_dims(query_embedding)
  order by chunk.embedding <=> query_embedding,
           document.review_version desc, chunk.id
  limit greatest(1, least(match_count, 20));
$$;

create or replace function public.stage5_weekly_profile(
  requested_stage text,
  requested_unit text,
  requested_range_start integer,
  requested_range_end integer,
  requested_jurisdiction text,
  requested_domain text,
  requested_conditions text[],
  requested_evidence_lanes text[],
  requested_corpus_version text,
  requested_release_id uuid
)
returns jsonb
language sql
stable
security invoker
set search_path = public, pg_temp
as $$
  select (
    select jsonb_build_object(
      'profile_id', profile.profile_id,
      'release_id', release.id,
      'corpus_version', release.corpus_version,
      'journey', jsonb_build_object(
        'stage', profile.stage, 'unit', profile.unit,
        'exact', case when profile.range_start = profile.range_end
          then profile.range_start else null end,
        'range_start', case when profile.range_start <> profile.range_end
          then profile.range_start else null end,
        'range_end', case when profile.range_start <> profile.range_end
          then profile.range_end else null end),
      'jurisdiction', to_jsonb(profile.jurisdiction),
      'hero', profile.hero, 'card_slots', profile.card_slots,
      'evidence_ids', to_jsonb(profile.source_evidence_ids),
      'status', 'published',
      'fixture_only', release.corpus_version like 'stage5-fixture-%')
    from public.weekly_profiles profile
    join public.content_releases release on release.id = profile.release_id
    where release.status = 'published' and release.published_at is not null
      and release.corpus_version = requested_corpus_version
      and release.id = requested_release_id
      and profile.status = 'published'
      and 'weekly_profile' = any(requested_evidence_lanes)
      and profile.stage = requested_stage
      and profile.unit = requested_unit
      and (requested_unit = 'none' or (
        profile.range_start = requested_range_start
        and profile.range_end = requested_range_end))
      and (upper(requested_jurisdiction) = any(profile.jurisdiction)
        or 'GLOBAL' = any(profile.jurisdiction))
    order by release.published_at desc, profile.profile_id
    limit 1);
$$;

revoke all on function public.stage5_personal_full_text(uuid, text, integer)
  from public, anon, authenticated;
revoke all on function public.stage5_personal_vector(uuid, extensions.vector, integer)
  from public, anon, authenticated;
revoke all on function public.stage5_weekly_profile(
  text, text, integer, integer, text, text, text[], text[], text, uuid)
  from public, anon, authenticated;
grant execute on function public.stage5_personal_full_text(uuid, text, integer)
  to authenticated;
grant execute on function public.stage5_personal_vector(uuid, extensions.vector, integer)
  to authenticated;
grant execute on function public.stage5_weekly_profile(
  text, text, integer, integer, text, text, text[], text[], text, uuid)
  to authenticated;

-- Directed traversal follows stored causal edges, never crosses a workspace,
-- stops at depth four, rejects cycles, and returns only complete causal paths.
create or replace function public.stage5_graph_paths(
  requested_workspace_id uuid,
  search_query text,
  requested_max_depth integer default 4,
  requested_max_paths integer default 8
)
returns setof jsonb
language sql
stable
security invoker
set search_path = public, extensions, pg_temp
as $$
  with recursive walks as (
    select start_node.id as current_id,
           array[start_node.id]::uuid[] as node_ids,
           array[start_node.node_type]::text[] as node_types,
           jsonb_build_array(jsonb_build_object(
             'node_id', start_node.id, 'node_type', start_node.node_type,
             'entity_id', start_node.entity_id,
             'entity_release_id', start_node.entity_release_id,
             'entity_key', start_node.entity_key, 'label', start_node.label,
             'source_document_id', start_node.source_document_id)) as nodes,
           '[]'::jsonb as edges,
           0 as depth,
           exists(select 1
             from regexp_split_to_table(lower(search_query), E'\\W+') term
             where length(term) >= 3
               and lower(start_node.label) like '%' || term || '%') as query_matched
    from public.graph_nodes start_node
    where start_node.workspace_id = requested_workspace_id
      and private.is_workspace_owner(requested_workspace_id)
      and start_node.node_type = 'document'

    union all

    select next_node.id,
           walk.node_ids || next_node.id,
           walk.node_types || next_node.node_type,
           walk.nodes || jsonb_build_array(jsonb_build_object(
             'node_id', next_node.id, 'node_type', next_node.node_type,
             'entity_id', next_node.entity_id,
             'entity_release_id', next_node.entity_release_id,
             'entity_key', next_node.entity_key, 'label', next_node.label,
             'source_document_id', next_node.source_document_id)),
           walk.edges || jsonb_build_array(jsonb_build_object(
             'edge_id', edge.id, 'relation', edge.relation,
             'from_node_id', edge.from_node_id,
             'to_node_id', edge.to_node_id)),
           walk.depth + 1,
           walk.query_matched or exists(select 1
             from regexp_split_to_table(lower(search_query), E'\\W+') term
             where length(term) >= 3
               and lower(next_node.label) like '%' || term || '%')
    from walks walk
    join public.graph_edges edge
      on edge.workspace_id = requested_workspace_id
     and edge.from_node_id = walk.current_id
    join public.graph_nodes next_node
      on next_node.workspace_id = edge.workspace_id
     and next_node.id = edge.to_node_id
    where walk.depth < greatest(1, least(requested_max_depth, 4))
      and not next_node.id = any(walk.node_ids)
  ), eligible as (
    select encode(extensions.digest(convert_to(
             array_to_string(node_ids, '>'), 'UTF8'), 'sha256'), 'hex') as path_id,
           nodes, edges, depth
    from walks
    where depth >= 2
      and query_matched
      and node_types[1] = 'document'
      and node_types[array_length(node_types, 1)] in ('plan', 'question')
      and ('plan_item' = any(node_types))
      and (node_types && array['restriction', 'fact']::text[])
  )
  select jsonb_build_object(
    'path_id', path_id,
    'workspace_id', requested_workspace_id,
    'nodes', nodes, 'edges', edges, 'depth', depth,
    'provenance', jsonb_build_object(
      'source', 'postgres_graph_nodes_edges',
      'filter_version', 'stage5-filter-v1',
      'max_depth', greatest(1, least(requested_max_depth, 4))))
  from eligible
  order by depth desc, path_id
  limit greatest(1, least(requested_max_paths, 8));
$$;
revoke all on function public.stage5_graph_paths(uuid, text, integer, integer)
  from public, anon, authenticated;
grant execute on function public.stage5_graph_paths(uuid, text, integer, integer)
  to authenticated;
comment on function public.stage5_graph_paths(uuid, text, integer, integer) is
  'Read-only owner-scoped causal traversal with depth/path limits and cycle protection.';

-- Older broad vector RPCs remain for migration compatibility but are no longer
-- callable by ordinary users; Stage 5 uses the filter-complete functions above.
revoke all on function public.match_guideline_chunks(
  extensions.vector, text, text, integer, text[], integer)
  from public, anon, authenticated;
revoke all on function public.match_document_chunks(
  uuid, extensions.vector, integer)
  from public, anon, authenticated;

-- Hardened compatibility wrappers keep Stage 2-4 callers operational while the
-- Stage 5 gateway uses the filter-complete RPCs above.
create or replace function public.match_guideline_chunks(
  query_embedding extensions.vector,
  requested_stage text,
  requested_unit text,
  requested_position integer,
  requested_jurisdictions text[],
  match_count integer default 8
)
returns table (
  chunk_id text, evidence_id text, source_id text, text text,
  source_block_ids text[], similarity double precision
)
language sql
stable
security invoker
set search_path = public, extensions, pg_temp
as $$
  select chunk.chunk_id, chunk.evidence_id, chunk.source_id, chunk.text,
         chunk.source_block_ids,
         1 - (chunk.embedding <=> query_embedding) as similarity
  from public.guideline_chunks chunk
  join public.content_releases release on release.id = chunk.release_id
  join public.public_sources source
    on source.source_id = chunk.source_id and source.release_id = chunk.release_id
  where release.status = 'published' and release.published_at is not null
    and source.status = 'published'
    and 'embed' = any(source.allowed_use) and 'display' = any(source.allowed_use)
    and chunk.status = 'published' and chunk.embedding is not null
    and chunk.stage = requested_stage and chunk.unit = requested_unit
    and (requested_unit = 'none'
      or requested_position between chunk.range_start and chunk.range_end)
    and (chunk.jurisdiction && requested_jurisdictions
      or 'GLOBAL' = any(chunk.jurisdiction))
    and chunk.conditions_required = '{}'::text[]
    and chunk.conditions_excluded = '{}'::text[]
    and extensions.vector_dims(chunk.embedding) =
      extensions.vector_dims(query_embedding)
  order by chunk.embedding <=> query_embedding, source.source_version desc,
           chunk.chunk_id
  limit greatest(1, least(match_count, 20));
$$;

create or replace function public.match_document_chunks(
  requested_workspace_id uuid,
  query_embedding extensions.vector,
  match_count integer default 6
)
returns table (
  chunk_id uuid, document_id uuid, page integer, text text,
  source_span jsonb, similarity double precision
)
language sql
stable
security invoker
set search_path = public, extensions, pg_temp
as $$
  select chunk.id, chunk.document_id, chunk.page, chunk.text,
         chunk.source_span, 1 - (chunk.embedding <=> query_embedding)
  from public.document_chunks chunk
  join public.private_documents document
    on document.workspace_id = chunk.workspace_id
   and document.id = chunk.document_id
  where chunk.workspace_id = requested_workspace_id
    and private.is_workspace_owner(requested_workspace_id)
    and document.status = 'confirmed'
    and not document.has_unresolved_conflicts
    and document.scan_status in ('clean', 'fixture_verified')
    and chunk.embedding is not null
    and extensions.vector_dims(chunk.embedding) =
      extensions.vector_dims(query_embedding)
  order by chunk.embedding <=> query_embedding, document.review_version desc,
           chunk.id
  limit greatest(1, least(match_count, 20));
$$;

grant execute on function public.match_guideline_chunks(
  extensions.vector, text, text, integer, text[], integer)
  to anon, authenticated;
grant execute on function public.match_document_chunks(
  uuid, extensions.vector, integer) to authenticated;
comment on function public.match_guideline_chunks(
  extensions.vector, text, text, integer, text[], integer) is
  'Hardened compatibility vector lookup for published unconditional evidence.';
comment on function public.match_document_chunks(
  uuid, extensions.vector, integer) is
  'Hardened compatibility vector lookup for owner-only confirmed documents.';
comment on function public.stage5_public_full_text(
  text, text, text, integer, integer, text, text, text[], text[], text, uuid, integer) is
  'Published-only filter-first PostgreSQL full-text retrieval.';
comment on function public.stage5_public_vector(
  extensions.vector, text, text, integer, integer, text, text, text[], text[], text, uuid, integer) is
  'Published-only filter-first pgvector retrieval; no provider call occurs here.';
comment on function public.stage5_personal_full_text(uuid, text, integer) is
  'Owner-only retrieval over confirmed, scanned, conflict-free personal documents.';
comment on function public.stage5_personal_vector(uuid, extensions.vector, integer) is
  'Owner-only pgvector retrieval over confirmed, scanned, conflict-free personal documents.';

commit;







