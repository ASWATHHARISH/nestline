# Stage 4 in plain language

Think of Nestline as having a locked envelope, a careful reader and a form that
the mother must approve.

1. She signs in and chooses a private file.
2. Nestline checks that the file is really a supported PDF or image, is small
   enough, opens correctly, belongs to the expected fictional person in Demo
   Mode, and has passed the configured file scanner.
3. Nestline stores the original inside her private workspace.
4. It reads normal PDF text first. It asks the controlled OCR reader only when an
   image has no text layer.
5. It makes suggestions such as “this record says week 24” or “this record contains
   a movement restriction.” Every suggestion shows the page and exact words it
   came from.
6. Nothing changes yet. She can edit, confirm, reject or keep a disagreement for
   clarification.
7. Only after the whole review is complete does one protected database action save
   the approved facts.
8. If two documents disagree, Nestline keeps both. It asks a clarification question
   and stops that fact from silently changing advice.
9. If a confirmed restriction affects an old movement plan, the plan is marked
   stale so Stage 5 can explain and rebuild it.

Medication wording gets extra care. Nestline may record what a fictional document
says, but that text is labelled **record only**. It does not tell the mother to
start, stop or change a medicine.

The deliberately malicious sentence inside `DOC-006` is treated like ink on paper.
It cannot tell the app to ignore its rules, call a tool or publish private data.

The demo is repeatable because all eight records are invented, visibly watermarked
and copied into a separate session workspace. There is also one noisy OCR image
and five failure examples: locked, corrupt, unsupported, too large and wrong-person
files.

Stage 4 is ready for Stage 5 engineering with fictional data, including the shared
`nestline-dev` database. The remote database has both Stage 4 migrations, all 206
security/behavior checks pass, and a visitor who is not signed in can read only the
six reviewed public-content tables. Real medical uploads remain switched off until
a real malware scanner, the exact extraction model test, clinical/India review and
the final product review are complete.
