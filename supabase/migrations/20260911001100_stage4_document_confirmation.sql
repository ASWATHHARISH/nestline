-- Stage 4: governed fictional-document extraction and confirmed personal state.
-- Real medical uploads remain fail-closed until a deployable malware scanner
-- and the required human release gates are configured.

begin;

alter table public.private_documents
  alter column status set default 'uploaded',
  add column fixture_document_key text,
  add column scan_status text not null default 'pending',
  add column scan_provider text,
  add column scan_version text,
  add column scan_completed_at timestamptz,
  add column document_kind text,
  add column classification_confidence double precision,
  add column subject_as_written text,
  add column extraction_schema_version text,
  add column extraction_payload_sha256 text,
  add column extraction_provider text,
  add column extraction_model text,
  add column extraction_trace_id text,
  add column review_version integer not null default 0,
  add column confirmed_at timestamptz,
  add column confirmed_by_user_id uuid,
  add column has_unresolved_conflicts boolean not null default false,
  add constraint private_documents_fixture_key_check check (
    fixture_document_key is null or fixture_document_key ~ '^DOC-[0-9]{3}$'
  ),
  add constraint private_documents_scan_status_check check (
    scan_status in ('pending', 'fixture_verified', 'clean', 'failed')
  ),
  add constraint private_documents_scan_provenance_check check (
    (scan_status = 'pending' and scan_provider is null and scan_version is null and scan_completed_at is null)
    or (scan_status <> 'pending' and scan_provider is not null and scan_version is not null and scan_completed_at is not null)
  ),
  add constraint private_documents_classification_check check (
    classification_confidence is null or classification_confidence between 0 and 1
  ),
  add constraint private_documents_extraction_hash_check check (
    extraction_payload_sha256 is null or extraction_payload_sha256 ~ '^[a-f0-9]{64}$'
  ),
  add constraint private_documents_review_version_check check (review_version >= 0);

-- Upgrade old confirmed metadata honestly before validating the new invariant.
update public.private_documents document
set confirmed_at = document.updated_at,
    confirmed_by_user_id = workspace.owner_user_id,
    review_version = greatest(document.review_version, 1)
from public.workspaces workspace
where workspace.id = document.workspace_id
  and document.status = 'confirmed'
  and document.confirmed_at is null;

alter table public.private_documents
  add constraint private_documents_confirmation_provenance_check check (
    (confirmed_at is null) = (confirmed_by_user_id is null)
    and (status <> 'confirmed' or confirmed_at is not null)
  );

create unique index private_documents_workspace_sha256_unique
  on public.private_documents(workspace_id, sha256);
create unique index private_documents_workspace_fixture_key_unique
  on public.private_documents(workspace_id, fixture_document_key)
  where fixture_document_key is not null;

alter table public.document_chunks
  add column extraction_method text not null default 'embedded_text',
  add constraint document_chunks_extraction_method_check
    check (extraction_method in ('embedded_text', 'ocr'));

alter table public.document_facts
  drop constraint if exists document_facts_status_check;
alter table public.document_facts
  add column candidate_key text,
  add column fact_type text,
  add column source_span jsonb,
  add column completeness text,
  add column disposition text,
  add column record_only boolean not null default false,
  add column source_value_matches boolean not null default true,
  add column conflict_document_keys text[] not null default '{}',
  add column edited_value jsonb,
  add column decided_at timestamptz,
  add column decided_by_user_id uuid,
  add column committed_health_fact_id uuid,
  add constraint document_facts_status_check
    check (status in ('proposed', 'confirmed', 'rejected', 'conflict', 'superseded')),
  add constraint document_facts_fact_type_check check (
    fact_type is null or fact_type in (
      'subject', 'journey_timing', 'allergy', 'condition', 'clinician',
      'medication', 'medication_instruction', 'restriction', 'appointment',
      'test_result', 'follow_up', 'other'
    )
  ),
  add constraint document_facts_completeness_check check (
    completeness is null or completeness in ('complete', 'partial', 'missing', 'uncertain')
  ),
  add constraint document_facts_disposition_check check (
    disposition is null or disposition in ('extract_verbatim', 'abstain', 'manual_review')
  ),
  add constraint document_facts_source_span_check check (
    source_span is null or (
      jsonb_typeof(source_span) = 'object'
      and source_span ? 'page' and source_span ? 'exact_text'
      and source_span ? 'start' and source_span ? 'end'
    )
  );

update public.document_facts fact
set decided_at = fact.updated_at,
    decided_by_user_id = workspace.owner_user_id
