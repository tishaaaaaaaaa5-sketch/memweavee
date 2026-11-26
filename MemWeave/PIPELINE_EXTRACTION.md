# Research pipeline extraction: first parity-checked slice

This change extracts reusable, testable primitives from
`notebooks/04_MemWeave_Final.ipynb` without changing the notebook or its
reported outputs.

## Extracted modules

| Module | Notebook source | Extracted behavior |
|---|---|---|
| `memweave.features` | Sections 2 / feature cell | Candidate-pool definitions, within-pool z-scoring, 10 feature columns, similarity summaries, feature-group indices |
| `memweave.selection` | Section 3 selection helpers | Word-cost budget, stable rank and density selection, greedy MMR, evidence recall |
| `memweave.inference` | Section 3 statistics helpers | Question-level bootstrap, paired bootstrap/sign p-value, Holm correction, verdict classification |

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
