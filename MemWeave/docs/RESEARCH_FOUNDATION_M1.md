# MemWeave Research Foundation — Milestone 1

**Version:** 0.1  
**Status:** Research specification; hypotheses are untested  
**Programme:** Joint algorithm + evaluation framework  
**Working title:** Evidence-Preserving Memory Selection and Lifecycle Evaluation Under Fixed Budgets

## 1. Purpose and decision

This document establishes the first research milestone. It does not claim that MemWeave's proposed mechanisms are novel or that prior results establish the proposed hypotheses.

**M1 objective:** define a falsifiable research question, specify a candidate algorithm family, define an evaluation framework that separates memory-construction loss from retrieval loss, and establish an auditable experiment protocol.

**M1 exit criteria**
1. Research question and hypotheses are fixed before the next confirmatory run.
2. A literature/novelty matrix distinguishes adjacent work and the proposed gap.
3. The algorithm is specified without access to test questions or test labels at construction time.
4. Metrics separately measure preservation, retrieval, downstream answer quality, cost, and uncertainty.
5. Stage B and Stage C are retained as distinct historical runs; no headline result is selected until their discrepancy is reconciled.
6. The protocol includes exact token accounting, traceable evidence mappings, conversation-level splits, and reproducible exports.

## 2. Research question

**RQ:** Under a strict, query-agnostic memory budget, how should a conversational agent select and compress historical evidence so that future answer-supporting information is preserved, redundant content is controlled, and downstream retrieval and answer quality remain robust across unseen conversations?

This question separates three stages:
- **Construction:** which source evidence is retained in persistent memory?
- **Retrieval:** which retained evidence is surfaced for a future question?
- **Answering:** does the surfaced evidence support a correct, calibrated answer?

The primary setting is query-agnostic construction: the memory builder must not see future evaluation questions, gold evidence, or test labels. Query-conditioned retrieval may occur at inference time, but it must be reported separately from the storage policy.

## 3. Proposed contributions (to be validated)

### C1 — Budgeted evidence-preserving memory selection

A memory-selection policy that estimates evidence utility under a fixed token budget while accounting for semantic signal, information/turn role, evidence coverage, redundancy, recency or temporal validity, and token cost.

### C2 — Memory lifecycle evaluation framework

An evaluation protocol that attributes failures to:
1. evidence unavailable in the source or annotation;
2. evidence discarded during memory construction/compression;
3. evidence retained but not retrieved;
4. evidence retrieved but not used correctly in the final answer.

The framework will report evidence preservation and downstream task quality separately. It will also report cost and uncertainty rather than collapsing all outcomes into one score.

These contributions are hypotheses about useful research outputs, not novelty claims. The literature review must determine which elements are already established.

## 4. Hypotheses

- **H1 (budgeted preservation):** At matched exact-token budgets, a proposed selection policy retains more gold evidence than strong query-agnostic baselines on unseen conversations.
- **H2 (incremental role value):** Role/turn-type features improve evidence preservation after controlling for semantic similarity and other correlated signals.
- **H3 (coverage and redundancy):** Explicit coverage and redundancy control improve evidence preservation or downstream answer quality at tight budgets, compared with a score-only selector.
- **H4 (budget robustness):** Any advantage is not confined to a single budget point; performance is characterised over a predeclared budget curve.
- **H5 (downstream validity):** Improvements in preserved/retrievable evidence produce measurable gains in answer correctness and/or calibration under a fixed answering model and prompt.

Each hypothesis has a meaningful null. If H2 is unsupported, role features will not be presented as a causal source of gains. If H5 is unsupported, evidence recall will not be described as improved answer quality.

## 5. Candidate formalisation

Let:
- (S = \{s_1,\ldots,s_n\}) be source memory units (sessions or turns);
- (M \subseteq S) be the selected memory;
- (c_i\) be the exact tokenizer-derived storage cost of unit (s_i);
- (B\) be the hard token budget;
- (Q\) be a future-query distribution, unavailable to the memory builder;
- (E(q)\) be the gold evidence set for an evaluation query, used only for evaluation.

The constrained objective is:

\[
\max_{M\subseteq S} \mathbb{E}_{q\sim P(Q)}[R(M,q)]
\quad\text{subject to}\quad
\sum_{s_i\in M}c_i\leq B.
\]

Because the future query distribution is not available at construction time, the policy must estimate general evidence utility from permitted source-side features. The objective above defines the evaluation target; it does not license use of test queries or gold evidence during selection.

A candidate marginal utility is:

\[
\Delta(i\mid M)=
\alpha U_i + \beta G(i\mid M)
-\lambda D(i\mid M)
+\rho T_i,
\]

