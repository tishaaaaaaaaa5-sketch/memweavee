# MFAR offline adapter: Stage B/C retention traces

**Adapter version:** 0.1.0  
**Input:** the candidate-level export from notebook 06  
**Output:** partial MFAR trace records using schema 0.2.0  
**Status:** implementation committed; export-cell rerun and end-to-end execution still required.

## Why this adapter is deliberately partial

The Stage B/C LongMemEval experiment ranks candidate sessions and selects a subset under a 10% word-count proxy budget. It does not execute a separate retrieval operation over a previously stored memory, does not record a pre-compression representation, and does not generate or adjudicate an answer.

The adapter therefore records a **session-retention observation**, not a complete MFAR lifecycle execution. It must not be used as evidence that the four MFAR failure modes have been diagnosed.

## Input export

The updated final export cell in `06_Stage_BC_Controlled_Reconciliation.ipynb` writes:

- `stage_bc_candidate_trace.csv`
- the existing `stage_bc_reconciliation_manifest.json`

The candidate CSV contains one row per test question × variant × ranked candidate occurrence. A source session can appear more than once in a candidate list; these repeated occurrences are preserved by their distinct candidate indices rather than deduplicated. It includes:
- a truncated hash of the benchmark question identifier;
- a full SHA-256 hash of the question content;
- variant name and candidate index;
- a dataset-revision-scoped opaque source-session ID;
- a SHA-256 hash of canonicalized session JSON;
- query-specific relevance grade (`gold` or `irrelevant`);
- the existing word-count proxy cost;
- whether that candidate was selected by the budgeted retention policy.

It does not export question text, answer text, session text, or message text. Hashes and opaque IDs can still be linkable metadata and require appropriate access controls.

The original seven-output reconciliation run predates this candidate-level export. Rerun the updated final export cell in the same completed notebook kernel to generate the eighth CSV. The new export cell consumes the already computed `baseline_metrics`, `RUNS`, `Q`, `raw`, and `ROW_MAPS`; if the kernel has been reset, rerun the notebook from the top after reviewing and explicitly confirming the dataset terms.

## Trace mapping

For each question and variant, the adapter writes one trace:

| MFAR field | Adapter mapping | Interpretation |
|---|---|---|
| `dataset` | LongMemEval-S revision and SHA-256 from manifest | Pinned benchmark provenance |
| `query` | Question-content SHA-256 and opaque question ID hash | No query text is stored |
| `source_evidence` | All candidate sessions, with query-specific gold/irrelevant labels | Session-level benchmark evidence, not claim-level spans |
| `candidate_memory` | Candidate sessions represented as candidate memory units | A benchmark adapter representation, not output of a separately instrumented constructor |
| `stored_memory` | Candidate sessions selected by the budgeted retention policy | Retained-session subset, not compressed summaries |
| `transformations` | Candidate-to-retained selection | Marked as `other` with operation metadata; not labelled compression |
| `retrieved_evidence` | Empty | No separate retrieval stage was recorded |
| `diagnosis.probabilities` | Null | No failure estimator has been trained or applied |
| `oracle_labels` | All unknown/null | No lifecycle-level failure annotation is supported by this experiment |
| `outcome` | `not_evaluated`, null answer ID/hash | No answer-generation evaluation exists in this export |
| `cost` | Null token/latency fields | The experiment's word-count proxy is not exact token accounting |

Observability flags are set accordingly: source archive available; pre-compression trace unavailable; session-to-retention mapping available from the benchmark reconstruction; separate retrieval trace unavailable; answer trace unavailable. The memory provenance flag refers only to the reconstructed candidate-session-to-retained-session mapping, not provenance instrumentation in a production memory system.

Schema 0.2.0 permits null diagnosis probabilities, null answer identifiers/hashes, `not_evaluated` outcomes, and unknown memory creation timestamps. Null means unobserved or unestimated; it must never be interpreted as a zero probability or a negative failure label.

## Run

Install the schema validator dependency:

```bash
python -m pip install jsonschema
```

Then run from the repository root:

```bash
python MemWeave/scripts/assemble_mfar_retention_traces.py \
  --candidates /path/to/stage_bc_candidate_trace.csv \
  --manifest /path/to/stage_bc_reconciliation_manifest.json \
  --output /path/to/mfar_retention_traces.jsonl
```

The script checks required columns, rejects unexpected columns (including accidental raw-text fields), validates hashes and IDs, checks that candidate pools match across variants, checks the dataset revision/checksum in the manifest, and validates every assembled record against the Draft 2020-12 schema. Repeated source IDs are allowed only when they map to the same content hash; each candidate occurrence receives a distinct trace-local evidence/memory ID based on its candidate index. This preserves the ranked candidate list without collapsing repeated rows.

Expected record count for the standard notebook run is 235 test questions × 9 policies (baseline plus eight factorial variants) = 2,115 traces. The script reports the actual count; do not assume this count if the input differs.

## What this does not establish

- It does not identify construction or compression failures.
- It does not measure retrieval failures because the benchmark selection is not a separate retrieval operation.
- It does not measure answering failures or end-to-end answer accuracy.
- It does not train or validate a failure estimator.
- It does not establish that a persistent-memory system used the selected sessions.
- It does not replace the word-count proxy with exact tokenizer-based storage accounting.

The next milestone is to execute the updated export and assembler, inspect the resulting trace coverage and referential integrity, and conduct a privacy review. A genuine MFAR lifecycle study will additionally need an instrumented system that logs source ingestion, pre-compression candidates, stored memory, retrieval results, and answer/evidence support.
