# Reproducibility audit

## Current state

The role-aware locked-test report records LongMemEval-S cleaned and the expected file name, but the exact dataset revision and SHA-256 for the evaluated file were not preserved in the supplied run outputs. The raw per-question export and audit manifest described by the notebook are also absent from the repository snapshot.

The repository supports inspection of the notebook and aggregate findings, but is not yet a complete end-to-end reproduction package.

## Committed artifact consistency check

From the repository root, run `python MemWeave/scripts/validate_release.py`. This checks internal agreement among the committed run manifest, paired audit JSON, and question-type aggregate CSV using only the Python standard library. A successful check does not rerun training/evaluation, recover missing per-question rows, verify the source dataset, or establish independent generalization. The current release is expected to warn that the dataset SHA-256 and privacy-safe per-question export are absent.

## Required additions for the next rerun

- [ ] Pin the LongMemEval dataset revision or immutable download URL.
- [ ] Save SHA-256 of the exact source dataset file before preprocessing.
- [ ] Record Python, OS, package versions, and a full dependency lock.
- [ ] Record preprocessing configuration and hash the processed dataset.
- [ ] Record git commit SHA, random seeds, feature schema, hyperparameters, and split IDs.
- [ ] Save a run manifest with exact commands and timestamps.
- [ ] Export per-example identifiers, ranks, recall values, and paired differences without conversation text or answers.
- [ ] Hash each result export and link it to source data and code commit.
- [ ] Provide a clean-kernel reproduction command or notebook sequence.
- [ ] Verify a clean rerun reproduces aggregate tables within a stated tolerance.

## Privacy and licensing

Do not commit raw conversation histories, answers, or session text merely to make the experiment reproducible. Use benchmark-provided access routes and publish only minimal derived audit data allowed by the dataset terms. Include license and attribution for every dataset.

## Claims

Until missing provenance and exports are restored, describe the result as an aggregate result documented by the saved notebook, not as a fully independently reproducible artifact. See [INDEPENDENT_VALIDATION_PLAN.md](INDEPENDENT_VALIDATION_PLAN.md).
