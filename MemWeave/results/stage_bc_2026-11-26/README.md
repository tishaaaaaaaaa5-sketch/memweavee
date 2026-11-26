# Stage B/C controlled reconstruction — audited artifacts

**Audit date:** 2026-11-26  
**Branch:** `research/memweave-followup-release`  
**Status:** artifact integrity cross-check completed; MFAR adapter end-to-end execution still pending.

## Contents and provenance

The original notebook run produced seven primary CSV/JSON outputs. The candidate-level export was supplied afterward and is bound by the companion audited manifest in this directory. The audited manifest preserves the original notebook-generated manifest; it does not rewrite historical run provenance.

- LongMemEval-S revision: `98d7416c24c778c2fee6e6f3006e7a073259d48f`
- LongMemEval-S SHA-256: `d6f21ea9d60a0d56f34a05b609c79c88a451d2ae03597821ea3d5a9678c3a442`
- LoCoMo revision: `cbfbc1dba6bc53d00625212a0f22d55ffee7c1fc`
- LoCoMo SHA-256: `79fa87e90f04081343b8c8debecb80a9a6842b76a7aa537dc9fdf651ea698ff4`
- Source notebook commit: `d642215226fa2a9204bb6d64c4ff0f6447920274`
- Split: 235 DEV / 235 TEST; pool: `same_pipeline`
- Candidate CSV: 49,140 rows; 2,115 question-condition groups; nine conditions including baseline.
- Candidate CSV SHA-256: `79610897e7401a297434b8a5b9703c9407658a4e4fc04fdd7b56981b6c860065`

See [the audited companion manifest](stage_bc_reconciliation_manifest_audited.json) for the full checksum inventory.

## Reconstructed results

| Condition | Mean evidence recall |
|---|---:|
| Baseline | 0.404184 |
| Raw role features, 20k vocabulary | 0.709433 |
| Raw role features, unlimited vocabulary | 0.684610 |
| Z-score role features, 20k vocabulary | 0.827021 |
| Z-score role features, unlimited vocabulary | 0.820638 |

Factorial contrasts:

| Factor | Effect | 95% paired-question bootstrap CI |
|---|---:|---:|
| Feature scaling | +0.126809 | [0.086596, 0.169007] |
| Vocabulary cap | -0.015603 | [-0.026241, -0.006738] |
| Message filtering | 0.000000 | [0.000000, 0.000000] |

These are results for this controlled reconstruction, not evidence of end-to-end answer accuracy. The zero filtering effect is specific to the tested candidate pipeline and merits checking whether the filter actually changes any candidate messages.

## Integrity checks performed

- All seven derived-artifact checksums in the supplied audited manifest match the corresponding files in the ZIP.
- The candidate CSV in the ZIP is byte-identical to the separately supplied CSV and matches its audited SHA-256.
- Candidate-level evidence recall agrees with all 2,115 per-question rows.
- Candidate selected-index sets and selected word costs agree with all 1,880 role-aware selection-trace groups.
- Repeated source IDs occur in 18 question-condition groups affecting two questions. Repeated occurrences share the same content hash and must not be deduplicated. The adapter now generates distinct trace-local evidence/memory IDs using candidate index.

## Statistical correction

Holm-adjusted p-values in the variant summary apply across the eight variant-vs-baseline paired sign tests. They are not tests of the factorial main effects. The factorial effects are reported separately with paired-question bootstrap intervals.

## Run the MFAR retention adapter

From the repository root, after obtaining the candidate CSV and audited manifest from the supplied output bundle:

```bash
python -m pip install jsonschema
python MemWeave/scripts/assemble_mfar_retention_traces.py \
  --candidates /path/to/stage_bc_candidate_trace.csv \
  --manifest MemWeave/results/stage_bc_2026-11-26/stage_bc_reconciliation_manifest_audited.json \
  --output /path/to/mfar_retention_traces.jsonl
python -m unittest discover -s MemWeave/tests -p "test_*.py"
```

Expected output for this run: 2,115 partial retention traces. This expected count is not a substitute for checking the actual CLI output. The adapter output is not a complete MFAR lifecycle trace: retrieval, answer generation, and failure diagnoses remain unobserved.

## Artifact storage decision

The 12.1 MB candidate CSV and original ZIP bundle are not copied into Git history in this commit. Keep them as versioned release artifacts or in an approved artifact store, subject to dataset terms and privacy review. This directory commits the checksum manifest and audit record, not the raw candidate export. No raw question, answer, conversation, or session text should be added to the repository.
