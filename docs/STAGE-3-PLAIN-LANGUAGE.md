# Stage 3 in plain language

Stage 3 is the front door of Nestline. It now works.

Imagine Nestline is a careful notebook. Before it can show the right pregnancy or
postpartum information, it needs to know where the person is in their journey.
The person can say:

- “I may be pregnant.”
- “My estimated due date is this date.”
- “I was at week 24 and day 2 on this date.”
- “I am around month 5.”
- “I delivered on this date.”
- “I was at postpartum week 2 and day 3 on this date.”

A normal calculator, not an AI model, works out today's result. It knows that days
move forward, so week 24 day 5 becomes week 25 day 0 two days later. If the person
only knows a month, Nestline keeps a range such as approximately weeks 18–22. It
does not pretend to know one exact week.

## What happens when two dates disagree

Nestline shows both answers. It says there is a difference and asks the person to
choose. It does not secretly decide which doctor, report or memory is correct.
When the person confirms a new value, the earlier value stays in history so the
team can see what changed.

A new pregnancy after postpartum needs a new workspace because one workspace is
one pregnancy-through-postpartum episode. Nestline now blocks that backward move
instead of showing a choice that cannot be saved.

## What else the person can enter

During onboarding they may add allergies, medical history, dietary restrictions,
movement restrictions, a current symptom and the next appointment. These are
optional and are stored with the confirmed onboarding submission.

Symptoms are saved with the time they were reported. The existing draft safety
rules check them before saving. A known urgent phrase stays urgent. If a draft rule
does not understand the symptom, Nestline asks for clarification; it does not call
the symptom safe. This is careful engineering, but the wording and rules still
need the real specialist reviews before public release.

## What “Save” now means

Saving requires a visible confirmation checkbox. If dates conflict, there is a
second choice. The database saves the journey, optional facts, symptom and
appointment together. If one part is invalid, none of it is saved.

A repeated click with the same information creates no duplicate. An old browser
tab cannot overwrite a newer version. Another signed-in user cannot see or change
the workspace. Even the owner cannot bypass confirmation by writing a journey row
directly; the protected confirmed-save function is the allowed route.

After refresh or a new login, the confirmed timing is still there and moves
forward from the recorded date. The database also repeats the important timing,
conflict and draft-safety checks, so a changed or homemade request cannot skip the
rules enforced by the screen.

## What is ready on screen

The Streamlit application now has:

- the fictional-data and privacy warning;
- sign-in and create-account forms;
- Personal Empty and Fictional Demo workspace choices;
- all six timing paths;
- optional onboarding details;
- calculated week/range review;
- conflict comparison and explicit confirmation;
- saved-state display.

## What comes later

Medical-report upload and confirmation of extracted report facts are Stage 4.
RAG and personal/public retrieval are Stage 5. The specialist-approved live safety
gate is Stage 6. Chat, agents, the full weekly dashboard and plans are later
integration stages.

So Stage 3 answers: “Who is this workspace for, where are they in the journey, what
did they explicitly tell us, and did they confirm it?” It does not yet answer
health questions or read reports.

## Proof we ran

- 154 Python tests passed.
- 64 earlier deterministic cases passed.
- 26 journey date/conflict cases passed.
- 160 current database assertions passed on both an exact upgrade and a clean build.
- 17 real onboarding API checks passed across all six timing paths, including relogin and another-user denial.
- The Streamlit start screen rendered without a network call.
- The deployed Supabase project has the Stage 3 migration and zero test fixtures.

The detailed engineering evidence is in **docs/STAGE-3-IMPLEMENTATION.md**.
Kajal's review checklist is in **docs/STAGE-3-REVIEW-HANDOFF.md**.