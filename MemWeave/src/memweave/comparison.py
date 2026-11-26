"""Pure helpers for comparing completed experiment runs from the local registry."""
from __future__ import annotations

import json
from typing import Any, Iterable


def compare_run_metrics(
    records: Iterable[dict[str, Any]],
    run_ids: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    """Flatten each selected run's compact main-results summary into comparable rows.

    A row is keyed by run, pool and method. Missing or malformed result summaries
    are skipped rather than guessed or reconstructed from unrelated artifacts.
    """
    selected = set(run_ids or [])
    rows: list[dict[str, Any]] = []
    for record in records:
        run_id = record.get("run_id")
        if selected and run_id not in selected:
            continue
        summary = record.get("summary") or {}
        metrics = summary.get("main_results", [])
        if not isinstance(metrics, list):
            continue
        for metric in metrics:
            if not isinstance(metric, dict) or "pool" not in metric or "method" not in metric:
                continue
            rows.append({
                **metric,
                "run_id": run_id,
                "created_at": record.get("created_at"),
                "primary_pool": summary.get("primary_pool"),
                "n_dev": summary.get("n_dev"),
                "n_test": summary.get("n_test"),
            })
    return rows


def _flatten_mapping(value: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    flattened: dict[str, Any] = {}
    for key, item in value.items():
        path = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(item, dict):
            flattened.update(_flatten_mapping(item, path))
        else:
            flattened[path] = item
    return flattened


def configuration_differences(
    records: Iterable[dict[str, Any]],
    run_ids: Iterable[str],
) -> list[dict[str, Any]]:
    """Return nested configuration paths whose values differ across selected runs."""
    wanted = list(dict.fromkeys(run_ids))
    by_id = {
        record.get("run_id"): record
        for record in records
        if record.get("run_id") in wanted
    }
    if len(by_id) < 2:
        return []

    flattened = {
        run_id: _flatten_mapping((by_id[run_id].get("config") or {}))
        for run_id in wanted if run_id in by_id
    }
    paths = sorted(set().union(*(values.keys() for values in flattened.values())))
    differences = []
    for path in paths:
        values = {
            run_id: flattened[run_id].get(path, "<missing>")
            for run_id in flattened
        }
        encoded = {
            json.dumps(value, sort_keys=True, default=str)
            for value in values.values()
        }
        if len(encoded) > 1:
            differences.append({"path": path, "values": values})
    return differences
