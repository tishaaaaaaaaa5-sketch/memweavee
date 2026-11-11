# MemWeave results

Results are versioned by research stage. Do not merge the headline numbers across stages: v2.0–v2.3 and the role-aware follow-up use distinct experimental comparisons and should be interpreted separately.

## v2.0 historical baseline

`v2_0/` contains curated outputs and the original run manifest from the initial pipeline. These are historical results, not the current role-aware headline.

## v2.1 benchmark audit

`v2_1/` contains feature-AUC and nearest-neighbour diagnostics. These analyses motivate the later benchmark-shortcut and evidence-clustering discussion.

## v2.2 main run

`v2_2/` contains the 500-question run findings, manifest, primary Setting A/B tables, ablation/category/evidence-group tables, efficiency measurements and LoCoMo summaries. The v2.2 H2/H3 narrative is superseded by the v2.3 corrected-inference analysis.

## v2.3 corrected inference

The folder root contains the corrected-inference summary; `tables/` contains the curated comparisons and sensitivity analyses. The original learned-selector edge over `low_novelty` was small (+0.028 recall) and sensitivity-dependent. It should not be described as robust superiority.

## Final role-aware locked-test follow-up

`final_locked_test/` documents the separate role-aware feature experiment. On 235 held-out `same_pipeline` questions at a 10% word-count budget:
- Baseline budgeted evidence recall: 0.404184.
- Role-aware budgeted evidence recall: 0.709433.
- Paired mean improvement: +0.305248 (30.52 percentage points).
- Paired question-level bootstrap 95% CI: [0.252979, 0.359574].
- Exact paired sign test: p = 5.1055e-25 (96 positive, 3 negative, 136 ties).
- Sign-flip Monte Carlo p = 5.0e-6 using 200,000 permutations and plus-one correction; this is the Monte Carlo resolution, so report p ≤ 0.000005.
- Gold rank improved for 127 questions, worsened for 3, and was unchanged for 105.

The feature matrix reconstruction reproduced both OOF score sets exactly (maximum absolute score error 0.0). Both variants used logistic regression with C=0.3 and 4,216/5,523 training rows after the content-overlap filter.

### Question-type breakdown

See `final_locked_test/question_type_breakdown.csv`. Five of six categories have Holm-adjusted exact sign-test p-values below 0.05. The single-session-preference category is inconclusive (n=15; Holm p=0.25).

### Interpretation limits

The result is from one held-out split of one benchmark. The development process was iterative, not preregistered. The bootstrap resamples questions, not conversation clusters; cluster dependence remains a limitation. The role-aware bundle has not been fully ablated, so category gains do not identify causal feature contributions. Evidence recall is not answer correctness. The 10% budget is based on word count as a proxy, not exact tokenizer tokens.

## Provenance and large artifacts

Raw benchmark JSONs, feature caches and large per-question exports are intentionally excluded from ordinary Git history. Store large artifacts in Git LFS or an external artifact host and publish checksums and dataset terms. The uploaded executed notebook used for the latest audit is not silently represented as committed notebook output; the committed notebook remains the source workflow and the aggregate results are captured here.
