# MemWeave: Research Synthesis Draft

**Status:** working synthesis; not a final publication-ready manuscript  
**Project:** role-aware, budget-constrained memory retention for long-horizon conversations  
**Repository branch:** `research/memweave-followup-release`

## 1. Research question

When a conversational assistant cannot retain its full interaction history, can role-aware selection preserve more useful conversational evidence under a constrained memory budget, and does that retained evidence improve downstream answers?

MemWeave studies memory retention as a constrained selection problem. The selector ranks conversation sessions using query relevance and message-role-aware signals; a budgeted policy chooses what to retain. The project evaluates both evidence-retention outcomes and downstream reader QA. These are related but distinct endpoints and must not be conflated.

## 2. Main contributions supported by the current experiments

1. **Role-aware evidence selection:** adding message-role-aware features to a baseline feature set substantially improves budgeted evidence recall on the LongMemEval-S held-out question split.
2. **Controlled implementation reconciliation:** a controlled reconstruction shows that feature scaling accounts for most of the difference between the Stage B-like and Stage C-like configurations; vocabulary-cap and message-filter effects are smaller or null in the tested setup.
3. **Downstream answer-quality evaluation:** under evidence-aware span packing, the role-aware selector obtains higher lexical answer scores than baseline and recency on the sampled LoCoMo questions with both FLAN-T5-small and FLAN-T5-base.
4. **Exploratory external transfer:** on Long-MT-Bench+, role-aware selection improves token F1 over baseline and recency under the corrected span-level budget, although exact match remains near zero.
5. **Ablation insight:** the corrected individual leave-one-out analysis shows that the two message-count features have no observed effect in this run, while removing individual similarity features changes recall only slightly. This is descriptive evidence, not a causal attribution analysis.

## 3. Methods and evaluation design

### 3.1 Selector and retention endpoint

The principal role-aware comparison uses logistic regression with frozen regularization (C = 0.3), a `same_pipeline` evaluation pool, 235 DEV questions and 235 TEST questions, and a 10% word-count-based memory budget. The six added features represent user/assistant maximum and top-three mean question similarity, plus log user/assistant message counts.

The primary selector endpoint is budgeted evidence recall. It measures whether annotated gold evidence is represented among retained candidates under the memory budget. It is not a measure of answer correctness, semantic entailment, or hallucination.

### 3.2 Downstream reader endpoint

The reader experiments use a frozen selector and FLAN-T5 readers with deterministic generation, a 512-token reader input cap, and a 10% memory budget. Evidence-aware span packing selects lexical spans within retained sessions. Exact match and token F1 are reported as lexical answer metrics.

LoCoMo reader experiments use 200 questions from 10 conversations. Long-MT-Bench+ uses 288 questions from 11 conversations. Paired uncertainty estimates resample conversation clusters; however, the small number of clusters limits the reliability and resolution of those estimates.

## 4. Results

### 4.1 LongMemEval-S role-aware evidence retention

The historical Stage B result was:

| Method | Budgeted evidence recall |
|---|---:|
| Baseline | 0.404184 |
| Role-aware (Stage B) | 0.709433 |
| Paired gain | +0.305248 |

The regenerated Stage C result was:

| Method | Budgeted evidence recall |
|---|---:|
| Baseline | 0.404184 |
| Role-aware (Stage C) | 0.820638 |
| Paired gain | +0.416454 |

These are separate experimental records. They must not be averaged, silently substituted, or described as a direct replication. The Stage B/C controlled reconstruction found a Stage C-like minus Stage B-like endpoint difference of +0.11121 on the same 235 TEST questions (95% paired bootstrap CI [+0.07099, +0.15411]). This reconstruction explains implementation sensitivity but does not establish which historical code state generated every original artifact.

### 4.2 Controlled Stage B/C reconstruction