from public.workspaces workspace
where workspace.id = fact.workspace_id
  and fact.status <> 'proposed'
  and fact.decided_at is null;

alter table public.document_facts
  add constraint document_facts_decision_provenance_check check (
    (decided_at is null) = (decided_by_user_id is null)
    and (status = 'proposed' or decided_at is not null)
  );

create unique index document_facts_workspace_candidate_key_unique
  on public.document_facts(workspace_id, document_id, candidate_key)
  where candidate_key is not null;

alter table public.health_facts
  drop constraint if exists health_facts_confirmation_status_check;
alter table public.health_facts
  add column source_document_fact_id uuid,
  add column document_review_submission_key text,
  add column record_only boolean not null default false,
  add column provenance jsonb not null default '{}',
  add constraint health_facts_confirmation_status_check
    check (confirmation_status in ('proposed', 'confirmed', 'rejected', 'conflict', 'superseded')),
  add constraint health_facts_document_fact_fk
    foreign key (workspace_id, source_document_fact_id)
    references public.document_facts(workspace_id, id) on delete cascade,
  add constraint health_facts_document_provenance_check check (
    (source_kind <> 'document_extracted' and source_document_fact_id is null)
    or (source_kind = 'document_extracted' and source_document_id is not null and source_document_fact_id is not null)
  );

create unique index health_facts_document_fact_unique
  on public.health_facts(workspace_id, source_document_fact_id)
  where source_document_fact_id is not null;

alter table public.document_facts
  add constraint document_facts_committed_health_fact_fk
  foreign key (workspace_id, committed_health_fact_id)
  references public.health_facts(workspace_id, id) on delete set null (committed_health_fact_id);

alter table public.medication_mentions
  drop constraint if exists medication_mentions_status_check;
alter table public.medication_mentions
  add column candidate_key text,
  add column decided_at timestamptz,
  add column decided_by_user_id uuid,
  add constraint medication_mentions_status_check
    check (status in ('proposed', 'confirmed', 'rejected', 'conflict', 'superseded'));

update public.medication_mentions mention
set decided_at = mention.created_at,
    decided_by_user_id = workspace.owner_user_id
from public.workspaces workspace
where workspace.id = mention.workspace_id
  and mention.status <> 'proposed'
  and mention.decided_at is null;

alter table public.medication_mentions
  add constraint medication_mentions_decision_provenance_check check (
    (decided_at is null) = (decided_by_user_id is null)
    and (status = 'proposed' or decided_at is not null)
  );

create unique index medication_mentions_workspace_candidate_unique
  on public.medication_mentions(workspace_id, document_id, candidate_key)
  where candidate_key is not null;

alter table public.appointments
  add column scheduled_date date,
  add column source_document_fact_id uuid,
  add constraint appointments_schedule_precision_check check (
    scheduled_for is not null or scheduled_date is not null
  ),
  add constraint appointments_source_document_fact_fk
    foreign key (workspace_id, source_document_fact_id)
    references public.document_facts(workspace_id, id) on delete set null (source_document_fact_id);

create unique index appointments_document_fact_unique
  on public.appointments(workspace_id, source_document_fact_id)
  where source_document_fact_id is not null;

-- Architecture edge labels are constrained, while the original Stage 2
-- fixture's generic `supports` relation remains valid for upgrade compatibility.
alter table public.graph_edges
  add constraint graph_edges_relation_check check (
    relation in (
      'supports', 'IN_WEEK', 'EXTRACTED_FROM', 'CONFLICTS_WITH', 'SUPERSEDES',
      'CONSTRAINS', 'SUPPORTED_BY', 'TRIGGERED', 'SCHEDULED_FOR',
      'NEEDS_CLARIFICATION', 'REVIEWED_BY'
    )
  );

create table private.document_review_commits (
  workspace_id uuid not null,
  document_id uuid not null,
  submission_key text not null,
  payload_sha256 text not null check (payload_sha256 ~ '^[a-f0-9]{64}$'),
  result jsonb not null,
  committed_at timestamptz not null default timezone('utc', now()),
  primary key (workspace_id, document_id, submission_key),
  foreign key (workspace_id, document_id)
    references public.private_documents(workspace_id, id) on delete cascade
);

-- Extracted rows are derived state. API users may read their own rows but can
-- create or change them only through the functions below.
drop policy if exists "workspace members manage document_chunks" on public.document_chunks;
drop policy if exists "workspace members manage document_facts" on public.document_facts;
drop policy if exists "workspace members manage medication_mentions" on public.medication_mentions;

