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

The reviewed Stage C notebook is committed at [notebooks/05_MemWeave_Kaggle_Followup.ipynb](../../notebooks/05_MemWeave_Kaggle_Followup.ipynb). Its six generated CSV/JSON result exports are not yet committed as separate artifacts. The report at [results/followup_2026/README.md](../../results/followup_2026/README.md) records the results and the outstanding artifact gap.

## Committed artifact consistency check for the earlier release

From the repository root:

```bash
python MemWeave/scripts/validate_release.py
```

This standard-library validator checks internal agreement among the earlier run manifest, paired audit JSON, and question-type aggregate CSV. A successful check does not rerun training/evaluation, recover missing per-question rows, verify the source dataset, or establish independent generalization. Its warnings apply to the earlier release snapshot; they should not be confused with Stage C's separately recorded provenance.

## Remaining work before Stage C is a complete release

- [ ] Export and publish the six generated CSV/JSON artifacts from the Kaggle output directory, subject to privacy and licensing review.
- [ ] Verify each artifact checksum against the run manifest; include the per-question CSV checksum already printed by the notebook.
- [ ] Re-run the final audit from the committed notebook and exported artifacts in a clean environment.
- [ ] Independently reconstruct the word-count budget from selected session IDs and word costs; replace the proxy with exact tokenizer-based accounting in the next controlled study.
- [ ] Audit gold-evidence-to-session mapping end to end.
- [ ] Verify LoCoMo speaker-role mapping and annotation alignment.
- [ ] Obtain an independent reproduction before claiming independent replication.

## Privacy and licensing

Do not commit raw conversation histories, answers, or session text merely to make the experiment reproducible. Publish only minimal derived audit data permitted by the dataset terms. Include license and attribution for every dataset.

## Claims

Stage B and Stage C are distinct runs with materially different role-aware recall estimates (0.709433 and 0.820638). Report them separately until the source of the difference is understood. Stage C's LoCoMo results are preliminary transfer evidence over ten conversation clusters, not definitive independent replication. Evidence recall is not end-to-end answer accuracy.


## Stage B/C controlled reconstruction — artifact audit (2026-11-26)

The user-supplied reconciliation bundle and separately supplied candidate trace were inspected together. The candidate CSV in the bundle is byte-identical to the separately supplied CSV and has SHA-256 `79610897e7401a297434b8a5b9703c9407658a4e4fc04fdd7b56981b6c860065`.

- LongMemEval-S revision: `98d7416c24c778c2fee6e6f3006e7a073259d48f`; SHA-256: `d6f21ea9d60a0d56f34a05b609c79c88a451d2ae03597821ea3d5a9678c3a442`.
- LoCoMo revision: `cbfbc1dba6bc53d00625212a0f22d55ffee7c1fc`; SHA-256: `79fa87e90f04081343b8c8debecb80a9a6842b76a7aa537dc9fdf651ea698ff4`.
- Source notebook commit: `d642215226fa2a9204bb6d64c4ff0f6447920274`.
- Split: 235 DEV / 235 TEST; candidate export: 49,140 rows, 2,115 question-condition groups (235 × 9).
- The seven derived artifacts listed in the audited manifest match their recorded SHA-256 digests. The candidate CSV also matches its recorded digest.
- Candidate source IDs repeat in 18 question-condition groups across two questions. Repeated rows have the same source ID/content hash; they are retained as distinct ranked occurrences by candidate index. They must not be deduplicated.
- Cross-checks: candidate-level recall agrees with all 2,115 per-question records; the 1,880 role-aware selected-candidate sets and selected word costs agree with the selection-trace export. Candidate-index list order is not semantically meaningful; compare as sets.

Controlled reconstruction results (evidence recall, not answer accuracy):

| Condition | Mean recall |
|---|---:|
| Baseline | 0.404184 |
| Raw role features, 20k vocabulary | 0.709433 |
| Raw role features, uncapped vocabulary | 0.684610 |
| Z-score role features, 20k vocabulary | 0.827021 |
| Z-score role features, uncapped vocabulary | 0.820638 |

Factorial contrasts: scaling +0.126809 (95% bootstrap CI 0.086596–0.169007); vocabulary-cap factor −0.015603 (CI −0.026241 to −0.006738); message-filter factor 0.000000 (CI 0–0). These are effects in this reconstruction and should not be generalized beyond the tested pipeline. Filtering's zero effect warrants a targeted check of whether the filter changes any candidate messages in this data.

**Statistical reporting correction:** Holm-adjusted p-values in `stage_bc_factorial_summary.csv` apply to the eight variant-vs-baseline paired sign tests. They are not Holm-adjusted tests of the factorial main effects. Factorial effects are reported with paired-question bootstrap intervals. Any manuscript must preserve this distinction.

The candidate trace and detailed CSV exports are not committed as raw repository files in this revision. The audited manifest, checksum inventory, and audit report are committed; retain the original ZIP and CSV as release artifacts under the dataset terms and attach them to a versioned release or approved artifact store. Do not commit source conversations, answers, or raw session text.

The MFAR adapter has not yet been independently executed against this exact user-supplied CSV/manifest pair. Passing unit tests or static consistency checks must not be described as a successful end-to-end adapter run.



