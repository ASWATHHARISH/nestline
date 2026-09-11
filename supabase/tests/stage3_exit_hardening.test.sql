begin;

create extension if not exists pgtap with schema extensions;
select plan(12);

create or replace function pg_temp.sqlstate_of(command text)
returns text
language plpgsql
as $$
begin
  execute command;
  return 'NO_ERROR';
exception when others then
  return sqlstate;
end;
$$;

insert into auth.users(id) values
  ('14000000-0000-0000-0000-000000000001');
insert into public.workspaces(id, owner_user_id, mode, display_name) values
  ('14000000-0000-0000-0000-000000000011', '14000000-0000-0000-0000-000000000001', 'personal_empty', 'Stage 3 EDD hardening fixture'),
  ('14000000-0000-0000-0000-000000000012', '14000000-0000-0000-0000-000000000001', 'personal_empty', 'Stage 3 transition hardening fixture'),
  ('14000000-0000-0000-0000-000000000013', '14000000-0000-0000-0000-000000000001', 'personal_empty', 'Stage 3 delivery hardening fixture');

create temporary table stage3_hardening_requests as
select
  jsonb_build_object(
    'stage', 'pregnancy', 'timing_source', 'manual_week_day',
    'gestational_week', 24, 'gestational_day', 2,
    'postpartum_week', null, 'postpartum_day', null,
    'estimated_due_date', null, 'delivery_date', null,
    'approximate_month_min', null, 'approximate_month_max', null,
    'effective_date', current_date::text,
    'calculation_date', current_date::text,
    'derived_from_fact_ids', '[]'::jsonb
  ) as manual,
  jsonb_build_object(
    'stage', 'pregnancy', 'timing_source', 'user_estimated_due_date',
    'gestational_week', 20, 'gestational_day', 0,
    'postpartum_week', null, 'postpartum_day', null,
    'estimated_due_date', (current_date + 100)::text,
    'delivery_date', null,
    'approximate_month_min', null, 'approximate_month_max', null,
    'effective_date', current_date::text,
    'calculation_date', current_date::text,
    'derived_from_fact_ids', '[]'::jsonb
  ) as bad_edd,
  jsonb_build_object(
    'stage', 'postpartum', 'timing_source', 'delivery_date',
    'gestational_week', null, 'gestational_day', null,
    'postpartum_week', 2, 'postpartum_day', 0,
    'estimated_due_date', null,
    'delivery_date', (current_date - 8)::text,
    'approximate_month_min', null, 'approximate_month_max', null,
    'effective_date', (current_date - 8)::text,
    'calculation_date', current_date::text,
    'derived_from_fact_ids', '[]'::jsonb
  ) as bad_delivery,
  jsonb_build_object(
    'stage', 'possible_pregnancy',
    'timing_source', 'user_reported_possible_pregnancy',
    'gestational_week', null, 'gestational_day', null,
    'postpartum_week', null, 'postpartum_day', null,
    'estimated_due_date', null, 'delivery_date', null,
    'approximate_month_min', null, 'approximate_month_max', null,
    'effective_date', current_date::text,
    'calculation_date', current_date::text,
    'derived_from_fact_ids', '[]'::jsonb
  ) as possible;
grant select on stage3_hardening_requests to authenticated;

select is((
  select count(*) from pg_trigger
  where tgrelid = 'public.journey_states'::regclass
    and tgname = 'journey_states_validate_transition'
    and not tgisinternal
), 1::bigint, 'journey transition hardening trigger exists');

select is((
  select count(*) from pg_constraint
  where conrelid in (
    'public.journey_states'::regclass,
    'public.symptom_events'::regclass
  ) and conname in (
    'journey_states_edd_arithmetic_check',
    'journey_states_delivery_arithmetic_check',
    'journey_states_confirmation_provenance_check',
    'symptom_events_onboarding_safety_draft_check'
  )
), 4::bigint, 'all Stage 3 exit constraints exist');

