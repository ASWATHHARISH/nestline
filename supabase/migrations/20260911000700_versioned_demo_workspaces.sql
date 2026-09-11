-- Stage 2 correction: create one deterministic fictional workspace per session
-- and support a storage-aware reset/reseed workflow.

begin;

alter table public.workspaces
  add column demo_session_key text,
  add column demo_seed_version text;

-- Preserve an explicit label if a pre-existing fictional workspace is found.
-- The currently verified development database contains no such rows.
update public.workspaces
set demo_session_key = 'legacy-' || id::text,
    demo_seed_version = 'legacy-unseeded'
where mode = 'fictional_demo' and demo_session_key is null;

alter table public.workspaces
  add constraint workspaces_demo_identity_check check (
    (mode = 'personal_empty' and demo_session_key is null and demo_seed_version is null)
    or
    (mode = 'fictional_demo'
      and length(trim(demo_session_key)) between 8 and 128
      and demo_seed_version in ('maya-v1'))
  );

create unique index workspaces_owner_demo_session_key
on public.workspaces(owner_user_id, demo_session_key)
where mode = 'fictional_demo';

create or replace function private.seed_demo_workspace_state(
  requested_workspace_id uuid,
  requested_seed_version text
)
returns void
language plpgsql
volatile
security definer
set search_path = public, pg_temp
as $$
begin
  if auth.uid() is null or not private.is_workspace_owner(requested_workspace_id) then
    raise exception 'workspace owner access required' using errcode = '42501';
  end if;
  if not exists (
    select 1 from public.workspaces workspace
    where workspace.id = requested_workspace_id
      and workspace.mode = 'fictional_demo'
      and workspace.demo_seed_version = requested_seed_version
  ) then
    raise exception 'fictional demo workspace or seed version not found' using errcode = '22023';
  end if;
  if requested_seed_version <> 'maya-v1' then
    raise exception 'unsupported demo seed version' using errcode = '22023';
  end if;
  if exists (select 1 from public.journey_states where workspace_id = requested_workspace_id)
     or exists (select 1 from public.health_facts where workspace_id = requested_workspace_id)
     or exists (select 1 from public.appointments where workspace_id = requested_workspace_id) then
    raise exception 'demo workspace must be empty before seeding' using errcode = '55000';
  end if;

  insert into public.journey_states(
    workspace_id, stage, timing_source, gestational_week, gestational_day,
    user_confirmed, has_dating_conflict, is_current, version
  ) values (
    requested_workspace_id, 'pregnancy', 'manual_week_day', 24, 2,
    true, false, true, 1
  );

  insert into public.health_facts(
    workspace_id, fact_type, value, source_kind, confirmation_status
  ) values
    (requested_workspace_id, 'allergy',
      '{"label":"Peanut allergy","fictional":true}'::jsonb,
      'user_reported', 'confirmed'),
    (requested_workspace_id, 'dietary_restriction',
      '{"label":"Vegetarian","fictional":true}'::jsonb,
      'user_reported', 'confirmed'),
    (requested_workspace_id, 'medical_history',
      '{"label":"Hypothyroidism","fictional":true}'::jsonb,
      'user_reported', 'confirmed');

  insert into public.appointments(
    workspace_id, scheduled_for, appointment_type, location, status
  ) values (
    requested_workspace_id,
    '2026-09-25 10:00:00+05:30'::timestamptz,
    'Routine antenatal follow-up',
    'Fictional clinic',
    'confirmed'
  );
end;
$$;

create or replace function public.create_demo_workspace(
  requested_session_key text,
  requested_display_name text,
  requested_seed_version text default 'maya-v1'
)
returns uuid
language plpgsql
volatile
security invoker
set search_path = public, pg_temp
as $$
declare
  created_id uuid;
  existing_seed_version text;
begin
  if auth.uid() is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  if length(trim(requested_session_key)) not between 8 and 128 then
    raise exception 'demo session key must contain 8 to 128 characters' using errcode = '22023';
  end if;
  if requested_seed_version <> 'maya-v1' then
    raise exception 'unsupported demo seed version' using errcode = '22023';
  end if;

  select workspace.id, workspace.demo_seed_version
  into created_id, existing_seed_version
  from public.workspaces workspace
  where workspace.owner_user_id = auth.uid()
    and workspace.mode = 'fictional_demo'
    and workspace.demo_session_key = trim(requested_session_key);

  if created_id is not null then
    if existing_seed_version <> requested_seed_version then
      raise exception 'demo session key already belongs to another seed version'
        using errcode = '23505';
    end if;
    return created_id;
  end if;

  insert into public.workspaces(
    owner_user_id, mode, display_name, demo_session_key, demo_seed_version
  ) values (
    auth.uid(), 'fictional_demo', requested_display_name,
    trim(requested_session_key), requested_seed_version
  ) returning id into created_id;

  perform private.seed_demo_workspace_state(created_id, requested_seed_version);
  return created_id;
end;
$$;

create or replace function public.reseed_demo_workspace_state(
  requested_workspace_id uuid,
  expected_workspace_updated_at timestamptz,
  requested_seed_version text default 'maya-v1'
)
returns timestamptz
language plpgsql
volatile
security invoker
set search_path = public, pg_temp
as $$
declare
  resulting_updated_at timestamptz;
begin
  if not exists (
    select 1 from public.workspaces workspace
    where workspace.id = requested_workspace_id
      and workspace.owner_user_id = auth.uid()
      and workspace.mode = 'fictional_demo'
      and workspace.demo_seed_version = requested_seed_version
  ) then
    raise exception 'owned fictional demo workspace or seed version not found'
      using errcode = '22023';
  end if;

  resulting_updated_at := public.reset_demo_workspace_state(
    requested_workspace_id, expected_workspace_updated_at
  );
  perform private.seed_demo_workspace_state(requested_workspace_id, requested_seed_version);
  return resulting_updated_at;
end;
$$;

revoke all on function public.create_demo_workspace(text, text, text) from public, anon;
revoke all on function public.reseed_demo_workspace_state(uuid, timestamptz, text) from public, anon;
grant execute on function public.create_demo_workspace(text, text, text) to authenticated;
grant execute on function public.reseed_demo_workspace_state(uuid, timestamptz, text) to authenticated;

comment on function public.create_demo_workspace(text, text, text) is
  'Creates or returns one owner-scoped fictional workspace for a session key and applies the versioned Maya seed.';
comment on function public.reseed_demo_workspace_state(uuid, timestamptz, text) is
  'After Storage objects are removed, atomically resets and reapplies the workspace seed.';

commit;
