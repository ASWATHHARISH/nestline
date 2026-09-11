# Stage 2 explained simply

Think of Supabase as Nestline's apartment building.

- Each signed-in mother owns a locked apartment called a **workspace**.
- One apartment holds one pregnancy and its postpartum recovery period.
- A future pregnancy gets a fresh apartment, so old facts do not mix with new ones.
- Her report files go into a private locker labelled with that workspace ID.
- Her week, allergies, history, symptoms, appointments and plans use separate drawers.
- Reviewed public guidance belongs in a library downstairs; draft material stays closed.

We built 28 database tables and turned Row Level Security on for every table.
Sixteen tables hold personal information. This first product is owner-only: labels
like viewer or editor cannot be added and accidentally receive owner powers.

When a confirmed fact changes, Nestline now follows all the strings tied to that
fact. A saved plan, plan item or appointment question becomes **stale**, the journey
asks for confirmation again, and the old graph link is removed. This prevents the
app from quietly showing advice based on information that no longer exists.

Deleting a report happens in the safe order:

1. List only the files inside that exact workspace locker.
2. Delete those files through the Supabase Storage API.
3. Delete the database record and everything derived from it.
4. For fictional demos, rebuild the same clean `maya-v1` seed.

The database refuses step 3 while the Storage file still exists. A failed Storage
deletion stops the reset rather than leaving an orphaned file.

We tested the building with two fictional users. The live suite checks all 16
personal tables, private vector search, graph links, Storage rules, cross-apartment
references, fact invalidation and demo reset. The current file pins 122 assertions and rolls back
all fixtures. It passes both when upgrading the five-migration database we already
had and when building all ten migrations from an empty database. Database lint
also reports zero errors.

We also used the real local Auth, database and file APIs with two temporary users.
All 13 checks passed: the owner could manage her own fictional report, the other
user could not see or change it, metadata could not disappear before the file,
and every temporary user, workspace and file was removed afterward.

The same five corrective migrations are deployed to `nestline-dev`. A read-only
remote check found all ten migrations, all 28 RLS locks, five dependency tables,
zero direct report-metadata delete grants and zero leftover test fixtures.

The vector drawer is deliberately empty. We have not selected the final embedding
model, and public health passages still need the remaining human approvals. That
is safe and belongs to later stages.

What this lets us build next:

1. Stage 3 can save and confirm onboarding details and pregnancy/postpartum timing.
2. Stage 4 can upload fictional reports and propose extracted facts for confirmation.
3. Stage 5 can retrieve approved public evidence without mixing users or episodes.

For the demo, say:

> “Stage 2 is Nestline's locked data building. Every user owns one private care
> episode, report files must be removed in the safe order, and changing a fact
> automatically marks dependent plans stale. We proved the isolation and reset
> rules with 122 pinned Stage 2 checks; the full current Stage 2–4 gate has 206.”
