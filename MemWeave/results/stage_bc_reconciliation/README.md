# Stage B/C controlled reconciliation — interim results

**Status:** controlled reconstruction and paired endpoint analysis completed; historical artifact provenance remains unresolved.  
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

## Paired factorial main effects — supplementary candidate-level metric

The reported effects are paired across the same 235 questions. Effects are expressed in percentage points (pp) of the per-question fraction of selected candidates labelled gold, averaged over the other factorial dimensions.

| Factor | Contrast | Questions | Mean effect (pp) | Paired bootstrap 95% CI (pp) |
|---|---|---:|---:|---:|
| Feature scaling | z-score minus raw | 235 | **+7.482** | [+4.504, +10.532] |
| Vocabulary cap | 20,000 minus unlimited | 235 | **+1.064** | [+0.496, +1.702] |
| Message filtering | filtered minus all messages | 235 | **0.000** | [0.000, 0.000] |

For each of the four scale × vocabulary-cap combinations, filtered and unfiltered outputs were identical for all 235 questions (235/235). This is an observed equivalence in this dataset population, not a general claim about filtering.

## Descriptive candidate-selection reference

The baseline candidate trace selected 541 candidates (2.302 per question); 192 were labelled gold (35.49%). Across the factorial configurations:

- Raw scaling, 20,000 cap: 306 gold among 539 selected (56.77%).
- Raw scaling, unlimited vocabulary: 297 gold among 537 selected (55.31%).
- Z-score scaling, 20,000 cap: 340 gold among 539 selected (63.08%).
- Z-score scaling, unlimited vocabulary: 338 gold among 541 selected (62.48%).

These are candidate-selection gold fractions, not evidence recall, retrieval success, QA accuracy, or end-to-end answer correctness. The baseline is an additional reference configuration, not a ninth factorial cell.

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

## Message-filtering population audit

A read-only audit of the 5,458 candidate sessions across all 235 TEST questions examined 65,288 messages:

- 65,288/65,288 already had a role of user or assistant.
- 65,288/65,288 had non-empty content after stripping whitespace.
- No role-case changes were counted.
- 37 messages had leading or trailing whitespace.
- All 65,288 messages entered the role-grouped population in both the raw and filtered paths.

This explains the exact zero filtering effect on this population: the filter retained every message. The 37 whitespace-only boundary changes do not ordinarily affect TF-IDF tokenization. This result is specific to the audited population.

## Direct Stage B-like versus Stage C-like endpoint comparison

A further read-only paired comparison directly contrasted the two endpoint configurations on the same 235 TEST questions, using the already-computed `RUNS` metrics. No model training or experiment rerun was performed.

- **Stage B-like:** `scale=raw|cap=20000|filtered=False`
- **Stage C-like:** `scale=zscore|cap=none|filtered=True`

| Measure | Result |
|---|---:|
| Stage B-like mean budgeted evidence recall | 0.709433 (70.943%) |
| Stage C-like mean budgeted evidence recall | 0.820638 (82.064%) |
| Paired mean improvement (C-like − B-like) | **+0.111206 (+11.121 pp)** |
| Paired question-level bootstrap 95% CI | **[+7.099, +15.411] pp** |
| Questions where C-like was better | 39 |
| Questions where B-like was better | 8 |
| Ties | 188 |
| Exact paired sign-test p-value (ties excluded) | **5.5396 × 10⁻⁶** |

The direct endpoint contrast supports a higher mean budgeted evidence recall for the Stage C-like configuration in this controlled reconstruction. The direction counts show that most questions tie; the aggregate improvement is driven by the subset with non-zero differences, where C-like wins substantially more often than B-like.

This direct comparison is consistent with the factorial findings: z-score scaling is the dominant positive factor, the 20,000 cap has a smaller positive main effect, and filtering is a no-op on this audited message population. The endpoint contrast combines these factor changes and any interactions; it should not be interpreted as the effect of scaling alone.

## Integrated interpretation and claim boundaries

1. Z-score scaling is the dominant improvement on the primary evidence-recall endpoint.
2. A 20,000-feature vocabulary cap provides a smaller positive improvement.
3. Message filtering is redundant for the audited candidate-session population.
4. The scale × cap interaction is not established by its bootstrap interval.
5. The direct Stage C-like endpoint has +11.12 pp mean recall over the Stage B-like endpoint on the paired TEST questions.

These findings identify configuration effects in a controlled reconstruction. They do **not** prove which implementation generated the historical Stage B or Stage C artifacts, nor do they establish the historical discrepancy's cause. Keep historical Stage B and Stage C headline metrics unchanged.

Do not describe candidate-gold fraction or budgeted evidence recall as answer accuracy. Do not pool these results with Stage A, historical Stage B, or regenerated Stage C headline results. The retention traces have `not_evaluated` outcomes and no retrieval/answer traces; no downstream QA claim is supported.
