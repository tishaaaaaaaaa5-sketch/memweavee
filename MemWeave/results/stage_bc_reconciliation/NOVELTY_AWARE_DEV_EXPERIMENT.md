# Novelty-aware retention experiment (DEV)

**Status:** executed; exploratory results do not support the tested novelty blends  
**Notebook:** `notebooks/06_Stage_BC_Controlled_Reconciliation.ipynb`  
**Split:** 235 DEV questions; TEST not used  
**Evaluation:** five-fold GroupKFold by connected components of shared answer-session IDs  
**Budget:** 10% word-count proxy  
**Primary endpoint:** out-of-fold budgeted evidence recall

## Protocol

The experiment compared a canonical base-feature relevance ranker with fixed convex blends of its within-question relevance percentile and a novelty percentile. Novelty was the within-question z-scored value of one minus maximum pairwise TF-IDF similarity. Tested relevance/novelty weights were 100/0, 90/10, 75/25 and 50/50.

Each fold fitted IDF on training candidate sessions after excluding candidate hashes present in that fold's validation questions. Logistic regression used frozen `C=0.3` and balanced class weights. The 10% word-count proxy budget was held fixed. Paired intervals used 5,000 bootstrap resamples of answer-session connected components, with identical resamples across blend settings.

All five folds contained 47 validation questions. The 235 DEV questions formed 233 answer-session connected components. This grouping is a provisional dependence control, not proof of independent sampling units.

## Results

| Relevance weight | Novelty weight | Mean OOF evidence recall | Paired delta vs relevance-only | Paired 95% CI |
|---:|---:|---:|---:|---:|
| 1.00 | 0.00 | **0.4049** | reference | reference |
| 0.90 | 0.10 | 0.4060 | +0.0011 | [-0.0159, +0.0191] |
| 0.75 | 0.25 | 0.3727 | -0.0322 | [-0.0643, -0.0004] |
| 0.50 | 0.50 | 0.1833 | -0.2216 | [-0.2879, -0.1554] |

| Relevance / novelty | Selected evidence precision | Budget utilization | Mean selected novelty percentile |
|---|---:|---:|---:|
| 100 / 0 | 0.3351 | 0.8856 | 0.1654 |
| 90 / 10 | 0.3277 | 0.8869 | 0.1815 |
| 75 / 25 | 0.2851 | 0.8821 | 0.2701 |
| 50 / 50 | 0.0837 | 0.8770 | 0.7729 |

## Interpretation and decision

- The 90/10 blend's +0.11 percentage-point point estimate is negligible; its paired interval crosses zero. No improvement is established.
- The 75/25 blend reduces recall by 3.22 percentage points; its paired interval is below zero.
- The 50/50 blend reduces recall by 22.16 percentage points and sharply lowers selected evidence precision.
- Higher novelty weight increases selected novelty percentile, but this does not translate into better evidence retention.

**Decision:** retain relevance-only ranking as the reference configuration. Do not promote these novelty blends into the canonical pipeline. This rejects the tested fixed percentile blends at these weights; it does not prove that all diversity-aware or redundancy-aware methods are ineffective.

## Limitations and next step

This is exploratory DEV evaluation on one benchmark split, not independent confirmation. The answer-session grouping is only a provisional dependence proxy, and the cost unit is a word-count proxy rather than exact tokenizer tokens. The tested novelty feature is a single maximum-similarity statistic; coverage-aware selection, evidence-conditioned diversity, provenance, and risk were not evaluated.

Do not continue sweeping the same blend weights. If diversity is revisited, test a constrained tie-breaker that only reorders near-tied high-relevance candidates, using the same folds, budget and paired group bootstrap. Otherwise freeze relevance-only and proceed to the next unresolved research objective.

## Artifact note

The Kaggle run reported outputs under `/kaggle/working/memweave_followup_outputs/novelty_aware_dev_experiment/`. The aggregate results above are transcribed from the run output supplied for this report. Per-question CSV, fold assignments and JSON manifest were not available as files to this GitHub update and are not represented as committed artifacts.
