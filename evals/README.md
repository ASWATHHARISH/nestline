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
## Stage 6 deterministic Safety Gate development set

`stage6_safety_development.jsonl` is a visible, synthetic English development set
for the deterministic Stage 6 software contract. It covers every configured urgent
category, all five entry channels, ambiguity, context, prompt injection, fixed
messages, configuration failures and trace minimisation. It does not access the
sealed final holdout and does not establish clinical validity, population
sensitivity or public-release readiness. The draft rule specification may be used
only through the explicit evaluation-only path; public runtime remains fail-closed.

Regenerate and evaluate it with:

```text
python -m scripts.build_stage6_safety_evals
python -m scripts.run_stage6_safety_evals --write-report
```

## Stage 7 bounded orchestration development set

`stage7_orchestration_development.jsonl` is a generated, visible set of 76
synthetic cases for the deterministic router, all eight bounded workers, provider
failure boundaries, safety bypass, context minimisation and the Schedule Builder.
Regenerate it with `python -m scripts.build_stage7_evals`, then run
`python -m scripts.run_stage7_evals --write-report` and
`python -m scripts.check_stage7 --write-report`.

The set uses deterministic fixture evidence and the offline provider adapter. It
does not call a paid provider, does not access the sealed final holdout, and does
not establish clinical, production retrieval or public-release quality. Routine
symptom navigation remains disabled until a reviewed non-urgent symptom policy
exists; urgent and unresolved cases stay at the Stage 6 boundary.

## Stage 8 validation and composition development set

`stage8_validation_development.jsonl` is a generated, visible set of 62
synthetic cases for the seven-validator display gate, exact-span citations, bounded
semantic assessment, answerability, provenance, repair/retry limits and reusable
daily/weekly plan validation. Regenerate it with

```text
python -m scripts.build_stage8_evals
python -m scripts.run_stage8_evals --write-report
python -m scripts.check_stage8 --write-report
```

The set uses controlled fixtures and deterministic evaluator outcomes. It does not
call a paid provider, access the sealed final holdout, establish clinical validity,
or prove public-release quality. An unavailable or uncertain semantic evaluator
remains blocking, and the draft safety specification keeps public runtime closed.
## Stage 9 Streamlit product-experience development set

`stage9_product_experience.jsonl` is a visible set of 38 deterministic cases for
the local Streamlit shell, Personal/Demo isolation, Weekly Home, Compass, records,
plans, evidence, simulated review, evaluator truth and Stage 10-disabled behavior.
Run it with:

```text
python -m scripts.run_stage9_evals
python -m scripts.check_stage9_ui
python -m scripts.check_stage9 --write-report
```

The generated three-story inventory repeats each fictional story three times after
a deterministic Demo Mode reset. The UI evidence is an internal implementation
walkthrough. It does not access the sealed final holdout, use real personal data,
call a paid provider, establish clinical validity, prove WCAG conformance or count
as external user research. Durable writes and deployment remain outside Stage 9.
