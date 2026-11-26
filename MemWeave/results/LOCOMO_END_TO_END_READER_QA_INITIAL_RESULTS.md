# LoCoMo End-to-End Reader QA: Initial Run Withdrawn After Prompt Audit

## Status

**The initial reader QA scores are invalid as a comparison of memory-assisted question answering and must not be used as evidence that role-aware selection improves answer quality.** A post-run prompt audit established that the question was completely truncated for every baseline, recency, and role-aware prompt (600/600), while all 200 question-only prompts retained the question.

The earlier reported scores and bootstrap intervals are preserved below for provenance only; they are withdrawn from substantive interpretation.

## Initial run configuration

- Dataset: LoCoMo, 10 conversation clusters.
- Sample: 200 QA items, 20 per conversation.
- Reader: `google/flan-t5-small`, pinned revision `0fc9ddf78a1e988dac52e2dac162b0ede4fd74ab`.
- Device: CUDA.
- Generated outputs: 800 answers across four methods.
- Input cap: 512 tokens, with silent right truncation in the initial implementation.

## Initial scores (withdrawn)

| Method | n | Exact match | Token F1 |
|---|---:|---:|---:|
| Baseline | 200 | 0.000 | 0.0264 |
| Question-only | 200 | 0.005 | 0.0467 |
| Recency | 200 | 0.000 | 0.0273 |
| Role-aware | 200 | 0.000 | 0.0408 |

Previously calculated paired cluster-bootstrap deltas (also withdrawn): role-aware minus baseline token F1 +0.014400 (95% CI [+0.004270, +0.025263]); role-aware minus recency +0.013565 (95% CI [+0.001615, +0.026583]). These statistics quantify the flawed prompt comparison and are not valid evidence of selector quality.

## Prompt audit: decisive failure

The audit inspected all 800 prompts and measured whether the question suffix survived the tokenizer's 512-token right-truncation behavior.

| Method | Prompts | Over 512 tokens | Question fully retained | Question completely truncated |
|---|---:|---:|---:|---:|
| Baseline | 200 | 200 | 0 | 200 |
| Question-only | 200 | 0 | 200 | 0 |
| Recency | 200 | 200 | 0 | 200 |
| Role-aware | 200 | 200 | 0 | 200 |

For the three memory methods, the context preceded the question and consumed the full input window. The reader therefore received no question. The question-only control was the only method that received its intended question. This invalidates all between-method answer-quality comparisons from this run.

## Corrective implementation committed

The reader QA cell has been patched to:
- reserve and preserve the complete question and answer marker;
- binary-search the longest context prefix that fits within the 512-token input cap;
- reject a question/instruction prefix that itself exceeds the cap;
- disable silent tokenizer truncation and assert the batched input remains within the cap;
- record per-prompt input length, post-packing context tokens, and whether context was shortened;
- include these diagnostics in the per-question export and method summary.

## Required rerun

Rerun the patched Notebook 05 Cell 23 from a clean QA run (the preceding frozen models and LoCoMo helper state can remain loaded). Do not reuse the old `generated`, `qa_results`, or summary tables as corrected results. Verify:
1. 800 prompts are generated and scored;
2. every prompt preserves the full question;
3. no model input exceeds 512 tokens;
4. context retained after packing and context-shortening rates are reported by method.

The corrected run will still be exploratory: 200 sampled questions from 10 conversation clusters, using FLAN-T5-small and token F1/exact match. A positive result would warrant further validation, not a claim of definitive answer-quality superiority.
