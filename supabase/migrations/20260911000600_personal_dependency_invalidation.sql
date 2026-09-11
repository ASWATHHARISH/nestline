-- Stage 2 correction: normalize personal dependencies and invalidate derived
-- state transactionally when a confirmed fact or document disappears.

begin;

alter table public.appointment_questions
  drop constraint if exists appointment_questions_status_check;
alter table public.appointment_questions
  add column stale_reasons text[] not null default '{}',
  add constraint appointment_questions_status_check
    check (status in ('draft', 'saved', 'asked', 'stale', 'archived'));

-- These relationship tables are implementation details. The private schema is
-- not exposed to API roles, while composite foreign keys keep the workspace
-- boundary intact.
create table private.journey_state_fact_dependencies (
  workspace_id uuid not null,
  journey_state_id uuid not null,
  health_fact_id uuid not null,
  primary key (workspace_id, journey_state_id, health_fact_id),
  foreign key (workspace_id, journey_state_id)
    references public.journey_states(workspace_id, id) on delete cascade,
  foreign key (workspace_id, health_fact_id)
    references public.health_facts(workspace_id, id) on delete restrict
);

create table private.appointment_question_fact_dependencies (
  workspace_id uuid not null,
  appointment_question_id uuid not null,
  health_fact_id uuid not null,
  primary key (workspace_id, appointment_question_id, health_fact_id),
  foreign key (workspace_id, appointment_question_id)
    references public.appointment_questions(workspace_id, id) on delete cascade,
  foreign key (workspace_id, health_fact_id)
    references public.health_facts(workspace_id, id) on delete restrict
);

create table private.plan_item_fact_dependencies (
  workspace_id uuid not null,
  plan_item_id uuid not null,
  health_fact_id uuid not null,
  primary key (workspace_id, plan_item_id, health_fact_id),
  foreign key (workspace_id, plan_item_id)
    references public.plan_items(workspace_id, id) on delete cascade,
  foreign key (workspace_id, health_fact_id)
    references public.health_facts(workspace_id, id) on delete restrict
);

create table private.plan_item_guidance_dependencies (
  workspace_id uuid not null,
  plan_item_id uuid not null,
  release_id uuid not null,
  fragment_id text not null,
  primary key (workspace_id, plan_item_id, release_id, fragment_id),
  foreign key (workspace_id, plan_item_id)
    references public.plan_items(workspace_id, id) on delete cascade,
  foreign key (release_id, fragment_id)
    references public.guidance_fragments(release_id, fragment_id) on delete restrict
);

create table private.plan_item_evidence_dependencies (
  workspace_id uuid not null,
  plan_item_id uuid not null,
  release_id uuid not null,
  evidence_id text not null,
  primary key (workspace_id, plan_item_id, release_id, evidence_id),
  foreign key (workspace_id, plan_item_id)
    references public.plan_items(workspace_id, id) on delete cascade,
  foreign key (release_id, evidence_id)
    references public.guideline_chunks(release_id, evidence_id) on delete restrict
);

create or replace function private.append_unique_text(items text[], item text)
returns text[]
language sql
immutable
set search_path = pg_catalog, pg_temp
as $$
  select coalesce(array_agg(value order by value), '{}')
  from (select distinct unnest(coalesce(items, '{}') || array[item]) as value) values_to_keep;
$$;

create or replace function private.sync_journey_state_fact_dependencies()
returns trigger
language plpgsql
security definer
set search_path = public, private, pg_temp
as $$
begin
  if exists (
    select 1 from unnest(new.derived_from_fact_ids) fact_id
    where not exists (
      select 1 from public.health_facts fact
      where fact.workspace_id = new.workspace_id
        and fact.id = fact_id
        and fact.confirmation_status = 'confirmed'
        and fact.valid_to is null
    )
  ) then
    raise exception 'journey state contains an invalid or unconfirmed fact dependency'
      using errcode = '23503';
  end if;

  delete from private.journey_state_fact_dependencies dependency
  where dependency.workspace_id = new.workspace_id
    and dependency.journey_state_id = new.id;

  insert into private.journey_state_fact_dependencies(
    workspace_id, journey_state_id, health_fact_id
  )
  select new.workspace_id, new.id, fact_id
  from (select distinct unnest(new.derived_from_fact_ids) as fact_id) dependencies;
  return new;
end;
$$;

