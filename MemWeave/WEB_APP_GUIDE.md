# MemWeave public web application

## What this adds
- Responsive dark research website with project overview, architecture and scoped results.
- Public visitors can create isolated private workspaces.
- Workspace users can add, list, delete and search memory notes.
- Workspace keys are high-entropy bearer credentials returned once and stored in that browser.
- Retrieval is deterministic lexical overlap. It returns matching source memories and matched terms; it does not call an LLM or generate answers.
- Existing research aggregate endpoints remain read-only and separate from workspace data.

## Run locally
From the repository root:
    python -m pip install -e "MemWeave[api]"
    uvicorn api.app:app --app-dir MemWeave --host 0.0.0.0 --port 8000
Open http://localhost:8000.

Set MEMWEAVE_DB_PATH to a persistent writable path before launch. The default is MemWeave/data/memweave_app.sqlite3.

## API
- POST /workspaces creates a workspace and returns a one-time workspace key.
- GET /workspaces/{workspace_id}/memories lists memories (requires X-Workspace-Key).
- POST /workspaces/{workspace_id}/memories creates a memory.
- DELETE /workspaces/{workspace_id}/memories/{memory_id} deletes a memory.
- POST /workspaces/{workspace_id}/retrieve performs lexical-overlap retrieval.
- GET /health, /results/summary and /results/question-types are research endpoints.

## Security and deployment
The workspace key is a bearer secret: anyone who obtains it can access that workspace. The browser stores it in local storage; clearing browser storage loses the key. Do not store secrets or sensitive personal data in this early preview. Use HTTPS, configure persistent storage for SQLite, back up the database, and set request-size limits at the hosting layer. Before a wider public launch, add account-based authentication, key rotation, workspace export/deletion, abuse controls and managed PostgreSQL.

The public retrieval baseline is intentionally transparent and must not be described as the learned research model. Research results shown on the website are scoped to their source evaluations and limitations.
