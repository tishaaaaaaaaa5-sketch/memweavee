"""End-to-end orchestration and reproducible artifact writing.

This runner executes the extracted LongMemEval pipeline from caller-supplied
local benchmark files. It never downloads data and keeps tuning on dev IDs only.
"""
from __future__ import annotations

import hashlib
import json
import platform
import uuid
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import sklearn

from .data import load_json, prepare_longmemeval
from .downstream import evaluate_downstream_proxy
from .evaluation import run_locked_evaluation
from .experiment import build_question_pools, locked_split, POOLS
from .modeling import make_folds
from .tuning import tune_pool
from .robustness import evaluate_split_robustness
from .transfer import build_locomo_conversations, evaluate_locomo_transfer


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_default(value):
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (set, tuple)):
        return list(value)
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"cannot JSON-serialize {type(value).__name__}")


def write_artifacts(output_dir: str | Path, tables: dict[str, pd.DataFrame],
                    payload: dict[str, Any]) -> dict[str, Any]:
    """Write CSV/JSON/text outputs and a SHA-256 manifest for every artifact."""
    target = Path(output_dir).expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)
    written = []
    for name, table in tables.items():
        filename = f"{name}.csv"
        table.to_csv(target / filename, index=False)
        written.append(filename)

    (target / "run_config.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=_json_default) + "\n",
        encoding="utf-8",
    )
    written.append("run_config.json")

    findings = [
        "MemWeave extracted-pipeline run",
        f"Primary pool: {payload['settings']['primary_pool']}",
        f"Development questions: {payload['split']['n_dev']}",
        f"Locked-test questions: {payload['split']['n_test']}",
        "",
        "Interpretation limits:",
        "- Evidence recall measures retention of labelled evidence sessions.",
        "- The downstream answer-in-context measure is a literal string proxy, not LLM QA accuracy.",
        "- Robustness split test halves overlap and are not independent replications.",
        "- This run does not establish parity with the canonical notebook unless separately compared.",
        "",
        "See the CSV tables and run_config.json for numerical results and provenance.",
    ]
    (target / "findings.txt").write_text("\n".join(findings) + "\n", encoding="utf-8")
    written.append("findings.txt")

    manifest = {
        "manifest_version": 1,
        "files": {
            name: {"sha256": _sha256(target / name), "bytes": (target / name).stat().st_size}
            for name in sorted(written)
        },
    }
    (target / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {"output_dir": str(target), "manifest": manifest}


def run_pipeline(config: dict[str, Any]) -> dict[str, Any]:
    """Run ingestion -> pools -> dev tuning -> locked test -> secondary analyses."""
    pipeline = config.get("pipeline", {})
    evaluation = config.get("evaluation", {})
    if not isinstance(pipeline, dict) or not isinstance(evaluation, dict):
        raise ValueError("'pipeline' and 'evaluation' must be YAML mappings")

    data_path = Path(pipeline.get("longmemeval_path", "")).expanduser()
    if not str(data_path) or not data_path.is_file():
        raise FileNotFoundError(
            "Set pipeline.longmemeval_path to a local LongMemEval JSON file; "
            "benchmark data is never downloaded automatically."
        )
    output_dir = Path(pipeline.get("output_dir", "results/pipeline_run")).expanduser()
    if not output_dir.is_absolute():
        output_dir = Path.cwd() / output_dir

    raw = load_json(data_path, max_questions=pipeline.get("max_questions"))
    prepared = prepare_longmemeval(raw, batch_size=int(pipeline.get("batch_size", 400)))
    pools = build_question_pools(
        prepared["questions"], prepared["sessions"], prepared["X"]
    )
    split = locked_split(
        pools, prepared["questions"],
        test_fraction=float(pipeline.get("test_fraction", 0.5)),
        seed=int(pipeline.get("split_seed", 2026)),
    )
    dev_ids, test_ids = split["dev"], split["test"]
    folds = make_folds(
        dev_ids, folds=int(pipeline.get("cv_folds", 5)),
        seed=int(pipeline.get("cv_seed", 2026)),
    )

    tuning_results = {}
    tuned, best_simple = {}, {}
    tuning_rows = []
    for pool in POOLS:
        result = tune_pool(
            pools, prepared["questions"], pool, dev_ids, folds,
            C_grid=tuple(pipeline.get("C_grid", [0.03, 0.3, 3.0])),
            budget=float(evaluation.get("budget", 0.10)),
        )
        tuning_results[pool] = result
        tuned[pool] = result["config"]
        best_simple[pool] = result["best_simple"]
        tuning_rows.extend(
            {"pool": row[0], "stage": row[1], "parameter": row[2],
             "score": row[3], "standard_error": row[4]}
            for row in result["tune_rows"]
        )

    locked = run_locked_evaluation(
        pools, prepared["questions"], dev_ids, test_ids, tuned, best_simple,
        primary_pool=evaluation.get("primary_pool", "same_pipeline"),
        budget=float(evaluation.get("budget", 0.10)),
        budget_sweep=tuple(evaluation.get("budget_sweep", [0.05, 0.10, 0.20, 0.30])),
        random_reps=int(evaluation.get("random_reps", 50)),
        random_seed=int(evaluation.get("random_seed", 0)),
        bootstrap_resamples=int(evaluation.get("bootstrap_resamples", 4000)),
        bootstrap_seed=int(evaluation.get("bootstrap_seed", 1)),
        equivalence_margin=float(evaluation.get("equivalence_margin", 0.03)),
        alpha=float(evaluation.get("alpha", 0.05)),
    )

    downstream_summaries, downstream_pairs = [], []
    for pool in POOLS:
        selected = locked["selections"][pool]
        method_selections = {
            "LR (tuned)": selected["lr"],
            "random": selected["random"],
            "recency": selected["simple"]["recency"],
            "best simple (dev-chosen)": selected["simple"][best_simple[pool]],
            "full_history (ceiling)": {
                q: np.arange(len(pools[pool][q]["h"])) for q in test_ids
            },
        }
        result = evaluate_downstream_proxy(
            pools, prepared["questions"], prepared["X"], prepared["X_questions"],
            prepared["sessions"]["text"], test_ids, method_selections,
            pool=pool, topk=int(evaluation.get("downstream_topk", 3)),
            primary_method="LR (tuned)",
            bootstrap_resamples=int(evaluation.get("bootstrap_resamples", 4000)),
            bootstrap_seed=int(evaluation.get("bootstrap_seed", 1)) + 100,
        )
        downstream_summaries.append(result["summary"])
        downstream_pairs.append(result["paired_comparisons"])

    robustness = pd.DataFrame()
    robustness_seeds = pipeline.get("robustness_seeds", [])
    if robustness_seeds:
        robustness = evaluate_split_robustness(
            pools, prepared["questions"], split["valid"],
            primary_pool=evaluation.get("primary_pool", "same_pipeline"),
            seeds=robustness_seeds,
            test_fraction=float(pipeline.get("test_fraction", 0.5)),
            folds=int(pipeline.get("cv_folds", 5)),
            C_grid=tuple(pipeline.get("C_grid", [0.03, 0.3, 3.0])),
            budget=float(evaluation.get("budget", 0.10)),
            bootstrap_resamples=int(evaluation.get("bootstrap_resamples", 4000)),
            bootstrap_seed=int(evaluation.get("bootstrap_seed", 1)),
        )

    transfer_comparisons = pd.DataFrame()
    transfer_meta = {"requested": bool(pipeline.get("locomo_path")), "executed": False}
    locomo_path = pipeline.get("locomo_path")
    if locomo_path:
        path = Path(locomo_path).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"LoCoMo file not found: {path}")
        locomo_raw = load_json(path)
        conversations = build_locomo_conversations(
            locomo_raw, prepared["hashing_vectorizer"], prepared["tfidf_transformer"]
        )
        transfer = evaluate_locomo_transfer(
            pools, prepared["questions"], split["valid"], conversations,
            tuned[evaluation.get("primary_pool", "same_pipeline")],
            pool=evaluation.get("primary_pool", "same_pipeline"),
            budget=float(evaluation.get("budget", 0.10)),
            random_reps=int(evaluation.get("random_reps", 50)),
            seed=int(evaluation.get("random_seed", 0)),
            bootstrap_resamples=int(evaluation.get("bootstrap_resamples", 4000)),
        )
        transfer_comparisons = transfer["comparisons"]
        transfer_meta = {
            "requested": True, "executed": True,
            "n_conversations": transfer["n_conversations"],
            "n_questions_with_evidence": transfer["n_questions_with_evidence"],
            "minimum_detectable_difference": transfer["minimum_detectable_difference"],
            "input_sha256": _sha256(path.resolve()),
        }

    question_types = pd.DataFrame([
        {"question_id": prepared["questions"][q]["qid"],
         "question_type": prepared["questions"][q]["qtype"],
         "split": "dev" if q in set(dev_ids) else "locked_test"}
        for q in split["valid"]
    ])
    tables = {
        "main_results": locked["main_results"],
        "paired_comparisons": locked["comparisons"],
        "group_ablation": locked["group_ablation"],
        "mechanism_test": locked["mechanism_test"],
        "budget_sweep": locked["budget_sweep"],
        "downstream_proxy": pd.concat(downstream_summaries, ignore_index=True),
        "downstream_paired": pd.concat(downstream_pairs, ignore_index=True),
        "tuning_dev_only": pd.DataFrame(tuning_rows),
        "question_splits": question_types,
        "robustness_overlapping_splits": robustness,
        "locomo_transfer": transfer_comparisons,
    }
    run_id = uuid.uuid4().hex
    payload = {
        "run_id": run_id,
        "run": {
            "python": platform.python_version(), "numpy": np.__version__,
            "pandas": pd.__version__, "scikit_learn": sklearn.__version__,
            "longmemeval_input": str(data_path.resolve()),
            "longmemeval_sha256": _sha256(data_path.resolve()),
            "n_raw_questions": len(raw),
            "n_deduplicated_sessions": len(prepared["sessions"]["text"]),
        },
        "settings": {
            "primary_pool": evaluation.get("primary_pool", "same_pipeline"),
            "budget": float(evaluation.get("budget", 0.10)),
            "split_seed": int(pipeline.get("split_seed", 2026)),
            "cv_seed": int(pipeline.get("cv_seed", 2026)),
            "cv_folds": int(pipeline.get("cv_folds", 5)),
            "C_grid": list(pipeline.get("C_grid", [0.03, 0.3, 3.0])),
            "robustness_seeds": robustness_seeds,
            "downstream_topk": int(evaluation.get("downstream_topk", 3)),
        },
        "split": {
            "n_valid": len(split["valid"]), "n_dev": len(dev_ids),
            "n_test": len(test_ids), "dev_ids": dev_ids, "test_ids": test_ids,
        },
        "tuned_dev_only": tuned,
        "best_simple_dev_only": best_simple,
        "locomo": transfer_meta,
        "limitations": [
            "No automatic dataset download.",
            "No full parity claim without comparison to a saved canonical notebook run.",
            "Downstream answer-in-context is a string-match proxy, not reader-model QA accuracy.",
            "Alternative split test halves overlap and are descriptive, not independent replications.",
        ],
    }
    artifact_result = write_artifacts(output_dir, tables, payload)
    registry_path = Path(
        pipeline.get("registry_path", str(output_dir.parent / "run_registry.sqlite3"))
    ).expanduser()
    if not registry_path.is_absolute():
        registry_path = Path.cwd() / registry_path
    from .registry import RunRegistry

    registry = RunRegistry(registry_path)
    manifest_path = Path(artifact_result["output_dir"]) / "manifest.json"
    registry_record = registry.record(
        run_id=run_id,
        output_dir=artifact_result["output_dir"],
        manifest_sha256=_sha256(manifest_path),
        input_sha256=payload["run"]["longmemeval_sha256"],
        config=config,
        summary={
            "primary_pool": payload["settings"]["primary_pool"],
            "n_valid": payload["split"]["n_valid"],
            "n_dev": payload["split"]["n_dev"],
            "n_test": payload["split"]["n_test"],
            "main_results": locked["main_results"].to_dict(orient="records"),
        },
    )
    return {
        "tables": tables,
        "payload": payload,
        "artifacts": artifact_result,
        "registry": {"path": str(registry_path.resolve()), "run": registry_record},
    }
