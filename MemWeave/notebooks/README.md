# Notebook index

This directory is the canonical notebook sequence for the MemWeave research project. Version numbers describe the research progression; exported copies are not separate research versions.

| Order | Canonical file | Role | Output status |
|---|---|---|---|
| 00 | `00_MemWeave_2_0.ipynb` | Initial real-data pipeline, MLP/heuristic comparisons and early ablations | Uploaded source notebook; no saved outputs in the supplied copy |
| 01 | `01_MemWeave_2_1.ipynb` | Fair-baseline and benchmark-structure audit | Executed notebook copy with saved cell outputs |
| 02 | `02_MemWeave_2_2.ipynb` | Revised model selection, tuning and external/QA analyses | Uploaded source notebook; run outputs are preserved separately under `../results/v2_2/` |
| 03 | `03_memweave_v2_3_addendum.ipynb` | Corrected inference, component activity, abstention and power audits | Standalone addendum; reads saved outputs and does not retrain the model |
| 04 | `04_MemWeave_Final.ipynb` | Leak-controlled, pre-declared, locked-test evaluation | Uploaded source notebook; no saved execution outputs were supplied |

## Recommended execution

1. Read the main [project guide](../README.md) and the matching result notes before running an experiment.
2. Run v2.0 and v2.1 only when reproducing those historical stages.
3. For v2.2, follow its setup/configuration cells and preserve the generated run manifest and tables in `../results/v2_2/`.
4. Run the v2.3 addendum against the saved v2.2 artifacts. It is an analysis layer, not a fresh training run.
5. Treat the final notebook as a separate locked-test stage. Run it from a clean kernel and preserve outputs, configuration, dataset checksums and a run manifest before reporting any final-test result.

## Duplicate uploads and archive

The supplied files contained multiple copies of the v2.1 notebook, including Kaggle/export filenames. Identical source-only copies are not presented as separate research versions. The `archive/` subfolder preserves historical exported copies for auditability; use the numbered canonical notebooks above for navigation.

## Data and artifact safety

Benchmark JSONs, large raw per-question CSVs and feature-cache pickles are not stored in this notebook directory. Keep those outside ordinary Git history unless their license, size and reproducibility requirements have been reviewed. See [the results guide](../results/README.md).
