-- Authenticated workspace lifecycle and compare-and-set journey updates.

begin;

alter table public.private_documents
  add constraint private_documents_workspace_hash_key unique (workspace_id, sha256);

create or replace function public.create_workspace(
  requested_mode text,
  requested_display_name text
)
returns uuid
language plpgsql
volatile
security invoker
set search_path = public, pg_temp
as $$
declare
  created_id uuid;
begin
  if auth.uid() is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  if requested_mode not in ('personal_empty', 'fictional_demo') then
    raise exception 'invalid workspace mode' using errcode = '22023';
  end if;
  insert into public.workspaces(owner_user_id, mode, display_name)
  values (auth.uid(), requested_mode, requested_display_name)
  returning id into created_id;
  return created_id;
end;
$$;

create or replace function public.replace_current_journey_state(
  requested_workspace_id uuid,
  expected_current_version integer,
  requested_stage text,
  requested_timing_source text,
  requested_gestational_week integer default null,
  requested_gestational_day integer default null,
  requested_postpartum_week integer default null,
  requested_postpartum_day integer default null,
  requested_estimated_due_date date default null,
  requested_delivery_date date default null,
  requested_approximate_month_min integer default null,
  requested_approximate_month_max integer default null,
  requested_user_confirmed boolean default false,
  requested_has_dating_conflict boolean default false,
  requested_derived_from_fact_ids uuid[] default '{}'
)
returns public.journey_states
language plpgsql
volatile
security invoker
set search_path = public, pg_temp
as $$
declare
  current_version integer;
  created public.journey_states;
begin
  if not private.is_workspace_member(requested_workspace_id) then
    raise exception 'workspace access denied' using errcode = '42501';
  end if;

  perform 1 from public.workspaces
  where id = requested_workspace_id
  for update;

  select version into current_version
  from public.journey_states
  where workspace_id = requested_workspace_id and is_current
  for update;

  current_version := coalesce(current_version, 0);
  if current_version <> expected_current_version then
    raise exception 'stale journey version: expected %, current %',
      expected_current_version, current_version using errcode = '40001';
  end if;

  update public.journey_states
  set is_current = false
  where workspace_id = requested_workspace_id and is_current;

  insert into public.journey_states(
    workspace_id, stage, timing_source, gestational_week, gestational_day,
    postpartum_week, postpartum_day, estimated_due_date, delivery_date,
    approximate_month_min, approximate_month_max, user_confirmed,
    has_dating_conflict, is_current, version, derived_from_fact_ids
  ) values (
    requested_workspace_id, requested_stage, requested_timing_source,
    requested_gestational_week, requested_gestational_day,
    requested_postpartum_week, requested_postpartum_day,
    requested_estimated_due_date, requested_delivery_date,
    requested_approximate_month_min, requested_approximate_month_max,
    requested_user_confirmed, requested_has_dating_conflict, true,
    current_version + 1, requested_derived_from_fact_ids
  ) returning * into created;

  return created;
end;
$$;

create or replace function public.reset_demo_workspace_state(
  requested_workspace_id uuid,
  expected_workspace_updated_at timestamptz
)
returns timestamptz
language plpgsql
volatile
security definer
set search_path = public, storage, pg_temp
as $$
declare
  current_updated_at timestamptz;
  resulting_updated_at timestamptz;
begin
  if auth.uid() is null or not private.is_workspace_owner(requested_workspace_id) then
    raise exception 'workspace owner access required' using errcode = '42501';
  end if;

  select updated_at into current_updated_at
  from public.workspaces
  where id = requested_workspace_id and mode = 'fictional_demo'
  for update;

  if current_updated_at is null then
    raise exception 'fictional demo workspace not found' using errcode = '22023';
  end if;
  if current_updated_at <> expected_workspace_updated_at then
    raise exception 'stale workspace reset request' using errcode = '40001';
  end if;
  if exists (
    select 1 from storage.objects object
    where object.bucket_id = 'medical-documents'
      and private.storage_workspace_id(object.name) = requested_workspace_id
  ) then
    raise exception 'remove workspace files through the Storage API before database reset'
      using errcode = '55000';
  end if;

  delete from public.notifications where workspace_id = requested_workspace_id;
  delete from public.feedback where workspace_id = requested_workspace_id;
  delete from public.human_review_cases where workspace_id = requested_workspace_id;
  delete from public.plans where workspace_id = requested_workspace_id;
  delete from public.appointments where workspace_id = requested_workspace_id;
  delete from public.symptom_events where workspace_id = requested_workspace_id;
  delete from public.graph_nodes where workspace_id = requested_workspace_id;
  delete from public.medication_mentions where workspace_id = requested_workspace_id;
  delete from public.health_facts where workspace_id = requested_workspace_id;
  delete from public.private_documents where workspace_id = requested_workspace_id;
  delete from public.journey_states where workspace_id = requested_workspace_id;

  update public.workspaces
  set updated_at = clock_timestamp()
  where id = requested_workspace_id
  returning updated_at into resulting_updated_at;
  return resulting_updated_at;
end;
$$;

revoke all on function public.create_workspace(text, text) from public, anon;
revoke all on function public.replace_current_journey_state(
  uuid, integer, text, text, integer, integer, integer, integer,
  date, date, integer, integer, boolean, boolean, uuid[]) from public, anon;
revoke all on function public.reset_demo_workspace_state(uuid, timestamptz) from public, anon;

grant execute on function public.create_workspace(text, text) to authenticated;
grant execute on function public.replace_current_journey_state(
  uuid, integer, text, text, integer, integer, integer, integer,
  date, date, integer, integer, boolean, boolean, uuid[]) to authenticated;
grant execute on function public.reset_demo_workspace_state(uuid, timestamptz) to authenticated;

commit;
