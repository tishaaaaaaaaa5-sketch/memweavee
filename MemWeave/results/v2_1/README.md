# v2.1 audit diagnostics

This folder contains the compact, reviewable diagnostics extracted from the uploaded `memweave2_results` archive. The archive is a v2.1 artifact bundle, not the v2.2 or v2.3 result set.

## Included files

- `tables/table_feature_auc.csv` — univariate feature AUCs and confidence intervals (20 features).
- `tables/table_nearest_neighbour_summary.csv` — aggregate summary over the 324 question-level nearest-neighbour diagnostic rows.
- `figures/` — reserved for plots that are intentionally curated for publication.

## Headline diagnostic

Across 324 questions, the mean observed rate that a gold evidence session's nearest neighbour is also gold is 0.820, versus a mean question-specific chance rate of 0.030. This is a benchmark-structure diagnostic, not a model performance score. The per-question source table remains in the original archive and is not duplicated here.

The feature AUC table shows centrality as the strongest listed univariate feature (AUC 0.730); novelty (0.215), rare fraction (0.277), and rarity mean (0.313) are directionally lower for evidence sessions in this evaluation. These results are dataset-specific diagnostics, not universal feature properties.

## Artifact hygiene

The uploaded archive also contains `all_results_raw.csv` (~32.5 MB) and a serialized feature cache (~10.2 MB). They are intentionally not committed as normal Git files: use the notebooks to regenerate them, or publish large derived artifacts through a versioned release / external artifact store. The uploaded ZIP SHA-256 is:

`7e5e5519ce66934c0b569fd25946cf9a3b57b91188cf1dcb7c6662a8872bae48`

