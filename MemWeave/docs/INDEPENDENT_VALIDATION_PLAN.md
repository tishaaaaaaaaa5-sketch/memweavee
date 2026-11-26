# Independent validation plan

This is a prospective protocol. No new benchmark result is claimed in this document.

## Why this is needed

The current role-aware result is a held-out evaluation on one LongMemEval-S split. It is promising, but it does not establish generalization to a different benchmark, dataset construction process or conversation distribution.

## Proposed external benchmark

Use **LoCoMo** as the first external evaluation, subject to its license and task-format compatibility. Preserve the benchmark's official conversation/question split and do not merge its scores with LongMemEval-S.

A second independent benchmark may be added after the first pipeline is stable. Keep each benchmark's metrics and sample counts separate.

## Evaluation design

1. Freeze the current baseline feature set, six role-aware features, logistic-regression hyperparameter and retention budget before external evaluation.
2. Implement a benchmark adapter that maps the external dataset into the same session/message schema without using answer labels to construct features.
3. Define evidence relevance and gold-session matching using the benchmark's official annotations or a documented, manually audited mapping.
4. Split by conversation, not by question, wherever multiple questions refer to the same conversation.
5. Fit all learned feature weights and thresholds on training/development conversations only.
6. Keep the external test conversations untouched until the pipeline and scoring rules are frozen.
7. Compare the same baseline and role-aware systems on identical questions and identical memory budgets.

## Metrics

Report:
- budgeted evidence recall at 5%, 10% and 20% of the memory budget;
- Recall@1, @3, @5 and @10;
- MRR and mean/median gold rank;
- end-to-end answer accuracy only if a separately validated answer-generation/evaluation pipeline is included;
- runtime and retained-memory size.

Use the benchmark's recommended evaluation protocol where it differs from the internal LongMemEval-S protocol, and explain the difference.

## Statistical analysis

Use paired question-level comparisons, but account for shared-conversation dependence with a conversation-cluster bootstrap. Report the number of conversations and questions, confidence intervals, and the exact permutation/bootstrap procedure. Correct for multiple comparisons when reporting several budgets or question categories.

## Feature attribution

Ablate the six role-aware features individually and in prespecified groups. Treat these as diagnostic experiments; do not infer causal explanations from the bundle comparison alone.

## Data governance and reproducibility

- Follow the dataset's license and access conditions.
- Do not commit raw private or restricted conversation text.
- Record source URL, dataset release/version, split, preprocessing code commit and checksums.
- Publish aggregate results and privacy-preserving per-question identifiers only where permitted.
- Preserve the exact notebook/script, package lock, random seeds and run manifest.

## Reporting rule

A positive external result should be described as replication only if the task, data split, baseline, scoring rule and budget are independently implemented and the test set was not used for feature or threshold selection. If the benchmark adapter changes the task definition, describe it as an external evaluation rather than a direct replication.
