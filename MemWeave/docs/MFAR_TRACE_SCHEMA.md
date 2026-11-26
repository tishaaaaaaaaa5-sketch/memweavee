# MFAR trace schema: implementation notes

**Schema version:** 0.1.0  
**Status:** Initial instrumentation contract; not yet integrated into a running memory pipeline.

## Files

- `schemas/mfar_trace.schema.json`: JSON Schema Draft 2020-12 contract.
- `schemas/examples/mfar_trace.example.json`: synthetic example with hashes and placeholder identifiers only.
- `scripts/validate_mfar_trace.py`: command-line schema validator.

## Design choices

### One record per query execution

A trace records one query as it passes through the memory pipeline. `run_id` groups records from the same experiment run; `example_id` identifies the evaluated example without exposing the original question or conversation ID.

### Provenance without raw conversation text

The schema stores stable IDs, content hashes, source spans, transformation lineage, and operational metadata. It deliberately does not define fields for raw conversation messages, raw queries, or reference answers. Keep sensitive source text in its approved data store and link only through access-controlled identifiers.

A plain SHA-256 hash is not anonymization: low-entropy text can be guessed and hashed. Treat hashes and IDs as potentially linkable metadata; use access controls, retention limits, and dataset-specific privacy rules.

### Four-stage observability

The `observability` object records whether the source archive, pre-compression trace, memory provenance, retrieval trace, and answer trace are available. If a stage is not observable, its failure mode must be marked unknown in evaluation rather than inferred as absent.

The `pipeline` object records source evidence, candidate memory, stored memory, retrieved evidence, and transformations. Stable IDs connect records across stages. The same underlying fact may have different evidence and memory IDs after a transformation; preserve lineage through `source_evidence_ids` and transformation input/output IDs.

### Online diagnosis versus oracle labels

`diagnosis` is the system's online multi-label estimate. The four probabilities are independent probabilities and must not be normalized to sum to one.

`oracle_labels` is evaluation-only annotation. It must never be passed to the online failure estimator or controller. Use `null` in production/inference traces. The validator's `--online` flag enforces this separation.

An oracle label may be `null` when the mode is unobservable or cannot be adjudicated. Do not encode unknown as `false`.

### Answer evidence

The outcome records answer and claim hashes plus evidence IDs and support states. It does not store generated answer text. The answer evaluator should preserve a separate access-controlled mapping if textual adjudication is required.

### Costs

Record actual token counts and latency where available. Use `null` when a measurement is unavailable; do not silently substitute estimates for measured values. If estimates are used, label them in experiment documentation.

## Validate

Install the optional dependency:

```bash
python -m pip install jsonschema
```

Validate a synthetic or experimental trace:

```bash
python MemWeave/scripts/validate_mfar_trace.py path/to/trace.json
```

Validate an inference trace and reject oracle labels:

```bash
python MemWeave/scripts/validate_mfar_trace.py path/to/trace.json --online
```

The validator checks JSON Schema structure and date-time formats. It does not establish that provenance links are semantically correct, that spans point to real source records, or that labels are accurate. Those require referential-integrity checks and annotation audits in the next implementation stage.

## Known limitations to address in version 0.2

1. Add explicit cross-reference checks: every referenced evidence, memory, transformation, and answer ID should resolve.
2. Enforce span ordering (`end > start`) and verify offsets against source metadata.
3. Define a versioned ontology for query requirement kinds and diagnostic feature names.
4. Define units and tokenizer identity for token and cost measurements.
5. Add annotation provenance, adjudication protocol, and inter-rater agreement details.
6. Decide whether multiple source conversations and multiple answer attempts need first-class representation.
7. Replace the placeholder schema `$id` with a stable project-controlled URI if the project publishes one.

## Next implementation task

Build an offline trace assembler that converts existing benchmark records and retrieval outputs into this schema, then run referential-integrity and privacy checks. Only after trace coverage is measured should the failure-label generator be built.
