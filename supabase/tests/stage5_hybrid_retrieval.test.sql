begin;

create extension if not exists pgtap with schema extensions;
select plan(48);

insert into auth.users(id) values
  ('51000000-0000-4000-8000-000000000001'),
  ('51000000-0000-4000-8000-000000000002');
insert into public.workspaces(id, owner_user_id, mode, display_name) values
  ('52000000-0000-4000-8000-000000000001', '51000000-0000-4000-8000-000000000001', 'fictional_demo', 'Maya Stage 5 fixture'),
  ('52000000-0000-4000-8000-000000000002', '51000000-0000-4000-8000-000000000002', 'fictional_demo', 'Other Stage 5 fixture');

insert into public.content_releases(id, corpus_version, release_fingerprint, status, published_at) values
  ('53000000-0000-4000-8000-000000000001', 'stage5-fixture-v1', repeat('1', 64), 'published', clock_timestamp()),
  ('53000000-0000-4000-8000-000000000002', 'stage5-other-v1', repeat('2', 64), 'published', clock_timestamp()),
  ('53000000-0000-4000-8000-000000000003', 'stage5-draft-v1', repeat('3', 64), 'draft', null);
insert into public.public_sources(
  source_id, release_id, title, publisher, canonical_url, jurisdiction,
  source_version, reuse_status, allowed_use, status, content_checksum
) values
  ('S5-GOOD', '53000000-0000-4000-8000-000000000001', 'Synthetic approved source', 'Nestline tests', 'https://example.invalid/s5-good', array['IN'], '1', 'permitted', array['store','embed','display'], 'published', repeat('4',64)),
  ('S5-US', '53000000-0000-4000-8000-000000000001', 'Synthetic US source', 'Nestline tests', 'https://example.invalid/s5-us', array['US'], '1', 'permitted', array['store','embed','display'], 'published', repeat('5',64)),
  ('S5-NOEMBED', '53000000-0000-4000-8000-000000000001', 'Synthetic display source', 'Nestline tests', 'https://example.invalid/s5-noembed', array['IN'], '1', 'permitted', array['store','display'], 'published', repeat('6',64)),
  ('S5-REVIEWED', '53000000-0000-4000-8000-000000000001', 'Synthetic reviewed source', 'Nestline tests', 'https://example.invalid/s5-reviewed', array['IN'], '1', 'permitted', array['store','embed','display'], 'reviewed', repeat('7',64)),
  ('S5-OTHER', '53000000-0000-4000-8000-000000000002', 'Synthetic other corpus', 'Nestline tests', 'https://example.invalid/s5-other', array['IN'], '1', 'permitted', array['store','embed','display'], 'published', repeat('8',64)),
  ('S5-DRAFT', '53000000-0000-4000-8000-000000000003', 'Synthetic draft release source', 'Nestline tests', 'https://example.invalid/s5-draft', array['IN'], '1', 'permitted', array['store','embed','display'], 'published', repeat('9',64));

