# Constrained Novelty Tie-Breaker — DEV Results

**Status:** Completed; no evidence of improvement over relevance-only.  
**Evaluation:** Exploratory five-fold grouped cross-validation on DEV only. TEST was not read.

## Outcome

The predeclared constrained novelty tie-breaker completed on 235 DEV questions across 233 answer-session connected-component groups. Fold validation sizes were 47 questions each.

| Method | Mean OOF budgeted evidence recall | Group-bootstrap SE | Group-bootstrap 95% CI | Selected evidence precision | Budget utilization | Selected novelty percentile | Selected relevance percentile |
|---|---:|---:|---:|---:|---:|---:|---:|
| Relevance-only | 0.4049 | 0.0273 | [0.3509, 0.4578] | 0.3351 | 0.8856 | 0.1654 | 0.9500 |
| Constrained novelty tie-breaker (5 pp bands) | 0.4028 | 0.0271 | [0.3495, 0.4556] | 0.3344 | 0.8846 | 0.1648 | 0.9503 |

### Paired comparison

| Comparison | Mean paired recall delta | Paired group-bootstrap 95% CI | Questions | Groups | Relevance band width |
|---|---:|---:|---:|---:|---:|
| Constrained novelty tie-breaker − relevance-only | -0.0021 | [-0.0086, +0.0043] | 235 | 233 | 0.05 |

The point estimate is -0.21 percentage points. The paired interval crosses zero, so the experiment does not establish either a reliable improvement or a reliable decrement. The secondary metrics are also effectively unchanged; selected novelty percentile did not increase.

## Decision

**Retain relevance-only as the reference selector. Do not promote the constrained novelty tie-breaker.** Together with the preceding unconstrained blend experiment, these results provide no empirical support for adding this tested novelty signal to the current budgeted selector.

This is a narrow negative/inconclusive finding about the tested feature, ranking rule, 5-percentile bands, dataset, and budget. It does not rule out other diversity or coverage methods. Do not tune the band width on this same DEV result and then present it as confirmatory.

## Protocol and limitations

The experiment used the predeclared 5-percentile relevance bands; novelty ordered candidates only within a band. It retained the frozen logistic ranker, fold-local TF-IDF feature construction, candidate-hash overlap exclusion, 10% word-count proxy budget, and paired bootstrap over answer-session connected components (5,000 replicates; seed 20261128). Gold labels were used for evaluation only. TEST was not accessed.

The 233 answer-session connected components are a provisional dependence-control proxy, not proof of independent sampling units. The budget is based on word-count proxy rather than exact tokenizer accounting. Evidence recall is not answer accuracy or downstream LLM answer quality. This is exploratory DEV evidence, not independent confirmation.

## Reproducibility artifacts

Kaggle output directory: `/kaggle/working/memweave_followup_outputs/constrained_novelty_tiebreaker_dev/`

- `constrained_tiebreaker_per_question.csv`
- `constrained_tiebreaker_summary.csv`
- `constrained_tiebreaker_paired_delta.csv`
- `constrained_tiebreaker_fold_audit.csv`
- `constrained_tiebreaker_fold_assignments.csv`
- `constrained_tiebreaker_manifest.json`

The aggregate values above were transcribed from the completed Kaggle output supplied for this run. Raw per-question artifacts remain in the Kaggle output directory and are not claimed to be committed to Git.
