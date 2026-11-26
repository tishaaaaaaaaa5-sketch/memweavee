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

## MFAR trace and runtime instrumentation utilities

The research follow-up adds `assemble_mfar_retention_traces.py`, `audit_mfar_retention_traces.py`, `mfar_runtime_event_writer.py`, and trace/runtime validators. The Stage B/C adapter covers offline retention traces only. The runtime writer and validator are standalone components; Notebook 01 does not currently import or call them. Unit tests cover the standalone privacy and lineage contract, but there is no end-to-end runtime ledger until explicit notebook hooks are integrated and a real run is executed. See [runtime instrumentation status](../docs/instrumentation/MFAR_REAL_BACKEND_INSTRUMENTATION.md).

## Next full rerun

Follow [the reproducibility audit](../docs/reproducibility/REPRODUCIBILITY_AUDIT.md) and [data provenance note](../results/final_locked_test/data_provenance.md). Record the dataset revision and SHA-256 before preprocessing, capture the environment and Git commit, preserve split IDs, and export privacy-safe per-question results with checksums. Do not commit raw conversation text or answers.


Run the focused runtime privacy tests from this directory with `python -m pytest tests/test_mfar_runtime_events.py -q`. A passing result is unit-level validation only, not proof of notebook instrumentation.
