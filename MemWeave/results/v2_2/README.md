# v2.2 run outputs

These are compact tables and the run manifest extracted from the v2.2 results archive. The full archive also contains large raw result CSVs, plots, feature caches and benchmark datasets; see the top-level results README for the artifact limitation.

## Provenance

- Benchmark: LongMemEval-S cleaned
- Questions: 500
- Seeds: 100, 101, 102
- Folds: 5
- Primary budget: 10%; secondary budgets: 5%, 20%, 30%
- Tokenizer: tiktoken/cl100k_base
- Dense baseline: enabled
- Main metric: session-level evidence recall
- Important audit flag: session-ID evidence leakage was confirmed in the benchmark file; IDs and per-turn has_answer flags were not used as model features.

The v2.2 findings are superseded for H2/H3 interpretation by the v2.3 corrected-inference files in `../`.
