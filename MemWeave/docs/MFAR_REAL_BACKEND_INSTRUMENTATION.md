# MFAR instrumentation plan for the existing MemWeave notebooks

**Status:** repository-level experimental pipeline identified; runtime instrumentation not yet executed.
**Applies to:** the existing MemWeave v2.x notebook pipeline, MFAR trace schema v0.2.0, and real-data-only workflow.
**Rule:** instrument the actual notebook operations and preserve their outputs. Do not create a second/mock backend, synthetic events, or inferred failure labels.

## 1. Corrected repository inspection

The earlier statement that no memory implementation existed was too broad. The repository contains an experimental memory-selection and downstream QA pipeline, especially in:

- `notebooks/00_MemWeave_2_0.ipynb`
- `notebooks/01_MemWeave_2_1.ipynb`
- `notebooks/04_MemWeave_Final.ipynb`

Notebook 01 contains real implementations of:

- `session_turns()` and `encode_session()`: parse conversation sessions and construct session representations (`full`, user-only text, turn counts, token/word cost, entity features).
- `build_bundle()`: build per-question session pools, relevance references, TF-IDF similarity, static/query-conditioned features, and BM25 scores.
- `select()`: budget-constrained retention using utility, redundancy, and supersession penalties.
- `metrics()`: retention recall and BM25 ranking metrics over retained sessions.
- `qa_context()`: assemble selected session excerpts for downstream question answering.
- The optional `run_qa_proxy` block: load a Hugging Face causal LM, generate answers from selected excerpts, and compute a containment-style correctness proxy.

Notebook 04 separately contains the Stage C candidate-pool and budgeted-selection analysis, including `select_idx()`, `recall_of()`, `selections()`, and a downstream evidence/answer-in-context proxy.

**Important boundary:** these are benchmark-driven experimental notebook pipelines, not evidence of a continuously running personal-memory service with an independently persisted store. The current code does not expose a separate general-purpose compression service or persistent memory index. In Notebook 01, selection is the retention/budget operation; the BM25 ordering in `metrics()` and the QA context construction are downstream experimental retrieval paths. The QA block is optional and its existing CSV records correctness indicators, not a complete privacy-safe evidence-to-answer event trace.

## 2. Existing operation-to-MFAR mapping

| Existing code | What it genuinely observes | MFAR mapping | Remaining limitation |
|---|---|---|---|
| `session_turns()` / `encode_session()` | Original benchmark session and its encoded representation | source evidence / candidate construction | No independent source archive ingestion event; source-to-candidate provenance needs explicit IDs and hashes |
| `build_bundle()` | Per-question candidate pool, session IDs, content-derived features, gold reference membership | candidate memory formation | Gold/reference membership is evaluation-only and must not enter online diagnostic features |
| `select()` / `eval_method()` | Chosen candidate indices and used budget | retention / compression proxy | This is budgeted selection, not a separately measured lossy compressor or persistent write |
| `metrics()` | BM25 order among selected candidates and recall at configured cut-offs | retrieval metric proxy | It computes evaluation metrics; it is not itself a captured external retrieval API result |
| `qa_context()` | Exact selected session excerpts assembled for a QA prompt | evidence supplied to answering model | Must record the selected session IDs and prompt-evidence mapping, not the raw prompt text |
| optional QA generation loop | Model/config, input context, generated answer in local variable, correctness proxy | answering | Existing export does not preserve answer IDs/hashes and per-answer evidence lineage |

## 3. Instrumentation objective

Add an opt-in, privacy-minimised event ledger to the existing notebook execution. It should record only real events produced while processing the original approved benchmark inputs:

1. **Construction:** source/session ID, source content hash, candidate occurrence ID, candidate representation hash, run/question identifiers.
2. **Retention:** candidate IDs, selected candidate IDs, actual budget/cost value and unit, selection policy/config fingerprint.
3. **Retrieval:** the exact ordered selected-session IDs used to assemble each QA context, rank, retrieval method, and configured top-k.
4. **Answering:** the exact evidence/session IDs included in each prompt, model and generation configuration, generated answer hash, and answer-evaluation result. Do not export prompt, query, source text, or answer text.

The ledger must distinguish a real event from a derived evaluation metric. In particular, a sorted list computed inside `metrics()` must be tagged as a metric-time ranking, not represented as an independently observed backend retrieval call.

## 4. Required identifiers and hashing

- Use stable source session IDs already supplied by the benchmark.
- Derive occurrence IDs from the question ID plus candidate index so repeated appearances of one source session remain distinct occurrences.
- Hash exact UTF-8 source/session text and exact encoded representation separately with SHA-256.
- Use a run ID tied to the notebook execution and record the Git commit, dataset revision/checksum, split, configuration, and tokenizer/cost unit.
- Do not use gold labels, answer references, or benchmark relevance grades to construct runtime IDs, ranking features, or event presence.
- Hashes are linkable metadata, not anonymisation. Keep access to any raw data and mappings controlled.

## 5. Instrumentation safeguards

1. Instrument existing code boundaries; do not change selection scores, candidate order, model inputs, prompts, generation settings, or output metrics.
2. Keep instrumentation opt-in and write a separate JSONL event file; do not overwrite benchmark result files.
3. Record actual measured token counts only when the tokenizer is known. Label whitespace word counts as word-count proxies.
4. Store no raw conversation, query, prompt, retrieved excerpt, or answer text in Git or the event ledger.
5. Keep reference answers and gold evidence strictly evaluation-only.
6. Missing events remain unobserved; never infer a failure from an absent trace.
7. Compare instrumented and uninstrumented outputs on the same approved real inputs. This checks observational equivalence; it is not a synthetic benchmark.
8. Validate event IDs and lineage before mapping events into schema v0.2.0.

## 6. Execution sequence

1. Use the exact code-cell mapping in [MFAR_NOTEBOOK_INSTRUMENTATION_MAP.md](MFAR_NOTEBOOK_INSTRUMENTATION_MAP.md).
2. Add the opt-in recorder and call it from the existing functions/loops; keep it disabled by default.
3. Run the original approved notebook on the original real dataset with tracing enabled.
4. Produce a privacy-safe event coverage report: source/candidate/retained/retrieved/answered counts, plus explicit unobserved stages.
5. Check referential integrity and output equivalence.
6. Only then assemble runtime traces and adjudicate failure labels on a supported subset.
7. Do not train a detector or claim MFAR effectiveness until the real trace coverage and annotation protocol support it.

## 7. Current decision

**The notebook implementation gate is partially passed:** actual construction, budgeted retention, retrieval-like ranking/context assembly, and optional QA generation code have been identified. **The runtime observability gate is not yet passed:** the current exports do not capture a complete event lineage across those operations, and there is no demonstrated persistent-memory write/read service.

Permitted next work: instrument the existing notebook functions, preserve real outputs, validate event lineage, and report coverage. Blocked: treating selection metrics as actual storage/compression performance, treating metric-time BM25 ranking as an independently observed retrieval call, inferring missing-stage labels, detector training, and end-to-end MFAR effectiveness claims.
