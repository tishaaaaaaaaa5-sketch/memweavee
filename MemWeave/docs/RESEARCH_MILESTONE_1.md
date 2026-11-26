# MemWeave Research Milestone 1
## Strategy C: Algorithm + evaluation framework

**Status:** Research specification (not a results claim)  
**Branch:** `research/memweave-strategy-c-m1`  
**Date:** 2026-11-26

## 1. Purpose and decision rule

This milestone establishes a falsifiable research programme before further model tuning. MemWeave will pursue two linked contributions:

1. A **query-agnostic, budget-constrained memory-selection method** intended to preserve evidence that supports unknown future questions.
2. An **evaluation framework** that measures not only whether evidence survives selection, but whether it remains usable for correct downstream answers under realistic budgets, distractors, temporal updates, and uncertainty.

The project must not claim novelty or superiority until the related-work comparison and controlled experiments support those claims. Existing Stage A, B, and C results remain distinct historical records.

## 2. Research question

> Given a conversation history and a strict memory budget, can a query-agnostic selector preserve more future-answerable evidence than strong simple and learned baselines, and does that retention advantage translate into better downstream answer quality across datasets and conversation domains?

### Subquestions

- RQ1 — Retention: Which selection policy preserves the greatest fraction of gold evidence at equal exact-token budgets?
- RQ2 — Mechanism: Do speaker role, temporal state, provenance, information novelty, and complementarity each contribute beyond semantic similarity?
- RQ3 — Utilisation: When evidence is retained, does a fixed downstream reader answer more accurately and abstain more reliably?
- RQ4 — Robustness: Do gains survive distribution shift, hard distractors, multiple evidence sessions, updates/contradictions, and different budget levels?
- RQ5 — Efficiency: What are the storage, selection-time, and inference-time costs?

## 3. Working algorithm hypothesis (not a novelty claim)

We will investigate a candidate family provisionally called **MemWeave Evidence-Coverage Selection (MW-ECS)**. The name is temporary and may change after the literature audit.

For conversation sessions (S = \{s_1,\ldots,s_n\}), each session has an exact tokenizer cost (c_i), and the memory budget is (B). Select (M \subseteq S) such that:

\[
\sum_{s_i\in M} c_i \leq B.
\]

The candidate objective is:

\[
\max_{M: \, c(M)\leq B}
\left[
\sum_{s_i\in M} u_\theta(s_i)
+ \lambda\, C_\phi(M)
- \rho\, D_\psi(M)
\right].
\]

Where:

- (u_\theta(s_i)) estimates query-agnostic future evidence utility from session-level signals.
- (C_\phi(M)) estimates complementary evidence coverage across the selected set.
- (D_\psi(M)) penalises redundant selection.
- (\lambda) and (\rho) are tuned only on training/validation data.
- (c(M)) is measured with a pinned tokenizer, not a word-count proxy.

Candidate feature families to test separately:

1. Semantic content and similarity (including the strongest existing similarity features).
2. Speaker/role and message-function signals.
3. Temporal validity, update, and supersession cues.
4. Provenance and evidence traceability.
5. Novelty and information density.
6. Cross-session complementarity and redundancy.
7. Cost-aware utility and uncertainty.

**Critical constraint:** At selection time, the method must not access the future evaluation question, gold evidence labels, answer text, benchmark ID conventions, or any derived leakage. Query-aware retrieval is a separate comparison track, not a valid substitute for the primary query-agnostic task.

We will not assume the objective is submodular or that greedy selection has a formal approximation guarantee. Such claims require a proof under explicit assumptions. First test whether the objective and its components are useful empirically.

## 4. Falsifiable hypotheses

- **H1 — Equal-budget retention:** MW-ECS improves evidence recall over the strongest simple query-agnostic baseline at the same exact token budget.
- **H2 — Incremental role value:** Role/message-function features improve performance after controlling for semantic similarity and other feature families.
- **H3 — Complementarity:** Set-level coverage contributes beyond independent per-session utility, particularly for questions requiring multiple sessions.
- **H4 — Downstream utility:** Any retention improvement produces a measurable improvement in answer quality with the same frozen reader, prompt, and inference settings.
- **H5 — Robustness:** Improvements persist across multiple budget levels and at least one independent dataset/domain, with uncertainty estimated at the conversation level.
- **H6 — Cost effectiveness:** Gains are not explained by materially greater compute, larger stored text, or a different reader/inference budget.

A hypothesis may be rejected. Negative and null findings will be reported.

## 5. Evaluation framework

### 5.1 Two separate evaluation tracks

**Track A — Query-agnostic memory retention (primary).**

The selector receives the history and budget only. Primary outcomes:

- Evidence-session recall under budget.
- Evidence precision and F1 where meaningful.
- Fraction of questions for which all required evidence is retained.
- Exact stored tokens and budget violation rate.
- Per-question and per-conversation outcomes.

