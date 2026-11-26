# Reproducibility audit

## Release status by experiment stage

### Stage B — Earlier role-aware locked-test run

The earlier locked-test notebook snapshot did not preserve the exact dataset revision/SHA-256 or the privacy-safe per-question export. Its aggregate report remains a historical result. Do not apply Stage C provenance to Stage B or retroactively claim that Stage B's original source file was checksum-verified.

### Stage C — Regenerated follow-up

A later executed Kaggle notebook supplied for review regenerated the per-question export, pinned both datasets, recorded SHA-256 checksums, ran feature ablations, evaluated frozen LongMemEval models on LoCoMo, and executed a final artifact audit.

Recorded provenance:

| Dataset | Immutable revision | SHA-256 |
|---|---|---|
| LongMemEval-S cleaned | `98d7416c24c778c2fee6e6f3006e7a073259d48f` | `d6f21ea9d60a0d56f34a05b609c79c88a451d2ae03597821ea3d5a9678c3a442` |
| LoCoMo | `cbfbc1dba6bc53d00625212a0f22d55ffee7c1fc` | `79fa87e90f04081343b8c8debecb80a9a6842b76a7aa537dc9fdf651ea698ff4` |

The Stage C notebook's final audit reported 54 PASS, 3 WARNING, and 0 FAIL. This validates the checks implemented in that notebook against its generated files. It is not an independent rerun of the experiment or proof that every evaluator mapping is correct.

The Stage C notebook and its separate generated CSV/JSON outputs have not yet been committed to this repository branch. The report at [results/followup_2026/README.md](../results/followup_2026/README.md) records the results and explicitly identifies this artifact gap.

## Committed artifact consistency check for the earlier release

From the repository root:

```bash
python MemWeave/scripts/validate_release.py
```

This standard-library validator checks internal agreement among the earlier run manifest, paired audit JSON, and question-type aggregate CSV. A successful check does not rerun training/evaluation, recover missing per-question rows, verify the source dataset, or establish independent generalization. Its warnings apply to the earlier release snapshot; they should not be confused with Stage C's separately recorded provenance.

## Remaining work before Stage C is a complete release

- [ ] Commit the reviewed Stage C notebook with obsolete/debug outputs removed.
- [ ] Attach the six generated CSV/JSON artifacts from the Kaggle output directory.
- [ ] Verify each artifact checksum against the run manifest; include the per-question CSV checksum already printed by the notebook.
- [ ] Re-run the final audit from the committed artifacts in a clean environment.
- [ ] Independently reconstruct the word-count budget from selected session IDs and word costs.
- [ ] Audit gold-evidence-to-session mapping end to end.
- [ ] Verify LoCoMo speaker-role mapping and annotation alignment.
- [ ] Obtain an independent reproduction before claiming independent replication.

## Privacy and licensing

Do not commit raw conversation histories, answers, or session text merely to make the experiment reproducible. Publish only minimal derived audit data permitted by the dataset terms. Include license and attribution for every dataset.

## Claims

Stage B and Stage C are distinct runs with materially different role-aware recall estimates (0.709433 and 0.820638). Report them separately until the source of the difference is understood. Stage C's LoCoMo results are preliminary transfer evidence over ten conversation clusters, not definitive independent replication. Evidence recall is not end-to-end answer accuracy.
