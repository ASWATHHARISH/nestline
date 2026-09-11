begin;

create extension if not exists pgtap with schema extensions;
select plan(26);

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
  ('13000000-0000-0000-0000-000000000001'),
  ('23000000-0000-0000-0000-000000000002');
insert into public.workspaces(id, owner_user_id, mode, display_name) values
  ('13000000-0000-0000-0000-000000000011', '13000000-0000-0000-0000-000000000001', 'personal_empty', 'Stage 3 owner fixture'),
  ('23000000-0000-0000-0000-000000000022', '23000000-0000-0000-0000-000000000002', 'personal_empty', 'Stage 3 other fixture');

create temporary table stage3_request as
select
  jsonb_build_object(
    'stage', 'pregnancy',
    'timing_source', 'manual_week_day',
    'gestational_week', 24,
    'gestational_day', 2,
    'postpartum_week', null,
    'postpartum_day', null,
    'estimated_due_date', null,
    'delivery_date', null,
    'approximate_month_min', null,
    'approximate_month_max', null,
    'effective_date', current_date::text,
    'calculation_date', current_date::text,
    'derived_from_fact_ids', '[]'::jsonb
  ) as journey,
  jsonb_build_array(
    jsonb_build_object('fact_type', 'allergy', 'value', jsonb_build_object('label', 'Fictional allergy')),
    jsonb_build_object('fact_type', 'other', 'value', jsonb_build_object('label', 'Fictional restriction', 'category', 'movement_restriction'))
  ) as facts,
  jsonb_build_array(
    jsonb_build_object(
      'description', 'Fictional breathing difficulty',
      'reported_at', (clock_timestamp() - interval '1 minute')::text,
      'safety_route', 'urgent',
      'matched_rule_ids', jsonb_build_array('S-BREATHING'),
      'safety_spec_version', '1.0.0',
      'safety_evaluation_only', true
    )
  ) as symptoms,
  jsonb_build_array(
    jsonb_build_object(
      'scheduled_for', (clock_timestamp() + interval '7 days')::text,
      'appointment_type', 'Fictional follow-up',
      'location', 'Fictional clinic'
    )
  ) as appointments;
grant select on stage3_request to authenticated;

select extensions.has_function(
  'public', 'complete_onboarding',
  array['uuid','integer','text','text','jsonb','boolean','uuid','integer','jsonb','jsonb','jsonb'],
  'atomic onboarding function exists'
);
select extensions.has_column('public', 'journey_states', 'effective_date',
  'journey state preserves source effective date');
select extensions.has_column('public', 'journey_states', 'calculation_date',
  'journey state preserves calculation date');
select extensions.has_column('public', 'journey_states', 'confirmed_at',
  'journey state preserves user confirmation time');
select extensions.has_column('public', 'symptom_events', 'safety_spec_version',
  'symptom event preserves safety-rule provenance');

select set_config('request.jwt.claim.sub', '13000000-0000-0000-0000-000000000001', true);
set local role authenticated;
select is(pg_temp.sqlstate_of($command$
  update public.journey_states
  set gestational_week = 25
  where workspace_id = '13000000-0000-0000-0000-000000000011'
$command$), '42501', 'direct journey updates are denied outside the confirmed committer');
select is(pg_temp.sqlstate_of($command$
  select public.replace_current_journey_state(
    '13000000-0000-0000-0000-000000000011', 0,
    'pregnancy', 'manual_week_day', 24, 2
  )
$command$), '42501', 'superseded journey mutation function cannot be called');
create temporary table stage3_first_result as
select public.complete_onboarding(
  '13000000-0000-0000-0000-000000000011', 0,
  'stage3-pgtap-submission-0001', repeat('a', 64),
  request.journey, false, null, null,
  request.facts, request.symptoms, request.appointments
) as result
from stage3_request request;
reset role;

select is((select (result->>'version')::integer from stage3_first_result), 1,
  'first confirmed onboarding commit creates journey version 1');
select is((select count(*) from public.journey_states
           where workspace_id = '13000000-0000-0000-0000-000000000011' and is_current),
          1::bigint, 'one current journey state exists');
select ok((select user_confirmed and confirmed_at is not null and confirmed_by_user_id =
                  '13000000-0000-0000-0000-000000000001'
           from public.journey_states
           where workspace_id = '13000000-0000-0000-0000-000000000011' and is_current),
          'current journey records explicit authenticated confirmation');
select is((select count(*) from public.health_facts
           where workspace_id = '13000000-0000-0000-0000-000000000011'),
          2::bigint, 'reported facts commit in the same transaction');
select is((select count(*) from public.symptom_events
           where workspace_id = '13000000-0000-0000-0000-000000000011'),
          1::bigint, 'timestamped symptom commits in the same transaction');
select ok((select safety_route = 'urgent'
                  and matched_rule_ids = array['S-BREATHING']
                  and safety_spec_version = '1.0.0'
                  and safety_evaluation_only
           from public.symptom_events
           where workspace_id = '13000000-0000-0000-0000-000000000011'),
          'symptom preserves its draft safety handoff metadata');
