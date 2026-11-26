# MemWeave research project

MemWeave investigates how to retain useful conversational sessions under a constrained memory budget. The repository contains two related but distinct research stages: the original query-agnostic retention study (v2.0–v2.3) and a later role-aware feature experiment evaluated on a held-out test split.

## Research stages

### Stage A — Original retention study (v2.0–v2.3)

- Benchmark: LongMemEval-S cleaned, 500 questions in the reported study.
- Primary task: query-agnostic session retention.
- Primary metric: session-level evidence recall.
- The v2.3 corrected-inference addendum found a small, sensitivity-dependent advantage over the strongest simple rule. Read [the findings](results/findings_v2_3.txt); do not describe that result as robust superiority.
- External LoCoMo and downstream QA-proxy results are reported separately and have their own limitations.

### Stage B — Role-aware follow-up (final locked-test audit)

- Pool: same_pipeline.
- Split: 235 DEV / 235 locked TEST questions; abstention questions excluded.
- Model: logistic regression, C = 0.3.
- Comparison: baseline feature set vs. baseline plus six message-role-aware features.
- Budget: 10% of pool word count (a proxy, not exact tokenization).
- Held-out budgeted evidence recall: 0.4042 baseline vs. 0.7094 role-aware (+0.3052).
- Paired bootstrap 95% CI: [0.252979, 0.359574].
- Exact paired sign test: p = 5.11e-25; sign-flip Monte Carlo p = 5e-6 at 200,000 permutations.
- OOF reconstruction was exact for both variants before locked-test scoring.

The follow-up result is not a replacement for the v2.3 result: it is a separate feature experiment and evaluation. See [the final locked-test report](results/final_locked_test/README.md).

## Research software platform

MemWeave now includes an installable Python package, command-line interface, YAML experiment configuration, unit tests, CI workflow, read-only results API, and Streamlit research dashboard.

Install from the repository root:

    python -m pip install -e "MemWeave[dev,dashboard,api]"

Run the committed aggregate-artifact audit:

    memweave evaluate --config MemWeave/configs/role_aware.yaml

Run tests and launch the dashboard:

    pytest MemWeave/tests
    memweave serve

The current CLI evaluate mode validates the consistency of committed aggregate artifacts. It does not retrain the model, fetch benchmark data, or recreate missing per-question predictions. See the [platform guide](PLATFORM_GUIDE.md) for exact scope and API endpoints.

## Canonical notebook sequence

See the [notebook index](notebooks/README.md).

1. notebooks/00_MemWeave_2_0.ipynb — initial real-data pipeline.
2. notebooks/01_MemWeave_2_1.ipynb — fair-baseline and benchmark-structure audit.
3. notebooks/02_MemWeave_2_2.ipynb — revised tuning, inference, external and QA analyses.
4. notebooks/03_memweave_v2_3_addendum.ipynb — corrected inference and evidence-limit addendum.
5. notebooks/04_MemWeave_Final.ipynb — leak-controlled final evaluation workflow and role-aware follow-up audit cells.

## Reproduction

Before attempting a full rerun, check the committed aggregate artifacts with:

    python MemWeave/scripts/validate_release.py

This standard-library validator checks internal consistency across the run manifest, paired audit JSON, and question-type CSV. A pass is not a model rerun or independent replication; the current dataset checksum and per-question export are still missing. See the [reproducibility utilities](scripts/README.md) and [reproducibility audit](docs/reproducibility/REPRODUCIBILITY_AUDIT.md).

For a full rerun, use a clean kernel and preserve exact notebook version and outputs, dataset names and SHA-256 checksums, Python and package versions, split seed, model parameters, per-question result CSVs and statistical audit outputs.

The final role-aware audit uses 50,000 question-level paired bootstrap resamples and 200,000 sign-flip permutations. Its question-level inference is not conversation-clustered.

## Data and reporting guidance

The full raw benchmark JSONs are not stored as standalone files in this source tree. However, the archived bundle at `results/artifacts/2026-11-26/MemWeave_Research_Artifacts.zip` does contain per-question exports and cleartext LoCoMo-derived selected spans in `locomo_reader_qa_evidence_span_flan_t5_base/evidence_span_selections.csv`; it must not be described as a privacy-safe export. Its ZIP and per-file manifest integrity have been checked, but that does not clear privacy or redistribution rights. Review the [research archive content audit](docs/reproducibility/RESEARCH_ARCHIVE_CONTENT_AUDIT_2026-11-27.md) before redistributing it. Keep raw or text-bearing benchmark material outside public Git unless the relevant dataset terms, attribution, privacy and size have been reviewed.

Distinguish evidence retention from answer accuracy, the original v2.3 experiment from the role-aware follow-up, and a held-out split from independent replication. The research process was iterative rather than preregistered. Do not claim that the six role-aware features have individually established causal effects.