create policy "workspace owners read document_chunks" on public.document_chunks
  for select to authenticated using (private.is_workspace_owner(workspace_id));
create policy "workspace owners read document_facts" on public.document_facts
  for select to authenticated using (private.is_workspace_owner(workspace_id));
create policy "workspace owners read medication_mentions" on public.medication_mentions
  for select to authenticated using (private.is_workspace_owner(workspace_id));

revoke insert, update, delete on public.document_chunks from authenticated;
revoke insert, update, delete on public.document_facts from authenticated;
revoke insert, update, delete on public.medication_mentions from authenticated;

-- The graph becomes retrieval evidence in Stage 5, so clients cannot fabricate
-- relationship paths. Stage-specific committers create graph state.
drop policy if exists "workspace members manage graph_nodes" on public.graph_nodes;
drop policy if exists "workspace members manage graph_edges" on public.graph_edges;
create policy "workspace owners read graph_nodes" on public.graph_nodes
  for select to authenticated using (private.is_workspace_owner(workspace_id));
create policy "workspace owners read graph_edges" on public.graph_edges
  for select to authenticated using (private.is_workspace_owner(workspace_id));
revoke insert, update, delete on public.graph_nodes from authenticated;
revoke insert, update, delete on public.graph_edges from authenticated;

-- User-reported facts remain owner-editable. A client cannot masquerade as the
-- document committer by directly creating confirmed extracted facts.
drop policy if exists "workspace members manage health_facts" on public.health_facts;
create policy "workspace owners read health_facts" on public.health_facts
  for select to authenticated using (private.is_workspace_owner(workspace_id));
create policy "workspace owners create user-reported health_facts" on public.health_facts
  for insert to authenticated with check (
    private.is_workspace_owner(workspace_id)
    and source_kind = 'user_reported'
    and source_document_id is null
    and source_document_fact_id is null
  );
create policy "workspace owners update user-reported health_facts" on public.health_facts
  for update to authenticated using (
    private.is_workspace_owner(workspace_id) and source_kind = 'user_reported'
  ) with check (
    private.is_workspace_owner(workspace_id)
    and source_kind = 'user_reported'
    and source_document_id is null
    and source_document_fact_id is null
  );
create policy "workspace owners delete user-reported health_facts" on public.health_facts
  for delete to authenticated using (
    private.is_workspace_owner(workspace_id) and source_kind = 'user_reported'
  );

-- Protect processing and confirmation metadata with column-level grants. The
-- owner can register an uploaded object but cannot self-assert a clean scan or
-- confirmed status through PostgREST.
revoke insert, update on public.private_documents from authenticated;
grant insert (
  workspace_id, storage_object_path, original_filename, media_type, byte_size,
  sha256, contains_real_medical_data, fixture_document_key
) on public.private_documents to authenticated;

create or replace function public.record_document_extraction(
  requested_workspace_id uuid,
  requested_document_id uuid,
  requested_document_sha256 text,
  requested_scan_status text,
  requested_scan_provider text,
  requested_scan_version text,
  requested_payload_sha256 text,
  requested_extraction jsonb
)
returns jsonb
language plpgsql
volatile
security definer
set search_path = public, private, pg_temp
as $$
declare
  document public.private_documents;
  chunk jsonb;
  candidate jsonb;
  source jsonb;
  candidate_page integer;
  candidate_source text;
  candidate_value jsonb;
