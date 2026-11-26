# MemWeave architecture

MemWeave has two complementary layers:

1. **Research record:** notebooks, benchmark reports, configurations, and committed result artifacts. These preserve the history and scope of the experiments.
2. **Research software platform:** installable Python tooling for validation, metrics, configuration, command-line workflows, and read-only result presentation.

The platform is intended to make research assets easier to inspect and maintain. It must not blur the distinction between checking saved outputs and rerunning an experiment.

## Repository map

| Path | Responsibility |
|---|---|
| `MemWeave/notebooks/` | Canonical exploratory and evaluation notebooks |
| `MemWeave/results/` | Committed aggregate reports and evaluation artifacts |
| `MemWeave/configs/` | YAML configuration for supported workflows |
| `MemWeave/src/memweave/` | Installable Python package |
| `MemWeave/tests/` | Unit and integration tests for the package |
| `MemWeave/api/` | Read-only HTTP results API |
| `MemWeave/dashboard/` | Read-only Streamlit results dashboard |
| `MemWeave/scripts/` | Repository-level validation utilities |
| `.github/workflows/` | Automated quality checks |

## Runtime boundaries

### Artifact audit

The `memweave validate` and `memweave evaluate` workflows validate committed aggregate artifacts. They do not download data, retrain models, or reconstruct missing per-question predictions.

### Research execution

Notebook workflows remain the historical source of the reported research results. Any extracted or newly automated pipeline must document its relationship to the notebook implementation, make data inputs explicit, and preserve development/locked-test separation. A successful synthetic test suite is evidence of software behavior on fixtures, not proof of parity on a benchmark.

### Presentation

The dashboard and API expose saved results for inspection. They are read-only interfaces; they should not mutate source artifacts or launch expensive training jobs as a side effect of viewing a page.

## Configuration and data

- Keep configuration in version-controlled YAML with safe parsing.
- Keep raw datasets outside the repository unless licensing and storage constraints have been reviewed.
- Make paths and random seeds explicit.
- Record software versions, input checksums, and output checksums for reproducible runs.
- Avoid placing secrets or user conversation content in logs and generated reports.

## Change strategy

Prefer small modules with explicit inputs and outputs. Keep notebook-derived logic isolated from presentation code. Add tests at the layer being changed, then add an integration test when behavior crosses module boundaries. When changing a metric or evaluation protocol, document the definition and update affected reports rather than silently changing the interpretation of existing numbers.
