# Research pipeline extraction: first parity-checked slice

This change extracts reusable, testable primitives from
`notebooks/04_MemWeave_Final.ipynb` without changing the notebook or its
reported outputs.

## Extracted modules

| Module | Notebook source | Extracted behavior |
|---|---|---|
| `memweave.features` | Sections 2 / feature cell | Candidate-pool definitions, within-pool z-scoring, 10 feature columns, similarity summaries, feature-group indices |
| `memweave.selection` | Section 3 selection helpers | Word-cost budget, stable rank and density selection, greedy MMR, evidence recall |
| `memweave.inference` | Section 3 statistics helpers | Question-level bootstrap, paired bootstrap/sign p-value, Holm correction, verdict classification |\n| `memweave.modeling` | Section 5 | Leakage-aware LR/HGB fitting, deterministic folds, out-of-fold predictions, CV evidence recall |\n| `memweave.tuning` | Section 5 | Development-only C search, backward feature-group elimination, one-standard-error selector choice, simple-rule selection |\n| `memweave.evaluation` | Sections 6–7 | Frozen locked-test results, paired/Holm comparisons, group ablations, mechanism tests, budget sweep |\n| `memweave.downstream` | Section 8 | Retrieval-based evidence hit@k and answer-in-context proxy with paired comparisons |\n| `memweave.transfer` | Section 9 | LoCoMo session/evidence parsing, transfer and role-free models, conversation-cluster bootstrap |\n| `memweave.robustness` | Section 7 | Repeated stratified split seeds with fresh dev-only tuning and paired per-split diagnostics |

The implementations retain the notebook's feature ordering, tie handling,
budget definition, MMR update, bootstrap resampling unit, random seeds, and
Holm ordering. Synthetic parity fixtures exercise those semantics.

## What is deliberately not extracted yet

The end-to-end runner still depends on notebook-level data structures and
state: LongMemEval parsing and deduplication, TF-IDF cache construction,
question-level split construction, cross-validation, model fitting/tuning,
LoCoMo transfer, downstream QA proxy, and artifact/report writing. Those
steps must be moved behind explicit typed inputs and outputs in separate
changes. This PR does not claim a full pipeline rerun or reproduce the
published benchmark metrics.

## Install and test

From `MemWeave/`:

```bash
pip install -e ".[dev,research]"
pytest
```

The optional `research` extra supplies NumPy, SciPy, pandas and scikit-learn
used by the research pipeline. The lightweight package and CLI remain usable
without installing that extra.
\n\n## Locked-test API boundary\n\n`memweave.tuning.tune_pool` accepts development question IDs and development folds only. Its output is the frozen per-pool configuration. `memweave.evaluation.run_locked_evaluation` then accepts those frozen configurations plus disjoint development/test IDs; it does not search hyperparameters or choose the best simple rule. The synthetic test checks this call sequence and verifies that reported result arrays have the locked-test question count.\n\n\n## External transfer and downstream proxy\n\n`memweave.downstream.evaluate_downstream_proxy` reports retrieval-based evidence hit@k and literal answer-in-context@k. It explicitly marks the latter as ineligible when the answer is not short and present in gold-session text; it is not an LLM answer-accuracy metric. `memweave.transfer.build_locomo_conversations` parses evidence-bearing LoCoMo questions, and `evaluate_locomo_transfer` trains only on LongMemEval before scoring at conversation level. The bootstrap resamples conversations, not individual QA rows.\n\n\n`memweave.robustness.evaluate_split_robustness` repeats the full dev-tuning/test-scoring procedure for each supplied split seed. Its test halves can overlap across seeds; the returned rows are explicitly robustness diagnostics, not independent replications.\n