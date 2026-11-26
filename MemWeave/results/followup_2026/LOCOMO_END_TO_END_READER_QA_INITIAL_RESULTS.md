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
- A post-run audit of all 800 prompt records passed: all 800 preserve the complete question and answer suffix, and all 800 inputs are <=512 tokens. By method, each of baseline, recency, role-aware, and question-only has 200/200 preserved questions and 200/200 in-limit inputs; maximum input lengths were 512, 512, 512, and 61 tokens respectively. The tokenizer emitted a warning about a 680-token candidate during context packing, but no generated input exceeded the model limit.
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
- Completed: audit all 800 generated prompt records; 800/800 preserve the question and 800/800 fit within 512 tokens.
- Next: measure gold-evidence retention after context packing, by method.
- Repeat with more independent conversations and preferably a second reader model.
- Keep reader model revision, sample, prompt template, context budget, and decoding settings fixed for paired comparisons.
- Preserve the per-question output, summary, bootstrap JSON, and manifest as run artifacts; do not claim those raw outputs are committed unless they are separately uploaded.

## Gold-evidence retention after current prefix packing

A post-run diagnostic reconstructed retrieval and the exact 512-token prompt packing for the same 200 questions (600 memory-method rows; 10 conversation clusters). Results:

| Method | Mean retrieved-gold recall | Mean full-session packed-gold recall | Mean partial packed-gold recall | Questions with any gold retrieved | Questions with any gold fully packed | Questions with any gold partially packed |
|---|---:|---:|---:|---:|---:|---:|
| Baseline | 0.100833 | 0.014167 | 0.086667 | 0.120 | 0.020 | 0.100 |
| Recency | 0.073750 | 0.001667 | 0.072083 | 0.085 | 0.005 | 0.085 |
| Role-aware | 0.672667 | 0.019167 | 0.511417 | 0.735 | 0.025 | 0.570 |

The role-aware selector retrieves substantially more annotated gold evidence than baseline and recency. However, under the current retrieval ordering and prefix-truncation packer, only a small fraction of gold sessions survive in full. The partial-retention measure is a conservative diagnostic based on whether the first 80 normalized characters of a gold session occur in the packed context; it is not a semantic evidence-coverage metric.

This points to a concrete pipeline bottleneck: the reader receives a truncated prefix of a concatenated context, which can cut through a relevant session. The next experiment should compare the existing prefix packer with a whole-session packer that ranks retrieved sessions by query similarity and includes only complete sessions that fit within the same 512-token input limit. Keep the selector scores, selected memory budget, sample, reader, decoding, and answer metrics fixed. This isolates the packing-policy change more cleanly than changing the selector and reader simultaneously.

The current gold-retention diagnostic does not change the answer-quality results and does not establish that the extra retrieved gold evidence caused the role-aware QA improvement. Only ten conversation clusters are represented; continue to label the result exploratory.



## Whole-session packing follow-up (Cell 24)

A paired follow-up compared the existing prefix-packed reader contexts with greedy whole-session packing. The same 200 QA items (20 from each of 10 LoCoMo conversations), frozen selector scores, FLAN-T5-small reader, deterministic decoding, and 512-token input cap were retained. Whole-session packing ranked the top three retrieved sessions by query similarity and included only complete sessions that fit; sessions that did not fit were skipped.

### Whole-session results

| Method | n | Exact match | Token F1 | Mean reader input tokens | Mean packed sessions | Mean retrieved-gold recall | Mean packed-gold recall |
|---|---:|---:|---:|---:|---:|---:|---:|
| Baseline | 200 | 0.005 | 0.042409 | 230.465 | 0.445 | 0.100833 | 0.014167 |
| Question-only | 200 | 0.005 | 0.046679 | 42.770 | 0.000 | 0.000000 | 0.000000 |
| Recency | 200 | 0.005 | 0.036622 | 196.565 | 0.385 | 0.073750 | 0.001667 |
| Role-aware | 200 | 0.010 | 0.048561 | 131.285 | 0.210 | 0.672667 | 0.019167 |

### Paired prefix-versus-whole-session comparison

| Method | Prefix token F1 | Whole-session token F1 | Whole minus prefix |
|---|---:|---:|---:|
| Baseline | 0.101501 | 0.042409 | -0.059092 |
| Question-only | 0.046679 | 0.046679 | 0.000000 |
| Recency | 0.073569 | 0.036622 | -0.036947 |
| Role-aware | 0.205651 | 0.048561 | -0.157090 |

