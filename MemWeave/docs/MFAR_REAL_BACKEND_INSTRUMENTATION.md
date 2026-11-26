# MFAR real-backend instrumentation plan

**Status:** integration plan only; no memory backend has yet been identified in the MemWeave repository.
**Applies to:** the existing MFAR trace schema v0.2.0 and the real-data-only research workflow.
**Rule:** instrument the user's actual memory implementation. Do not substitute a mock backend, synthetic events, or fabricated labels.

## 1. Repository inspection result

The canonical MemWeave notebooks inspected for this milestone (00, 04, 05, and 06), along with the current repository guide and MFAR scripts, document benchmark feature extraction/ranking, budgeted retention, offline trace assembly, and retention auditing. Notebook 06's apparent memory-related match is its privacy-minimised result-export cell, not a persistent-memory backend. No inspected file exposes an implemented memory service with independently observable construction, compression, retrieval, and answer-generation operations.

The MFAR algorithm design and schema are specifications, not a running implementation. The Stage B/C adapter is a benchmark reconstruction of candidate-session retention. It must not be described as a live memory backend.

Therefore this repository is not yet ready to train a failure estimator or evaluate targeted MFAR interventions. The next dependency is the actual backend source and a real execution path that can be instrumented.

## 2. Minimum event capture contract

Instrument the real pipeline at its existing function boundaries. Preserve the implementation's behavior; instrumentation must be observational and must not alter ranking, storage, retrieval, prompting, or answers.

| Event boundary | Capture from the real operation | Required trace representation |
|---|---|---|
| Source ingestion / construction | Source record IDs and spans; extracted candidate IDs; source-to-candidate lineage; construction implementation version and timestamp | pipeline.source_evidence, pipeline.candidate_memory, construction transformation(s), source/pre-compression observability |
| Compression / persistence | Exact candidate inputs; persisted memory IDs and content hashes; source lineage; transformation kind/version; creation/update timestamps; actual stored-token measurement if available | pipeline.candidate_memory, pipeline.stored_memory, compression/merge/summarize transformations, memory provenance observability |
| Query retrieval | Query ID/hash; memory index/version; actual returned memory IDs and rank/score metadata where safe; retrieval filters and top-k; retrieval latency and token cost | pipeline.retrieved_evidence, retrieval observability, retrieval cost fields |
| Answer generation / verification | IDs of evidence actually passed to the generator; answer ID/hash; claim-to-evidence support decisions if the system performs them; model/config version; latency and token usage | outcome.evidence_ids, outcome.status, optional claim_support, answer observability and cost fields |

The schema's IDs must resolve across stages. If a real backend cannot provide a field, preserve it as unavailable/null where the schema allows and document the reason. Do not synthesize a timestamp, token count, evidence link, or confidence value.

## 3. Failure-mode evidence requirements

- **Construction:** requires evidence that was present in the approved source archive and an observable candidate-construction result. A source-to-candidate omission can then be adjudicated.
- **Compression:** requires both the pre-compression candidate and the actual stored representation, linked by transformation lineage. A difference in text alone is not automatically a failure; relevance and meaning must be assessed.
- **Retrieval:** requires a known relevant item in stored memory and the actual result set returned for the query.
- **Answering:** requires the evidence actually supplied to the answer generator and the generated answer or a privacy-safe adjudication record.

A missing event is NOT_OBSERVABLE, not a negative label. A gold item omitted at the Stage B/C selection boundary remains a retention omission only.

## 4. Instrumentation safeguards

1. Add logging at existing operation boundaries; do not change control flow or model inputs.
2. Use stable opaque IDs and SHA-256 content hashes for linkage. Hashes are potentially linkable metadata, not anonymization.
3. Keep raw conversation, query, retrieved text, and answer text out of Git and ordinary trace exports. Retain any text-to-ID mapping only in the approved access-controlled data store.
4. Record actual token counts, tokenizer identity, latency, model calls, and model/config versions when measured. Use null when not measured.
5. Keep online diagnostic features separate from evaluation-only oracle labels and reference answers.
6. Version the instrumentation and trace schema. Record repository commit, dataset revision/checksum, split, and run ID.
7. Run referential-integrity checks before annotation: every memory's source evidence and every retrieved item must resolve to the same run's upstream records.
8. Verify that enabling instrumentation does not change the backend's outputs on the same real inputs. This is an observational-equivalence check, not a synthetic test.

## 5. Integration sequence once the backend is supplied

1. Identify the actual entry points for ingestion, candidate construction, compression/persistence, retrieval, and answer generation.
2. Map existing native IDs and logs to schema v0.2.0. Extend the schema only if a real field cannot be represented without losing meaning.
3. Add a thin, optional trace writer around those entry points. It must be disabled by default and must not affect the memory policy.
4. Run the original benchmark or the user's approved real workload with instrumentation enabled.
5. Validate schema, ID resolution, source lineage, stage coverage, privacy, and observational equivalence.
6. Report stage observability coverage before creating any annotations.
7. Only then define a real-data annotation subset and train/evaluate simple diagnostic baselines using train/dev splits. Keep the held-out test set untouched until the protocol is locked.

## 6. Inputs needed to proceed with code integration

The integration requires the actual source code or notebook that performs memory construction and retrieval, plus its real execution entry point. The most useful handoff is:

- the backend source files or executed notebook;
- the command/cell used to run it;
- the real configuration identifying storage, compression, retrieval, and answer components;
- any existing logs or trace files from an approved run (with raw text removed if necessary).

Do not upload API keys, credentials, private user conversations, or restricted benchmark content. If the backend is in a separate repository, provide its repository URL or the relevant source files.

## 7. Current decision

**Gate not passed:** no real backend source or lifecycle event stream is currently available in this repository inspection.

Permitted work before that dependency is resolved: schema review, adapter correctness, documentation, and privacy-safe processing of original benchmark exports.

Blocked until real instrumentation exists: failure labels, detector training, probability calibration, diagnosis-driven interventions, and claims about MFAR end-to-end effectiveness.
