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

### Validation feasibility audit: source-session grouping

A deterministic 5-fold purge audit was run on the 235 DEV questions (seed 20261126). Each fold held out 47 questions; training initially contained 188. For each fold, every training question sharing at least one `haystack_session_id` with any validation question was removed.

| Fold | Validation | Training before purge | Purged | Retained | Retention |
|---|---:|---:|---:|---:|---:|
| 1 | 47 | 188 | 171 | 17 | 9.04% |
| 2 | 47 | 188 | 160 | 28 | 14.89% |
| 3 | 47 | 188 | 164 | 24 | 12.77% |
| 4 | 47 | 188 | 163 | 25 | 13.30% |
| 5 | 47 | 188 | 166 | 22 | 11.70% |

Across DEV, there are 10,140 unique source sessions: 9,125 occur in one question, 920 occur in two, 89 in three, and 6 in four. Despite most sessions being question-unique, shared-session links connect all 235 questions into one connected component. The five-fold purge retains only 9.04%–14.89% of training questions.

**Decision:** do not use this purged 5-fold procedure for model selection. Its training sets are too small to support a stable comparison. Do not replace it with ordinary random question-level CV and call that independent validation.

### Required next validation-design step

Before fitting or selecting any new configuration, inspect the benchmark schema and provenance to distinguish:

- the independent sampling unit (for example, the original conversation/person/task, if explicitly present);
- the retrieved haystack sessions attached to a question;
- candidate content hashes and other direct duplicate indicators.

The `haystack_session_ids` overlap graph may describe shared retrieval context rather than the benchmark's independent sampling unit. Do not assume it is the correct fold-group key without verifying its semantics.

Then choose and document a defensible design based on fields actually present:

1. If a genuine independent source-group field exists and yields viable groups, use deterministic grouped folds on that field, with candidate-hash overlap exclusion and train-only preprocessing.
2. If no viable independent grouping exists, keep DEV as a development set, avoid claims of independent cross-validation, and obtain a new independent conversation-level/external confirmation set before confirmatory claims.
3. Report the number of groups, group-size distribution, fold sizes, and retained training counts before running any model.
4. Apply the same 10% word-count proxy budget and stable ranking policy only after the validation design is approved.
5. Keep the existing TEST set for historical comparability and diagnostics; do not use it to choose features, thresholds, or hyperparameters.

No configuration is selected by this document. The next decision is about the correct independent sampling unit, not another model run.

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
