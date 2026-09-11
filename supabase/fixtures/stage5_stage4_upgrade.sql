-- Controlled Stage 4 rows inserted before the Stage 5 migration.
-- Every identifier is reserved for this upgrade proof and removed by the check.
insert into auth.users(id)
values ('61000000-0000-4000-8000-000000000001');

insert into public.workspaces(id, owner_user_id, mode, display_name)
values (
  '62000000-0000-4000-8000-000000000001',
  '61000000-0000-4000-8000-000000000001',
  'personal_empty',
  'Stage 5 upgrade fixture'
);

insert into public.content_releases(
  id, corpus_version, release_fingerprint, status
) values (
  '63000000-0000-4000-8000-000000000001',
  'stage5-upgrade-fixture-v1',
  repeat('6', 64),
  'draft'
);

insert into public.public_sources(
  source_id, release_id, title, publisher, canonical_url, jurisdiction,
  source_version, reuse_status, allowed_use, status, content_checksum
) values (
  'S5-UPGRADE-SOURCE',
  '63000000-0000-4000-8000-000000000001',
  'Synthetic Stage 5 upgrade source',
  'Nestline test fixture',
  'https://example.invalid/stage5-upgrade',
  array['IN'],
  'fixture-1',
  'permitted',
  array['store'],
  'reviewed',
  repeat('7', 64)
);

insert into public.guideline_chunks(
  chunk_id, release_id, evidence_id, source_id, candidate_checksum, text,
  source_block_ids, stage, unit, range_start, range_end, jurisdiction,
  domains, display_slots, status
) values (
  'S5-UPGRADE-CHUNK',
  '63000000-0000-4000-8000-000000000001',
  'S5-UPGRADE-EVIDENCE',
  'S5-UPGRADE-SOURCE',
  repeat('8', 64),
  'synthetic upgrade protein terminology fixture',
  array['S5-UPGRADE-BLOCK'],
  'pregnancy',
  'week',
  24,
  24,
  array['IN'],
  array['nutrition'],
  array['plan'],
  'reviewed'
);

insert into public.private_documents(
  id, workspace_id, storage_object_path, original_filename, media_type,
  byte_size, sha256, status, scan_status, scan_provider, scan_version,
  scan_completed_at, review_version, confirmed_at, confirmed_by_user_id
) values (
  '64000000-0000-4000-8000-000000000001',
  '62000000-0000-4000-8000-000000000001',
  '62000000-0000-4000-8000-000000000001/stage5-upgrade.pdf',
  'stage5-upgrade.pdf',
  'application/pdf',
  20,
  repeat('9', 64),
  'confirmed',
  'fixture_verified',
  'upgrade_fixture',
  '1',
  clock_timestamp(),
  1,
  clock_timestamp(),
  '61000000-0000-4000-8000-000000000001'
);

insert into public.document_chunks(
  id, workspace_id, document_id, page, source_span, text, text_sha256
) values (
  '65000000-0000-4000-8000-000000000001',
  '62000000-0000-4000-8000-000000000001',
  '64000000-0000-4000-8000-000000000001',
  1,
  '{"locator":"upgrade/page/1","start_char":0,"end_char":39}',
  'synthetic upgrade confirmed allergy record',
  repeat('a', 64)
);

insert into public.graph_nodes(
  id, workspace_id, node_type, entity_id, label, source_document_id
) values (
  '66000000-0000-4000-8000-000000000001',
  '62000000-0000-4000-8000-000000000001',
  'document',
  '64000000-0000-4000-8000-000000000001',
  'Synthetic upgrade document node',
  '64000000-0000-4000-8000-000000000001'
);
