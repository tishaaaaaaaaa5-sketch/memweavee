# Notebook index

This directory contains the canonical notebook sequence for MemWeave. The project has two related but distinct result stages; consult the corresponding result documentation before comparing metrics.

| Order | Canonical file | Role | Output status |
|---|---|---|---|
| 00 | `00_MemWeave_2_0.ipynb` | Initial real-data pipeline and early comparisons | Historical notebook |
| 01 | `01_MemWeave_2_1.ipynb` | Fair-baseline and benchmark-structure audit | Executed copy with saved outputs |
| 02 | `02_MemWeave_2_2.ipynb` | Revised model selection, tuning, external and QA analyses | Source notebook; outputs preserved separately under `../results/v2_2/` |
| 03 | `03_memweave_v2_3_addendum.ipynb` | Corrected inference and component/evidence-limit audit | Addendum; reads saved outputs |
| 04 | `04_MemWeave_Final.ipynb` | Leak-controlled evaluation workflow and role-aware locked-test follow-up | Committed source notebook; aggregate locked-test outputs documented under `../results/final_locked_test/` |

## Current role-aware evaluation

The final follow-up compares a baseline feature set with the same baseline plus six message-role-aware features. It uses `same_pipeline`, logistic regression (`C=0.3`), a 10% word-count budget proxy, 235 DEV questions and 235 held-out TEST questions. Exact OOF score reconstruction passed for both variants before test evaluation.

The held-out budgeted evidence recall was 0.4042 (baseline) and 0.7094 (role-aware), a paired gain of 0.3052 (95% question-level bootstrap CI [0.252979, 0.359574]). See [the full audit summary](../results/final_locked_test/README.md) and [aggregated category table](../results/final_locked_test/question_type_breakdown.csv).

## Recommended execution

1. Read the [project guide](../README.md) and the relevant result notes.
2. Run historical v2.0–v2.2 notebooks only when reproducing those stages.
3. Run the v2.3 addendum against its saved artifacts; it is not a fresh training run.
4. Run the final notebook from a clean kernel and preserve its complete outputs, configuration, dataset checksums and per-question CSVs.
5. Before reporting the role-aware result, verify OOF reconstruction and confirm that no test data are used for tuning.

## Reproducibility and limitations

The role-aware audit used 50,000 paired bootstrap resamples and 200,000 sign-flip permutations. Inference resamples questions rather than conversation clusters. The research process was iterative, not preregistered; the held-out test split is not an independent benchmark. Evidence recall does not establish improved LLM answer accuracy.

Benchmark JSONs, feature caches and raw per-question exports are not stored in this directory. Store large artifacts in Git LFS or an external artifact store after checking dataset terms.
