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


### Novelty-aware DEV follow-up

The self-contained DEV experiment in Notebook 06 rebuilt its five grouped folds without relying on missing prior-kernel CV variables. Its result does not support the tested novelty blends: relevance-only recall was 0.4049; 90/10 relevance/novelty was 0.4060 with a paired interval crossing zero; stronger novelty weights reduced recall. See the [novelty experiment report](../results/stage_bc_reconciliation/NOVELTY_AWARE_DEV_EXPERIMENT.md). Do not treat this exploratory DEV result as independent confirmation.


### Constrained novelty tie-breaker (DEV-only)

The notebook now includes a predeclared follow-up that keeps relevance primary and uses novelty only to order candidates within fixed 5-percentile relevance bands. It reuses the self-contained five-fold answer-session grouped DEV protocol, fold-local feature construction, candidate-hash overlap exclusion, frozen logistic ranker, 10% word-count proxy budget, and paired group bootstrap. It does not read TEST.

Run the final notebook cell titled **“Constrained novelty tie-breaker (DEV-only; relevance remains primary)”** after the preceding self-contained novelty DEV experiment cell. Outputs are written to `memweave_followup_outputs/constrained_novelty_tiebreaker_dev/`. The completed DEV run produced recall 0.4049 for relevance-only and 0.4028 for the constrained tie-breaker; paired delta -0.0021 (95% group-bootstrap CI [-0.0086, +0.0043]). The interval crosses zero, so retain relevance-only and do not promote the tie-breaker. See the [results report](../results/stage_bc_reconciliation/CONSTRAINED_NOVELTY_TIEBREAKER_RESULTS.md). This is exploratory DEV evidence, not independent confirmation.


### End-to-end reader QA (new; pending execution)

Notebook 05 now adds an end-to-end reader evaluation after the existing LoCoMo selector-transfer cell. Run the notebook through its final three cells to install the reader dependencies and execute the fixed FLAN-T5-small evaluation. It compares frozen role-aware, baseline, and recency selectors under an exact 10% reader-tokenizer storage budget, with a question-only control. The deterministic sample is up to 20 answerable, evidence-annotated questions per each of the ten LoCoMo conversations. It reports exact match, token F1, and paired conversation-cluster bootstrap intervals. Outputs are saved under memweave_followup_outputs/locomo_reader_qa/.

This is exploratory: LoCoMo has already been used for selector-transfer analysis, and ten clusters provide limited inferential power. Do not describe it as independent replication or as validation of the proposed MFAR controller. See the [protocol](../results/followup_2026/END_TO_END_READER_QA_PROTOCOL.md).

## Consolidated Kaggle execution snapshot — archive only

An executed consolidated Kaggle workbench is preserved at [`archive/06_MemWeave_Consolidated_Kaggle_Execution_2026-11-26.ipynb`](archive/06_MemWeave_Consolidated_Kaggle_Execution_2026-11-26.ipynb). It contains 88 cells (78 executed; 74 cells with outputs) and combines the Stage B/C workflow with later trace assembly, reader QA, Long-MT-Bench+, and ablation/debug work.

This is an **archive-only execution snapshot**, not a replacement for canonical Notebook 06. Cell 85 contains the corrected LongMemEval role-feature ablation; cells 83–84 are superseded intermediate code/results, cell 79's Long-MT-Bench+ feature ablation errored, and cell 86 is diagnostic only. Do not treat every saved cell output as a valid experiment. The accompanying ZIP is stored in [`results/artifacts/2026-11-26/`](../results/artifacts/2026-11-26/); its release checks remain pending. See the [artifact organization audit](../docs/ARTIFACT_ORGANIZATION_AUDIT_2026-11-27.md).

## Status correction for downstream QA

The “End-to-end reader QA (new; pending execution)” section above is historical. The corrected LoCoMo reader-QA experiments have since completed with evidence-aware span packing for both FLAN-T5-small and FLAN-T5-base, and the corrected Long-MT-Bench+ span-budget evaluation has completed. Use the dated reports in `../results/` for their metrics and limitations; do not rerun these completed experiments merely to update this index.