begin
  if auth.uid() is null or not private.is_workspace_owner(requested_workspace_id) then
    raise exception 'workspace owner access required' using errcode = '42501';
  end if;
  if requested_document_sha256 !~ '^[a-f0-9]{64}$'
     or requested_payload_sha256 !~ '^[a-f0-9]{64}$' then
    raise exception 'invalid document or extraction checksum' using errcode = '22023';
  end if;
  if requested_scan_status <> 'fixture_verified'
     or length(trim(requested_scan_provider)) not between 1 and 100
     or length(trim(requested_scan_version)) not between 1 and 100 then
    raise exception 'only verified fictional fixtures are accepted in this build'
      using errcode = '55000';
  end if;
  if jsonb_typeof(requested_extraction) <> 'object'
     or requested_extraction->>'schema_version' <> 'stage4-document-v1'
     or jsonb_typeof(requested_extraction->'chunks') <> 'array'
     or jsonb_typeof(requested_extraction->'candidates') <> 'array'
     or jsonb_array_length(requested_extraction->'chunks') not between 1 and 100
     or jsonb_array_length(requested_extraction->'candidates') > 100 then
    raise exception 'invalid extraction packet' using errcode = '22023';
  end if;

  select value.* into document
  from public.private_documents value
  join public.workspaces workspace on workspace.id = value.workspace_id
  where value.workspace_id = requested_workspace_id
    and value.id = requested_document_id
    and workspace.mode = 'fictional_demo'
  for update of value;

  if document.id is null then
    raise exception 'fictional demo document not found' using errcode = '22023';
  end if;
  if document.contains_real_medical_data
     or requested_extraction->>'fictional' <> 'true' then
    raise exception 'real medical documents are blocked until scanning is configured'
      using errcode = '55000';
  end if;
  if document.sha256 <> requested_document_sha256
     or requested_extraction->>'document_sha256' <> requested_document_sha256 then
    raise exception 'document checksum changed before extraction' using errcode = '40001';
  end if;
  if document.extraction_payload_sha256 is not null then
    if document.extraction_payload_sha256 <> requested_payload_sha256 then
      raise exception 'document already has a different extraction packet'
        using errcode = '23505';
    end if;
    return jsonb_build_object(
      'document_id', document.id,
      'review_version', document.review_version,
      'idempotent_replay', true
    );
  end if;
  if document.status <> 'uploaded' or document.review_version <> 0 then
    raise exception 'document is not ready for first extraction' using errcode = '40001';
  end if;

  update public.private_documents
  set status = 'processing'
  where workspace_id = requested_workspace_id and id = requested_document_id;

  for chunk in select value from jsonb_array_elements(requested_extraction->'chunks') value
  loop
    if (chunk->>'page')::integer not between 1 and 100
       or length(chunk->>'text') not between 1 and 100000
       or chunk->>'text_sha256' !~ '^[a-f0-9]{64}$'
       or chunk->>'extraction_method' not in ('embedded_text', 'ocr')
       or jsonb_typeof(chunk->'source_span') <> 'object' then
      raise exception 'invalid extraction chunk' using errcode = '22023';
    end if;
    insert into public.document_chunks(
      workspace_id, document_id, page, source_span, text, text_sha256,
      extraction_method
    ) values (
      requested_workspace_id, requested_document_id, (chunk->>'page')::integer,
      chunk->'source_span', chunk->>'text', chunk->>'text_sha256',
      chunk->>'extraction_method'
    );
  end loop;

  for candidate in select value from jsonb_array_elements(requested_extraction->'candidates') value
  loop
    source := candidate->'source';
    candidate_page := (source->>'page')::integer;
    candidate_source := source->>'exact_text';
    candidate_value := candidate->'value';
    if length(trim(candidate->>'candidate_key')) not between 1 and 160
       or length(trim(candidate->>'field_name')) not between 1 and 100
       or candidate->>'fact_type' not in (
         'subject', 'journey_timing', 'allergy', 'condition', 'clinician',
         'medication', 'medication_instruction', 'restriction', 'appointment',
         'test_result', 'follow_up', 'other'
       )
       or candidate->>'status' <> 'proposed'
       or candidate->>'completeness' not in ('complete', 'partial', 'missing', 'uncertain')
       or candidate->>'disposition' not in ('extract_verbatim', 'abstain', 'manual_review')
       or (candidate->>'confidence')::double precision not between 0 and 1
       or candidate_page not between 1 and 100
       or length(candidate_source) not between 1 and 2000
       or not exists (
         select 1 from public.document_chunks existing
         where existing.workspace_id = requested_workspace_id
           and existing.document_id = requested_document_id
           and existing.page = candidate_page
           and position(candidate_source in existing.text) > 0
       )
       or (candidate->>'fact_type' in ('medication', 'medication_instruction')
           and coalesce((candidate->>'record_only')::boolean, false) is not true)
       or (candidate->>'completeness' = 'missing' and candidate->>'disposition' <> 'abstain') then
      raise exception 'invalid or unsupported extraction candidate' using errcode = '22023';
    end if;
    insert into public.document_facts(
      workspace_id, document_id, candidate_key, field_name, fact_type, value,
      source_page, source_text, source_span, confidence, completeness,
      disposition, status, record_only, source_value_matches,
      conflict_document_keys
    ) values (
      requested_workspace_id, requested_document_id,
      trim(candidate->>'candidate_key'), trim(candidate->>'field_name'),
      candidate->>'fact_type', candidate_value, candidate_page, candidate_source,
      source, (candidate->>'confidence')::double precision,
      candidate->>'completeness', candidate->>'disposition', 'proposed',
      coalesce((candidate->>'record_only')::boolean, false),
      coalesce((candidate->>'source_value_matches')::boolean, false),
      coalesce(array(
        select jsonb_array_elements_text(candidate->'conflict_document_keys')
      ), '{}'::text[])
    );
    if candidate->>'fact_type' = 'medication' and candidate->>'disposition' <> 'abstain' then
      insert into public.medication_mentions(
        workspace_id, document_id, candidate_key, name_as_written,
        context_text, status
      ) values (
        requested_workspace_id, requested_document_id,
        trim(candidate->>'candidate_key'), trim(candidate_value #>> '{}'),
        candidate_source, 'proposed'
      );
    end if;
  end loop;

  update public.private_documents
  set status = 'needs_confirmation',
      scan_status = requested_scan_status,
      scan_provider = trim(requested_scan_provider),
      scan_version = trim(requested_scan_version),
      scan_completed_at = clock_timestamp(),
      document_kind = requested_extraction->>'document_kind',
      classification_confidence = (requested_extraction->>'classification_confidence')::double precision,
      subject_as_written = nullif(trim(requested_extraction->>'subject_as_written'), ''),
      extraction_schema_version = requested_extraction->>'schema_version',
      extraction_payload_sha256 = requested_payload_sha256,
      extraction_provider = requested_extraction->'provider_trace'->>'provider',
      extraction_model = requested_extraction->'provider_trace'->>'model',
      extraction_trace_id = nullif(requested_extraction->'provider_trace'->>'trace_id', ''),
      review_version = 1
  where workspace_id = requested_workspace_id and id = requested_document_id;

  return jsonb_build_object(
    'document_id', requested_document_id,
    'review_version', 1,
    'idempotent_replay', false
  );
end;
$$;

create or replace function public.commit_document_review(
  requested_workspace_id uuid,
  requested_document_id uuid,
  expected_review_version integer,
  requested_submission_key text,
  requested_payload_sha256 text,
  requested_decisions jsonb
)
returns jsonb
language plpgsql
volatile
security definer
set search_path = public, private, pg_temp
as $$
declare
  document public.private_documents;
  prior_commit private.document_review_commits;
  candidate public.document_facts;
  decision jsonb;
  action text;
  chosen_value jsonb;
  mapped_fact_type text;
  created_fact_id uuid;
  prior_fact public.health_facts;
  document_node_id uuid;
  fact_node_id uuid;
  prior_node_id uuid;
  question_id uuid;
  question_node_id uuid;
  next_appointment_id uuid;
  affected_plan_id uuid;
  confirmed_ids uuid[] := '{}'::uuid[];
  conflict_ids uuid[] := '{}'::uuid[];
  rejected_keys text[] := '{}'::text[];
  stale_plan_ids uuid[] := '{}'::uuid[];
  result jsonb;
  has_conflict boolean := false;
begin
  if auth.uid() is null or not private.is_workspace_owner(requested_workspace_id) then
    raise exception 'workspace owner access required' using errcode = '42501';
  end if;
  if expected_review_version < 1
     or length(trim(requested_submission_key)) not between 16 and 128
     or requested_payload_sha256 !~ '^[a-f0-9]{64}$'
     or jsonb_typeof(requested_decisions) <> 'array'
     or jsonb_array_length(requested_decisions) not between 1 and 100 then
    raise exception 'invalid review request' using errcode = '22023';
  end if;

  select * into document
  from public.private_documents value
  where value.workspace_id = requested_workspace_id
    and value.id = requested_document_id
  for update;
  if document.id is null then
    raise exception 'document not found' using errcode = '22023';
  end if;

  select * into prior_commit
  from private.document_review_commits value
  where value.workspace_id = requested_workspace_id
    and value.document_id = requested_document_id
    and value.submission_key = trim(requested_submission_key);
  if prior_commit.submission_key is not null then
    if prior_commit.payload_sha256 <> requested_payload_sha256 then
      raise exception 'submission key already belongs to a different review'
        using errcode = '23505';
    end if;
    return prior_commit.result || jsonb_build_object('idempotent_replay', true);
  end if;

  if document.status <> 'needs_confirmation'
     or document.review_version <> expected_review_version then
    raise exception 'stale document review version' using errcode = '40001';
  end if;
  if document.scan_status <> 'fixture_verified'
     or document.contains_real_medical_data then
    raise exception 'document is outside the enabled fictional confirmation boundary'
      using errcode = '55000';
  end if;
  if jsonb_array_length(requested_decisions) <> (
    select count(*) from public.document_facts value
    where value.workspace_id = requested_workspace_id
      and value.document_id = requested_document_id
      and value.status = 'proposed'
  ) then
    raise exception 'review must decide every proposed candidate' using errcode = '22023';
  end if;
  if exists (
    select decision_value->>'candidate_key'
    from jsonb_array_elements(requested_decisions) decision_value
    group by decision_value->>'candidate_key'
    having count(*) <> 1
  ) or exists (
    select 1 from jsonb_array_elements(requested_decisions) decision_value
    where not exists (
      select 1 from public.document_facts value
      where value.workspace_id = requested_workspace_id
        and value.document_id = requested_document_id
        and value.candidate_key = decision_value->>'candidate_key'
        and value.status = 'proposed'
    )
  ) then
    raise exception 'review contains duplicate or unknown candidate keys'
      using errcode = '22023';
  end if;

  insert into public.graph_nodes(
    workspace_id, node_type, entity_id, label, source_document_id
  ) values (
    requested_workspace_id, 'document', requested_document_id,
    coalesce(document.fixture_document_key, document.original_filename), requested_document_id
  ) on conflict (workspace_id, node_type, entity_id) do update
    set label = excluded.label
  returning id into document_node_id;

  for decision in select value from jsonb_array_elements(requested_decisions) value
  loop
    select * into candidate
    from public.document_facts value
    where value.workspace_id = requested_workspace_id
      and value.document_id = requested_document_id
      and value.candidate_key = decision->>'candidate_key'
    for update;
    action := decision->>'action';
    if action not in ('confirm', 'edit_and_confirm', 'reject', 'keep_conflict', 'supersede') then
      raise exception 'unsupported review action' using errcode = '22023';
    end if;
    if candidate.disposition = 'abstain' and action <> 'reject' then
      raise exception 'an abstention can only be rejected' using errcode = '22023';
    end if;
    if cardinality(candidate.conflict_document_keys) > 0
       and action not in ('reject', 'keep_conflict', 'supersede') then
      raise exception 'a declared conflict must be preserved, rejected, or explicitly superseded'
        using errcode = '22023';
    end if;
    if action = 'edit_and_confirm' then
      if not decision ? 'edited_value' or decision->'edited_value' = 'null'::jsonb then
        raise exception 'edited confirmation requires a value' using errcode = '22023';
      end if;
      chosen_value := decision->'edited_value';
    else
      chosen_value := candidate.value;
    end if;

    if action = 'reject' then
      update public.document_facts
      set status = 'rejected', decided_at = clock_timestamp(),
          decided_by_user_id = auth.uid()
      where id = candidate.id;
      update public.medication_mentions
      set status = 'rejected', decided_at = clock_timestamp(),
          decided_by_user_id = auth.uid()
      where workspace_id = requested_workspace_id
        and document_id = requested_document_id
        and candidate_key = candidate.candidate_key;
      rejected_keys := array_append(rejected_keys, candidate.candidate_key);
      continue;
    end if;

    mapped_fact_type := case candidate.fact_type
      when 'allergy' then 'allergy'
      when 'condition' then 'medical_history'
      when 'medication' then 'medication'
      when 'medication_instruction' then 'clinician_instruction'
      when 'restriction' then 'clinician_instruction'
      when 'clinician' then 'clinician_instruction'
      when 'journey_timing' then 'other'
      when 'appointment' then 'other'
      when 'follow_up' then 'other'
      when 'test_result' then 'other'
      else 'other'
    end;

    if action = 'supersede' then
      select * into prior_fact from public.health_facts value
      where value.workspace_id = requested_workspace_id
        and value.id = (decision->>'supersedes_fact_id')::uuid
        and value.confirmation_status = 'confirmed'
        and value.valid_to is null
      for update;
      if prior_fact.id is null then
        raise exception 'superseded fact is not a current confirmed fact'
          using errcode = '22023';
      end if;
    else
      prior_fact := null;
    end if;

    insert into public.health_facts(
      workspace_id, fact_type, value, source_kind, confirmation_status,
      source_document_id, source_document_fact_id, supersedes_fact_id,
      document_review_submission_key, record_only, provenance
    ) values (
      requested_workspace_id, mapped_fact_type,
      jsonb_build_object(
        'field', candidate.field_name,
        'value', chosen_value,
        'source_text', candidate.source_text,
        'record_only', candidate.record_only
      ),
      'document_extracted',
      case when action = 'keep_conflict' then 'conflict' else 'confirmed' end,
      requested_document_id, candidate.id, prior_fact.id,
      trim(requested_submission_key), candidate.record_only,
      jsonb_build_object(
        'document_sha256', document.sha256,
        'candidate_key', candidate.candidate_key,
        'source_page', candidate.source_page,
        'source_span', candidate.source_span,
        'extraction_provider', document.extraction_provider,
        'extraction_model', document.extraction_model,
        'user_confirmed_at', clock_timestamp()
      )
    ) returning id into created_fact_id;

    if prior_fact.id is not null then
      update public.health_facts
      set confirmation_status = 'superseded', valid_to = clock_timestamp()
      where workspace_id = requested_workspace_id and id = prior_fact.id;
    end if;

    update public.document_facts
    set status = case when action = 'keep_conflict' then 'conflict' else 'confirmed' end,
        edited_value = case when action = 'edit_and_confirm' then chosen_value else null end,
        confirmed_at = case when action = 'keep_conflict' then null else clock_timestamp() end,
        decided_at = clock_timestamp(), decided_by_user_id = auth.uid(),
        committed_health_fact_id = created_fact_id
    where id = candidate.id;
    update public.medication_mentions
    set status = case when action = 'keep_conflict' then 'conflict' else 'confirmed' end,
        decided_at = clock_timestamp(), decided_by_user_id = auth.uid()
    where workspace_id = requested_workspace_id
      and document_id = requested_document_id
      and candidate_key = candidate.candidate_key;

    if action = 'keep_conflict' then
      conflict_ids := array_append(conflict_ids, created_fact_id);
      has_conflict := true;
    else
      confirmed_ids := array_append(confirmed_ids, created_fact_id);
    end if;

    insert into public.graph_nodes(
      workspace_id, node_type, entity_id, label, source_document_id
    ) values (
      requested_workspace_id,
      case when candidate.fact_type = 'restriction' then 'restriction' else 'fact' end,
      created_fact_id, left(candidate.field_name || ': ' || (chosen_value #>> '{}'), 300),
      requested_document_id
    ) returning id into fact_node_id;
    insert into public.graph_edges(
      workspace_id, from_node_id, to_node_id, relation
    ) values (
      requested_workspace_id, fact_node_id, document_node_id, 'EXTRACTED_FROM'
    ) on conflict do nothing;

    if prior_fact.id is not null then
      select id into prior_node_id from public.graph_nodes
      where workspace_id = requested_workspace_id and entity_id = prior_fact.id
        and node_type in ('fact', 'restriction') limit 1;
      if prior_node_id is null then
        insert into public.graph_nodes(
          workspace_id, node_type, entity_id, label, source_document_id
        ) values (
          requested_workspace_id, 'fact', prior_fact.id,
          'Superseded confirmed fact', prior_fact.source_document_id
        ) returning id into prior_node_id;
      end if;
      insert into public.graph_edges(
        workspace_id, from_node_id, to_node_id, relation
      ) values (
        requested_workspace_id, fact_node_id, prior_node_id, 'SUPERSEDES'
      ) on conflict do nothing;
    end if;

    if action = 'keep_conflict' then
      for prior_fact in
        select value.* from public.health_facts value
        join public.private_documents prior_document
          on prior_document.workspace_id = value.workspace_id
         and prior_document.id = value.source_document_id
        where value.workspace_id = requested_workspace_id
          and prior_document.fixture_document_key = any(candidate.conflict_document_keys)
          and value.confirmation_status = 'confirmed'
          and value.valid_to is null
      loop
        select id into prior_node_id from public.graph_nodes
        where workspace_id = requested_workspace_id and entity_id = prior_fact.id
          and node_type in ('fact', 'restriction') limit 1;
        if prior_node_id is null then
          insert into public.graph_nodes(
            workspace_id, node_type, entity_id, label, source_document_id
          ) values (
            requested_workspace_id, 'fact', prior_fact.id,
            'Earlier confirmed source', prior_fact.source_document_id
          ) returning id into prior_node_id;
        end if;
        insert into public.graph_edges(
          workspace_id, from_node_id, to_node_id, relation
        ) values (
          requested_workspace_id, fact_node_id, prior_node_id, 'CONFLICTS_WITH'
        ) on conflict do nothing;
      end loop;

      select id into next_appointment_id from public.appointments
      where workspace_id = requested_workspace_id
        and status in ('planned', 'confirmed')
        and coalesce(scheduled_date, scheduled_for::date) >= current_date
      order by coalesce(scheduled_date, scheduled_for::date), created_at
      limit 1;
      if next_appointment_id is not null then
        insert into public.appointment_questions(
          workspace_id, appointment_id, question, source_fact_ids, status
        ) values (
          requested_workspace_id, next_appointment_id,
          'Ask about the conflicting documented instructions.',
          '{}'::uuid[], 'draft'
        ) returning id into question_id;
        insert into public.graph_nodes(
          workspace_id, node_type, entity_id, label, source_document_id
        ) values (
          requested_workspace_id, 'question', question_id,
          'Clarify conflicting documented instructions', requested_document_id
        ) returning id into question_node_id;
        insert into public.graph_edges(
          workspace_id, from_node_id, to_node_id, relation
        ) values (
          requested_workspace_id, question_node_id, fact_node_id,
          'NEEDS_CLARIFICATION'
        ) on conflict do nothing;
      end if;
    end if;

    if candidate.fact_type = 'restriction' then
      for affected_plan_id in
        select distinct plan.id
        from public.plans plan
        join public.plan_items item
          on item.workspace_id = plan.workspace_id and item.plan_id = plan.id
        where plan.workspace_id = requested_workspace_id
          and plan.status in ('saved', 'active')
          and item.category = 'movement'
      loop
        update public.plans
        set status = 'stale',
            stale_reasons = private.append_unique_text(
              stale_reasons, 'document_fact_confirmed:' || candidate.id::text
            )
        where workspace_id = requested_workspace_id and id = affected_plan_id;
        update public.plan_items
        set state = 'stale'
        where workspace_id = requested_workspace_id
          and plan_id = affected_plan_id and category = 'movement';
        if not affected_plan_id = any(stale_plan_ids) then
          stale_plan_ids := array_append(stale_plan_ids, affected_plan_id);
        end if;
      end loop;
    end if;

    if candidate.field_name = 'followup_date'
       and action <> 'keep_conflict'
       and (chosen_value #>> '{}') ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' then
      insert into public.appointments(
        workspace_id, scheduled_date, appointment_type, status,
        source_fact_id, source_document_fact_id
      ) values (
        requested_workspace_id, (chosen_value #>> '{}')::date,
        'Documented follow-up', 'confirmed', created_fact_id, candidate.id
      ) on conflict (workspace_id, source_document_fact_id) where source_document_fact_id is not null
        do nothing;
    end if;
  end loop;

  update public.private_documents
  set status = 'confirmed', review_version = review_version + 1,
      confirmed_at = clock_timestamp(), confirmed_by_user_id = auth.uid(),
      has_unresolved_conflicts = has_conflict
  where workspace_id = requested_workspace_id and id = requested_document_id
  returning * into document;

  result := jsonb_build_object(
    'document_id', document.id,
    'review_version', document.review_version,
    'confirmed_fact_ids', to_jsonb(confirmed_ids),
    'conflict_fact_ids', to_jsonb(conflict_ids),
    'rejected_candidate_keys', to_jsonb(rejected_keys),
    'stale_plan_ids', to_jsonb(stale_plan_ids),
    'idempotent_replay', false,
    'committed_at', document.confirmed_at
  );
  insert into private.document_review_commits(
    workspace_id, document_id, submission_key, payload_sha256, result
  ) values (
    requested_workspace_id, requested_document_id, trim(requested_submission_key),
    requested_payload_sha256, result
  );
  return result;
end;
$$;

revoke all on function public.record_document_extraction(
  uuid, uuid, text, text, text, text, text, jsonb
) from public, anon;
grant execute on function public.record_document_extraction(
  uuid, uuid, text, text, text, text, text, jsonb
) to authenticated;
revoke all on function public.commit_document_review(
  uuid, uuid, integer, text, text, jsonb
) from public, anon;
grant execute on function public.commit_document_review(
  uuid, uuid, integer, text, text, jsonb
) to authenticated;

comment on function public.record_document_extraction(
  uuid, uuid, text, text, text, text, text, jsonb
) is 'Records a validated fictional extraction as non-personalizing proposals.';
comment on function public.commit_document_review(
  uuid, uuid, integer, text, text, jsonb
) is 'Atomically applies one complete, explicit and idempotent owner review of document proposals.';
comment on column public.health_facts.record_only is
  'True for documented medication content; it records source text and never authorizes treatment advice.';

commit;
