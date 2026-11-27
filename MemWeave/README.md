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

## Research follow-up and Strategy C

The supplemental [research follow-up notebooks](notebooks/README.md#research-follow-up-notebooks-separate-from-the-canonical-sequence), [Stage B/C reconciliation](results/stage_bc_2026-11-26/README.md), [reader-QA reports](results/followup_2026/README.md), and [MFAR instrumentation design](docs/instrumentation/README.md) are now included in the repository through a selective integration branch. The [Strategy C milestone](docs/RESEARCH_MILESTONE_1.md) is a falsifiable research plan, not a novelty claim or completed new experiment. See the [related-work matrix](docs/RELATED_WORK_MATRIX.md) before making novelty statements.

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

### Browser atomic-evidence audit bridge

The static browser workspace exports a versioned question-level annotation file (`memweave-question-evidence-labels-v2`). It contains candidate IDs, manually labelled gold evidence IDs, and selected/retrieved IDs for each browser policy and budget. Import it with the Python package:

    memweave browser-audit --input /private/path/memweave-evidence-labels.json --output-dir results/browser_audit

The importer validates the export, recomputes retention recall and retrieval precision/recall/F1@5 from the ID sets, and writes derived JSON/CSV plus a SHA-256 manifest. The output intentionally omits evidence text; keep the input export private because it contains source excerpts.

For a matched multi-question diagnostic, export one JSON per distinct question
against the **same loaded conversation and candidate evidence units**. Put
only those exports in a dedicated folder, then pass the folder as `--input`:

    memweave browser-audit --input /private/path/question_exports --output-dir results/browser_batch

Batch mode requires identical candidate evidence, policy/budget rows, and
retention selections across exports. It reports per-policy/budget macro means,
deterministic question-level bootstrap 95% intervals, and paired metric deltas
against rank-only. The resampling unit is the question; intervals describe
only the annotated questions supplied, not a benchmark population. The batch
output omits question text and evidence excerpts.

This is an **atomic-evidence diagnostic**, not a LongMemEval run. The browser uses sentence/claim candidates and transparent heuristic policies; the primary research pipeline uses session-level LongMemEval candidates, its frozen feature schema, and a trained logistic-regression selector. Do not pool these metrics or claim the browser export evaluates the trained selector. Both stages share the retention-versus-retrieval metric distinction, while downstream answer quality remains a separate fixed-reader evaluation.


### Public web application

The GitHub Pages homepage is now the full research portal at [site/research.html](../site/research.html), documenting the algorithm families, experiment history, results, limitations, and an illustrative selection-mechanism explorer. The browser-local workspace is available separately at [site/workspace.html](../site/workspace.html); it supports transcript ingestion, a configurable word-count retention budget, inspectable heuristic retention, persistent local memory, intent-aware evidence retrieval, item deletion, and JSON backup/import. Conversation data stays in the visitor's browser and is not uploaded. This workspace remains an application baseline, not the trained research selector or a reproduction of reported experiments. GitHub Pages is static; the Python research package, API, and Streamlit dashboard run separately. See [the web app guide](WEB_APP_GUIDE.md) for scope and limitations.

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

The full raw benchmark JSONs are not stored as standalone files in this source tree. The previously committed `results/artifacts/2026-11-26/MemWeave_Research_Artifacts.zip` was withdrawn from the current `main` tree on 2026-11-27 because it contained cleartext LoCoMo-derived dialogue spans and other text-bearing outputs whose redistribution terms had not been cleared. A sanitized replacement has not yet been generated. The old ZIP remains present in earlier public Git history; deleting the current path does not erase historical commits or copies already downloaded. Do not redistribute that historical archive. See the [research archive content audit](docs/reproducibility/RESEARCH_ARCHIVE_CONTENT_AUDIT_2026-11-27.md). Keep raw or text-bearing benchmark material outside public Git unless dataset terms, attribution, privacy and size have been reviewed.

Distinguish evidence retention from answer accuracy, the original v2.3 experiment from the role-aware follow-up, and a held-out split from independent replication. The research process was iterative rather than preregistered. Do not claim that the six role-aware features have individually established causal effects.
