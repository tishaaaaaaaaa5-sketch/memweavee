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

Read the [Stage C follow-up report](results/followup_2026/README.md) for ablation results, provenance, interpretation, and remaining limitations. The [Stage C Kaggle follow-up notebook](notebooks/05_MemWeave_Kaggle_Followup.ipynb) is now committed. Its seven generated CSV/JSON result exports remain separate release artifacts and are not included in this notebook-only commit.

## Proposed next research direction: MFAR

The next proposed contribution is **Memory Failure-Aware Retrieval (MFAR)**. It treats construction, compression, retrieval, and answering failures as distinct but potentially co-occurring failure modes, and proposes trace-aware diagnostics with targeted interventions under explicit resource budgets.

MFAR is a design proposal, not an implemented or validated method. Its algorithm specification, hypotheses, observability requirements, evaluation plan, ablations, and decision gates are in [MFAR_ALGORITHM_DESIGN.md](docs/MFAR_ALGORITHM_DESIGN.md).

The first engineering contract is the [MFAR trace schema](schemas/mfar_trace.schema.json), with an [illustrative trace](schemas/examples/mfar_trace.example.json), [schema implementation notes](docs/MFAR_TRACE_SCHEMA.md), and [validator CLI](scripts/validate_mfar_trace.py). The schema is an initial instrumentation contract, not yet integrated into the existing memory pipeline. Schema v0.2.0 supports explicitly unobserved stages. An offline adapter can convert the Stage B/C retention export into partial traces; this does not create retrieval or answer evidence. See [the adapter specification](docs/MFAR_RETENTION_TRACE_ADAPTER.md) and [assembler](scripts/assemble_mfar_retention_traces.py). The existing Stage A/B/C results are motivation and baselines; they are not evidence that MFAR works.

The Stage B/C notebook now includes an additional candidate-level trace export. The original controlled run produced seven exports; rerun the updated final export cell to generate the eighth `stage_bc_candidate_trace.csv` required by the offline MFAR adapter. Do not interpret its session-retention decisions as a separate retrieval stage or answer evaluation.


### MFAR implementation scope

MFAR development proceeds only from original benchmark artifacts and observable events from the real memory pipeline. Synthetic failure fixtures are excluded from the research workflow. The existing Stage B/C adapter records retention selection only; retrieval and answer stages remain unobserved until real pipeline instrumentation is available. No failure labels or probabilities may be inferred for those missing stages. The original retention traces can now be audited with [the real-data retention audit utility](scripts/audit_mfar_retention_traces.py) and [its usage note](docs/MFAR_RETENTION_AUDIT.md). It reports retained/missed gold candidates and budget-proxy utilization without assigning any MFAR failure labels.

The existing v2.x notebooks contain an experimental pipeline for session encoding, candidate-pool construction, budget-constrained retention, BM25 ranking, QA-context assembly, and optional downstream language-model answering. These are real benchmark operations, but they are not equivalent to a continuously running persistent-memory service or a separately measured compression/index backend. The corrected operation-by-operation assessment is in [MFAR_REAL_BACKEND_INSTRUMENTATION.md](docs/MFAR_REAL_BACKEND_INSTRUMENTATION.md), and the exact Notebook 01 instrumentation points are mapped in [MFAR_NOTEBOOK_INSTRUMENTATION_MAP.md](docs/MFAR_NOTEBOOK_INSTRUMENTATION_MAP.md). Runtime event capture and lineage validation remain the next engineering gate; no missing-stage failure labels may be inferred.

## Canonical notebook sequence

See [the notebook index](notebooks/README.md). The Stage C Kaggle notebook is published at [05_MemWeave_Kaggle_Followup.ipynb](notebooks/05_MemWeave_Kaggle_Followup.ipynb). The obsolete false-positive audit cell and automatic terms-confirmation cell were removed; the corrected audit remains. The six generated CSV/JSON exports are still pending separate publication and privacy review.

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
