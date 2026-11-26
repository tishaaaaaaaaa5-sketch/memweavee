# MemWeave public website and application

## GitHub Pages website

The public research website is a static site in `MemWeave/web/`. A GitHub Actions workflow publishes this directory to GitHub Pages when changes reach the `main` branch.

To enable it in the repository:
1. Open **Settings → Pages**.
2. Under **Build and deployment**, choose **GitHub Actions** as the source.
3. Merge the website workflow to `main`.
4. Open the Pages URL shown in the repository's Pages settings.

The website uses relative asset paths so it works at the repository's GitHub Pages project URL.

## What GitHub Pages can and cannot run

GitHub Pages hosts static HTML, CSS, JavaScript, and other static assets. It does not run Python, FastAPI, SQLite, or other server-side application processes.

Accordingly, the Pages site is the public research/portfolio website. It does not provide live private workspaces, memory persistence, or API retrieval. The interactive workspace UI is not exposed on the static site.

## Application backend source

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

## Security and research scope

The workspace key is a bearer secret. Anyone who obtains it can access that workspace. Do not store sensitive personal information in this early preview. Before wider public launch, add account-based authentication, key rotation, workspace export/deletion, abuse controls, HTTPS, persistent managed storage and backups.

The public workspace retrieval baseline is deterministic lexical overlap. It returns matching source memories and matched terms; it does not call an LLM or generate answers, and it must not be described as the learned research model. Research results shown on the website are scoped to their source evaluations and limitations.
