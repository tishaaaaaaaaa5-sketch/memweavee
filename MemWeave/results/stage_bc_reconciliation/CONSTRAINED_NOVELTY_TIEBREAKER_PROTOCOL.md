# Constrained Novelty Tie-Breaker — Protocol

**Status:** Implemented in the notebook; awaiting Kaggle execution and results.  
**Evaluation split:** DEV only. TEST is not read.

## Motivation

The preceding unconstrained novelty-blend experiment did not establish a benefit. The 90/10 relevance/novelty blend had a paired recall delta of only +0.11 percentage points, with a 95% paired group-bootstrap interval crossing zero. Larger novelty weights reduced evidence recall. The next test therefore gives novelty a strictly subordinate role.

## Predeclared selection rule

1. Compute the frozen fold-specific relevance ranker score for every candidate.
2. Convert relevance scores to within-question percentiles.
3. Assign candidates to fixed 5-percentile relevance bands.
4. Process bands from highest to lowest relevance.
5. Within each band only, sort by novelty percentile descending. Relevance percentile and original candidate order are deterministic secondary tie-breakers.
6. Apply the same 10% word-count proxy budget and stable cost-feasibility selection used by the prior DEV experiment.

A candidate cannot cross a relevance-band boundary because of novelty. The primary setting is a 0.05 relevance-percentile band width; it is fixed before inspecting this experiment's outcomes.

## Comparator and evaluation

- Comparator: relevance-only ranking.
- Data: same 235-question DEV partition.
- Folds: same five-fold GroupKFold split based on connected components of shared answer-session IDs.
- Feature construction: fold-local hashing TF-IDF; canonical base features.
- Leakage control: exclude training candidate hashes that occur in the validation fold.
- Ranker: LogisticRegression with frozen C=0.3, class_weight='balanced', max_iter=500.
- Budget: 10% of candidate word-count proxy.
- Primary metric: out-of-fold budgeted evidence recall.
- Secondary metrics: selected evidence precision, budget utilization, selected novelty percentile, selected relevance percentile.
- Uncertainty: paired bootstrap of answer-session connected components, 5,000 replicates, seed 20261128.
- Gold labels are used only for evaluation, never for candidate selection.

## Output artifacts

The final notebook cell writes the following under `memweave_followup_outputs/constrained_novelty_tiebreaker_dev/`:

- `constrained_tiebreaker_per_question.csv`
- `constrained_tiebreaker_summary.csv`
- `constrained_tiebreaker_paired_delta.csv`
- `constrained_tiebreaker_fold_audit.csv`
- `constrained_tiebreaker_fold_assignments.csv`
- `constrained_tiebreaker_manifest.json`

## Interpretation guardrails

This is an exploratory DEV-only grouped cross-validation experiment, not independent confirmation. The answer-session connected-component grouping is a provisional dependence-control proxy, not proof of independent sampling units. The budget is a word-count proxy, not exact tokenizer accounting. Do not inspect or use TEST for this experiment. Do not claim a benefit unless the paired interval and practical effect support it; if the interval crosses zero, retain relevance-only as the reference and report the result as inconclusive.
