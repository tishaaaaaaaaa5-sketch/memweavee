# Independent validation plan

This is a proposed protocol, not a report of a completed external replication.

## Why another benchmark is needed

The role-aware result is currently reported on one LongMemEval-S cleaned split. It is promising evidence-retrieval performance, but does not establish generalization to a different benchmark or conversation style.

## Candidate benchmark: LoCoMo

Evaluate the frozen role-aware scoring method on the LoCoMo long-conversation benchmark, subject to its current license and access terms.

Before running:
1. Verify benchmark version, license, source URL, and permitted use.
2. Record exact dataset revision and SHA-256.
3. Map examples to the same abstract task without using benchmark-specific labels as features.
4. Freeze the LongMemEval-trained model and preprocessing. Do not tune on LoCoMo test examples.
5. If feature-schema adaptation is required, define it using a separate development split and disclose it.

## Comparators

Compare the query-agnostic baseline, role-aware model trained on LongMemEval only, simple recency baseline, and a frequency/importance heuristic where inputs permit. All methods must use the same candidate-session pool and memory budget.

## Metrics

Primary: evidence recall at a fixed memory budget.

Secondary: Recall@1/@3/@5/@10, MRR, mean gold rank, budget utilization, retained word/token count, and end-to-end answer accuracy only if a fixed answer-generation and grading pipeline is implemented. Report word-count budget and tokenizer-based token budget separately.

## Leakage and uncertainty controls

- Split by conversation wherever benchmark structure permits; all questions from one conversation belong to one split.
- Fit preprocessing, feature selection, and hyperparameters on training/development data only.
- Use paired bootstrap intervals clustered by conversation/session.
- Report all benchmark subsets and exclusions.
- Publish privacy-safe per-example identifiers/ranks, not raw conversation text or answers unless the license permits it.

## Acceptance criteria

A cross-benchmark generalization claim requires the frozen LongMemEval-trained model to beat the predeclared baseline on the primary LoCoMo metric under the same budget, with uncertainty intervals and exclusions documented. If it fails, report the failure rather than tuning against the test set.

## Current status

No LoCoMo experiment has been run in this repository. The LongMemEval headline remains benchmark-specific until this protocol is completed.
