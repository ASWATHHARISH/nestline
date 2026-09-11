-- Stage 2 correction: the capstone has private, owner-only care episodes.
-- A workspace is one pregnancy/postpartum episode; collaboration is deferred.

begin;

-- Fail rather than silently deleting a collaborator if this migration is ever
-- applied to a database where the unused role surface was already exercised.
do $$
begin
  if exists (select 1 from public.workspace_members where role <> 'owner') then
    raise exception 'owner-only migration requires explicit removal of existing non-owner memberships';
  end if;
end;
$$;

drop policy if exists "owners add non-owner members" on public.workspace_members;
drop policy if exists "owners update non-owner members" on public.workspace_members;
drop policy if exists "owners remove non-owner members" on public.workspace_members;

revoke insert, update, delete on public.workspace_members from authenticated;

alter table public.workspace_members
  drop constraint if exists workspace_members_role_check;
alter table public.workspace_members
  add constraint workspace_members_owner_only check (role = 'owner');

-- Existing table and Storage policies call this boundary. Replacing it makes
-- every personal operation owner-only without leaving misleading role labels.
create or replace function private.is_workspace_member(target_workspace_id uuid)
returns boolean
language sql
stable
security definer
set search_path = public, pg_temp
as $$
  select exists (
    select 1
    from public.workspaces workspace
    join public.workspace_members member on member.workspace_id = workspace.id
    where workspace.id = target_workspace_id
      and workspace.owner_user_id = auth.uid()
      and member.user_id = auth.uid()
      and member.role = 'owner'
  );
$$;

comment on table public.workspaces is
  'One private care episode per workspace. A later pregnancy creates a new workspace; ownership is derived through owner_user_id.';
comment on table public.workspace_members is
  'Owner membership only for the capstone. Editor/reviewer/viewer collaboration is deferred until capability-specific policies exist.';

commit;
