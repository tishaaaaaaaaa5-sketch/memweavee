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

Follow [the reproducibility audit](../docs/REPRODUCIBILITY_AUDIT.md) and [data provenance note](../results/final_locked_test/data_provenance.md). Record the dataset revision and SHA-256 before preprocessing, capture the environment and Git commit, preserve split IDs, and export privacy-safe per-question results with checksums. Do not commit raw conversation text or answers.


## Assemble partial MFAR traces from the Stage B/C retention export

Notebook 06 exports `stage_bc_candidate_trace.csv` with candidate-session hashes, query-content hashes, gold/irrelevant labels, word-count proxy costs, and per-variant retention decisions. It contains no raw question or session text.

After running the updated notebook export cell, assemble one partial trace per test question and variant:

```bash
python MemWeave/scripts/assemble_mfar_retention_traces.py \
  --candidates /path/to/stage_bc_candidate_trace.csv \
  --manifest /path/to/stage_bc_reconciliation_manifest.json \
  --output /path/to/mfar_retention_traces.jsonl
```

The adapter validates candidate-pool consistency across variants, checks manifest provenance, creates privacy-minimised session-level traces, and validates every output record against the MFAR 0.2.0 JSON Schema (requires `jsonschema`). Repeated appearances of the same source session are preserved as separate candidate occurrences (keyed by candidate index); they are not deduplicated. A repeated source ID must map to the same content hash. It records the budgeted retention selection as such; it does **not** fabricate retrieval evidence, generated answers, failure probabilities, or oracle labels. See [the adapter specification](../docs/MFAR_RETENTION_TRACE_ADAPTER.md).

This export is an offline benchmark reconstruction, not an instrumented online memory system. SHA-256 hashes are potentially linkable metadata, not anonymization.


## Run the adapter unit tests

From the repository root:

```bash
python -m unittest discover -s MemWeave/tests -p "test_*.py"
```

The schema-validation test uses `jsonschema` when installed and is skipped if the optional dependency is absent. The assembler CLI itself requires `jsonschema`.
