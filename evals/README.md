# Stage 0 software cases and future AI evaluation

phase_1_contract.jsonl contains 64 visible, versioned examples: 20 safety-routing
examples, 12 condition cases, 8 postpartum-day cases, 9 month ranges, 7 food
constraint cases and 8 synthetic-document integrity cases.

These are software checks and preparation requested by the Stage 0 correction
plan. Running scripts.run_contract_evals does not call an AI model or OCR service.
Document cases check artifacts and their truth annotations; they do not implement
or verify extraction, consent, graph updates or stale-plan behaviour.

Every record has id, version, kind, inputs, outputs and metadata. Do not relabel
these visible cases as a sealed holdout. Future model-specific experiments still
need reviewed question/expected-answer/citation/abstention cases and a separately
protected holdout. The planned 45 development/15 held-out AI scenarios remain
unimplemented; this file does not substitute for that independent benchmark.

The safety examples are draft product routing cases awaiting clinical review.
Negation/history examples deliberately over-trigger. A no-match result does not
establish low risk. Both no-match and clarify keep generation_allowed false.
Later safety work needs broader language, spelling, ambiguity and population-level
validation. Do not report 64/64 as medical accuracy.

Record changes as a new dataset version; keep the previous file/hash in Git.
The runner records the dataset SHA-256 in reports/local/contract-evals.json.
