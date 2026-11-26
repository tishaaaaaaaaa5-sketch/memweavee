# MFAR: Memory Failure-Aware Retrieval
## Algorithm design and research specification

**Status:** Proposed method; not yet implemented or empirically validated  
**Project:** MemWeave  
**Version:** 0.1  
**Purpose:** Specify a falsifiable algorithm and evaluation plan before implementation.

---

## 1. Executive summary

MemWeave's current experiments study evidence selection and report promising evidence-recall improvements. Those results motivate, but do not establish, a broader memory-management method.

We propose **Memory Failure-Aware Retrieval (MFAR)**: a query-time and lifecycle-aware controller that diagnoses where a conversational memory pipeline is losing answer-relevant information, then chooses a targeted corrective action.

MFAR distinguishes four failure modes:

1. **Construction failure:** relevant source information was never written into persistent memory.
2. **Compression failure:** relevant information existed before compression but was omitted, distorted, or stripped of necessary context.
3. **Retrieval failure:** sufficient information survives in memory but the retrieval stage fails to surface it.
4. **Answering failure:** sufficient evidence is supplied to the answer generator, but the generated answer is unsupported, incomplete, or incorrect.

These failures can co-occur and form cascades. MFAR therefore estimates a *multi-label failure profile*, not a single mutually exclusive class.

The central design principle is **diagnose before spending more memory or retrieval budget**. A retrieval failure may call for query expansion or reranking; a construction failure may require source re-ingestion; an answering failure may require evidence-constrained generation or abstention. Increasing top-k alone cannot repair information that was never stored.

## 2. Research question and hypotheses

### 2.1 Primary research question

Can a memory system improve long-horizon conversational question answering by identifying the stage at which answer-relevant information is lost and applying a stage-specific corrective action, compared with a fixed retrieval policy under comparable storage, latency, and token budgets?

### 2.2 Hypotheses

- **H1 — Diagnostic utility:** stage-specific diagnostic signals predict the corresponding failure modes better than a single undifferentiated retrieval-confidence score.
- **H2 — Targeted intervention:** selecting an intervention based on the estimated failure profile improves answer quality or evidence recall relative to a fixed top-k retrieval policy at a matched cost budget.
- **H3 — Cost efficiency:** MFAR achieves a better quality–cost trade-off than indiscriminately increasing retrieval depth or memory size.
- **H4 — Complementarity:** the four failure modes provide non-redundant explanatory information; removing a diagnostic or intervention family measurably degrades performance.
- **H5 — Robustness:** benefits persist across conversation lengths, question types, and at least two independently evaluated datasets.

All hypotheses are empirical. A null or negative result must be reported.

## 3. Formal problem formulation

### 3.1 Pipeline objects

For a conversation history, define:

- (X): the available source conversation or event stream.
- (M_0): the candidate information representation before persistent-memory compression.
- (M): the persistent memory actually stored.
- (R_q): the evidence retrieved from (M) for query (q).
- (A_q): the system answer generated from (q) and (R_q).
- (Y_q): the reference answer or adjudicated answer-support target.
- (B_s): storage budget.
- (B_r): retrieval/answer context budget.
- (C): measured operational cost (tokens, latency, and optionally monetary cost).

The pipeline is:
[
X \xrightarrow{\text{construction}} M_0
\xrightarrow{\text{compression}} M
\xrightarrow{\text{retrieval}(q)} R_q
\xrightarrow{\text{answering}(q)} A_q.
]

The target is not merely to maximize the number of retrieved items. It is to maximize answer quality subject to explicit resource constraints:
[
\max_{\pi} \; \mathbb{E}[Q(A_q,Y_q)]
\quad \text{subject to} \quad
\mathbb{E}[C_s] \leq B_s,\;
\mathbb{E}[C_r] \leq B_r.
]
Here \(\pi\) is the complete memory and retrieval policy and \(Q\) is a predeclared answer-quality measure.

### 3.2 Failure indicators

For each query (q), define four binary *evaluation-time* indicators:

