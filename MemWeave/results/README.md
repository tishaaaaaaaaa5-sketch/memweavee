# MemWeave results

Results are grouped by experiment generation so the source notebook and its outputs remain aligned.

## v2.2

`v2_2/` contains the 500-question run findings, run manifest, primary Setting A/B tables, ablation/category/evidence-group tables, efficiency measurements and LoCoMo paired/external summary. The v2.2 narrative findings are historical; read the v2.3 corrected-inference findings before making H2/H3 claims.

## v2.3 corrected inference

The root of this folder contains the compact, reviewable outputs from the v2.3 corrected-inference addendum. These files are intended to be read alongside `../notebooks/03_memweave_v2_3_addendum.ipynb`.

- `findings_v2_3.txt` — concise narrative findings and caveats.
- `tables/` — H2 Holm comparison, specification curve, budget sweep, abstention sensitivity, component activity/ledger, benchmark artifact facts, LoCoMo power, QA-proxy context, exposure gradient, audit lift and related-work ledger.

## Interpretation

The corrected v2.3 analysis finds a small, analysis-sensitive gain over `low_novelty` (+0.028 recall). It passes the de-duplicated eight-comparison Holm family but not the four-budget Holm sensitivity or the abstention-exclusion sensitivity. Report it as fragile, not robust superiority.

The redundancy penalty and cost-awareness components were inactive in the audited folds; their ablations are vacuous. Pairwise-similarity features account for much of the measured signal. QA-proxy accuracy is supplementary and is not an official LLM-judge score.

## Provenance and large artifacts

The original `results.zip` is about 135 MB and contains the LongMemEval-S JSON dataset (about 277 MB uncompressed), LoCoMo data, a feature cache, raw result exports and plots. The archive cannot be committed as a normal Git file because it exceeds GitHub's 100 MB per-file limit. The full raw export `all_results_raw.csv` is about 34 MB; the feature cache is about 10 MB. Large artifacts should be published through Git LFS or a dedicated artifact store.

The tables committed here are a curated, human-reviewable subset of the full archive. The raw archive, full raw CSV, feature cache, benchmark datasets and plot image have not been uploaded in this pass.

### Full archive checksum

Original `results.zip` SHA-256: `6f9d54fab2b9870c16982ef0d77e1e4b80204f27ab7018756da664ba34be1c35` (135,252,137 bytes). Use this to verify the original archive if you transfer it through Git LFS or an artifact store.