insert into public.guideline_chunks(
  chunk_id, release_id, evidence_id, source_id, candidate_checksum, text,
  source_block_ids, stage, unit, range_start, range_end, jurisdiction,
  domains, display_slots, conditions_required, embedding_provider,
  embedding_model, embedding_dimensions, embedding, status
) values
  ('S5-CHUNK-GOOD','53000000-0000-4000-8000-000000000001','S5-EV-GOOD','S5-GOOD',repeat('a',64),'week 24 protein foods synthetic guidance',array['S5-BLOCK-GOOD'],'pregnancy','week',24,24,array['IN'],array['nutrition'],array['plan'],'{}','TEST_ONLY','sha256-test-vector-v1',3,'[1,0,0]','published'),
  ('S5-CHUNK-WRONG-WEEK','53000000-0000-4000-8000-000000000001','S5-EV-WRONG-WEEK','S5-GOOD',repeat('b',64),'week 12 protein foods decoy',array['S5-BLOCK-W12'],'pregnancy','week',12,12,array['IN'],array['nutrition'],array['plan'],'{}','TEST_ONLY','sha256-test-vector-v1',3,'[1,0,0]','published'),
  ('S5-CHUNK-US','53000000-0000-4000-8000-000000000001','S5-EV-US','S5-US',repeat('c',64),'week 24 protein foods US decoy',array['S5-BLOCK-US'],'pregnancy','week',24,24,array['US'],array['nutrition'],array['plan'],'{}','TEST_ONLY','sha256-test-vector-v1',3,'[1,0,0]','published'),
  ('S5-CHUNK-NOEMBED','53000000-0000-4000-8000-000000000001','S5-EV-NOEMBED','S5-NOEMBED',repeat('d',64),'week 24 protein foods display only',array['S5-BLOCK-NO'],'pregnancy','week',24,24,array['IN'],array['nutrition'],array['plan'],'{}','TEST_ONLY','sha256-test-vector-v1',3,'[1,0,0]','published'),
  ('S5-CHUNK-REVIEWED','53000000-0000-4000-8000-000000000001','S5-EV-REVIEWED','S5-REVIEWED',repeat('e',64),'week 24 protein foods reviewed decoy',array['S5-BLOCK-REV'],'pregnancy','week',24,24,array['IN'],array['nutrition'],array['plan'],'{}','TEST_ONLY','sha256-test-vector-v1',3,'[1,0,0]','published'),
  ('S5-CHUNK-CONDITION','53000000-0000-4000-8000-000000000001','S5-EV-CONDITION','S5-GOOD',repeat('f',64),'week 24 protein foods condition decoy',array['S5-BLOCK-COND'],'pregnancy','week',24,24,array['IN'],array['nutrition'],array['plan'],array['movement_restriction'],'TEST_ONLY','sha256-test-vector-v1',3,'[1,0,0]','published'),
  ('S5-CHUNK-OTHER','53000000-0000-4000-8000-000000000002','S5-EV-OTHER','S5-OTHER',repeat('0',64),'week 24 protein foods other corpus',array['S5-BLOCK-OTHER'],'pregnancy','week',24,24,array['IN'],array['nutrition'],array['plan'],'{}','TEST_ONLY','sha256-test-vector-v1',3,'[1,0,0]','published'),
  ('S5-CHUNK-DRAFT','53000000-0000-4000-8000-000000000003','S5-EV-DRAFT','S5-DRAFT',repeat('1',64),'week 24 protein foods draft release',array['S5-BLOCK-DRAFT'],'pregnancy','week',24,24,array['IN'],array['nutrition'],array['plan'],'{}','TEST_ONLY','sha256-test-vector-v1',3,'[1,0,0]','published'),
  ('S5-CHUNK-RETIRED','53000000-0000-4000-8000-000000000001','S5-EV-RETIRED','S5-GOOD',repeat('2',64),'week 24 protein foods retired chunk',array['S5-BLOCK-RET'],'pregnancy','week',24,24,array['IN'],array['nutrition'],array['plan'],'{}','TEST_ONLY','sha256-test-vector-v1',3,'[1,0,0]','retired');

insert into public.journey_states(
  id, workspace_id, stage, timing_source, gestational_week, gestational_day,
  user_confirmed, version, confirmed_at, confirmed_by_user_id,
  effective_date, calculation_date
) values
  ('54000000-0000-4000-8000-000000000001','52000000-0000-4000-8000-000000000001','pregnancy','manual_week_day',24,2,true,1,clock_timestamp(),'51000000-0000-4000-8000-000000000001',current_date,current_date);

insert into public.private_documents(
  id, workspace_id, storage_object_path, original_filename, media_type,
  byte_size, sha256, status, fixture_document_key, scan_status, scan_provider,
  scan_version, scan_completed_at, review_version, confirmed_at,
  confirmed_by_user_id, has_unresolved_conflicts
) values
  ('55000000-0000-4000-8000-000000000001','52000000-0000-4000-8000-000000000001','52000000-0000-4000-8000-000000000001/a/DOC-091.pdf','DOC-091.pdf','application/pdf',100,repeat('3',64),'confirmed','DOC-091','fixture_verified','pgtap','1',clock_timestamp(),1,clock_timestamp(),'51000000-0000-4000-8000-000000000001',false),
  ('55000000-0000-4000-8000-000000000002','52000000-0000-4000-8000-000000000002','52000000-0000-4000-8000-000000000002/b/DOC-092.pdf','DOC-092.pdf','application/pdf',100,repeat('4',64),'confirmed','DOC-092','fixture_verified','pgtap','1',clock_timestamp(),1,clock_timestamp(),'51000000-0000-4000-8000-000000000002',false),
  ('55000000-0000-4000-8000-000000000003','52000000-0000-4000-8000-000000000001','52000000-0000-4000-8000-000000000001/c/DOC-093.pdf','DOC-093.pdf','application/pdf',100,repeat('5',64),'needs_confirmation','DOC-093','fixture_verified','pgtap','1',clock_timestamp(),1,null,null,false),
  ('55000000-0000-4000-8000-000000000004','52000000-0000-4000-8000-000000000001','52000000-0000-4000-8000-000000000001/d/DOC-094.pdf','DOC-094.pdf','application/pdf',100,repeat('6',64),'confirmed','DOC-094','fixture_verified','pgtap','1',clock_timestamp(),1,clock_timestamp(),'51000000-0000-4000-8000-000000000001',true);

