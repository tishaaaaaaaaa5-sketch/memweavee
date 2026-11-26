#!/usr/bin/env python3
"""Validate cross-stage ID references in MFAR JSONL traces.

This complements JSON Schema validation: it checks that provenance and
transformation references resolve within each real trace. It creates no data,
labels, or inferred lifecycle events.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def require_unique_ids(items: list[dict[str, Any]], key: str, context: str) -> set[str]:
    found: set[str] = set()
    for index, item in enumerate(items):
        value = item.get(key)
        if not isinstance(value, str) or not value:
            raise ValueError(f"{context}[{index}] has no valid {key}")
        if value in found:
            raise ValueError(f"{context} contains duplicate {key}: {value}")
        found.add(value)
    return found


def require_refs(refs: Any, allowed: set[str], context: str) -> None:
    if not isinstance(refs, list):
        raise ValueError(f"{context} must be a list")
    missing = [ref for ref in refs if not isinstance(ref, str) or ref not in allowed]
    if missing:
        raise ValueError(f"{context} contains unresolved references: {missing[:5]}")


def validate_trace(trace: dict[str, Any], line_no: int) -> None:
    prefix = f"line {line_no}"
    if trace.get("schema_version") != "0.2.0":
        raise ValueError(f"{prefix}: unsupported schema version {trace.get('schema_version')!r}")

    pipeline = trace.get("pipeline")
    if not isinstance(pipeline, dict):
        raise ValueError(f"{prefix}: pipeline must be an object")

    source = pipeline.get("source_evidence", [])
    candidates = pipeline.get("candidate_memory", [])
    stored = pipeline.get("stored_memory", [])
    retrieved = pipeline.get("retrieved_evidence", [])
    transformations = pipeline.get("transformations", [])

    evidence_ids = require_unique_ids(source, "evidence_id", f"{prefix} source_evidence")
    candidate_ids = require_unique_ids(candidates, "memory_id", f"{prefix} candidate_memory")
    stored_ids = require_unique_ids(stored, "memory_id", f"{prefix} stored_memory")
    retrieved_ids = require_unique_ids(retrieved, "evidence_id", f"{prefix} retrieved_evidence")
    transformation_ids = require_unique_ids(
        transformations, "transformation_id", f"{prefix} transformations"
    )

    for label, memories in (("candidate_memory", candidates), ("stored_memory", stored)):
        for index, memory in enumerate(memories):
            require_refs(
                memory.get("source_evidence_ids", []),
                evidence_ids,
                f"{prefix} {label}[{index}].source_evidence_ids",
            )

    # A stored representation must retain explicit lineage to the source
    # archive; it is not enough for its content hash to happen to match.
    for index, memory in enumerate(stored):
        if not memory.get("source_evidence_ids"):
            raise ValueError(f"{prefix} stored_memory[{index}] has empty source lineage")

    all_memory_ids = candidate_ids | stored_ids
    all_evidence_ids = evidence_ids | retrieved_ids
    known_ids = all_memory_ids | all_evidence_ids

    for index, transformation in enumerate(transformations):
        require_refs(
            transformation.get("input_ids", []),
            known_ids,
            f"{prefix} transformations[{index}].input_ids",
        )
        require_refs(
            transformation.get("output_ids", []),
            known_ids,
            f"{prefix} transformations[{index}].output_ids",
        )

    outcome = trace.get("outcome") or {}
    require_refs(
        outcome.get("evidence_ids", []),
        retrieved_ids,
        f"{prefix} outcome.evidence_ids",
    )
    for index, claim in enumerate(outcome.get("claim_support", [])):
        require_refs(
            claim.get("evidence_ids", []),
            retrieved_ids,
            f"{prefix} outcome.claim_support[{index}].evidence_ids",
        )

    observability = trace.get("observability") or {}
    if observability.get("retrieval_trace_available") is False and retrieved:
        raise ValueError(f"{prefix}: retrieved evidence exists while retrieval is marked unobserved")
    if observability.get("answer_trace_available") is False:
        if outcome.get("status") != "not_evaluated":
            raise ValueError(f"{prefix}: answer status is evaluated while answer trace is marked unobserved")
        if outcome.get("answer_id") is not None or outcome.get("answer_content_sha256") is not None:
            raise ValueError(f"{prefix}: answer identifiers exist while answer trace is marked unobserved")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="MFAR trace JSONL")
    args = parser.parse_args()

    count = 0
    try:
        with args.input.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    trace = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"line {line_no}: invalid JSON: {exc}") from exc
                if not isinstance(trace, dict):
                    raise ValueError(f"line {line_no}: trace must be a JSON object")
                validate_trace(trace, line_no)
                count += 1
    except (OSError, ValueError) as exc:
        parser.exit(2, f"ERROR: {exc}\n")

    if count == 0:
        parser.exit(2, "ERROR: input contains no trace records\n")
    print(f"Cross-stage referential integrity passed for {count} traces.")
    print("No missing stages or failure labels were inferred.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
