"""Read-only research results API plus isolated public memory workspaces."""
import csv
import json
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .memory_store import (
    DEFAULT_DB, add_memory, authenticate, create_workspace,
    delete_memory, initialize, list_memories, retrieve,
)

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "final_locked_test"
WEB = ROOT / "web"
DB_PATH = Path(os.environ.get("MEMWEAVE_DB_PATH", str(DEFAULT_DB))).expanduser()

app = FastAPI(
    title="MemWeave",
    version="0.2.0",
    description="Research evidence API and private workspace memory application.",
)

class MemoryInput(BaseModel):
    content: str = Field(min_length=1, max_length=8000)
    source: str = Field(default="manual", max_length=120)

class RetrievalInput(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    limit: int = Field(default=5, ge=1, le=20)

def require_workspace(workspace_id: str, workspace_key: str | None):
    if not authenticate(workspace_id, workspace_key or "", DB_PATH):
        raise HTTPException(status_code=401, detail="Invalid workspace credentials")

@app.on_event("startup")
def startup():
    initialize(DB_PATH)

@app.get("/health")
def health():
    return {"status": "ok", "service": "memweave"}

@app.post("/workspaces")
def new_workspace():
    return create_workspace(DB_PATH)

@app.get("/workspaces/{workspace_id}/memories")
def get_memories(workspace_id: str, x_workspace_key: str | None = Header(default=None)):
    require_workspace(workspace_id, x_workspace_key)
    return list_memories(workspace_id, db_path=DB_PATH)

@app.post("/workspaces/{workspace_id}/memories")
def post_memory(workspace_id: str, payload: MemoryInput,
                x_workspace_key: str | None = Header(default=None)):
    require_workspace(workspace_id, x_workspace_key)
    return add_memory(workspace_id, payload.content.strip(), payload.source.strip() or "manual", DB_PATH)

@app.delete("/workspaces/{workspace_id}/memories/{memory_id}")
def remove_memory(workspace_id: str, memory_id: str,
                  x_workspace_key: str | None = Header(default=None)):
    require_workspace(workspace_id, x_workspace_key)
    if not delete_memory(workspace_id, memory_id, DB_PATH):
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"deleted": True, "memory_id": memory_id}

@app.post("/workspaces/{workspace_id}/retrieve")
def retrieve_memories(workspace_id: str, payload: RetrievalInput,
                      x_workspace_key: str | None = Header(default=None)):
    require_workspace(workspace_id, x_workspace_key)
    return retrieve(workspace_id, payload.query, payload.limit, DB_PATH)

@app.get("/results/summary")
def summary():
    path = RESULTS / "paired_test_audit.json"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Committed audit artifact not found")
    audit = json.loads(path.read_text(encoding="utf-8"))
    return {"test_questions": audit.get("test_questions"),
            "test_metrics": audit.get("test_metrics", {}),
            "scope": "aggregate artifact access; no model execution"}

@app.get("/results/question-types")
def question_types():
    path = RESULTS / "question_type_breakdown.csv"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Question-type artifact not found")
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))

if WEB.is_dir():
    app.mount("/assets", StaticFiles(directory=WEB), name="assets")

    @app.get("/", include_in_schema=False)
    def website():
        return FileResponse(WEB / "index.html")
