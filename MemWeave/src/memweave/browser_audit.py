"""Import and score browser atomic-evidence annotation exports.

Single-question exports are descriptive diagnostics. Batch aggregation requires
matched candidate sets and identical retention selections across questions;
question-conditioned retrieval remains paired by policy and budget. These
browser atomic claims are not LongMemEval session candidates and do not
evaluate the trained logistic-regression selector.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from pathlib import Path
from typing import Any, Iterable

FORMAT = "memweave-question-evidence-labels-v2"
MAX_BYTES = 5 * 1024 * 1024
MAX_CANDIDATES = 5000
MAX_EVALUATIONS = 100
MAX_BATCH_FILES = 500
BOOTSTRAP_REPLICATES = 2000
METRICS = (
    "retention_precision",
    "retention_recall",
    "retention_f1",
    "retrieval_precision_at_5",
    "retrieval_recall_at_5",
    "retrieval_f1_at_5",
)


def _digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _stable_digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


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
    if not isinstance(evaluations, list) or not 1 <= len(evaluations) <= MAX_EVALUATIONS:
        raise ValueError(f"evaluations must contain 1..{MAX_EVALUATIONS} rows")

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
        if any(not isinstance(value, str) or value not in candidate_ids
               for value in selected + retrieved):
            raise ValueError("selected/retrieved IDs must refer to candidateEvidence")
        if len(selected) != len(set(selected)) or len(retrieved) != len(set(retrieved)):
            raise ValueError("selected/retrieved IDs must not contain duplicates")
        if not isinstance(budget, int) or isinstance(budget, bool) or not 1 <= budget <= 100:
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
            "selected_ids_sha256": _stable_digest(sorted(selected)),
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
        "candidate_set_sha256": _stable_digest(candidates),
        "gold_evidence_count": len(gold),
        "cost_unit": "browser word-count proxy",
        "input_sha256": _digest(source),
        "results": rows,
        "limitations": [
            "Atomic browser evidence units are not LongMemEval session candidates.",
            "Browser policy scores are heuristic; no trained LR model is evaluated here.",
            "Retention recall and retrieval recall are separate from downstream answer quality.",
            "Word-count proxy excludes exact tokenizer and full metadata costs.",
            "One annotation is descriptive; batch intervals quantify only variation across supplied questions.",
        ],
    }


def _percentile(sorted_values: list[float], probability: float) -> float:
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = (len(sorted_values) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(sorted_values) - 1)
    fraction = position - lower
    return sorted_values[lower] * (1 - fraction) + sorted_values[upper] * fraction


def _mean_ci(values: list[float], seed: int) -> dict[str, float | int]:
    if not values:
        raise ValueError("cannot aggregate an empty metric")
    mean = sum(values) / len(values)
    if len(values) == 1:
        return {"mean": mean, "ci95_low": mean, "ci95_high": mean, "n_questions": 1}
    rng = random.Random(seed)
    means = sorted(
        sum(rng.choice(values) for _ in values) / len(values)
        for _ in range(BOOTSTRAP_REPLICATES)
    )
    return {
        "mean": mean,
        "ci95_low": _percentile(means, 0.025),
        "ci95_high": _percentile(means, 0.975),
        "n_questions": len(values),
    }


def load_browser_audit_batch(paths: Iterable[str | Path]) -> dict[str, Any]:
    """Aggregate matched per-question exports with deterministic question bootstrap CIs."""
    files = sorted({Path(path).expanduser().resolve() for path in paths})
    if not files:
        raise ValueError("no browser audit JSON files were supplied")
    if len(files) > MAX_BATCH_FILES:
        raise ValueError(f"batch exceeds the {MAX_BATCH_FILES}-file limit")
    audits = [load_browser_audit(path) for path in files]
    if len({audit["input_sha256"] for audit in audits}) != len(audits):
        raise ValueError("the same annotation export was supplied more than once")
    if len({audit["question"].strip() for audit in audits}) != len(audits):
        raise ValueError("batch question texts must be unique")
    candidate_signatures = {audit["candidate_set_sha256"] for audit in audits}
    if len(candidate_signatures) != 1:
        raise ValueError(
            "matched batch requires the exact same candidate evidence set in every export"
        )

    lookup = []
    reference_keys = {(row["budget_percent"], row["policy"]) for row in audits[0]["results"]}
    for audit in audits:
        current_keys = {(row["budget_percent"], row["policy"]) for row in audit["results"]}
        if current_keys != reference_keys:
            raise ValueError("every question must contain the same policy/budget comparisons")
        lookup.append({
            (row["budget_percent"], row["policy"]): row for row in audit["results"]
        })

    for key in reference_keys:
        rows = [item[key] for item in lookup]
        signatures = {
            (row["selected_ids_sha256"], row["lambda"], row["solver"],
             row["word_proxy_cap"], row["word_proxy_used"])
            for row in rows
        }
        if len(signatures) != 1:
            raise ValueError(
                f"retention selections/configuration are not matched for budget/policy {key}"
            )

    aggregated = []
    for key in sorted(reference_keys):
        question_rows = [item[key] for item in lookup]
        metrics = {}
        for metric_index, metric in enumerate(METRICS):
            values = [float(row[metric]) for row in question_rows]
            metrics[metric] = _mean_ci(values, seed=1729 + key[0] * 101 + metric_index)
        first = question_rows[0]
        aggregated.append({
            "budget_percent": key[0],
            "policy": key[1],
            "lambda": first["lambda"],
            "solver": first["solver"],
            "word_proxy_used": first["word_proxy_used"],
            "word_proxy_cap": first["word_proxy_cap"],
            "selected_count": first["selected_count"],
            "metrics": metrics,
        })

    by_key = {(row["budget_percent"], row["policy"]): row for row in aggregated}
    paired = []
    policies = sorted({policy for _, policy in reference_keys})
    for budget in sorted({budget for budget, _ in reference_keys}):
        baseline_key = (budget, "rank")
        if baseline_key not in by_key:
            continue
        for policy in policies:
            if policy == "rank" or (budget, policy) not in by_key:
                continue
            left = lookup
            comparison = {"budget_percent": budget, "policy": policy, "baseline": "rank"}
            comparison["deltas"] = {}
            for metric_index, metric in enumerate(
                ("retention_recall", "retrieval_recall_at_5", "retrieval_f1_at_5")
            ):
                deltas = [
                    float(item[(budget, policy)][metric])
                    - float(item[baseline_key][metric])
                    for item in left
                ]
                comparison["deltas"][metric] = _mean_ci(
                    deltas, seed=9187 + budget * 97 + metric_index
                )
            paired.append(comparison)

    return {
        "format": "memweave-browser-atomic-batch-v1",
        "task_type": "matched_multi_question_browser_atomic_diagnostic",
        "question_count": len(audits),
        "candidate_count": audits[0]["candidate_count"],
        "candidate_set_sha256": next(iter(candidate_signatures)),
        "input_sha256": {path.name: _digest(path) for path in files},
        "bootstrap": {
            "method": "question-level nonparametric percentile bootstrap of the macro mean",
            "replicates": BOOTSTRAP_REPLICATES,
            "confidence_level": 0.95,
            "seed_rule": "fixed deterministic seeds by budget and metric",
            "unit": "question",
        },
        "results": aggregated,
        "paired_deltas_vs_rank": paired,
        "limitations": [
            "Confidence intervals describe only the supplied annotated questions, not a benchmark population.",
            "All exports must share the exact candidate evidence set and retention selections.",
            "Atomic browser claims are not LongMemEval session candidates.",
            "Browser policies are heuristics; the trained logistic-regression selector is not evaluated.",
            "Downstream answer quality requires a separate fixed-reader evaluation.",
            "Word-count proxy excludes exact tokenizer and full metadata costs.",
        ],
    }


def write_browser_audit(payload: dict[str, Any], output_dir: str | Path) -> Path:
    """Write privacy-minimised single-question JSON/CSV and a SHA-256 manifest."""
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
        files[path.name] = {"sha256": _digest(path), "bytes": path.stat().st_size}
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


def write_browser_audit_batch(payload: dict[str, Any], output_dir: str | Path) -> Path:
    """Write multi-question aggregate JSON/CSV and an input/output hash manifest."""
    target = Path(output_dir).expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)
    json_path = target / "browser_atomic_batch.json"
    csv_path = target / "browser_atomic_batch.csv"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    flat_rows = []
    for result in payload["results"]:
        row = {key: value for key, value in result.items() if key != "metrics"}
        for metric, summary in result["metrics"].items():
            for field, value in summary.items():
                row[f"{metric}_{field}"] = value
        flat_rows.append(row)
    for comparison in payload["paired_deltas_vs_rank"]:
        for metric, summary in comparison["deltas"].items():
            row = {
                "budget_percent": comparison["budget_percent"],
                "policy": comparison["policy"],
                "baseline": comparison["baseline"],
                "metric": metric,
                **{f"delta_{key}": value for key, value in summary.items()},
            }
            flat_rows.append(row)
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        if flat_rows:
            fields = list(dict.fromkeys(key for row in flat_rows for key in row))
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(flat_rows)
    files = {}
    for path in (json_path, csv_path):
        files[path.name] = {"sha256": _digest(path), "bytes": path.stat().st_size}
    manifest = {
        "manifest_version": 1,
        "input_sha256": payload["input_sha256"],
        "files": files,
        "note": "Aggregate metrics only; question text and raw evidence are not copied.",
    }
    (target / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import MemWeave browser atomic-evidence audits")
    parser.add_argument("--input", required=True, help="One private v2 JSON export or a folder of exports")
    parser.add_argument("--output-dir", required=True, help="Directory for derived JSON/CSV and manifest")
    args = parser.parse_args(argv)
    source = Path(args.input).expanduser().resolve()
    if source.is_dir():
        paths = sorted(source.glob("*.json"))
        payload = load_browser_audit_batch(paths)
        output = write_browser_audit_batch(payload, args.output_dir)
        print(
            f"Aggregated {payload['question_count']} matched questions over "
            f"{len(payload['results'])} policy/budget rows."
        )
        print("Reported macro means, question-bootstrap 95% CIs and paired deltas vs rank-only.")
    else:
        payload = load_browser_audit(source)
        output = write_browser_audit(payload, args.output_dir)
        print(
            f"Validated {payload['candidate_count']} atomic candidates and "
            f"{len(payload['results'])} policy/budget rows."
        )
        print("Recomputed retention recall and retrieval P/R/F1@5 from exported IDs.")
    print("This is an atomic-evidence diagnostic, not a LongMemEval or answer-quality result.")
    print(f"Artifacts: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
