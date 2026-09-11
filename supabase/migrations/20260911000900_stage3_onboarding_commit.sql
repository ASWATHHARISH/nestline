-- Stage 3: durable onboarding provenance and one atomic confirmed commit.

begin;

alter table public.journey_states
  add column effective_date date,
  add column calculation_date date,
  add column confirmed_at timestamptz,
  add column confirmed_by_user_id uuid,
  add column conflicts_with_state_id uuid,
  add column dating_difference_days integer,
  add column onboarding_submission_key text,
  add column onboarding_payload_sha256 text;

update public.journey_states state
set effective_date = (state.created_at at time zone 'utc')::date,
    calculation_date = (state.created_at at time zone 'utc')::date,
    confirmed_at = case when state.user_confirmed then state.updated_at else null end,
    confirmed_by_user_id = case when state.user_confirmed then workspace.owner_user_id else null end
from public.workspaces workspace
where workspace.id = state.workspace_id;

alter table public.journey_states
  alter column effective_date set not null,
  alter column effective_date set default current_date,
  alter column calculation_date set not null,
  alter column calculation_date set default current_date,
  add constraint journey_states_effective_calculation_order_check
    check (effective_date <= calculation_date),
  add constraint journey_states_conflict_reference_check check (
    conflicts_with_state_id is null
    or (has_dating_conflict and dating_difference_days is not null)
  ),
  add constraint journey_states_dating_difference_check
    check (dating_difference_days is null or dating_difference_days >= 0),
  add constraint journey_states_onboarding_idempotency_check check (
    (onboarding_submission_key is null and onboarding_payload_sha256 is null)
    or (
      length(trim(onboarding_submission_key)) between 16 and 128
      and onboarding_payload_sha256 ~ '^[a-f0-9]{64}$'
    )
  ),
  add constraint journey_states_workspace_conflict_state_fk
    foreign key (workspace_id, conflicts_with_state_id)
    references public.journey_states(workspace_id, id) on delete restrict;

create unique index journey_states_workspace_onboarding_submission_key
on public.journey_states(workspace_id, onboarding_submission_key)
where onboarding_submission_key is not null;

alter table public.health_facts
  add column onboarding_submission_key text;
alter table public.symptom_events
  add column onboarding_submission_key text,
  add column input_source text not null default 'onboarding',
  add column safety_spec_version text,
  add column safety_evaluation_only boolean not null default true,
  add constraint symptom_events_input_source_check
    check (input_source in ('onboarding', 'chat', 'check_in', 'document'));
alter table public.appointments
  add column onboarding_submission_key text;

create index health_facts_onboarding_submission
  on public.health_facts(workspace_id, onboarding_submission_key)
  where onboarding_submission_key is not null;
create index symptom_events_onboarding_submission
  on public.symptom_events(workspace_id, onboarding_submission_key)
  where onboarding_submission_key is not null;
create index appointments_onboarding_submission
  on public.appointments(workspace_id, onboarding_submission_key)
  where onboarding_submission_key is not null;

-- A confirmed state transition must pass through the atomic committer below.
-- Owners retain read access to their full history, while direct inserts, updates,
-- deletes, and the superseded Stage 2 mutation RPC are closed.
drop policy if exists "workspace members manage journey_states"
  on public.journey_states;
create policy "workspace owners read journey_states"
  on public.journey_states for select to authenticated
  using (private.is_workspace_owner(workspace_id));

revoke insert, update, delete on public.journey_states from authenticated;
revoke execute on function public.replace_current_journey_state(
  uuid, integer, text, text, integer, integer, integer, integer,
  date, date, integer, integer, boolean, boolean, uuid[]
) from authenticated;

create or replace function public.complete_onboarding(
  requested_workspace_id uuid,
  expected_current_version integer,
  requested_submission_key text,
  requested_payload_sha256 text,
  requested_journey jsonb,
  requested_has_dating_conflict boolean,
  requested_conflicts_with_state_id uuid,
  requested_dating_difference_days integer,
  requested_facts jsonb,
  requested_symptoms jsonb,
  requested_appointments jsonb
)
returns jsonb
language plpgsql
volatile
security definer
set search_path = public, private, pg_temp
as $$
declare
  current_state_id uuid;
  current_version integer;
  next_version integer;
  existing_state public.journey_states;
  created_state public.journey_states;
  item jsonb;
  created_id uuid;
  fact_ids uuid[] := '{}'::uuid[];
  symptom_ids uuid[] := '{}'::uuid[];
  appointment_ids uuid[] := '{}'::uuid[];
  derived_fact_ids uuid[] := '{}'::uuid[];
  matched_rule_ids text[] := '{}'::text[];
  submitted_calculation_date date;