- (F_c(q)=1) if answer-relevant evidence exists in (X) but is absent from the constructed candidate memory (M_0).
- (F_p(q)=1) if answer-relevant evidence is represented in (M_0) but is absent or materially distorted in stored memory (M).
- (F_r(q)=1) if sufficient answer-relevant evidence exists in (M) but is absent from retrieved set (R_q).
- (F_a(q)=1) if sufficient evidence is present in (R_q) but (A_q) fails the answer rubric.

These labels are **not assumed to be mutually exclusive**. A single question can experience a cascade, for example construction loss followed by an unsupported answer.

For retrieval and answering, define sufficiency before the experiment. A practical annotation protocol should mark the minimum evidence set (G_q) needed to answer (q), including acceptable alternatives where appropriate. Then:
- construction and compression failures compare the evidence trace across (X), (M_0), and (M);
- retrieval failure compares (M) with (R_q);
- answering failure is adjudicated conditional on whether (R_q) contains a sufficient evidence set.

If the system does not retain (X), (M_0), or provenance traces, the corresponding failure cannot be reliably distinguished online. MFAR must report **unobservable/unknown**, not infer a confident diagnosis from missing data.

## 4. Observability and diagnostic signals

MFAR uses two distinct kinds of signals:

1. **Online diagnostic features:** available during normal operation and used to choose an intervention.
2. **Oracle evaluation labels:** created from traceable source/memory/retrieval/answer records and used only to train or evaluate the diagnostic model.

Never leak oracle labels or reference answers into online inference.

| Failure mode | Online signals (examples) | Oracle evidence for evaluation |
|---|---|---|
| Construction | Source coverage ledger, ingestion status, entity/event extraction gaps, missing provenance links | Gold evidence in source (X) but absent from (M_0) |
| Compression | Pre/post-compression claim alignment, retained-fact coverage, contradiction or qualifier loss, provenance survival | Gold evidence in (M_0) but not faithfully represented in (M) |
| Retrieval | Query–memory similarity distribution, reranker margins, evidence diversity, temporal/entity filters, retrieved coverage estimate | Gold evidence exists in (M) but not in (R_q) |
| Answering | Evidence-to-claim citation coverage, contradiction checks, answer confidence calibration, unsupported-claim detector | Sufficient evidence in (R_q), but answer fails adjudicated rubric |

Similarity or confidence alone is not proof of a failure mode. Diagnostics should be calibrated on held-out data and may abstain.

### 4.1 Provenance requirement

Each stored memory item should optionally carry:
- stable item identifier;
- source conversation/session and source span identifiers;
- creation and update timestamps;
- entity/event/claim identifiers;
- transformation lineage (extract, merge, summarize, compress);
- confidence and uncertainty metadata;
- temporal validity or supersession relation, where applicable.

Store only metadata needed for reproducibility and user-approved memory operation. Apply privacy, retention, and dataset licensing requirements.

## 5. MFAR architecture

MFAR has five components:

1. **Traceable memory builder:** produces candidate memory units and provenance links.
2. **Compression auditor:** compares candidate units with the compressed representation.
3. **Failure estimator:** estimates a multi-label vector and uncertainty.
4. **Intervention controller:** selects a targeted action subject to budgets.
5. **Evidence-grounded answerer:** answers from retrieved evidence, cites internal evidence IDs, and abstains when support is insufficient.

The estimator returns:
[
\hat{\mathbf p}_q =
[p_c,p_p,p_r,p_a], \qquad p_i \in [0,1],
]
plus an observability mask (\mathbf o_q\) and uncertainty estimate (u_q).

The vector is multi-label. It is not normalized to sum to one.

## 6. Targeted interventions

| Diagnosis | Candidate intervention | What it cannot fix |
|---|---|---|
| High construction risk | Re-scan source window; extract missed entities, events, preferences, or changes; add traceable memory candidates | Cannot recover source data that is unavailable |
| High compression risk | Reconstruct from provenance; preserve omitted qualifiers, dates, relations, and uncertainty; selectively re-compress | Cannot guarantee fidelity if original source/provenance was discarded |
| High retrieval risk | Query expansion; temporal/entity-aware filtering; diversify candidates; rerank; increase top-k only within budget | Cannot retrieve evidence absent from stored memory |
| High answering risk | Evidence-constrained generation; claim-level support checking; contradiction handling; ask clarification or abstain | Cannot make insufficient evidence sufficient |