The tested factorial reconstruction found:
- Z-score scaling versus raw scaling: +0.126809 budgeted recall (95% paired-bootstrap CI [+0.086596, +0.169007]).
- 20,000-feature vocabulary cap versus uncapped vocabulary: -0.015603 in the reported contrast (95% CI [-0.026241, -0.006738]); the cap did not explain the Stage C improvement.
- Message-filter factor: zero observed effect in the audited population.
- The scale-by-cap interaction was not established.

These are effects within the reconstructed pipeline, not universal properties of the features or dataset.

### 4.3 Corrected individual feature ablation

The valid leave-one-feature-out run used the actual six role columns from the augmented feature matrix and the original DEV/TEST fitting and evaluation functions:

| Variant | Mean budgeted recall |
|---|---:|
| Full role-aware | 0.820638 |
| Without user max question similarity | 0.819574 |
| Without user top-three mean question similarity | 0.827021 |
| Without assistant max question similarity | 0.822057 |
| Without assistant top-three mean question similarity | 0.827021 |
| Without log user message count | 0.820638 |
| Without log assistant message count | 0.820638 |
| Baseline | 0.404184 |

Each variant used 4,216 training candidates from 5,523 and evaluated 235 TEST questions. The two message-count removals produced no observed change. Removing either top-three similarity feature slightly increased the point estimate. The individual changes are small and should not be interpreted as statistically established feature contributions; paired per-question uncertainty for this table has not been published.

### 4.4 LoCoMo selector transfer

The frozen LongMemEval-trained selector was evaluated on 10 LoCoMo conversations under two speaker-role orientations. In the reported summary, role-aware macro recall was approximately 0.617, compared with 0.0935 for baseline, in both orientations. This is preliminary cross-dataset transfer evidence. The ten conversations are the independent clusters; the two orientations are sensitivity analyses, not two independent replications. Speaker-role mapping and gold-annotation alignment remain audit requirements.

### 4.5 LoCoMo downstream QA with evidence-aware span packing

| Reader | Method | Exact match | Token F1 |
|---|---|---:|---:|
| FLAN-T5-small | Baseline | 0.025 | 0.1016 |
| FLAN-T5-small | Question-only | 0.010 | 0.0440 |
| FLAN-T5-small | Recency | 0.015 | 0.0812 |
| FLAN-T5-small | Role-aware | **0.120** | **0.2417** |
| FLAN-T5-base | Baseline | 0.030 | 0.0918 |
| FLAN-T5-base | Question-only | 0.005 | 0.0057 |
| FLAN-T5-base | Recency | 0.010 | 0.0577 |
| FLAN-T5-base | Role-aware | **0.100** | **0.2376** |

For FLAN-T5-small, the paired 10-conversation cluster-bootstrap token-F1 gain was +0.1401 over baseline (95% CI [+0.0640, +0.2213]). For FLAN-T5-base, it was +0.1458 (95% CI [+0.0818, +0.2170]). The role-aware advantage therefore persisted across these two reader sizes under the same evidence-span packing condition.

The earlier whole-session packing results were substantially worse and must remain a separate packing-policy experiment. They do not contradict the span-packing results because the packing policies differ. Gold-session retention after span packing means a span from an annotated session survived; it does not prove that the exact supporting utterance or semantically sufficient evidence survived.

### 4.6 Long-MT-Bench+ external transfer

The corrected span-level budget evaluation used 288 questions from 11 conversations with FLAN-T5-base:

| Method | Exact match | Token F1 |
|---|---:|---:|
| Baseline | 0.0000 | 0.0823 |
| Question-only | 0.0000 | 0.0060 |
| Recency | 0.0035 | 0.0810 |
| Role-aware | 0.0035 | **0.1443** |

The paired 11-conversation cluster-bootstrap token-F1 gain was +0.0627 over baseline (95% CI [+0.0441, +0.0820]) and +0.0634 over recency (95% CI [+0.0456, +0.0817]). Exact match did not improve over recency. The first whole-session attempt is excluded from selector conclusions because all selectors chose identical session lists and 264 of 288 questions received no packed context.

