# MemWeave results

Results are grouped by experiment generation so source notebooks, run manifests and outputs remain aligned. The repository keeps compact, reviewable tables and metadata; large raw exports, benchmark JSONs and feature caches are intentionally excluded from ordinary Git history.

## v2.0 historical baseline

`v2_0/` contains the curated tables and original run manifest from the v2.0 archive. These are historical outputs from the initial pipeline and should not be quoted as the project's final result.

## v2.1 benchmark audit

`v2_1/` contains the feature-AUC and nearest-neighbour diagnostics extracted from the v2.1 archive. The nearest-neighbour diagnostic is important context for the later evidence-clustering audit.

## v2.2 main run

`v2_2/` contains the 500-question run findings, run manifest, primary Setting A/B tables, ablation/category/evidence-group tables, efficiency measurements and LoCoMo paired/external summary. The v2.2 narrative findings are historical; read the v2.3 corrected-inference findings before making H2/H3 claims.

## v2.3 corrected inference

The root of this folder contains compact, reviewable outputs from the v2.3 corrected-inference addendum. These files are intended to be read alongside `../notebooks/03_memweave_v2_3_addendum.ipynb`.

- `findings_v2_3.txt` — concise narrative findings and caveats.
- `tables/` — H2 Holm comparison, specification curve, budget sweep, abstention sensitivity, component activity/ledger, benchmark artifact facts, LoCoMo power, QA-proxy context, exposure gradient, audit lift and related-work ledger.

## Interpretation

The corrected v2.3 analysis finds a small, analysis-sensitive gain over `low_novelty` (+0.028 recall). It passes the de-duplicated eight-comparison Holm family but not the four-budget Holm sensitivity or the abstention-exclusion sensitivity. Report it as fragile, not robust superiority.

The redundancy penalty and cost-awareness components were inactive in the audited folds; their ablations are vacuous. Pairwise-similarity features account for much of the measured signal. QA-proxy accuracy is supplementary and is not an official LLM-judge score.

## Provenance and large artifacts

The original `results.zip` is about 135 MB and contains the LongMemEval-S JSON dataset (about 277 MB uncompressed), LoCoMo data, a feature cache, raw result exports and plots. The archive cannot be committed as a normal Git file because it exceeds GitHub's 100 MB per-file limit. The full raw export `all_results_raw.csv` is about 34 MB; the feature cache is about 10 MB. Large artifacts should be published through Git LFS or a dedicated artifact store.

The tables committed here are curated, human-reviewable subsets of the full archives. Raw per-question exports, feature caches and benchmark datasets are not copied into the source tree.

### Full archive checksum

Original v2.2 `results.zip` SHA-256: `6f9d54fab2b9870c16982ef0d77e1e4b80204f27ab7018756da664ba34be1c35` (135,252,137 bytes). Use this to verify the original archive if you transfer it through Git LFS or an artifact store.
