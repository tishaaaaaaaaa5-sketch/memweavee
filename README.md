# MemWeave

**MemWeave** studies query-agnostic session-memory retention under a fixed token budget. The experiments use LongMemEval-S and compare learned retention policies with recency, random selection, and simple heuristic baselines.

> **Research status:** Results are mixed and should be reported conservatively. The v2.3 corrected analysis finds a small, analysis-sensitive gain over the strongest simple rule, not robust algorithmic superiority. Pairwise-similarity features account for much of the measured signal; redundancy and cost-awareness components were not active in the audited folds.

## Start here

- [Project guide](MemWeave/README.md) — setup, notebook order, data and output locations.
- [Research overview](MemWeave/PROJECT_OVERVIEW.md) — question, method, metrics and interpretation limits.
- [Notebooks](MemWeave/notebooks/) — versioned research notebooks.
- [Results](MemWeave/results/) — findings and tabular outputs.

## Repository structure

```text
MemWeave/
├── README.md
├── PROJECT_OVERVIEW.md
├── notebooks/
│   ├── 01_MemWeave_2_1.ipynb
│   ├── 02_MemWeave_2_2.ipynb
│   ├── 03_memweave_v2_3_addendum.ipynb
│   └── 04_MemWeave_Final.ipynb
└── results/
    ├── README.md
    ├── findings_v2_3.txt
    └── tables/
```

## Reproducibility

The notebooks are intended for Jupyter or Google Colab. Read the notebook setup cells before running. The main benchmark is LongMemEval-S; optional LoCoMo validation is reported separately. Dataset files and feature caches are not bundled in the normal source tree.

The primary metric is **session-level evidence recall**. QA-proxy accuracy is supplementary and is not an official LLM-judge evaluation.

## Evidence and reporting guardrails

- Do not claim that MemWeave is conclusively better than the strongest simple baseline.
- The v2.3 corrected H2 result is small (+0.028 recall) and sensitive to analysis choices; the budget-family and abstention sensitivity checks are not significant after correction.
- The redundancy penalty and cost-awareness terms were inactive in the audited folds; those ablations are not valid tests of component value.
- Pairwise-similarity features show a strong contribution in the reported ablation, so describe this as a finding about the current benchmark/pipeline, not a general guarantee.
- Treat exploratory analyses and QA-proxy results as such.

## Large artifacts

GitHub rejects ordinary Git files larger than 100 MB. The original `results.zip` is about 135 MB and contains the benchmark dataset, feature cache, and experiment outputs; it must be stored using Git LFS or external artifact storage. Do not commit the benchmark dataset or cache as ordinary source files.
