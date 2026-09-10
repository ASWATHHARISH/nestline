# Stage 1 explained simply

Imagine Nestline is building a very careful library for a mother.

Stage 0 made the list of books, the little information cards and the labels that
say where each card belongs. Stage 1 builds the machine that reads those books.

The machine does ten simple things:

1. It checks whether Nestline is allowed to use the exact page or PDF.
2. It saves the exact version and makes a fingerprint so changes are visible.
3. It reads headings, paragraphs, lists, tables and PDF page numbers.
4. If a PDF is only a picture, it either uses a named OCR tool or stops and says so.
5. It looks only for passages already selected in Stage 0. It does not make new health advice.
6. It proves where every passage came from.
7. It labels which week, country and dashboard area the passage can support.
8. It says which personal facts will matter later, such as allergies or a movement restriction.
9. It gives every unapproved passage to a real reviewer.
10. Only after approval can it make the searchable number called an embedding.

We ran this machine on all 14 source pages/PDFs that support the current dataset.
It found all 55 unique passages in the real source text. None are lost. None are
published. All 55 are waiting for review, so the machine made zero embeddings.

Kajal's independent check found seven engineering gaps. They are now closed: the
proof travels with a fresh Git checkout, citation block IDs point to saved blocks,
source changes reopen review, reviewer jobs stay separate, publication checks all
five approvals, and repeated captures share one logical version. The separate
Windows certificate concern did not recur; all five OWH pages downloaded with
normal certificate checking still on.

That does **not** mean the feature failed. It means the lock works. A machine test
cannot pretend to be a doctor, licence reviewer or product owner.

The future app will use these labels like this:

- “Which week am I in?” comes from confirmed onboarding/timing data.
- “How big is the embryo?” comes from reviewed general source data, never a made-up comparison.
- “What should I eat?” checks reviewed food options against confirmed allergies and restrictions.
- “How can I move?” checks reviewed movement options against symptoms and clinician instructions.
- “How am I feeling?” offers reviewed, optional wellbeing support and routes concerns properly.
- “When is my next appointment?” comes from her confirmed private information.
- Chat answers use the same public passages and show where the answer came from.

Her uploaded reports are a different locked box. Stage 4 will read fictional/demo
reports, show proposed facts and ask her to confirm them. Stage 1 never mixes those
private files with the public library.

The one problem Stage 1 found was useful: the same NHS sentence had accidentally
been saved twice. We kept the sentence once and linked both useful cards to it.
That is what “no duplicate units” means.

For the demo, say:

> “Stage 1 is our careful library machine. It can read and trace every current
> source passage, but it refuses to publish or embed health content until real
> reviewers approve it. It also already knows which future dashboard cards and
> personal facts each passage may depend on.”
