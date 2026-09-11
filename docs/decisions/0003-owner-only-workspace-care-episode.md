# Decision 0003: owner-only workspaces represent one care episode

- **Status:** accepted for the capstone
- **Date:** 11 September 2026
- **Scope:** Stage 2 storage and authorization

## Decision

Nestline V1 has one authenticated owner per workspace and no collaborator roles.
One workspace represents one pregnancy-through-twelve-weeks-postpartum care
episode. If the same person later begins another pregnancy, Nestline creates a new
workspace rather than mixing the two episodes.

Child records store `workspace_id`. Their owner and episode are derived through
the workspace, so the schema does not repeat `owner_id` and `episode_id` on every
row. Record-specific provenance and version fields remain present where the
workflow needs them; they are not meaningless mandatory columns on every table.

## Reason

The earlier schema named owner, editor, reviewer and viewer but gave every member
the same database powers. The capstone does not expose collaboration, so carrying
four unused roles creates risk without product value. The owner-only boundary is
smaller, testable and matches the current onboarding and demo flows.

Treating the workspace as the episode also keeps every foreign key and RLS filter
workspace-scoped. It prevents a later episode from silently reusing current facts,
plans or reports.

## Consequences

- The database rejects every non-owner membership row.
- Only `auth.uid() = workspaces.owner_user_id` can access personal records or files.
- A future collaboration feature requires a new migration, a capability matrix and
  explicit per-role tests before any non-owner membership is enabled.
- A future multi-episode view may aggregate several owned workspaces in application
  code, while keeping their private facts and plans separate.
