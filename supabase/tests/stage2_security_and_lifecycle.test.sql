begin;

create extension if not exists pgtap with schema extensions;
-- Pin the present suite size so accidental assertion deletion fails CI.
select plan(122);

-- Fixed UUIDs keep failures easy to reproduce while the surrounding
-- transaction guarantees that no test data survives.
insert into auth.users(id) values
  ('10000000-0000-0000-0000-000000000001'),
  ('20000000-0000-0000-0000-000000000002');

insert into public.workspaces(id, owner_user_id, mode, display_name) values
  ('11000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001', 'personal_empty', 'Owner fixture'),
  ('22000000-0000-0000-0000-000000000002', '20000000-0000-0000-0000-000000000002', 'personal_empty', 'Other fixture');

insert into public.content_releases(
  id, corpus_version, release_fingerprint, status, published_at
) values (
  '30000000-0000-0000-0000-000000000001', 'stage2-test-v1', repeat('a', 64),
  'published', now()
);
insert into public.public_sources(
  source_id, release_id, title, publisher, canonical_url, jurisdiction,
  source_version, reuse_status, allowed_use, status, content_checksum
) values (
  'SRC-STAGE2-TEST', '30000000-0000-0000-0000-000000000001',
  'Stage 2 test source', 'Nestline test suite', 'https://example.invalid/stage2',
  array['GLOBAL'], '1', 'permitted', array['testing'], 'published', repeat('b', 64)
);
insert into public.guideline_chunks(
  chunk_id, release_id, evidence_id, source_id, candidate_checksum, text,
  source_block_ids, stage, unit, range_start, range_end, jurisdiction,
  domains, display_slots, status
) values (
  'CHUNK-STAGE2-TEST', '30000000-0000-0000-0000-000000000001',
  'EVID-STAGE2-TEST', 'SRC-STAGE2-TEST', repeat('c', 64), 'Test evidence.',
  array['BLOCK-STAGE2-TEST'], 'pregnancy', 'week', 24, 24, array['GLOBAL'],
  array['nutrition'], array['plan'], 'published'
);
insert into public.guidance_fragments(
  fragment_id, release_id, domain, text, stage, unit, range_start, range_end,
  jurisdiction, evidence_ids, source_block_ids, presentation, status,
  content_checksum
) values (
  'GUIDANCE-STAGE2-TEST', '30000000-0000-0000-0000-000000000001',
  'nutrition', 'Test guidance.', 'pregnancy', 'week', 24, 24, array['GLOBAL'],
  array['EVID-STAGE2-TEST'], array['BLOCK-STAGE2-TEST'], 'paraphrase',
  'published', repeat('d', 64)
);

insert into public.health_facts(
  id, workspace_id, fact_type, value, source_kind, confirmation_status
) values (
  '41000000-0000-0000-0000-000000000001', '11000000-0000-0000-0000-000000000001',
  'allergy', '{"label":"Synthetic allergy"}', 'user_reported', 'confirmed'
);
insert into public.journey_states(
  id, workspace_id, stage, timing_source, gestational_week, gestational_day,
  user_confirmed, derived_from_fact_ids, confirmed_at, confirmed_by_user_id
) values (
  '42000000-0000-0000-0000-000000000001', '11000000-0000-0000-0000-000000000001',
  'pregnancy', 'manual_week_day', 24, 2, true,
  array['41000000-0000-0000-0000-000000000001'::uuid],
  clock_timestamp(), '10000000-0000-0000-0000-000000000001'
);
insert into public.private_documents(
  id, workspace_id, storage_object_path, original_filename, media_type,
  byte_size, sha256, status
) values
  ('43000000-0000-0000-0000-000000000001', '11000000-0000-0000-0000-000000000001',
   '11000000-0000-0000-0000-000000000001/report.pdf', 'report.pdf',
   'application/pdf', 12, repeat('e', 64), 'needs_confirmation'),
  ('43000000-0000-0000-0000-000000000002', '22000000-0000-0000-0000-000000000002',
   '22000000-0000-0000-0000-000000000002/report.pdf', 'report.pdf',
   'application/pdf', 12, repeat('f', 64), 'needs_confirmation'),
  ('43000000-0000-0000-0000-000000000003', '11000000-0000-0000-0000-000000000001',
   '11000000-0000-0000-0000-000000000001/without-object.pdf', 'without-object.pdf',
   'application/pdf', 12, repeat('8', 64), 'needs_confirmation');
