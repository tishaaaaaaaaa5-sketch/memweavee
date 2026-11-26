# LoCoMo End-to-End Reader QA: Corrected Exploratory Results

## Status

The initial reader QA comparison was withdrawn after an audit found that the question was truncated from all memory-method prompts. The reader prompt implementation was corrected to preserve the complete question, fit context into the remaining input budget, disable silent tokenizer truncation, and record post-packing diagnostics.

The corrected rerun completed successfully: 200 questions across 10 LoCoMo conversation clusters, with four methods and 800 generated answers.

## Run configuration

- Dataset: LoCoMo, 10 conversation clusters.
- Sample: 200 QA items, 20 per conversation.
- Reader: `google/flan-t5-small`, pinned revision `0fc9ddf78a1e988dac52e2dac162b0ede4fd74ab`.
- Device: CUDA.
- Reader input cap: 512 tokens.
- Generation: deterministic, up to 64 new tokens.
- Evaluation: exact match and token F1.
- Uncertainty: paired bootstrap resampling the 10 conversation clusters.

## Corrected results

| Method | n | Exact match | Token F1 | Mean selected memory tokens | Mean retrieved context tokens before packing | Mean reader context tokens after packing | Context truncation rate | Mean reader input tokens | Mean selected sessions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Baseline | 200 | 0.035 | 0.1015 | 1851.90 | 1470.925 | 459.220 | 1.00 | 511.990 | 3.500 |
| Question-only | 200 | 0.005 | 0.0467 | 0.00 | 0.000 | 0.000 | 0.00 | 42.770 | 0.000 |
| Recency | 200 | 0.010 | 0.0736 | 1814.40 | 1814.400 | 459.205 | 1.00 | 511.975 | 2.700 |
| Role-aware | 200 | 0.080 | 0.2057 | 1783.93 | 1760.120 | 459.205 | 1.00 | 511.975 | 2.505 |

Role-aware has the highest token F1 and exact match among the four tested methods. Its token-F1 point improvement is +0.1042 over baseline and +0.1321 over recency. Its exact-match point improvement over baseline is +0.045.

## Paired conversation-cluster bootstrap

| Contrast | Delta | 95% CI | Clusters |
|---|---:|---:|---:|
| Role-aware − baseline token F1 | +0.104149 | [+0.050744, +0.158614] | 10 |
| Role-aware − baseline exact match | +0.045000 | [+0.010000, +0.085000] | 10 |
| Role-aware − recency token F1 | +0.132081 | [+0.081263, +0.176543] | 10 |
| Baseline − question-only token F1 | +0.054822 | [+0.017291, +0.099166] | 10 |

All three reported role-aware comparison intervals exclude zero. The baseline also exceeds question-only on token F1 in this sample, with the reported interval excluding zero. These are cluster-bootstrap intervals over only ten conversations; they should be interpreted cautiously and do not substitute for evaluation on more independent conversations.

## Prompt-budget diagnostics and interpretation

- The corrected prompt builder preserves the question and answer marker, packs a context prefix into the remaining 512-token input budget, and raises an error if the question/instructions alone cannot fit.
- The generation tokenizer call disables truncation and asserts that the batched input length does not exceed 512 tokens.
- The reported context truncation rate is 1.00 for all three memory methods: every retrieved context was shortened to fit the fixed reader input budget. This is expected under the observed context lengths, but it means the experiment compares selectors after a second-stage context-packing operation.
- Mean post-packing context length is nearly identical across memory methods (about 459 tokens), and mean total reader input length is about 512 tokens. This makes the reader's consumed input budgets comparable across those methods.
- The tokenizer emitted a warning about a 680-token sequence exceeding the model's nominal maximum. The corrected generation path disables silent truncation and asserts that actual batched model inputs fit within 512 tokens. The warning can arise while measuring/encoding a longer candidate before packing; the successful full generation and input-length assertion are the relevant safeguards. Retain the per-prompt input-length audit in future runs.
- The question-only method has no memory context and uses substantially fewer input tokens (mean 42.77), so it is a useful no-memory control but not a matched-token-budget competitor.

## Interpretation limits

1. The corrected result is promising evidence that role-aware selection improves this FLAN-T5-small reader's answers relative to baseline and recency on this sampled LoCoMo set. It is not yet a general claim about answer quality across readers or datasets.
2. Only 10 conversation clusters were sampled. Cluster bootstrap intervals based on ten clusters are inherently uncertain.
3. The sample contains 200 questions (20 per conversation), not all LoCoMo questions.
4. Exact match and token F1 are lexical metrics. They do not fully measure semantic correctness, factual grounding, hallucination, or answer completeness.
5. All memory methods undergo context packing because retrieved contexts exceed the reader window. The ordering and content of the packed prefix may affect what survives; future work should report retention of gold evidence after packing.
6. The earlier initial run is invalid and withdrawn; do not pool its scores with this corrected run.

## Decision and next steps

Retain role-aware selection as the leading candidate for further downstream QA evaluation. The corrected result is materially stronger than the invalid initial comparison and supports continued investigation, but not a definitive superiority claim.

Next:
- Audit all 800 generated prompt records for preserved question suffixes and input lengths <=512.
- Measure gold-evidence retention after context packing, by method.
- Repeat with more independent conversations and preferably a second reader model.
- Keep reader model revision, sample, prompt template, context budget, and decoding settings fixed for paired comparisons.
- Preserve the per-question output, summary, bootstrap JSON, and manifest as run artifacts; do not claim those raw outputs are committed unless they are separately uploaded.