**Track B — Downstream memory utilisation.**

A fixed reader receives only the selected memory and the question. Primary outcomes:

- Answer exact match / token F1 (dataset-appropriate).
- Evidence-grounded answer correctness, using a documented evaluator.
- Abstention quality on unanswerable questions.
- Hallucination or unsupported-claim rate.
- Reader input tokens, latency, and cost.

Track B must use identical reader model/version, prompt, decoding settings, and answer-evaluation procedure across selectors. Retention recall must never be presented as answer accuracy.

### 5.2 Datasets and generalisation

- **LongMemEval-S:** primary benchmark, with immutable revision and checksum recorded for every run.
- **LoCoMo:** external conversational transfer evaluation; report the number of independent conversation clusters and use cluster-aware uncertainty. Ten conversations are preliminary evidence, not a large independent sample.
- Additional datasets may be added only after their licensing, annotation structure, and suitability for query-agnostic selection are audited. New benchmark use must not be represented as independent if it shares source conversations or derived data with training.

### 5.3 Baselines

All primary-track methods must use the same input history, exact tokenizer, candidate session units, and hard budget:

- Random selection (multiple seeds).
- Recency.
- Existing strongest simple heuristic (including `low_novelty`).
- Existing MemWeave LR/HGB selectors.
- Similarity-only selector.
- Greedy cost-normalised utility.
- MW-ECS ablations.
- Full-history reference where it fits (context upper/reference, not budget-matched).
- Gold-evidence oracle only as a clearly labelled diagnostic upper bound; never as a deployable baseline.

BM25/TF-IDF/dense query-aware retrieval belongs in a separate **question-known retrieval** track. Do not compare it as if it had the same information at selection time.

### 5.4 Budgets and exact accounting

Primary budget: 10% of the eligible history's tokenizer count, with secondary budgets 1%, 5%, 20%, and 30%. Pin tokenizer name/version and counting rules, including separators and metadata. Save per-session costs, selected session IDs, and final memory token count. Report both target and achieved budget; no hidden truncation.

### 5.5 Splits and statistical protocol

- Split by conversation/user/history group before feature fitting; no related sessions from one conversation may cross train/validation/test.
- Freeze preprocessing, feature schema, tokenizer, and hyperparameter search before the final evaluation.
- Use development data for feature selection and tuning; use a sealed test set once.
- Run multiple seeds where stochasticity exists.
- Use paired comparisons and conversation-cluster bootstrap/permutation where the sampling unit is a conversation. Report effect sizes and confidence intervals, not p-values alone.
- Correct for multiple comparisons within predeclared hypothesis families.
- Publish per-question aggregate predictions and selection traces where dataset terms permit.
- Report subgroup performance as exploratory unless adequately powered and pre-specified.

## 6. Required mechanism-isolation experiment

The current Stage C ablation indicates that message-similarity features explain a substantial part of the observed gain. The next algorithm experiment must therefore isolate contributions rather than bundle features.

Minimum ablation matrix:

| Variant | Similarity | Role/message function | Temporal/update | Provenance | Set coverage | Redundancy |
|---|---:|---:|---:|---:|---:|---:|
| A: simple baseline | No | No | No | No | No | No |
| B: similarity-only | Yes | No | No | No | No | No |
| C: similarity + role | Yes | Yes | No | No | No | No |
| D: + temporal/provenance | Yes | Yes | Yes | Yes | No | No |
| E: + set coverage | Yes | Yes | Yes | Yes | Yes | No |
| F: full candidate | Yes | Yes | Yes | Yes | Yes | Yes |

Add leave-one-family-out ablations and verify that every component is active (non-zero learned/tuned coefficient or demonstrably operative selection effect). If a component is inactive, do not claim that it helps.

## 7. Reproducibility audit: known blockers

The repository currently documents distinct research stages:

- Stage A (v2.0–v2.3): corrected analysis found only a small, sensitivity-dependent advantage over `low_novelty`; redundancy and cost-awareness were inactive in the audited folds.
- Stage B: historical role-aware test recall 0.709433, baseline 0.404184, gain 0.305249.
- Stage C: regenerated follow-up role-aware recall 0.820638, baseline 0.404184, gain 0.416454.

Stage B and C are not interchangeable. The difference must be explained before a combined headline claim is made. Stage C records pinned dataset revisions/checksums, but its six generated CSV/JSON exports remain separate from the committed notebook. Its audit reported 54 PASS, 3 WARNING, 0 FAIL; this is an artifact audit, not independent replication.

### Required audit actions

