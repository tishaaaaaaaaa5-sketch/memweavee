# MFAR instrumentation of the existing MemWeave notebooks

**Status:** opt-in instrumentation is committed in Notebook 01; a real traced Kaggle execution and observational-equivalence check are still pending.
**Applies to:** the MemWeave v2.1 LongMemEval-S notebook, MFAR trace schema v0.2.0, and real-data-only workflow.
**Rule:** instrument existing operations only. Do not create a replacement/mock backend, synthetic events, or inferred failure labels.

## 1. Corrected implementation assessment

The repository contains an experimental benchmark pipeline, especially in:

- `notebooks/00_MemWeave_2_0.ipynb`
- `notebooks/01_MemWeave_2_1.ipynb`
- `notebooks/04_MemWeave_Final.ipynb`

Notebook 01 implements session encoding, question-specific candidate-pool construction, budget-constrained retention, BM25 ranking over retained sessions, QA-context assembly, and optional Hugging Face answer generation. Notebook 04 contains the separate Stage C candidate-pool and controlled-selection experiment.

These are real experimental operations, not merely a proposal. They are not equivalent to a continuously running personal-memory service with a persistent memory index. In particular, selection is the current retention operation; it is not proof of a separately measured lossy compressor or durable storage write.

## 2. Committed instrumentation

The opt-in event writer is `scripts/mfar_runtime_event_writer.py`. Its hooks are integrated into `notebooks/01_MemWeave_2_1.ipynb`:

| Existing operation | Recorded event | Semantics |
|---|---|---|
| `encode_session()` and source session handling in `build_bundle()` | `source_observed`, `candidate_constructed` | Real source session and encoded candidate, linked by opaque IDs and SHA-256 hashes |
| Candidate bundle creation in `build_bundle()` | `candidate_pool_built` | Ordered candidate occurrence IDs for the question |
| Test-fold method/budget evaluation in `record()` | `retention_selected` | Actual candidate pool, selected IDs, selection method, fold, seed, budget and cost unit |
| `qa_context()` | `qa_evidence_assembled` | Retained IDs and exact top-k session IDs assembled into the QA context |
| Optional generation loop | `answer_generated` | Evidence IDs passed to the model, model/config fingerprints, answer hash, measured generation latency/token counts, and the existing containment evaluation |

The notebook's BM25 ranking used for retention metrics is not exported as a separate live retrieval event. The QA context assembly is the observable retrieval-to-answer boundary. The optional QA generation block remains disabled by default; when disabled, answering is unobserved in that run.

A traced run sets `MFAR_TRACE_ENABLED=1` before executing the notebook, rebuilds the feature cache so construction events are observed, and writes a run-specific JSONL event file plus a coverage/checksum manifest under `v2_1/`. The LoCoMo external-validation pass is deliberately excluded from this LongMemEval-S event ledger.

## 3. Privacy and behavior safeguards

1. Instrumentation is disabled by default and writes separate event artifacts.
2. It records opaque IDs and SHA-256 hashes, never raw conversation, query, prompt, retrieved text, or generated answer text.
3. Session identifiers are hashed before export; hashes remain potentially linkable metadata, not anonymisation.
4. The original selection scores, ranking, budgets, prompt, model settings, and answer-evaluation logic are unchanged by the hooks.
5. Actual measured model token counts are recorded only in the QA generation path; retention costs carry the notebook's tokenizer/cost-unit label.
6. Gold evidence and reference answers remain evaluation-only. The answer containment flag is an evaluation metric, not a human support adjudication.
7. A missing event remains unobserved. It is not converted to a negative label.

## 4. Execution and validation sequence

1. Pull the research branch and confirm the updated Notebook 01 and event-writer module are present.
2. Set `os.environ["MFAR_TRACE_ENABLED"] = "1"` before running the notebook from the first cell; restart the kernel and run all cells in order.
3. Keep `MEMWEAVE_SMOKE` unset and use the approved original LongMemEval-S data. Tracing automatically rebuilds the real feature cache.
4. Inspect the generated run-specific JSONL file and its `mfar_runtime_trace_manifest_<run_id>.json` coverage/checksum report.
5. Compare traced and untraced outputs on the same original inputs: candidate ordering, selected IDs, budget usage, result CSVs, and (if enabled) QA answers/evaluation values. Any difference beyond trace files/timing overhead must be investigated.
6. Validate event ID lineage and privacy before converting supported events into MFAR schema v0.2.0 traces or creating annotations.

## 5. Current decision

**Code instrumentation is committed; runtime evidence is pending.** The hooks cover actual construction, retention, and QA-context/answer operations where those optional paths execute. They do not create a persistent memory store or an independently instrumented retrieval service. If the QA proxy is disabled, retrieval-to-answer and answering events are absent by design.

Permitted next work: execute the traced original-data notebook, inspect coverage, check output equivalence, and validate event lineage. Blocked: treating retention as persistent storage/compression, calling metric-time ranking a live retrieval API, inferring missing-stage labels, detector training, and end-to-end MFAR effectiveness claims.
