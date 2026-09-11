-- Stage 3 exit hardening: recheck deterministic timing and draft-safety
-- provenance inside Postgres so crafted RPC payloads cannot bypass the app.

begin;

alter table public.journey_states
  add constraint journey_states_edd_arithmetic_check check (
    timing_source not in ('document_estimated_due_date', 'user_estimated_due_date')
    or gestational_week * 7 + gestational_day =
       280 - (estimated_due_date - calculation_date)
  ),
  add constraint journey_states_delivery_arithmetic_check check (
    timing_source <> 'delivery_date'
    or (
      (postpartum_week - 1) * 7 + postpartum_day = calculation_date - delivery_date
      and effective_date = delivery_date
    )
  ),
  add constraint journey_states_confirmation_provenance_check check (
    (confirmed_at is null) = (confirmed_by_user_id is null)
    and (not user_confirmed or confirmed_at is not null)
  );

alter table public.symptom_events
  add constraint symptom_events_onboarding_safety_draft_check check (
    onboarding_submission_key is null or safety_evaluation_only
  );

create or replace function private.journey_state_position_bounds(
  requested_stage text,
  requested_timing_source text,
  requested_gestational_week integer,
  requested_gestational_day integer,
  requested_postpartum_week integer,
  requested_postpartum_day integer,
  requested_estimated_due_date date,
  requested_delivery_date date,
  requested_approximate_month_min integer,
  requested_approximate_month_max integer,
  requested_effective_date date,
  target_calculation_date date
)
returns table(position_min integer, position_max integer)
language plpgsql
immutable
security invoker
set search_path = pg_temp
as $$
declare
  elapsed_days integer;
  first_week integer;
  last_week integer;
begin
  if requested_stage = 'possible_pregnancy' then
    return query select null::integer, null::integer;
    return;
  end if;

  if target_calculation_date < requested_effective_date then
    raise exception 'calculation date precedes source effective date'
      using errcode = '22023';
  end if;

  if requested_timing_source in (
    'document_estimated_due_date', 'user_estimated_due_date'
  ) then
    position_min := 280 - (requested_estimated_due_date - target_calculation_date);
    position_max := position_min;
    return next;
    return;
  end if;

  elapsed_days := target_calculation_date - requested_effective_date;
  if requested_timing_source = 'manual_week_day' then
    position_min := requested_gestational_week * 7
      + requested_gestational_day + elapsed_days;
    position_max := position_min;
    return next;
    return;
  end if;

  if requested_timing_source = 'approximate_month_range' then
    first_week := case requested_approximate_month_min
      when 1 then 1 when 2 then 5 when 3 then 9 when 4 then 14
      when 5 then 18 when 6 then 23 when 7 then 28 when 8 then 32
      when 9 then 36 else null end;
    last_week := case requested_approximate_month_max
      when 1 then 4 when 2 then 8 when 3 then 13 when 4 then 17
      when 5 then 22 when 6 then 27 when 7 then 31 when 8 then 35
      when 9 then 42 else null end;
    if first_week is null or last_week is null then
      raise exception 'unsupported approximate pregnancy month'
        using errcode = '22023';
    end if;
    position_min := first_week * 7 + elapsed_days;
    position_max := last_week * 7 + 6 + elapsed_days;
    return next;
    return;
  end if;

  if requested_timing_source = 'delivery_date' then
    position_min := target_calculation_date - requested_delivery_date;
    position_max := position_min;
    return next;
    return;
  end if;

  if requested_timing_source = 'postpartum_week' then
    position_min := (requested_postpartum_week - 1) * 7
      + requested_postpartum_day + elapsed_days;
    position_max := position_min;
    return next;
    return;
  end if;

  raise exception 'unsupported journey timing source'
    using errcode = '22023';
end;
$$;

revoke all on function private.journey_state_position_bounds(
  text, text, integer, integer, integer, integer,
  date, date, integer, integer, date, date
) from public, anon, authenticated;

create or replace function private.validate_journey_state_transition()
returns trigger
language plpgsql
security definer
set search_path = public, private, pg_temp
as $$
declare
  prior_state public.journey_states;
  new_min integer;
  new_max integer;
  prior_min integer;
  prior_max integer;
  expected_conflict boolean := false;
  expected_difference integer;