create or replace function private.sync_appointment_question_fact_dependencies()
returns trigger
language plpgsql
security definer
set search_path = public, private, pg_temp
as $$
begin
  if exists (
    select 1 from unnest(new.source_fact_ids) fact_id
    where not exists (
      select 1 from public.health_facts fact
      where fact.workspace_id = new.workspace_id
        and fact.id = fact_id
        and fact.confirmation_status = 'confirmed'
        and fact.valid_to is null
    )
  ) then
    raise exception 'appointment question contains an invalid or unconfirmed fact dependency'
      using errcode = '23503';
  end if;

  delete from private.appointment_question_fact_dependencies dependency
  where dependency.workspace_id = new.workspace_id
    and dependency.appointment_question_id = new.id;

  insert into private.appointment_question_fact_dependencies(
    workspace_id, appointment_question_id, health_fact_id
  )
  select new.workspace_id, new.id, fact_id
  from (select distinct unnest(new.source_fact_ids) as fact_id) dependencies;
  return new;
end;
$$;

create or replace function private.sync_plan_item_dependencies()
returns trigger
language plpgsql
security definer
set search_path = public, private, pg_temp
as $$
declare
  plan_release_id uuid;
begin
  select plan.source_release_id into plan_release_id
  from public.plans plan
  where plan.workspace_id = new.workspace_id and plan.id = new.plan_id;

  if plan_release_id is null then
    raise exception 'plan item has no workspace-scoped parent plan' using errcode = '23503';
  end if;
  if exists (
    select 1 from unnest(new.confirmed_fact_ids) fact_id
    where not exists (
      select 1 from public.health_facts fact
      where fact.workspace_id = new.workspace_id
        and fact.id = fact_id
        and fact.confirmation_status = 'confirmed'
        and fact.valid_to is null
    )
  ) then
    raise exception 'plan item contains an invalid or unconfirmed fact dependency'
      using errcode = '23503';
  end if;
  if exists (
    select 1 from unnest(new.guidance_fragment_ids) fragment_id
    where not exists (
      select 1 from public.guidance_fragments fragment
      where fragment.release_id = plan_release_id and fragment.fragment_id = fragment_id
    )
  ) then
    raise exception 'plan item contains an invalid guidance dependency' using errcode = '23503';
  end if;
  if exists (
    select 1 from unnest(new.evidence_ids) evidence_id
    where not exists (
      select 1 from public.guideline_chunks chunk
      where chunk.release_id = plan_release_id and chunk.evidence_id = evidence_id
    )
  ) then
    raise exception 'plan item contains an invalid evidence dependency' using errcode = '23503';
  end if;

  delete from private.plan_item_fact_dependencies dependency
  where dependency.workspace_id = new.workspace_id and dependency.plan_item_id = new.id;
  delete from private.plan_item_guidance_dependencies dependency
  where dependency.workspace_id = new.workspace_id and dependency.plan_item_id = new.id;
  delete from private.plan_item_evidence_dependencies dependency
  where dependency.workspace_id = new.workspace_id and dependency.plan_item_id = new.id;

  insert into private.plan_item_fact_dependencies(workspace_id, plan_item_id, health_fact_id)
  select new.workspace_id, new.id, fact_id
  from (select distinct unnest(new.confirmed_fact_ids) as fact_id) dependencies;
  insert into private.plan_item_guidance_dependencies(
    workspace_id, plan_item_id, release_id, fragment_id
  )
  select new.workspace_id, new.id, plan_release_id, fragment_id
  from (select distinct unnest(new.guidance_fragment_ids) as fragment_id) dependencies;
  insert into private.plan_item_evidence_dependencies(
    workspace_id, plan_item_id, release_id, evidence_id
  )
  select new.workspace_id, new.id, plan_release_id, evidence_id
  from (select distinct unnest(new.evidence_ids) as evidence_id) dependencies;
  return new;
end;
$$;

create trigger journey_states_sync_fact_dependencies
after insert or update of derived_from_fact_ids on public.journey_states
for each row execute function private.sync_journey_state_fact_dependencies();

create trigger appointment_questions_sync_fact_dependencies
after insert or update of source_fact_ids on public.appointment_questions
for each row execute function private.sync_appointment_question_fact_dependencies();

create trigger plan_items_sync_dependencies
after insert or update of confirmed_fact_ids, guidance_fragment_ids, evidence_ids
on public.plan_items
for each row execute function private.sync_plan_item_dependencies();

