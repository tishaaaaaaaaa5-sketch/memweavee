"""Import and score browser atomic-evidence annotation exports.

This diagnostic is intentionally separate from the session-level LongMemEval
pipeline: browser units are atomic claims, and their labels are not LongMemEval
gold session labels. The importer recomputes metrics from exported ID sets and
never treats browser heuristic scores as trained-model predictions.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

FORMAT = "memweave-question-evidence-labels-v2"
MAX_BYTES = 5 * 1024 * 1024
MAX_CANDIDATES = 5000
MAX_EVALUATIONS = 100


def _digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _metric(selected: list[str], gold: set[str]) -> dict[str, float]:
    hits = len(set(selected) & gold)
    precision = hits / len(selected) if selected else 0.0
    recall = hits / len(gold) if gold else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


def load_browser_audit(path: str | Path) -> dict[str, Any]:
    """Validate one v2 browser export and recompute retention/retrieval metrics."""
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Browser audit export not found: {source}")
    if source.stat().st_size > MAX_BYTES:
        raise ValueError(f"Browser audit export exceeds {MAX_BYTES} bytes")
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("format") != FORMAT:
        raise ValueError(f"Expected browser audit format {FORMAT!r}")
    question = payload.get("question")
    candidates = payload.get("candidateEvidence")
    relevant_ids = payload.get("relevantEvidenceIds")
    evaluations = payload.get("evaluations")
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question must be a non-empty string")
    if not isinstance(candidates, list) or not 1 <= len(candidates) <= MAX_CANDIDATES:
        raise ValueError(f"candidateEvidence must contain 1..{MAX_CANDIDATES} units")
    if not isinstance(relevant_ids, list) or not relevant_ids:
        raise ValueError("relevantEvidenceIds must contain at least one labelled ID")
    if not isinstance(evaluations, list) or not 1 <= len(evaluations) <= MAX_EVALUATIONS:
        raise ValueError(f"evaluations must contain 1..{MAX_EVALUATIONS} rows")

    ids = []
    for item in candidates:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"]:
            raise ValueError("every candidate must have a non-empty string id")
        if not isinstance(item.get("text"), str) or not item["text"].strip():
            raise ValueError("every candidate must contain non-empty text")
        ids.append(item["id"])
    if len(ids) != len(set(ids)):
        raise ValueError("candidate IDs must be unique")
    candidate_ids = set(ids)
    gold = set(relevant_ids)
    if len(gold) != len(relevant_ids) or not gold or not gold <= candidate_ids:
        raise ValueError("relevantEvidenceIds must be unique IDs from candidateEvidence")

    rows = []
    seen_keys = set()
    for entry in evaluations:
        if not isinstance(entry, dict):
            raise ValueError("each evaluation must be an object")
        selected = entry.get("selectedIds")
        retrieved = entry.get("retrievalIds")
        budget = entry.get("budgetPercent")
        policy = entry.get("policy")
        if not isinstance(selected, list) or not isinstance(retrieved, list):
            raise ValueError("selectedIds and retrievalIds must be lists")
        if any(value not in candidate_ids for value in selected + retrieved):
            raise ValueError("selected/retrieved IDs must refer to candidateEvidence")
        if len(selected) != len(set(selected)) or len(retrieved) != len(set(retrieved)):
            raise ValueError("selected/retrieved IDs must not contain duplicates")
        if not isinstance(budget, int) or not 1 <= budget <= 100:
            raise ValueError("budgetPercent must be an integer from 1 to 100")
        if not isinstance(policy, str) or not policy:
            raise ValueError("policy must be a non-empty string")
        key = (budget, policy)
        if key in seen_keys:
            raise ValueError("duplicate policy/budget evaluation")
        seen_keys.add(key)
        retained = _metric(selected, gold)
        retrieved_metrics = _metric(retrieved[:5], gold)
        rows.append({
            "budget_percent": budget,
            "policy": policy,
            "lambda": float(entry.get("lambda", 0.0)),
            "solver": str(entry.get("solver", "unspecified")),
            "selected_count": len(selected),
            "retrieved_count_at_5": len(retrieved[:5]),
            "word_proxy_used": int(entry.get("usedCost", 0)),
            "word_proxy_cap": int(entry.get("budgetCap", 0)),
            "retention_precision": retained["precision"],
            "retention_recall": retained["recall"],
            "retention_f1": retained["f1"],
            "retrieval_precision_at_5": retrieved_metrics["precision"],
            "retrieval_recall_at_5": retrieved_metrics["recall"],
            "retrieval_f1_at_5": retrieved_metrics["f1"],
        })
    rows.sort(key=lambda row: (row["budget_percent"], row["policy"]))
    return {
        "format": FORMAT,
        "task_type": "browser_atomic_evidence_diagnostic",
        "question": question,
        "source": str(payload.get("source", "")),
        "annotated_at": str(payload.get("annotatedAt", "")),
        "candidate_count": len(candidates),
        "gold_evidence_count": len(gold),
        "cost_unit": "browser word-count proxy",
        "input_sha256": _digest(source),
        "results": rows,
        "limitations": [
            "Atomic browser evidence units are not LongMemEval session candidates.",
            "Browser policy scores are heuristic; no trained LR model is evaluated here.",
            "Retention recall and retrieval recall are separate from downstream answer quality.",
            "Word-count proxy excludes exact tokenizer and full metadata costs.",
            "This single-question annotation is descriptive, not a benchmark estimate.",
        ],
    }


def write_browser_audit(payload: dict[str, Any], output_dir: str | Path) -> Path:
    """Write privacy-minimised JSON/CSV results and a SHA-256 manifest."""
    target = Path(output_dir).expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)
    json_path = target / "browser_atomic_audit.json"
    csv_path = target / "browser_atomic_audit.csv"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    rows = payload["results"]
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]) if rows else [])
        if rows:
            writer.writeheader()
            writer.writerows(rows)
    files = {}
    for path in (json_path, csv_path):
        files[path.name] = {
            "sha256": _digest(path),
            "bytes": path.stat().st_size,
        }
    manifest = {
        "manifest_version": 1,
        "input_sha256": payload["input_sha256"],
        "files": files,
        "note": "Derived metrics only; raw candidate text is not copied to output.",
    }
    (target / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import a MemWeave browser atomic-evidence audit")
    parser.add_argument("--input", required=True, help="Private JSON export from the browser workspace")
    parser.add_argument("--output-dir", required=True, help="Directory for derived JSON/CSV and manifest")
    args = parser.parse_args(argv)
    payload = load_browser_audit(args.input)
    output = write_browser_audit(payload, args.output_dir)
    print(f"Validated {payload['candidate_count']} atomic candidates and {len(payload['results'])} policy/budget rows.")
    print(f"Gold evidence units: {payload['gold_evidence_count']}")
    print("Retention recall and retrieval P/R/F1@5 were recomputed from exported IDs.")
    print("No LongMemEval result or downstream answer-quality score was generated.")
    print(f"Artifacts: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
