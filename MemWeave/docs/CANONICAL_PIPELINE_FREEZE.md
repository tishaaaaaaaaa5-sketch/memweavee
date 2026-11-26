# Canonical MemWeave pipeline freeze protocol

**Status:** protocol drafted; canonical feature configuration not yet frozen  
**Branch:** `research/memweave-followup-release`  
**Purpose:** establish a development-only selection procedure before implementing the next memory-selection method.

## 1. Why this phase exists

The Stage B/C controlled reconstruction has established that implementation choices materially affect budgeted evidence recall. It does not justify choosing a configuration by its TEST score.

The 235-question TEST set used in the Stage B/C analysis has now been inspected repeatedly. It is therefore **not an untouched confirmatory test set for the next algorithm**. We will not use it to select features, thresholds, hyperparameters, or controller policies.

## 2. Frozen reference pipeline

The following elements are the starting reference, not claims that every setting has already passed development-only selection.

| Component | Reference specification | Freeze status |
|---|---|---|
| Dataset | LongMemEval-S cleaned, pinned revision and checksum recorded in run manifests | Dataset identity fixed for this phase |
| Pool | `same_pipeline` | Fixed |
| Split | Existing 235 DEV / 235 TEST split | Existing split retained for historical comparability; TEST is no longer considered untouched |
| Base features | Feature indices `[0, 1, 7, 8, 9]` from the canonical feature matrix | Fixed reference |
| Role-aware features | Six features: user max/top-3 mean similarity; assistant max/top-3 mean similarity; log user/assistant message counts | Fixed reference bundle |
| Classifier | `LogisticRegression(C=0.3, class_weight="balanced", max_iter=500)` | Fixed reference model |
| Candidate order | Stable deterministic ordering for tied scores | Fixed |
| Selection | Rank candidates by model score; take candidates in order subject to budget | Fixed reference policy |
| Budget | 10% of pool word-count cost | Fixed proxy; not exact tokenizer tokens |
| Leakage control | Exclude candidate hashes overlapping TEST from DEV training, matching the existing pipeline | Retain and independently test |
| Primary outcome | Per-question budgeted evidence recall | Fixed for selection-stage comparisons |

The baseline and role-aware reference results remain separately attributed to their original runs. Do not silently replace historical metrics with regenerated numbers.

## 3. Settings that must be selected on DEV only

The controlled factorial identified feature scaling and vocabulary cap as consequential. Because their TEST effects have already been observed, the next configuration decision must be made without using those TEST outcomes.

Evaluate the eight existing combinations on DEV using cross-validation:

- scaling: raw / within-question z-score;
- TF-IDF vocabulary cap: 20,000 / unlimited;
- message filter: all messages / valid non-empty user and assistant messages.

### Required validation procedure

1. Create deterministic folds using the strongest available independent grouping unit (conversation or source-conversation cluster), not random candidate rows.
2. For each fold, fit the classifier and all learned preprocessing on training folds only.
3. Apply the same overlap-exclusion rule within each fold: no candidate content hash may cross from validation into training.
4. Apply the identical 10% word-count proxy budget and stable ranking policy.
5. Aggregate out-of-fold per-question budgeted evidence recall.
6. Report mean, paired fold/question differences, uncertainty intervals, and cost/budget utilization for all eight configurations.
7. If reliable conversation grouping is unavailable, document the limitation and use a conservative grouped proxy; do not describe question-level CV as independent conversation-level validation.
8. Select one configuration using a predeclared rule, not the maximum of a single noisy point estimate.

### Predeclared selection rule

Use the following rule unless a deviation is justified and recorded before examining results:

- Primary criterion: highest mean out-of-fold budgeted evidence recall.
- Stability: prefer a simpler or lower-cost configuration when its score is within one standard error of the best.
- Feasibility: reject configurations with invalid feature values, unstable fitting, leakage, or material budget-accounting failures.
- Filtering: if the population audit again confirms exact equivalence, retain the simpler path and document the population-specific reason.
- Record the complete comparison, including negative and tied results.