An intervention may target more than one mode when the diagnosis is ambiguous. The controller should prefer a low-cost diagnostic action when uncertainty is high.

## 7. Controller objective

Let (a\) be a candidate intervention, (\Delta Q(a\mid q)\) its expected improvement in answer quality, (\Delta C(a\mid q)\) its incremental cost, and (\rho(a)\) its risk (for example, introducing stale or contradictory memory).

A simple initial controller is:
[
a^* = \arg\max_{a\in\mathcal A}
\left[
\widehat{\Delta Q}(a\mid q)
-\lambda_C\widehat{\Delta C}(a\mid q)
-\lambda_R\widehat{\rho}(a\mid q)
\right]
]
subject to storage, retrieval, latency, and privacy constraints.

The estimates must be learned or calibrated on development data. The initial implementation should use transparent rules and log every decision; a learned policy can be tested later. Do not tune controller thresholds on the final test set.

### 7.1 Abstention and observability

If required provenance is unavailable, mark the corresponding mode unobservable. If diagnostic uncertainty exceeds a development-set threshold, do not take an expensive irreversible action. Choose a reversible diagnostic step, use ordinary retrieval, or abstain/ask for clarification.

## 8. Algorithm sketch

**Input:** query (q), stored memory (M), optional source archive (X), provenance trace (P), budgets (B_s,B_r).

**Output:** answer (A_q), evidence IDs, diagnosis, selected action, and cost trace.

1. Parse the query into answer requirements (entities, relations, time constraints, requested attributes).
2. Load available provenance and set the observability mask.
3. Retrieve an initial low-cost candidate set from (M).
4. Compute retrieval coverage, relevance, diversity, temporal consistency, and confidence features.
5. If source and pre-compression traces exist, compute construction and compression coverage diagnostics.
6. Estimate the multi-label failure probabilities and uncertainty.
7. If uncertainty is high, run a reversible diagnostic or retain the baseline retrieval policy.
8. Generate feasible targeted interventions and estimate quality gain, cost, and risk.
9. Select the highest-utility feasible action; log its rationale.
10. Execute the action and assemble the evidence set within (B_r).
11. Generate an answer grounded in evidence IDs.
12. Verify each material answer claim against evidence; if support is insufficient or contradictory, qualify, clarify, or abstain.
13. Log the final answer, evidence, diagnosis, intervention, latency, token usage, and provenance references.

### 8.1 Pseudocode

```text
function MFAR(query, memory, provenance, source_archive, budgets):
    requirements = parse_query(query)
    observability = inspect_available_traces(provenance, source_archive)

    initial = retrieve(memory, requirements, budget=budgets.initial)
    features = diagnose_features(
        requirements, initial, memory, provenance, source_archive,
        observability
    )

    probabilities, uncertainty = failure_estimator(features, observability)

    if uncertainty > calibrated_uncertainty_limit:
        action = low_cost_reversible_diagnostic(features)
    else:
        actions = feasible_interventions(probabilities, budgets)
        action = argmax_expected_utility(actions)

    evidence = execute_and_retrieve(action, memory, provenance, budgets)
    draft = answer_with_evidence_ids(query, evidence)
    verdict = verify_claim_support(draft, evidence)

    if verdict == INSUFFICIENT_OR_CONTRADICTORY:
        answer = qualify_or_abstain(draft, verdict)
    else:
        answer = draft

    return answer, evidence.ids, probabilities, action, cost_trace
```

This is a design sketch, not production-ready code. Each function needs an explicit interface and tests before implementation.

## 9. Evaluation protocol

### 9.1 Required baselines

At minimum compare:
1. Existing MemWeave baseline.
2. Fixed top-k retrieval.
3. Fixed retrieval with query expansion.
4. Confidence-only adaptive retrieval (no failure taxonomy).
5. MFAR with all diagnostics and interventions.
6. MFAR ablations removing one failure-mode family at a time.