## Follow-up release checkpoint — 2026-11-27

This checkpoint supersedes older "pending execution" statements in follow-up notes where later results are listed below. It does not imply that the raw run artifacts have been published.

### Repository inspection

- The Stage C notebook exists at `MemWeave/notebooks/05_MemWeave_Kaggle_Followup.ipynb`.
- The committed notebook contains 25 cells. Thirteen code cells have execution counts and saved outputs. The appended end-to-end reader QA, whole-session packing, and subsequent evidence-span/reader follow-ups are not represented as executed outputs in this committed notebook snapshot.
- Therefore, the committed notebook is not yet a complete executed record of the later QA work. The QA result reports document the supplied results, but the raw QA outputs remain in the Kaggle runtime unless separately exported.
- The six Stage C CSV/JSON exports listed in `results/followup_2026/README.md` are still not present as separate committed files in the release inventory. Do not describe the Stage C artifact package as complete.
- The current follow-up results report documents LoCoMo span-packing results for FLAN-T5-small and FLAN-T5-base, plus corrected Long-MT-Bench+ span-budget results. Their raw per-question outputs, bootstrap JSONs, and budget-audit exports still need to be attached as privacy-reviewed artifacts.
- The repository's older aggregate validator targets `results/final_locked_test/` (Stage B). It does not validate the Stage C follow-up or later reader QA artifacts.

### Latest corrected individual role-feature ablation

The corrected leave-one-feature-out table was reconstructed from the actual `F_aug[:, ROLE_IDX]` columns using the original DEV/TEST training and evaluation pipeline. The earlier attempt that used nonexistent/wrong feature matrices is discarded. The valid descriptive results are:

| Variant | Retained role features | Mean budgeted recall | Recall delta vs full |
|---|---:|---:|---:|
| Full role-aware | 6 | 0.820638 | 0.000000 |
| Leave out user max question similarity | 5 | 0.819574 | -0.001064 |
| Leave out user top-3 mean question similarity | 5 | 0.827021 | +0.006383 |
| Leave out assistant max question similarity | 5 | 0.822057 | +0.001418 |
| Leave out assistant top-3 mean question similarity | 5 | 0.827021 | +0.006383 |
| Leave out log user message count | 5 | 0.820638 | 0.000000 |
| Leave out log assistant message count | 5 | 0.820638 | 0.000000 |
| Baseline | 0 | 0.404184 | -0.416454 |

All variants used 4,216 training candidates out of 5,523 and 235 held-out questions. These are descriptive leave-one-out comparisons, not causal feature-importance estimates; no per-question paired uncertainty is included in this aggregate table. Message-count feature removals had no observed effect in this run. The corrected aggregate CSV was saved in the Kaggle runtime, but its checksum and committed copy have not yet been verified.

### Latest downstream QA status

- LoCoMo evidence-span packing, FLAN-T5-small: 200 questions / 10 conversations; role-aware token F1 0.2417, exact match 0.120; paired cluster-bootstrap token-F1 gain +0.1401 vs baseline (95% CI [+0.0640, +0.2213]).
- LoCoMo evidence-span packing, FLAN-T5-base: same 200 questions / 10 conversations; role-aware token F1 0.2376, exact match 0.100; paired cluster-bootstrap token-F1 gain +0.1458 vs baseline (95% CI [+0.0818, +0.2170]).
- Long-MT-Bench+ corrected span-budget transfer, FLAN-T5-base: 288 questions / 11 conversations; role-aware token F1 0.1443 vs baseline 0.0823 and recency 0.0810; paired cluster-bootstrap gains +0.0627 and +0.0634 respectively. Exact match is 0.0035 for role-aware and recency, so no exact-match advantage over recency is established.

These are exploratory results from 10 and 11 conversation clusters. Exact match/token F1 are lexical metrics; gold annotations are session-level and lexical span ranking is not semantic entailment. Do not present these as definitive independent confirmation.

### Actions required to close the release

1. Export the six Stage C CSV/JSON files and the corrected individual-ablation CSV from the Kaggle output directory. Record SHA-256 for each file and verify against the run manifest where a digest exists.
2. Export the LoCoMo small/base span-packing and Long-MT-Bench+ per-question CSVs, paired cluster-bootstrap JSONs, and token-budget audits. Include dataset/revision, code commit, reader model revision, prompt, tokenizer, seed, and sample IDs in each manifest.
3. Commit a privacy-reviewed executed notebook or a separate machine-readable run bundle for the later QA experiments. Do not leave reports implying that the current committed notebook contains those executed cells.
4. Re-run validators against the exported artifacts from a clean environment. Keep the Stage B aggregate validator separate from Stage C/reader-QA validators.
5. Complete the independent word-cost reconstruction, gold-evidence mapping audit, and LoCoMo speaker-role/annotation alignment checks already listed above.
6. Update all summary documents to remove stale status statements and preserve the distinction between Stage B, Stage C, and downstream QA endpoints.

**Release status:** documentation is substantially informative, but the Stage C and downstream QA artifact bundle remains incomplete until the raw privacy-safe exports, manifests, checksums, and clean-environment validation are committed.
