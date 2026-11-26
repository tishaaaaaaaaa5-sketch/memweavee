# Stage B/C controlled reconciliation — interim results

**Status:** controlled reconstruction completed; candidate-selection analysis in progress.  
**Notebook:** `notebooks/06_Stage_BC_Controlled_Reconciliation.ipynb`  
**Branch:** `research/memweave-followup-release`

## Purpose

This experiment reconstructs the three implementation differences under one pinned dataset and one controlled protocol:

1. Role-feature scaling: raw vs within-question z-score.
2. TF-IDF vocabulary cap: 20,000 vs unlimited.
3. Message population: all messages vs filtered non-empty user/assistant messages.

The design evaluates all eight factorial combinations while holding the dataset, deterministic split, classifier, overlap-exclusion rule, and memory budget constant. These results are a controlled reconstruction, not proof of which code state generated either historical Stage B or Stage C artifact.

## Existing artifact audit

The Kaggle working directory contained:

- `mfar_retention_traces.jsonl`: 2,115 valid schema-v0.2.0 records, 235 unique TEST queries across nine runs.
- `stage_bc_candidate_trace.csv`: 49,140 rows, nine variants, 235 unique query-content hashes.
- All 235 query-content hashes in the candidate trace matched the query hashes in the retention ledger.
- Every retention record has outcome status `not_evaluated`; retrieval traces and answer traces are unavailable. These files therefore support candidate/retention analysis, not answer-quality claims.

The candidate trace and retention ledger are Kaggle artifacts. They are not copied into this repository by this report.

## Paired factorial main effects

The reported effects are paired across the same 235 questions. Effects are expressed in percentage points (pp) of the per-question fraction of selected candidates labelled gold, averaged over the other factorial dimensions.

| Factor | Contrast | Questions | Mean effect (pp) | Paired bootstrap 95% CI (pp) |
|---|---|---:|---:|---:|
| Feature scaling | z-score minus raw | 235 | **+7.482** | [+4.504, +10.532] |
| Vocabulary cap | 20,000 minus unlimited | 235 | **+1.064** | [+0.496, +1.702] |
| Message filtering | filtered minus all messages | 235 | **0.000** | [0.000, 0.000] |

### Filtering equivalence

For each of the four scale × vocabulary-cap combinations, filtered and unfiltered outputs were identical for all 235 questions (235/235). This is an observed equivalence in the recorded candidate-selection outputs. It does not establish that filtering is generally ineffective or that the implementation is correct; the message population and filter path still need inspection.

## Descriptive candidate-selection reference

The baseline candidate trace selected 541 candidates (2.302 per question); 192 were labelled gold (35.49%). Across the factorial configurations:

- Raw scaling, 20,000 cap: 306 gold among 539 selected (56.77%).
- Raw scaling, unlimited vocabulary: 297 gold among 537 selected (55.31%).
- Z-score scaling, 20,000 cap: 340 gold among 539 selected (63.08%).
- Z-score scaling, unlimited vocabulary: 338 gold among 541 selected (62.48%).

These are candidate-selection gold fractions, not evidence recall, retrieval success, QA accuracy, or end-to-end answer correctness. The baseline is an additional reference configuration, not a ninth factorial cell.

## Interpretation

The strongest observed main effect is z-score scaling. The 20,000-term vocabulary cap has a smaller positive main effect. The message-filter switch produced no difference in the recorded outputs.

The confidence intervals for scaling and vocabulary capping are above zero under the reported paired bootstrap. This supports positive effects on the measured candidate-selection gold fraction in this reconstruction. It does not establish that these switches explain the historical Stage B/Stage C discrepancy.

## Remaining analysis

1. Estimate the scale × vocabulary-cap interaction using paired per-question differences-in-differences.
2. Inspect the notebook's message filtering implementation and count eligible/excluded messages to explain the exact filtered/unfiltered equivalence.
3. Preserve the analysis code, configuration, and run-manifest linkage for reproducibility.
4. Only after those checks, assess which implementation differences are plausible contributors to the historical discrepancy.

## Claim boundaries

- Do not describe these numbers as answer accuracy or QA recall.
- Do not pool them with Stage A (v2.0–v2.3), Stage B historical locked-test, or Stage C regenerated follow-up headline metrics.
- Do not claim the historical discrepancy is resolved.
- The 2,115-record MFAR retention audit is a distinct artifact from the candidate-level factorial trace; neither provides retrieval or answer-stage observations here.
