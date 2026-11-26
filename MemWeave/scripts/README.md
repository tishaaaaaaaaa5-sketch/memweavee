# MemWeave reproducibility utilities

These scripts make the committed experiment record easier to inspect. They do **not** claim to reproduce model training or the held-out evaluation without the original benchmark file and per-question outputs.

## Validate the committed aggregate release

From the repository root:

```bash
python MemWeave/scripts/validate_release.py
```

Expected behavior for the current snapshot:
- checks that the run manifest and paired audit agree on sample size and headline metrics;
- checks that the paired gain equals role-aware recall minus baseline recall;
- checks confidence-interval bounds;
- checks that question-type sample counts sum to the 235 held-out questions and that category values are internally consistent;
- exits non-zero if a required artifact is missing or inconsistent.

The validator should emit warnings because the current snapshot does not contain the source dataset SHA-256 or privacy-safe per-question export. A PASS means only that the committed aggregate artifacts are internally consistent. It is **not** a fresh experiment, data-integrity proof, or independent replication.

## Next full rerun

Follow [the reproducibility audit](../docs/reproducibility/REPRODUCIBILITY_AUDIT.md) and [data provenance note](../results/final_locked_test/data_provenance.md). Record the dataset revision and SHA-256 before preprocessing, capture the environment and Git commit, preserve split IDs, and export privacy-safe per-question results with checksums. Do not commit raw conversation text or answers.
