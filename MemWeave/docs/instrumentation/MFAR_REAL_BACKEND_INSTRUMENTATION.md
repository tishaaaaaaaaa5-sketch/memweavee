# MFAR runtime instrumentation status

**Status: standalone writer and validator only. Notebook instrumentation is not integrated or end-to-end validated.**

The repository contains scripts/mfar_runtime_event_writer.py and
scripts/validate_mfar_runtime_events.py as opt-in building blocks. A search of
Notebook 01 (notebooks/01_MemWeave_2_1.ipynb) at the integration commit
confirmed that it does not import or call the writer, set MFAR_TRACE_ENABLED,
or emit the runtime event types. Earlier wording in this document that said
hooks were integrated into Notebook 01 was inaccurate and is superseded here.

## What exists

- An append-only JSONL writer for explicitly emitted events.
- A separate validator for opaque identifiers, bounded metadata, run metadata,
  event lineage, and event coverage.
- Unit tests for the writer and validator, including invalid identifiers,
  free-form metadata, mixed runs, and broken lineage.
- An offline Stage B/C retention-trace adapter. This adapts exported retention
  observations; it is not a runtime execution trace.

## Privacy contract

- Question, source-session, candidate, and lineage IDs must be prefixed,
  lowercase hexadecimal opaque tokens.
- Event/run IDs have dedicated opaque formats.
- Metadata is restricted to enumerated values, hashes, finite numeric values,
  non-negative integer counters, and booleans. Arbitrary strings and nested
  collections are rejected.
- Dataset revisions are bounded revision tokens; split names are enumerated.
- Raw queries, prompts, conversations, retrieved text, and answers must never
  be written. SHA-256 hashes remain potentially linkable metadata and are not
  anonymisation.

The writer enforces this contract before writing. The validator independently
re-enforces it when reading a ledger; it must not trust the writer as the only
privacy boundary.

## Tests

From the MemWeave directory:

    python -m pytest tests/test_mfar_runtime_events.py tests/test_assemble_mfar_retention_traces.py -q

A passing unit-test suite establishes only that the standalone writer and
validator behave according to their tested contract. It does not demonstrate
that notebook execution emits events.

## What remains before claiming runtime instrumentation

1. Integrate explicit writer calls into the real notebook operations (source
   observation, candidate construction/pool, retention selection, QA evidence,
   and answer generation only when that optional path runs).
2. Use the approved original data and execute the notebook from the first cell.
3. Validate a real run-specific event ledger and report event coverage.
4. Compare traced and untraced outputs to confirm instrumentation does not
   change candidate order, selections, budgets, metrics, or answers.
5. Keep unavailable stages explicitly unobserved; do not infer failure labels.

Until those steps are completed, the runtime writer is a standalone component
and no end-to-end MFAR runtime instrumentation claim is made.
