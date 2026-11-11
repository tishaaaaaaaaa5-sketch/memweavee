# MemWeave v2.0 results

This directory contains a curated, reviewable subset of the original v2.0 result archive. The full archive also includes a 22 MB per-question CSV and a 10 MB feature cache; those bulky intermediate artifacts are intentionally not duplicated into the repository.

## Included artifacts

- `run_manifest.json` — dataset checksum, code version, seeds, folds, budgets, tokenizer, model and environment metadata.
- `tables/table_main_A.csv` — question-known retrieval results.
- `tables/table_main_B.csv` — primary query-agnostic retention results.
- `tables/table_category_B.csv` — Setting B breakdown by question type.
- `tables/table_ablation.csv` and `tables/table_ablation_paired.csv` — component and paired ablation summaries.
- `tables/table_efficiency.csv` — token use and timing summary.
- `tables/table_ceiling.csv` — full-history BM25 reference.
- `tables/table_h4_temporal.csv` — temporal-engine category comparison.

## Interpretation

These are historical v2.0 outputs, not the final corrected result. Later versions revised the model and inference protocol, and the v2.3 addendum documents why the early headline advantage should not be treated as robust evidence of superiority. Read the current top-level research report and v2.3 findings before citing any v2.0 number.

## Provenance

Source archive: `memweave2_results.zip` (uploaded with the project materials). The original archive's raw per-question export and feature cache are not copied here.
