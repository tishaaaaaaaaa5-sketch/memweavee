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

The evaluate command currently performs aggregate artifact validation using the committed manifest, paired audit JSON and question-type CSV. It checks internal consistency; it does not retrain a model, fetch benchmark data, or recreate missing per-question predictions.

## Dashboard

The serve command launches a read-only Streamlit dashboard over the committed role-aware aggregate results.

## API

Install optional API dependencies and run:

    uvicorn api.app:app --app-dir MemWeave --reload

Endpoints: GET /health, GET /results/summary, GET /results/question-types.

## Next integration step

The package currently contains shared metric helpers, safe YAML configuration loading, CLI orchestration, unit tests, CI, a dashboard and a read-only API. The research algorithms remain in canonical notebooks. The next substantive step is to extract the exact tested preprocessing, feature and retrieval pipeline into versioned modules, then add end-to-end tests against synthetic fixtures. Do not silently substitute a new implementation for the historical experimental pipeline.
