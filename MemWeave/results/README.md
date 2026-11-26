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

## Stage B/C controlled reconciliation

The controlled Notebook 06 factorial reconstruction and its direct endpoint comparison are documented in [the Stage B/C reconciliation report](stage_bc_reconciliation/README.md).

Primary budgeted evidence-recall factorial results:
- Z-score vs raw scaling: **+12.68 pp** (95% paired-bootstrap CI [+8.66, +16.90] pp).
- 20,000-feature cap vs unlimited: **+1.56 pp** (95% CI [+0.67, +2.62] pp).
- Scale × cap interaction is not established; message filtering retained all 65,288 audited messages and had zero observed effect.

Direct paired endpoint comparison on the same 235 TEST questions:
- Stage B-like mean recall: 0.709433; Stage C-like: 0.820638.
- C-like paired improvement: **+11.121 pp** (95% paired bootstrap CI [+7.099, +15.411] pp).
- C-like better on 39 questions, B-like better on 8, 188 ties; exact paired sign-test p=5.5396×10⁻⁶.

This is a controlled reconstruction, not proof of which implementation generated historical Stage B or Stage C artifacts. Historical headline results remain unchanged. Candidate-selection gold fraction, budgeted evidence recall, and answer accuracy are distinct metrics.


## Novelty-aware DEV follow-up

The fixed relevance/novelty blend experiment in Notebook 06 did not establish a benefit from novelty weighting. On 235 DEV questions with five answer-session-grouped folds, relevance-only achieved 0.4049 OOF budgeted evidence recall. A 90/10 relevance/novelty blend achieved 0.4060, but its paired group-bootstrap 95% CI versus relevance-only was [-0.0159, +0.0191]. The 75/25 and 50/50 blends reduced recall to 0.3727 and 0.1833. **Keep relevance-only as the reference; do not promote these tested novelty blends.** See [the experiment report](stage_bc_reconciliation/NOVELTY_AWARE_DEV_EXPERIMENT.md). This is exploratory DEV evidence, not independent confirmation.


### Next experiment: constrained novelty tie-breaker

The unconstrained novelty blends did not establish a benefit. A predeclared relevance-first tie-breaker experiment is now implemented in notebook 06; novelty can reorder candidates only within 5-percentile relevance bands. See [the protocol](stage_bc_reconciliation/CONSTRAINED_NOVELTY_TIEBREAKER_PROTOCOL.md). The completed DEV run found relevance-only recall of 0.4049 and constrained tie-breaker recall of 0.4028. The paired delta was -0.0021 (95% group-bootstrap CI [-0.0086, +0.0043]), crossing zero. **Retain relevance-only; do not promote the tie-breaker.** See the [results report](stage_bc_reconciliation/CONSTRAINED_NOVELTY_TIEBREAKER_RESULTS.md). This remains exploratory DEV evidence, not independent confirmation.


## LoCoMo end-to-end reader QA (corrected exploratory run)

The corrected 200-question FLAN-T5-small evaluation passed a post-run audit: all 800 prompts (200 per method) preserve the complete question and fit within the 512-token reader limit. Role-aware selection achieved token F1 **0.2057** and exact match **0.080**, versus baseline 0.1015 / 0.035 and recency 0.0736 / 0.010. Paired 10-conversation cluster-bootstrap deltas were +0.1041 token F1 versus baseline (95% CI [+0.0507, +0.1586]) and +0.1321 versus recency (95% CI [+0.0813, +0.1765]); role-aware exact-match delta versus baseline was +0.0450 (95% CI [+0.0100, +0.0850]). This is promising but exploratory evidence from only 10 conversation clusters. All memory contexts were shortened to fit the 512-token input cap, so post-packing gold-evidence retention should be audited. The invalid first run remains withdrawn. See [the corrected QA report](LOCOMO_END_TO_END_READER_QA_INITIAL_RESULTS.md).


### Whole-session packing follow-up

Notebook 05 Cell 24 completed a paired 200-question (10-conversation) comparison of prefix packing and greedy complete-session packing with the same FLAN-T5-small reader and 512-token input cap. Whole-session token F1 was 0.0424 baseline, 0.0366 recency, and 0.0486 role-aware, versus prefix-packed scores of 0.1015, 0.0736, and 0.2057 respectively. Question-only remained 0.0467 in both conditions. Whole-session packing reduced token F1 for all memory methods in this configuration. Role-aware retrieved-gold recall remained 0.6727, but packed-gold recall was only 0.0192, with a mean of 0.21 complete sessions packed. This points to a context-packing bottleneck, not a failure of role-aware ranking. The whole-session input lengths were not budget-matched across methods, and the result is exploratory with only 10 conversation clusters. **Do not replace prefix packing with this whole-session strategy.** See the [full reader QA and packing report](LOCOMO_END_TO_END_READER_QA_INITIAL_RESULTS.md).


The prefix-versus-whole-session paired cluster bootstrap (20,000 replicates over 10 LoCoMo conversations) found whole-session token-F1 declines for baseline (-0.0591; 95% CI [-0.0987, -0.0307]), recency (-0.0370; [-0.0630, -0.0118]), and role-aware (-0.1571; [-0.2004, -0.1105]). Role-aware exact match also declined by 0.0700 ([-0.1000, -0.0400]). These remain exploratory intervals from 10 clusters. A FLAN-T5-base second-reader load was initiated, but no second-reader QA metrics are yet available. See the full report for details.


### Consolidated follow-up: second reader and budget audit

The FLAN-T5-base second-reader run completed 800/800 generations on the 200-question, 10-conversation sample using whole-session packing. Token F1 was 0.0307 baseline, 0.0057 question-only, 0.0331 recency, and 0.0272 role-aware; thus the role-aware lead from the FLAN-T5-small prefix-packed run did not replicate in this condition. Reader and packing policy are confounded across those runs, so this is not an isolated reader-size comparison. The lexical answer-context overlap proxy (role-aware mean 0.6940) is not semantic grounding or entailment. Exact tokenizer audit confirmed all reader inputs within 512 tokens and equal selected-memory token counts/budget caps across prefix and whole-session runs. Dataset inventory: 1,536 eligible questions, 200 sampled, 1,336 additional, but still only 10 independent conversation clusters. Next: cross both reader models with both packing strategies on the same questions and obtain an independent dataset. See the [full report](LOCOMO_END_TO_END_READER_QA_INITIAL_RESULTS.md).
