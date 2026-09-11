begin;

-- Supabase projects can be created with automatic Data API grants enabled.
-- Make Nestline's anonymous boundary deterministic regardless of that project
-- setting: anonymous users may read only reviewed, published knowledge tables.
revoke all privileges on all tables in schema public from anon;
revoke all privileges on all sequences in schema public from anon;
revoke execute on all functions in schema public from public, anon;

-- Keep later Nestline migrations from silently exposing newly created tables,
-- sequences or functions. Application migrations are owned by postgres;
-- Supabase's platform-owner defaults are managed outside application SQL.
alter default privileges for role postgres in schema public
  revoke all privileges on tables from anon;
alter default privileges for role postgres in schema public
  revoke all privileges on sequences from anon;
alter default privileges for role postgres in schema public
  revoke execute on functions from public, anon;

grant select on
  public.content_releases,
  public.public_sources,
  public.source_blocks,
  public.weekly_profiles,
  public.guidance_fragments,
  public.guideline_chunks
to anon;

-- PostgreSQL grants EXECUTE on new functions to PUBLIC by default. Remove that
-- inherited access and explicitly restore only the two intended retrieval paths.
revoke all on function public.match_guideline_chunks(
  extensions.vector, text, text, integer, text[], integer
) from public, anon, authenticated;
grant execute on function public.match_guideline_chunks(
  extensions.vector, text, text, integer, text[], integer
) to anon, authenticated;

revoke all on function public.match_document_chunks(
  uuid, extensions.vector, integer
) from public, anon, authenticated;
grant execute on function public.match_document_chunks(
  uuid, extensions.vector, integer
) to authenticated;

comment on function public.match_guideline_chunks(
  extensions.vector, text, text, integer, text[], integer
) is 'Published-knowledge retrieval; available to anonymous and authenticated API roles and still filtered by published release state.';
comment on function public.match_document_chunks(
  uuid, extensions.vector, integer
) is 'Owner-scoped private-document retrieval; available only to authenticated users and additionally enforced by workspace membership.';

commit;