insert into public.document_chunks(
  id, workspace_id, document_id, page, source_span, text, text_sha256,
  embedding_provider, embedding_model, embedding_dimensions, embedding
) values (
  '44000000-0000-0000-0000-000000000001', '11000000-0000-0000-0000-000000000001',
  '43000000-0000-0000-0000-000000000001', 1, '{"start":0,"end":12}',
  'Synthetic text', repeat('1', 64), 'test', 'test-3', 3, '[1,0,0]'::extensions.vector
), (
  '44000000-0000-0000-0000-000000000003', '11000000-0000-0000-0000-000000000001',
  '43000000-0000-0000-0000-000000000003', 1, '{"start":0,"end":12}',
  'Synthetic cascade text', repeat('7', 64), null, null, null, null
);
insert into public.document_facts(
  id, workspace_id, document_id, field_name, value, source_page, confidence, status
) values (
  '45000000-0000-0000-0000-000000000001', '11000000-0000-0000-0000-000000000001',
  '43000000-0000-0000-0000-000000000001', 'synthetic_field', '"value"', 1, 1, 'proposed'
);
insert into public.medication_mentions(
  id, workspace_id, document_id, name_as_written, status
) values (
  '46000000-0000-0000-0000-000000000001', '11000000-0000-0000-0000-000000000001',
  '43000000-0000-0000-0000-000000000001', 'Synthetic medicine', 'proposed'
);
insert into public.symptom_events(
  id, workspace_id, description, safety_route, user_confirmed
) values (
  '47000000-0000-0000-0000-000000000001', '11000000-0000-0000-0000-000000000001',
  'Synthetic symptom', 'no_match', true
);
insert into public.appointments(
  id, workspace_id, scheduled_for, appointment_type, status,
  source_fact_id
) values (
  '48000000-0000-0000-0000-000000000001', '11000000-0000-0000-0000-000000000001',
  now() + interval '7 days', 'Synthetic appointment', 'confirmed',
  '41000000-0000-0000-0000-000000000001'
);
insert into public.appointment_questions(
  id, workspace_id, appointment_id, question, source_fact_ids, status
) values (
  '49000000-0000-0000-0000-000000000001', '11000000-0000-0000-0000-000000000001',
  '48000000-0000-0000-0000-000000000001', 'Synthetic question?',
  array['41000000-0000-0000-0000-000000000001'::uuid], 'saved'
);
insert into public.plans(
  id, workspace_id, version, journey_state_id, source_release_id, status
) values (
  '50000000-0000-0000-0000-000000000001', '11000000-0000-0000-0000-000000000001',
  1, '42000000-0000-0000-0000-000000000001',
  '30000000-0000-0000-0000-000000000001', 'draft'
);
insert into public.plan_items(
  id, workspace_id, plan_id, guidance_fragment_ids, evidence_ids,
  confirmed_fact_ids, category, title, body, state, position
) values (
  '51000000-0000-0000-0000-000000000001', '11000000-0000-0000-0000-000000000001',
  '50000000-0000-0000-0000-000000000001', array['GUIDANCE-STAGE2-TEST'],
  array['EVID-STAGE2-TEST'], array['41000000-0000-0000-0000-000000000001'::uuid],
  'nutrition', 'Synthetic plan item', 'Synthetic body.', 'confirmed', 0
);
insert into public.graph_nodes(id, workspace_id, node_type, entity_id, label) values
  ('52000000-0000-0000-0000-000000000001', '11000000-0000-0000-0000-000000000001',
   'document', '43000000-0000-0000-0000-000000000001', 'Synthetic document'),
  ('52000000-0000-0000-0000-000000000002', '11000000-0000-0000-0000-000000000001',
   'fact', '41000000-0000-0000-0000-000000000001', 'Synthetic fact');
