-- Stage 2 correction: prevent API clients from bypassing Storage-first document
-- deletion by deleting private_documents rows directly.

begin;

drop policy if exists "workspace members manage private_documents" on public.private_documents;

create policy "owners read private document metadata" on public.private_documents
for select to authenticated
using (private.is_workspace_member(workspace_id));

create policy "owners create private document metadata" on public.private_documents
for insert to authenticated
with check (private.is_workspace_member(workspace_id));

create policy "owners update private document metadata" on public.private_documents
for update to authenticated
using (private.is_workspace_member(workspace_id))
with check (private.is_workspace_member(workspace_id));

revoke delete on public.private_documents from authenticated;

create or replace function public.delete_private_document(
  requested_workspace_id uuid,
  requested_document_id uuid
)
returns text
language plpgsql
volatile
security definer
set search_path = public, private, storage, pg_temp
as $$
declare
  deleted_path text;
begin
  if auth.uid() is null or not private.is_workspace_owner(requested_workspace_id) then
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

-- This function deletes the whole workspace state only after its existing
-- owner and empty-Storage checks pass. Definer rights are required because
-- authenticated users no longer have direct DELETE on private_documents.
alter function public.reset_demo_workspace_state(uuid, timestamptz) security definer;

revoke all on function public.delete_private_document(uuid, uuid) from public, anon;
grant execute on function public.delete_private_document(uuid, uuid) to authenticated;

comment on function public.delete_private_document(uuid, uuid) is
  'Owner-only metadata deletion after the matching Storage object has already been removed.';

commit;