begin
  select bounds.position_min, bounds.position_max
  into new_min, new_max
  from private.journey_state_position_bounds(
    new.stage, new.timing_source, new.gestational_week, new.gestational_day,
    new.postpartum_week, new.postpartum_day, new.estimated_due_date,
    new.delivery_date, new.approximate_month_min, new.approximate_month_max,
    new.effective_date, new.calculation_date
  ) bounds;

  if new.stage = 'pregnancy' and (
    new_min < 7 or new_max > 300
  ) then
    raise exception 'calculated pregnancy timing is outside supported weeks 1 through 42'
      using errcode = '22023';
  end if;
  if new.stage = 'postpartum' and (
    new_min < 0 or new_max > 83
  ) then
    raise exception 'calculated postpartum timing is outside supported weeks 1 through 12'
      using errcode = '22023';
  end if;

  select state.* into prior_state
  from public.journey_states state
  where state.workspace_id = new.workspace_id
    and state.version < new.version
  order by state.version desc
  limit 1;

  if prior_state.id is null then
    if new.version <> 1 then
      raise exception 'first journey state must use version 1'
        using errcode = '22023';
    end if;
    if new.has_dating_conflict
       or new.conflicts_with_state_id is not null
       or new.dating_difference_days is not null then
      raise exception 'first journey state cannot claim a timing conflict'
        using errcode = '22023';
    end if;
    return new;
  end if;

  if new.version <> prior_state.version + 1 then
    raise exception 'journey versions must be contiguous'
      using errcode = '22023';
  end if;
  if new.calculation_date < prior_state.calculation_date then
    raise exception 'journey calculation date cannot move backwards'
      using errcode = '22023';
  end if;
  if prior_state.stage = 'postpartum' and new.stage <> 'postpartum' then
    raise exception 'start a new workspace for a new pregnancy after postpartum'
      using errcode = '22023';
  end if;
  if prior_state.stage = 'pregnancy' and new.stage = 'possible_pregnancy' then
    raise exception 'confirmed pregnancy cannot move back to possible pregnancy'
      using errcode = '22023';
  end if;

  if prior_state.stage = new.stage and new.stage <> 'possible_pregnancy' then
    select bounds.position_min, bounds.position_max
    into prior_min, prior_max
    from private.journey_state_position_bounds(
      prior_state.stage, prior_state.timing_source,
      prior_state.gestational_week, prior_state.gestational_day,
      prior_state.postpartum_week, prior_state.postpartum_day,
      prior_state.estimated_due_date, prior_state.delivery_date,
      prior_state.approximate_month_min, prior_state.approximate_month_max,
      prior_state.effective_date, new.calculation_date
    ) bounds;

    if prior_min = prior_max and new_min = new_max then
      expected_difference := abs(prior_min - new_min);
      expected_conflict := expected_difference <> 0;
    elsif greatest(prior_min, new_min) <= least(prior_max, new_max) then
      expected_difference := 0;
    else
      expected_difference := greatest(prior_min, new_min)
        - least(prior_max, new_max);
      expected_conflict := true;
    end if;
  end if;

  if expected_conflict then
    if not new.has_dating_conflict
       or new.conflicts_with_state_id is distinct from prior_state.id
       or new.dating_difference_days is distinct from expected_difference then
      raise exception 'timing conflict provenance does not match the previous journey state'
        using errcode = '22023';
    end if;
  elsif new.has_dating_conflict
        or new.conflicts_with_state_id is not null
        or new.dating_difference_days is not null then
    raise exception 'non-conflicting transition cannot claim timing conflict provenance'
      using errcode = '22023';
  end if;

  return new;
end;
$$;

revoke all on function private.validate_journey_state_transition()
  from public, anon, authenticated;

drop trigger if exists journey_states_validate_transition
  on public.journey_states;
create trigger journey_states_validate_transition
before insert on public.journey_states
for each row execute function private.validate_journey_state_transition();

-- Migration 009 added confirmation provenance after this seed function was
-- originally defined. Keep future demo sessions valid under the new invariant.
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
    raise exception 'fictional demo workspace or seed version not found'
      using errcode = '22023';
  end if;
  if requested_seed_version <> 'maya-v1' then
    raise exception 'unsupported demo seed version' using errcode = '22023';
  end if;
  if exists (select 1 from public.journey_states where workspace_id = requested_workspace_id)
     or exists (select 1 from public.health_facts where workspace_id = requested_workspace_id)
     or exists (select 1 from public.appointments where workspace_id = requested_workspace_id) then
    raise exception 'demo workspace must be empty before seeding'
      using errcode = '55000';
  end if;

  insert into public.journey_states(
    workspace_id, stage, timing_source, gestational_week, gestational_day,
    user_confirmed, has_dating_conflict, is_current, version,
    effective_date, calculation_date, confirmed_at, confirmed_by_user_id
  ) values (
    requested_workspace_id, 'pregnancy', 'manual_week_day', 24, 2,
    true, false, true, 1,
    (clock_timestamp() at time zone 'Asia/Kolkata')::date,
    (clock_timestamp() at time zone 'Asia/Kolkata')::date,
    clock_timestamp(), auth.uid()
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
    clock_timestamp() + interval '14 days',
    'Routine antenatal follow-up',
    'Fictional clinic',
    'confirmed'
  );
end;
$$;

comment on function private.validate_journey_state_transition() is
  'Recomputes journey bounds and conflict provenance before each state insert.';
comment on constraint symptom_events_onboarding_safety_draft_check
  on public.symptom_events is
  'Onboarding symptom routing remains evaluation-only while the Stage 6 safety specification is a draft.';

commit;