insert into public.document_chunks(
  id, workspace_id, document_id, page, source_span, text, text_sha256,
  embedding_provider, embedding_model, embedding_dimensions, embedding
) values
  ('56000000-0000-4000-8000-000000000001','52000000-0000-4000-8000-000000000001','55000000-0000-4000-8000-000000000001',1,'{"locator":"page/1","start_char":0,"end_char":39}','confirmed fictional peanut allergy record',repeat('7',64),'TEST_ONLY','sha256-test-vector-v1',3,'[1,0,0]'),
  ('56000000-0000-4000-8000-000000000002','52000000-0000-4000-8000-000000000002','55000000-0000-4000-8000-000000000002',1,'{"locator":"page/1"}','other workspace private record',repeat('8',64),'TEST_ONLY','sha256-test-vector-v1',3,'[1,0,0]'),
  ('56000000-0000-4000-8000-000000000003','52000000-0000-4000-8000-000000000001','55000000-0000-4000-8000-000000000003',1,'{"locator":"page/1"}','unconfirmed document passage decoy',repeat('9',64),'TEST_ONLY','sha256-test-vector-v1',3,'[1,0,0]'),
  ('56000000-0000-4000-8000-000000000004','52000000-0000-4000-8000-000000000001','55000000-0000-4000-8000-000000000004',1,'{"locator":"page/1"}','conflicted document passage decoy',repeat('a',64),'TEST_ONLY','sha256-test-vector-v1',3,'[1,0,0]');

insert into public.health_facts(id, workspace_id, fact_type, value, source_kind, confirmation_status, valid_to, record_only) values
  ('57000000-0000-4000-8000-000000000001','52000000-0000-4000-8000-000000000001','allergy','{"substance":"peanut","fictional":true}','human_reviewed','confirmed',null,false),
  ('57000000-0000-4000-8000-000000000002','52000000-0000-4000-8000-000000000001','medical_history','{"fictional":"proposal"}','user_reported','proposed',null,false),
  ('57000000-0000-4000-8000-000000000003','52000000-0000-4000-8000-000000000001','medical_history','{"fictional":"conflict"}','human_reviewed','conflict',null,false),
  ('57000000-0000-4000-8000-000000000004','52000000-0000-4000-8000-000000000001','allergy','{"fictional":"old"}','human_reviewed','superseded',clock_timestamp(),false);

insert into public.medication_mentions(id, workspace_id, name_as_written, context_text, status, decided_at, decided_by_user_id) values
  ('58000000-0000-4000-8000-000000000001','52000000-0000-4000-8000-000000000001','Fictional supplement','record only','confirmed',clock_timestamp(),'51000000-0000-4000-8000-000000000001');
insert into public.symptom_events(id, workspace_id, description, safety_route, user_confirmed, safety_evaluation_only) values
  ('59000000-0000-4000-8000-000000000001','52000000-0000-4000-8000-000000000001','fictional symptom','no_match',true,true);
insert into public.appointments(id, workspace_id, scheduled_date, appointment_type, status) values
  ('5a000000-0000-4000-8000-000000000001','52000000-0000-4000-8000-000000000001',current_date + 7,'fictional check-up','confirmed');

insert into public.plans(id, workspace_id, version, journey_state_id, source_release_id, status) values
  ('5b000000-0000-4000-8000-000000000001','52000000-0000-4000-8000-000000000001',1,'54000000-0000-4000-8000-000000000001','53000000-0000-4000-8000-000000000001','stale');
insert into public.plan_items(id, workspace_id, plan_id, evidence_ids, category, title, body, state, position) values
  ('5c000000-0000-4000-8000-000000000001','52000000-0000-4000-8000-000000000001','5b000000-0000-4000-8000-000000000001',array['S5-EV-GOOD'],'movement','Stale movement item','fictional body','stale',0);
insert into public.appointment_questions(id, workspace_id, appointment_id, question, source_fact_ids, status) values
  ('5d000000-0000-4000-8000-000000000001','52000000-0000-4000-8000-000000000001','5a000000-0000-4000-8000-000000000001','Clarify fictional conflict','{}'::uuid[],'saved');

