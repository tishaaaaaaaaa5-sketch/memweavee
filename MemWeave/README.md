# MemWeave research project

MemWeave investigates how to retain useful conversational sessions under a constrained memory budget. The repository contains three related but distinct research stages. Their metrics must remain separately attributed; do not pool them into one headline.

## Research stages

### Stage A — Original retention study (v2.0–v2.3)

- Benchmark: LongMemEval-S cleaned.
- Primary task: query-agnostic session retention.
- Primary metric: session-level evidence recall.
- The v2.3 corrected-inference addendum found a small, sensitivity-dependent advantage over the strongest simple rule. Read `../results/findings_v2_3.txt`; do not describe that result as robust superiority.
- External LoCoMo and downstream QA-proxy results are reported separately and have their own limitations.

### Stage B — Earlier role-aware locked-test run

- Pool: `same_pipeline`; 235 DEV / 235 TEST questions.
- Model: logistic regression, `C=0.3`; six role/message features added to the baseline.
- Budget: 10% of pool word count (a proxy, not exact tokenization).
- Evidence recall: 0.4042 baseline vs. 0.7094 role-aware (+0.3052).
- Paired bootstrap 95% CI: [0.252979, 0.359574].
- This historical run remains documented in [the original locked-test report](results/final_locked_test/README.md).

### Stage C — Regenerated recovery, ablation, and LoCoMo transfer follow-up

The supplied executed Kaggle notebook regenerated a new result set under pinned dataset revisions and added feature ablations plus frozen-model LoCoMo evaluation.

- LongMemEval-S revision: `98d7416c24c778c2fee6e6f3006e7a073259d48f`.
- LongMemEval SHA-256: `d6f21ea9d60a0d56f34a05b609c79c88a451d2ae03597821ea3d5a9678c3a442`.
- DEV / TEST: 235 / 235; `same_pipeline`; logistic regression `C=0.3`.
- Evidence recall: 0.404184 baseline vs. 0.820638 role-aware (+0.416454).
- Paired bootstrap 95% CI: [0.358723, 0.474184].
- The regenerated result differs materially from Stage B. Preserve both records and investigate the difference; do not silently replace the earlier result.
- LoCoMo was pinned to commit `cbfbc1dba6bc53d00625212a0f22d55ffee7c1fc`, SHA-256 `79fa87e90f04081343b8c8debecb80a9a6842b76a7aa537dc9fdf651ea698ff4`.
- Frozen LongMemEval-trained role-aware macro recall was 0.6169 / 0.6165 across two speaker-role orientations, versus baseline 0.0935. This is preliminary transfer evidence over only 10 conversation clusters, not definitive independent replication.
- The final notebook audit reported 54 PASS, 3 WARNING, 0 FAIL. The warnings concern independent budget reconstruction, end-to-end evidence mapping, and independent replication.

Read the [Stage C follow-up report](results/followup_2026/README.md) for ablation results, provenance, interpretation, and remaining limitations. The notebook and generated CSV/JSON files still need to be added as release artifacts; the report does not pretend they are already committed.

## Canonical notebook sequence

See [the notebook index](notebooks/README.md). The uploaded Stage C notebook is pending repository publication and privacy review; it should be added only after obsolete/debug outputs are removed and the separate result exports are attached.

## Reproduction

For the earlier committed aggregate release, run:

```bash
python MemWeave/scripts/validate_release.py
```

This standard-library validator checks internal consistency across the earlier run manifest, paired audit JSON, and question-type CSV. A pass is not a model rerun or independent replication. Stage C has its own audit embedded in the supplied notebook; its CSV/JSON outputs are not yet committed. See [the reproducibility utilities](scripts/README.md) and [the reproducibility audit](docs/REPRODUCIBILITY_AUDIT.md).

For every run, preserve the exact notebook version and outputs, dataset revisions and SHA-256 checksums, Python/package versions, split seed, feature schema, hyperparameters, selection budget, and privacy-safe per-question exports. Do not commit raw benchmark conversations, answers, or session text.

## Data and large files

Raw benchmark JSONs, feature caches and large per-question exports are not stored in this source tree. Keep data outside Git unless licensing and size have been reviewed. For large reproducibility artifacts, use Git LFS or a stable artifact host and record checksums.

## Reporting guidance

Distinguish evidence retention from answer accuracy, Stage A from Stages B/C, and a held-out split from independent replication. The research process was iterative rather than preregistered. The Stage C ablation suggests the message-similarity group accounts for much of the measured gain; do not attribute the full improvement to role-awareness without further controlled experiments.
