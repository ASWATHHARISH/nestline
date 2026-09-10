-- Keep the trigger-created owner membership immutable through the client API.
-- Workspace deletion remains the only supported way to remove an owner row.

begin;

drop policy if exists "owners manage membership" on public.workspace_members;

create policy "owners add non-owner members" on public.workspace_members
for insert to authenticated
with check (
  private.is_workspace_owner(workspace_id)
  and role <> 'owner'
);

create policy "owners update non-owner members" on public.workspace_members
for update to authenticated
using (
  private.is_workspace_owner(workspace_id)
  and role <> 'owner'
)
with check (
  private.is_workspace_owner(workspace_id)
  and role <> 'owner'
);

create policy "owners remove non-owner members" on public.workspace_members
for delete to authenticated
using (
  private.is_workspace_owner(workspace_id)
  and role <> 'owner'
);

commit;