### Interpretation

Whole-session packing did not improve downstream QA in this configuration. It reduced token F1 for all memory-based methods; the role-aware method remained the highest-scoring method among the four whole-session conditions (0.048561), but its large prefix-packing advantage was substantially attenuated. Question-only outscored baseline and recency under whole-session packing.

The role-aware selector's mean retrieved-gold recall remained 0.672667, while mean packed-gold recall was only 0.019167. Thus the selector still ranked annotated evidence highly, but the complete-session fit constraint admitted very few complete evidence sessions into the reader context. The mean number of packed role-aware sessions was 0.210. This is consistent with a packing bottleneck, not evidence that retrieval quality itself deteriorated.

The whole-session reader inputs were not token-budget matched across methods: mean input lengths ranged from 42.770 tokens for question-only to 230.465 for baseline. Whole-session packing is therefore a diagnostic comparison of this packing policy, not a controlled claim that complete-session packing is intrinsically inferior under all possible packing designs. The paired comparison is on the same sampled questions, but the evaluation still contains only 10 conversation clusters and remains exploratory.

### Decision

Do not replace prefix packing with the tested greedy whole-session packer. The next packing experiment should preserve evidence-bearing portions of sessions rather than requiring every selected session to fit in full, and should measure both exact tokenizer use and gold-evidence retention. A more efficient evidence-span or sentence-level packer is a logical next candidate. Do not infer semantic grounding or causality from lexical QA metrics or annotated-gold overlap alone.


### Paired conversation-cluster bootstrap for prefix vs whole-session packing

A paired bootstrap resampled the 10 conversation clusters (20,000 replicates) for each method's whole-session-minus-prefix difference:

| Method | Token-F1 delta | 95% cluster-bootstrap CI | Exact-match delta | 95% cluster-bootstrap CI |
|---|---:|---:|---:|---:|
| Baseline | -0.05909 | [-0.09872, -0.03073] | -0.030 | [-0.070, 0.000] |
| Question-only | 0.00000 | [0.00000, 0.00000] | 0.000 | [0.000, 0.000] |
| Recency | -0.03695 | [-0.06302, -0.01179] | -0.005 | [-0.020, 0.010] |
| Role-aware | -0.15709 | [-0.20037, -0.11048] | -0.070 | [-0.100, -0.040] |

The token-F1 intervals for all three memory methods lie below zero. For exact match, the role-aware interval lies below zero, baseline reaches zero at its upper endpoint, and recency's interval crosses zero. These are paired cluster-bootstrap intervals over only 10 conversations and should remain exploratory.

An initial second-reader whole-session run with `google/flan-t5-base` is reported in the consolidated follow-up below. A later controlled evidence-span replication with the same reader is reported in the next section.


## Consolidated follow-up: second reader, lexical support proxy, budget audit, and dataset inventory

The consolidated follow-up completed 800/800 generations with `google/flan-t5-base` on the same 200-question sample (four methods; 10 LoCoMo conversation clusters). The second-reader run used the whole-session prompt set.

### Second-reader QA results: FLAN-T5-base

| Method | n | Exact match | Token F1 |
|---|---:|---:|---:|
| Baseline | 200 | 0.010 | 0.0307 |
| Question-only | 200 | 0.005 | 0.0057 |
| Recency | 200 | 0.010 | 0.0331 |
| Role-aware | 200 | 0.010 | 0.0272 |

Unlike the FLAN-T5-small prefix-packed result, role-aware did not lead under this second-reader/whole-session condition: recency and baseline had higher mean token F1. This does not isolate a reader-model effect because the strongest FLAN-T5-small result used prefix packing while the FLAN-T5-base follow-up used whole-session packing. Reader and packing policy are confounded in this cross-run comparison. No paired cluster-bootstrap interval for these second-reader differences is reported here.

### Lexical evidence-support proxy

| Method | n | Mean lexical support | Median lexical support | Mean answer content tokens |
|---|---:|---:|---:|---:|
| Baseline | 200 | 0.6709 | 0.6667 | 2.820 |
| Question-only | 200 | Not defined | Not defined | 2.970 |
| Recency | 200 | 0.6765 | 0.6667 | 2.735 |
| Role-aware | 200 | 0.6940 | 1.0000 | 2.965 |

