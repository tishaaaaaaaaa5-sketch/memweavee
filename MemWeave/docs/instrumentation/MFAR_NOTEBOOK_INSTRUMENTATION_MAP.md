# MFAR instrumentation map: MemWeave v2.1 notebook

**Target notebook:** `notebooks/01_MemWeave_2_1.ipynb`
**Purpose:** specify where to instrument the existing real-data pipeline without changing its algorithm.
**Status:** opt-in event-writer hooks are committed in Notebook 01; execution on original Kaggle data is pending.

## 1. Exact operation boundaries

| Notebook location | Existing symbol / block | Event to emit after the operation | Required privacy-safe fields |
|---|---|---|---|
| Code cell defining session parsing | `session_turns()`, `encode_session()` | `source_observed`, then `candidate_constructed` | run_id, question_id, source_session_id, candidate_occurrence_id, source_sha256, representation_sha256, turn_count, measured cost and cost_unit |
| Code cell defining question bundle | `build_bundle(rec, idx)` | `candidate_pool_built` | question_id, ordered candidate_occurrence_ids, candidate count, query hash, source hashes; keep gold/reference flags out of runtime event fields |
| Code cell defining selection | `select(b, util, p)` and `eval_method(...)` | `retention_selected` | question_id, method/config fingerprint, ordered candidate IDs, selected IDs, actual used cost, budget and cost unit |
| Code cell defining retention metrics | `metrics(b, chosen, used)` | `ranking_metric_computed` only if needed | selected IDs and BM25 ordering; mark explicitly as an evaluation-derived ranking, not a backend retrieval event |
| QA context function | `qa_context(b, chosen, k, words)` | `qa_evidence_assembled` | question_id, method, ordered session/candidate IDs actually included, top-k and excerpt word cap; never store excerpt text |
| Optional QA generation block | `lm.generate(...)`, answer decode, `rows.append(...)` | `answer_generated` | evidence IDs passed to prompt, model/tokenizer IDs, generation settings, answer hash, measured latency/token counts if available, and evaluation result in a separate evaluation-only field |

## 2. Important semantics

- `encode_session()` is a representation/feature encoder over benchmark sessions. It is not by itself a general-purpose memory-construction service.
- `select()` is budget-constrained retention. It is the current notebook's compression/retention proxy, not proof of a persistent storage write or a lossy summarizer.
- The BM25 sort in `metrics()` is used to calculate retrieval-at-k metrics. It must not be logged as an independent retrieval call.
- `qa_context()` is the strongest current retrieval-to-answer boundary: its returned context is what the QA prompt receives. Record IDs of the excerpts actually included.
- The optional QA block only runs when `CFG["run_qa_proxy"]` is true. If it is false, answer generation is unobserved for that run.
- The current QA export contains a correctness/containment proxy. A correct flag is not a human support judgment and should not be used as a failure label without a documented adjudication protocol.

## 3. Event ledger contract

The committed runtime recorder writes run-specific JSONL events, one event per actual operation. Minimum envelope:

```json
{
  "event_schema_version": "0.1.0",
  "run_id": "run_<opaque-id>",
  "event_id": "evt_<unique-id>",
  "event_type": "candidate_constructed",
  "question_id": "<opaque-question-id>",
  "occurred_at": "<actual UTC timestamp>",
  "source_session_id": "<existing source id or null>",
  "candidate_occurrence_id": "<run/question/index scoped id or null>",
  "input_ids": [],
  "output_ids": [],
  "content_sha256": null,
  "metadata": {}
}
```

The values above are field definitions only, not example experimental observations. Do not write placeholder events. Emit a record only when the corresponding real code operation executes. If an ID or measurement is unavailable, use null and preserve the reason in the run manifest.

Recommended event types:

- `source_observed`
- `candidate_constructed`
- `candidate_pool_built`
- `retention_selected`
- `ranking_metric_computed` (reserved; not emitted as a live retrieval event by the current Notebook 01 hooks)
- `qa_evidence_assembled`
- `answer_generated`

The ledger is an intermediate runtime artifact. Convert it to MFAR schema v0.2.0 only after validating all event references and distinguishing evaluation-only fields from online observable fields.

## 4. Observational-equivalence check

For the same original dataset, notebook commit, seed, configuration, and model revision:

1. Run the existing notebook with tracing disabled and preserve its normal outputs.
2. Run it with tracing enabled.
3. Compare candidate IDs/order, selected IDs/order, budget usage, retrieval-context IDs/order, generated answers (or answer hashes), and evaluation outputs.
4. Investigate any difference. Instrumentation is accepted only if the algorithmic outputs are unchanged, apart from trace files and trace-related timing overhead.

Do not use generated or synthetic conversations for this check. Use the approved original data only.

## 5. Stage coverage report

After a real traced run, the final notebook cell writes a coverage/checksum manifest. Report counts from those actual event records:

- distinct source sessions observed;
- candidate occurrences constructed;
- question pools built;
- retention decisions recorded;
- QA evidence assemblies recorded;
- answer generations recorded;
- questions with each stage observable;
- missing-stage reasons.

Do not convert coverage gaps into failure labels. Keep the Stage B/C 2,115-trace retention audit separate from any newly instrumented Notebook 01 run; they are different experiment artifacts and must not be pooled.

## 6. Current execution status

The event writer is wired into Notebook 01 behind `MFAR_TRACE_ENABLED=1`. The notebook automatically rebuilds its feature cache for a traced run, uses hashed source/question identifiers, and writes a run-specific event file. The QA evidence and answer hooks execute only when the optional QA proxy is enabled. No Kaggle runtime output has yet been supplied for this instrumented version, so coverage and observational equivalence remain unverified.

The current retention hook deliberately records only the primary query-agnostic Setting B policy at the notebook's fixed primary budget, on the first configured seed. This keeps the trace aligned with the retained sessions used by the optional QA proxy and avoids exporting every ablation/fold/budget combination. Other methods remain in the notebook's normal evaluation tables, not in this MFAR runtime event ledger.
