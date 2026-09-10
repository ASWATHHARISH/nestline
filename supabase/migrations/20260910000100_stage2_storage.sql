-- Nestline Stage 2 storage foundation.
-- Public medical knowledge is admin-published; personal records are workspace-isolated.

begin;

create schema if not exists private;
revoke all on schema private from public, anon, authenticated;

create extension if not exists pgcrypto with schema extensions;
create extension if not exists vector with schema extensions;

create or replace function private.set_updated_at()
returns trigger
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
begin
  new.updated_at = timezone('utc', now());
  return new;
end;
$$;

create table public.workspaces (
  id uuid primary key default extensions.gen_random_uuid(),
  owner_user_id uuid not null references auth.users(id) on delete cascade,
  mode text not null check (mode in ('personal_empty', 'fictional_demo')),
  display_name text not null check (length(trim(display_name)) between 1 and 120),
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table public.workspace_members (
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null check (role in ('owner', 'editor', 'reviewer', 'viewer')),
  created_at timestamptz not null default timezone('utc', now()),
  primary key (workspace_id, user_id)
);

create or replace function private.is_workspace_member(target_workspace_id uuid)
returns boolean
language sql
stable
security definer
set search_path = public, pg_temp
as $$
  select exists (
    select 1 from public.workspace_members member
    where member.workspace_id = target_workspace_id
      and member.user_id = auth.uid()
  );
$$;

create or replace function private.is_workspace_owner(target_workspace_id uuid)
returns boolean
language sql
stable
security definer
set search_path = public, pg_temp
as $$
  select exists (
    select 1 from public.workspaces workspace
    where workspace.id = target_workspace_id
      and workspace.owner_user_id = auth.uid()
  );
$$;

create or replace function private.add_workspace_owner_membership()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  insert into public.workspace_members(workspace_id, user_id, role)
  values (new.id, new.owner_user_id, 'owner')
  on conflict (workspace_id, user_id) do update set role = 'owner';
  return new;
end;
$$;

create trigger workspaces_set_updated_at
before update on public.workspaces
for each row execute function private.set_updated_at();

create trigger workspaces_add_owner
after insert on public.workspaces
for each row execute function private.add_workspace_owner_membership();

-- Immutable public knowledge releases and Stage 1 provenance.
create table public.content_releases (
  id uuid primary key default extensions.gen_random_uuid(),
  corpus_version text not null unique,
  release_fingerprint text not null unique check (release_fingerprint ~ '^[a-f0-9]{64}$'),
  status text not null check (status in ('draft', 'published', 'retired')),
  embedding_provider text,
  embedding_model text,
  published_at timestamptz,
  created_at timestamptz not null default timezone('utc', now()),
  check ((status = 'draft' and published_at is null)
    or (status in ('published', 'retired') and published_at is not null))
);

create table public.public_sources (
  source_id text primary key,
  release_id uuid not null references public.content_releases(id) on delete restrict,
  title text not null,
  publisher text not null,
  canonical_url text not null check (canonical_url ~ '^https://'),
  jurisdiction text[] not null check (cardinality(jurisdiction) > 0),
  source_version text not null,
  reuse_status text not null check (reuse_status in ('permitted', 'restricted')),
  allowed_use text[] not null,
  attribution_text text not null default '',
  status text not null check (status in ('reviewed', 'published', 'retired')),
  content_checksum text not null check (content_checksum ~ '^[a-f0-9]{64}$'),
  created_at timestamptz not null default timezone('utc', now()),
  unique (release_id, source_id)
);

create table public.source_artifacts (
  id uuid primary key default extensions.gen_random_uuid(),
  release_id uuid not null references public.content_releases(id) on delete restrict,
  source_id text not null references public.public_sources(source_id) on delete restrict,
  logical_version_id text not null,
  original_sha256 text not null check (original_sha256 ~ '^[a-f0-9]{64}$'),
  document_type text not null check (document_type in ('html', 'pdf')),
  retrieved_at date not null,
  byte_size bigint not null check (byte_size > 0),
  parser_name text not null,
  parser_version text not null,
  storage_object_path text,
  created_at timestamptz not null default timezone('utc', now()),
  unique (source_id, logical_version_id),
  unique (source_id, original_sha256)
);

create table public.source_blocks (
  block_id text primary key,
  release_id uuid not null references public.content_releases(id) on delete restrict,
  source_id text not null references public.public_sources(source_id) on delete restrict,
  source_artifact_id uuid not null references public.source_artifacts(id) on delete restrict,
  ordinal integer not null check (ordinal >= 0),
  block_kind text not null check (block_kind in ('heading', 'paragraph', 'list_item', 'table')),
  original_text text not null,
  normalized_text text not null,
  locator text not null,
  heading_path text[] not null default '{}',
  page integer check (page is null or page >= 1),
  extraction_method text not null check (extraction_method in ('html_structure', 'pdf_text', 'ocr')),
  extraction_confidence double precision not null check (extraction_confidence between 0 and 1),
  unique (source_artifact_id, ordinal)
);

create table public.ingestion_runs (
  run_id text primary key,
  logical_version_id text not null,
  source_id text not null references public.public_sources(source_id) on delete restrict,
  source_artifact_id uuid references public.source_artifacts(id) on delete restrict,
  evaluated_at date not null,
  dry_run boolean not null,
  outcome text not null check (outcome in ('rejected', 'review_required', 'publishable', 'published')),
  admission jsonb not null,
  diff jsonb not null default '{}'::jsonb,
  issues jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default timezone('utc', now())
);

create table public.evidence_review_tasks (
  task_id text primary key,
  release_id uuid not null references public.content_releases(id) on delete restrict,
  run_id text not null references public.ingestion_runs(run_id) on delete cascade,
  candidate_id text not null,
  evidence_id text not null,
  source_id text not null references public.public_sources(source_id) on delete restrict,
  candidate_checksum text not null check (candidate_checksum ~ '^[a-f0-9]{64}$'),
  required_checks text[] not null check (cardinality(required_checks) > 0),
  required_roles text[] not null check (cardinality(required_roles) > 0),
  blocking_reasons text[] not null check (cardinality(blocking_reasons) > 0),
  status text not null check (status in ('pending', 'accepted', 'changes_requested', 'rejected', 'needs_specialist_review')),
  created_at timestamptz not null default timezone('utc', now()),
  unique (candidate_id, candidate_checksum)
);

create table public.evidence_review_decisions (
  id uuid primary key default extensions.gen_random_uuid(),
  task_id text not null references public.evidence_review_tasks(task_id) on delete cascade,
  candidate_checksum text not null check (candidate_checksum ~ '^[a-f0-9]{64}$'),
  role text not null check (role in ('licence', 'content', 'clinical', 'india_localisation', 'product')),
  decision text not null check (decision in ('accepted', 'changes_requested', 'rejected', 'needs_specialist_review')),
  reviewer_name text not null,
  reviewer_capacity text not null,
  reviewed_at date not null,
  reason text not null,
  exact_replacement_wording text,
  supporting_reference text,
  proposed_timing_change text,
  proposed_condition_change text,
  proposed_jurisdiction_change text,
  created_at timestamptz not null default timezone('utc', now()),
  unique (task_id, role),
  check (decision <> 'changes_requested' or coalesce(
    exact_replacement_wording, proposed_timing_change,
    proposed_condition_change, proposed_jurisdiction_change) is not null)
);

create table public.weekly_profiles (
  profile_id text not null,
  release_id uuid not null references public.content_releases(id) on delete restrict,
  stage text not null check (stage in ('possible_pregnancy', 'pregnancy', 'postpartum')),
  unit text not null check (unit in ('none', 'week', 'day')),
  range_start integer,
  range_end integer,
  jurisdiction text[] not null check (cardinality(jurisdiction) > 0),
  hero jsonb not null,
  card_slots jsonb not null default '{}'::jsonb,
  guidance_fragment_ids text[] not null default '{}',
  source_evidence_ids text[] not null default '{}',
  content_priority text not null,
  status text not null check (status in ('draft', 'reviewed', 'published', 'superseded')),
  content_checksum text not null check (content_checksum ~ '^[a-f0-9]{64}$'),
  primary key (release_id, profile_id)
);

create table public.guidance_fragments (
  fragment_id text not null,
  release_id uuid not null references public.content_releases(id) on delete restrict,
  domain text not null check (domain in ('journey', 'nutrition', 'movement', 'wellbeing', 'symptoms', 'preparation', 'followup')),
  text text not null,
  stage text not null check (stage in ('possible_pregnancy', 'pregnancy', 'postpartum')),
  unit text not null check (unit in ('none', 'week', 'day')),
  range_start integer,
  range_end integer,
  jurisdiction text[] not null check (cardinality(jurisdiction) > 0),
  evidence_ids text[] not null check (cardinality(evidence_ids) > 0),
  source_block_ids text[] not null check (cardinality(source_block_ids) > 0),
  conditions_required text[] not null default '{}',
  conditions_excluded text[] not null default '{}',
  presentation text not null check (presentation in ('paraphrase', 'quotation')),
  status text not null check (status in ('draft', 'reviewed', 'published', 'superseded')),
  content_checksum text not null check (content_checksum ~ '^[a-f0-9]{64}$'),
  primary key (release_id, fragment_id)
);

create table public.guideline_chunks (
  chunk_id text not null,
  release_id uuid not null references public.content_releases(id) on delete restrict,
  evidence_id text not null,
  source_id text not null references public.public_sources(source_id) on delete restrict,
  candidate_checksum text not null check (candidate_checksum ~ '^[a-f0-9]{64}$'),
  text text not null,
  source_block_ids text[] not null check (cardinality(source_block_ids) > 0),
  stage text not null check (stage in ('possible_pregnancy', 'pregnancy', 'postpartum')),
  unit text not null check (unit in ('none', 'week', 'day')),
  range_start integer,
  range_end integer,
  jurisdiction text[] not null check (cardinality(jurisdiction) > 0),
  domains text[] not null check (cardinality(domains) > 0),
  display_slots text[] not null check (cardinality(display_slots) > 0),
  conditions_required text[] not null default '{}',
  conditions_excluded text[] not null default '{}',
  embedding_provider text,
  embedding_model text,
  embedding_dimensions integer check (embedding_dimensions is null or embedding_dimensions > 0),
  embedding extensions.vector,
  status text not null check (status in ('reviewed', 'published', 'retired')),
  primary key (release_id, chunk_id),
  unique (release_id, evidence_id),
  check ((embedding is null) = (embedding_dimensions is null))
);

-- User-owned journey, document, planning and continuity records.
create table public.journey_states (
  id uuid primary key default extensions.gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  stage text not null check (stage in ('possible_pregnancy', 'pregnancy', 'postpartum')),
  timing_source text not null check (timing_source in (
    'document_estimated_due_date', 'user_estimated_due_date', 'manual_week_day',
    'approximate_month_range', 'delivery_date', 'postpartum_week')),
  gestational_week integer check (gestational_week between 1 and 42),
  gestational_day integer check (gestational_day between 0 and 6),
  postpartum_week integer check (postpartum_week between 1 and 12),
  postpartum_day integer check (postpartum_day between 0 and 7),
  estimated_due_date date,
  delivery_date date,
  approximate_month_min integer check (approximate_month_min between 1 and 10),
  approximate_month_max integer check (approximate_month_max between 1 and 10),
  user_confirmed boolean not null default false,
  has_dating_conflict boolean not null default false,
  is_current boolean not null default true,
  version integer not null default 1 check (version >= 1),
  derived_from_fact_ids uuid[] not null default '{}',
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  unique (workspace_id, version),
  unique (workspace_id, id),
  check ((approximate_month_min is null) = (approximate_month_max is null)),
  check (approximate_month_min is null or approximate_month_min <= approximate_month_max),
  check (stage <> 'possible_pregnancy' or (
    gestational_week is null and postpartum_week is null and postpartum_day is null and delivery_date is null)),
  check (stage <> 'pregnancy' or postpartum_week is null),
  check (stage <> 'postpartum' or gestational_week is null)
);

create unique index journey_states_one_current_per_workspace
on public.journey_states(workspace_id) where is_current;

create table public.private_documents (
  id uuid primary key default extensions.gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  storage_object_path text not null,
  original_filename text not null,
  media_type text not null,
  byte_size bigint not null check (byte_size > 0),
  sha256 text not null check (sha256 ~ '^[a-f0-9]{64}$'),
  status text not null check (status in ('uploaded', 'processing', 'needs_confirmation', 'confirmed', 'failed')),
  contains_real_medical_data boolean not null default false,
  failure_code text,
  uploaded_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  unique (workspace_id, storage_object_path),
  unique (workspace_id, id)
);

create table public.document_chunks (
  id uuid primary key default extensions.gen_random_uuid(),
  workspace_id uuid not null,
  document_id uuid not null,
  page integer check (page is null or page >= 1),
  source_span jsonb not null,
  text text not null,
  text_sha256 text not null check (text_sha256 ~ '^[a-f0-9]{64}$'),
  embedding_provider text,
  embedding_model text,
  embedding_dimensions integer check (embedding_dimensions is null or embedding_dimensions > 0),
  embedding extensions.vector,
  created_at timestamptz not null default timezone('utc', now()),
  foreign key (workspace_id, document_id)
    references public.private_documents(workspace_id, id) on delete cascade,
  unique (workspace_id, id),
  check ((embedding is null) = (embedding_dimensions is null))
);

create table public.document_facts (
  id uuid primary key default extensions.gen_random_uuid(),
  workspace_id uuid not null,
  document_id uuid not null,
  field_name text not null,
  value jsonb not null,
  source_page integer check (source_page is null or source_page >= 1),
  source_text text not null default '',
  confidence double precision not null check (confidence between 0 and 1),
  status text not null check (status in ('proposed', 'confirmed', 'rejected', 'conflict')),
  confirmed_at timestamptz,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  foreign key (workspace_id, document_id)
    references public.private_documents(workspace_id, id) on delete cascade,
  unique (workspace_id, id)
);

create table public.health_facts (
  id uuid primary key default extensions.gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  fact_type text not null check (fact_type in (
    'allergy', 'dietary_restriction', 'medical_history', 'medication',
    'clinician_instruction', 'feeding_status', 'delivery_history', 'other')),
  value jsonb not null,
  source_kind text not null check (source_kind in ('user_reported', 'document_extracted', 'human_reviewed')),
  confirmation_status text not null check (confirmation_status in ('proposed', 'confirmed', 'rejected', 'conflict')),
  source_document_id uuid,
  supersedes_fact_id uuid,
  valid_from timestamptz not null default timezone('utc', now()),
  valid_to timestamptz,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  unique (workspace_id, id),
  foreign key (workspace_id, source_document_id)
    references public.private_documents(workspace_id, id) on delete cascade,
  foreign key (workspace_id, supersedes_fact_id)
    references public.health_facts(workspace_id, id) on delete restrict
);

create table public.medication_mentions (
  id uuid primary key default extensions.gen_random_uuid(),
  workspace_id uuid not null,
  document_id uuid,
  name_as_written text not null,
  context_text text not null default '',
  status text not null check (status in ('proposed', 'confirmed', 'rejected', 'conflict')),
  created_at timestamptz not null default timezone('utc', now()),
  foreign key (workspace_id, document_id)
    references public.private_documents(workspace_id, id) on delete cascade,
  unique (workspace_id, id)
);

create table public.symptom_events (
  id uuid primary key default extensions.gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  description text not null,
  reported_at timestamptz not null default timezone('utc', now()),
  safety_route text not null check (safety_route in ('urgent', 'clarify', 'no_match')),
  matched_rule_ids text[] not null default '{}',
  user_confirmed boolean not null default false,
  created_at timestamptz not null default timezone('utc', now()),
  unique (workspace_id, id)
);

create table public.appointments (
  id uuid primary key default extensions.gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  scheduled_for timestamptz,
  appointment_type text not null default '',
  location text not null default '',
  status text not null check (status in ('planned', 'confirmed', 'completed', 'cancelled')),
  source_fact_id uuid,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  unique (workspace_id, id),
  foreign key (workspace_id, source_fact_id)
    references public.health_facts(workspace_id, id) on delete set null (source_fact_id)
);

create table public.appointment_questions (
  id uuid primary key default extensions.gen_random_uuid(),
  workspace_id uuid not null,
  appointment_id uuid not null,
  question text not null,
  source_fact_ids uuid[] not null default '{}',
  status text not null check (status in ('draft', 'saved', 'asked', 'archived')),
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  foreign key (workspace_id, appointment_id)
    references public.appointments(workspace_id, id) on delete cascade,
  unique (workspace_id, id)
);

create table public.plans (
  id uuid primary key default extensions.gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  version integer not null check (version >= 1),
  journey_state_id uuid not null,
  source_release_id uuid not null references public.content_releases(id) on delete restrict,
  status text not null check (status in ('draft', 'user_reviewed', 'saved', 'active', 'stale', 'replaced', 'archived')),
  stale_reasons text[] not null default '{}',
  user_confirmed_at timestamptz,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  unique (workspace_id, version),
  unique (workspace_id, id),
  foreign key (workspace_id, journey_state_id)
    references public.journey_states(workspace_id, id) on delete restrict,
  check (status not in ('saved', 'active') or user_confirmed_at is not null)
);

create table public.plan_items (
  id uuid primary key default extensions.gen_random_uuid(),
  workspace_id uuid not null,
  plan_id uuid not null,
  catalogue_item_id text,
  guidance_fragment_ids text[] not null default '{}',
  evidence_ids text[] not null check (cardinality(evidence_ids) > 0),
  confirmed_fact_ids uuid[] not null default '{}',
  category text not null check (category in (
    'nutrition', 'movement', 'wellbeing', 'preparation', 'followup', 'consider', 'avoid')),
  title text not null,
  body text not null,
  state text not null check (state in ('proposed', 'confirmed', 'stale')),
  position integer not null check (position >= 0),
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  foreign key (workspace_id, plan_id)
    references public.plans(workspace_id, id) on delete cascade,
  unique (plan_id, position),
  unique (workspace_id, id)
);

create table public.graph_nodes (
  id uuid primary key default extensions.gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  node_type text not null check (node_type in (
    'document', 'fact', 'restriction', 'symptom', 'appointment', 'question', 'plan', 'plan_item')),
  entity_id uuid not null,
  label text not null,
  source_document_id uuid,
  created_at timestamptz not null default timezone('utc', now()),
  foreign key (workspace_id, source_document_id)
    references public.private_documents(workspace_id, id) on delete cascade,
  unique (workspace_id, node_type, entity_id),
  unique (workspace_id, id)
);

create table public.graph_edges (
  id uuid primary key default extensions.gen_random_uuid(),
  workspace_id uuid not null,
  from_node_id uuid not null,
  to_node_id uuid not null,
  relation text not null,
  created_at timestamptz not null default timezone('utc', now()),
  foreign key (workspace_id, from_node_id)
    references public.graph_nodes(workspace_id, id) on delete cascade,
  foreign key (workspace_id, to_node_id)
    references public.graph_nodes(workspace_id, id) on delete cascade,
  unique (workspace_id, from_node_id, to_node_id, relation)
);

create table public.human_review_cases (
  id uuid primary key default extensions.gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  state text not null check (state in (
    'not_required', 'offered', 'consented', 'queued', 'reviewed',
    'resumed', 'declined', 'timed_out', 'unavailable')),
  reason text not null,
  packet jsonb,
  simulated boolean not null default true,
  consented_at timestamptz,
  reviewed_at timestamptz,
  reviewer_label text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  check (state not in ('consented', 'queued', 'reviewed', 'resumed') or consented_at is not null),
  check (state not in ('reviewed', 'resumed') or reviewed_at is not null)
);

create table public.notifications (
  id uuid primary key default extensions.gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  kind text not null,
  status text not null check (status in ('pending', 'sent', 'failed', 'cancelled')),
  idempotency_key text not null,
  payload jsonb not null default '{}'::jsonb,
  scheduled_for timestamptz,
  sent_at timestamptz,
  attempt_count integer not null default 0 check (attempt_count >= 0),
  last_error_code text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  unique (workspace_id, idempotency_key)
);

create table public.feedback (
  id uuid primary key default extensions.gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  rating integer check (rating between 1 and 5),
  category text not null,
  comment text not null default '',
  langsmith_trace_id text not null default '',
  created_at timestamptz not null default timezone('utc', now())
);

-- Fast deterministic and ownership lookups. Vector indexes wait for the chosen
-- provider dimension; pgvector cannot safely index mixed dimensions.
create index source_blocks_source_idx on public.source_blocks(source_id, source_artifact_id);
create index guideline_chunks_filter_idx on public.guideline_chunks(release_id, stage, range_start, range_end);
create index document_chunks_workspace_document_idx on public.document_chunks(workspace_id, document_id);
create index document_facts_workspace_status_idx on public.document_facts(workspace_id, status);
create index health_facts_workspace_type_status_idx on public.health_facts(workspace_id, fact_type, confirmation_status);
create index symptom_events_workspace_time_idx on public.symptom_events(workspace_id, reported_at desc);
create index appointments_workspace_time_idx on public.appointments(workspace_id, scheduled_for);
create index plans_workspace_status_idx on public.plans(workspace_id, status, version desc);
create index graph_edges_workspace_from_idx on public.graph_edges(workspace_id, from_node_id);
create index graph_edges_workspace_to_idx on public.graph_edges(workspace_id, to_node_id);
create index review_cases_workspace_state_idx on public.human_review_cases(workspace_id, state);

-- Updated timestamps.
do $$
declare table_name text;
begin
  foreach table_name in array array[
    'journey_states', 'private_documents', 'document_facts', 'health_facts',
    'appointments', 'appointment_questions', 'plans', 'plan_items',
    'human_review_cases', 'notifications'
  ] loop
    execute format(
      'create trigger %I_set_updated_at before update on public.%I '
      'for each row execute function private.set_updated_at()', table_name, table_name);
  end loop;
end;
$$;

-- RLS is mandatory even when grants or API exposure settings later change.
alter table public.workspaces enable row level security;
alter table public.workspace_members enable row level security;
alter table public.content_releases enable row level security;
alter table public.public_sources enable row level security;
alter table public.source_artifacts enable row level security;
alter table public.source_blocks enable row level security;
alter table public.ingestion_runs enable row level security;
alter table public.evidence_review_tasks enable row level security;
alter table public.evidence_review_decisions enable row level security;
alter table public.weekly_profiles enable row level security;
alter table public.guidance_fragments enable row level security;
alter table public.guideline_chunks enable row level security;
alter table public.journey_states enable row level security;
alter table public.private_documents enable row level security;
alter table public.document_chunks enable row level security;
alter table public.document_facts enable row level security;
alter table public.health_facts enable row level security;
alter table public.medication_mentions enable row level security;
alter table public.symptom_events enable row level security;
alter table public.appointments enable row level security;
alter table public.appointment_questions enable row level security;
alter table public.plans enable row level security;
alter table public.plan_items enable row level security;
alter table public.graph_nodes enable row level security;
alter table public.graph_edges enable row level security;
alter table public.human_review_cases enable row level security;
alter table public.notifications enable row level security;
alter table public.feedback enable row level security;

create policy "users create own workspaces" on public.workspaces
for insert to authenticated with check (owner_user_id = auth.uid());
create policy "members read workspaces" on public.workspaces
for select to authenticated using (private.is_workspace_member(id));
create policy "owners update workspaces" on public.workspaces
for update to authenticated using (owner_user_id = auth.uid()) with check (owner_user_id = auth.uid());
create policy "owners delete workspaces" on public.workspaces
for delete to authenticated using (owner_user_id = auth.uid());

create policy "members read membership" on public.workspace_members
for select to authenticated using (private.is_workspace_member(workspace_id));
create policy "owners manage membership" on public.workspace_members
for all to authenticated using (private.is_workspace_owner(workspace_id))
with check (private.is_workspace_owner(workspace_id));

create policy "read published content releases" on public.content_releases
for select to anon, authenticated using (status = 'published');

create policy "read published sources" on public.public_sources
for select to anon, authenticated using (
  status = 'published' and exists (
    select 1 from public.content_releases release
    where release.id = public.public_sources.release_id and release.status = 'published'));

create policy "read blocks from published releases" on public.source_blocks
for select to anon, authenticated using (exists (
  select 1 from public.content_releases release
  where release.id = public.source_blocks.release_id and release.status = 'published'));

create policy "read published weekly profiles" on public.weekly_profiles
for select to anon, authenticated using (
  status = 'published' and exists (
    select 1 from public.content_releases release
    where release.id = public.weekly_profiles.release_id and release.status = 'published'));

create policy "read published guidance fragments" on public.guidance_fragments
for select to anon, authenticated using (
  status = 'published' and exists (
    select 1 from public.content_releases release
    where release.id = public.guidance_fragments.release_id and release.status = 'published'));

create policy "read published guideline chunks" on public.guideline_chunks
for select to anon, authenticated using (
  status = 'published' and exists (
    select 1 from public.content_releases release
    where release.id = public.guideline_chunks.release_id and release.status = 'published'));

-- All user-owned records use the same database-enforced workspace boundary.
do $$
declare table_name text;
begin
  foreach table_name in array array[
    'journey_states', 'private_documents', 'document_chunks', 'document_facts',
    'health_facts', 'medication_mentions', 'symptom_events', 'appointments',
    'appointment_questions', 'plans', 'plan_items', 'graph_nodes', 'graph_edges',
    'human_review_cases', 'notifications', 'feedback'
  ] loop
    execute format(
      'create policy %I on public.%I for all to authenticated '
      'using (private.is_workspace_member(workspace_id)) '
      'with check (private.is_workspace_member(workspace_id))',
      'workspace members manage ' || table_name, table_name);
  end loop;
end;
$$;

-- Only explicitly published public knowledge is granted to API clients.
revoke all on public.content_releases, public.public_sources, public.source_artifacts,
  public.source_blocks, public.ingestion_runs, public.evidence_review_tasks,
  public.evidence_review_decisions, public.weekly_profiles, public.guidance_fragments,
  public.guideline_chunks from anon, authenticated;
grant select on public.content_releases, public.public_sources, public.source_blocks,
  public.weekly_profiles, public.guidance_fragments, public.guideline_chunks to anon, authenticated;

grant select, insert, update, delete on public.workspaces, public.workspace_members,
  public.journey_states, public.private_documents, public.document_chunks,
  public.document_facts, public.health_facts, public.medication_mentions,
  public.symptom_events, public.appointments, public.appointment_questions,
  public.plans, public.plan_items, public.graph_nodes, public.graph_edges,
  public.human_review_cases, public.notifications, public.feedback to authenticated;

grant usage on schema private to authenticated;
grant execute on function private.is_workspace_member(uuid) to authenticated;
grant execute on function private.is_workspace_owner(uuid) to authenticated;

create or replace function public.match_guideline_chunks(
  query_embedding extensions.vector,
  requested_stage text,
  requested_unit text,
  requested_position integer,
  requested_jurisdictions text[],
  match_count integer default 8
)
returns table (
  chunk_id text,
  evidence_id text,
  source_id text,
  text text,
  source_block_ids text[],
  similarity double precision
)
language sql
stable
security invoker
set search_path = public, extensions, pg_temp
as $$
  select chunk.chunk_id, chunk.evidence_id, chunk.source_id, chunk.text,
         chunk.source_block_ids, 1 - (chunk.embedding <=> query_embedding) as similarity
  from public.guideline_chunks chunk
  join public.content_releases release on release.id = chunk.release_id
  where release.status = 'published'
    and chunk.status = 'published'
    and chunk.embedding is not null
    and chunk.stage = requested_stage
    and chunk.unit = requested_unit
    and (requested_unit = 'none' or requested_position between chunk.range_start and chunk.range_end)
    and (chunk.jurisdiction && requested_jurisdictions or 'GLOBAL' = any(chunk.jurisdiction))
    and extensions.vector_dims(chunk.embedding) = extensions.vector_dims(query_embedding)
  order by chunk.embedding <=> query_embedding
  limit greatest(1, least(match_count, 20));
$$;

create or replace function public.match_document_chunks(
  requested_workspace_id uuid,
  query_embedding extensions.vector,
  match_count integer default 6
)
returns table (
  chunk_id uuid,
  document_id uuid,
  page integer,
  text text,
  source_span jsonb,
  similarity double precision
)
language sql
stable
security invoker
set search_path = public, extensions, pg_temp
as $$
  select chunk.id, chunk.document_id, chunk.page, chunk.text, chunk.source_span,
         1 - (chunk.embedding <=> query_embedding) as similarity
  from public.document_chunks chunk
  where chunk.workspace_id = requested_workspace_id
    and private.is_workspace_member(requested_workspace_id)
    and chunk.embedding is not null
    and extensions.vector_dims(chunk.embedding) = extensions.vector_dims(query_embedding)
  order by chunk.embedding <=> query_embedding
  limit greatest(1, least(match_count, 20));
$$;

grant execute on function public.match_guideline_chunks(
  extensions.vector, text, text, integer, text[], integer) to anon, authenticated;
grant execute on function public.match_document_chunks(
  uuid, extensions.vector, integer) to authenticated;

-- Original medical documents are private. The first path component must be a
-- workspace UUID that the signed-in user can access.
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('medical-documents', 'medical-documents', false, 10485760,
        array['application/pdf', 'image/png', 'image/jpeg'])
on conflict (id) do update set public = false, file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;

create or replace function private.storage_workspace_id(object_name text)
returns uuid
language plpgsql
immutable
security invoker
set search_path = pg_temp
as $$
begin
  return split_part(object_name, '/', 1)::uuid;
exception when invalid_text_representation then
  return null;
end;
$$;

create policy "members read private medical documents" on storage.objects
for select to authenticated using (
  bucket_id = 'medical-documents'
  and private.is_workspace_member(private.storage_workspace_id(name)));
create policy "members upload private medical documents" on storage.objects
for insert to authenticated with check (
  bucket_id = 'medical-documents'
  and private.is_workspace_member(private.storage_workspace_id(name)));
create policy "members update private medical documents" on storage.objects
for update to authenticated using (
  bucket_id = 'medical-documents'
  and private.is_workspace_member(private.storage_workspace_id(name)))
with check (
  bucket_id = 'medical-documents'
  and private.is_workspace_member(private.storage_workspace_id(name)));
create policy "members delete private medical documents" on storage.objects
for delete to authenticated using (
  bucket_id = 'medical-documents'
  and private.is_workspace_member(private.storage_workspace_id(name)));

commit;