insert into public.graph_edges(
  id, workspace_id, from_node_id, to_node_id, relation
) values (
  '53000000-0000-0000-0000-000000000001', '11000000-0000-0000-0000-000000000001',
  '52000000-0000-0000-0000-000000000001', '52000000-0000-0000-0000-000000000002',
  'supports'
);
insert into public.human_review_cases(id, workspace_id, state, reason) values (
  '54000000-0000-0000-0000-000000000001', '11000000-0000-0000-0000-000000000001',
  'not_required', 'Synthetic fixture.'
);
insert into public.notifications(id, workspace_id, kind, status, idempotency_key) values (
  '55000000-0000-0000-0000-000000000001', '11000000-0000-0000-0000-000000000001',
  'synthetic', 'pending', 'stage2-fixture'
);
insert into public.feedback(id, workspace_id, rating, category, comment) values (
  '56000000-0000-0000-0000-000000000001', '11000000-0000-0000-0000-000000000001',
  5, 'synthetic', 'Synthetic fixture.'
);

create or replace function pg_temp.visible_workspace_rows(table_name text, target uuid)
returns bigint language plpgsql as $$
declare found_rows bigint;
begin
  execute format('select count(*) from public.%I where workspace_id = $1', table_name)
    into found_rows using target;
  return found_rows;
end;
$$;

create or replace function pg_temp.updated_workspace_rows(table_name text, target uuid)
returns bigint language plpgsql as $$
declare affected_rows bigint;
begin
  execute format(
    'update public.%I set workspace_id = workspace_id where workspace_id = $1',
    table_name
  ) using target;
  get diagnostics affected_rows = row_count;
  return affected_rows;
end;
$$;

create or replace function pg_temp.delete_is_allowed(table_name text, target uuid)
returns boolean language plpgsql as $$
declare affected_rows bigint := 0;
begin
  begin
    execute format('delete from public.%I where workspace_id = $1', table_name)
      using target;
    get diagnostics affected_rows = row_count;
    raise exception 'ROLLBACK_DELETE_PROBE' using errcode = 'P0001';
  exception
    when sqlstate 'P0001' then null;
    when others then return false;
  end;
  return affected_rows > 0;
end;
$$;

create or replace function pg_temp.sqlstate_of(command text)
returns text language plpgsql as $$
begin
  execute command;
  return null;
exception when others then
  return sqlstate;
end;
$$;

-- Policy catalogue check. Stage 4 makes extracted rows read-only to clients;
-- private_documents keeps policies for registration but protected columns have no grant.
select ok(
  case
    when table_name = 'journey_states' then commands = array['SELECT']
    when table_name = 'private_documents' then commands = array['INSERT', 'SELECT', 'UPDATE']
    when table_name = any(array['document_chunks', 'document_facts', 'medication_mentions', 'graph_nodes', 'graph_edges']) then commands = array['SELECT']
    when table_name = 'health_facts' then commands = array['DELETE', 'INSERT', 'SELECT', 'UPDATE']
    else commands = array['ALL']
  end,
  format('%s has its complete authenticated policy set', table_name)
)
from (
  select tablename as table_name, array_agg(cmd order by cmd) as commands
  from pg_policies
  where schemaname = 'public'
    and tablename = any(array[
      'journey_states', 'private_documents', 'document_chunks', 'document_facts',
      'health_facts', 'medication_mentions', 'symptom_events', 'appointments',
      'appointment_questions', 'plans', 'plan_items', 'graph_nodes', 'graph_edges',
      'human_review_cases', 'notifications', 'feedback'
    ])
    and 'authenticated' = any(roles)
  group by tablename
) policies;