select set_config('request.jwt.claim.sub', '14000000-0000-0000-0000-000000000001', true);
set local role authenticated;
select is(pg_temp.sqlstate_of($command$
  select public.complete_onboarding(
    '14000000-0000-0000-0000-000000000011', 0,
    'stage3-hardening-edd-0001', repeat('1', 64), request.bad_edd,
    false, null, null, '[]'::jsonb, '[]'::jsonb, '[]'::jsonb
  ) from stage3_hardening_requests request
$command$), '23514', 'tampered due-date arithmetic is rejected');
reset role;
select is((select count(*) from public.journey_states
  where workspace_id = '14000000-0000-0000-0000-000000000011'),
  0::bigint, 'failed due-date commit leaves no journey state');

set local role authenticated;
select is(pg_temp.sqlstate_of($command$
  select public.complete_onboarding(
    '14000000-0000-0000-0000-000000000013', 0,
    'stage3-hardening-delivery-0001', repeat('2', 64), request.bad_delivery,
    false, null, null, '[]'::jsonb, '[]'::jsonb, '[]'::jsonb
  ) from stage3_hardening_requests request
$command$), '23514', 'tampered delivery-date arithmetic is rejected');

create temporary table stage3_hardening_first as
select public.complete_onboarding(
  '14000000-0000-0000-0000-000000000012', 0,
  'stage3-hardening-base-0001', repeat('3', 64), request.manual,
  false, null, null, '[]'::jsonb, '[]'::jsonb, '[]'::jsonb
) as result
from stage3_hardening_requests request;

select is(pg_temp.sqlstate_of($command$
  select public.complete_onboarding(
    '14000000-0000-0000-0000-000000000012', 1,
    'stage3-hardening-conflict-0001', repeat('4', 64),
    request.manual || jsonb_build_object('gestational_week', 25),
    false, null, null, '[]'::jsonb, '[]'::jsonb, '[]'::jsonb
  ) from stage3_hardening_requests request
$command$), '22023', 'a crafted request cannot omit a real timing conflict');
reset role;
select ok((select count(*) = 1 and max(version) = 1
  from public.journey_states
  where workspace_id = '14000000-0000-0000-0000-000000000012'),
  'rejected conflict omission leaves version 1 intact');

set local role authenticated;
select is(pg_temp.sqlstate_of($command$
  select public.complete_onboarding(
    '14000000-0000-0000-0000-000000000012', 1,
    'stage3-hardening-safety-0001', repeat('5', 64), request.manual,
    false, null, null, '[]'::jsonb,
    jsonb_build_array(jsonb_build_object(
      'description', 'Fictional symptom',
      'reported_at', (clock_timestamp() - interval '1 minute')::text,
      'safety_route', 'clarify', 'matched_rule_ids', '[]'::jsonb,
      'safety_spec_version', '1.0.0', 'safety_evaluation_only', false
    )), '[]'::jsonb
  ) from stage3_hardening_requests request
$command$), '23514', 'onboarding cannot remove the draft-safety label');
reset role;
select ok(
  (select count(*) = 1 and bool_and(is_current) and max(version) = 1
   from public.journey_states
   where workspace_id = '14000000-0000-0000-0000-000000000012')
  and
  (select count(*) = 0 from public.symptom_events
   where workspace_id = '14000000-0000-0000-0000-000000000012'),
  'failed safety write rolls back the whole onboarding transaction');

set local role authenticated;
select is(pg_temp.sqlstate_of($command$
  select public.complete_onboarding(
    '14000000-0000-0000-0000-000000000012', 1,
    'stage3-hardening-regression-0001', repeat('6', 64), request.possible,
    false, null, null, '[]'::jsonb, '[]'::jsonb, '[]'::jsonb
  ) from stage3_hardening_requests request
$command$), '22023', 'confirmed pregnancy cannot regress to possible pregnancy');
select is(pg_temp.sqlstate_of($command$
  select * from private.journey_state_position_bounds(
    'pregnancy', 'manual_week_day', 24, 2, null, null,
    null, null, null, null, current_date, current_date
  )
$command$), '42501', 'authenticated callers cannot execute the private bounds helper');
reset role;

select is((select count(*) from public.journey_states
  where workspace_id = '14000000-0000-0000-0000-000000000012'),
  1::bigint, 'all rejected transitions leave the confirmed state unchanged');

select * from extensions.finish();
rollback;