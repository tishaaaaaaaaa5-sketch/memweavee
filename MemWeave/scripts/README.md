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


## Audit the assembled original retention traces

After assembling the original Stage B/C JSONL, run the real-data audit:

```bash
python MemWeave/scripts/audit_mfar_retention_traces.py \
  --input /path/to/mfar_retention_traces.jsonl \
  --per-trace-output /path/to/mfar_retention_audit_per_trace.csv \
  --summary-output /path/to/mfar_retention_audit_summary.json
```

This reports candidate/retained gold counts, retention recall and precision, and word-count-proxy budget utilization by question and variant. It also checks candidate-to-stored provenance and cross-variant candidate-pool consistency. It uses only the original trace JSONL and the Python standard library. It does not create synthetic data or infer construction, compression, retrieval, or answering labels. See [the audit note](../docs/MFAR_RETENTION_AUDIT.md).

## Validate cross-stage trace references

After assembling real traces, run the referential-integrity validator:

```bash
python MemWeave/scripts/validate_mfar_trace_integrity.py \
  --input /path/to/mfar_retention_traces.jsonl
```

This complements JSON Schema validation by checking that memory-to-source lineage, transformation inputs/outputs, and answer-to-retrieved-evidence references resolve within each trace. It also rejects answer/retrieval records that contradict the corresponding unobserved-stage flags. It does not infer missing events or failure labels.


## Record real MemWeave runtime events (Notebook 01 instrumentation)

`mfar_runtime_event_writer.py` provides an append-only, privacy-minimised JSONL writer for actual notebook events. It does not create events automatically: call `emit()` only at an operation that really executed. It accepts hashes and opaque IDs, not raw text. Metadata is allow-listed to reduce accidental text leakage.

A minimal setup cell in the existing Notebook 01 run:

```python
from MemWeave.scripts.mfar_runtime_event_writer import (
    MFARRuntimeEventWriter,
    sha256_text,
)

trace_writer = MFARRuntimeEventWriter(
    "/kaggle/working/mfar_runtime_events.jsonl",
    run_id=RUN_ID,  # set once for this real execution
    repository_commit=GIT_COMMIT,
    dataset_revision=DATASET_REVISION,
    dataset_sha256=DATASET_SHA256,
    split="test",
)
```

At the existing code boundaries, emit records using the actual session/question IDs and selected indices. For example, after `encode_session(session)` has returned a real representation:

```python
trace_writer.emit(
    "candidate_constructed",
    question_id=question_id,
    source_session_id=source_session_id,
    candidate_occurrence_id=f"{question_id}:{candidate_index}",
    content_sha256=sha256_text(encoded["full"]),
    metadata={"cost_unit": TOKENIZER},
)
```

This is a usage pattern, not a ready-to-run notebook cell: names such as `RUN_ID`, `GIT_COMMIT`, `DATASET_REVISION`, `question_id`, and `source_session_id` must be bound to the actual run variables in the notebook. Do not invent them or emit a record when the operation did not occur. The instrumentation map specifies each event boundary and semantic constraint.

The writer is an intermediate ledger, not yet an MFAR schema v0.2.0 trace assembler. Do not report runtime coverage or failure labels until the existing notebook has been instrumented, run on the approved original data, and its event lineage has been validated. Never commit raw benchmark content or generated answers.