No configuration is selected by this document. The DEV-only analysis must produce the evidence first.

## 4. Confirmatory evaluation after the freeze

Because the existing TEST set has been repeatedly inspected, it may be used only for historical comparability and diagnostics, not as the final untouched confirmation of the new algorithm.

Before making a confirmatory claim for the new method:

- identify a new held-out set of independent conversations or a suitable external benchmark;
- pin the dataset version and checksum;
- freeze the method, thresholds, and primary outcomes before evaluating that set;
- use conversation-clustered paired inference where the sampling design requires it;
- report evidence recall separately from answer quality.

Do not tune on the new confirmation set. If no suitable independent set is available, report the work as development-stage evidence and state that limitation explicitly.

## 5. Next algorithm: budgeted evidence-aware selection

Once the reference pipeline is frozen, implement the proposed selection method as a separate policy, leaving the reference baseline unchanged.

For query (q), candidate memory units (i \in C_q), binary selection variables (x_i\), costs (c_i\), and budget (B_q\), define a transparent objective:

\[
\max_{x_i\in\{0,1\}}
\left[
\sum_i x_i u_i(q)
+ \alpha\,\mathrm{Coverage}(S,q)
- \beta\,\mathrm{Redundancy}(S)
- \gamma\,\mathrm{Risk}(S,q)
\right]
\quad
\text{subject to } \sum_i c_i x_i \le B_q,
\]

where (S=\{i:x_i=1\}).

- (u_i(q)): calibrated relevance/evidence utility from the frozen reference model.
- (mathrm{Coverage}(S,q)): coverage of distinct query requirements, entities, relations, temporal constraints, or evidence facets.
- (mathrm{Redundancy}(S)): overlap among selected units, defined independently of relevance.
- (mathrm{Risk}(S,q)): explicit penalties for stale, contradictory, low-confidence, or provenance-deficient items.

All terms, normalization, and weights must be specified operationally. The initial method should use a deterministic, interpretable greedy or submodular-style selection procedure. Parameters (alpha,\beta,\gamma) are development-set parameters and must not be tuned on TEST.

The exact form of coverage and risk must be grounded in fields that the real benchmark/pipeline actually exposes. Missing provenance or lifecycle traces must be marked unobserved; they must not be fabricated or inferred from the current retention-only export.

## 6. Core experiments after the freeze

Compare under identical data, costs, and answer/evidence evaluation:

1. Frozen score-ranked reference policy.
2. Relevance utility only.
3. Relevance + coverage.
4. Relevance + redundancy penalty.
5. Full relevance + coverage + redundancy policy.
6. Full policy without role-aware features.
7. Full policy across multiple budget fractions.
8. Random and simple heuristic baselines, where appropriate.

Primary selection-stage endpoint: budgeted evidence recall. Secondary endpoints: evidence precision, evidence-set coverage, redundancy, rank, and budget utilization. End-to-end answer quality is a separate evaluation and requires actual answer traces and a fixed answer-generation protocol.

## 7. Reproducibility requirements

Every run must record:

- source commit and notebook hash;
- dataset revision and checksum;
- split and fold assignments (privacy-safe identifiers);
- feature names, preprocessing fit scope, and configuration;
- classifier and all hyperparameters;
- overlap exclusions and counts;
- cost definition and budget;
- random seeds and package versions;
- per-question out-of-fold predictions and metrics using privacy-safe IDs;
- selection traces and aggregate results;
- deviations, warnings, failed runs, and exclusions.

## 8. Decision gate

The canonical pipeline is considered frozen only after:

- DEV-only grouped validation has been completed;
- leakage and overlap checks pass;
- all eight configurations are reported;
- the selection rule is applied and the chosen configuration is justified;
- a machine-readable manifest and source commit are recorded.

Until then, refer to the current configuration as the **reference pipeline**, not the final canonical pipeline.
