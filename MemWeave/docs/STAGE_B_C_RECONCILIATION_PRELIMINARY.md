# Stage B / Stage C Reconciliation — Preliminary Code Audit

**Status:** Preliminary source-code comparison; no causal attribution yet  
**Purpose:** Explain why two historical role-aware runs on the same nominal benchmark/split report materially different evidence recall.

## 1. Observed discrepancy

The repository reports two distinct runs:

| Run | Baseline evidence recall | Role-aware evidence recall | Gain |
|---|---:|---:|---:|
| Stage B | 0.4042 | 0.7094 | +0.3052 |
| Stage C | 0.404184 | 0.820638 | +0.416454 |

Both reports describe 235 DEV / 235 TEST questions, the `same_pipeline` pool, logistic regression with `C=0.3`, and a 10% word-count proxy budget. The runs must not be pooled or silently substituted.

The near-identical baseline but different augmented score makes role-feature construction and/or its integration the first audit target. This is a clue, not proof of cause.

## 2. Code paths inspected

- Stage B: `MemWeave/notebooks/04_MemWeave_Final_Executed.ipynb`, especially cells 97, 99, 105, 106, and 107. Cell 106 is labelled “CORRECTED ROLE-AWARE LOCKED TEST” and says it reconstructs the original Experiment 1 feature construction.
- Stage C: `MemWeave/notebooks/05_MemWeave_Kaggle_Followup.ipynb`, especially cells 8, 10, 12, 15, and 19. Cell 8 loads the canonical source notebook at pinned commit `d642215226fa2a9204bb6d64c4ff0f6447920274`.

## 3. Concrete implementation differences

| Detail | Stage B corrected locked-test cell 106 | Stage C role-feature cell 10 |
|---|---|---|
| TF-IDF configuration | `lowercase=True`, `stop_words="english"`, bigrams, sublinear TF, `max_features=20000` | `stop_words="english"`, bigrams, sublinear TF; no explicit `max_features` |
| Message inclusion | Appends every message's content and role from each candidate session | Strips text and filters to non-empty messages with role in user/assistant |
| Role feature aggregation | User/assistant max similarity and top-3 mean, plus log message counts | Same six conceptual features |
| Feature scaling | Cell 106 explicitly says “no normalization”; appends raw role features | Standardises the six added features within each question |
| Candidate alignment | Maps candidate hash to row and session ID; checks mapping | Maps candidate hash to row and session ID; constructs aligned arrays |
| Classifier | Logistic regression, `C=0.3`, balanced classes | Logistic regression, `C=0.3`, balanced classes |
| Budget | 10% of word-count cost | 10% of word-count cost |

There are earlier exploratory Stage B cells (e.g. cell 105) that standardise role features, but cell 106 is explicitly labelled as the corrected locked-test path and uses raw features. The reconciliation must identify the exact executed path and saved outputs, not select a cell based on its title alone.

## 4. Plausible explanations to test

1. **Feature scaling:** Stage B raw message-level TF-IDF similarities/counts versus Stage C per-question standardisation changes the scale relative to the five baseline features.
2. **Vocabulary cap:** Stage B limits the per-question TF-IDF vocabulary to 20,000 features; Stage C leaves the vocabulary uncapped.
3. **Message filtering:** Stage C excludes empty messages and unsupported roles before vectorisation; Stage B's corrected cell includes message contents from all roles and counts only exact user/assistant labels.
4. **Feature reconstruction / execution lineage:** The notebook contains exploratory and corrected cells. The saved result must be tied to the precise executed cell sequence, source notebook commit, and raw input checksums.
5. **Potential interactions:** Any one difference may interact with the others and with the per-question feature scaling of the baseline matrix.

No item above is yet established as the cause.

## 5. Required controlled reconciliation experiment

Use the same pinned LongMemEval file, same 235/235 question split, same `same_pipeline` pool, same base features, same candidate ordering, same DEV-only training, same content-overlap exclusion, same classifier, same selection policy, and same budget.

Run a predeclared factorial reconstruction:

- A: Stage B feature construction exactly as in cell 106.
- B: Stage C feature construction exactly as in cell 10.
- C: Stage B construction with only feature scaling changed to Stage C scaling.
- D: Stage B construction with only the vocabulary cap changed.
- E: Stage B construction with only message filtering changed.
- F: Stage C construction with each Stage B choice changed individually.
- G: Full cross of the three identified implementation switches if computationally feasible.

For each variant, save:
- per-question six-dimensional role-feature vectors (privacy-safe candidate IDs only);
- feature means, standard deviations, sparsity and vocabulary sizes;
- prediction scores and selected candidate indices;
- exact selected cost and budget cap;
- per-question evidence recall and rank;
- code/config/data checksums.

Compare per-question score differences, rank changes, selected-set overlap, evidence recall, and paired confidence intervals. Use the question as a paired unit for within-benchmark comparisons; conversation-cluster inference is additionally required where the benchmark's independent unit is conversation.

## 6. Acceptance criteria

The discrepancy is reconciled only when:
1. both historical paths are reproducible from pinned inputs, or an irrecoverable artifact gap is explicitly documented;
2. the controlled switches identify which code differences change predictions and metrics;
3. the Stage B and Stage C result tables can be regenerated from their declared configurations;
4. one canonical implementation is selected for future experiments based on a documented methodological rationale, not on which result is larger;
5. all historical results remain preserved and separately labelled.

## 7. Current conclusion

The source audit identifies concrete differences in role-feature scaling, TF-IDF vocabulary capping, and message filtering. These are plausible contributors to the gap between 0.7094 and 0.8206 role-aware evidence recall. The available inspection does not establish causality. A controlled reconstruction is required before either result is treated as the canonical estimate.