begin
  if auth.uid() is null or not private.is_workspace_owner(requested_workspace_id) then
    raise exception 'workspace owner access required' using errcode = '42501';
  end if;
  if expected_current_version is null or expected_current_version < 0 then
    raise exception 'expected current version must be zero or greater' using errcode = '22023';
  end if;
  if requested_submission_key is null
     or length(trim(requested_submission_key)) not between 16 and 128 then
    raise exception 'submission key must contain 16 to 128 characters' using errcode = '22023';
  end if;
  if requested_payload_sha256 is null
     or requested_payload_sha256 !~ '^[a-f0-9]{64}$' then
    raise exception 'invalid onboarding payload checksum' using errcode = '22023';
  end if;
  if jsonb_typeof(requested_journey) <> 'object'
     or jsonb_typeof(requested_facts) <> 'array'
     or jsonb_typeof(requested_symptoms) <> 'array'
     or jsonb_typeof(requested_appointments) <> 'array' then
    raise exception 'onboarding payload has invalid JSON shapes' using errcode = '22023';
  end if;
  if jsonb_array_length(requested_facts) > 40
     or jsonb_array_length(requested_symptoms) > 10
     or jsonb_array_length(requested_appointments) > 10 then
    raise exception 'onboarding payload exceeds item limits' using errcode = '22023';
  end if;

  select * into existing_state
  from public.journey_states state
  where state.workspace_id = requested_workspace_id
    and state.onboarding_submission_key = trim(requested_submission_key);

  if existing_state.id is not null then
    if existing_state.onboarding_payload_sha256 <> requested_payload_sha256 then
      raise exception 'submission key already belongs to different onboarding data'
        using errcode = '23505';
    end if;
    select coalesce(array_agg(id order by id), '{}'::uuid[]) into fact_ids
      from public.health_facts
      where workspace_id = requested_workspace_id
        and onboarding_submission_key = trim(requested_submission_key);
    select coalesce(array_agg(id order by id), '{}'::uuid[]) into symptom_ids
      from public.symptom_events
      where workspace_id = requested_workspace_id
        and onboarding_submission_key = trim(requested_submission_key);
    select coalesce(array_agg(id order by id), '{}'::uuid[]) into appointment_ids
      from public.appointments
      where workspace_id = requested_workspace_id
        and onboarding_submission_key = trim(requested_submission_key);
    return jsonb_build_object(
      'journey_state_id', existing_state.id,
      'version', existing_state.version,
      'fact_ids', to_jsonb(fact_ids),
      'symptom_event_ids', to_jsonb(symptom_ids),
      'appointment_ids', to_jsonb(appointment_ids),
      'idempotent_replay', true
    );
  end if;

  perform 1 from public.workspaces
  where id = requested_workspace_id and owner_user_id = auth.uid()
  for update;

  select state.id, state.version into current_state_id, current_version
  from public.journey_states state
  where state.workspace_id = requested_workspace_id and state.is_current
  for update;

  current_version := coalesce(current_version, 0);
  if current_version <> expected_current_version then
    raise exception 'stale journey version: expected %, current %',
      expected_current_version, current_version using errcode = '40001';
  end if;
  if requested_has_dating_conflict then
    if current_state_id is null
       or requested_conflicts_with_state_id is distinct from current_state_id
       or requested_dating_difference_days is null then
      raise exception 'dating conflict must reference the current journey state'
        using errcode = '22023';
    end if;
  elsif requested_conflicts_with_state_id is not null
        or requested_dating_difference_days is not null then
    raise exception 'non-conflicting timing cannot include conflict provenance'
      using errcode = '22023';
  end if;

  submitted_calculation_date := (requested_journey->>'calculation_date')::date;
  if (requested_journey->>'effective_date')::date > submitted_calculation_date
     or submitted_calculation_date >
       (clock_timestamp() at time zone 'Asia/Kolkata')::date then
    raise exception 'invalid effective or future calculation date' using errcode = '22023';
  end if;

  if requested_journey ? 'derived_from_fact_ids' then
    if jsonb_typeof(requested_journey->'derived_from_fact_ids') <> 'array' then
      raise exception 'derived fact IDs must be an array' using errcode = '22023';
    end if;
    select coalesce(array_agg(value::uuid), '{}'::uuid[]) into derived_fact_ids
    from jsonb_array_elements_text(requested_journey->'derived_from_fact_ids') values_to_cast(value);
  end if;

  select coalesce(max(version), 0) + 1 into next_version
  from public.journey_states where workspace_id = requested_workspace_id;

  update public.journey_states
  set is_current = false
  where workspace_id = requested_workspace_id and is_current;

  insert into public.journey_states(
    workspace_id, stage, timing_source, gestational_week, gestational_day,
    postpartum_week, postpartum_day, estimated_due_date, delivery_date,
    approximate_month_min, approximate_month_max, user_confirmed,
    has_dating_conflict, is_current, version, derived_from_fact_ids,
    effective_date, calculation_date, confirmed_at, confirmed_by_user_id,
    conflicts_with_state_id, dating_difference_days,
    onboarding_submission_key, onboarding_payload_sha256
  ) values (
    requested_workspace_id,
    requested_journey->>'stage',
    requested_journey->>'timing_source',
    nullif(requested_journey->>'gestational_week', '')::integer,
    nullif(requested_journey->>'gestational_day', '')::integer,
    nullif(requested_journey->>'postpartum_week', '')::integer,
    nullif(requested_journey->>'postpartum_day', '')::integer,
    nullif(requested_journey->>'estimated_due_date', '')::date,
    nullif(requested_journey->>'delivery_date', '')::date,
    nullif(requested_journey->>'approximate_month_min', '')::integer,
    nullif(requested_journey->>'approximate_month_max', '')::integer,
    true, requested_has_dating_conflict, true, next_version, derived_fact_ids,
    (requested_journey->>'effective_date')::date,
    submitted_calculation_date,
    clock_timestamp(), auth.uid(),
    requested_conflicts_with_state_id, requested_dating_difference_days,
    trim(requested_submission_key), requested_payload_sha256
  ) returning * into created_state;

  for item in select value from jsonb_array_elements(requested_facts)
  loop
    if item->>'fact_type' not in (
      'allergy', 'dietary_restriction', 'medical_history', 'medication',
      'clinician_instruction', 'feeding_status', 'delivery_history', 'other'
    ) or jsonb_typeof(item->'value') <> 'object'
       or coalesce(length(trim(item->'value'->>'label')), 0) not between 1 and 200 then
      raise exception 'invalid reported fact' using errcode = '22023';
    end if;
    insert into public.health_facts(
      workspace_id, fact_type, value, source_kind, confirmation_status,
      onboarding_submission_key
    ) values (
      requested_workspace_id, item->>'fact_type', item->'value',
      'user_reported', 'confirmed', trim(requested_submission_key)
    ) returning id into created_id;
    fact_ids := array_append(fact_ids, created_id);
  end loop;

  for item in select value from jsonb_array_elements(requested_symptoms)
  loop
    if length(trim(item->>'description')) not between 1 and 1000
       or (item->>'reported_at')::timestamptz > clock_timestamp()
       or item->>'safety_route' not in ('urgent', 'clarify', 'no_match')
       or length(trim(item->>'safety_spec_version')) not between 1 and 100
       or jsonb_typeof(item->'matched_rule_ids') <> 'array' then
      raise exception 'invalid symptom event' using errcode = '22023';
    end if;
    select coalesce(array_agg(value), '{}'::text[]) into matched_rule_ids
    from jsonb_array_elements_text(item->'matched_rule_ids') values_to_keep(value);
    insert into public.symptom_events(
      workspace_id, description, reported_at, safety_route, matched_rule_ids,
      user_confirmed, input_source, safety_spec_version,
      safety_evaluation_only, onboarding_submission_key
    ) values (
      requested_workspace_id, trim(item->>'description'),
      (item->>'reported_at')::timestamptz, item->>'safety_route',
      matched_rule_ids, true, 'onboarding', trim(item->>'safety_spec_version'),
      (item->>'safety_evaluation_only')::boolean, trim(requested_submission_key)
    ) returning id into created_id;
    symptom_ids := array_append(symptom_ids, created_id);
  end loop;

  for item in select value from jsonb_array_elements(requested_appointments)
  loop
    if (item->>'scheduled_for')::timestamptz <= clock_timestamp()
       or length(trim(item->>'appointment_type')) not between 1 and 200
       or length(coalesce(item->>'location', '')) > 300 then
      raise exception 'invalid next appointment' using errcode = '22023';
    end if;
    insert into public.appointments(
      workspace_id, scheduled_for, appointment_type, location, status,
      onboarding_submission_key
    ) values (
      requested_workspace_id, (item->>'scheduled_for')::timestamptz,
      trim(item->>'appointment_type'), trim(coalesce(item->>'location', '')),
      'confirmed', trim(requested_submission_key)
    ) returning id into created_id;
    appointment_ids := array_append(appointment_ids, created_id);
  end loop;

  return jsonb_build_object(
    'journey_state_id', created_state.id,
    'version', created_state.version,
    'fact_ids', to_jsonb(fact_ids),
    'symptom_event_ids', to_jsonb(symptom_ids),
    'appointment_ids', to_jsonb(appointment_ids),
    'idempotent_replay', false
  );
end;
$$;

revoke all on function public.complete_onboarding(
  uuid, integer, text, text, jsonb, boolean, uuid, integer, jsonb, jsonb, jsonb
) from public, anon;
grant execute on function public.complete_onboarding(
  uuid, integer, text, text, jsonb, boolean, uuid, integer, jsonb, jsonb, jsonb
) to authenticated;

comment on function public.complete_onboarding(
  uuid, integer, text, text, jsonb, boolean, uuid, integer, jsonb, jsonb, jsonb
) is 'Atomically commits one explicitly confirmed, idempotent onboarding submission for the authenticated workspace owner.';
comment on column public.journey_states.effective_date is
  'Date on which the source week/day/month observation was effective.';
comment on column public.journey_states.calculation_date is
  'Reference date used by deterministic Python to calculate the displayed state.';
comment on column public.symptom_events.safety_evaluation_only is
  'True while the applied safety rule specification still awaits specialist publication.';

commit;