# Contributing to MemWeave

Thank you for helping improve MemWeave. The repository combines a historical notebook-based research record with a Python tooling layer. Contributions should improve the software without silently changing the meaning of previously reported experiments.

## Development setup

Use Python 3.10 or newer. From the repository root:

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell
# .venv\\Scripts\\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -e "MemWeave[dev,dashboard,api]"
```

For work that only touches the package and tests, the development extra is sufficient:

```bash
python -m pip install -e "MemWeave[dev]"
```

## Local checks

Run the test suite:

```bash
pytest MemWeave/tests
```

Run Ruff when changing Python code:

```bash
ruff check MemWeave/src MemWeave/tests
```

Validate the committed aggregate release artifacts:

```bash
memweave validate
# Equivalent explicit audit:
memweave evaluate --config MemWeave/configs/role_aware.yaml
```

The artifact audit checks consistency of committed outputs. It is not a fresh benchmark run, model retraining, or independent replication.

## Working with research data

- Do not commit raw benchmark datasets, private conversations, credentials, API keys, or large generated caches.
- Keep dataset acquisition explicit. Do not add implicit network downloads to commands that process benchmark data.
- Record dataset identity and SHA-256 checksums when a run consumes external data.
- Keep development-set tuning separate from locked-test evaluation.
- Treat question-level and conversation-level uncertainty according to the sampling unit used by the experiment.
- Label proxy metrics clearly. Evidence recall, answer-in-context string matching, and reader-model answer quality are different outcomes.
- Preserve historical notebooks and result artifacts unless a change is specifically intended to revise them and includes an audit trail.

## Pull request checklist

Before opening a pull request:

- [ ] Explain the user-facing or research-software problem being solved.
- [ ] Keep the change focused and describe any migration or compatibility impact.
- [ ] Add or update tests for changed behavior.
- [ ] Run the relevant tests and static checks; report exactly what was run.
- [ ] Update documentation and configuration examples when interfaces change.
- [ ] State whether results are synthetic-test results, artifact audits, or real benchmark executions.
- [ ] Do not claim benchmark parity or scientific replication unless it has been directly established.

Small, reviewable pull requests are preferred. If a change affects reported research results, include the affected notebook, configuration, source data identifiers, seeds, and generated artifacts in the explanation.
