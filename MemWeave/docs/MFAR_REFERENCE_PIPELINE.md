# MFAR synthetic reference pipeline

**Status:** instrumentation fixture; not a production memory backend and not an evaluated MFAR controller.

## Purpose

`scripts/mfar_reference_pipeline.py` emits schema-v0.2.0 traces for five controlled synthetic scenarios: a clean path and one injected failure at each of construction, compression, retrieval, and answering. It exists to test the trace contract before integrating a real memory system.

## Run in Kaggle or locally

From the repository root:

```bash
python MemWeave/scripts/mfar_reference_pipeline.py --scenario clean --output /kaggle/working/mfar_clean.json
python MemWeave/scripts/mfar_reference_pipeline.py --scenario construction_loss --output /kaggle/working/mfar_construction_loss.json
python MemWeave/scripts/mfar_reference_pipeline.py --scenario compression_loss --output /kaggle/working/mfar_compression_loss.json
python MemWeave/scripts/mfar_reference_pipeline.py --scenario retrieval_loss --output /kaggle/working/mfar_retrieval_loss.json
python MemWeave/scripts/mfar_reference_pipeline.py --scenario answering_failure --output /kaggle/working/mfar_answering_failure.json
```

Validate an individual trace with the existing CLI:

```bash
python MemWeave/scripts/validate_mfar_trace.py /kaggle/working/mfar_clean.json
```

Run automated tests:

```bash
python -m unittest discover -s MemWeave/tests -p "test_*.py" -v
```

## Interpretation

| Scenario | Expected observable signature |
|---|---|
| clean | source → candidate → stored → retrieved → supported answer |
| construction_loss | source evidence exists; candidate memory is empty |
| compression_loss | candidate memory exists; stored memory is empty |
| retrieval_loss | stored memory exists; retrieved evidence is empty |
| answering_failure | evidence is retrieved; answer claim is marked unsupported |

The fixture stores hashes rather than synthetic text. It records stage artifacts and provenance; it does **not** automatically assign oracle failure labels or model probabilities. `oracle_labels` and diagnosis probabilities remain null. Scenario names are test controls, not annotations.

## Limitations and next integration step

- The fixture has one synthetic fact and deterministic rules; it says nothing about real-world diagnostic accuracy.
- The answer-support status is a controlled fixture outcome, not a human adjudication.
- It does not implement a learned detector, intervention policy, persistent store, or real compressor/retriever/LLM.
- The next integration must wrap an actual memory backend and log pre/post transformation evidence, retrieval results, answer hashes, claim-level support, and measured token/latency costs.
- Human oracle annotation must remain separate from online features and must be performed under the frozen annotation protocol.