insert into public.graph_nodes(id, workspace_id, node_type, entity_id, label, source_document_id) values
  ('5e000000-0000-4000-8000-000000000001','52000000-0000-4000-8000-000000000001','document','55000000-0000-4000-8000-000000000001','Maya fictional document','55000000-0000-4000-8000-000000000001'),
  ('5e000000-0000-4000-8000-000000000002','52000000-0000-4000-8000-000000000001','restriction','57000000-0000-4000-8000-000000000001','Confirmed fictional restriction','55000000-0000-4000-8000-000000000001'),
  ('5e000000-0000-4000-8000-000000000003','52000000-0000-4000-8000-000000000001','plan_item','5c000000-0000-4000-8000-000000000001','Stale movement plan item',null),
  ('5e000000-0000-4000-8000-000000000004','52000000-0000-4000-8000-000000000001','plan','5b000000-0000-4000-8000-000000000001','Stale movement plan',null),
  ('5e000000-0000-4000-8000-000000000006','52000000-0000-4000-8000-000000000002','document','55000000-0000-4000-8000-000000000002','Other fictional document','55000000-0000-4000-8000-000000000002');
insert into public.graph_nodes(
  id, workspace_id, node_type, entity_id, entity_release_id, entity_key, label
) values (
  '5e000000-0000-4000-8000-000000000005',
  '52000000-0000-4000-8000-000000000001','guideline_evidence',null,
  '53000000-0000-4000-8000-000000000001','S5-EV-GOOD',
  'Architecture vocabulary fixture'
);
insert into public.graph_edges(id, workspace_id, from_node_id, to_node_id, relation) values
  ('5f000000-0000-4000-8000-000000000001','52000000-0000-4000-8000-000000000001','5e000000-0000-4000-8000-000000000001','5e000000-0000-4000-8000-000000000002','EXTRACTED_FROM'),
  ('5f000000-0000-4000-8000-000000000002','52000000-0000-4000-8000-000000000001','5e000000-0000-4000-8000-000000000002','5e000000-0000-4000-8000-000000000003','CONSTRAINS'),
  ('5f000000-0000-4000-8000-000000000003','52000000-0000-4000-8000-000000000001','5e000000-0000-4000-8000-000000000003','5e000000-0000-4000-8000-000000000004','TRIGGERED'),
  ('5f000000-0000-4000-8000-000000000004','52000000-0000-4000-8000-000000000001','5e000000-0000-4000-8000-000000000004','5e000000-0000-4000-8000-000000000001','supports');

create or replace function pg_temp.sqlstate_of(command text)
returns text language plpgsql as $$
begin
  execute command;
  return null;
exception when others then
  return sqlstate;
end;
$$;

select ok(to_regclass('public.personal_retrieval_versions') is not null,
  'personal retrieval version table exists');
select ok(exists(select 1 from information_schema.columns where table_schema='public' and table_name='guideline_chunks' and column_name='search_vector'),
  'public chunks have a generated full-text column');
select ok(exists(select 1 from information_schema.columns where table_schema='public' and table_name='document_chunks' and column_name='search_vector'),
  'private chunks have a generated full-text column');
select ok(to_regclass('public.guideline_chunks_search_idx') is not null,
  'public full-text GIN index exists');
select ok(to_regclass('public.document_chunks_search_idx') is not null,
  'private full-text GIN index exists');
select ok(exists(select 1 from public.graph_nodes where node_type='guideline_evidence'),
  'additive graph vocabulary accepts an architecture node type');

select ok(not has_function_privilege('anon','public.stage5_authenticated_scope(uuid)','EXECUTE'),
  'anonymous users cannot derive personal retrieval scope');
select ok(has_function_privilege('authenticated','public.stage5_authenticated_scope(uuid)','EXECUTE'),
  'authenticated users may derive their owner scope');
select ok(not has_function_privilege('anon','public.stage5_public_full_text(text,text,text,integer,integer,text,text,text[],text[],text,uuid,integer)','EXECUTE'),
  'anonymous users cannot bypass the authenticated gateway through Stage 5 full text');
select ok(has_function_privilege('authenticated','public.match_document_chunks(uuid,extensions.vector,integer)','EXECUTE'),
  'authenticated callers retain the hardened confirmed-document compatibility RPC');
select ok(has_function_privilege('anon','public.match_guideline_chunks(extensions.vector,text,text,integer,text[],integer)','EXECUTE'),
  'anonymous callers retain only the hardened published-evidence compatibility RPC');