where:
- (U_i\): source-only estimated utility (semantic/information value);
- (G(i\mid M)\): incremental coverage/diversity contribution;
- (D(i\mid M)\): redundancy with already selected items;
- (T_i\): temporal validity or update signal where applicable;
- coefficients are fit/tuned on development data only.

A greedy cost-normalised selector may rank candidates by \(\Delta(i\mid M)/c_i\), subject to exact budget feasibility. This is a baseline candidate, not a proven optimal algorithm. We will test alternative formulations and will not claim submodularity or approximation guarantees without proving the required assumptions.

**Leakage guard:** role labels may be derived from source turn metadata, but gold-evidence labels, test questions, test annotations, and test outcomes must never be used to construct or tune persistent memory.

## 6. Evaluation framework

### 6.1 Stage-separated metrics

| Stage | Primary measurements | Interpretation |
|---|---|---|
| Construction/preservation | Gold-evidence retention/recall, evidence coverage, exact token utilisation | What relevant evidence survives storage? |
| Compression | Evidence loss, redundancy, source-to-memory traceability | What is removed, merged, or transformed? |
| Retrieval | Recall@k, precision@k, MRR/nDCG where applicable | Can the system find preserved evidence? |
| Answering | Exact match/F1 and benchmark-approved judge metrics; abstention/calibration | Does retrieved evidence support correct answers? |
| Efficiency | Tokens stored/retrieved, latency, calls, memory footprint | What is the cost of the result? |
| Reliability | Paired confidence intervals, conversation-cluster bootstrap, seed variance | How stable is the observed difference? |

Evidence recall is not answer accuracy. Report each stage independently.

### 6.2 Required baselines

At minimum, compare under matched source data and exact token budgets:
1. chronological/recency selection;
2. random selection (multiple seeds);
3. source-only heuristic or frequency/novelty selection;
4. semantic-similarity-only selection;
5. raw-history retrieval / no persistent compression where feasible;
6. role-only and role-plus-similarity ablations;
7. coverage/diversity-aware selection;
8. the current MemWeave baseline;
9. relevant published memory systems where their implementations, licenses, and evaluation conditions permit a fair comparison.

Do not compare published headline scores across different answer models, prompts, budgets, or dataset versions as if they were controlled results.

### 6.3 Ablation design

Predeclare ablations that isolate:
- semantic similarity;
- user/assistant role and message type;
- evidence/importance signals;
- coverage/diversity;
- redundancy penalty;
- temporal/update handling;
- token-cost normalisation.

Use a factorial or otherwise controlled design where feasible. Report interactions and uncertainty. A leave-one-feature-out result alone does not establish causal contribution when features are correlated.

### 6.4 Budget curve

Initial budget grid: 1%, 2%, 5%, 10%, 20%, and 30% of source tokens. Also report absolute token budgets where dataset scale allows. All budgets must use a pinned tokenizer and exact token counts, not word-count proxies.

### 6.5 Generalisation and splits

- Split by conversation/user entity, never by question alone where multiple questions share the same conversation.
- Freeze model, features, hyperparameters, and thresholds before held-out evaluation.
- Use at least one benchmark for development and a separate benchmark for transfer, with no tuning on the transfer set.
- Treat multiple speaker orientations of the same conversations as sensitivity analyses, not independent replications.
- Bootstrap at the conversation cluster level where conversation is the independent sampling unit.

### 6.6 Downstream QA protocol

Hold the answer model, system prompt, retrieved-context budget, decoding parameters, and scoring procedure fixed across memory policies. Save privacy-safe per-question outputs and evidence traces. Report exact-match/F1 and benchmark-appropriate judge scores separately, including abstention and unsupported-answer behaviour. Human adjudication should be used for a sample of judge-sensitive cases if feasible.

## 7. Literature positioning: initial reading list

This is an initial map, not a completed systematic review.

| Work | Relevance to MemWeave | Consequence for novelty claim |
|---|---|---|
| LongMemEval (Wu et al., ICLR 2025) | Long-term conversational memory benchmark; multi-session, temporal, update, abstention tasks | Benchmark and task framing are established |
| Do Conversational Agents Need Explicit Memory? (Zhou et al., 2025/2026; code repository) | Controlled comparison of explicit memory systems and raw-history RAG; distinguishes construction loss from retrieval failure | MemWeave must include strong raw-history baselines and stage-separated attribution |
| MemRefine (Kim et al., 2026 preprint) | Explicit budget-constrained memory-store management and compression | Fixed-budget memory management alone is not novel |
| Memora (Uddin et al., Findings of ACL 2026) | Consolidation, memory mutation, obsolete-memory handling and forgetting-aware evaluation | Evaluation should include updates/validity where benchmark support exists |
| Long-Term Agent Memory through Complementary Curation and Consolidation (Findings of AACL 2026) | Episodic and structured relational memory with consolidation | Hybrid/structured memory is already an active direction |
| LongMemEval agent-memory study (Redis AI Research, 2026) | Compares raw retrieval, extracted memories, and hybrid memory with downstream QA | Include hybrid and raw-history comparisons; avoid relying on evidence recall alone |