-- Reject an upgrade rather than accepting stale pre-existing array references.
do $$
begin
  if exists (
    select 1 from public.journey_states state
    cross join lateral unnest(state.derived_from_fact_ids) fact_id
    where not exists (
      select 1 from public.health_facts fact
      where fact.workspace_id = state.workspace_id and fact.id = fact_id
        and fact.confirmation_status = 'confirmed' and fact.valid_to is null
    )
  ) or exists (
    select 1 from public.appointment_questions question
    cross join lateral unnest(question.source_fact_ids) fact_id
    where not exists (
      select 1 from public.health_facts fact
      where fact.workspace_id = question.workspace_id and fact.id = fact_id
        and fact.confirmation_status = 'confirmed' and fact.valid_to is null
    )
  ) or exists (
    select 1 from public.plan_items item
    cross join lateral unnest(item.confirmed_fact_ids) fact_id
    where not exists (
      select 1 from public.health_facts fact
      where fact.workspace_id = item.workspace_id and fact.id = fact_id
        and fact.confirmation_status = 'confirmed' and fact.valid_to is null
    )
  ) then
    raise exception 'existing personal records contain invalid fact dependencies';
  end if;
end;
$$;

-- Populate the normalized map for a safe upgrade from the five deployed
-- migrations. Plan-item public dependencies are populated by re-running their
-- trigger after the fact maps are present.
update public.journey_states set derived_from_fact_ids = derived_from_fact_ids;
update public.appointment_questions set source_fact_ids = source_fact_ids;
update public.plan_items set confirmed_fact_ids = confirmed_fact_ids;

create or replace function private.invalidate_health_fact_dependents(
  requested_workspace_id uuid,
  requested_fact_id uuid,
  reason text
)
returns void
language plpgsql
volatile
security definer
set search_path = public, private, pg_temp
as $$
begin
  update public.plans plan
  set status = 'stale',
      stale_reasons = private.append_unique_text(plan.stale_reasons, reason)
  where plan.workspace_id = requested_workspace_id
    and exists (
      select 1
      from public.plan_items item
      join private.plan_item_fact_dependencies dependency
        on dependency.workspace_id = item.workspace_id
       and dependency.plan_item_id = item.id
      where item.workspace_id = plan.workspace_id
        and item.plan_id = plan.id
        and dependency.health_fact_id = requested_fact_id
    );

  update public.plan_items item
  set state = 'stale',
      confirmed_fact_ids = array_remove(item.confirmed_fact_ids, requested_fact_id)
  from private.plan_item_fact_dependencies dependency
  where dependency.workspace_id = requested_workspace_id
    and dependency.health_fact_id = requested_fact_id
    and item.workspace_id = dependency.workspace_id
    and item.id = dependency.plan_item_id;

  update public.appointment_questions question
  set status = 'stale',
      stale_reasons = private.append_unique_text(question.stale_reasons, reason),
      source_fact_ids = array_remove(question.source_fact_ids, requested_fact_id)
  from private.appointment_question_fact_dependencies dependency
  where dependency.workspace_id = requested_workspace_id
    and dependency.health_fact_id = requested_fact_id
    and question.workspace_id = dependency.workspace_id
    and question.id = dependency.appointment_question_id;

  update public.journey_states state
  set has_dating_conflict = true,
      user_confirmed = false,
      derived_from_fact_ids = array_remove(state.derived_from_fact_ids, requested_fact_id)
  from private.journey_state_fact_dependencies dependency
  where dependency.workspace_id = requested_workspace_id
    and dependency.health_fact_id = requested_fact_id
    and state.workspace_id = dependency.workspace_id
    and state.id = dependency.journey_state_id;

  delete from public.graph_nodes node
  where node.workspace_id = requested_workspace_id
    and node.entity_id = requested_fact_id
    and node.node_type in ('fact', 'restriction');
end;
$$;

create or replace function private.invalidate_deleted_health_fact()
returns trigger
language plpgsql
security definer
set search_path = public, private, pg_temp
as $$
begin
  perform private.invalidate_health_fact_dependents(
    old.workspace_id, old.id, 'health_fact_deleted:' || old.id::text
  );
  return old;
end;
$$;

create trigger health_facts_invalidate_before_delete
before delete on public.health_facts
for each row execute function private.invalidate_deleted_health_fact();

create or replace function private.invalidate_superseded_health_fact()
returns trigger
language plpgsql
security definer
set search_path = public, private, pg_temp
as $$
begin
  if new.supersedes_fact_id is not null then
    perform private.invalidate_health_fact_dependents(
      new.workspace_id,
      new.supersedes_fact_id,
      'health_fact_superseded:' || new.id::text
    );
  end if;
  if tg_op = 'UPDATE'
     and old.confirmation_status = 'confirmed'
     and old.valid_to is null
     and (new.confirmation_status <> 'confirmed' or new.valid_to is not null) then
    perform private.invalidate_health_fact_dependents(
      new.workspace_id, new.id, 'health_fact_no_longer_current:' || new.id::text
    );
  end if;
  return new;
end;
$$;

create trigger health_facts_invalidate_after_change
after insert or update of supersedes_fact_id, confirmation_status, valid_to
on public.health_facts
for each row execute function private.invalidate_superseded_health_fact();