1. Recover and checksum the exact Stage B and Stage C source data, notebook versions, generated files, and run configurations where available.
2. Compare dataset revision, preprocessing, session/evidence mapping, row order, filtering, feature construction, train/test membership, random seeds, model fitting, and budget accounting.
3. Reconstruct selected-session costs independently from saved IDs and token/word costs.
4. Verify gold-evidence-to-session mapping end to end without exposing raw private conversation content.
5. Recompute per-question predictions and aggregate metrics from exported predictions.
6. Re-run the same canonical pipeline in a clean environment.
7. Keep unresolved discrepancies visible; do not overwrite historical records.

## 8. Initial literature map (scoped scan; not exhaustive)

| Work / resource | Relevant contribution or warning for MemWeave | Implication |
|---|---|---|
| LongMemEval (Wu et al., 2024) | Long-term memory benchmark covering extraction, multi-session, temporal, update, and abstention capabilities. | Use as a benchmark foundation, but distinguish its task settings and evidence labels carefully. |
| A-MEM (2025) | Dynamic, interconnected agent memory organisation. | Compare against structured/dynamic memory, not only flat heuristics. |
| Mem0 / memory-system evaluations | Practical persistent memory systems with extraction and retrieval pipelines. | Include deployable memory-system comparisons where an equal-budget protocol is feasible. |
| MemRefine (2026 preprint) | Budgeted memory-store maintenance using LLM-guided delete/merge/preserve decisions. | Directly relevant to budgeted memory management; compare the task formulation and cost assumptions. |
| UTILMEM (2026 preprint) | Argues factual recall alone misses evidence integration, implicit relevance, and distractor resistance. | Strengthens the case for Track B and hard-distractor evaluation. |
| Memora (Findings of ACL 2026) | Long-term remembering/reasoning/recommending and forgetting-aware evaluation. | Consider obsolete-memory and update handling in robustness tests. |
| ProgMem (Findings of AACL 2026) | Structured belief-state memory, temporal updates, and evidence checking. | Compare with state-based memory and explicit provenance/update handling. |
| Long-Term Agent Memory through Complementary Curation and Consolidation (Findings of AACL 2026) | Combines episodic and relational memory with consolidation. | Compare complementary representations and consolidation, not just session scoring. |
| A-MAC (ICLR 2026 MemAgents) | Memory admission as an interpretable multi-factor decision. | The broad idea of multi-factor admission is already explored; novelty must be more specific. |

This is an initial scoping map, not a complete systematic review or verified novelty claim. Before paper submission, verify full texts, implementations, licences, benchmark protocols, and the closest competing methods.

## 9. Milestone 1 acceptance criteria

Milestone 1 is complete only when:

- [ ] The literature matrix includes at least 15 directly relevant papers/systems, with full-text verification for the closest competitors.
- [ ] A written novelty statement distinguishes MemWeave from memory admission, memory consolidation, query-aware retrieval, and evidence-utilisation evaluation.
- [ ] The Stage B/Stage C discrepancy is either explained with evidence or formally documented as unresolved.
- [ ] Exact-token accounting and evidence-mapping audit procedures are implemented and independently checked.
- [ ] The Track A/Track B protocol, splits, metrics, statistical unit, and multiple-comparison families are frozen before new test evaluation.
- [ ] The first mechanism-isolation ablation plan is executable from a clean environment.

No performance target is used as a milestone acceptance criterion. The purpose is to make the next performance result interpretable and defensible.

## 10. Immediate next actions

1. Audit the actual Stage B and Stage C notebooks and exports; do not assume missing artifacts can be reconstructed.
2. Complete the closest-work literature matrix and mark each entry as full-text verified or abstract-only.
3. Specify a machine-readable run manifest and privacy-safe per-question output schema.
4. Implement exact token-budget reconstruction and evidence-ID validation.
5. Only then run the frozen mechanism-isolation experiment.

## Selected references and starting points

- Wu et al. (2024), *LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory*, https://arxiv.org/abs/2410.10813
- *MemRefine: LLM-Guided Compression for Long-Term Agent Memory* (2026 preprint), https://arxiv.org/abs/2606.13177
- *UTILMEM: Benchmarking Evidence Utilization in Long-Term Conversational Memory* (2026 preprint), https://arxiv.org/abs/2608.30508
- *From Recall to Forgetting: Benchmarking Long-Term Memory for Personalized Agents* (Findings of ACL 2026), https://aclanthology.org/2026.findings-acl.1337/
- *ProgMem: Programmatic Belief-State Memory for Long-Horizon Conversational Agents* (Findings of AACL 2026), https://aclanthology.org/2026.findings-aacl.120/
- *Long-Term Agent Memory through Complementary Curation and Consolidation* (Findings of AACL 2026), https://aclanthology.org/2026.findings-aacl.218/
- *Adaptive Memory Admission Control for LLM Agents* (ICLR 2026 MemAgents), https://openreview.net/pdf/3a8ba70bb8efe017018cebc9cf4bec9763d8bf77.pdf
