# Stage 5 in plain language

Imagine Nestline has one careful librarian.

When a mother asks a question, the librarian receives the question and a sealed
identity card created by the server. The question itself cannot change the identity
card. This prevents one person from asking for another person's records.

The librarian uses four tools:

1. The exact-record drawer finds facts that must be exact, such as a confirmed
   allergy, pregnancy week, appointment date or medication record.
2. The word finder searches approved passages for the same medical terms.
3. The meaning finder looks for similar passages with vectors.
4. The relationship map explains links such as: a document confirmed a restriction,
   the restriction affected a plan item, and the plan became stale.

Before ranking anything, a strict guard removes every item from the wrong person,
week, stage, country, domain, condition, evidence lane, corpus or release. Draft,
rejected, retired and unapproved content is also removed. A bad item cannot stay in
the list with a low score.

The remaining passages are combined in the same order every time. The packet shows
where every passage came from, its exact supporting span, which retrieval tool found
it, what information is missing and whether Nestline must abstain or ask for
clarification.

## What personal information can be used

Only confirmed, current facts can personalize retrieval. Proposed, rejected,
superseded and conflicted facts stay out. A conflict is shown separately so the
mother can clarify it.

Medication is only repeated as a record. Stage 5 cannot recommend changing it.
A symptom is only a recorded input for the future Safety Gate. Stage 5 cannot say a
symptom is safe because no rule matched.

## What happens when something fails

- No eligible approved evidence: Nestline abstains.
- Missing week or other required information: Nestline says what is missing.
- Conflicting personal records: Nestline asks for clarification.
- Vector search fails: exact SQL and full text may continue, and the packet says the
  result is degraded.
- Personal database retrieval fails: no personal facts are claimed.
- The time limit is exceeded: the result is marked recoverable and must abstain.
- No public release exists: Nestline says so and does not invent content.

## What was tested

Five frozen fictional questions test expected evidence, confirmed personal facts,
forbidden decoys, clarification and the causal graph. Two real local login sessions
also prove that one user cannot retrieve the other user's SQL facts, document
vectors or graph.

The result is locally ready for engineers to begin Stage 6. It is not ready to give
public medical guidance because the Safety Gate and the named clinical, India
localisation, licence and product approvals remain open.