The question-only support statistic is undefined because it has no retrieved context. This proxy measures lexical overlap only; it is not semantic entailment, factual grounding, or a validated hallucination metric. The small differences should not be interpreted as proof that one method is more grounded.

### Exact tokenizer-budget audit

| Method | n | Mean selected memory tokens | Mean memory budget | Mean reader input tokens | Maximum reader input tokens | All within limit |
|---|---:|---:|---:|---:|---:|---|
| Baseline | 200 | 1851.90 | 1955.3 | 230.465 | 512 | Yes |
| Recency | 200 | 1814.40 | 1955.3 | 196.565 | 512 | Yes |
| Role-aware | 200 | 1783.93 | 1955.3 | 131.285 | 512 | Yes |

The audit confirms that all measured reader inputs stayed within the 512-token cap. The prefix-versus-whole consistency check also confirmed equality of selected-memory token counts and budget caps across the two packing conditions. Note that selected-memory token budget and final reader-input token count are different quantities: whole-session packing can leave unused reader-window capacity when complete sessions do not fit.

### Dataset inventory and independence

The inventory identified 1,536 eligible QA questions in the available dataset. The existing reader sample contains 200, leaving 1,336 additional eligible questions. All belong to the same 10 conversation clusters. Expanding question coverage can improve within-dataset coverage, but it does not increase the number of independent conversation clusters.

### Interpretation and next steps

The small-reader prefix-packed run showed a strong role-aware point estimate, but the base-reader whole-session run did not reproduce that ranking. Because the packing policies differ, the cross-reader comparison is not a clean model-size replication. The evidence supports treating the current downstream result as reader-and-packer dependent and exploratory, rather than claiming a general role-aware answer-quality gain.

Next validation should use a crossed design: evaluate both FLAN-T5-small and FLAN-T5-base under both prefix and whole-session packing on the same questions, with the same selectors, prompt template, input cap, and decoding settings. Then report paired conversation-cluster bootstrap intervals for each within-packing selector contrast and reader-by-packing interaction. A genuinely independent dataset with more conversation clusters remains necessary. Keep the lexical-support measure explicitly labeled as a proxy, not groundedness.


## Evidence-aware sentence-span packing follow-up

The evidence-aware span-packing experiment completed 800/800 deterministic generations with FLAN-T5-small on the same 200-question sample and 10 LoCoMo conversation clusters. It reused the frozen baseline, role-aware, and recency selectors and question-only control. Candidate sentence spans were ranked by lexical query similarity from the top-three retrieved sessions; gold answers and evidence annotations were not used for span selection. Full prompts were checked against the exact 512-token reader input limit, and complete questions were preserved.

| Method | n | Exact match | Token F1 | Mean reader input tokens | Mean packed sessions | Mean packed spans | Mean retrieved gold-session recall | Mean packed gold-session recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Baseline | 200 | 0.025 | 0.1016 | 508.245 | 2.700 | 23.805 | 0.1008 | 0.1008 |
| Question-only | 200 | 0.010 | 0.0440 | 42.770 | 0.000 | 0.000 | 0.0000 | 0.0000 |
| Recency | 200 | 0.015 | 0.0812 | 508.025 | 2.620 | 23.285 | 0.0738 | 0.0738 |
| Role-aware | 200 | 0.120 | 0.2417 | 507.685 | 2.445 | 23.045 | 0.6727 | 0.6727 |

Paired conversation-cluster bootstrap (10 clusters, 20,000 resamples):

| Contrast | Mean difference | 95% CI |
|---|---:|---:|
| Role-aware minus baseline token F1 | +0.1401 | [+0.0640, +0.2213] |
| Role-aware minus recency token F1 | +0.1606 | [+0.1016, +0.2240] |
| Role-aware minus baseline exact match | +0.0950 | [+0.0300, +0.1750] |

This is the strongest downstream role-aware result so far in the tested configurations. Unlike the earlier greedy whole-session packer, span packing retained the retrieved gold-session recall at the packed-context stage: role-aware 0.6727 versus 0.0192 with whole-session packing. For all methods, packed gold-session recall equals retrieved gold-session recall in this diagnostic because at least one selected span from each retrieved gold session was retained; this is session-level retention, not proof that the specific supporting utterance or semantic evidence survived. Lexical similarity is not semantic relevance, and the gold-session metric is not entailment or factual-grounding validation.