select set_config('request.jwt.claim.sub', '10000000-0000-0000-0000-000000000001', true);
set local role authenticated;

select ok(
  pg_temp.visible_workspace_rows(table_name, '11000000-0000-0000-0000-000000000001') > 0,
  format('owner can read %s', table_name)
)
from unnest(array[
  'journey_states', 'private_documents', 'document_chunks', 'document_facts',
  'health_facts', 'medication_mentions', 'symptom_events', 'appointments',
  'appointment_questions', 'plans', 'plan_items',
  'human_review_cases', 'notifications', 'feedback'
]) table_name;
select is((select count(*) from public.graph_nodes
           where workspace_id = '11000000-0000-0000-0000-000000000001'),
          2::bigint, 'owner can read governed graph nodes');
select is((select count(*) from public.graph_edges
           where workspace_id = '11000000-0000-0000-0000-000000000001'),
          1::bigint, 'owner can read governed graph edges');

select ok(
  pg_temp.updated_workspace_rows(table_name, '11000000-0000-0000-0000-000000000001') > 0,
  format('owner can update %s', table_name)
)
from unnest(array[
  'health_facts', 'symptom_events', 'appointments',
  'appointment_questions', 'plans', 'plan_items',
  'human_review_cases', 'notifications', 'feedback'
]) table_name;

select ok(
  pg_temp.delete_is_allowed(table_name, '11000000-0000-0000-0000-000000000001'),
  format('owner can delete %s through its table policy', table_name)
)
from unnest(array[
  'health_facts', 'symptom_events', 'appointments', 'appointment_questions',
  'plans', 'plan_items', 'human_review_cases',
  'notifications', 'feedback'
]) table_name;

select is(
  pg_temp.sqlstate_of($command$
    delete from public.journey_states
    where id = '42000000-0000-0000-0000-000000000001'
  $command$),
  '42501',
  'owner journey deletion is denied outside the confirmed state committer'
);

select is(
  pg_temp.sqlstate_of($command$
    delete from public.private_documents
    where id = '43000000-0000-0000-0000-000000000001'
  $command$),
  '42501',
  'direct private document metadata deletion is denied'
);

select is(
  (select count(*) from public.match_document_chunks(
    '11000000-0000-0000-0000-000000000001', '[1,0,0]'::extensions.vector, 6
  )),
  1::bigint,
  'owner can retrieve an embedded private chunk'
);

select is(
  pg_temp.sqlstate_of($command$
    insert into public.document_chunks(
      workspace_id, document_id, source_span, text, text_sha256
    ) values (
      '11000000-0000-0000-0000-000000000001',
      '43000000-0000-0000-0000-000000000002', '{}', 'Cross workspace',
      repeat('9', 64)
    )
  $command$),
  '42501',
  'direct derived chunk insertion is rejected before any cross-workspace reference'
);

select is(
  pg_temp.sqlstate_of($command$
    insert into public.health_facts(
      workspace_id, fact_type, value, source_kind, confirmation_status
    ) values (
      '22000000-0000-0000-0000-000000000002', 'other', '{}',
      'user_reported', 'confirmed'
    )
  $command$),
  '42501',
  'owner cannot insert into another workspace'
);

select is(
  pg_temp.sqlstate_of($command$
    insert into public.journey_states(
      workspace_id, stage, timing_source, gestational_week
    ) values (
      '11000000-0000-0000-0000-000000000001',
      'possible_pregnancy', 'manual_week_day', 4
    )
  $command$),
  '42501',
  'direct journey inserts are denied outside the confirmed state committer'
);

reset role;
select set_config('request.jwt.claim.sub', '20000000-0000-0000-0000-000000000002', true);
set local role authenticated;

select is(
  pg_temp.visible_workspace_rows(table_name, '11000000-0000-0000-0000-000000000001'),
  0::bigint,
  format('other user cannot read %s', table_name)
)
from unnest(array[
  'journey_states', 'private_documents', 'document_chunks', 'document_facts',
  'health_facts', 'medication_mentions', 'symptom_events', 'appointments',
  'appointment_questions', 'plans', 'plan_items',
  'human_review_cases', 'notifications', 'feedback'
]) table_name;
select is((select count(*) from public.graph_nodes
           where workspace_id = '11000000-0000-0000-0000-000000000001'),
          0::bigint, 'other user cannot read governed graph nodes');
