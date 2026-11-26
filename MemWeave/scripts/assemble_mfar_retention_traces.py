#!/usr/bin/env python3
"""Assemble privacy-minimised MFAR-compatible traces from Stage B/C candidate exports.

This adapter represents the LongMemEval experiment as a *session-retention*
observation. It does not pretend that retained sessions are retrieval results,
or that the benchmark recorded compression or generated answers.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HEX20 = re.compile(r"^[0-9a-f]{20}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
REQUIRED_COLUMNS = {
    "question_id_sha256_20",
    "query_content_sha256",
    "variant",
    "candidate_index",
    "source_id",
    "content_sha256",
    "relevance_grade",
    "word_cost",
    "selected",
}


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read JSON from {path}: {exc}")
    if not isinstance(value, dict):
        fail(f"{path} must contain a JSON object")
    return value


def parse_bool(value: str, field: str) -> bool:
    normal = value.strip().lower()
    if normal in {"true", "1", "yes"}:
        return True
    if normal in {"false", "0", "no"}:
        return False
    fail(f"invalid boolean in {field}: {value!r}")


def read_candidate_rows(path: Path) -> dict[tuple[str, str], list[dict[str, Any]]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            columns = set(reader.fieldnames or [])
            missing = REQUIRED_COLUMNS - columns
            extra = columns - REQUIRED_COLUMNS
            if missing:
                fail(f"{path} is missing columns: {sorted(missing)}")
            if extra:
                fail(f"unexpected columns are rejected to prevent accidental text leakage: {sorted(extra)}")
            for line_no, row in enumerate(reader, start=2):
                qid = row["question_id_sha256_20"].strip().lower()
                query_hash = row["query_content_sha256"].strip().lower()
                source_id = row["source_id"].strip()
                content_hash = row["content_sha256"].strip().lower()
                variant = row["variant"].strip()
                if not HEX20.fullmatch(qid):
                    fail(f"line {line_no}: question id must be a 20-char SHA-256 prefix")
                if not HEX64.fullmatch(query_hash) or not HEX64.fullmatch(content_hash):
                    fail(f"line {line_no}: invalid SHA-256 field")
                if not re.fullmatch(r"src_[0-9a-f]{32}", source_id):
                    fail(f"line {line_no}: source_id must be src_ plus a 32-character lowercase hex digest")
                if not variant:
                    fail(f"line {line_no}: empty variant")
                try:
                    candidate_index = int(row["candidate_index"])
                    word_cost = float(row["word_cost"])
                except ValueError:
                    fail(f"line {line_no}: candidate_index/word_cost is not numeric")
                if candidate_index < 0 or not math.isfinite(word_cost) or word_cost < 0:
                    fail(f"line {line_no}: invalid candidate_index/word_cost")
                grade = row["relevance_grade"].strip()
                if grade not in {"gold", "irrelevant"}:
                    fail(f"line {line_no}: relevance_grade must be gold or irrelevant")
                groups[(qid, variant)].append({
                    "qid": qid,
                    "query_hash": query_hash,
                    "variant": variant,
                    "candidate_index": candidate_index,
                    "source_id": source_id,
                    "content_hash": content_hash,
                    "grade": grade,
                    "word_cost": word_cost,
                    "selected": parse_bool(row["selected"], "selected"),
                })
    except OSError as exc:
        fail(f"cannot read candidate CSV {path}: {exc}")
    if not groups:
        fail("candidate CSV contains no data rows")
    return groups


def validate_groups(groups: dict[tuple[str, str], list[dict[str, Any]]]) -> None:
    by_question: dict[str, list[tuple[str, list[dict[str, Any]]]]] = defaultdict(list)
    for (qid, variant), rows in groups.items():
        by_question[qid].append((variant, rows))
        indices = [row["candidate_index"] for row in rows]
        if len(indices) != len(set(indices)):
            fail(f"duplicate candidate_index for question {qid}, variant {variant}")
        if sorted(indices) != list(range(len(indices))):
            fail(f"candidate_index values must be contiguous from zero for question {qid}, variant {variant}")
        if not any(row["grade"] == "gold" for row in rows):
            fail(f"no gold candidate in question {qid}, variant {variant}")
        if len({row["query_hash"] for row in rows}) != 1:
            fail(f"inconsistent query content hash for question {qid}, variant {variant}")
        source_hashes: dict[str, str] = {}
        for row in rows:
            previous = source_hashes.setdefault(row["source_id"], row["content_hash"])
            if previous != row["content_hash"]:
                fail(f"source_id maps to multiple content hashes: {row['source_id']}")
        if len(source_hashes) != len(rows):
            fail(f"duplicate source_id within question {qid}, variant {variant}")
    reference_variants = None
    for qid, variants in by_question.items():
        variant_names = {variant for variant, _ in variants}
        if reference_variants is None:
            reference_variants = variant_names
        elif variant_names != reference_variants:
            fail(f"variant set differs for question {qid}")
        reference = None
        reference_query_hash = None
        for variant, rows in variants:
            query_hash = rows[0]["query_hash"]
            if reference_query_hash is None:
                reference_query_hash = query_hash
            elif query_hash != reference_query_hash:
                fail(f"query content hash differs across variants for question {qid}")
            signature = sorted(
                (r["candidate_index"], r["source_id"], r["content_hash"], r["grade"])
                for r in rows
            )
            if reference is None:
                reference = signature
            elif signature != reference:
                fail(f"candidate pool differs across variants for question {qid}")


def build_trace(
    qid: str,
    variant: str,
    rows: list[dict[str, Any]],
    manifest: dict[str, Any],
    created_at: str,
) -> dict[str, Any]:
    rows = sorted(rows, key=lambda row: row["candidate_index"])
    query_hashes = {row["query_hash"] for row in rows}
    if len(query_hashes) != 1:
        fail(f"question {qid} has inconsistent query hashes")
    query_hash = next(iter(query_hashes))

    source_evidence = []
    candidate_memory = []
    stored_memory = []
    candidate_ids = []
    stored_ids = []
    for row in rows:
        source_id = row["source_id"]
        suffix = source_id.removeprefix("src_")
        evidence_id = "ev_" + suffix
        candidate_memory_id = "mc_" + suffix
        stored_memory_id = "ms_" + suffix
        source_evidence.append({
            "evidence_id": evidence_id,
            "source_id": source_id,
            "content_sha256": row["content_hash"],
            "source_span": None,
            "relevance_grade": row["grade"],
        })
        candidate_memory.append({
            "memory_id": candidate_memory_id,
            "content_sha256": row["content_hash"],
            "source_evidence_ids": [evidence_id],
            "created_at": None,
            "confidence": None,
        })
        candidate_ids.append(candidate_memory_id)
        if row["selected"]:
            stored_memory.append({
                "memory_id": stored_memory_id,
                "content_sha256": row["content_hash"],
                "source_evidence_ids": [evidence_id],
                "created_at": None,
                "confidence": None,
            })
            stored_ids.append(stored_memory_id)

    manifest_fingerprint = hashlib.sha256(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    variant_fingerprint = hashlib.sha256(variant.encode("utf-8")).hexdigest()[:10]
    run_id = "run_" + manifest_fingerprint[:20] + "_" + variant_fingerprint
    example_id = "ex_" + qid + "_" + variant_fingerprint
    query_id = "q_" + qid

    return {
        "schema_version": "0.2.0",
        "run_id": run_id,
        "example_id": example_id,
        "created_at": created_at,
        "dataset": {
            "name": "LongMemEval-S",
            "revision": manifest.get("longmemeval_revision"),
            "checksum_sha256": manifest.get("longmemeval_sha256"),
            "split": "test",
            "conversation_cluster_id": None,
        },
        "query": {
            "query_id": query_id,
            "content_sha256": query_hash,
            "question_type": None,
            "requirements": [],
        },
        "observability": {
            "source_archive_available": True,
            "precompression_trace_available": False,
            "memory_provenance_available": True,
            "retrieval_trace_available": False,
            "answer_trace_available": False,
            "unavailable_reasons": [
                "The benchmark export contains source-session identifiers and hashes, but no pre-compression representation trace.",
                "The experiment evaluates budgeted retention; it does not record a separate retrieval operation.",
                "No generated-answer trace or answer-support adjudication is present in this benchmark export.",
            ],
        },
        "pipeline": {
            "source_evidence": source_evidence,
            "candidate_memory": candidate_memory,
            "stored_memory": stored_memory,
            "retrieved_evidence": [],
            "transformations": [{
                "transformation_id": "tr_" + qid + "_" + variant_fingerprint,
                "kind": "other",
                "input_ids": candidate_ids,
                "output_ids": stored_ids,
                "timestamp": created_at,
                "implementation_version": "stage-bc-factorial-notebook-export-v1",
                "metadata": {
                    "operation": "budgeted_session_retention_selection",
                    "variant": variant,
                    "budget_fraction": float(manifest.get("budget_fraction", 0.10)),
                    "budget_cost_unit": str(manifest.get("budget_cost_unit", "word-count proxy; not exact tokens")),
                },
            }],
        },
        "diagnosis": {
            "mode": "multi_label",
            "probabilities": {
                "construction": None,
                "compression": None,
                "retrieval": None,
                "answering": None,
            },
            "uncertainty": None,
            "model_version": "not_estimated",
            "feature_snapshot": {
                "candidate_count": len(rows),
                "retained_session_count": len(stored_memory),
                "gold_session_count": sum(row["grade"] == "gold" for row in rows),
                "variant": variant,
            },
        },
        "oracle_labels": {
            "construction": None,
            "compression": None,
            "retrieval": None,
            "answering": None,
            "annotation_version": "not_annotated",
            "annotator_agreement": None,
        },
        "controller": {
            "selected_action": "diagnostic_only",
            "policy_version": "offline-retention-adapter-0.1.0",
            "reason_codes": ["benchmark_retention_selection_is_not_an_mfar_intervention"],
            "estimated_quality_gain": None,
            "estimated_incremental_cost": None,
            "estimated_risk": None,
        },
        "outcome": {
            "answer_id": None,
            "answer_content_sha256": None,
            "evidence_ids": [],
            "status": "not_evaluated",
            "claim_support": [],
        },
        "cost": {
            "stored_tokens": None,
            "retrieved_tokens": None,
            "prompt_tokens": None,
            "completion_tokens": None,
            "latency_ms": None,
            "model_calls": None,
            "estimated_cost_usd": None,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, required=True, help="stage_bc_candidate_trace.csv")
    parser.add_argument("--manifest", type=Path, required=True, help="stage_bc_reconciliation_manifest.json")
    parser.add_argument("--schema", type=Path, default=Path(__file__).resolve().parents[1] / "schemas" / "mfar_trace.schema.json")
    parser.add_argument("--output", type=Path, default=Path("mfar_retention_traces.jsonl"))
    parser.add_argument("--created-at", help="UTC ISO-8601 trace-generation timestamp; defaults to current UTC time")
    args = parser.parse_args()

    manifest = load_json(args.manifest)
    if not manifest.get("longmemeval_revision") or not HEX64.fullmatch(str(manifest.get("longmemeval_sha256", ""))):
        fail("manifest must contain LongMemEval revision and full SHA-256 checksum")
    if manifest.get("pool") != "same_pipeline":
        fail("this adapter currently supports only the same_pipeline pool")
    groups = read_candidate_rows(args.candidates)
    validate_groups(groups)
    expected_variants = int(manifest.get("variant_count", 0)) + 1  # plus baseline
    if expected_variants < 2:
        fail("manifest must record a positive variant_count")
    variants_per_question: dict[str, set[str]] = defaultdict(set)
    for qid, variant in groups:
        variants_per_question[qid].add(variant)
    for qid, variants in variants_per_question.items():
        if "baseline" not in variants:
            fail(f"question {qid} is missing the baseline retention condition")
        if len(variants) != expected_variants:
            fail(
                f"question {qid} has {len(variants)} variants; "
                f"manifest expects {expected_variants} including baseline"
            )

    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ImportError:
        fail("install jsonschema first: python -m pip install jsonschema")
    schema = load_json(args.schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    created_at = args.created_at or datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

    traces = []
    for (qid, variant), rows in sorted(groups.items()):
        trace = build_trace(qid, variant, rows, manifest, created_at)
        errors = sorted(validator.iter_errors(trace), key=lambda e: list(e.absolute_path))
        if errors:
            details = "; ".join(
                f"{'.'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}"
                for e in errors
            )
            fail(f"assembled trace failed schema validation: {details}")
        traces.append(trace)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for trace in traces:
            handle.write(json.dumps(trace, ensure_ascii=False, separators=(",", ":")) + "\n")

    print(f"Assembled {len(traces)} traces across {len({t['query']['query_id'] for t in traces})} test questions.")
    print("All traces passed JSON Schema Draft 2020-12 validation.")
    print("Observability boundary: retention selection is represented; retrieval and answer stages remain unobserved.")
    print(f"Output: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