Interpretation remains exploratory: there are only 10 conversation clusters, the gold annotation maps evidence to sessions rather than sentence spans, and this is one reader/model configuration. Next, rerun this exact span-packing pipeline with FLAN-T5-base using the same 200 questions, frozen selectors, candidate spans, deterministic decoding, and exact tokenizer-specific 512-token checks. Preserve the FLAN-T5-small artifacts separately. If the result holds, proceed to independent-dataset validation and complete the reproducibility package.

Artifacts were saved in the Kaggle runtime under `locomo_reader_qa_evidence_span`; raw CSV/JSON files have not been added to the repository by this documentation update.


## Evidence-aware span-packing replication: FLAN-T5-base

The evidence-aware span-packing pipeline was repeated with `google/flan-t5-base` on the same 200 sampled LoCoMo questions and 10 conversation clusters. The frozen baseline, role-aware, and recency selectors, question-only control, 10% memory budget, top-three selected sessions, TF-IDF span ranking, deterministic decoding, and exact tokenizer-specific 512-token input cap were retained. The run completed all 800 generations. Every prompt preserved the complete question and passed the 512-token audit.

| Method | n | Exact match | Token F1 | Mean reader input tokens | Mean packed sessions | Mean packed spans | Mean retrieved gold-session recall | Mean packed gold-session recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Baseline | 200 | 0.030 | 0.0918 | 510.660 | 2.80 | 45.200 | 0.0933 | 0.0933 |
| Question-only | 200 | 0.005 | 0.0057 | 42.770 | 0.00 | 0.000 | 0.0000 | 0.0000 |
| Recency | 200 | 0.010 | 0.0577 | 510.755 | 2.70 | 45.460 | 0.0738 | 0.0738 |
| Role-aware | 200 | 0.100 | 0.2376 | 510.675 | 2.46 | 43.905 | 0.6727 | 0.6727 |

Paired conversation-cluster bootstrap (10 clusters, 20,000 resamples):

| Contrast | Mean difference | 95% CI |
|---|---:|---:|
| Role-aware minus baseline token F1 | +0.1458 | [+0.0818, +0.2170] |
| Role-aware minus recency token F1 | +0.1799 | [+0.1176, +0.2436] |
| Role-aware minus baseline exact match | +0.0700 | [+0.0250, +0.1300] |
| Role-aware minus recency exact match | +0.0900 | [+0.0400, +0.1500] |

### Cross-reader consistency

| Reader | Method | Exact match | Token F1 |
|---|---|---:|---:|
| FLAN-T5-small | Baseline | 0.025 | 0.1016 |
| FLAN-T5-small | Question-only | 0.010 | 0.0440 |
| FLAN-T5-small | Recency | 0.015 | 0.0812 |
| FLAN-T5-small | Role-aware | 0.120 | 0.2417 |
| FLAN-T5-base | Baseline | 0.030 | 0.0918 |
| FLAN-T5-base | Question-only | 0.005 | 0.0057 |
| FLAN-T5-base | Recency | 0.010 | 0.0577 |
| FLAN-T5-base | Role-aware | 0.100 | 0.2376 |

The role-aware selector remains the strongest method under both reader sizes. Its token F1 is 0.2417 with FLAN-T5-small and 0.2376 with FLAN-T5-base; exact match is 0.120 and 0.100 respectively. This is useful cross-reader consistency evidence under the span-packing condition, although the two readers are not independent datasets and the experiment still contains only 10 conversation clusters.

The role-aware packed gold-session recall equals its retrieved gold-session recall (0.6727) in this diagnostic. This means at least one selected span from each retained gold session survived packing; it does not establish that the exact supporting utterance or semantically sufficient evidence survived. Span ranking is lexical TF-IDF similarity, not semantic relevance or entailment.

**Interpretation:** evidence-aware span packing plus role-aware session selection has now produced a consistent downstream advantage across two reader sizes on this sample. The prior whole-session FLAN-T5-base run should not be conflated with this span-packing replication: it used a different packing policy and gave a different ranking. The evidence remains exploratory because of the 10-cluster dataset, session-level gold annotations, lexical span ranking, and limited reader/model configurations.