select is((select count(*) from public.appointments
           where workspace_id = '13000000-0000-0000-0000-000000000011'),
          1::bigint, 'next appointment commits in the same transaction');

set local role authenticated;
select ok((
  select (public.complete_onboarding(
    '13000000-0000-0000-0000-000000000011', 0,
    'stage3-pgtap-submission-0001', repeat('a', 64),
    request.journey, false, null, null,
    request.facts, request.symptoms, request.appointments
  )->>'idempotent_replay')::boolean
  from stage3_request request
), 'same submission key and checksum returns an idempotent replay');
reset role;
select ok(
  (select count(*) from public.journey_states where workspace_id = '13000000-0000-0000-0000-000000000011') = 1
  and (select count(*) from public.health_facts where workspace_id = '13000000-0000-0000-0000-000000000011') = 2
  and (select count(*) from public.symptom_events where workspace_id = '13000000-0000-0000-0000-000000000011') = 1
  and (select count(*) from public.appointments where workspace_id = '13000000-0000-0000-0000-000000000011') = 1,
  'idempotent replay creates no duplicate rows'
);

set local role authenticated;
select is(pg_temp.sqlstate_of($command$
  select public.complete_onboarding(
    '13000000-0000-0000-0000-000000000011', 0,
    'stage3-pgtap-submission-0001', repeat('b', 64),
    request.journey, false, null, null,
    request.facts, request.symptoms, request.appointments
  ) from stage3_request request
$command$), '23505', 'reused submission key with different data is rejected');
select is(pg_temp.sqlstate_of($command$
  select public.complete_onboarding(
    '13000000-0000-0000-0000-000000000011', 0,
    'stage3-pgtap-submission-0002', repeat('b', 64),
    request.journey, false, null, null,
    request.facts, request.symptoms, request.appointments
  ) from stage3_request request
$command$), '40001', 'stale journey version is rejected');
select is(pg_temp.sqlstate_of($command$
  select public.complete_onboarding(
    '13000000-0000-0000-0000-000000000011', 1,
    'stage3-pgtap-submission-0003', repeat('c', 64),
    request.journey || jsonb_build_object('calculation_date', (current_date + 1)::text),
    false, null, null, '[]'::jsonb, '[]'::jsonb, '[]'::jsonb
  ) from stage3_request request
$command$), '22023', 'future calculation date is rejected');
select is(pg_temp.sqlstate_of($command$
  select public.complete_onboarding(
    '13000000-0000-0000-0000-000000000011', 1,
    'stage3-pgtap-submission-0004', repeat('d', 64),
    request.journey || jsonb_build_object('estimated_due_date', (current_date + 100)::text),
    false, null, null, '[]'::jsonb, '[]'::jsonb, '[]'::jsonb
  ) from stage3_request request
$command$), '23514', 'extraneous journey fields are rejected atomically');
reset role;

select set_config('request.jwt.claim.sub', '23000000-0000-0000-0000-000000000002', true);
set local role authenticated;
select is((select count(*) from public.journey_states
           where workspace_id = '13000000-0000-0000-0000-000000000011'),
          0::bigint, 'another user cannot read the owner journey');
select is(pg_temp.sqlstate_of($command$
  select public.complete_onboarding(
    '13000000-0000-0000-0000-000000000011', 1,
    'stage3-pgtap-submission-0005', repeat('e', 64),
    request.journey, false, null, null,
    request.facts, request.symptoms, request.appointments
  ) from stage3_request request
$command$), '42501', 'another user cannot commit owner onboarding data');
reset role;

select set_config('request.jwt.claim.sub', '13000000-0000-0000-0000-000000000001', true);
set local role authenticated;
create temporary table stage3_conflict_result as
select public.complete_onboarding(
  '13000000-0000-0000-0000-000000000011', 1,
  'stage3-pgtap-submission-0006', repeat('f', 64),
  request.journey || jsonb_build_object('gestational_week', 25),
  true,
  (select (result->>'journey_state_id')::uuid from stage3_first_result),
  7,
  '[]'::jsonb, '[]'::jsonb, '[]'::jsonb
) as result
from stage3_request request;
reset role;

select is((select (result->>'version')::integer from stage3_conflict_result), 2,
  'explicitly accepted conflicting timing creates version 2');
select is((select count(*) from public.journey_states
           where workspace_id = '13000000-0000-0000-0000-000000000011'),
          2::bigint, 'both timing versions remain auditable');
select is((select version from public.journey_states
           where workspace_id = '13000000-0000-0000-0000-000000000011' and is_current),
          2, 'accepted proposal becomes the one current version');
select ok((select has_dating_conflict
                  and conflicts_with_state_id =
                    (select (result->>'journey_state_id')::uuid from stage3_first_result)
                  and dating_difference_days = 7
           from public.journey_states
           where workspace_id = '13000000-0000-0000-0000-000000000011' and is_current),
          'accepted conflict preserves the compared version and difference');

select * from extensions.finish();
rollback;