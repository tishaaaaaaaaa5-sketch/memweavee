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


## Assemble partial MFAR traces from the Stage B/C retention export

Notebook 06 exports `stage_bc_candidate_trace.csv` with candidate-session hashes, query-content hashes, gold/irrelevant labels, word-count proxy costs, and per-variant retention decisions. It contains no raw question or session text.

After running the updated notebook export cell, assemble one partial trace per test question and variant:

```bash
python MemWeave/scripts/assemble_mfar_retention_traces.py \
  --candidates /path/to/stage_bc_candidate_trace.csv \
  --manifest /path/to/stage_bc_reconciliation_manifest.json \
  --output /path/to/mfar_retention_traces.jsonl
```

The adapter validates candidate-pool consistency across variants, checks manifest provenance, creates privacy-minimised session-level traces, and validates every output record against the MFAR 0.2.0 JSON Schema (requires `jsonschema`). Repeated appearances of the same source session are preserved as separate candidate occurrences (keyed by candidate index); they are not deduplicated. A repeated source ID must map to the same content hash. It records the budgeted retention selection as such; it does **not** fabricate retrieval evidence, generated answers, failure probabilities, or oracle labels. See [the adapter specification](../docs/instrumentation/MFAR_RETENTION_TRACE_ADAPTER.md).

This export is an offline benchmark reconstruction, not an instrumented online memory system. SHA-256 hashes are potentially linkable metadata, not anonymization.


## Run the adapter unit tests

From the repository root:

```bash
python -m unittest discover -s MemWeave/tests -p "test_*.py"
```

The schema-validation test uses `jsonschema` when installed and is skipped if the optional dependency is absent. The assembler CLI itself requires `jsonschema`.


## Audit the assembled original retention traces

After assembling the original Stage B/C JSONL, run the real-data audit:

```bash
python MemWeave/scripts/audit_mfar_retention_traces.py \
  --input /path/to/mfar_retention_traces.jsonl \
  --per-trace-output /path/to/mfar_retention_audit_per_trace.csv \
  --summary-output /path/to/mfar_retention_audit_summary.json
```

This reports candidate/retained gold counts, retention recall and precision, and word-count-proxy budget utilization by question and variant. It also checks candidate-to-stored provenance and cross-variant candidate-pool consistency. It uses only the original trace JSONL and the Python standard library. It does not create synthetic data or infer construction, compression, retrieval, or answering labels. See [the audit note](../docs/instrumentation/MFAR_RETENTION_AUDIT.md).

## Validate cross-stage trace references

After assembling real traces, run the referential-integrity validator:

```bash
python MemWeave/scripts/validate_mfar_trace_integrity.py \
  --input /path/to/mfar_retention_traces.jsonl
```

This complements JSON Schema validation by checking that memory-to-source lineage, transformation inputs/outputs, and answer-to-retrieved-evidence references resolve within each trace. It also rejects answer/retrieval records that contradict the corresponding unobserved-stage flags. It does not infer missing events or failure labels.


## Capture real MemWeave runtime events (Notebook 01)

The event writer is integrated into `MemWeave/notebooks/01_MemWeave_2_1.ipynb`. Do not manually create events or copy placeholder IDs into a trace.

To enable it in Kaggle, run this setup cell before running the notebook from the first cell:

```python
import os
os.environ["MFAR_TRACE_ENABLED"] = "1"
```

Restart the kernel and run all cells in order. Keep `MEMWEAVE_SMOKE` unset. The notebook automatically rebuilds the feature cache during tracing so source and candidate construction events correspond to real execution. It writes a run-specific `mfar_runtime_events_<run_id>.jsonl` and a `mfar_runtime_trace_manifest_<run_id>.json` under the v2.1 results directory.

The event hooks cover source/candidate construction, candidate pools, test-fold retention selections, and (when `CFG["run_qa_proxy"]` is enabled) QA evidence assembly and answer generation. QA generation remains off by default. The retention selection is not a persistent storage write, and the metric-time BM25 ranking is not represented as a live retrieval service call.

The manifest reports observed event counts and question coverage; it does not infer failure labels. Compare traced and untraced outputs on the same approved original data before treating instrumentation as behavior-preserving. Never commit raw benchmark data, event ledgers, prompts, or generated answers. Hashes are linkable metadata, not anonymisation.


## Validate the instrumented Notebook 01 runtime event ledger

After a traced original-data Kaggle run, validate the run-specific JSONL event file:

```bash
python MemWeave/scripts/validate_mfar_runtime_events.py \
  --input /path/to/mfar_runtime_events_<run_id>.jsonl \
  --summary-output /path/to/mfar_runtime_event_validation.json
```

The standard-library validator checks event structure, unique event IDs, source-to-candidate lineage, candidate-pool consistency, retention references, QA-context evidence, answer-to-context linkage, timestamps, and absence of raw-text fields. A pass establishes internal event-ledger consistency only; it does not prove semantic correctness, observational equivalence, or MFAR effectiveness. It does not infer missing stages or failure labels.
