-- Prove the exact Stage 4 state survives the additive Stage 5 migration.
do $$
begin
  if not exists (
    select 1 from public.workspaces
    where id = '62000000-0000-4000-8000-000000000001'
  ) then
    raise exception 'Stage 5 upgrade did not preserve the workspace';
  end if;

  if not exists (
    select 1 from public.personal_retrieval_versions
    where workspace_id = '62000000-0000-4000-8000-000000000001'
      and version >= 1
  ) then
    raise exception 'Stage 5 upgrade did not backfill the personal cache version';
  end if;

  if not exists (
    select 1 from public.guideline_chunks
    where release_id = '63000000-0000-4000-8000-000000000001'
      and chunk_id = 'S5-UPGRADE-CHUNK'
      and search_vector @@ websearch_to_tsquery(
        'english', 'protein terminology'
      )
  ) then
    raise exception 'Stage 5 upgrade did not backfill public full-text search';
  end if;

  if not exists (
    select 1 from public.document_chunks
    where id = '65000000-0000-4000-8000-000000000001'
      and search_vector @@ websearch_to_tsquery(
        'english', 'confirmed allergy'
      )
  ) then
    raise exception 'Stage 5 upgrade did not backfill personal full-text search';
  end if;

  if not exists (
    select 1 from public.graph_nodes
    where id = '66000000-0000-4000-8000-000000000001'
      and entity_id = '64000000-0000-4000-8000-000000000001'
      and entity_release_id is null
      and entity_key is null
  ) then
    raise exception 'Stage 5 upgrade changed a Stage 4 graph entity reference';
  end if;
end;
$$;

delete from public.graph_nodes
where workspace_id = '62000000-0000-4000-8000-000000000001';
delete from public.document_chunks
where workspace_id = '62000000-0000-4000-8000-000000000001';
delete from public.private_documents
where workspace_id = '62000000-0000-4000-8000-000000000001';
delete from public.personal_retrieval_versions
where workspace_id = '62000000-0000-4000-8000-000000000001';
delete from public.workspaces
where id = '62000000-0000-4000-8000-000000000001';
delete from public.guideline_chunks
where release_id = '63000000-0000-4000-8000-000000000001';
delete from public.public_sources
where release_id = '63000000-0000-4000-8000-000000000001';
delete from public.content_releases
where id = '63000000-0000-4000-8000-000000000001';
delete from auth.users
where id = '61000000-0000-4000-8000-000000000001';

do $$
begin
  if exists (
    select 1 from public.workspaces
    where id = '62000000-0000-4000-8000-000000000001'
  ) or exists (
    select 1 from public.content_releases
    where id = '63000000-0000-4000-8000-000000000001'
  ) then
    raise exception 'Stage 5 upgrade fixture cleanup left temporary rows';
  end if;
end;
$$;
