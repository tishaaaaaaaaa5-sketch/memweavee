# Notebook index

## Canonical research sequence

Run these in order, using the same intended benchmark files and configuration described in each notebook:

1. `01_MemWeave_2_1.ipynb` — v2.1 baseline and audit revision.
2. `02_MemWeave_2_2.ipynb` — v2.2 inference/tuning revision.
3. `03_memweave_v2_3_addendum.ipynb` — corrected inference addendum; reads saved v2.2 outputs.
4. `04_MemWeave_Final.ipynb` — leak-controlled, locked-test evaluation stage.

## Archive

The `archive/` subfolder preserves alternate or executed notebook exports that are useful for auditability but are not part of the canonical run order:

- `01_MemWeave_2_1_executed_outputs.ipynb` — executed v2.1 notebook export with cell outputs preserved.
- `02_v2_3_addendum_results_zip_runner.ipynb` — standalone v2.3 addendum variant that extracts and reads the supplied `results.zip`.

The unexecuted Kaggle/export copy of v2.1 is the canonical v2.1 notebook; identical source-only duplicate copies have been omitted to avoid confusion.
