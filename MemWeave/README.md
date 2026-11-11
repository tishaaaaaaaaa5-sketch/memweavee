# MemWeave research project

MemWeave investigates query-agnostic memory retention: given a conversation history and a fixed token budget, which sessions should be kept so later questions can still be answered?

## Research setup

- **Benchmark:** LongMemEval-S (cleaned), 500-question evaluation in the reported runs.
- **Primary setting:** memory selection without access to the future question.
- **Primary metric:** session-level evidence recall.
- **Primary budget:** 10% of each history's token count; 5%, 20% and 30% are secondary budget checks.
- **Baselines:** recency, random selection, and non-learned heuristic/single-feature rules.
- **External validation:** LoCoMo is reported separately and should not be conflated with the LongMemEval-S primary evaluation.

## Canonical research sequence

See [the notebook index](notebooks/README.md) for the role and execution status of each file.

1. `notebooks/00_MemWeave_2_0.ipynb` — initial real-data pipeline and early model/heuristic comparisons.
2. `notebooks/01_MemWeave_2_1.ipynb` — fair-baseline and benchmark-structure audit; the supplied canonical copy preserves executed cell outputs.
3. `notebooks/02_MemWeave_2_2.ipynb` — revised tuning, inference, and external/QA analyses.
4. `notebooks/03_memweave_v2_3_addendum.ipynb` — corrected inference and evidence-limit addendum; reads saved outputs and does not rerun model training.
5. `notebooks/04_MemWeave_Final.ipynb` — leak-controlled, post-hoc held-out evaluation stage; the supplied copy has no saved outputs and the held-out split was inspected during earlier development.

The multiple v2.1 Kaggle/export copies were consolidated into one canonical notebook. They are not separate research versions.

## Reproduction

Use Python in Jupyter or Google Colab. Run notebooks from top to bottom and inspect each configuration cell before execution. The v2.2 notebook writes run outputs under `memweave2_results/v2_2/` in its default configuration. The v2.3 addendum reads saved results and dataset files; it does not retrain or change the split.

The notebooks may use NumPy, pandas, Matplotlib, SciPy, scikit-learn, and optional tokenizer/dense-retrieval packages. Follow the imports and optional dependency checks in each notebook; the exact environment can affect tokenizer and dense-feature behavior.

## Results interpretation

The corrected v2.3 analysis reports a small, fragile advantage over `low_novelty` in one de-duplicated comparison (+0.028 recall; Holm-adjusted p=0.035), but the result is not robust across the full sensitivity set: the four-budget Holm result and abstention sensitivity do not support a reliable advantage. Therefore, do not state that MemWeave robustly outperforms the strongest simple rule.

The component audit found that pairwise-similarity features carry much of the measured signal. Redundancy penalty and cost-awareness were inactive in the audited folds and their ablations are vacuous. QA-proxy results are supplementary, not an official LLM-judge score.

See [results/README.md](results/README.md) and the accompanying tables for the precise values and caveats. Historical v2.0 outputs are preserved separately under [results/v2_0/](results/v2_0/).

## Data and large files

Do not commit raw benchmark datasets, feature caches, or the 135 MB `results.zip` as ordinary Git files. The archive contains the 277 MB LongMemEval-S JSON, a feature cache, raw result exports and plots. Store large artifacts with Git LFS or an external artifact store, and document the download location and checksum if you publish them.

## Citation and claims

When writing about this project, cite the benchmark and related methods independently. Clearly distinguish confirmatory/pre-specified tests from post-hoc analyses, and report the negative/fragile findings alongside positive results.
