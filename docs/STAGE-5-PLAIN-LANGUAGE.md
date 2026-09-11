# Stage 5 in plain language

**Status:** final consolidated correction accepted for controlled engineering; required GitHub checks passed
**Stage 6:** may begin as a separate controlled engineering stage; not implemented in this change
**Git:** final consolidated review baseline `2a067945986d68f85fba6234b9cb59be90a90eab`; see `STAGE-5-FINAL-CONSOLIDATED-CORRECTION-AND-STAGE-6-GATE.md`

## What Stage 5 does

Think of Nestline as a careful librarian. When someone asks a question, Stage 5 gathers only the allowed and relevant material:

- exact confirmed records from the signed-in person’s workspace;
- approved public evidence for the right journey stage, week, country and topic;
- related causes and effects from a small, bounded graph;
- exact source spans and provenance for future citations.

It returns an Evidence Packet. It does not write the final health answer, decide whether a symptom is safe, change medication, confirm facts or modify a plan.

The last correction makes the packet act like a sealed checklist: its answerability, journey, evidence list, graph path, trace and failure reason must all tell the same story. The current local evidence is 56/56 focused tests, 232/232 Python tests and 212/212 adversarial cases.

## How Nestline decides what is enough

The gateway first identifies the question’s trusted purpose:

- public guidance needs approved public evidence;
- a personal-record question needs a relevant confirmed record;
- personalized guidance needs both public guidance and a relevant personal constraint;
- a causal “why did this change?” question needs the permitted graph relationship.

The gateway constructs this policy itself. A caller cannot label public guidance as personal-only or otherwise weaken what evidence is required.

Full support may continue to a later stage. Partial or missing support, a relevant unresolved conflict, database failure or timeout causes abstention or clarification.

## What the second review found

The earlier rectification fixed two answerability bugs, but five technical gaps remained:

1. A public question and a causal question could share the same personal cache entry. The first one run could hide or leak a graph path.
2. A small result request could cache too few candidates for a later larger request.
3. A caller could construct an evidence-policy object and claim it was trusted.
4. Individual fields could be valid even when the Evidence Packet or result contradicted itself.
5. A generic question such as “What allergies are in my record?” could miss an unresolved allergy conflict because the user did not type “conflict” or name its value.

All five were reproduced on the reviewed commit and corrected.

## What happens for every request

1. The server checks who is signed in.
2. It finds that owner’s workspace and care episode.
3. It reads confirmed journey, conditions, restrictions and state version from the database.
4. It distinguishes the current week from a clearly requested other week.
5. It builds the fixed evidence policy from the trusted purpose.
6. It retrieves exact records, public text/vector matches and permitted graph paths.
7. It excludes wrong-user, wrong-week, wrong-country, draft, rejected, retired and unrelated material before ranking.
8. It ranks remaining evidence in a repeatable order.
9. It checks conflicts, missing information and every required type of support.
10. It returns a validated packet and trace or abstains.

## Cache correction

Cache identity now includes the policy ID/version/purpose, required support and candidate limit. Personal cache identity also includes the allowed private context, authenticated workspace/care episode and database state version.

This means:

- public and causal questions cannot exchange graph results;
- personal and mixed questions cannot exchange private passages;
- max-1 and max-5 requests behave like fresh requests in either order;
- one workspace cannot reuse another workspace’s private result;
- a confirmed state or release version change invalidates the old result.

## Generic conflict and missing-information correction

Nestline maps normal singular/plural category wording to allergies, restrictions, medications, conditions, appointments and journey timing. Users do not need to know an unresolved value or special system terminology.

A matching unresolved conflict asks for clarification. A matching required missing field is reported. An unrelated appointment conflict does not block an otherwise supported movement question.

## Privacy and safety rules preserved

- Only confirmed personal facts can personalize.
- Proposed, rejected, superseded and conflicted facts cannot become active context.
- Medication remains record-only.
- Symptoms remain safety-evaluation-only; “no match” never means “safe.”
- Graph traversal is bounded, cycle-safe and workspace-safe.
- All 63 weekly profiles remain drafts.
- No production embedding or paid model is needed for deterministic Stage 5 checks.

## What the checks proved

- 232/232 Python tests passed.
- 56/56 focused Stage 5 tests passed.
- 64/64 content-contract cases passed.
- 26/26 journey cases passed.
- 28/28 frozen Stage 5 behavior, support and journey decisions passed.
- 212/212 second-rectification matrix cases passed.
- 18/18 expected public evidence items were found in the top five.
- 18/18 returned public evidence items were correct.
- 12/12 returned personal facts were expected.
- 1/1 required graph path was correct.
- 254/254 database assertions passed.
- 70/70 authenticated API checks passed.
- Wrong-week, wrong-country, unapproved-source, cross-workspace and proposal/conflict personalization counts were zero.
- Application-schema lint found zero issues.
- Every Stage 1–4 gate remained green.

## What this does not prove

The embeddings are repeatable test fixtures, not a selected production model. Twenty-eight synthetic questions are not a clinical benchmark or sealed final holdout. Clinical, India-localisation, licence, product/publication and production-provider reviews remain open. Stage 6 must still build and independently review the Safety Gate.

Stage 5 should now go to an independent reviewer. Stage 6 should begin only after that reviewer accepts this exact local change set.
