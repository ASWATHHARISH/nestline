begin;

create extension if not exists pgtap with schema extensions;
select plan(11);

select is(
  (
    select count(*)
    from information_schema.role_table_grants
    where grantee = 'anon'
      and table_schema = 'public'
  ),
  6::bigint,
  'anon has exactly the six reviewed public-knowledge table grants'
);

select is(
  (
    select count(*)
    from information_schema.role_table_grants
    where grantee = 'anon'
      and table_schema = 'public'
      and privilege_type <> 'SELECT'
  ),
  0::bigint,
  'anon has no public-table mutation privileges'
);

select is(
  (
    select count(*)
    from information_schema.role_table_grants
    where grantee = 'anon'
      and table_schema = 'public'
      and table_name not in (
        'content_releases', 'public_sources', 'source_blocks',
        'weekly_profiles', 'guidance_fragments', 'guideline_chunks'
      )
  ),
  0::bigint,
  'anon has no grants on personal or administrative tables'
);

select is(
  (
    select count(*)
    from information_schema.role_usage_grants
    where grantee = 'anon'
      and object_schema = 'public'
      and object_type = 'SEQUENCE'
  ),
  0::bigint,
  'anon has no sequence privileges'
);

select ok(
  has_function_privilege(
    'anon',
    'public.match_guideline_chunks(extensions.vector,text,text,integer,text[],integer)',
    'EXECUTE'
  ),
  'anon may call published guideline retrieval'
);

select ok(
  not has_function_privilege(
    'anon',
    'public.match_document_chunks(uuid,extensions.vector,integer)',
    'EXECUTE'
  ),
  'anon cannot call private document retrieval'
);

select ok(
  not has_function_privilege(
    'public',
    'public.match_document_chunks(uuid,extensions.vector,integer)',
    'EXECUTE'
  ),
  'PUBLIC cannot provide inherited private document retrieval access'
);

select ok(
  has_function_privilege(
    'authenticated',
    'public.match_document_chunks(uuid,extensions.vector,integer)',
    'EXECUTE'
  ),
  'authenticated users retain owner-scoped private document retrieval'
);

select is(
  (
    select count(*)
    from pg_proc procedure
    join pg_namespace namespace on namespace.oid = procedure.pronamespace
    where namespace.nspname = 'public'
      and has_function_privilege('anon', procedure.oid, 'EXECUTE')
  ),
  1::bigint,
  'anon can execute only the published guideline retrieval function'
);

select ok(
  not exists (
    select 1
    from pg_default_acl defaults
    cross join lateral aclexplode(defaults.defaclacl) privilege
    left join pg_roles grantee on grantee.oid = privilege.grantee
    join pg_roles owner_role on owner_role.oid = defaults.defaclrole
    where defaults.defaclnamespace = 'public'::regnamespace
      and defaults.defaclobjtype in ('r', 'S', 'f')
      and owner_role.rolname = 'postgres'
      and (privilege.grantee = 0 or grantee.rolname = 'anon')
  ),
  'future postgres-owned application objects have no anonymous defaults'
);

select is(
  (
    select count(*)
    from information_schema.role_table_grants
    where grantee = 'authenticated'
      and table_schema = 'public'
      and table_name in (
        'workspaces', 'private_documents', 'document_facts',
        'health_facts', 'graph_nodes', 'graph_edges'
      )
      and privilege_type = 'SELECT'
  ),
  6::bigint,
  'authenticated owner flows retain their read grants'
);

select * from finish();
rollback;