Where feasible, include a strong current memory/retrieval baseline under the same data, budget, and answer-generation conditions. Document implementation and configuration differences.

### 9.2 Metrics

**Evidence stage**
- Evidence recall and precision.
- Gold evidence rank / reciprocal rank.
- Evidence-set sufficiency.
- Redundancy and diversity.
- Memory coverage before and after compression.

**Answer stage**
- Exact match or benchmark-provided score where appropriate.
- Token-level F1 where appropriate.
- Claim-level factuality / evidence support.
- Completeness and contradiction rate.
- Abstention quality and calibration.

**Diagnostic stage**
- Per-mode precision, recall, F1, AUROC/AUPRC where class balance permits.
- Calibration (Brier score or expected calibration error).
- Multi-label confusion and unobservable rate.
- Diagnostic performance by question type and conversation length.

**Efficiency**
- Stored tokens/bytes.
- Retrieved and prompt tokens.
- Latency (median and tail).
- Model calls and monetary cost, if measurable.
- Quality at matched budgets and quality–cost curves.

Evidence recall must not be presented as answer accuracy.

### 9.3 Controlled comparisons

- Use identical conversation splits and source revisions for all methods.
- Split by conversation/cluster, not merely by question, when questions share source conversations.
- Fit feature scalers, diagnostic models, and policy thresholds on training/development data only.
- Lock the test set before final evaluation.
- Use paired question- or conversation-cluster bootstrap intervals, respecting the sampling unit.
- Predeclare primary outcomes and comparisons; correct for multiple testing where applicable.
- Report all variants, failed runs, missing traces, and deviations.
- Repeat with at least one additional dataset; transfer evidence is not independent replication if data or code paths overlap.

## 10. Ablation plan

| Ablation | Removed component | Main question |
|---|---|---|
| A1 | Construction diagnosis/intervention | Does source-aware recovery add value? |
| A2 | Compression audit/recovery | Does fidelity tracking matter? |
| A3 | Retrieval diagnosis/adaptation | Does targeted retrieval beat fixed retrieval? |
| A4 | Answer verification | Does answer-stage control improve factual support? |
| A5 | Uncertainty/abstention | Does uncertainty handling prevent harmful interventions? |
| A6 | Provenance metadata | What performance and auditability are lost without traces? |
| A7 | Controller; use fixed policy | Does diagnosis-driven action selection add value beyond the components alone? |

Also test storage/retrieval budget sweeps and long, conflicting, stale, and temporally updated facts.

## 11. Complexity and systems considerations

Let (N) be the number of memory units, (d) embedding dimension, (k) retrieved candidates, and (m) candidate memory units considered for a source-aware audit.

- A brute-force dense similarity retrieval costs (O(Nd)) per query; an approximate nearest-neighbor index changes practical retrieval cost but must be reported.
- Reranking (k) candidates depends on the chosen reranker and input lengths; report actual model calls and latency rather than implying a universal asymptotic bound.
- A linear failure estimator over feature dimension (f) costs (O(f)) per query after feature construction.
- Provenance coverage audits may cost (O(m)) if indexed by claim/source IDs; unindexed semantic comparisons can be substantially more expensive.
- Source re-scanning and re-compression are potentially expensive and should be invoked selectively.

MFAR must be compared at matched cost budgets. An improvement obtained only by spending more tokens or model calls is not evidence of a more efficient controller.

## 12. Threats to validity

1. **Label ambiguity:** construction, compression, retrieval, and answering failures may co-occur. Define annotation rules and permit multi-label outcomes.
2. **Incomplete observability:** without source and transformation traces, early-stage failures cannot be diagnosed reliably.
3. **Oracle leakage:** reference evidence and answers are for evaluation only, never online controller input.
4. **Benchmark contamination:** inspect dataset use, prompt exposure, and model pretraining risks where possible.
5. **Metric mismatch:** evidence recall may rise without answer quality improving.
6. **Cost confounding:** adaptive methods may use more calls or tokens; compare at matched budgets.
7. **Threshold overfitting:** choose thresholds and policies on development data only.
8. **Dataset dependence:** results on one benchmark do not establish generality.
9. **Annotation reliability:** use clear rubrics and report inter-annotator agreement for manually labelled subsets.
10. **Novelty uncertainty:** the four-stage decomposition and individual techniques may overlap prior work. A literature review and closest-work comparison are required before claiming algorithmic novelty.