select is((select count(*) from public.graph_edges
           where workspace_id = '11000000-0000-0000-0000-000000000001'),
          0::bigint, 'other user cannot read governed graph edges');

select is(
  pg_temp.updated_workspace_rows(table_name, '11000000-0000-0000-0000-000000000001'),
  0::bigint,
  format('other user cannot update %s', table_name)
)
from unnest(array[
  'health_facts', 'symptom_events', 'appointments',
  'appointment_questions', 'plans', 'plan_items',
  'human_review_cases', 'notifications', 'feedback'
]) table_name;

select ok(
  not pg_temp.delete_is_allowed(table_name, '11000000-0000-0000-0000-000000000001'),
  format('other user cannot delete %s', table_name)
)
from unnest(array[
  'journey_states', 'private_documents', 'document_chunks', 'document_facts',
  'health_facts', 'medication_mentions', 'symptom_events', 'appointments',
  'appointment_questions', 'plans', 'plan_items',
  'human_review_cases', 'notifications', 'feedback'
]) table_name;

select is(
  (select count(*) from public.match_document_chunks(
    '11000000-0000-0000-0000-000000000001', '[1,0,0]'::extensions.vector, 6
  )),
  0::bigint,
  'other user cannot retrieve private vectors'
);

reset role;
select is(
  pg_temp.sqlstate_of($command$
    insert into public.workspace_members(workspace_id, user_id, role)
    values (
      '11000000-0000-0000-0000-000000000001',
      '20000000-0000-0000-0000-000000000002', 'editor'
    )
  $command$),
  '23514',
  'non-owner workspace roles are rejected by the database'
);

-- Deleting a current confirmed health fact invalidates every saved dependent
-- and removes its graph node in the same transaction.
select set_config('request.jwt.claim.sub', '10000000-0000-0000-0000-000000000001', true);
set local role authenticated;
delete from public.health_facts
where id = '41000000-0000-0000-0000-000000000001';
select is((select status from public.plans where id = '50000000-0000-0000-0000-000000000001'),
          'stale', 'fact deletion makes the plan stale');
select is((select state from public.plan_items where id = '51000000-0000-0000-0000-000000000001'),
          'stale', 'fact deletion makes the plan item stale');
select is((select status from public.appointment_questions where id = '49000000-0000-0000-0000-000000000001'),
          'stale', 'fact deletion makes the appointment question stale');
select ok((select has_dating_conflict and not user_confirmed from public.journey_states
           where id = '42000000-0000-0000-0000-000000000001'),
          'fact deletion forces journey reconfirmation');
select is((select count(*) from public.graph_nodes
           where entity_id = '41000000-0000-0000-0000-000000000001'),
          0::bigint, 'fact deletion removes its graph node');

-- Storage policies are tested against the same owner and outsider identities.
select is(
  pg_temp.sqlstate_of($command$
    insert into storage.objects(bucket_id, name, owner_id)
    values (
      'medical-documents',
      '11000000-0000-0000-0000-000000000001/report.pdf',
      '10000000-0000-0000-0000-000000000001'
    )
  $command$),
  null,
  'owner can create Storage metadata under the exact workspace prefix'
);
select is((select count(*) from storage.objects
           where bucket_id = 'medical-documents'
             and name = '11000000-0000-0000-0000-000000000001/report.pdf'),
          1::bigint, 'owner can list private Storage metadata');
select is(
  pg_temp.sqlstate_of($command$
    select public.delete_private_document(
      '11000000-0000-0000-0000-000000000001',
      '43000000-0000-0000-0000-000000000001'
    )
  $command$),
  '55000',
  'database document deletion is blocked while Storage metadata exists'
);

