-- An owner must be able to read a just-inserted workspace before the AFTER INSERT
-- membership trigger has finished creating the matching owner-membership row.

begin;

drop policy if exists "members read workspaces" on public.workspaces;
create policy "owners and members read workspaces" on public.workspaces
for select to authenticated using (
  owner_user_id = auth.uid()
  or private.is_workspace_member(id)
);

commit;
