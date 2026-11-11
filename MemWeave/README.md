# MemWeave research project

MemWeave investigates how to retain useful conversational sessions under a constrained memory budget. The repository contains two related but distinct research stages: the original query-agnostic retention study (v2.0–v2.3) and a later role-aware feature experiment evaluated on a held-out test split.

## Research stages

### Stage A — Original retention study (v2.0–v2.3)

- Benchmark: LongMemEval-S cleaned, 500 questions in the reported study.
- Primary task: query-agnostic session retention.
- Primary metric: session-level evidence recall.
- The v2.3 corrected-inference addendum found a small, sensitivity-dependent advantage over the strongest simple rule. Read `../results/findings_v2_3.txt`; do not describe that result as robust superiority.
- External LoCoMo and downstream QA-proxy results are reported separately and have their own limitations.

### Stage B — Role-aware follow-up (final locked-test audit)

- Pool: `same_pipeline`.
- Split: 235 DEV / 235 locked TEST questions; abstention questions excluded.
- Model: logistic regression, `C = 0.3`.
- Comparison: baseline feature set vs. baseline plus six message-role-aware features.
- Budget: 10% of pool word count (a proxy, not exact tokenization).
- Held-out budgeted evidence recall: 0.4042 baseline vs. 0.7094 role-aware (+0.3052).
- Paired bootstrap 95% CI: [0.252979, 0.359574].
- Exact paired sign test: p = 5.11e-25; sign-flip Monte Carlo p = 5e-6 at 200,000 permutations.
- OOF reconstruction was exact for both variants before locked-test scoring.

The follow-up result is not a replacement for the v2.3 result: it is a separate feature experiment and evaluation. See [the final locked-test report](results/final_locked_test/README.md).

## Canonical notebook sequence

See [the notebook index](notebooks/README.md).

1. `notebooks/00_MemWeave_2_0.ipynb` — initial real-data pipeline.
2. `notebooks/01_MemWeave_2_1.ipynb` — fair-baseline and benchmark-structure audit.
3. `notebooks/02_MemWeave_2_2.ipynb` — revised tuning, inference, external and QA analyses.
4. `notebooks/03_memweave_v2_3_addendum.ipynb` — corrected inference and evidence-limit addendum.
5. `notebooks/04_MemWeave_Final.ipynb` — leak-controlled final evaluation workflow and role-aware follow-up audit cells.

## Reproduction

Use Python in Jupyter or Google Colab. Run from a clean kernel and preserve:
- exact notebook version and execution outputs;
- dataset names, source URLs and SHA-256 checksums;
- Python and package versions;
- split seed, model parameters and selection budget;
- per-question result CSVs and statistical audit outputs.

The final role-aware audit uses 50,000 question-level paired bootstrap resamples and 200,000 sign-flip permutations. Its question-level inference is not conversation-clustered.

## Data and large files

Raw benchmark JSONs, feature caches and large per-question exports are not stored in this source tree. Keep data outside Git unless licensing and size have been reviewed. For large reproducibility artifacts, use Git LFS or a stable artifact host and record checksums.

## Reporting guidance

Distinguish evidence retention from answer accuracy, the original v2.3 experiment from the role-aware follow-up, and a held-out split from independent replication. The research process was iterative rather than preregistered. Do not claim that the six role-aware features have individually established causal effects.
