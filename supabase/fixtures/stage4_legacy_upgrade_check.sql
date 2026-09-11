-- Fails the exact-upgrade job unless Stage 4 backfilled all legacy provenance.
do $$
begin
  if not exists (
    select 1 from public.private_documents
    where id = 'b2000000-0000-0000-0000-000000000001'
      and review_version = 1
      and confirmed_at is not null
      and confirmed_by_user_id = 'b0000000-0000-0000-0000-000000000001'
  ) then
    raise exception 'Stage 4 did not backfill legacy document confirmation provenance';
  end if;
  if not exists (
    select 1 from public.document_facts
    where id = 'b3000000-0000-0000-0000-000000000001'
      and decided_at is not null
      and decided_by_user_id = 'b0000000-0000-0000-0000-000000000001'
  ) then
    raise exception 'Stage 4 did not backfill legacy document-fact decision provenance';
  end if;
  if not exists (
    select 1 from public.medication_mentions
    where id = 'b4000000-0000-0000-0000-000000000001'
      and decided_at is not null
      and decided_by_user_id = 'b0000000-0000-0000-0000-000000000001'
  ) then
    raise exception 'Stage 4 did not backfill legacy medication decision provenance';
  end if;
end;
$$;

delete from public.workspaces where id = 'b1000000-0000-0000-0000-000000000001';
delete from auth.users where id = 'b0000000-0000-0000-0000-000000000001';
