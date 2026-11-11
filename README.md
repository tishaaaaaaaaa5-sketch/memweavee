# MemWeave
### Budget-Constrained Memory Retention for Long-Horizon Conversational Assistants

MemWeave studies **query-agnostic session-memory retention**: when an assistant cannot keep its entire conversation history, which sessions should it preserve under a fixed token budget so that future questions remain answerable?

The project evaluates learned retention policies and interpretable session features on LongMemEval-S, compares them with simple baselines, and audits whether apparent gains survive corrected inference, harder distractor pools, and external evaluation.

> **Research takeaway:** The strongest contribution is the benchmark and evaluation audit—not a claim of robust algorithmic superiority. The learned selector's advantage over the best simple rule is small and sensitive to analysis choices, and it does not clearly transfer to the same-pipeline distractor pool or LoCoMo.

---

## At a glance

| Item | Description |
|---|---|
| Problem | Retain useful conversation sessions under a fixed token budget |
| Primary setting | Query-agnostic retention (the future question is unknown at selection time) |
| Main benchmark | LongMemEval-S (cleaned), 500 questions |
| External evaluation | LoCoMo; restricted usable subset reported in the research report |
| Primary budget | 10% of history tokens; also evaluated at 5%, 20%, and 30% |
| Primary metric | Session-level evidence recall |
| Learned selector | Logistic regression (LR); HistGradientBoosting (HGB) comparison |
| Feature families | Recency/length, temporal signals, rarity, importance cues, novelty, and pairwise similarity |
| Statistical analysis | Paired bootstrap, Holm correction, equivalence checks, sensitivity/specification analyses |

## Main findings

### Query-agnostic retention (Setting B, 10% budget)

| Selector | Evidence recall |
|---|---:|
| MemWeave-LR | **0.411** |
| Best simple rule: `low_novelty` | 0.383 |
| Difference | **+0.028** [+0.004, +0.052] |

The +0.028 difference passes the de-duplicated eight-comparison Holm family (adjusted p = 0.035), but it is **not robust across the full sensitivity analysis**. The four-budget Holm sensitivity and abstention-exclusion sensitivity do not support a reliable advantage. On a same-pipeline distractor pool, the difference is +0.004 [-0.023, +0.030], and on LoCoMo it is +0.007 [-0.010, +0.026]; both are statistically compatible with no difference.

### Question-known retrieval (Setting A)

When the question is available at selection time, MemWeave-LR-Q reaches 0.903 recall, compared with 0.871 for TF-IDF, 0.866 for BM25, and 0.859 for dense retrieval. The full-history BM25 reference is 0.911 at recall@5. This is a different, question-aware setting and should not be conflated with the primary query-agnostic retention task.

### What the audit revealed

- All 948 gold evidence-session IDs in the audited pool use the `answer_` prefix, while none of 22,919 non-gold IDs do. IDs and answer flags were not model features, but the pool construction exposes a benchmark shortcut.
- For questions with multiple evidence sessions, evidence sessions are unusually clustered: the nearest neighbour of an evidence session is another evidence session at an observed rate of 0.82 versus 0.03 chance.
- The learned selector's signal is concentrated in questions with two or more evidence sessions; single-evidence questions remain close to random.
- Pairwise-similarity features carry much of the measured signal. The temporal-engine contribution does not survive the reported Holm correction.
- Redundancy and cost-awareness terms were inactive in all 15 audited folds (`lambda = gamma = 0`); their ablations therefore do not establish that these mechanisms help.
- Retention recall is not the same as downstream answer accuracy. The small QA proxy is supplementary and underpowered; it is not an official LLM-judge evaluation.

**Interpretation:** MemWeave is best presented as a careful study of budgeted conversational-memory retention and benchmark validity, with a useful negative/fragile result and concrete lessons for future evaluations.

## Method overview

1. **Represent each session** with interpretable signals: recency and length; temporal/update cues; vocabulary rarity; importance cues; novelty; and pairwise similarity/centrality.
2. **Estimate retention utility** using learned selectors. The later pipeline uses logistic regression as the primary model and HGB as a comparison.
3. **Select within a token budget** using a budgeted optimization stage with utility, redundancy, and cost terms. The audit found that some intended terms were not active in the reported folds, which limits the mechanism claims.
4. **Evaluate retention** against evidence-session labels at multiple memory budgets, with paired uncertainty estimates and multiple-comparison/sensitivity analyses.
5. **Audit generalization and validity** using distractor-pool analysis, LoCoMo, component checks, and a supplementary downstream QA proxy.

Token counts in the reported pipeline use `tiktoken` with `cl100k_base`. Similarity signals include TF-IDF, BM25, and `all-MiniLM-L6-v2`.

## Repository guide

The repository contains a versioned research workflow and curated outputs:

- [Project guide](MemWeave/README.md) — notebook order, setup notes, and reproduction guidance.
- [Research overview](MemWeave/PROJECT_OVERVIEW.md) — concise scope and limitations.
- [Notebooks](MemWeave/notebooks/) — versioned experiments, addendum, and final locked-test notebook.
- [Results guide](MemWeave/results/README.md) — result generations, provenance, and interpretation.
- [Corrected v2.3 findings](MemWeave/results/findings_v2_3.txt) — compact corrected-inference summary.
- [Results tables](MemWeave/results/tables/) — curated tables supporting the audit and sensitivity findings.

### Recommended reading order

1. Read this README for the research question and headline findings.
2. Read `MemWeave/README.md` for the experiment/reproduction sequence.
3. Inspect the v2.2 results and run manifest for the original experiment.
4. Read the v2.3 corrected-inference findings and tables before quoting the learned-selector comparison.
5. Treat `04_MemWeave_Final.ipynb` as an unexecuted, post-hoc held-out evaluation notebook. Its split was inspected during earlier development, so it is not a pristine preregistered test. The supplied notebook has no saved outputs; do not report a final held-out result until a full run, dataset checksums, environment manifest and outputs are committed.

## Reproducibility and data

The notebooks are intended for Jupyter or Google Colab. Follow each notebook's setup and dependency checks, then run cells in order. Exact package versions, tokenizer availability, and dense-encoder setup can affect feature generation.

The benchmark JSONs, feature cache, and large raw exports are **not included as ordinary Git files**. The original `results.zip` is approximately 135 MB and contains a LongMemEval-S JSON of approximately 277 MB uncompressed, LoCoMo data, a feature cache, raw result exports, and plots. GitHub's ordinary file limit is 100 MB; use Git LFS or a dedicated artifact host for large files. Do not commit private or license-restricted benchmark data without checking its distribution terms.

The published curated results are a reviewable subset of the full experiment artifacts. See [the results provenance notes](MemWeave/results/README.md) for the recorded archive checksum and artifact details.

## Limitations and reporting guidance
- The QA proxy uses 100 questions and a small reader model. It should not be presented as definitive answer-quality validation.
- The related-work ledger is a research aid; its entries were not all full-text verified. Verify sources independently before citing them in a paper.

## Research status and next experiments

The most valuable next steps are to execute and preserve the final locked-test notebook outputs, tune the optimizer over genuinely active redundancy/cost settings and test those mechanisms, evaluate answer quality with a substantially larger and stronger-reader study, and validate on a harder-distractor benchmark with more independent conversation clusters.

---

*Research snapshot: MemWeave v2.1–v2.3 addendum and final locked-test notebook inventory, as documented in the project report dated November 11, 2026.*
