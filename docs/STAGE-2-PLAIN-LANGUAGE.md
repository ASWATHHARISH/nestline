# Stage 2 explained simply

Think of Supabase as Nestline's apartment building.

- Every mother gets her own apartment, called a **workspace**.
- Supabase Auth is the front desk that checks who she is.
- Row Level Security is the lock on every apartment door.
- Her report files go into a private locker whose label starts with her workspace ID.
- Her week, allergies, history, symptoms, appointments and plans have separate labelled drawers.
- Public reviewed guidance lives in a library downstairs. Draft or unapproved material stays in the staff room.

We built 28 labelled database tables and turned the locks on for every table.
Sixteen tables hold user-owned information. We also created the private report
locker, the empty vector fields needed for later search, and relationship tables
needed for later GraphRAG.

We tested the locks with two completely fictional users inside a temporary
transaction. User A could see A's normal row, vector row, graph row and private
file record. User B saw zero of A's records and could not change A's week. Then
we rolled the transaction back, so the test users and records disappeared.

We also tested the moving-in and reset flow. A signed-in fictional user created a
new demo workspace, saved journey version 1 and then version 2, and the database
rejected an old version-0 update. It rejected the same document bytes under a
second filename. Reset kept the private apartment and membership but removed its
journey state. That entire test also rolled back.

The vector drawer is deliberately empty. We have not selected an embedding
provider, and the 55 health passages are still waiting for human review. An empty
vector drawer is the correct safe result today.

What this lets us build next:

1. Stage 3 can create onboarding screens and save the confirmed pregnancy or postpartum timing.
2. Stage 4 can upload fictional reports into the private locker and propose facts for confirmation.
3. Stage 5 can load approved public guidance and search it without mixing one user's facts with another's.

For the demo, say:

> “Stage 2 is Nestline's locked data building. The database, private file locker,
> version controls and per-user locks are live in Supabase. We proved with two
> fictional users that one workspace cannot read, search or change another one.”
