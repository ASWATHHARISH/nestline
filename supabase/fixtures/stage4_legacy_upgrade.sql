-- Simulates legitimate Stage 3 rows before the Stage 4 migration is applied.
insert into auth.users(id) values ('b0000000-0000-0000-0000-000000000001');
insert into public.workspaces(
  id, owner_user_id, mode, display_name
) values (
  'b1000000-0000-0000-0000-000000000001',
  'b0000000-0000-0000-0000-000000000001',
  'fictional_demo', 'Stage 4 legacy upgrade fixture'
);
insert into public.private_documents(
  id, workspace_id, storage_object_path, original_filename, media_type,
  byte_size, sha256, status
) values (
  'b2000000-0000-0000-0000-000000000001',
  'b1000000-0000-0000-0000-000000000001',
  'b1000000-0000-0000-0000-000000000001/legacy.pdf', 'legacy.pdf',
  'application/pdf', 12, repeat('b', 64), 'confirmed'
);
insert into public.document_facts(
  id, workspace_id, document_id, field_name, value, source_page,
  source_text, confidence, status
) values (
  'b3000000-0000-0000-0000-000000000001',
  'b1000000-0000-0000-0000-000000000001',
  'b2000000-0000-0000-0000-000000000001',
  'legacy_field', '"legacy"', 1, 'legacy_field: legacy', 1, 'confirmed'
);
insert into public.medication_mentions(
  id, workspace_id, document_id, name_as_written, context_text, status
) values (
  'b4000000-0000-0000-0000-000000000001',
  'b1000000-0000-0000-0000-000000000001',
  'b2000000-0000-0000-0000-000000000001',
  'FICTIONAL LEGACY MEDICINE', 'Fictional upgrade row.', 'confirmed'
);
