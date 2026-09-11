# Stage 5 in plain language

**Status:** corrected locally and ready for independent Stage 5 re-review
**Stage 6:** not started
**Git:** reviewed baseline 448eb6d2ab7b4e8cc7db9fc42ce5c523a7fe10a7; rectification implementation commit dcec1f9e847a64185330ba4406a886bcced688b2 is pushed to the review branch

## What Stage 5 does

Think of Nestline as a careful librarian.

When someone asks a question, Stage 5 collects only the information that is allowed and relevant:

- exact personal records from the signed-in person’s workspace;
- approved public health material for the right journey stage, week, country and topic;
- related causes and effects from a small, bounded graph;
- source labels and exact text spans so later stages can cite the evidence.

Stage 5 returns this evidence package. It does not write the final answer and it does not decide whether a symptom is safe.

## What was wrong

The first version asked a question that was too simple: “Did I find anything?”

That meant an unrelated peanut-allergy record could make a hospital-preparation question look supported. It also meant a conflict about prenatal yoga could be hidden because other confirmed facts existed.

The corrected version asks two questions:

1. What kind of evidence does this question require?
2. Did we find relevant evidence of every required kind?

A public-guidance question requires approved public guidance. A question such as “What allergy is in my record?” can use a relevant confirmed personal record and does not need public guidance. A personalised guidance question needs both the right public guidance and the relevant personal constraint. A causal “why did my plan change?” question needs the graph relationship.

## What happens now

For each request, Nestline:

1. checks who is signed in;
2. finds that person’s workspace and care episode on the server;
3. reads the confirmed current journey and state version from the database;
4. decides whether the question is about the current week or clearly names another week;
5. chooses the trusted evidence policy in server code;
6. retrieves exact records, public text/vector matches and permitted graph paths;
7. removes wrong-user, wrong-week, wrong-country, draft, rejected, retired and unrelated items;
8. ranks the eligible evidence in a repeatable order;
9. reports full support, partial support, no support or clarification needed;
10. returns citations, provenance, component results and failures.

The question text cannot change the authenticated workspace, confirmed conditions or cache state version.

## The two reported failures

| Question situation | Before | After |
|---|---|---|
| No matching public preparation evidence, but unrelated personal records exist | It incorrectly said an answer could continue | It removes unrelated personal data and abstains with `no_approved_public_content` |
| Prenatal-yoga conflict plus unrelated confirmed information | It incorrectly said an answer could continue | It carries only the relevant restriction/conflict and asks for clarification with `unresolved_conflict` |

The complete before/after packets are saved in `docs/STAGE-5-RECTIFICATION-EVIDENCE-PACKETS.json`.

## Privacy and safety rules kept

- A signed-in user cannot retrieve another user’s facts, vectors, graph paths or cache.
- Only confirmed personal facts can personalise.
- Proposed, rejected, superseded and unresolved-conflict facts cannot silently become active truth.
- A medication can be shown as a record, but Stage 5 never recommends changing it.
- A symptom stays marked for safety evaluation. “No match” never means “safe.”
- Generic words such as “record” cannot expose unrelated private passages.
- Stage 5 reads; it never confirms facts or changes plans.
- Draft public material stays draft. All 63 weekly profiles remain unpublished.

## What the checks proved

- 212/212 Python tests passed.
- 36/36 focused Stage 5 tests passed.
- 64/64 content-contract cases passed.
- 26/26 journey cases passed.
- 26/26 frozen Stage 5 behaviors passed.
- 18/18 expected public evidence items were found in the top five.
- 18/18 returned public evidence items were correct for the frozen truth.
- 11/11 returned personal facts were expected.
- 1/1 required graph path was correct.
- 254/254 database assertions passed.
- 70/70 authenticated API checks passed.
- Wrong week, wrong country, unapproved source, cross-workspace leakage and proposal/conflict personalization counts were all zero.
- Database lint found zero issues.
- Every Stage 1–4 gate remained green.

## What this does not prove

The embeddings are repeatable test fixtures, not a chosen production model. The dataset has 26 synthetic development questions and is not a large clinical benchmark. Health content still needs clinical, India-localisation, licence, product and publication approval. Stage 6 still has to build and review the Safety Gate.

Stage 5 should now go to an independent reviewer. Stage 6 should begin only after that reviewer accepts this rectification.