**Next:** preserve these results, then move to independent-dataset validation with conversation-level cluster reporting. Follow with targeted ablations of role features and memory budget. Do not describe the current result as proof of semantic grounding or broad generalization.

Artifacts were saved in the Kaggle runtime under `locomo_reader_qa_evidence_span_flan_t5_base`; raw CSV/JSON artifacts have not been added to the repository by this documentation update.


## External conversational transfer: Long-MT-Bench+ with corrected span-level budget

An initial Long-MT-Bench+ transfer attempt used a greedy whole-session admission rule. Its audit found that all three memory selectors selected identical session lists on all 288 questions; 264/288 questions received no packed session. Those results are retained as a failed packing diagnostic and are not interpreted as a test of selector quality.

The corrected experiment moved the memory-budget decision to the span level. It evaluated 288 questions across 11 conversations with `google/flan-t5-base`, four methods, deterministic generation, an exact 10% tokenizer-based memory budget, and a 512-token reader-input cap. Session-level selector scores and lexical span similarity were combined for span ranking; selected spans were packed within the fixed memory budget. All 1,152 method/question rows completed. Every question received context for the three memory methods, all memory budgets were respected, and all reader inputs were within 512 tokens.

### Results

| Method | n | Exact match | Token F1 | Mean reader input tokens | Mean packed sessions | Mean packed spans |
|---|---:|---:|---:|---:|---:|---:|
| Baseline | 288 | 0.0000 | 0.082333 | 510.913 | 1.656 | 24.278 |
| Question-only | 288 | 0.0000 | 0.006017 | 55.444 | 0.000 | 0.000 |
| Recency | 288 | 0.0035 | 0.080957 | 510.420 | 2.205 | 21.365 |
| Role-aware | 288 | 0.0035 | 0.144299 | 510.972 | 1.344 | 20.396 |

### Paired conversation-cluster bootstrap

The paired bootstrap resampled the 11 conversation clusters (20,000 replicates):

| Contrast | Metric | Difference | 95% CI |
|---|---|---:|---:|
| Role-aware − baseline | Token F1 | +0.062667 | [+0.044136, +0.082037] |
| Role-aware − recency | Token F1 | +0.063443 | [+0.045635, +0.081690] |
| Role-aware − baseline | Exact match | +0.003497 | [0.000000, +0.010490] |
| Role-aware − recency | Exact match | 0.000000 | [0.000000, 0.000000] |

### Budget audit

| Method | Mean memory used | Mean memory budget | Mean selected spans | Mean packed spans | Zero-packed questions |
|---|---:|---:|---:|---:|---:|
| Baseline | 2184.295 | 2185.201 | 93.042 | 24.278 | 0 |
| Recency | 2184.295 | 2185.201 | 83.490 | 21.365 | 0 |
| Role-aware | 2184.385 | 2185.201 | 89.903 | 20.396 | 0 |

All three methods used essentially the full available memory budget, and none produced an empty packed context. Role-aware achieved the highest token F1 while packing fewer spans on average than baseline and recency. This is consistent with more useful evidence selection under the tested scoring and packing procedure, but it does not by itself establish why the answer metric improved.

### Interpretation and limits

This is encouraging external-transfer evidence: role-aware token F1 exceeded baseline and recency by about 0.063, with both 11-cluster paired bootstrap intervals above zero. Exact match remained extremely low and did not show a meaningful advantage over recency. The result therefore supports a claim about token-level lexical answer overlap in this setup, not a broad claim of exact answer correctness.

The benchmark contains only 11 conversation clusters, so cluster-bootstrap uncertainty remains limited by the small number of independent conversations. Token F1 and exact match are lexical metrics, not semantic entailment or factual-grounding evaluations. The span-ranking procedure uses lexical similarity and the combined session/span score; it is not a semantic evidence verifier. This experiment should be described as exploratory external transfer, not definitive independent validation.

The original whole-session attempt is not pooled with this corrected run: it had a different admission bottleneck and identical selected-session lists across selectors. Raw CSV outputs remain in the Kaggle runtime at `long_mt_bench_plus_span_budget_flan_t5_base`; they have not been committed as raw artifacts in this documentation update.

**Decision:** retain this corrected Long-MT-Bench+ result as positive but limited external evidence. No further rerun of this configuration is required. Next research work should move to targeted ablations of role features and budget sensitivity, while preserving the current result and its limitations.
