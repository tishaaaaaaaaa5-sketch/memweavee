#!/usr/bin/env python3
"""Append-only, privacy-bounded event ledger for explicitly instrumented runs.

This writer is a standalone component: it does not itself instrument notebooks.
Identifiers must be opaque, prefixed hexadecimal tokens; free-form text is rejected.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

EVENT_TYPES = {
    "source_observed", "candidate_constructed", "candidate_pool_built",
    "retention_selected", "ranking_metric_computed", "qa_evidence_assembled",
    "answer_generated",
}
OPAQUE_ID = re.compile(r"^[a-z]{2,8}_[0-9a-f]{16,64}$")
RUN_ID = re.compile(r"^run_[0-9a-f]{16,64}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
SAFE_ENUMS = {
    "cost_unit": {"tokens", "words", "word_count_proxy", "whitespace_tokens", "tokenizer_tokens"},
    "tokenizer": {"whitespace-approx", "tiktoken/cl100k_base", "tiktoken/p50k_base"},
    "selection_method": {"baseline", "bm25", "recency", "random", "setting_b", "setting_c"},
    "evaluation_metric": {"accuracy", "containment", "exact_match", "f1", "precision", "recall"},
}
HASH_FIELDS = {"config_sha256", "generation_config_sha256", "model_id", "model_revision"}
INTEGER_FIELDS = {
    "candidate_count", "selected_count", "retrieved_count", "rank", "top_k",
    "input_token_count", "output_token_count", "seed", "fold", "latency_ms",
}
NUMBER_FIELDS = {"budget", "used_cost", "evaluation_value", "budget_fraction"}
BOOLEAN_FIELDS = {"evaluation_correct"}
METADATA_KEYS = set(SAFE_ENUMS) | HASH_FIELDS | INTEGER_FIELDS | NUMBER_FIELDS | BOOLEAN_FIELDS


def sha256_text(value: str) -> str:
    """Hash exact UTF-8 text without retaining the text itself."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _opaque_id(value: str | None, field: str, *, required: bool = False) -> None:
    if value is None and not required:
        return
    if not isinstance(value, str) or not OPAQUE_ID.fullmatch(value):
        raise ValueError(f"{field} must be an opaque prefixed lowercase-hex identifier")


def _safe_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    if metadata is None:
        return {}
    if not isinstance(metadata, dict):
        raise TypeError("metadata must be an object")
    unknown = set(metadata) - METADATA_KEYS
    if unknown:
        raise ValueError(f"metadata keys are not allowed: {sorted(unknown)}")
    safe: dict[str, Any] = {}
    for key, value in metadata.items():
        if value is None:
            safe[key] = None
        elif key in SAFE_ENUMS:
            if not isinstance(value, str) or value not in SAFE_ENUMS[key]:
                raise ValueError(f"metadata[{key!r}] must be one of the approved enum values")
            safe[key] = value
        elif key in HASH_FIELDS:
            if not isinstance(value, str) or not SHA256.fullmatch(value):
                raise ValueError(f"metadata[{key!r}] must be a lowercase SHA-256 digest")
            safe[key] = value
        elif key in INTEGER_FIELDS:
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"metadata[{key!r}] must be a non-negative integer")
            safe[key] = value
        elif key in NUMBER_FIELDS:
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f"metadata[{key!r}] must be a finite number")
            safe[key] = value
        elif key in BOOLEAN_FIELDS:
            if not isinstance(value, bool):
                raise ValueError(f"metadata[{key!r}] must be boolean")
            safe[key] = value
    return safe


def _safe_run_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    allowed = {"repository_commit", "dataset_revision", "dataset_sha256", "split", "instrumentation_version"}
    if set(metadata) - allowed:
        raise ValueError("run_metadata contains unsupported fields")
    commit = metadata.get("repository_commit")
    if commit is not None and (not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit)):
        raise ValueError("repository_commit must be a full lowercase Git SHA")
    revision = metadata.get("dataset_revision")
    if revision is not None and (
        not isinstance(revision, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", revision)
    ):
        raise ValueError("dataset_revision must be a bounded revision token")
    digest = metadata.get("dataset_sha256")
    if digest is not None and (not isinstance(digest, str) or not SHA256.fullmatch(digest)):
        raise ValueError("dataset_sha256 must be a lowercase SHA-256 digest")
    split = metadata.get("split")
    if split is not None and split not in {"train", "validation", "dev", "test"}:
        raise ValueError("split must be train, validation, dev, or test")
    version = metadata.get("instrumentation_version")
    if not isinstance(version, str) or not re.fullmatch(r"\\d+\\.\\d+\\.\\d+", version):
        raise ValueError("instrumentation_version must be semantic version x.y.z")
    return metadata


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
        if not isinstance(run_id, str) or not RUN_ID.fullmatch(run_id):
            raise ValueError("run_id must be run_ followed by 16-64 lowercase hex characters")
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id
        self.run_metadata = _safe_run_metadata({
            "repository_commit": repository_commit,
            "dataset_revision": dataset_revision,
            "dataset_sha256": dataset_sha256,
            "split": split,
            "instrumentation_version": instrumentation_version,
        })

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
        _opaque_id(question_id, "question_id", required=True)
        _opaque_id(source_session_id, "source_session_id")
        _opaque_id(candidate_occurrence_id, "candidate_occurrence_id")
        inputs, outputs = list(input_ids), list(output_ids)
        for field, values in (("input_ids", inputs), ("output_ids", outputs)):
            if any(not isinstance(value, str) or not OPAQUE_ID.fullmatch(value) for value in values):
                raise ValueError(f"{field} must contain only opaque prefixed lowercase-hex identifiers")
            if len(values) != len(set(values)):
                raise ValueError(f"{field} must not contain duplicate identifiers")
        if content_sha256 is not None and (
            not isinstance(content_sha256, str) or not SHA256.fullmatch(content_sha256)
        ):
            raise ValueError("content_sha256 must be a lowercase SHA-256 digest")

        event = {
            "event_schema_version": "0.1.0",
            "run_id": self.run_id,
            "event_id": "evt_" + uuid.uuid4().hex,
            "event_type": event_type,
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "question_id": question_id,
            "source_session_id": source_session_id,
            "candidate_occurrence_id": candidate_occurrence_id,
            "input_ids": inputs,
            "output_ids": outputs,
            "content_sha256": content_sha256,
            "metadata": _safe_metadata(metadata),
            "run_metadata": self.run_metadata,
        }
        with self.output_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\\n")
        return event
