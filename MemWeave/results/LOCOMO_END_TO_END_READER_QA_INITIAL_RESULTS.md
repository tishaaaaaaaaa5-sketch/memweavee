# LoCoMo End-to-End Reader QA: Initial Exploratory Results

## Run configuration

- Dataset: LoCoMo, 10 conversation clusters.
- Sample: 200 QA items, 20 per conversation.
- Reader: `google/flan-t5-small`, pinned revision `0fc9ddf78a1e988dac52e2dac162b0ede4fd74ab`.
- Device: CUDA.
- Generated outputs: 800 answers across four methods.
- Evaluation: exact match and token-level F1.
- Uncertainty: paired bootstrap over the 10 conversation clusters.

## Results

| Method | n | Exact match | Token F1 | Mean memory tokens | Mean reader-context tokens | Mean selected sessions |
|---|---:|---:|---:|---:|---:|---:|
| Baseline | 200 | 0.000 | 0.0264 | 1851.90 | 1470.925 | 3.500 |
| Question-only | 200 | 0.005 | 0.0467 | 0.00 | 0.000 | 0.000 |
| Recency | 200 | 0.000 | 0.0273 | 1814.40 | 1814.400 | 2.700 |
| Role-aware | 200 | 0.000 | 0.0408 | 1783.93 | 1760.120 | 2.505 |

### Paired conversation-cluster bootstrap

| Contrast | Token-F1 delta | 95% CI |
|---|---:|---:|
| Role-aware − baseline | +0.014400 | [+0.004270, +0.025263] |
| Role-aware − recency | +0.013565 | [+0.001615, +0.026583] |
| Baseline − question-only | −0.020241 | [−0.044152, +0.000404] |

The role-aware method improves token F1 over both the baseline and recency in this sample; both reported cluster-bootstrap intervals exclude zero. Question-only has the highest point estimate (0.0467), so role-aware is not the best-performing method overall in this run. The baseline-versus-question-only interval crosses zero. Exact match is zero for baseline, recency, and role-aware, and 0.005 for question-only; therefore the positive role-aware result is partial token overlap, not exact answer correctness.

## Critical implementation caveat: 512-token reader input cap

The run emitted a tokenizer warning for a sequence of 680 tokens exceeding the model's nominal 512-token maximum. The committed evaluation cell subsequently tokenizes generation prompts with `truncation=True` and `max_length=READER_INPUT_MAX_TOKENS` (512). Thus the warning did not prevent the run from generating all 800 answers, but the reader did not necessarily see the full selected context. The logged `mean_reader_context_tokens` measures context before prompt tokenization/truncation, not the number of context tokens actually consumed by the model.

This creates an important evaluation limitation: selector methods can differ in context length and ordering, while the reader sees at most 512 prompt tokens. The current numbers should be treated as results under a 512-token prompt cap, not as a clean comparison of the full selected memories. Before making a stronger claim, run a controlled follow-up that explicitly measures post-truncation context tokens and applies a consistent context-packing policy that preserves the question and allocates the same usable context budget to each method. Record truncation rates and the fraction of selected context retained.

## Interpretation and limitations

- This is an exploratory sample of 200 questions from only 10 LoCoMo conversations; the conversation-cluster bootstrap has just 10 clusters and should be interpreted cautiously.
- The reader is FLAN-T5-small, so results are reader- and prompt-dependent.
- Exact match is near zero across methods; token F1 is a weak lexical-overlap metric and does not establish semantic correctness or factual faithfulness.
- The QA sample is not an independent benchmark confirmation and should not be conflated with the separate selector-transfer/evidence-recall results.
- The run is completed and its outputs were written under `/kaggle/working/memweave_followup_outputs/locomo_reader_qa`; raw per-question outputs are not included here.

## Decision

Keep role-aware selection as a promising candidate: it beats baseline and recency on token F1 in this exploratory run. Do not claim overall superiority because question-only has a higher point estimate, exact-match performance is essentially zero, and the 512-token truncation means the full selected contexts were not necessarily consumed. Prioritize a context-budget-controlled rerun with post-truncation diagnostics before treating this as a headline answer-quality result.