select is((select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname like 'stage5_%' and p.provolatile <> 's'),0::bigint,
  'all Stage 5 public retrieval functions are declared stable reads');

select set_config('request.jwt.claim.sub','51000000-0000-4000-8000-000000000001',true);
set local role authenticated;

select ok(public.stage5_authenticated_scope('52000000-0000-4000-8000-000000000001') is not null,
  'owner derives scope for own workspace');
select is(public.stage5_authenticated_scope('52000000-0000-4000-8000-000000000002'),null::jsonb,
  'owner cannot derive another workspace scope');
select is(public.stage5_authenticated_scope('52000000-0000-4000-8000-000000000001')->>'owner_user_id','51000000-0000-4000-8000-000000000001',
  'scope owner comes from the authenticated database record');
select ok((public.stage5_authenticated_scope('52000000-0000-4000-8000-000000000001')->>'state_version')::bigint > 1,
  'scope carries a monotonic relevant-state version');

select is(jsonb_array_length(public.stage5_exact_personal_context('52000000-0000-4000-8000-000000000001')->'confirmed_facts'),1,
  'exact SQL returns only one active confirmed fact');
select is(public.stage5_exact_personal_context('52000000-0000-4000-8000-000000000001')->'confirmed_facts'->0->>'fact_type','allergy',
  'exact SQL retrieves the confirmed allergy without vector guessing');
select is(jsonb_array_length(public.stage5_exact_personal_context('52000000-0000-4000-8000-000000000001')->'unresolved_conflicts'),1,
  'unresolved conflict is returned separately');
select is(public.stage5_exact_personal_context('52000000-0000-4000-8000-000000000001')->'medications'->0->>'record_only','true',
  'medication is explicitly record-only');
select is(public.stage5_exact_personal_context('52000000-0000-4000-8000-000000000001')->'symptoms'->0->>'safety_evaluation_only','true',
  'symptom remains safety-evaluation-only');
select is(jsonb_array_length(public.stage5_exact_personal_context('52000000-0000-4000-8000-000000000001')->'appointments'),1,
  'exact SQL returns the confirmed appointment');
select is(jsonb_array_length(public.stage5_exact_personal_context('52000000-0000-4000-8000-000000000001')->'open_questions'),1,
  'exact SQL returns the open clarification question');
select is(public.stage5_exact_personal_context('52000000-0000-4000-8000-000000000002'),null::jsonb,
  'exact SQL cannot read another workspace');

create temporary table s5_text_results as
select * from public.stage5_public_full_text(
  'protein foods','pregnancy','week',24,24,'IN','nutrition','{}',array['guideline'],
  'stage5-fixture-v1','53000000-0000-4000-8000-000000000001',20);
select ok(exists(select 1 from s5_text_results where candidate->>'evidence_id'='S5-EV-GOOD'),
  'full text retrieves expected approved evidence');
select ok(not exists(select 1 from s5_text_results where candidate->>'evidence_id'='S5-EV-WRONG-WEEK'),
  'full text excludes wrong-week evidence before ranking');
select ok(not exists(select 1 from s5_text_results where candidate->>'evidence_id'='S5-EV-US'),
  'full text excludes wrong-jurisdiction evidence before ranking');
select ok(not exists(select 1 from s5_text_results where candidate->>'evidence_id' in ('S5-EV-REVIEWED','S5-EV-DRAFT','S5-EV-RETIRED')),
  'full text excludes unapproved, draft, and retired evidence');
select ok(not exists(select 1 from s5_text_results where candidate->>'evidence_id'='S5-EV-CONDITION'),
  'full text excludes an unmet applicability condition');
select is((select count(*) from public.stage5_public_full_text(
  'protein foods','pregnancy','week',24,24,'IN','nutrition','{}',array['weekly_profile'],
  'stage5-fixture-v1','53000000-0000-4000-8000-000000000001',20)),0::bigint,
  'wrong evidence lane returns no guideline candidate');
select ok(not exists(select 1 from s5_text_results where candidate->>'evidence_id'='S5-EV-OTHER'),
  'a different published corpus and release is excluded');
select ok((select candidate->'spans'->0->>'text_sha256' from s5_text_results where candidate->>'evidence_id'='S5-EV-GOOD') ~ '^[a-f0-9]{64}$',
  'public evidence carries an exact traceable span checksum');

