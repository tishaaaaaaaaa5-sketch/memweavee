# MemWeave research project

MemWeave investigates query-agnostic memory retention: given a conversation history and a fixed token budget, which sessions should be kept so later questions can still be answered?

## Research setup

- **Benchmark:** LongMemEval-S (500-question evaluation in the reported run).
- **Primary setting:** memory selection without access to the future question.
- **Primary metric:** session-level evidence recall.
- **Primary budget:** 10% of each history's token count; 5%, 20% and 30% are secondary budget checks.
- **Baselines:** recency, random selection, and non-learned heuristic/single-feature rules.
- **External validation:** LoCoMo is reported separately and should not be conflated with the LongMemEval-S primary evaluation.

## Notebook reading order

1. `notebooks/01_MemWeave_2_1.ipynb` — v2.1 research pipeline and fair-baseline audit.
2. `notebooks/02_MemWeave_2_2.ipynb` — v2.2 revised tuning, inference and audit protocol.
3. `notebooks/03_memweave_v2_3_addendum.ipynb` — corrected inference and evidence-limit addendum; run after the v2.2 analysis.
4. `notebooks/04_MemWeave_Final.ipynb` — leak-controlled, locked-test evaluation stage.

Do not treat similarly named Kaggle/export copies as separate research versions. The repository keeps one canonical copy of each version.

## Reproduction

Use Python in Jupyter or Google Colab. Run notebooks from top to bottom and inspect each configuration cell before execution. The v2.2 notebook downloads LongMemEval-S cleaned if it is not already available, and writes run outputs under `memweave2_results/v2_2/`. The v2.3 addendum reads the saved results and dataset; it does not rerun model training or change the split.

The notebooks may use NumPy, pandas, Matplotlib, SciPy, scikit-learn, and optional tokenizer/dense-retrieval packages. Follow the imports and optional dependency checks in each notebook; the exact environment can affect tokenizer and dense-feature behavior.

## Results interpretation

The corrected v2.3 analysis reports a small, fragile advantage over `low_novelty` in one de-duplicated comparison (+0.028 recall; Holm-adjusted p=0.035), but the result is not robust across the full sensitivity set: the four-budget Holm result and abstention sensitivity do not pass the adjusted threshold. Therefore, do not state that MemWeave robustly outperforms the strongest simple rule.

The component audit found that pairwise-similarity features carry much of the measured signal. Redundancy penalty and cost-awareness were inactive in the audited folds and their ablations are vacuous. QA-proxy results are supplementary, not an official LLM-judge score.

See [results/README.md](results/README.md) and the accompanying tables for the precise values and caveats.

## Data and large files

Do not commit raw benchmark datasets, feature caches, or the 135 MB `results.zip` as ordinary Git files. The archive contains the 277 MB LongMemEval-S JSON, a feature cache, raw result exports and plots. Store large artifacts with Git LFS or an external artifact store, and document the download location and checksum if you publish them.

## Citation and claims

When writing about this project, cite the benchmark and related methods independently. Clearly distinguish confirmatory/pre-specified tests from post-hoc analyses, and report the negative/fragile findings alongside positive results.
