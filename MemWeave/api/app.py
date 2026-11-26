"""Optional read-only HTTP API for committed aggregate results."""
import csv
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "final_locked_test"
app = FastAPI(title="MemWeave Research API", version="0.1.0",
              description="Read-only access to committed aggregate evidence-retention results.")

@app.get("/health")
def health():
    return {"status": "ok", "service": "memweave-research-api"}

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
