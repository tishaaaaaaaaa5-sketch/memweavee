#!/usr/bin/env python3
"""Privacy-minimised runtime event ledger for real MemWeave notebook executions.

This module records only events explicitly emitted by instrumented code. It does
not create placeholder events, infer MFAR labels, or alter memory decisions.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

EVENT_TYPES = {
    "source_observed",
    "candidate_constructed",
    "candidate_pool_built",
    "retention_selected",
    "ranking_metric_computed",
    "qa_evidence_assembled",
    "answer_generated",
}

# Only these metadata keys are accepted. Values must be JSON scalar/list data;
# raw text fields are deliberately not part of the contract.
METADATA_KEYS = {
    "candidate_count",
    "selected_count",
    "retrieved_count",
    "rank",
    "top_k",
    "budget",
    "used_cost",
    "cost_unit",
    "tokenizer",
    "selection_method",
    "config_sha256",
    "model_id",
    "model_revision",
    "generation_config_sha256",
    "latency_ms",
    "input_token_count",
    "output_token_count",
    "evaluation_correct",
    "evaluation_metric",
    "evaluation_value",
    "seed",
    "fold",
    "budget_fraction",
    "stage_note",
}


def sha256_text(value: str) -> str:
    """Hash exact UTF-8 text without retaining the text itself."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _safe_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    if metadata is None:
        return {}
    unknown = set(metadata) - METADATA_KEYS
    if unknown:
        raise ValueError(f"metadata keys are not allowed: {sorted(unknown)}")
    safe: dict[str, Any] = {}
    for key, value in metadata.items():
        if value is None or isinstance(value, (str, int, float, bool)):
            safe[key] = value
        elif isinstance(value, (list, tuple)) and all(
            item is None or isinstance(item, (str, int, float, bool))
            for item in value
        ):
            safe[key] = list(value)
        else:
            raise TypeError(f"metadata[{key!r}] must contain JSON scalar values")
    return safe


class MFARRuntimeEventWriter:
    """Append-only JSONL writer for observed MemWeave runtime operations."""

    def __init__(
        self,
        output_path: str | Path,
        *,
        run_id: str,
        repository_commit: str | None = None,
        dataset_revision: str | None = None,
        dataset_sha256: str | None = None,
        split: str | None = None,
        instrumentation_version: str = "0.1.0",
    ) -> None:
        if not run_id or not isinstance(run_id, str):
            raise ValueError("run_id must be a non-empty string")
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id
        self.run_metadata = {
            "repository_commit": repository_commit,
            "dataset_revision": dataset_revision,
            "dataset_sha256": dataset_sha256,
            "split": split,
            "instrumentation_version": instrumentation_version,
        }

    def emit(
        self,
        event_type: str,
        *,
        question_id: str | None = None,
        source_session_id: str | None = None,
        candidate_occurrence_id: str | None = None,
        input_ids: Iterable[str] = (),
        output_ids: Iterable[str] = (),
        content_sha256: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Write one event for an operation that actually occurred."""
        if event_type not in EVENT_TYPES:
            raise ValueError(f"unsupported event_type: {event_type}")
        if content_sha256 is not None and (
            len(content_sha256) != 64
            or any(ch not in "0123456789abcdef" for ch in content_sha256)
        ):
            raise ValueError("content_sha256 must be a lowercase SHA-256 hex digest")

        event = {
            "event_schema_version": "0.1.0",
            "run_id": self.run_id,
            "event_id": "evt_" + uuid.uuid4().hex,
            "event_type": event_type,
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "question_id": question_id,
            "source_session_id": source_session_id,
            "candidate_occurrence_id": candidate_occurrence_id,
            "input_ids": list(input_ids),
            "output_ids": list(output_ids),
            "content_sha256": content_sha256,
            "metadata": _safe_metadata(metadata),
            "run_metadata": self.run_metadata,
        }
        with self.output_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")
        return event
