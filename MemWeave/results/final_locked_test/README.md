# Final role-aware locked-test audit

## Executive summary

This report documents the role-aware follow-up experiment in the executed `MemWeave-Final` notebook. It is a separate experimental stage from the v2.3 corrected-inference comparison with `low_novelty`.

On 235 held-out questions in the `same_pipeline` pool, adding six message-role-aware features to the baseline feature set increased 10%-budget evidence recall from 0.404184 to 0.709433. The paired improvement was 0.305248 (30.52 percentage points), with a question-level paired bootstrap 95% confidence interval of [0.252979, 0.359574].

This is a promising held-out result on one LongMemEval-S split. It does not establish independent-benchmark generalization, causal attribution to individual role features, or improved end-to-end answer accuracy.

## Frozen evaluation configuration

| Item | Value |
|---|---|
| Dataset | LongMemEval-S cleaned |
| Pool | `same_pipeline` |
| DEV questions | 235 |
| TEST questions | 235 |
| TEST abstention handling | Abstention questions excluded |
| Model | LogisticRegression |
| Regularization | `C = 0.3` |
| Baseline feature indices | `[0, 1, 7, 8, 9]` |
| Augmented features | Baseline plus indices `[10, 11, 12, 13, 14, 15]` |
| Training rows retained | 4,216 / 5,523 for each model |
| Selection budget | 10% of pool word count |
| OOF reconstruction | Passed exactly; maximum absolute score error 0.0 for both models |
| Paired bootstrap | 50,000 resamples; seed 20261112 |
| Sign-flip permutation | 200,000 permutations; seed 20261113; plus-one correction |
| Category bootstrap | 20,000 resamples per category |
| Holm correction | Across six question-type sign tests |

The notebook describes the 10% budget as a word-count proxy. It should not be called an exact tokenizer-based token budget.

## Overall held-out metrics

| Metric | Baseline | Role-aware | Difference |
|---|---:|---:|---:|
| Budgeted evidence recall | 0.404184 | 0.709433 | +0.305248 |
| Recall@1 | 0.4255 | 0.8000 | +0.3745 |
| Recall@3 | 0.6128 | 0.8979 | +0.2851 |
| Recall@5 | 0.7064 | 0.9447 | +0.2383 |
| Recall@10 | 0.8000 | 0.9702 | +0.1702 |
| MRR | 0.5486 | 0.8546 | +0.3060 |
| Mean gold rank | 5.8553 | 1.9277 | -3.9277 |
| Median gold rank | 2 | 1 | -1 |

## Paired statistical inference

The per-question budgeted-recall differences yielded:
- Mean paired gain: 0.305248.
- Paired bootstrap 95% CI: [0.252979, 0.359574].
- Sign-flip permutation Monte Carlo p-value: 0.000004999975 (200,000 draws plus-one correction). This is the minimum reportable value at this Monte Carlo resolution; report as **p ≤ 0.000005**, not as an exact p-value.
- Exact paired sign test: p = 5.1055e-25.
- Positive / negative / tied question-level differences: 96 / 3 / 136.

The distinct gold-rank direction audit found 127 improved, 3 worsened and 105 unchanged questions; its exact sign-test p-value was 5.3819e-34. Do not conflate this rank-direction test with the budgeted-recall sign test.

## Question-type results

| Question type | n | Baseline | Role-aware | Gain | Holm sign-test p |
|---|---:|---:|---:|---:|---:|
| Knowledge update | 36 | 0.4444 | 0.8333 | +0.3889 | 0.000015 |
| Multi-session | 61 | 0.5290 | 0.7186 | +0.1896 | 0.000363 |
| Single-session assistant | 28 | 0.6786 | 0.9286 | +0.2500 | 0.031250 |
| Single-session preference | 15 | 0.0000 | 0.2000 | +0.2000 | 0.250000 |
| Single-session user | 32 | 0.0625 | 0.6875 | +0.6250 | 0.000010 |
| Temporal reasoning | 63 | 0.4082 | 0.6648 | +0.2566 | 0.000001 |

The largest absolute gain was in single-session-user questions (+62.50 pp), followed by knowledge-update questions (+38.89 pp). The preference subgroup is inconclusive and small (n=15). These are subgroup associations, not causal explanations of which individual features drove the overall gain.

## What is verified

1. Both models were evaluated on the same 235 TEST questions.
2. The baseline and role-aware feature matrices were reconstructed.
3. OOF reproduction passed with maximum absolute score error 0.0 for both variants.
4. The original feature matrices were restored after the test evaluation.
5. The statistical audit ran on the saved per-question locked-test results and did not retrain or tune on TEST.

## Limitations and reporting cautions

- **Single benchmark/split:** DEV and TEST are from the same LongMemEval-S benchmark. This is not independent external replication.
- **Iterative research process:** the overall project evolved through iterative development. The locked test was held out for this evaluation, but the research process was not preregistered.
- **Conversation dependence:** the bootstrap resamples questions. If questions share source conversations, independence may be imperfect. A conversation-cluster bootstrap is a useful sensitivity analysis if conversation IDs are available.
- **Feature attribution:** the six role-aware features were evaluated as a bundle. Complete feature ablations are needed before attributing gains to particular features.
- **Outcome scope:** evidence recall and rank are retrieval/retention metrics, not end-to-end LLM answer accuracy.
- **Subgroup uncertainty:** the preference category contains only 15 questions and is not statistically conclusive.
- **Budget definition:** the notebook uses word count as a proxy for tokens.
- **External validation:** this report does not claim that the new role-aware model has independently replicated on LoCoMo or another benchmark.

## Reproduction artifacts

The executed notebook writes the following audit outputs in the Kaggle working environment:
- `memweave_role_aware_locked_test.csv`
- `memweave_role_aware_question_type_audit.csv`
- `memweave_role_aware_audit_manifest.json`

These raw files are not included in this repository update. The committed report and CSV contain aggregate values transcribed from the executed notebook output. Preserve the raw per-question files and their checksums with the research release before making a full reproducibility claim.
