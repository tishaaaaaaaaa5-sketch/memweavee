# Research artifact bundle — 2026-11-26

**Bundle:** [MemWeave_Research_Artifacts.zip](MemWeave_Research_Artifacts.zip)  
**Source:** uploaded Kaggle execution snapshot; original upload commit `a8d27a625d7d11d56883225ccf99fa7df866fbfa`.

## Recorded export facts

The notebook's final export cell reports 52 archived files, a ZIP size of approximately 1.51 MiB, a successful `ZipFile.testzip()` integrity check, and archive SHA-256:

```
32bc3f886f569a8fe788ca62b37032fe51d44178184b432539a7b224b7575634
```

The export code recursively packages `/kaggle/working/memweave_followup_outputs`, includes matching corrected ablation CSVs, and writes `SHA256_MANIFEST.json`.

## Release status

This directory is the canonical repository location for the uploaded bundle. The bundle is **preserved, not yet certified for public release**.

Before treating it as a reproducible public artifact:

1. Extract the ZIP and enumerate every path, byte size, and SHA-256.
2. Compare every file against `SHA256_MANIFEST.json` and the notebook's recorded archive hash.
3. Reconcile the inventory against the expected Stage B/C, MFAR-retention, LoCoMo reader-QA, Long-MT-Bench+, and corrected ablation outputs.
4. Review file contents for raw benchmark conversations, session text, prompts, answers, private identifiers, or other restricted material.
5. Record dataset terms and any redistribution restrictions.

The notebook's saved output reports a successful ZIP integrity test, but this repository intake did not independently extract the binary and verify each manifest entry. Do not describe the archive as independently audited until the checks above are completed.

## Interpretation guardrails

- The consolidated notebook is an execution archive, not a canonical replacement for Notebook 06.
- The corrected LongMemEval leave-one-role-feature-out summary is in notebook cell 85 and is descriptive, not causal feature attribution.
- The Long-MT-Bench+ individual feature-ablation cell failed; it is not a completed result.
- MFAR artifacts currently document retention-only traces. They do not validate compression, retrieval, answer-stage failure detection, or an end-to-end MFAR controller.
