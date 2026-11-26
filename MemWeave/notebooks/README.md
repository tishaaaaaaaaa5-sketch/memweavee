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

## Stage B/C reconciliation (new)

Notebook 06 reconstructs both historical feature-construction endpoints inside one controlled run: raw vs within-question z-scored role features; 20,000-feature cap vs unlimited vocabulary; and all-message vs filtered user/assistant messages. It holds the pinned LongMemEval source, DEV/TEST split, base features, logistic regression settings, overlap exclusion, and 10% word-count proxy budget constant. It evaluates all eight factorial combinations, reports paired per-question effects and interactions, and exports feature diagnostics, per-question metrics, selection traces, a run manifest, and a privacy-minimised candidate-level retention trace. The updated export cell also records the candidate CSV SHA-256 in the manifest. The controlled reconstruction run supplied seven original exports; the separately generated candidate trace was uploaded later and is checked against an audit-enriched companion manifest. The existing run results are described separately in the reconciliation notes; no new result is inferred from the added export code.

## Latest controlled reconciliation status

The first paired factorial main-effect analysis is recorded in [the Stage B/C reconciliation report](../results/stage_bc_reconciliation/README.md). Z-score scaling and the 20,000-term cap have positive effects on candidate-selection gold fraction; message filtering is observationally identical across the 235-question test set. The scale × cap interaction and the cause of filtering equivalence are the next analyses. No answer-quality claim is supported by these candidate traces.

## Latest Stage B/C reconciliation findings

The primary Notebook 06 factorial endpoint is budgeted evidence recall. Z-score scaling improves it by 12.68 pp (95% paired-bootstrap CI [+8.66, +16.90] pp), and the 20,000-feature cap improves it by 1.56 pp versus unlimited vocabulary (95% CI [+0.67, +2.62] pp). The scale × cap interaction is not established. The filtering audit found that all 65,288 candidate-session messages already passed the filter, explaining its zero effect on this population. See the [full reconciliation report](../results/stage_bc_reconciliation/README.md). These findings do not establish the cause of the historical Stage B/C discrepancy.

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
