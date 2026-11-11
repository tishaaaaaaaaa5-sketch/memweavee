# MemWeave results

This folder contains the compact, reviewable outputs from the v2.3 corrected-inference addendum. These files are intended to be read alongside the notebook in `../notebooks/03_memweave_v2_3_addendum.ipynb`.

## Files

- `findings_v2_3.txt` — concise narrative findings and caveats.
- `tables/table_h2_holm_corrected.csv` — primary learned-policy vs baseline comparison family.
- `tables/table_h2_spec_curve.csv` — sensitivity/specification curve for the H2 result.
- `tables/table_budget_sweep_holm.csv` — multiple-comparison-adjusted budget checks.
- `tables/table_abstention_sensitivity.csv` — sensitivity excluding abstention-labelled questions.
- `tables/table_component_ledger.csv` and `table_component_activity.csv` — component contributions and whether ablations were actually active.
- `tables/table_artifact_facts.csv` — benchmark artifact audit facts.
- `tables/table_locomo_power.csv` — external-validation effect and detectable-effect context.
- `tables/table_qa_power.csv` and `table_retention_vs_qa.csv` — supplementary QA-proxy context.

## Interpretation

The primary v2.3 comparison against `low_novelty` is small (+0.028 recall) and fragile. It passes the de-duplicated eight-comparison Holm family but does not pass the four-budget Holm sensitivity or the abstention-exclusion sensitivity. Report it as a small, analysis-sensitive gain, not robust superiority.

The redundancy penalty and cost-awareness components were inactive in the audited folds; their ablations are vacuous. Pairwise-similarity features account for much of the measured signal. QA-proxy accuracy is supplementary and is not an official LLM-judge score.

## Provenance and missing large artifacts

The original `results.zip` (about 135 MB) also contains large raw outputs, plots, the feature cache and the 277 MB LongMemEval-S source dataset. It cannot be committed as a normal Git file because GitHub's standard per-file limit is 100 MB. Large artifacts should be published through Git LFS or a dedicated artifact store. The compact CSV/TXT files here are a curated subset for inspection; they are not a replacement for the full archive.
