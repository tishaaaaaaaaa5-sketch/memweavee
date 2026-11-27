# MemWeave research platform

This layer adds installable Python tooling around the existing notebook-led research record. It does not rewrite historical notebooks or claim that aggregate validation is a fresh model evaluation.

## Install

From the repository root:

    python -m pip install -e "MemWeave[dev,dashboard,api]"

## Commands

    memweave --version
    memweave validate
    memweave evaluate --config MemWeave/configs/role_aware.yaml
    pytest MemWeave/tests
    memweave serve
    memweave browser-audit --input /private/path/memweave-evidence-labels.json --output-dir results/browser_audit

The evaluate command currently performs aggregate artifact validation using the committed manifest, paired audit JSON and question-type CSV. It checks internal consistency; it does not retrain a model, fetch benchmark data, or recreate missing per-question predictions.

## Dashboard

The serve command launches a read-only Streamlit dashboard over the committed role-aware aggregate results.

## API

Install optional API dependencies and run:

    uvicorn api.app:app --app-dir MemWeave --reload

Endpoints: GET /health, GET /results/summary, GET /results/question-types.

## Next integration step

The package currently contains shared metric helpers, safe YAML configuration loading, CLI orchestration, unit tests, CI, a dashboard and a read-only API. The research algorithms remain in canonical notebooks. The next substantive step is to extract the exact tested preprocessing, feature and retrieval pipeline into versioned modules, then add end-to-end tests against synthetic fixtures. Do not silently substitute a new implementation for the historical experimental pipeline.


## Experiment run registry

The extracted pipeline records each successful execution in a local SQLite registry. The registry stores a unique run ID, UTC creation time, output directory, input checksum, manifest checksum, configuration, and a compact result summary. It stores provenance pointers and summaries—not raw benchmark data or full per-question predictions.

Each run receives its own subdirectory under the configured `pipeline.output_dir`, so later runs do not overwrite earlier artifacts. By default, the registry is written to `run_registry.sqlite3` next to that output root (for the default `results/pipeline_run`, this is `results/run_registry.sqlite3`). Override this with `pipeline.registry_path` in `configs/pipeline.yaml`.

After a pipeline run:

```bash
memweave runs list
memweave runs list --limit 50
memweave runs show <RUN_ID>
```

To inspect a registry at a custom location:

```bash
memweave runs --registry /path/to/run_registry.sqlite3 list
```

The registry is append-only at the run-ID level: recording an existing ID fails rather than overwriting its provenance. It is a local convenience index, not a replacement for preserving the run output directory and its `manifest.json`. Back up both the registry and the referenced artifacts when archiving a study.


## Comparing experiment runs in the dashboard

The read-only Streamlit dashboard now includes a registry-backed run history and comparison view. It displays each completed run's ID, timestamp, primary pool, split sizes and output directory; selected runs can be compared by pool/method recall and by nested configuration values.

By default, the dashboard looks for:

    results/run_registry.sqlite3

This is the default registry location when the pipeline writes to results/pipeline_run. To use a registry elsewhere, set the environment variable before starting the dashboard:

    MEMWEAVE_REGISTRY_PATH=/path/to/run_registry.sqlite3 memweave serve

The comparison is descriptive, not a paired significance test. Runs using different input datasets, split seeds, budgets or evaluation settings may not be directly comparable. The dashboard shows configuration differences to make those changes visible; it does not claim that a metric change was caused by a particular code or configuration change.

The historical aggregate-results view remains available independently of the local run registry. The dashboard does not execute models or download benchmark data.


## Provenance-aware run comparability

New pipeline runs store a structured summary.provenance record alongside their metrics:

- SHA-256 of the exact LongMemEval input file.
- Stable SHA-256 fingerprints of the ordered DEV and TEST question-ID lists.
- Metric protocol identifier, primary pool, budget fraction and budget-cost unit.
- Split and cross-validation seeds/fold count.
- Optional dataset revision labels and LoCoMo dataset checksum/revision when transfer evaluation is run.

The dashboard now gates primary LongMemEval evidence-recall comparisons:

- **Directly comparable:** all required dataset, split, metric, budget and pool fields are present and match.
- **Not comparable:** at least one required field differs.
- **Insufficient provenance:** one or more older runs do not contain the required fields. Missing metadata is never treated as a match.

Model and feature configuration differences remain visible in the separate configuration-difference table. They are not automatically treated as a comparability failure because changing the selector may be the intended experimental variable. The gate does not establish causality or independent replication.

Legacy registry records are not retroactively upgraded. Re-run them with the updated pipeline if a structured provenance record is required. LoCoMo transfer comparability is a separate question: compare its dataset checksum, conversation set, reader and evaluation protocol before interpreting transfer metrics.


## Browser atomic-evidence audit import

The static workspace exports versioned manual annotations plus selected and top-5 retrieved evidence IDs for five browser policies at 10–50% word-proxy budgets. The memweave browser-audit command validates that export and recomputes retention recall separately from retrieval precision/recall/F1@5. It writes derived metrics and an input/output SHA-256 manifest without copying candidate text into the output directory.

This bridge does not convert atomic claims into LongMemEval sessions and does not run the trained LR selector. It is a complementary annotation diagnostic; the canonical pipeline remains session-level and uses its own benchmark labels, features, split, and frozen model protocol. Neither metric substitutes for fixed-reader downstream answer quality.

For multiple questions, save one v2 export per question in a dedicated input
directory and run the same `memweave browser-audit` command with that directory.
Batch mode enforces the same candidate evidence set, policy/budget comparisons,
and retention selections across questions. It calculates macro means, 95%
question-bootstrap percentile intervals, and paired deltas versus rank-only.
The bootstrap unit is the question, and its intervals are descriptive of the
annotated question set rather than population-level benchmark confidence
intervals. Aggregate outputs exclude question text and raw evidence excerpts.
