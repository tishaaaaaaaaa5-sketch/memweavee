# Research pipeline extraction

This change extracts reusable research stages from
`notebooks/04_MemWeave_Final.ipynb`. The notebook remains unchanged; the
extracted modules accept explicit inputs and return explicit outputs.

## Extracted modules

| Module | Notebook source | Extracted behavior |
|---|---|---|
| `memweave.data` | Section 1 | LongMemEval parsing, content-hash deduplication, label-free session statistics, HashingVectorizer and sublinear TF-IDF |
| `memweave.features` | Section 2 | Candidate-pool definitions, within-pool z-scoring, 10 feature columns, similarity summaries and feature-group indices |
| `memweave.experiment` | Section 2 | Per-question pool construction and stratified locked dev/test split |
| `memweave.selection` | Section 3 | Word-cost budget, stable rank/density selection, greedy MMR and evidence recall |
| `memweave.inference` | Section 3 | Question-level bootstrap, paired bootstrap/sign p-value, Holm correction and verdict classification |
| `memweave.modeling` | Section 5 | Leakage-aware LR/HGB fitting, deterministic folds, out-of-fold predictions and CV evidence recall |
| `memweave.tuning` | Section 5 | Development-only C search, backward feature-group elimination, one-standard-error selector choice and simple-rule selection |
| `memweave.evaluation` | Sections 6–7 | Frozen locked-test results, paired/Holm comparisons, group ablations, mechanism tests and budget sweep |
| `memweave.robustness` | Section 7 | Repeated stratified split seeds with fresh dev-only tuning and paired per-split diagnostics |
| `memweave.downstream` | Section 8 | Retrieval-based evidence hit@k and answer-in-context proxy with paired comparisons |
| `memweave.transfer` | Section 9 | LoCoMo session/evidence parsing, transfer and role-free models, conversation-cluster bootstrap |
| `memweave.runner` | Orchestration | Local data ingestion, frozen dev tuning, locked-test evaluation, optional robustness/LoCoMo, CSV/JSON outputs and SHA-256 manifest |

## Run the extracted pipeline

Install the research dependencies from `MemWeave/`:

```bash
pip install -e ".[dev,research]"
pytest
```

Copy `configs/pipeline.yaml`, set `pipeline.longmemeval_path` to a local
LongMemEval-S JSON file, and optionally set `pipeline.locomo_path` to a local
LoCoMo JSON file. Then run:

```bash
memweave run --config configs/pipeline.yaml
```

The runner never downloads benchmark data. It writes CSV tables, a
`run_config.json`, `findings.txt`, and a `manifest.json` containing SHA-256
hashes for each output file. Optional robustness seeds rerun dev tuning for
each split; their overlapping test halves are explicitly descriptive.

## Leakage and test-set boundary

`memweave.tuning.tune_pool` accepts development question IDs and development
folds only. Its output is the frozen per-pool configuration. The locked-test
evaluation accepts those frozen configurations and disjoint development/test
IDs; it does not tune hyperparameters or choose the best simple rule.

The model-fitting helpers remove training rows whose deduplicated session
content appears in any held-out question. The LoCoMo transfer helper trains on
LongMemEval only and bootstraps at the conversation level, not the QA-row level.

The downstream module measures retrieval-based evidence hit@k and literal
answer-in-context@k. This is not end-to-end LLM answer accuracy.

## Parity status and limitations

Synthetic fixtures exercise feature ordering, candidate pools, selection
semantics, bootstrap calculations, leakage filtering, out-of-fold coverage,
tuning, locked-test orchestration, downstream retrieval, LoCoMo evidence
parsing and artifact-manifest writing.

**Full benchmark parity has not yet been established.** The canonical notebook
does not contain executed outputs, and the checked-in executed notebook is a
different role-aware evaluation pipeline, so its numbers are not valid
reference outputs for this notebook. The LongMemEval and LoCoMo input datasets
are also not checked into the repository. A full parity run requires the exact
source datasets and a saved execution of the canonical final notebook. No
benchmark metrics are claimed by synthetic tests or the extraction itself.

The downstream answer-in-context measure is a literal string-match proxy, not
reader-model QA accuracy. Alternative split test halves overlap and are not
independent replications.

## Existing aggregate audit

The pre-existing artifact-audit workflow remains separate:

```bash
memweave evaluate --config configs/role_aware.yaml
```

That command audits committed aggregate outputs; it does not rerun experiments.
