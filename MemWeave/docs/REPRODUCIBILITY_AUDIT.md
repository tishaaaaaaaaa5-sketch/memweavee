# Reproducibility audit

This checklist distinguishes artifacts currently documented in the repository from items still required for a complete independent rerun.

## Available in the repository

- Canonical notebook sequence and a cleaned executed final notebook.
- Locked-test report with the 235-question test configuration.
- Paired aggregate audit JSON and question-type aggregate CSV.
- OOF reconstruction check and statistical procedure details.
- Data provenance note and explicit statement that raw per-question exports were not present in the recovered artifact bundle.

## Known gaps

- The role-aware locked-test report does not include the raw per-question export referenced by the notebook.
- The reported budget is a 10% word-count proxy, not tokenizer-exact tokenization.
- The primary uncertainty analysis resamples questions rather than conversation clusters.
- The current reported role-aware test is one split from one benchmark, not an external replication.
- The repository does not yet provide a fully frozen, independently tested environment lock for every notebook stage.

## Required additions before claiming full reproduction

- [ ] Recover or regenerate the permitted per-question result export and publish its checksum.
- [ ] Record dataset release/version, source URL, preprocessing commit and checksums.
- [ ] Export a complete environment lock from the successful clean run.
- [ ] Add a one-command or one-cell clean-kernel reproduction path.
- [ ] Add conversation-cluster bootstrap sensitivity analysis if conversation IDs are available.
- [ ] Run the frozen feature pipeline on an independent benchmark.
- [ ] Add prespecified feature ablations.

## Environment capture

For each successful run, capture at minimum:
```bash
python --version
python -m pip freeze > requirements-lock.txt
```

Also record the operating system, CPU, accelerator, driver/runtime, notebook execution order, dataset identifiers and random seeds. A lock file should be generated from the actual successful environment; do not invent package versions from an unpinned requirements list.

## Reporting rule

Do not describe the current aggregate artifacts as a complete raw-data reproduction package. Do not claim independent generalization, causal feature attribution or end-to-end answer accuracy from evidence-recall results alone.
