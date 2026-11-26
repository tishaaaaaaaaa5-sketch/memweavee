# Notebook index

This directory contains the canonical notebook sequence for MemWeave. The project has two related but distinct result stages; consult the corresponding result documentation before comparing metrics.

| Order | Canonical file | Role | Output status |
|---|---|---|---|
| 00 | `00_MemWeave_2_0.ipynb` | Initial real-data pipeline and early comparisons | Historical notebook |
| 01 | `01_MemWeave_2_1.ipynb` | Fair-baseline and benchmark-structure audit | Executed copy with saved outputs |
| 02 | `02_MemWeave_2_2.ipynb` | Revised model selection, tuning, external and QA analyses | Source notebook; outputs preserved separately under `../results/v2_2/` |
| 03 | `03_memweave_v2_3_addendum.ipynb` | Corrected inference and component/evidence-limit audit | Addendum; reads saved outputs |
| 04 | `04_MemWeave_Final.ipynb` | Leak-controlled evaluation workflow and role-aware locked-test follow-up | Source notebook |
| 04e | `04_MemWeave_Final_Executed.ipynb` | Executed record of the final locked-test and paired statistical audit | 94 executed code cells; final audit outputs retained; debug conversation outputs removed |
| 05 | `05_MemWeave_Kaggle_Followup.ipynb` | Stage C recovery, feature ablation, and frozen LoCoMo transfer follow-up | Executed Kaggle record; corrected artifact audit retained; raw dataset text is not exported |
| 06 | `06_Stage_BC_Controlled_Reconciliation.ipynb` | 2×2×2 factorial reconstruction of Stage B/C role-feature scaling, vocabulary cap, and message-filter differences | Executed once; original seven exports were produced. The additional candidate-level retention trace was added afterward and requires rerunning the final export cell to produce the eighth CSV. |

## Current role-aware evaluation

The final follow-up compares a baseline feature set with the same baseline plus six message-role-aware features. It uses `same_pipeline`, logistic regression (`C=0.3`), a 10% word-count budget proxy, 235 DEV questions and 235 held-out TEST questions. Exact OOF score reconstruction passed for both variants before test evaluation.

The held-out budgeted evidence recall was 0.4042 (baseline) and 0.7094 (role-aware), a paired gain of 0.3052 (95% question-level bootstrap CI [0.252979, 0.359574]). See [the full audit summary](../results/final_locked_test/README.md) and [aggregated category table](../results/final_locked_test/question_type_breakdown.csv).

The Stage C Kaggle notebook is a separate follow-up record; its regenerated results must not be conflated with the historical Stage B run. The executed notebook is a record of the run, not a guarantee that its external dataset can still be fetched unchanged. See [`data_provenance.md`](../results/final_locked_test/data_provenance.md) for the missing per-question export and checksum limitations.

## Stage B/C reconciliation — latest results

Notebook 06 reconstructs both endpoint configurations in one controlled factorial run. The primary factorial endpoint finds +12.68 pp for z-score scaling vs raw and +1.56 pp for the 20,000-feature cap vs unlimited vocabulary; the scale × cap interaction is not established. The message filter retained all 65,288 audited messages and had zero observed effect in this population.

The direct paired comparison on 235 TEST questions reports Stage B-like mean budgeted evidence recall 0.709433 and Stage C-like 0.820638: **+11.121 pp** (95% paired-bootstrap CI [+7.099, +15.411] pp). Stage C-like was better on 39 questions, Stage B-like on 8, with 188 ties (exact paired sign-test p=5.5396×10⁻⁶). This analysis reused existing run metrics; no training or experiment rerun was performed.

See the [full reconciliation report](../results/stage_bc_reconciliation/README.md). This controlled reconstruction does not prove which code state generated the historical Stage B and Stage C artifacts; historical headline metrics remain unchanged. Evidence recall is not answer accuracy.

## Recommended execution

1. Read the [project guide](../README.md) and the relevant result notes.
2. Run historical v2.0–v2.2 notebooks only when reproducing those stages.
3. Run the v2.3 addendum against its saved artifacts; it is not a fresh training run.
4. Run the final notebook from a clean kernel and preserve its complete outputs, configuration, dataset checksums and per-question CSVs.
5. Run notebook 06 from a clean kernel after reviewing the dataset terms and explicitly confirming them in its environment variables. Preserve all eight reconciliation outputs after rerunning the updated export cell.
6. Before reporting any reconciliation result, inspect all eight factorial conditions; use DEV/CV—not TEST—to choose a canonical implementation.

## Reproducibility and limitations

The role-aware audit used 50,000 paired bootstrap resamples and 200,000 sign-flip permutations. Inference resamples questions rather than conversation clusters. The research process was iterative, not preregistered; the held-out test split is not an independent benchmark. Evidence recall does not establish improved LLM answer accuracy.

Benchmark JSONs, feature caches and raw per-question exports are not stored in this directory. Store large artifacts in Git LFS or an external artifact store after checking dataset terms.
