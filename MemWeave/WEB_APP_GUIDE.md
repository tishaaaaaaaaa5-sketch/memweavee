# MemWeave public website and application

## Live browser application

The GitHub Pages homepage is the MemWeave workspace:

https://tishaaaaaaaaa5-sketch.github.io/memweavee/

The research overview is available at:

https://tishaaaaaaaaa5-sketch.github.io/memweavee/research.html

The browser-local workspace supports:
- Paste a conversation transcript with `User:`, `Assistant:`, or similar speaker labels.
- Set a word-count memory budget and run a transparent heuristic evidence-retention pass.
- Inspect selected message units, roles, scoring reasons, and budget usage before saving.
- Keep a persistent memory store in browser localStorage.
- Search retained evidence by query terms and inspect matched source snippets.
- Delete individual memories, export a JSON backup, and import a prior backup.

## Data and research scope

This is a usable application prototype, not just a landing page. It runs entirely in the browser and does not send conversation data to a backend. Browser storage is local to the current browser profile and device; clearing site data or switching devices can remove or hide the saved workspace. Users should export backups they want to preserve.

The current retention logic is a deliberately transparent heuristic using speaker role, preference/goal language, questions, reasoning/decision cues, and message length. Retrieval is lexical query-term coverage with an exact-phrase bonus. These are application baselines, not the trained role-aware selector, not a model-generated answer system, and not a reproduction of the research evaluation. Scores are not calibrated confidence.

## GitHub Pages limits

GitHub Pages hosts static HTML, CSS, and JavaScript. It does not execute Python, FastAPI, SQLite, or other server-side processes. Therefore this public prototype provides local browser persistence, not shared cloud workspaces, server-side accounts, or cross-device synchronization.

## Optional FastAPI backend (local development)

The FastAPI workspace backend remains in `MemWeave/api/` for local development or future deployment to a Python-capable host.

Run locally from the repository root:

    python -m pip install -e "MemWeave[api]"
    uvicorn api.app:app --app-dir MemWeave --host 127.0.0.1 --port 8000

Open http://127.0.0.1:8000.

Set `MEMWEAVE_DB_PATH` to a persistent writable path before launch. The default is `MemWeave/data/memweave_app.sqlite3`.

## API endpoints

- `POST /workspaces` creates a workspace and returns a one-time workspace key.
- `GET /workspaces/{workspace_id}/memories` lists memories (requires `X-Workspace-Key`).
- `POST /workspaces/{workspace_id}/memories` creates a memory.
- `DELETE /workspaces/{workspace_id}/memories/{memory_id}` deletes a memory.
- `POST /workspaces/{workspace_id}/retrieve` performs lexical-overlap retrieval.
- `GET /health`, `/results/summary` and `/results/question-types` are research endpoints.

Before a public server deployment, add account-based authentication, key rotation, workspace export/deletion, abuse controls, HTTPS, managed persistent storage, backups, and operational monitoring.