create temporary table s5_vector_results as
select * from public.stage5_public_vector(
  '[1,0,0]'::extensions.vector,'pregnancy','week',24,24,'IN','nutrition','{}',array['guideline'],
  'stage5-fixture-v1','53000000-0000-4000-8000-000000000001',20);
select ok(exists(select 1 from s5_vector_results where candidate->>'evidence_id'='S5-EV-GOOD'),
  'pgvector retrieves expected approved evidence');
select ok(not exists(select 1 from s5_vector_results where candidate->>'evidence_id'='S5-EV-NOEMBED'),
  'pgvector excludes sources without embedding permission');
select ok(not exists(select 1 from s5_vector_results where candidate->>'evidence_id' in ('S5-EV-WRONG-WEEK','S5-EV-US','S5-EV-OTHER')),
  'pgvector applies week, jurisdiction, corpus, and release filters before ranking');

create temporary table s5_personal_text as
select * from public.stage5_personal_full_text(
  '52000000-0000-4000-8000-000000000001','peanut allergy',20);
select is((select count(*) from s5_personal_text),1::bigint,
  'personal full text returns only the confirmed conflict-free owner passage');
select is((select count(*) from public.stage5_personal_full_text(
  '52000000-0000-4000-8000-000000000002','private record',20)),0::bigint,
  'personal full text cannot cross workspaces');
select ok(not exists(select 1 from s5_personal_text where candidate->>'document_id' in (
  '55000000-0000-4000-8000-000000000003','55000000-0000-4000-8000-000000000004')),
  'unconfirmed and unresolved-conflict documents are excluded before ranking');
select is((select count(*) from public.stage5_personal_vector(
  '52000000-0000-4000-8000-000000000001','[1,0,0]'::extensions.vector,20)),1::bigint,
  'personal pgvector returns only the confirmed owner passage');
select is((select count(*) from public.stage5_personal_vector(
  '52000000-0000-4000-8000-000000000002','[1,0,0]'::extensions.vector,20)),0::bigint,
  'personal pgvector cannot cross workspaces');
select is(public.stage5_weekly_profile(
  'pregnancy','week',24,24,'IN','nutrition','{}',array['weekly_profile'],
  'stage5-fixture-v1','53000000-0000-4000-8000-000000000001'),null::jsonb,
  'no published weekly profile produces an explicit null result');

create temporary table s5_graph_results(path jsonb);
insert into s5_graph_results
select * from public.stage5_graph_paths(
  '52000000-0000-4000-8000-000000000001','stale movement plan',100,100);
select is((select count(*) from s5_graph_results),1::bigint,
  'bounded graph returns the complete relevant causal path once');
select is((select string_agg(node->>'node_type',',' order by ordinal)
  from s5_graph_results cross join lateral jsonb_array_elements(path->'nodes') with ordinality as item(node,ordinal)),
  'document,restriction,plan_item,plan',
  'graph preserves document to restriction to affected item to stale plan types');
select ok((select max((path->>'depth')::integer) from s5_graph_results) <= 4,
  'graph clamps excessive requested depth to four');
select ok(not exists(
  select 1 from s5_graph_results result
  where jsonb_array_length(result.path->'nodes') <>
    (select count(distinct node->>'node_id')
     from jsonb_array_elements(result.path->'nodes') node)),
  'graph cycle protection prevents repeated nodes');
select is((select count(*) from public.stage5_graph_paths(
  '52000000-0000-4000-8000-000000000002','other document',4,8)),0::bigint,
  'graph traversal cannot cross into another workspace');
select ok(pg_temp.sqlstate_of($sql$
  update public.personal_retrieval_versions
  set version = version + 1
  where workspace_id = '52000000-0000-4000-8000-000000000001'
$sql$) is not null,
  'ordinary authenticated retrieval cannot mutate cache versions');

reset role;
create temporary table s5_version_before(value bigint);
insert into s5_version_before
select version from public.personal_retrieval_versions
where workspace_id='52000000-0000-4000-8000-000000000001';
insert into public.health_facts(
  id, workspace_id, fact_type, value, source_kind, confirmation_status
) values (
  '57000000-0000-4000-8000-000000000005',
  '52000000-0000-4000-8000-000000000001',
  'other','{"fictional":"cache invalidation"}','user_reported','confirmed'
);
select ok((select version from public.personal_retrieval_versions
  where workspace_id='52000000-0000-4000-8000-000000000001') >
  (select value from s5_version_before),
  'relevant confirmed state writes invalidate the personal cache version');

select * from finish();
rollback;