## 13. Minimum viable implementation plan

Implement in the following order:

**M0 — Trace schema**
- Define memory item, provenance, transformation, and evidence ID schemas.
- Add deterministic logging and unit tests.
- Do not change the existing baseline.

**M1 — Offline failure labels**
- Build a small, carefully annotated trace dataset.
- Label the four modes independently.
- Measure agreement and label coverage.
- Establish how often each mode is observable.

**M2 — Transparent diagnostics**
- Implement rule-based features and a multi-label baseline estimator.
- Calibrate probabilities on development data.
- Include an explicit unknown/unobservable state.

**M3 — Targeted interventions**
- Add one intervention at a time.
- Start with retrieval and answer-stage actions that can be evaluated without destructive memory mutation.
- Add source re-ingestion and re-compression only when provenance is reliable.

**M4 — Controller and evaluation**
- Compare fixed, confidence-only, and MFAR policies.
- Run ablations and matched-budget tests.
- Evaluate answer quality, not just evidence recall.

**M5 — Generalization**
- Transfer to another dataset and stress-test temporal updates, contradictions, long contexts, and missing provenance.

## 14. Decision gates

Do not claim MFAR is successful unless all relevant gates pass:

- **G1 — Instrumentation:** the pipeline exposes enough traces to label the relevant failure modes.
- **G2 — Diagnostic validity:** diagnostics predict failure labels on held-out conversations.
- **G3 — Intervention value:** targeted interventions improve a predeclared primary outcome over strong baselines.
- **G4 — Efficiency:** gains persist under matched resource budgets or the cost trade-off is explicitly justified.
- **G5 — Generalization:** results replicate on a separate dataset or a clearly independent test setting.
- **G6 — Reproducibility:** code, data revisions, configs, seeds, and evaluation artifacts are auditable.

If a gate fails, narrow the claim and report the failure. Do not relabel a negative result as success.

## 15. Positioning and claims discipline

The current MemWeave evidence-recall experiments motivate this proposal. They do not demonstrate:
- that the four failure modes have been reliably diagnosed;
- that MFAR's interventions improve answer accuracy;
- that MFAR is more efficient than existing systems;
- or that the proposed combination is novel relative to all prior work.

Before publication, conduct a focused literature review covering long-term conversational memory, memory construction and summarization, retrieval-augmented generation, evidence attribution, adaptive retrieval, confidence calibration, and self-correction. Build a closest-work table and state the precise difference supported by that review.

**Permitted current claim:** “We propose a failure-aware memory pipeline and a testable evaluation framework.”

**Not yet permitted:** “MFAR achieves state-of-the-art performance,” “MFAR solves memory failures,” or “MFAR is the first method” without evidence.

---

## References and literature work

No external literature review has been completed in this design document. Add verified primary references, publication details, and a closest-work comparison before making novelty claims. Do not insert unverified citations.

## Appendix A — Required experiment record

Every run should record at least:

- method name and version;
- code commit;
- dataset name, revision, and checksum;
- conversation-level split identifiers;
- model/provider/version and decoding parameters;
- storage and retrieval budgets;
- feature and policy configuration;
- random seeds;
- all primary and secondary metrics;
- paired statistical analysis and sampling unit;
- token usage, latency, and model-call count;
- failed/abstained/unobservable cases;
- output artifact checksums.

## Appendix B — Immediate next engineering task

Create a separate implementation module for MFAR without modifying the existing MemWeave baseline. Begin with the trace schema and offline oracle-label pipeline. Only after those are validated should the failure estimator and adaptive controller be implemented.
