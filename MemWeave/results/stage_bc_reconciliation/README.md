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

## Primary endpoint versus candidate-level supplement

The canonical Notebook 06 factorial analysis (cell 13 in the committed notebook source) operates on `RUNS[name]["metrics"][q]["recall"]`, i.e. per-question **budgeted evidence recall**. It computes all seven factorial terms: the three main effects, three two-way interactions, and the three-way interaction, with 20,000 paired question-level bootstrap resamples. That is the primary endpoint for the controlled reconciliation and must be interpreted before drawing conclusions about the historical Stage B/C gap.

The gold-fraction results in this report are a separate, supplementary audit derived from `stage_bc_candidate_trace.csv`. They measure the fraction of selected candidates labelled gold; they are not the notebook's primary evidence-recall endpoint. Do not substitute these candidate-level effects for the canonical `factorial_effects` output.

The notebook's feature-construction code also clarifies the filtering switch: the filtered path lowercases roles and removes messages whose role is not user/assistant or whose content is empty after stripping whitespace. The unfiltered path keeps all messages and their raw role/content strings. The exact equality in candidate-level outcomes therefore warrants a direct audit of role casing, blank content, and non-user/assistant messages in the candidate-session population before attributing the equality to a no-op filter.


## Primary factorial endpoint: budgeted evidence recall

The canonical Notebook 06 factorial analysis uses per-question budgeted evidence recall as its primary endpoint. The reported effects use the notebook's conventional (2^3) factorial coding and 20,000 paired question-level bootstrap resamples.

| Factorial term | Effect on evidence recall | Paired bootstrap 95% CI | Interpretation |
|---|---:|---:|---|
| Feature scaling (z-score vs raw) | **+0.126809** (+12.68 pp) | [+0.086596, +0.169007] | Positive main effect; interval excludes zero |
| Vocabulary cap (unlimited vs 20,000) | **−0.015603** (−1.56 pp) | [−0.026241, −0.006738] | Unlimited vocabulary is worse; equivalently, the 20,000 cap improves recall |
| Message filtering (filtered vs all) | 0.000000 | [0.000000, 0.000000] | No effect in this candidate population |
| Scale × vocabulary cap | +0.009220 (+0.92 pp) | [−0.000355, +0.019504] | Interval crosses zero; interaction not established |
| Scale × filtering | 0.000000 | [0.000000, 0.000000] | No observed interaction |
| Vocabulary cap × filtering | 0.000000 | [0.000000, 0.000000] | No observed interaction |
| Three-way interaction | 0.000000 | [0.000000, 0.000000] | No observed interaction |

**Factor coding matters:** the notebook codes `vocab_cap=None` (unlimited) as +1 and `vocab_cap=20000` as −1. Thus the negative `vocab_cap` effect means unlimited vocabulary reduces recall; the equivalent 20,000-cap contrast is +1.56 pp.

### Message-filtering population audit

A read-only audit of the 5,458 candidate sessions across all 235 TEST questions examined 65,288 messages:

- 65,288/65,288 already had a role of user or assistant.
- 65,288/65,288 had non-empty content after stripping whitespace.
- No role-case changes were counted.
- 37 messages had leading or trailing whitespace.
- All 65,288 messages entered the role-grouped population in both the raw and filtered paths.

This explains the exact zero filtering effect on this population: the filter retained every message. The 37 whitespace-only boundary changes do not ordinarily affect TF-IDF tokenization. The result is dataset/population-specific and does not show that filtering is generally useless.

## Integrated interpretation

The primary endpoint and the supplementary candidate-level analysis agree on the direction of the main effects:

1. Z-score scaling is the dominant improvement.
2. A 20,000-feature vocabulary cap provides a smaller positive improvement.
3. Message filtering is redundant for the audited candidate-session population.
4. The scale × cap interaction is not established by the paired bootstrap interval.

The primary evidence-recall effect for scaling (+12.68 pp) is distinct from the supplementary +7.482 pp effect on selected-candidate gold fraction. They are different metrics and must not be conflated.

## Historical discrepancy: status

These findings identify which switches alter outcomes in a controlled reconstruction. They make scaling and vocabulary capping plausible contributors to the historical Stage B/Stage C difference, but they do not prove that either switch caused the historical discrepancy. That would require the original execution states/artifacts or an independently reproducible reconstruction of both historical pipelines. Keep the Stage B and Stage C historical headline results unchanged.
