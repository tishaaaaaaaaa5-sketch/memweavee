# Contributing to MemWeave

Thanks for helping improve MemWeave. The repository combines research notebooks, benchmark artifacts, and an installable Python research platform. Contributions should preserve the distinction between historical research evidence and new software behavior.

## Development setup

Use Python 3.10 or newer. From the repository root:

```bash
python -m pip install -e "MemWeave[dev,dashboard,api]"
```

For work on the extracted research pipeline, use the pipeline-extraction branch/PR and install its research extra from the `MemWeave/` directory:

```bash
cd MemWeave
python -m pip install -e ".[dev,research]"
```

Do not assume that pipeline-extraction functionality is already present on `main`; check the target branch before relying on the `memweave run` command.

## Common checks

From the repository root:

```bash
python -m pytest MemWeave/tests
python MemWeave/scripts/validate_release.py
```

For Python changes, also run Ruff where available:

```bash
python -m ruff check MemWeave/src MemWeave/tests
```

The release validator checks consistency of committed aggregate artifacts. It does not retrain models, rerun benchmarks, verify source datasets, or establish independent replication.

## Contribution guidelines

### Keep research history traceable

- Do not overwrite or silently relabel historical Stage A, Stage B, or Stage C results.
- Keep distinct runs, datasets, splits, budgets, and model configurations separate.
- Record the branch/commit, configuration, random seeds, dataset revision, and checksums for new experiments.
- Separate development-set tuning from locked-test evaluation.
- Treat synthetic tests as software verification, not benchmark evidence.

### Protect benchmark data

- Do not commit raw conversation histories, user messages, answers, or licensed benchmark payloads.
- Keep local datasets and generated caches outside version control.
- Prefer privacy-reviewed aggregate outputs and minimal per-example identifiers.
- Check dataset terms and attribution before publishing derived artifacts.

### Keep claims calibrated

- Evidence retention/recall is not the same as retrieval quality or answer accuracy.
- A string-match proxy is not an LLM reader evaluation.
- A successful CLI run is not proof of parity with a canonical notebook.
- Distinguish held-out evaluation from independent replication and report uncertainty and sample scope.

### Keep software changes maintainable

- Prefer small, focused modules with explicit inputs and outputs.
- Add unit tests for pure transformations and integration tests for cross-module behavior.
- Keep network access and dataset downloads explicit; commands should not silently fetch benchmark data.
- Preserve backwards-compatible CLI behavior unless a change is intentional and documented.
- Update the relevant README or guide when commands, configuration, outputs, or limitations change.

## Pull request checklist

Before requesting review, confirm that the PR:

- [ ] States the user-facing or research-software problem it solves.
- [ ] Identifies the affected branch and modules.
- [ ] Includes tests for changed behavior.
- [ ] Reports commands run and their actual outcomes.
- [ ] Does not include raw benchmark data or sensitive conversation content.
- [ ] Updates documentation and configuration examples where needed.
- [ ] Separates software verification from scientific claims.
- [ ] Notes known limitations and follow-up work.