create or replace function private.validate_graph_node_entity()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  entity_exists boolean := false;
begin
  case new.node_type
    when 'document' then
      select exists(select 1 from public.private_documents where workspace_id = new.workspace_id and id = new.entity_id) into entity_exists;
    when 'fact' then
      select exists(select 1 from public.document_facts where workspace_id = new.workspace_id and id = new.entity_id)
          or exists(select 1 from public.health_facts where workspace_id = new.workspace_id and id = new.entity_id) into entity_exists;
    when 'restriction' then
      select exists(select 1 from public.health_facts where workspace_id = new.workspace_id and id = new.entity_id) into entity_exists;
    when 'symptom' then
      select exists(select 1 from public.symptom_events where workspace_id = new.workspace_id and id = new.entity_id) into entity_exists;
    when 'appointment' then
      select exists(select 1 from public.appointments where workspace_id = new.workspace_id and id = new.entity_id) into entity_exists;
    when 'question' then
      select exists(select 1 from public.appointment_questions where workspace_id = new.workspace_id and id = new.entity_id) into entity_exists;
    when 'plan' then
      select exists(select 1 from public.plans where workspace_id = new.workspace_id and id = new.entity_id) into entity_exists;
    when 'plan_item' then
      select exists(select 1 from public.plan_items where workspace_id = new.workspace_id and id = new.entity_id) into entity_exists;
  end case;
  if not entity_exists then
    raise exception 'graph node entity does not exist in this workspace' using errcode = '23503';
  end if;
  return new;
end;
$$;

create trigger graph_nodes_validate_entity
before insert or update of workspace_id, node_type, entity_id on public.graph_nodes
for each row execute function private.validate_graph_node_entity();

create or replace function private.remove_graph_nodes_for_deleted_entity()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  delete from public.graph_nodes
  where workspace_id = old.workspace_id
    and entity_id = old.id
    and node_type = any(tg_argv);
  return old;
end;
$$;

create trigger document_facts_remove_graph_node after delete on public.document_facts
for each row execute function private.remove_graph_nodes_for_deleted_entity('fact');
create trigger symptom_events_remove_graph_node after delete on public.symptom_events
for each row execute function private.remove_graph_nodes_for_deleted_entity('symptom');
create trigger appointments_remove_graph_node after delete on public.appointments
for each row execute function private.remove_graph_nodes_for_deleted_entity('appointment');
create trigger appointment_questions_remove_graph_node after delete on public.appointment_questions
for each row execute function private.remove_graph_nodes_for_deleted_entity('question');
create trigger plans_remove_graph_node after delete on public.plans
for each row execute function private.remove_graph_nodes_for_deleted_entity('plan');
create trigger plan_items_remove_graph_node after delete on public.plan_items
for each row execute function private.remove_graph_nodes_for_deleted_entity('plan_item');

create or replace function private.remove_document_graph_nodes()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  delete from public.graph_nodes node
  where node.workspace_id = old.workspace_id
    and (
      node.source_document_id = old.id
      or (node.node_type = 'document' and node.entity_id = old.id)
      or (node.node_type = 'fact' and node.entity_id in (
        select fact.id from public.document_facts fact
        where fact.workspace_id = old.workspace_id and fact.document_id = old.id
      ))
    );
  return old;
end;
$$;

create trigger private_documents_remove_graph_nodes
before delete on public.private_documents
for each row execute function private.remove_document_graph_nodes();

create or replace function public.delete_private_document(
  requested_workspace_id uuid,
  requested_document_id uuid
)
returns text
language plpgsql
volatile
security invoker
set search_path = public, storage, pg_temp
as $$
declare
  deleted_path text;
begin
  if not private.is_workspace_member(requested_workspace_id) then
    raise exception 'workspace owner access required' using errcode = '42501';
  end if;
  if exists (
    select 1 from storage.objects object
    where object.bucket_id = 'medical-documents'
      and object.name = (
        select document.storage_object_path
        from public.private_documents document
        where document.workspace_id = requested_workspace_id
          and document.id = requested_document_id
      )
  ) then
    raise exception 'remove the document through the Storage API before deleting its database record'
      using errcode = '55000';
  end if;

  delete from public.private_documents document
  where document.workspace_id = requested_workspace_id
    and document.id = requested_document_id
  returning document.storage_object_path into deleted_path;

  if deleted_path is null then
    raise exception 'private document not found' using errcode = '22023';
  end if;
  return deleted_path;
end;
$$;

revoke all on function public.delete_private_document(uuid, uuid) from public, anon;
grant execute on function public.delete_private_document(uuid, uuid) to authenticated;

commit;