This result supports exploratory transfer on token F1, not a broad claim of answer correctness or semantic grounding.

## 5. Interpretation

Taken together, the experiments support a promising but bounded conclusion: role-aware selection can improve budgeted evidence retention, and when paired with evidence-aware span packing it can improve lexical downstream QA metrics on the tested conversational samples. The downstream advantage appears across two FLAN-T5 reader sizes on LoCoMo and in token F1 on Long-MT-Bench+.

The evidence does not yet establish that:
- every role-aware feature is useful;
- role-awareness itself, rather than the message-similarity signals, is the causal mechanism;
- the retained spans are semantically sufficient evidence;
- the method improves factuality, entailment, hallucination rates, or human-rated answer quality;
- performance generalizes to a broad population of conversations;
- the word-count proxy is equivalent to a true token-level storage budget.

## 6. Limitations and threats to validity

1. **Few independent clusters:** LoCoMo has 10 conversations and Long-MT-Bench+ has 11. Many questions within one conversation do not create additional independent clusters.
2. **Exploratory evaluation:** the project evolved iteratively; the current transfer and reader results are not untouched preregistered confirmation.
3. **Lexical answer metrics:** exact match and token F1 do not establish semantic correctness, entailment, factual grounding, or hallucination reduction.
4. **Gold annotation granularity:** annotations often identify sessions rather than exact supporting utterances. Gold-session retention is a coarse proxy.
5. **Lexical span ranking:** TF-IDF similarity is not a semantic evidence verifier.
6. **Budget accounting:** the original selector endpoint uses a 10% word-count proxy. Exact tokenizer-based memory accounting is used in the later reader span-packing experiments, but the two budget definitions must not be conflated.
7. **Historical provenance:** Stage B and Stage C headline results differ. The controlled reconstruction narrows the implementation explanation but does not retroactively prove the exact historical provenance of every run.
8. **Artifact completeness:** the later Stage C and reader-QA raw exports, manifests, checksums, and clean-environment validations are not yet all committed.
9. **Annotation and role mapping:** LoCoMo speaker-role mapping and gold-evidence alignment require an independent audit.

## 7. Claims suitable for the current paper draft

**Supported, with explicit scope:** On the tested LongMemEval-S split, the regenerated role-aware configuration achieved higher budgeted evidence recall than the baseline. Under evidence-aware span packing, role-aware selection achieved higher token F1 than baseline and recency on the sampled LoCoMo and Long-MT-Bench+ evaluations.

**Not yet supported:** universal superiority, semantic grounding, hallucination reduction, causal benefit from every role feature, or definitive independent replication.

## 8. Release and next steps

Before calling the work reproducible:
- publish the privacy-reviewed Stage C CSV/JSON exports and corrected individual-ablation CSV;
- publish the per-question reader QA and Long-MT-Bench+ exports, bootstrap summaries, budget audits, manifests, and checksums;
- provide an executed notebook or run bundle containing the later QA outputs;
- validate the exported files in a clean environment;
- finish word-cost reconstruction, gold-evidence mapping, and speaker-role/annotation audits.

Before calling the result independently confirmed:
- freeze a protocol and analysis plan;
- use a larger number of independent conversation clusters or a genuinely independent dataset;
- keep selector training/tuning separate from external evaluation;
- report cluster-level estimates and uncertainty;
- use a semantic or human-judged answer-grounding endpoint in addition to lexical metrics.

## 9. Provisional conclusion

MemWeave provides evidence that role-aware memory selection can preserve more annotated conversational evidence under constrained retention and, when combined with evidence-aware span packing, can improve lexical answer quality in exploratory reader evaluations. The current results justify a carefully scoped research claim and further independent evaluation. They do not yet justify claims of semantic grounding, broad generalization, or definitive replication.

---

**Author note:** This document is a synthesis of the current reported results, not a substitute for the raw artifacts. Numerical claims should be rechecked against the exported, checksum-verified run files before manuscript submission.