reset role;
select set_config('request.jwt.claim.sub', '20000000-0000-0000-0000-000000000002', true);
set local role authenticated;
select is((select count(*) from storage.objects
           where bucket_id = 'medical-documents'
             and name = '11000000-0000-0000-0000-000000000001/report.pdf'),
          0::bigint, 'other user cannot list owner Storage metadata');
select is(
  pg_temp.sqlstate_of($command$
    insert into storage.objects(bucket_id, name, owner_id)
    values (
      'medical-documents',
      '11000000-0000-0000-0000-000000000001/other.pdf',
      '20000000-0000-0000-0000-000000000002'
    )
  $command$),
  '42501',
  'other user cannot upload under the owner Storage prefix'
);

reset role;
select set_config('request.jwt.claim.sub', '10000000-0000-0000-0000-000000000001', true);
set local role authenticated;
select is(
  pg_temp.sqlstate_of($command$
    delete from storage.objects
    where bucket_id = 'medical-documents'
      and name = '11000000-0000-0000-0000-000000000001/report.pdf'
  $command$),
  '42501',
  'authenticated direct SQL Storage deletion is denied'
);
select is(
  public.delete_private_document(
    '11000000-0000-0000-0000-000000000001',
    '43000000-0000-0000-0000-000000000003'
  ),
  '11000000-0000-0000-0000-000000000001/without-object.pdf',
  'owner can delete document metadata when no Storage object remains'
);
select is((select count(*) from public.document_chunks
           where document_id = '43000000-0000-0000-0000-000000000003'),
          0::bigint, 'document deletion cascades to derived chunks');

-- Each browser/demo session gets a distinct, versioned fictional workspace.
create temporary table demo_fixture(id uuid, updated_at timestamptz);
insert into demo_fixture(id)
select public.create_demo_workspace('stage2-session-one', 'Maya fixture', 'maya-v1');
update demo_fixture fixture set updated_at = workspace.updated_at
from public.workspaces workspace where workspace.id = fixture.id;
select is(public.create_demo_workspace('stage2-session-one', 'Maya fixture', 'maya-v1'),
          (select id from demo_fixture), 'same session key returns the same demo workspace');
select isnt(public.create_demo_workspace('stage2-session-two', 'Maya fixture', 'maya-v1'),
            (select id from demo_fixture), 'a second session receives a separate demo workspace');

select is((select count(*) from public.journey_states where workspace_id = (select id from demo_fixture)),
          1::bigint, 'demo seed has one journey state');
select is((select count(*) from public.health_facts where workspace_id = (select id from demo_fixture)),
          3::bigint, 'demo seed has three fictional health facts');
select is((select count(*) from public.appointments where workspace_id = (select id from demo_fixture)),
          1::bigint, 'demo seed has one appointment');

select ok(public.reseed_demo_workspace_state(
            (select id from demo_fixture), (select updated_at from demo_fixture), 'maya-v1') is not null,
          'first reset and reseed succeeds');
select ok(public.reseed_demo_workspace_state(
            (select id from demo_fixture), (select updated_at from demo_fixture), 'maya-v1') is not null,
          'second reset and reseed succeeds');
select ok(public.reseed_demo_workspace_state(
            (select id from demo_fixture), (select updated_at from demo_fixture), 'maya-v1') is not null,
          'third reset and reseed succeeds');
select is((select count(*) from public.journey_states where workspace_id = (select id from demo_fixture)),
          1::bigint, 'three resets still leave one journey state');
select is((select count(*) from public.health_facts where workspace_id = (select id from demo_fixture)),
          3::bigint, 'three resets still leave three health facts');
select is((select count(*) from public.appointments where workspace_id = (select id from demo_fixture)),
          1::bigint, 'three resets still leave one appointment');
select is((select display_name from public.workspaces
           where id = '22000000-0000-0000-0000-000000000002'),
          null, 'demo reset cannot reveal another owner workspace');

reset role;
select * from finish();
rollback;