Links:
- LongMemEval: https://arxiv.org/abs/2410.10813
- Controlled memory-vs-RAG comparison and code: https://github.com/ielab/memory-systems-vs-rag
- MemRefine: https://arxiv.org/abs/2606.13177
- Memora: https://aclanthology.org/2026.findings-acl.1337/
- Complementary Curation and Consolidation: https://aclanthology.org/2026.findings-aacl.218/
- Redis AI Research LongMemEval evaluation: https://redis.github.io/redis-ai-research-public/longmemeval-agent-memory/

**Provisional gap to investigate:** a rigorous, query-agnostic, exact-token-budget study that jointly traces source evidence through construction, compression, retrieval, and answer generation, while isolating the incremental value of role/coverage/redundancy signals under controlled raw-history and memory-system baselines. This is a candidate gap, not yet a verified claim of priority or novelty.

## 8. Existing MemWeave evidence: status and guardrails

The repository currently documents:
- Stage B: 235 TEST questions; 0.4042 baseline vs 0.7094 role-aware evidence recall; 10% word-count proxy.
- Stage C: separate regenerated run; 0.404184 baseline vs 0.820638 role-aware evidence recall; 10% word-count proxy; paired bootstrap 95% CI [0.358723, 0.474184].
- Stage C ablation: the message-similarity group accounts for most of the observed measured gain. This prevents attributing the full result to role-awareness.
- Preliminary frozen LongMemEval-to-LoCoMo transfer: 10 conversation clusters; promising but insufficient to claim definitive independent replication.
- Stage C audit: 54 PASS, 3 WARNING, 0 FAIL; warnings include independent budget reconstruction, end-to-end evidence mapping, and independent replication.

**Non-negotiable reporting rules**
1. Stage B and Stage C remain separate records until their discrepancy is explained.
2. The word-count proxy is not exact token-budget validation.
3. Evidence recall is not answer accuracy.
4. LoCoMo speaker orientations are not independent replications.
5. An artifact audit is not a clean independent rerun.
6. No claim of state of the art, statistical superiority, or novelty without a controlled comparison and literature review.

## 9. Immediate experimental work packages

### M1-A: Provenance and historical reconciliation
- Recover the exact Stage B and Stage C code/config/data lineage.
- Diff feature construction, row ordering, preprocessing, split construction, and scoring.
- Recompute both runs from preserved inputs where possible.
- Document any irrecoverable provenance gap; do not infer a cause.

### M1-B: Evidence and budget audit
- Export a privacy-safe selection trace: source-unit ID hash, token cost, selected flag, rank/score, and evidence mapping identifiers.
- Reconstruct exact token costs with a pinned tokenizer.
- Independently audit gold-evidence-to-source-unit mappings.
- Verify LoCoMo speaker mapping and annotation alignment.

### M1-C: Controlled baseline protocol
- Pin datasets, code, model versions, tokenizers, prompts, seeds, and package versions.
- Define conversation-level split and leakage checks.
- Implement matched-budget baselines and ablations.
- Save per-question, per-conversation, and aggregate outputs with checksums.

### M1-D: Lifecycle evaluation prototype
- Implement separate counters for evidence available, retained, retrieved, and used in correct answers.
- Add explicit failure categories and traceability.
- Add answer-level metrics only under a fixed answer-generation protocol.

## 10. M1 acceptance checklist

- [ ] Literature matrix expanded with methods, assumptions, budgets, datasets, metrics, and reproducibility status.
- [ ] Novelty claim narrowed and supported by comparison, or explicitly marked unresolved.
- [ ] Stage B/C reconciliation report completed.
- [ ] Exact-token budget reconstruction implemented and independently checked.
- [ ] Gold-evidence mapping audit completed.
- [ ] Leakage-safe, conversation-level experimental protocol frozen.
- [ ] Baseline and ablation implementation plan reviewed.
- [ ] Lifecycle metric definitions and output schemas implemented.
- [ ] Confirmatory experiment preregistration written before test execution.

**M1 is complete only when the protocol and audits are independently checkable.** A polished document or a successful notebook execution alone does not satisfy the milestone.
